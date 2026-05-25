"""Output guardrail for final generated test case pack."""

import json
import re

from llm import llm


EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.I)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD_CANDIDATE_PATTERN = re.compile(r"\b(?:\d[ -]?){13,19}\b")
SECRET_VALUE_PATTERN = re.compile(
    r"\b(api[_-]?key|secret|password|passwd|token|private[_-]?key)\b\s*[:=]\s*[\"']?[a-z0-9._~+/\-=]{8,}",
    re.I,
)
BEARER_TOKEN_PATTERN = re.compile(r"\bbearer\s+[a-z0-9._~+/\-=]{12,}\b", re.I)
PROTECTED_RELIGION_PATTERN = re.compile(
    r"\b("
    r"religion|religious affiliation|faith|caste|church|mosque|temple|synagogue|"
    r"christian|muslim|islam|hindu|sikh|jewish|buddhist|atheist"
    r")\b",
    re.I,
)
EXPLICIT_SEXUAL_PATTERN = re.compile(
    r"\b("
    r"porn|pornographic|sexual content|sexually explicit|nudity|nude|erotic|"
    r"intercourse|masturbat|genital"
    r")\b",
    re.I,
)
VIOLENT_CONTENT_PATTERN = re.compile(
    r"\b("
    r"kill|murder|suicide|self-harm|torture|bomb|shoot|stabbing|weapon|"
    r"blood|gore|graphic violence"
    r")\b",
    re.I,
)
UNSUPPORTED_CLAIM_PATTERN = re.compile(
    r"\b(testing was executed|tests were executed|verified in production|compliance certified)\b",
    re.I,
)
SAFE_TEST_EMAIL_DOMAINS = {"example.com", "example.org", "example.net", "test.com", "invalid.test"}


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
    data = _parse_guardrail_json(resp)
    if data is None:
        return True, "Output guardrail parser fallback: deterministic safety checks passed.", answer

    is_safe = bool(data.get("is_safe", False))
    cleaned_answer = str(data.get("cleaned_answer") or "")
    return (
        is_safe,
        str(data.get("reason", "")),
        cleaned_answer or answer if is_safe else cleaned_answer,
    )


def _parse_guardrail_json(raw_response: str) -> dict | None:
    response = (raw_response or "").strip()
    response = response.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(response)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    start = response.find("{")
    end = response.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(response[start : end + 1])
    except json.JSONDecodeError:
        return None

    return parsed if isinstance(parsed, dict) else None


def _deterministic_output_check(answer: str) -> tuple[bool, str, str] | None:
    content = answer or ""
    if _contains_real_email(content):
        return False, "PII detected in generated output. The response was blocked to avoid exposing personal data.", ""
    if SSN_PATTERN.search(content) or _contains_payment_card_number(content):
        return False, "PII-like numeric data detected in generated output. The response was blocked to avoid exposing personal data.", ""
    if SECRET_VALUE_PATTERN.search(content) or BEARER_TOKEN_PATTERN.search(content):
        return False, "Secret or credential-like content detected in generated output. The response was blocked.", ""
    if PROTECTED_RELIGION_PATTERN.search(content):
        return False, "Protected religious or caste-related data detected in generated output. The response was blocked.", ""
    if EXPLICIT_SEXUAL_PATTERN.search(content):
        return False, "Sexually explicit content detected in generated output. The response was blocked.", ""
    if VIOLENT_CONTENT_PATTERN.search(content):
        return False, "Violent or self-harm related content detected in generated output. The response was blocked.", ""
    if UNSUPPORTED_CLAIM_PATTERN.search(content):
        return False, "Unsupported execution or compliance claim detected. The response was blocked.", ""
    return None


def _contains_real_email(content: str) -> bool:
    for match in EMAIL_PATTERN.finditer(content):
        domain = match.group(0).rsplit("@", 1)[-1].lower().rstrip(".")
        if domain not in SAFE_TEST_EMAIL_DOMAINS:
            return True
    return False


def _contains_payment_card_number(content: str) -> bool:
    for match in CARD_CANDIDATE_PATTERN.finditer(content):
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19 and _passes_luhn_check(digits):
            return True
    return False


def _passes_luhn_check(digits: str) -> bool:
    total = 0
    reverse_digits = digits[::-1]
    for index, char in enumerate(reverse_digits):
        number = int(char)
        if index % 2 == 1:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return total % 10 == 0
