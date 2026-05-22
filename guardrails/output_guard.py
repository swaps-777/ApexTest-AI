"""Output guardrail for final generated test case pack."""

import json
from llm import llm


def check_output(answer: str) -> tuple[bool, str, str]:
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

Reject or clean:
- Fake test execution evidence
- False compliance claims
- Claims that testing was actually executed
- Secrets, passwords, API tokens, or credentials
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