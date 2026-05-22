from state import TestCasesGeneratorState
from guardrails.input_guard import check_input
from guardrails.output_guard import check_output
from guardrails.tone_check import improve_tone
from llm import llm
import json


def input_guardrail_node(state: TestCasesGeneratorState) -> dict:
    is_safe, reason = check_input(state["user_query"])

    return {
        "is_safe_input": is_safe,
        "input_rejection_reason": reason,
    }

def reformulator_node(state: TestCasesGeneratorState) -> dict:
    prompt = f"""Extract structured intent from this test case generation query.

Query: "{state['user_query']}"

JSON only:
{{
  "jira_key": "...",
  "intent": "generate_test_cases|analyze_story|create_traceability|null",
  "test_types": ["functional", "negative", "boundary", "api", "ui"],
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
- If user asks for specific test types, include only those requested types.
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
    }

def aggregator_node(state: TestCasesGeneratorState) -> dict:
    """
    Generates final test case pack using JIRA story + RAG context.
    """
    jira_story_text = state.get("jira_story_text", "")
    rag_context = state.get("rag_context", "")
    rag_answer = state.get("rag_answer", "")
    sq = state.get("structured_query", {})
    test_types = sq.get("test_types", ["functional", "negative", "boundary", "api", "ui"])
    test_types_text = ", ".join(test_types)

    prompt = f"""You are a senior QA test designer.

Generate a high-quality test case pack using the JIRA story and retrieved testing/BRD context.

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

Generate test cases ONLY for the requested test types:
{test_types_text}

Important:
- If requested test_types contains only "negative", generate ONLY negative test cases.
- If requested test_types contains only "functional", generate ONLY functional test cases.
- If requested test_types contains only "boundary", generate ONLY boundary test cases.
- If requested test_types contains only "api", generate ONLY API test cases.
- If requested test_types contains only "ui", generate ONLY UI test cases.
- Do not generate sections for unrequested test types.
- Do not add create test cases when the user asked only for specific type of test cases.

Generate the final output in this structure:

# Test Case Pack

## 1. Story Summary

## 2. Assumptions

## 3. Requested Test Cases

Use this format for each test case:
- Test Case ID:
- Title:
- Type:
- Priority:
- Preconditions:
- Test Data:
- Steps:
- Expected Result:
- Mapped Acceptance Criteria:

## 4. Traceability Matrix

Create a simple markdown table:
| Acceptance Criteria | Test Case IDs | Coverage Status |

## 5. Coverage Summary

Mention:
- Requested test types
- Total test cases
- Acceptance criteria covered
- Any gaps
- Assumptions

Rules:
- Do not invent acceptance criteria.
- Do not invent API endpoints unless clearly marked as assumptions.
- Use JIRA story as the main source of truth.
- Use RAG context only to improve testing quality.
- Keep test cases clear and executable.
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