"""Normalize LangGraph output for the ApexTest frontend."""

from __future__ import annotations

from typing import Any


TEST_TYPE_STATE_KEYS = {
    "functional": "functional_tests",
    "negative": "negative_tests",
    "boundary": "boundary_tests",
    "api": "api_tests",
    "ui": "ui_tests",
    "regression": "regression_tests",
}


def normalize_test_case(raw_case: dict[str, Any], test_type: str, jira_ref: str) -> dict[str, Any]:
    """Return a stable UI/API shape for one generated test case."""
    return {
        "id": raw_case.get("id") or raw_case.get("test_case_id") or "",
        "jira_ref": jira_ref,
        "title": raw_case.get("title") or raw_case.get("name") or "Untitled test case",
        "type": raw_case.get("type") or test_type,
        "priority": raw_case.get("priority") or "Medium",
        "objective": raw_case.get("objective") or "",
        "preconditions": _list(raw_case.get("preconditions")),
        "test_data": _list(raw_case.get("test_data")),
        "steps": _list(raw_case.get("steps")),
        "expected_result": raw_case.get("expected_result") or raw_case.get("expected") or "",
        "mapped_acceptance_criteria": _list(raw_case.get("mapped_acceptance_criteria")),
        "rag_rationale": raw_case.get("rag_rationale") or raw_case.get("rationale") or "",
        "assumptions": _list(raw_case.get("assumptions")),
        "risk": raw_case.get("risk") or raw_case.get("risk_covered") or "",
    }


def normalize_graph_result(result: dict[str, Any]) -> dict[str, Any]:
    """Flatten graph state into the public API response contract."""
    jira_story = result.get("jira_story") or {}
    jira_key = result.get("jira_key") or jira_story.get("key") or ""
    test_cases: list[dict[str, Any]] = []
    final_answer = result.get("final_answer") or ""
    traceability_matrix = _extract_traceability_matrix(final_answer)
    coverage_summary = _extract_coverage_summary(final_answer)
    jira_score = _live_score(result.get("jira_score"), _fallback_jira_score(result, test_cases))
    rag_score = _live_score(result.get("rag_score"), _fallback_rag_score(result))

    for test_type, state_key in TEST_TYPE_STATE_KEYS.items():
        for raw_case in result.get(state_key, []) or []:
            if isinstance(raw_case, dict):
                test_cases.append(normalize_test_case(raw_case, test_type, jira_key))

    debug = {
        "structured_query": result.get("structured_query"),
        "requirement_quality_status": result.get("requirement_quality_status"),
        "requirement_quality_score": result.get("requirement_quality_score"),
        "requirement_quality_gaps": result.get("requirement_quality_gaps", []),
        "requirement_clarifying_questions": result.get("requirement_clarifying_questions", []),
        "jira_score": jira_score,
        "jira_source": jira_story.get("source") or jira_story.get("url"),
        "rag_score": rag_score,
        "score_mode": "live_response",
        "rag_sources": result.get("rag_sources", []),
        "is_safe_input": result.get("is_safe_input"),
        "is_safe_output": result.get("is_safe_output"),
        "output_rejection_reason": result.get("output_rejection_reason"),
        "errors": result.get("errors", []),
        "counts": {
            test_type: len(result.get(state_key, []) or [])
            for test_type, state_key in TEST_TYPE_STATE_KEYS.items()
        },
    }

    status = "ready"
    if result.get("is_safe_input") is False:
        status = "blocked"
    elif result.get("is_safe_output") is False:
        status = "blocked"
    elif result.get("requirement_quality_status") == "needs_clarification":
        status = "needs_clarification"
    elif result.get("errors"):
        status = "error"

    public_test_cases = test_cases if status == "ready" else []
    public_traceability_matrix = traceability_matrix if status == "ready" else []
    public_coverage_summary = coverage_summary if status == "ready" else []

    return {
        "jira_key": jira_key,
        "status": status,
        "summary": {
            "total_cases": len(public_test_cases),
            "jira_score": jira_score,
            "rag_score": rag_score,
            "score_mode": "live_response",
            "source": jira_story.get("source") or "unknown",
            "requirement_quality_status": result.get("requirement_quality_status"),
            "requirement_quality_score": result.get("requirement_quality_score"),
        },
        "test_cases": public_test_cases,
        "traceability_matrix": public_traceability_matrix,
        "coverage_summary": public_coverage_summary,
        "quality_gate": {
            "status": result.get("requirement_quality_status"),
            "score": result.get("requirement_quality_score"),
            "reason": result.get("requirement_quality_reason"),
            "gaps": result.get("requirement_quality_gaps", []),
            "clarifying_questions": result.get("requirement_clarifying_questions", []),
        },
        "final_answer": final_answer,
        "debug": debug,
    }


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _live_score(value: Any, fallback: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = fallback
    if number <= 0:
        number = fallback
    return round(max(0.0, min(1.0, number)), 2)


def _fallback_jira_score(result: dict[str, Any], test_cases: list[dict[str, Any]]) -> float:
    story = result.get("jira_story") or {}
    score = 0.25
    if story.get("summary"):
        score += 0.15
    if story.get("description"):
        score += 0.25
    if story.get("acceptance_criteria"):
        score += 0.25
    if test_cases:
        score += 0.10
    return score


def _fallback_rag_score(result: dict[str, Any]) -> float:
    context = result.get("rag_context") or ""
    sources = result.get("rag_sources") or []
    answer = result.get("rag_answer") or ""
    score = 0.20
    if context:
        score += 0.35
    if sources:
        score += 0.20
    if answer:
        score += 0.15
    return score


def _extract_traceability_matrix(markdown: str) -> list[dict[str, str]]:
    section = _extract_section(markdown, "Traceability Matrix")
    if not section:
        return []

    rows: list[dict[str, str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 4 or cells[0].lower().startswith("acceptance criteria"):
            continue
        rows.append(
            {
                "acceptance_criteria": cells[0],
                "test_case_ids": cells[1],
                "test_types": cells[2],
                "coverage_status": cells[3],
            }
        )
    return rows


def _extract_coverage_summary(markdown: str) -> list[str]:
    section = _extract_section(markdown, "Coverage Summary")
    if not section:
        return []

    summary: list[str] = []
    for line in section.splitlines():
        stripped = line.strip().strip("-").strip()
        if stripped:
            summary.append(stripped)
    return summary


def _extract_section(markdown: str, heading: str) -> str:
    lines = markdown.splitlines()
    capture = False
    captured: list[str] = []
    heading_lower = heading.lower()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            normalized = stripped.lstrip("#").strip()
            normalized = normalized.split(".", 1)[-1].strip() if "." in normalized[:4] else normalized
            if capture:
                break
            capture = normalized.lower() == heading_lower
            continue
        if capture:
            captured.append(line)

    return "\n".join(captured).strip()
