# Authentication Module

Complete authentication system for the Email Generator App with user management, session handling, and Streamlit integration.

## Features

- ✅ **User Registration & Login** - Secure email/password authentication
- ✅ **Session Management** - Token-based sessions with expiration
- ✅ **Password Security** - SHA-256 hashing with salt
- ✅ **Role-Based Access Control** - User and admin roles
- ✅ **Streamlit Integration** - Ready-to-use UI components
- ✅ **Session Persistence** - JSON-based data storage
- ✅ **Account Management** - Profile updates, password changes, account deletion

## Quick Start

### Basic Setup

```python
from src.auth import AuthManager

# Initialize auth manager
auth = AuthManager()

# Register a new user
result = auth.register(
    email="user@example.com",
    password="SecurePass123",
    full_name="John Doe"
)

# Login
login_result = auth.login("user@example.com", "SecurePass123")
token = login_result["token"]

# Check authentication
if auth.is_authenticated(token):
    user = auth.get_current_user(token)
    print(f"Welcome {user['full_name']}")
```

### Streamlit Integration

```python
import streamlit as st
from src.auth.streamlit_auth import StreamlitAuth

# Initialize
auth_helper = StreamlitAuth()

# Require authentication
auth_helper.require_auth()

# Get current user
user = auth_helper.get_current_user()
st.write(f"Hello {user['full_name']}")

# Add user menu to sidebar
auth_helper.user_menu()
```

## Architecture

### Components

1. **UserManager** (`user_manager.py`)
   - User registration and credential verification
   - Password hashing and security
   - User profile management
   - Role-based access control

2. **SessionManager** (`session_manager.py`)
   - Session token generation and validation
   - Session expiration management
   - Token refresh mechanism
   - Multi-session support

3. **AuthManager** (`auth_manager.py`)
   - High-level authentication API
   - Combines UserManager and SessionManager
   - Login/logout workflows
   - Access control helpers

4. **StreamlitAuth** (`streamlit_auth.py`)
   - Streamlit UI components
   - Session state integration
   - Login/register forms
   - User menu widgets

### Data Storage

```
data/
├── users/
│   └── users.json          # User accounts and credentials
└── sessions/
    └── sessions.json       # Active sessions
```

## API Reference

### AuthManager

#### Registration

```python
auth.register(
    email: str,                    # User's email (unique)
    password: str,                 # Plain text password (min 8 chars)
    full_name: str,                # User's full name
    role: str = "user",            # Role: "user" or "admin"
    metadata: Optional[Dict] = None # Additional metadata
) -> Dict
```

Returns:
```python
{
    "success": True,
    "user_id": "abc123...",
    "message": "User registered successfully"
}
```

#### Login

```python
auth.login(
    email: str,                # User's email
    password: str,             # Plain text password
    remember_me: bool = False  # Extend session duration
) -> Dict
```

Returns:
```python
{
    "success": True,
    "token": "secure-token-here",
    "user": {
        "user_id": "abc123",
        "email": "user@example.com",
        "full_name": "John Doe",
        "role": "user",
        "status": "active",
        "created_at": "2025-11-12T10:30:00",
        "last_login": "2025-11-12T10:30:00"
    }
}
```

#### Check Authentication

```python
# Simple check
is_auth = auth.is_authenticated(token)  # Returns bool

# Get user info
user = auth.get_current_user(token)     # Returns user dict or None

# Require authentication (raises ValueError if not authenticated)
user = auth.require_auth(token)

# Require specific role
admin = auth.require_role(token, "admin")
```

#### Logout

```python
# Logout from current session
result = auth.logout(token)

# Logout from all sessions
result = auth.logout_all_sessions(token)
```

#### Profile Management

