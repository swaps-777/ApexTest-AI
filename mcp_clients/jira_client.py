"""JIRA MCP client with REST API fallback for Test Cases Generator AI Agent."""

import asyncio
import json
import os
from typing import Any, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import JIRA_MCP_COMMAND, JIRA_MCP_ARGS
from services.jira_service import get_jira_issue


async def _call_get_issue_via_mcp_async(issue_key: str) -> Dict[str, Any]:
    """
    Calls the custom JIRA MCP server tool: get_issue.
    """
    server_params = StdioServerParameters(
        command=JIRA_MCP_COMMAND,
        args=JIRA_MCP_ARGS,
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "get_issue",
                arguments={"issue_key": issue_key},
            )

            if not result.content:
                return {
                    "success": False,
                    "error": "No content returned from JIRA MCP server.",
                    "source": "mcp",
                }

            first_content = result.content[0]
            print(f"[MCP Client] Received content type: {type(first_content)}", flush=True)
            print(f"[MCP Client] Has text attr: {hasattr(first_content, 'text')}", flush=True)

            if hasattr(first_content, "text"):
                response_text = first_content.text
                print(f"[MCP Client] Response text (first 200 chars): {response_text[:200]}", flush=True)
                try:
                    data = json.loads(response_text)
                    print(f"[MCP Client] Successfully parsed JSON, keys: {data.keys()}", flush=True)
                    data["source"] = "mcp"
                    return data
                except json.JSONDecodeError as e:
                    print(f"[MCP Client] JSON parse error: {e}", flush=True)
                    print(f"[MCP Client] Full response: {response_text}", flush=True)
                    return {
                        "success": False,
                        "error": f"Could not parse MCP response as JSON: {str(e)}",
                        "raw_response": response_text[:500],
                        "source": "mcp",
                    }
                except Exception as e:
                    print(f"[MCP Client] Unexpected error: {e}", flush=True)
                    return {
                        "success": False,
                        "error": f"MCP response processing failed: {str(e)}",
                        "source": "mcp",
                    }

            return {
                "success": False,
                "error": "Unexpected MCP response format.",
                "raw_response": str(first_content),
                "source": "mcp",
            }


def _call_get_issue_via_rest_fallback(issue_key: str) -> Dict[str, Any]:
    """
    Fallback: calls JIRA REST API directly using jira_service.py.
    """
    result = get_jira_issue(issue_key)
    result["source"] = "rest_fallback"
    return result


def get_issue_from_jira(issue_key: str) -> Dict[str, Any]:
    """
    Main function used by LangGraph nodes.

    First tries the JIRA MCP server.
    If MCP fails, falls back to direct JIRA REST API.
    """
    try:
        result = asyncio.run(_call_get_issue_via_mcp_async(issue_key))

        if result.get("success"):
            return result

        print(f"[JIRA MCP] Failed. Falling back to REST API. Reason: {result.get('error')}")
        return _call_get_issue_via_rest_fallback(issue_key)

    except Exception as e:
        print(f"[JIRA MCP] Exception occurred. Falling back to REST API. Reason: {e}")
        return _call_get_issue_via_rest_fallback(issue_key)
