"""Output guardrail for final generated test case pack."""

import json
import re

from llm import llm


OUTPUT_BLOCK_PATTERNS = [
    (
        re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.I),
        "PII detected in generated output. The response was blocked to avoid exposing personal data.",
    ),
    (
        re.compile(r"\b(?:\+?\d[\s-]?){10,16}\b"),
        "PII-like numeric data detected in generated output. The response was blocked to avoid exposing personal data.",
    ),
    (
        re.compile(r"\b(api[_-]?key|secret|password|passwd|token|private[_-]?key|bearer\s+[a-z0-9._-]+)\b", re.I),
        "Secret or credential-like content detected in generated output. The response was blocked.",
    ),
    (
        re.compile(r"\b(testing was executed|tests were executed|verified in production|compliance certified)\b", re.I),
        "Unsupported execution or compliance claim detected. The response was blocked.",
    ),
]


def check_output(answer: str) -> tuple[bool, str, str]:
    deterministic_result = _deterministic_output_check(answer)
    if deterministic_result is not None:
        return deterministic_result

    prompt = f"""You are an output safety and quality guardrail for a Test Cases Generator AI Agent.

The agent generates test cases from JIRA stories, acceptance criteria, and RAG-based testing/BRD context.

Review the final answer below.

Final Answer:
{answer}

Check whether the final answer is safe, grounded, and suitable.

Allow:
- Test cases based on JIRA story and acceptance criteria
- Clearly marked assumptions
- Functional, negative, boundary, API, UI, regression, security, and accessibility test ideas
- Traceability matrix
- Coverage summary
- Requirement quality gate clarifying questions

Reject or clean:
- Fake test execution evidence
- False compliance claims
- Claims that testing was actually executed
- Secrets, passwords, API tokens, or credentials
- PII or personal data
- Destructive instructions
- Unsupported API endpoints presented as facts
- Invented acceptance criteria presented as facts
- Unsafe hacking or exploit instructions

Respond with strict JSON only:
{{
  "is_safe": true|false,
  "reason": "...",
  "cleaned_answer": "..."
}}

Rules:
- If the answer is safe, return it unchanged in cleaned_answer.
- If the answer has minor issues, clean it and return is_safe as true.
- If the answer is unsafe and cannot be cleaned, return is_safe as false.
- Do not include markdown outside JSON.
"""

    resp = llm.invoke(prompt).content.strip()
    resp = resp.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(resp)
        return (
            bool(data.get("is_safe", False)),
            str(data.get("reason", "")),
            str(data.get("cleaned_answer", "")),
        )
    except Exception:
        return False, "Could not parse output guardrail response.", ""


def _deterministic_output_check(answer: str) -> tuple[bool, str, str] | None:
    content = answer or ""
    for pattern, reason in OUTPUT_BLOCK_PATTERNS:
        if pattern.search(content):
            return False, reason, ""
    return None