```python
# Get profile
profile = auth.get_user_profile(token)

# Update profile
result = auth.update_profile(token, {
    "full_name": "Jane Doe",
    "metadata": {"phone": "+1234567890"}
})

# Change password
result = auth.change_password(
    token=token,
    old_password="OldPass123",
    new_password="NewPass456"
)

# Delete account (requires password)
result = auth.delete_account(token, password="CurrentPass123")
```

#### Session Management

```python
# Refresh session (get new token)
new_token = auth.refresh_session(old_token)

# Cleanup expired sessions
auth.cleanup_sessions()

# Get statistics
stats = auth.get_stats()
# Returns: {
#   "total_active_users": 42,
#   "active_sessions": 15,
#   "unique_users": 12
# }
```

### StreamlitAuth

#### Basic Usage

```python
from src.auth.streamlit_auth import StreamlitAuth

auth_helper = StreamlitAuth()

# Check if authenticated
if auth_helper.is_authenticated():
    user = auth_helper.get_current_user()
    st.write(f"Welcome {user['full_name']}")
else:
    st.write("Please login")
```

#### UI Components

```python
# Complete login/register page
user = auth_helper.login_page()

# Individual forms
auth_helper.login_form()
auth_helper.register_form()
auth_helper.change_password_form()

# User menu in sidebar
auth_helper.user_menu()

# Logout
if st.button("Logout"):
    auth_helper.logout()
```

#### Protecting Pages

```python
# Require authentication to access page
auth_helper.require_auth()

# Rest of your Streamlit app
st.title("Protected Page")
user = auth_helper.get_current_user()
st.write(f"Hello {user['full_name']}")
```

## Security Features

### Password Security
- **SHA-256 hashing** with unique salt per user
- **Minimum 8 characters** password requirement
- **Salt stored separately** for each user
- **No plain text storage** - passwords never stored in readable form

### Session Security
- **Cryptographically secure tokens** using `secrets.token_urlsafe()`
- **Automatic expiration** - default 24 hours
- **Session refresh** mechanism for extending sessions
- **Multi-session support** - users can have multiple active sessions
- **Automatic cleanup** of expired sessions

### Access Control
- **Role-based permissions** (user, admin)
- **Account status management** (active, suspended, deleted)
- **Soft deletion** - accounts marked as deleted, not removed
- **Protected fields** - sensitive fields cannot be updated directly

## Integration with Email Generator

### Adding Authentication to Main App

Update `src/ui/streamlit_app.py`:

```python
import streamlit as st
from src.auth.streamlit_auth import StreamlitAuth
from src.workflow.langgraph_flow import execute_workflow

# Initialize authentication
auth_helper = StreamlitAuth()

# Require login
auth_helper.require_auth()

# Get current user
user = auth_helper.get_current_user()

# Use user_id for personalization
st.sidebar.text_input("User ID", value=user['user_id'], disabled=True)

# Add user menu
auth_helper.user_menu()

# Rest of your email generation logic
# The user_id from auth can be used for execute_workflow(user_id=user['user_id'])
```

### Linking Auth User ID with Email Profiles

```python
from src.auth import AuthManager
from src.agents.personalization import PersonalizationAgent

auth = AuthManager()
personalizer = PersonalizationAgent(llm)

# After login
token = auth.login(email, password)["token"]
user = auth.get_current_user(token)

# Use auth user_id for email personalization
personalized_draft = personalizer.personalize(
    draft=draft,
    user_id=user["user_id"]
)
```

## Configuration

### Default Settings

```python
# Session duration
session_duration_hours = 24  # Sessions expire after 24 hours

# Token length
token_length = 32  # 32 bytes = 256 bits of entropy

# Data storage paths
users_file = "data/users/users.json"
sessions_file = "data/sessions/sessions.json"
```

### Custom Configuration

```python
# Custom session duration (7 days)
auth = AuthManager(session_duration_hours=168)

# Custom file paths
auth = AuthManager(
    users_file="custom/path/users.json",
    sessions_file="custom/path/sessions.json"
)
```

## User Roles

