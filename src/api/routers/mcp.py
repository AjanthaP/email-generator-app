from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import asyncio
from typing import Any, Dict

from src.integrations.mcp_integration import MCPEmailServer


class _EmailGeneratorAdapter:
    """Async adapter over our sync workflow entrypoint.

    Bridges MCP server's async tool calls to `generate_email`.
    """

    async def generate_email(self, user_id: str, prompt: str, **context: Any) -> Dict[str, Any]:
        from src.workflow.langgraph_flow import generate_email
        tone = context.get("tone") or "formal"
        length_preference = context.get("length_preference")
        developer_mode = bool(context.get("developer_mode", False))

        def _call():
            return generate_email(
                user_input=prompt,
                tone=tone,
                user_id=user_id or "default",
                developer_mode=developer_mode,
                length_preference=length_preference,
            )

        # Offload to thread to avoid blocking the event loop
        result = await asyncio.to_thread(_call)
        return {
            "email_content": result.get("final_draft", ""),
            "subject": "",
            "metadata": result.get("metadata", {}),
        }


router = APIRouter()

_mcp_server = MCPEmailServer(email_generator_instance=_EmailGeneratorAdapter())


@router.get("/mcp")
async def mcp_get_usage():
    """Human-friendly landing endpoint for MCP over HTTP.

    Browsers issue GET requests; return usage instead of 404.
    """
    return {
        "message": "MCP HTTP endpoint. Use POST JSON-RPC 2.0 to /api/mcp.",
        "examples": {
            "initialize": {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"}
            },
            "tools_list": {
                "jsonrpc": "2.0",
                "id": "2",
                "method": "tools/list"
            },
            "tools_call_generate_email": {
                "jsonrpc": "2.0",
                "id": "3",
                "method": "tools/call",
                "params": {
                    "name": "generate_email",
                    "arguments": {
                        "user_id": "default",
                        "prompt": "Follow up about the proposal.",
                        "tone": "formal",
                        "context": {"developer_mode": true, "length_preference": 120}
                    }
                }
            }
        },
        "tools_index": "/api/mcp/tools"
    }

@router.post("/mcp")
async def mcp_endpoint(request: Request):
    """JSON-RPC 2.0 endpoint to handle MCP requests over HTTP.

    Send a JSON body with fields: jsonrpc, id, method, params.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    response = await _mcp_server.handle_mcp_request(payload)
    return JSONResponse(content=response)


@router.get("/mcp/tools")
async def list_mcp_tools():
    """Convenience HTTP endpoint to inspect available tools (non-standard)."""
    return {"tools": list(_mcp_server.tools.values())}
