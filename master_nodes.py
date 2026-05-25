from state import TestCasesGeneratorState
from guardrails.input_guard import check_input
from guardrails.output_guard import check_output
from guardrails.tone_check import improve_tone
from llm import llm
import json


def input_guardrail_node(state: TestCasesGeneratorState) -> dict:
    is_safe, reason = check_input(state.get("raw_user_query") or state["user_query"])

    update = {
        "is_safe_input": is_safe,
        "input_rejection_reason": reason,
    }
    if not is_safe:
        update["final_answer"] = (
            "# Guardrail Blocked Request\n\n"
            f"{reason}\n\n"
            "Please submit a QA/testing request related to JIRA stories, requirements, acceptance criteria, "
            "traceability, coverage, or test-case generation. Remove PII, secrets, prompt-injection text, or unsafe payloads before retrying."
        )
    return update

def reformulator_node(state: TestCasesGeneratorState) -> dict:
    prompt = f"""Extract structured intent from this test case generation query.

Query: "{state['user_query']}"

JSON only:
{{
  "jira_key": "...",
  "intent": "generate_test_cases|analyze_story|create_traceability|null",
  "test_types": ["functional", "negative", "boundary", "api", "ui", "regression"],
  "output_format": "markdown|csv|excel|null"
}}

Rules:
- Extract jira_key from the query if present, for example SCRUM-5.
- If no JIRA key is found, jira_key should be null.
- intent should be generate_test_cases unless the user clearly asks something else.
- If user says "only negative", test_types must be ["negative"].
- If user says "only functional", test_types must be ["functional"].
- If user says "only boundary", test_types must be ["boundary"].
- If user says "only API", test_types must be ["api"].
- If user says "only UI", test_types must be ["ui"].
- If the query contains "Requested test types:", use those values as the exact test_types list.
- If user asks for specific test types, include only those requested types.
- If user says "only regression", test_types must be ["regression"].
- If user does not specify test types, use ["functional", "negative", "boundary", "api", "ui"].
- output_format should be markdown by default.
- Return JSON only. Do not include explanation.
"""

    resp = llm.invoke(prompt).content.strip()
    resp = resp.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        sq = json.loads(resp)
    except Exception:
        sq = {
            "jira_key": None,
            "intent": "generate_test_cases",
            "test_types": ["functional", "negative", "boundary", "api", "ui"],
            "output_format": "markdown",
        }

    return {
        "structured_query": sq,
        "jira_key": sq.get("jira_key"),
    }

def orchestrator_node(state: TestCasesGeneratorState) -> dict:
    sq = state.get("structured_query", {})

    test_types = sq.get("test_types") or []

    return {
        "use_jira": bool(sq.get("jira_key")),
        "use_rag": True,
        "needs_functional_tests": "functional" in test_types,
        "needs_negative_tests": "negative" in test_types,
        "needs_boundary_tests": "boundary" in test_types,
        "needs_api_tests": "api" in test_types,
        "needs_ui_tests": "ui" in test_types,
        "needs_regression_tests": "regression" in test_types,
    }


def requirement_quality_gate_node(state: TestCasesGeneratorState) -> dict:
    """Evaluates whether the JIRA story is complete enough for reliable test generation."""
    jira_story_text = state.get("jira_story_text", "")
    rag_context = state.get("rag_context", "")
    sq = state.get("structured_query", {})

    prompt = f"""You are the Requirement Quality Gate Agent for a QA test generation system.

Decide whether the JIRA story has enough complete information to generate accurate and relevant test cases.

Structured Query:
{json.dumps(sq, indent=2)}

JIRA Story:
{jira_story_text}

Retrieved RAG Context:
{rag_context}

Evaluate these dimensions:
- Clear feature/user goal
- Business rules
- Acceptance criteria
- Preconditions and user roles
- Validation/error rules
- Data constraints/boundaries
- API/UI/integration details if requested
- Ambiguities that would cause invented or inaccurate test cases

Return strict JSON only:
{{
  "status": "pass|needs_clarification",
  "score": 0.0,
  "reason": "...",
  "gaps": ["..."],
  "clarifying_questions": ["..."]
}}

Rules:
- Use "pass" only when the available JIRA story plus uploaded/static RAG context supports accurate test generation.
- Use "needs_clarification" when missing details would force test agents to invent important behavior.
- Ask concise questions addressed to the PO/BA.
- Do not ask about details already present in the JIRA story.
- If only minor implementation details are missing but executable tests can be written with explicit assumptions, pass.
"""

    response = llm.invoke(prompt).content.strip()
    response = response.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(response)
    except Exception:
        data = {
            "status": "needs_clarification",
            "score": 0.0,
            "reason": "Requirement Quality Gate could not parse the evaluation response.",
            "gaps": ["The quality gate response was not valid JSON."],
            "clarifying_questions": ["Can the PO/BA confirm the complete acceptance criteria and business rules for this story?"],
        }

    status = data.get("status", "needs_clarification")
    if status not in {"pass", "needs_clarification"}:
        status = "needs_clarification"

    questions = data.get("clarifying_questions") or []
    gaps = data.get("gaps") or []

    try:
        score = float(data.get("score", 0.0) or 0.0)
    except (TypeError, ValueError):
        score = 0.0

    return {
        "requirement_quality_status": status,
        "requirement_quality_score": score,
        "requirement_quality_reason": data.get("reason", ""),
        "requirement_quality_gaps": [str(gap) for gap in gaps],
        "requirement_clarifying_questions": [str(question) for question in questions],
    }


