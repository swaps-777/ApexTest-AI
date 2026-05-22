"""Specialized test-case generation agents for each requested test type."""

from __future__ import annotations

from typing import Any
import json

from llm import llm
from state import TestCasesGeneratorState


AGENT_CONFIGS: dict[str, dict[str, str]] = {
    "functional": {
        "state_key": "functional_tests",
        "title": "Functional Test Specialist",
        "focus": (
            "happy-path behavior, core user workflows, validation of every acceptance "
            "criterion, role/state variations, and business-rule alignment"
        ),
        "prefix": "FT",
    },
    "negative": {
        "state_key": "negative_tests",
        "title": "Negative Test Specialist",
        "focus": (
            "invalid inputs, missing mandatory data, unauthorized or unsupported actions, "
            "error messaging, resilience, and rule violations"
        ),
        "prefix": "NT",
    },
    "boundary": {
        "state_key": "boundary_tests",
        "title": "Boundary Test Specialist",
        "focus": (
            "minimum, maximum, just-below, just-above, empty, duplicate, length, range, "
            "limit, and state-transition boundaries"
        ),
        "prefix": "BT",
    },
    "api": {
        "state_key": "api_tests",
        "title": "API Test Specialist",
        "focus": (
            "request and response contract behavior, status codes, payload validation, "
            "authentication/authorization, idempotency, and integration edge cases"
        ),
        "prefix": "AT",
    },
    "ui": {
        "state_key": "ui_tests",
        "title": "UI Test Specialist",
        "focus": (
            "screen behavior, field states, visible feedback, accessibility cues, browser "
            "responsiveness, user interaction paths, and copy consistency"
        ),
        "prefix": "UT",
    },
    "regression": {
        "state_key": "regression_tests",
        "title": "Regression Test Specialist",
        "focus": (
            "previously working flows, cross-feature impact, smoke coverage, integration "
            "touchpoints, release confidence, and high-risk retest scenarios"
        ),
        "prefix": "RT",
    },
}


def _requested_test_types(state: TestCasesGeneratorState) -> list[str]:
    sq = state.get("structured_query", {})
    requested = sq.get("test_types") or ["functional", "negative", "boundary", "api", "ui"]
    return [test_type for test_type in requested if test_type in AGENT_CONFIGS]


def _extract_json_array(raw_response: str) -> list[dict[str, Any]]:
    response = raw_response.strip()
    response = response.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(response)
    except Exception:
        return []

    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]

    if isinstance(parsed, dict) and isinstance(parsed.get("test_cases"), list):
        return [item for item in parsed["test_cases"] if isinstance(item, dict)]

    return []


def _generate_for_type(state: TestCasesGeneratorState, test_type: str) -> list[dict[str, Any]]:
    config = AGENT_CONFIGS[test_type]
    sq = state.get("structured_query", {})
    jira_story_text = state.get("jira_story_text", "")
    rag_context = state.get("rag_context", "")
    rag_answer = state.get("rag_answer", "")

    prompt = f"""You are the {config["title"]} in a QA multi-agent system.

Generate deep, executable {test_type} test cases for the requested JIRA story.

Structured Query:
{json.dumps(sq, indent=2)}

JIRA Story:
{jira_story_text}

Retrieved Testing/BRD Context:
{rag_context}

RAG Guidance Summary:
{rag_answer}

Specialist Focus:
{config["focus"]}

Return strict JSON only:
[
  {{
    "id": "{config["prefix"]}-001",
    "title": "...",
    "type": "{test_type}",
    "priority": "High|Medium|Low",
    "objective": "...",
    "preconditions": ["..."],
    "test_data": ["..."],
    "steps": ["Step 1", "Step 2"],
    "expected_result": "...",
    "mapped_acceptance_criteria": ["..."],
    "rag_rationale": "...",
    "assumptions": ["..."],
    "risk": "..."
  }}
]

Rules:
- Produce 4 to 7 high-value {test_type} test cases when the story has enough detail.
- Cover each relevant acceptance criterion at least once where possible.
- Make steps concrete and executable.
- Include realistic test data ideas, but mark unavailable details as assumptions.
- Do not invent acceptance criteria.
- Do not invent API endpoints, screens, fields, roles, or integrations as facts.
- Use RAG only to improve quality and identify gaps; JIRA remains the source of truth.
- Return only JSON. No markdown or explanation.
"""

    response = llm.invoke(prompt).content
    return _extract_json_array(response)


def _agent_node(state: TestCasesGeneratorState, test_type: str) -> dict:
    state_key = AGENT_CONFIGS[test_type]["state_key"]

    if test_type not in _requested_test_types(state):
        return {state_key: []}

    return {state_key: _generate_for_type(state, test_type)}


def functional_test_agent_node(state: TestCasesGeneratorState) -> dict:
    """Generates functional test cases when requested."""
    return _agent_node(state, "functional")


def negative_test_agent_node(state: TestCasesGeneratorState) -> dict:
    """Generates negative test cases when requested."""
    return _agent_node(state, "negative")


def boundary_test_agent_node(state: TestCasesGeneratorState) -> dict:
    """Generates boundary test cases when requested."""
    return _agent_node(state, "boundary")


def api_test_agent_node(state: TestCasesGeneratorState) -> dict:
    """Generates API test cases when requested."""
    return _agent_node(state, "api")


def ui_test_agent_node(state: TestCasesGeneratorState) -> dict:
    """Generates UI test cases when requested."""
    return _agent_node(state, "ui")


def regression_test_agent_node(state: TestCasesGeneratorState) -> dict:
    """Generates regression test cases when requested."""
    return _agent_node(state, "regression")
