"""
OAuth 2.0 Integration for Email Generator App.

Provides OAuth authentication with multiple providers (Google, GitHub, Microsoft)
for seamless integration with external services.
"""

import os
import json
import secrets
import hashlib
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs
import uuid

# Import configuration
try:
    from ..utils.config import settings as app_settings
except ImportError:
    # Fallback for standalone usage
    class MockSettings:
        enable_oauth = True
        disable_oauth = False
        oauth_config_file = "config/oauth_config.json"
        google_client_id = ""
        google_client_secret = ""
        google_redirect_uri = "http://localhost:8000/auth/callback/google"
        github_client_id = ""
        github_client_secret = ""
        github_redirect_uri = "http://localhost:8000/auth/callback/github"
        microsoft_client_id = ""
        microsoft_client_secret = ""
        microsoft_redirect_uri = "http://localhost:8000/auth/callback/microsoft"
    app_settings = MockSettings()

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("OAuth dependencies not installed. Run: pip install requests")

_PLACEHOLDER_VALUES = {
    "your_google_client_id_here",
    "your_google_client_secret_here",
    "your_github_client_id_here",
    "your_github_client_secret_here",
    "your_microsoft_client_id_here",
    "your_microsoft_client_secret_here",
    "changeme",
    "placeholder",
}


def _has_real_value(value: Optional[str]) -> bool:
    """Return True when the provided setting value is populated with non-placeholder data."""
    if value is None:
        return False
    trimmed = str(value).strip()
    if not trimmed:
        return False
    lowered = trimmed.lower()
    if lowered in _PLACEHOLDER_VALUES:
        return False
    if lowered.startswith("your_"):
        return False
    return True


def _sanitize_user_id(raw_value: Optional[str], fallback: str) -> str:
    """Return a filesystem-safe identifier derived from OAuth user data."""
    candidate = (raw_value or fallback or "user").strip()
    if not candidate:
        candidate = "user"

    safe_chars: list[str] = []
    for ch in candidate:
        if ch.isalnum() or ch in {"-", "_"}:
            safe_chars.append(ch)
        elif ch in {"@", "."}:
            safe_chars.append("_")
        else:
            safe_chars.append("-")

    sanitized = "".join(safe_chars).strip("-_")
    return sanitized.lower() or "user"


