"""
Model Context Protocol (MCP) Integration for Email Generator App.

Provides MCP server/client capabilities for tool integration and context sharing
with other AI systems and applications.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid

# Import configuration
try:
    from ..utils.config import settings as app_settings
except ImportError:
    # Fallback for standalone usage
    class MockSettings:
        enable_mcp = True
        mcp_server_host = "localhost"
        mcp_server_port = 8765
        mcp_server_name = "email-generator-mcp-server"
        mcp_server_version = "1.0.0"
        mcp_client_timeout = 30.0
    app_settings = MockSettings()


class MCPEmailServer:
    """
    MCP Server for Email Generator App.
    
    Exposes email generation capabilities as MCP tools that other
    AI systems can use.
    """
    
    def __init__(
        self, 
        email_generator_instance=None,
        server_name: Optional[str] = None,
        server_version: Optional[str] = None,
        server_host: Optional[str] = None,
        server_port: Optional[int] = None
    ):
        """
        Initialize MCP server.
        
        Args:
            email_generator_instance: Instance of the main email generator
            server_name: Server name (uses app_settings if None)
            server_version: Server version (uses app_settings if None)
            server_host: Server host (uses app_settings if None)
            server_port: Server port (uses app_settings if None)
        """
        self.email_generator = email_generator_instance
        self.server_host = server_host or app_settings.mcp_server_host
        self.server_port = server_port or app_settings.mcp_server_port
        
        self.server_info = {
            "name": server_name or app_settings.mcp_server_name,
            "version": server_version or app_settings.mcp_server_version,
            "description": "MCP server for AI-powered email generation",
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True
            }
        }
        
        # Register available tools
        self.tools = {
            "generate_email": {
                "name": "generate_email",
                "description": "Generate a personalized email based on user input and context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier for personalization"
                        },
                        "prompt": {
                            "type": "string", 
                            "description": "Email prompt or description of what to write"
                        },
                        "recipient": {
                            "type": "string",
                            "description": "Recipient email or name (optional)"
                        },
                        "tone": {
                            "type": "string",
                            "description": "Desired email tone (professional, casual, friendly, etc.)"
                        },
                        "intent": {
                            "type": "string",
                            "description": "Email intent (request, follow_up, introduction, etc.)"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context information"
                        }
                    },
                    "required": ["user_id", "prompt"]
                }
            },
            
            "get_email_templates": {
                "name": "get_email_templates",
                "description": "Retrieve available email templates",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Template category (business, personal, marketing, etc.)"
                        },
                        "tone": {
                            "type": "string",
                            "description": "Template tone filter"
                        }
                    }
                }
            },
            
            "analyze_email_context": {
                "name": "analyze_email_context",
                "description": "Analyze email context and suggest improvements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "email_content": {
                            "type": "string",
                            "description": "Email content to analyze"
                        },
                        "user_id": {
                            "type": "string", 
                            "description": "User identifier"
                        }
                    },
                    "required": ["email_content", "user_id"]
                }
            },
            
            "get_user_preferences": {
                "name": "get_user_preferences",
                "description": "Get user's email preferences and settings",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        }
        
        # Register available resources
        self.resources = {
            "user://profiles": {
                "uri": "user://profiles",
                "name": "User Profiles",
                "description": "User profile information and preferences",
                "mimeType": "application/json"
            },
            
            "templates://library": {
                "uri": "templates://library", 
                "name": "Email Templates",
                "description": "Collection of email templates",
                "mimeType": "application/json"
            },
            
            "history://recent": {
                "uri": "history://recent",
                "name": "Recent Emails",
                "description": "Recently generated email history",
                "mimeType": "application/json"
            }
        }
        
        # Register available prompts
        self.prompts = {
            "compose_professional_email": {
                "name": "compose_professional_email",
                "description": "Template for composing professional emails",
                "arguments": [
                    {
                        "name": "recipient",
                        "description": "Email recipient",
                        "required": False
                    },
                    {
                        "name": "subject_area", 
                        "description": "Subject area or topic",
                        "required": True
                    },
                    {
                        "name": "urgency",
                        "description": "Urgency level (low, medium, high)",
                        "required": False
                    }
                ]
            },
            
            "compose_follow_up": {
                "name": "compose_follow_up",
                "description": "Template for follow-up emails",
                "arguments": [
                    {
                        "name": "previous_context",
                        "description": "Context of previous interaction",
                        "required": True
                    },
                    {
                        "name": "follow_up_reason",
                        "description": "Reason for following up",
                        "required": True
                    }
                ]
            }
        }
    
    async def handle_mcp_request(self, request: Dict) -> Dict:
        """
        Handle incoming MCP request.
        
        Args:
            request: MCP request dictionary
            
        Returns:
            MCP response dictionary
        """
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                return await self._handle_initialize(request_id)
            elif method == "tools/list":
                return await self._handle_tools_list(request_id)
            elif method == "tools/call":
                return await self._handle_tool_call(request_id, params)
            elif method == "resources/list":
                return await self._handle_resources_list(request_id)
            elif method == "resources/read":
                return await self._handle_resource_read(request_id, params)
            elif method == "prompts/list":
                return await self._handle_prompts_list(request_id)
            elif method == "prompts/get":
                return await self._handle_prompt_get(request_id, params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_initialize(self, request_id: str) -> Dict:
        """Handle MCP initialize request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": self.server_info,
                "capabilities": self.server_info["capabilities"]
            }
        }
    
    async def _handle_tools_list(self, request_id: str) -> Dict:
        """Handle tools list request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": list(self.tools.values())
            }
        }
    
    async def _handle_tool_call(self, request_id: str, params: Dict) -> Dict:
        """Handle tool call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
        
        try:
            if tool_name == "generate_email":
                result = await self._generate_email_tool(arguments)
            elif tool_name == "get_email_templates":
                result = await self._get_templates_tool(arguments)
            elif tool_name == "analyze_email_context":
                result = await self._analyze_context_tool(arguments)
            elif tool_name == "get_user_preferences":
                result = await self._get_preferences_tool(arguments)
            else:
                result = {"error": "Tool not implemented"}
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                }
            }
    
    async def _handle_resources_list(self, request_id: str) -> Dict:
        """Handle resources list request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": list(self.resources.values())
            }
        }
    
    async def _handle_resource_read(self, request_id: str, params: Dict) -> Dict:
        """Handle resource read request."""
        uri = params.get("uri")
        
        if uri not in self.resources:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Unknown resource: {uri}"
                }
            }
        
        try:
            if uri == "user://profiles":
                content = await self._read_user_profiles()
            elif uri == "templates://library":
                content = await self._read_template_library()
            elif uri == "history://recent":
                content = await self._read_recent_history()
            else:
                content = {"error": "Resource not implemented"}
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": self.resources[uri]["mimeType"],
                            "text": json.dumps(content, indent=2)
                        }
                    ]
                }
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Resource read error: {str(e)}"
                }
            }
    
    async def _handle_prompts_list(self, request_id: str) -> Dict:
        """Handle prompts list request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "prompts": list(self.prompts.values())
            }
        }
    
    async def _handle_prompt_get(self, request_id: str, params: Dict) -> Dict:
        """Handle prompt get request."""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if prompt_name not in self.prompts:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Unknown prompt: {prompt_name}"
                }
            }
        
        try:
            if prompt_name == "compose_professional_email":
                messages = await self._get_professional_prompt(arguments)
            elif prompt_name == "compose_follow_up":
                messages = await self._get_followup_prompt(arguments)
            else:
                messages = [{"role": "user", "content": {"type": "text", "text": "Prompt not implemented"}}]
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "description": self.prompts[prompt_name]["description"],
                    "messages": messages
                }
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Prompt error: {str(e)}"
                }
            }
    
    # Tool implementations
    async def _generate_email_tool(self, args: Dict) -> Dict:
        """Generate email using the email generator."""
        if not self.email_generator:
            return {"error": "Email generator not available"}
        
        try:
            # Call the actual email generator
            user_id = args.get("user_id")
            prompt = args.get("prompt")
            
            # Prepare context
            context = {
                "recipient": args.get("recipient"),
                "tone": args.get("tone"),
                "intent": args.get("intent"),
                **args.get("context", {})
            }
            
            # Generate email (this would call your actual generator)
            result = await self._call_email_generator(user_id, prompt, context)
            
            return {
                "email_content": result.get("email_content", ""),
                "subject": result.get("subject", ""),
                "metadata": result.get("metadata", {}),
                "generation_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Email generation failed: {str(e)}"}
    
    async def _get_templates_tool(self, args: Dict) -> Dict:
        """Get email templates."""
        try:
            category = args.get("category")
            tone = args.get("tone")
            
            # Mock template data (replace with actual template loading)
            templates = [
                {
                    "id": "prof_request",
                    "name": "Professional Request",
                    "category": "business",
                    "tone": "professional",
                    "template": "Dear [Name],\n\nI hope this email finds you well..."
                },
                {
                    "id": "casual_followup",
                    "name": "Casual Follow-up",
                    "category": "personal", 
                    "tone": "casual",
                    "template": "Hi [Name],\n\nJust wanted to follow up on..."
                }
            ]
            
            # Filter by criteria
            if category:
                templates = [t for t in templates if t["category"] == category]
            if tone:
                templates = [t for t in templates if t["tone"] == tone]
            
            return {"templates": templates}
            
        except Exception as e:
            return {"error": f"Template retrieval failed: {str(e)}"}
    
    async def _analyze_context_tool(self, args: Dict) -> Dict:
        """Analyze email context."""
        try:
            email_content = args.get("email_content", "")
            user_id = args.get("user_id")
            
            # Simple analysis (replace with actual analysis logic)
            analysis = {
                "word_count": len(email_content.split()),
                "sentiment": "neutral",  # Would use actual sentiment analysis
                "tone_detected": "professional",
                "readability_score": 8.5,
                "suggestions": [
                    "Consider adding a clear call to action",
                    "The tone is appropriate for the content"
                ],
                "user_id": user_id
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Context analysis failed: {str(e)}"}
    
    async def _get_preferences_tool(self, args: Dict) -> Dict:
        """Get user preferences."""
        try:
            user_id = args.get("user_id")
            
            # Mock preferences (replace with actual user preference loading)
            preferences = {
                "user_id": user_id,
                "default_tone": "professional",
                "signature": "Best regards,\n[Name]",
                "preferred_templates": ["prof_request", "follow_up"],
                "email_format": "html"
            }
            
            return preferences
            
        except Exception as e:
            return {"error": f"Preferences retrieval failed: {str(e)}"}
    
    # Resource implementations
    async def _read_user_profiles(self) -> Dict:
        """Read user profiles resource."""
        # Mock data (replace with actual profile loading)
        return {
            "profiles": [
                {
                    "user_id": "user1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "preferences": {"tone": "professional"}
                }
            ]
        }
    
    async def _read_template_library(self) -> Dict:
        """Read template library resource."""
        # Mock data (replace with actual template loading)
        return {
            "templates": [
                {
                    "id": "template1",
                    "name": "Business Inquiry",
                    "category": "business",
                    "content": "Professional inquiry template..."
                }
            ]
        }
    
    async def _read_recent_history(self) -> Dict:
        """Read recent email history resource."""
        # Mock data (replace with actual history loading)
        return {
            "recent_emails": [
                {
                    "id": "email1",
                    "timestamp": datetime.utcnow().isoformat(),
                    "subject": "Project Update",
                    "recipient": "team@company.com"
                }
            ]
        }
    
    # Prompt implementations
    async def _get_professional_prompt(self, args: Dict) -> List[Dict]:
        """Get professional email prompt."""
        recipient = args.get("recipient", "[Recipient]")
        subject_area = args.get("subject_area", "")
        urgency = args.get("urgency", "medium")
        
        prompt_text = f"""Compose a professional email for the following:

Recipient: {recipient}
Subject Area: {subject_area} 
Urgency Level: {urgency}

Please create an appropriate subject line and email body that is:
- Professional and courteous
- Clear and concise
- Appropriate for the urgency level
- Well-structured with proper greeting and closing"""
        
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": prompt_text
                }
            }
        ]
    
    async def _get_followup_prompt(self, args: Dict) -> List[Dict]:
        """Get follow-up email prompt."""
        previous_context = args.get("previous_context", "")
        follow_up_reason = args.get("follow_up_reason", "")
        
        prompt_text = f"""Compose a follow-up email based on:

Previous Context: {previous_context}
Follow-up Reason: {follow_up_reason}

Please create an email that:
- References the previous interaction appropriately
- Clearly states the reason for following up
- Maintains a professional but friendly tone
- Includes a clear call to action if needed"""
        
        return [
            {
                "role": "user", 
                "content": {
                    "type": "text",
                    "text": prompt_text
                }
            }
        ]
    
    async def _call_email_generator(self, user_id: str, prompt: str, context: Dict) -> Dict:
        """Call the actual email generator (placeholder)."""
        # This would integrate with your actual email generation workflow
        if self.email_generator and hasattr(self.email_generator, 'generate_email'):
            try:
                result = await self.email_generator.generate_email(
                    user_id=user_id,
                    prompt=prompt,
                    **context
                )
                return result
            except:
                pass
        
        # Fallback mock response
        return {
            "email_content": f"Generated email for: {prompt}",
            "subject": f"Re: {context.get('intent', 'Email')}",
            "metadata": {
                "user_id": user_id,
                "tone": context.get("tone", "professional"),
                "intent": context.get("intent", "general")
            }
        }