def clarification_response_node(state: TestCasesGeneratorState) -> dict:
    """Builds the response when the quality gate blocks test generation."""
    gaps = state.get("requirement_quality_gaps", [])
    questions = state.get("requirement_clarifying_questions", [])
    reason = state.get("requirement_quality_reason", "")
    score = state.get("requirement_quality_score", 0.0)
    jira_key = state.get("jira_key") or "the requested story"

    gap_lines = "\n".join(f"- {gap}" for gap in gaps) or "- The story does not provide enough detail for reliable generation."
    question_lines = "\n".join(f"- {question}" for question in questions) or "- Can the PO/BA provide complete acceptance criteria and business rules?"

    return {
        "aggregated_answer": f"""# Requirement Quality Gate

## Status
Test generation is paused for {jira_key}.

## Quality Score
{score:.2f}

## Reason
{reason or "The story needs clarification before accurate test cases can be generated."}

## Identified Gaps
{gap_lines}

## Clarifying Questions for PO/BA
{question_lines}

## Next Step
Update the JIRA story or upload supporting requirements, then run generation again.
""".strip(),
        "functional_tests": [],
        "negative_tests": [],
        "boundary_tests": [],
        "api_tests": [],
        "ui_tests": [],
        "regression_tests": [],
    }

def aggregator_node(state: TestCasesGeneratorState) -> dict:
    """
    Assembles the final test case pack from specialist agent outputs.
    """
    jira_story_text = state.get("jira_story_text", "")
    rag_context = state.get("rag_context", "")
    rag_answer = state.get("rag_answer", "")
    sq = state.get("structured_query", {})
    test_types = sq.get("test_types", ["functional", "negative", "boundary", "api", "ui"])
    test_types_text = ", ".join(test_types)
    specialist_outputs = {
        "functional": state.get("functional_tests", []),
        "negative": state.get("negative_tests", []),
        "boundary": state.get("boundary_tests", []),
        "api": state.get("api_tests", []),
        "ui": state.get("ui_tests", []),
        "regression": state.get("regression_tests", []),
    }
    requested_specialist_outputs = {
        test_type: specialist_outputs.get(test_type, [])
        for test_type in test_types
        if test_type in specialist_outputs
    }

    prompt = f"""You are a senior QA test lead assembling a final test case pack.

The detailed test cases were produced by specialized test-type agents. Your job is to format,
deduplicate, deepen any thin wording without changing facts, and create traceability/coverage
sections. Do not replace specialist coverage with a generic test list.

Structured Query:
{json.dumps(sq, indent=2)}

Requested Test Types:
{test_types_text}

JIRA Story:
{jira_story_text}

Retrieved Testing/BRD Context:
{rag_context}

RAG Guidance Summary:
{rag_answer}

Specialist Agent Outputs:
{json.dumps(requested_specialist_outputs, indent=2)}

Important:
- Include ONLY the requested test types: {test_types_text}.
- Preserve the specialist agent intent, IDs, mapped acceptance criteria, assumptions, and risk notes.
- If a specialist returned no cases for a requested type, include a short gap note for that type.
- Do not generate sections for unrequested test types.
- Do not create a test type the user did not request.

Generate the final output in this structure:

# Test Case Pack

## 1. Story Summary

## 2. Assumptions

## 3. Specialist Test Cases

Use this format for each test case:
- Test Case ID:
- Title:
- Type:
- Priority:
- Objective:
- Preconditions:
- Test Data:
- Steps:
- Expected Result:
- Mapped Acceptance Criteria:
- RAG/BRD Rationale:
- Risk Covered:

## 4. Traceability Matrix

Create a markdown table:
| Acceptance Criteria | Test Case IDs | Test Types | Coverage Status |

## 5. Coverage Summary

Mention:
- Requested test types
- Total test cases
- Acceptance criteria covered
- Any gaps
- Assumptions
- Risks covered

Rules:
- Do not invent acceptance criteria.
- Do not invent API endpoints unless clearly marked as assumptions.
- Use JIRA story as the main source of truth.
- Use RAG context only to improve testing quality.
- Keep test cases detailed, clear, and executable.
- Use concise professional markdown.
"""

    final_test_pack = llm.invoke(prompt).content.strip()

    return {
        "aggregated_answer": final_test_pack,
    }

def output_guardrail_node(state: TestCasesGeneratorState) -> dict:
    answer = state.get("aggregated_answer", "")

    is_safe, reason, cleaned_answer = check_output(answer)

    if not is_safe:
        return {
            "is_safe_output": False,
            "output_rejection_reason": reason,
            "final_answer": (
                "The generated test case pack could not be safely returned. "
                f"Reason: {reason}"
            ),
        }

    return {
        "is_safe_output": True,
        "output_rejection_reason": reason,
        "aggregated_answer": cleaned_answer or answer,
    }

def tone_node(state: TestCasesGeneratorState) -> dict:
    answer = state.get("aggregated_answer") or state.get("final_answer", "")

    polished_answer = improve_tone(answer)

    return {
        "final_answer": polished_answer,
    }