### Available Roles

- **user** - Standard user with basic access
- **admin** - Administrator with elevated privileges

### Checking Roles

```python
# Require admin role
try:
    admin_user = auth.require_role(token, "admin")
    # User is admin, proceed with admin operations
except ValueError:
    # User is not admin or not authenticated
    st.error("Admin access required")
```

### Custom Role Logic

```python
user = auth.get_current_user(token)

if user and user.get("role") == "admin":
    # Show admin features
    st.sidebar.button("Admin Panel")
```

## Examples

### Example 1: Basic Login Flow

```python
import streamlit as st
from src.auth.streamlit_auth import StreamlitAuth

auth = StreamlitAuth()

if not auth.is_authenticated():
    st.title("Please Login")
    auth.login_page()
else:
    user = auth.get_current_user()
    st.title(f"Welcome {user['full_name']}")
    
    if st.button("Logout"):
        auth.logout()
```

### Example 2: Protected Admin Page

```python
from src.auth import AuthManager

auth = AuthManager()

def admin_page(token):
    try:
        # Require admin role
        admin = auth.require_role(token, "admin")
        
        st.title("Admin Dashboard")
        stats = auth.get_stats()
        st.metric("Total Users", stats["total_active_users"])
        st.metric("Active Sessions", stats["active_sessions"])
        
    except ValueError as e:
        st.error(str(e))
        st.stop()
```

### Example 3: User Profile Management

```python
import streamlit as st
from src.auth.streamlit_auth import StreamlitAuth

auth = StreamlitAuth()
auth.require_auth()

st.title("My Profile")

user = auth.get_current_user()

# Display current info
st.write(f"**Name:** {user['full_name']}")
st.write(f"**Email:** {user['email']}")
st.write(f"**Role:** {user['role']}")

# Update profile
with st.form("update_profile"):
    new_name = st.text_input("Full Name", value=user['full_name'])
    
    if st.form_submit_button("Update"):
        result = auth.auth.update_profile(
            st.session_state.auth_token,
            {"full_name": new_name}
        )
        if result["success"]:
            st.success("Profile updated!")
            st.rerun()

# Change password
st.markdown("---")
auth.change_password_form()
```

## Testing

### Manual Testing

```python
from src.auth import AuthManager

# Initialize
auth = AuthManager(
    users_file="test_data/users.json",
    sessions_file="test_data/sessions.json"
)

# Test registration
result = auth.register("test@example.com", "TestPass123", "Test User")
assert result["success"]

# Test login
login = auth.login("test@example.com", "TestPass123")
assert login["success"]
token = login["token"]

# Test authentication
assert auth.is_authenticated(token)

# Test get user
user = auth.get_current_user(token)
assert user["email"] == "test@example.com"

# Test logout
auth.logout(token)
assert not auth.is_authenticated(token)
```

## Troubleshooting

### Common Issues

**Issue: "User already exists"**
```python
# Check if user exists before registering
if auth.user_manager.user_exists(email):
    st.error("Email already registered. Please login.")
```

**Issue: Sessions not persisting after restart**
- Sessions are stored in `data/sessions/sessions.json`
- Ensure the directory has write permissions
- Check if file is being saved correctly

**Issue: "Invalid email or password"**
```python
# Verify user exists and is active
user = auth.user_manager.get_user(email)
if user:
    print(f"User status: {user['status']}")
```

## Best Practices

1. **Always use HTTPS** in production for secure token transmission
2. **Store sensitive data** (API keys, secrets) in environment variables
3. **Regular session cleanup** - call `auth.cleanup_sessions()` periodically
4. **Strong password policy** - enforce minimum 8 characters (consider adding complexity requirements)
5. **Use role-based access** - implement `require_role()` for admin features
6. **Session refresh** - implement token refresh for long-running sessions
7. **Audit logging** - add logging for authentication events

## License

Part of the Email Generator App project.