class MCPEmailClient:
    """
    MCP Client for connecting to other MCP servers.
    
    Allows the email generator to use external MCP tools and resources.
    """
    
    def __init__(self, timeout: Optional[float] = None):
        """
        Initialize MCP client.
        
        Args:
            timeout: Client timeout (uses app_settings if None)
        """
        self.connections = {}
        self.available_tools = {}
        self.available_resources = {}
        self.timeout = timeout or app_settings.mcp_client_timeout
    
    async def connect_to_server(self, server_name: str, transport_config: Dict) -> bool:
        """
        Connect to an MCP server.
        
        Args:
            server_name: Name identifier for the server
            transport_config: Transport configuration (stdio, http, etc.)
            
        Returns:
            True if connection successful
        """
        try:
            # Initialize connection based on transport type
            # This is a simplified version - actual implementation would handle
            # different transport types (stdio, HTTP, WebSocket, etc.)
            
            connection = {
                "name": server_name,
                "config": transport_config,
                "initialized": False,
                "tools": [],
                "resources": [],
                "prompts": []
            }
            
            # Send initialize request
            init_response = await self._send_request(connection, {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {
                        "name": "email-generator-mcp-client",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "roots": {"listChanged": True},
                        "sampling": {}
                    }
                }
            })
            
            if init_response.get("result"):
                connection["initialized"] = True
                
                # Get available tools
                tools_response = await self._send_request(connection, {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "tools/list"
                })
                
                if tools_response.get("result"):
                    connection["tools"] = tools_response["result"].get("tools", [])
                
                self.connections[server_name] = connection
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to connect to MCP server {server_name}: {e}")
            return False
    
    async def call_tool(
        self,
        server_name: str, 
        tool_name: str,
        arguments: Dict
    ) -> Optional[Dict]:
        """
        Call a tool on a connected MCP server.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result or None if failed
        """
        if server_name not in self.connections:
            return None
        
        connection = self.connections[server_name]
        
        try:
            response = await self._send_request(connection, {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            })
            
            return response.get("result")
            
        except Exception as e:
            print(f"Failed to call tool {tool_name} on {server_name}: {e}")
            return None
    
    async def _send_request(self, connection: Dict, request: Dict) -> Dict:
        """Send request to MCP server (placeholder implementation)."""
        # This would implement the actual transport mechanism
        # For now, return a mock response
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"status": "mock_response"}
        }