class OAuthProvider:
    """Base class for OAuth providers."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: List[str] = None
    ):
        """
        Initialize OAuth provider.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Redirect URI after authentication
            scope: List of requested scopes
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope or []
        
        # Configure requests session with retries
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
    
    def get_authorization_url(self, state: str = None) -> tuple:
        """
        Get authorization URL and state.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Tuple of (authorization_url, state)
        """
        raise NotImplementedError("Subclasses must implement get_authorization_url")
    
    def exchange_code_for_token(self, code: str, state: str = None) -> Optional[Dict]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            state: State parameter for CSRF protection
            
        Returns:
            Token response dict or None if failed
        """
        raise NotImplementedError("Subclasses must implement exchange_code_for_token")
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token response dict or None if failed
        """
        raise NotImplementedError("Subclasses must implement refresh_access_token")
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Get user information using access token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User info dict or None if failed
        """
        raise NotImplementedError("Subclasses must implement get_user_info")


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth 2.0 provider."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scope: List[str] = None):
        if scope is None:
            scope = [
                'openid',
                'email', 
                'profile',
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.modify'
            ]
        
        super().__init__(client_id, client_secret, redirect_uri, scope)
        
        self.authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_authorization_url(self, state: str = None) -> tuple:
        """Get Google authorization URL."""
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scope),
            'response_type': 'code',
            'state': state,
            'access_type': 'offline',  # For refresh token
            'prompt': 'consent'  # Force consent to get refresh token
        }
        
        auth_url = f"{self.authorization_base_url}?{urlencode(params)}"
        return auth_url, state
    
    def exchange_code_for_token(self, code: str, state: str = None) -> Optional[Dict]:
        """Exchange Google authorization code for tokens."""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            
            response = self.session.post(
                self.token_url,
                data=token_data,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                token_info = response.json()
                
                # Add metadata
                token_info['provider'] = 'google'
                token_info['obtained_at'] = datetime.utcnow().isoformat()
                token_info['expires_at'] = (
                    datetime.utcnow() + timedelta(seconds=token_info.get('expires_in', 3600))
                ).isoformat()
                
                return token_info
            else:
                print(f"Google token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error exchanging Google code for token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh Google access token."""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            refresh_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = self.session.post(
                self.token_url,
                data=refresh_data,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                token_info = response.json()
                token_info['provider'] = 'google'
                token_info['obtained_at'] = datetime.utcnow().isoformat()
                token_info['expires_at'] = (
                    datetime.utcnow() + timedelta(seconds=token_info.get('expires_in', 3600))
                ).isoformat()
                
                # Preserve refresh token if not returned
                if 'refresh_token' not in token_info:
                    token_info['refresh_token'] = refresh_token
                
                return token_info
            else:
                print(f"Google token refresh failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error refreshing Google token: {e}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get Google user information."""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = self.session.get(
                self.userinfo_url,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                
                # Standardize user info format
                return {
                    'provider': 'google',
                    'provider_id': user_info.get('id'),
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'first_name': user_info.get('given_name'),
                    'last_name': user_info.get('family_name'),
                    'picture': user_info.get('picture'),
                    'verified_email': user_info.get('verified_email', False),
                    'locale': user_info.get('locale'),
                    'raw_data': user_info
                }
            else:
                print(f"Google user info failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting Google user info: {e}")
            return None


class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth 2.0 provider."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scope: List[str] = None):
        if scope is None:
            scope = ['user:email', 'read:user']
        
        super().__init__(client_id, client_secret, redirect_uri, scope)
        
        self.authorization_base_url = "https://github.com/login/oauth/authorize"
        self.token_url = "https://github.com/login/oauth/access_token"
        self.userinfo_url = "https://api.github.com/user"
        self.user_emails_url = "https://api.github.com/user/emails"
    
    def get_authorization_url(self, state: str = None) -> tuple:
        """Get GitHub authorization URL."""
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scope),
            'state': state,
            'allow_signup': 'true'
        }
        
        auth_url = f"{self.authorization_base_url}?{urlencode(params)}"
        return auth_url, state
    
    def exchange_code_for_token(self, code: str, state: str = None) -> Optional[Dict]:
        """Exchange GitHub authorization code for tokens."""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code
            }
            
            response = self.session.post(
                self.token_url,
                data=token_data,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                token_info = response.json()
                
                # GitHub doesn't provide expires_in, set default
                token_info['provider'] = 'github'
                token_info['obtained_at'] = datetime.utcnow().isoformat()
                token_info['expires_in'] = token_info.get('expires_in', 28800)  # 8 hours default
                token_info['expires_at'] = (
                    datetime.utcnow() + timedelta(seconds=token_info['expires_in'])
                ).isoformat()
                
                return token_info
            else:
                print(f"GitHub token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error exchanging GitHub code for token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """GitHub doesn't support refresh tokens in the traditional sense."""
        # GitHub tokens are long-lived and don't expire in the traditional sense
        # This method would need to re-authenticate the user
        return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get GitHub user information."""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            headers = {
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Get user info
            user_response = self.session.get(
                self.userinfo_url,
                headers=headers,
                timeout=10
            )
            
            if user_response.status_code != 200:
                return None
            
            user_info = user_response.json()
            
            # Get user emails
            email = user_info.get('email')
            if not email:
                # Try to get primary email
                emails_response = self.session.get(
                    self.user_emails_url,
                    headers=headers,
                    timeout=10
                )
                
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    primary_email = next((e for e in emails if e.get('primary')), None)
                    if primary_email:
                        email = primary_email.get('email')
            
            # Standardize user info format
            return {
                'provider': 'github',
                'provider_id': str(user_info.get('id')),
                'email': email,
                'name': user_info.get('name') or user_info.get('login'),
                'username': user_info.get('login'),
                'avatar_url': user_info.get('avatar_url'),
                'bio': user_info.get('bio'),
                'company': user_info.get('company'),
                'location': user_info.get('location'),
                'raw_data': user_info
            }
            
        except Exception as e:
            print(f"Error getting GitHub user info: {e}")
            return None


class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft OAuth 2.0 provider (Azure AD)."""
    
    def __init__(
        self, 
        client_id: str, 
        client_secret: str, 
        redirect_uri: str, 
        tenant: str = "common",
        scope: List[str] = None
    ):
        if scope is None:
            scope = [
                'openid',
                'profile', 
                'email',
                'https://graph.microsoft.com/Mail.Send',
                'https://graph.microsoft.com/Mail.ReadWrite'
            ]
        
        super().__init__(client_id, client_secret, redirect_uri, scope)
        
        self.tenant = tenant
        self.authorization_base_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
        self.token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        self.userinfo_url = "https://graph.microsoft.com/v1.0/me"
    
    def get_authorization_url(self, state: str = None) -> tuple:
        """Get Microsoft authorization URL."""
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'response_mode': 'query',
            'scope': ' '.join(self.scope),
            'state': state
        }
        
        auth_url = f"{self.authorization_base_url}?{urlencode(params)}"
        return auth_url, state
    
    def exchange_code_for_token(self, code: str, state: str = None) -> Optional[Dict]:
        """Exchange Microsoft authorization code for tokens."""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            
            response = self.session.post(
                self.token_url,
                data=token_data,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                token_info = response.json()
                
                token_info['provider'] = 'microsoft'
                token_info['obtained_at'] = datetime.utcnow().isoformat()
                token_info['expires_at'] = (
                    datetime.utcnow() + timedelta(seconds=token_info.get('expires_in', 3600))
                ).isoformat()
                
                return token_info
            else:
                print(f"Microsoft token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error exchanging Microsoft code for token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh Microsoft access token."""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            refresh_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = self.session.post(
                self.token_url,
                data=refresh_data,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                token_info = response.json()
                token_info['provider'] = 'microsoft'
                token_info['obtained_at'] = datetime.utcnow().isoformat()
                token_info['expires_at'] = (
                    datetime.utcnow() + timedelta(seconds=token_info.get('expires_in', 3600))
                ).isoformat()
                
                if 'refresh_token' not in token_info:
                    token_info['refresh_token'] = refresh_token
                
                return token_info
            else:
                print(f"Microsoft token refresh failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error refreshing Microsoft token: {e}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get Microsoft user information."""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = self.session.get(
                self.userinfo_url,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                
                return {
                    'provider': 'microsoft',
                    'provider_id': user_info.get('id'),
                    'email': user_info.get('mail') or user_info.get('userPrincipalName'),
                    'name': user_info.get('displayName'),
                    'first_name': user_info.get('givenName'),
                    'last_name': user_info.get('surname'),
                    'job_title': user_info.get('jobTitle'),
                    'office_location': user_info.get('officeLocation'),
                    'preferred_language': user_info.get('preferredLanguage'),
                    'raw_data': user_info
                }
            else:
                print(f"Microsoft user info failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting Microsoft user info: {e}")
            return None


class OAuthManager:
    """
    OAuth manager for handling multiple providers and token management.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize OAuth manager.
        
        Args:
            config_file: Path to OAuth configuration file (uses app_settings if None)
        """
        self.config_file = config_file or app_settings.oauth_config_file
        self.providers = {}
        self.active_sessions = {}
        
        # Load configuration (from file or direct settings)
        self.load_config()
    
    def load_config(self):
        """Load OAuth configuration from settings or file."""
        try:
            # First try to load from centralized settings
            providers_config = {}
            
            # Google OAuth provider
            if (
                app_settings.enable_google_oauth
                and _has_real_value(app_settings.google_client_id)
                and _has_real_value(app_settings.google_client_secret)
            ):
                providers_config['google'] = {
                    'type': 'google',
                    'client_id': app_settings.google_client_id.strip(),
                    'client_secret': app_settings.google_client_secret.strip(),
                    'redirect_uri': app_settings.google_redirect_uri.strip(),
                    'scope': list(app_settings.google_oauth_scopes or []),
                    'enabled': True,
                }
            
            # GitHub OAuth provider
            if (
                app_settings.enable_github_oauth
                and _has_real_value(app_settings.github_client_id)
                and _has_real_value(app_settings.github_client_secret)
            ):
                providers_config['github'] = {
                    'type': 'github',
                    'client_id': app_settings.github_client_id.strip(),
                    'client_secret': app_settings.github_client_secret.strip(),
                    'redirect_uri': app_settings.github_redirect_uri.strip(),
                    'scope': list(app_settings.github_oauth_scopes or []),
                    'enabled': True,
                }
            
            # Microsoft OAuth provider
            if (
                app_settings.enable_microsoft_oauth
                and _has_real_value(app_settings.microsoft_client_id)
                and _has_real_value(app_settings.microsoft_client_secret)
            ):
                providers_config['microsoft'] = {
                    'type': 'microsoft',
                    'client_id': app_settings.microsoft_client_id.strip(),
                    'client_secret': app_settings.microsoft_client_secret.strip(),
                    'redirect_uri': app_settings.microsoft_redirect_uri.strip(),
                    'tenant': (app_settings.microsoft_tenant or 'common').strip() or 'common',
                    'scope': list(app_settings.microsoft_oauth_scopes or []),
                    'enabled': True,
                }
            
            # If no providers configured via settings, fall back to config file
            if not providers_config and os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                providers_config = config.get('providers', {})
            
            # Initialize providers from config
            for provider_name, provider_config in providers_config.items():
                self.add_provider(provider_name, provider_config)
                
        except Exception as e:
            print(f"Error loading OAuth config: {e}")
    
    def add_provider(self, name: str, config: Dict):
        """
        Add OAuth provider.
        
        Args:
            name: Provider name
            config: Provider configuration
        """
        if not isinstance(config, dict):
            print(f"Skipping OAuth provider {name}: configuration is not a mapping")
            return

        if config.get('enabled') is False:
            return

        client_id = config.get('client_id')
        client_secret = config.get('client_secret')
        redirect_uri = (config.get('redirect_uri') or '').strip()

        if not (_has_real_value(client_id) and _has_real_value(client_secret)):
            print(f"Skipping OAuth provider {name}: missing client credentials")
            return

        if not redirect_uri:
            print(f"Skipping OAuth provider {name}: redirect URI is missing")
            return

        scope_config = config.get('scope')
        scopes: Optional[List[str]]
        if isinstance(scope_config, str):
            scopes = [scope_config.strip()] if scope_config.strip() else None
        elif isinstance(scope_config, (list, tuple, set)):
            scopes = [str(item).strip() for item in scope_config if str(item).strip()]
            if not scopes:
                scopes = None
        else:
            scopes = None

        provider_type = str(config.get('type', '')).lower().strip()

        if provider_type == 'google':
            provider = GoogleOAuthProvider(
                client_id=str(client_id).strip(),
                client_secret=str(client_secret).strip(),
                redirect_uri=redirect_uri,
                scope=scopes,
            )
        elif provider_type == 'github':
            provider = GitHubOAuthProvider(
                client_id=str(client_id).strip(),
                client_secret=str(client_secret).strip(),
                redirect_uri=redirect_uri,
                scope=scopes,
            )
        elif provider_type == 'microsoft':
            tenant = str(config.get('tenant', 'common') or 'common').strip() or 'common'
            provider = MicrosoftOAuthProvider(
                client_id=str(client_id).strip(),
                client_secret=str(client_secret).strip(),
                redirect_uri=redirect_uri,
                tenant=tenant,
                scope=scopes,
            )
        else:
            print(f"Unknown OAuth provider type: {provider_type}")
            return

        self.providers[name] = provider
    
    def start_oauth_flow(self, provider_name: str, user_id: str = None) -> Optional[Dict]:
        """
        Start OAuth flow for a provider.
        
        Args:
            provider_name: Name of the OAuth provider
            user_id: Optional user ID for session tracking
            
        Returns:
            Dict with authorization URL and state, or None if failed
        """
        if provider_name not in self.providers:
            return None
        
        provider = self.providers[provider_name]
        
        try:
            auth_url, state = provider.get_authorization_url()
            
            # Store session info
            session_id = str(uuid.uuid4())
            self.active_sessions[state] = {
                'session_id': session_id,
                'provider': provider_name,
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'pending'
            }
            
            return {
                'authorization_url': auth_url,
                'state': state,
                'session_id': session_id,
                'provider': provider_name
            }
            
        except Exception as e:
            print(f"Error starting OAuth flow for {provider_name}: {e}")
            return None
    
    def complete_oauth_flow(
        self, 
        provider_name: str, 
        code: str, 
        state: str
    ) -> Optional[Dict]:
        """
        Complete OAuth flow with authorization code.
        
        Args:
            provider_name: Name of the OAuth provider
            code: Authorization code from callback
            state: State parameter from callback
            
        Returns:
            Complete OAuth result with tokens and user info
        """
        if provider_name not in self.providers:
            return None
        
        if state not in self.active_sessions:
            return None
        
        session_info = self.active_sessions[state]
        if session_info['provider'] != provider_name:
            return None
        
        provider = self.providers[provider_name]
        
        try:
            # Exchange code for tokens
            tokens = provider.exchange_code_for_token(code, state)
            if not tokens:
                return None
            
            # Get user info
            user_info = provider.get_user_info(tokens['access_token'])
            if not user_info:
                return None

            raw_identifier = (
                user_info.get('email')
                or user_info.get('provider_id')
                or session_info.get('user_id')
                or f"{provider_name}_user"
            )
            safe_user_id = _sanitize_user_id(raw_identifier, provider_name)

            session_info['user_id'] = safe_user_id
            
            # Update session
            session_info['status'] = 'completed'
            session_info['completed_at'] = datetime.utcnow().isoformat()
            
            result = {
                'session_id': session_info['session_id'],
                'provider': provider_name,
                'user_id': safe_user_id,
                'tokens': tokens,
                'user_info': user_info,
                'completed_at': session_info['completed_at']
            }
            
            # Clean up session
            del self.active_sessions[state]
            
            return result
            
        except Exception as e:
            print(f"Error completing OAuth flow for {provider_name}: {e}")
            return None
    
    def refresh_tokens(self, provider_name: str, refresh_token: str) -> Optional[Dict]:
        """
        Refresh access tokens using refresh token.
        
        Args:
            provider_name: Name of the OAuth provider
            refresh_token: Refresh token
            
        Returns:
            New tokens or None if failed
        """
        if provider_name not in self.providers:
            return None
        
        provider = self.providers[provider_name]
        
        try:
            return provider.refresh_access_token(refresh_token)
        except Exception as e:
            print(f"Error refreshing tokens for {provider_name}: {e}")
            return None
    
    def get_user_info(self, provider_name: str, access_token: str) -> Optional[Dict]:
        """
        Get user info using access token.
        
        Args:
            provider_name: Name of the OAuth provider
            access_token: Valid access token
            
        Returns:
            User info or None if failed
        """
        if provider_name not in self.providers:
            return None
        
        provider = self.providers[provider_name]
        
        try:
            return provider.get_user_info(access_token)
        except Exception as e:
            print(f"Error getting user info from {provider_name}: {e}")
            return None
    
    def get_available_providers(self) -> List[str]:
        """Get list of available OAuth providers."""
        return list(self.providers.keys())
    
    def get_provider_info(self, provider_name: str) -> Optional[Dict]:
        """Get information about a specific provider."""
        if provider_name not in self.providers:
            return None
        
        provider = self.providers[provider_name]
        
        return {
            'name': provider_name,
            'type': provider.__class__.__name__.replace('OAuthProvider', '').lower(),
            'scopes': provider.scope,
            'redirect_uri': provider.redirect_uri
        }


# Factory function
def create_oauth_manager(
    use_oauth: Optional[bool] = None,
    config_file: Optional[str] = None
) -> Optional[OAuthManager]:
    """
    Factory function to create OAuth manager.
    
    Args:
        use_oauth: Whether to enable OAuth (uses app_settings if None)
        config_file: Path to OAuth configuration (uses app_settings if None)
        
    Returns:
        OAuthManager instance or None if disabled
    """
    # Use settings to determine if OAuth should be enabled
    use_oauth = use_oauth if use_oauth is not None else app_settings.enable_oauth
    
    # Check if OAuth is disabled via settings
    if not use_oauth or app_settings.disable_oauth:
        return None
    
    if not REQUESTS_AVAILABLE:
        print("OAuth integration disabled: requests library not installed")
        return None
    
    try:
        return OAuthManager(config_file)
    except Exception as e:
        print(f"Failed to initialize OAuth manager: {e}")
        return None