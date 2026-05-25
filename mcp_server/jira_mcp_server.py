"""Custom JIRA MCP server for Test Cases Generator AI Agent."""

import sys
import json
from pathlib import Path

# Add project root to Python path so services/ can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print(f"[MCP] Project root: {PROJECT_ROOT}", file=sys.stderr, flush=True)
print(f"[MCP] Python path: {sys.path[:3]}", file=sys.stderr, flush=True)

try:
    from mcp.server.fastmcp import FastMCP
    from services.jira_service import get_jira_issue
    print("[MCP] Successfully imported FastMCP and jira_service", file=sys.stderr, flush=True)
except ImportError as e:
    print(f"[MCP] Import error: {e}", file=sys.stderr, flush=True)
    sys.exit(1)


mcp = FastMCP("jira-mcp-server")


@mcp.tool()
def get_issue(issue_key: str) -> dict:
    """
    Fetch a JIRA issue/story by issue key.

    Example:
    SCRUM-5
    """
    try:
        result = get_jira_issue(issue_key)
        # Ensure result is JSON-serializable
        return json.loads(json.dumps(result))
    except Exception as e:
        print(f"[MCP] Error fetching issue {issue_key}: {e}", file=sys.stderr, flush=True)
        return {
            "success": False,
            "error": str(e),
            "issue_key": issue_key
        }


if __name__ == "__main__":
    try:
        print("[MCP] Starting JIRA MCP Server...", file=sys.stderr, flush=True)
        mcp.run()
    except Exception as e:
        print(f"[MCP] Error running JIRA MCP server: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)