"""Custom JIRA MCP server for Test Cases Generator AI Agent."""

import sys
from pathlib import Path

# Add project root to Python path so services/ can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP
from services.jira_service import get_jira_issue


mcp = FastMCP("jira-mcp-server")


@mcp.tool()
def get_issue(issue_key: str) -> dict:
    """
    Fetch a JIRA issue/story by issue key.

    Example:
    SCRUM-5
    """
    return get_jira_issue(issue_key)


if __name__ == "__main__":
    try:
        print("Starting JIRA MCP Server...", file=sys.stderr, flush=True)
        mcp.run()
    except Exception as e:
        print(f"Error running JIRA MCP server: {e}")
        sys.exit(1)