# Factory functions
def create_mcp_server(
    email_generator_instance=None,
    use_mcp: Optional[bool] = None,
    **kwargs
) -> Optional[MCPEmailServer]:
    """
    Create MCP server instance.
    
    Args:
        email_generator_instance: Instance of the main email generator
        use_mcp: Whether to enable MCP (uses app_settings if None)
        **kwargs: Additional server configuration
        
    Returns:
        MCPEmailServer instance or None if disabled
    """
    # Use settings to determine if MCP should be enabled
    use_mcp = use_mcp if use_mcp is not None else app_settings.enable_mcp
    if not use_mcp:
        return None
    
    try:
        return MCPEmailServer(email_generator_instance, **kwargs)
    except Exception as e:
        print(f"Failed to create MCP server: {e}")
        return None

def create_mcp_client(
    use_mcp: Optional[bool] = None,
    **kwargs
) -> Optional[MCPEmailClient]:
    """
    Create MCP client instance.
    
    Args:
        use_mcp: Whether to enable MCP (uses app_settings if None)
        **kwargs: Additional client configuration
        
    Returns:
        MCPEmailClient instance or None if disabled
    """
    # Use settings to determine if MCP should be enabled
    use_mcp = use_mcp if use_mcp is not None else app_settings.enable_mcp
    if not use_mcp:
        return None
    
    try:
        return MCPEmailClient(**kwargs)
    except Exception as e:
        print(f"Failed to create MCP client: {e}")
        return None