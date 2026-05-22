"""JIRA subgraph for fetching and evaluating JIRA story data."""

import json

from langgraph.graph import StateGraph, END

from llm import llm
from state import TestCasesGeneratorState
from mcp_clients.jira_client import get_issue_from_jira
from guardrails.agentic_guard import check_for_jira_access


def agentic_guardrail_node(state: TestCasesGeneratorState) -> dict:
    sq = state.get("structured_query", {})
    is_safe, reason = check_for_jira_access(sq)

    if not is_safe:
        return {
            "jira_story": {"error": f"agentic guardrail blocked: {reason}"},
            "jira_story_text": "",
            "jira_score": 0.0,
        }

    # Guardrail passed — return a no-op update
    return {"jira_retries": state.get("jira_retries", 0)}


def mcp_tool_execution_node(state: TestCasesGeneratorState) -> dict:
    """
    Fetches JIRA story using MCP first.
    If MCP is unavailable, fallback REST API is used by the client.
    """
    jira_key = state.get("jira_key") or state.get("structured_query", {}).get("jira_key", "")

    result = get_issue_from_jira(jira_key)

    if not result.get("success"):
        return {
            "jira_story": result,
            "jira_story_text": "",
            "jira_score": 0.0,
            "errors": [result.get("error", "Failed to fetch JIRA issue.")],
        }

    acceptance_criteria = result.get("acceptance_criteria", [])

    story_text = f"""
JIRA Key: {result.get("key")}
Source: {result.get("source")}
Summary: {result.get("summary")}
Issue Type: {result.get("issue_type")}
Status: {result.get("status")}
Priority: {result.get("priority")}

Description:
{result.get("description")}

Acceptance Criteria:
{chr(10).join(acceptance_criteria)}
""".strip()

    return {
        "jira_story": result,
        "jira_story_text": story_text,
    }


def search_evaluation_node(state: TestCasesGeneratorState) -> dict:
    """
    Evaluates if the fetched JIRA story has enough detail to generate useful test cases.
    """
    story_text = state.get("jira_story_text", "")

    prompt = f"""You are a QA requirement quality evaluator.

Evaluate whether the following JIRA story has enough information to generate meaningful test cases.

JIRA Story:
{story_text}

Score from 0.0 to 1.0.

Scoring guide:
- 1.0 = Clear story with description and acceptance criteria
- 0.8 = Mostly clear story with enough testable details
- 0.6 = Some useful details but missing important clarity
- 0.3 = Very limited details, mostly summary only
- 0.0 = No useful story data

Respond with strict JSON only:
{{"score": 0.0, "reason": "..."}}
"""

    resp = llm.invoke(prompt).content.strip()
    resp = resp.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(resp)
        return {
            "jira_score": float(data.get("score", 0.0)),
            "jira_evaluation_reason": data.get("reason", ""),
        }
    except Exception:
        return {
            "jira_score": 0.5,
            "jira_evaluation_reason": "Could not parse JIRA evaluation response.",
        }


def build_jira_subgraph():
    """
    Builds the JIRA subgraph.

    Flow:
    agentic_guardrail -> mcp_tool_execution -> search_evaluation -> END
    """
    graph = StateGraph(TestCasesGeneratorState)

    graph.add_node("agentic_guardrail", agentic_guardrail_node)
    graph.add_node("mcp_tool_execution", mcp_tool_execution_node)
    graph.add_node("search_evaluation", search_evaluation_node)

    graph.set_entry_point("agentic_guardrail")
    graph.add_edge("agentic_guardrail", "mcp_tool_execution")
    graph.add_edge("mcp_tool_execution", "search_evaluation")
    graph.add_edge("search_evaluation", END)

    return graph.compile()