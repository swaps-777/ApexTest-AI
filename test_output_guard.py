import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from guardrails import output_guard
from guardrails.output_guard import _deterministic_output_check, check_output


class FakeLLMResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self, content):
        self.content = content

    def invoke(self, _prompt):
        return FakeLLMResponse(self.content)


def test_output_guard_allows_reserved_example_email_test_data():
    answer = "Test Data: registered_user@example.com with a valid password."

    result = _deterministic_output_check(answer)

    assert result is None


def test_output_guard_blocks_real_email_address():
    answer = "Test Data: swapnil@company.com should receive a notification."

    result = _deterministic_output_check(answer)

    assert result is not None
    assert result[0] is False
    assert "PII detected" in result[1]


def test_output_guard_allows_generic_auth_terms():
    answer = "Verify invalid password handling and expired authentication token messaging."

    result = _deterministic_output_check(answer)

    assert result is None


def test_output_guard_allows_synthetic_password_test_data():
    answer = "Test Data: password: Password123 for a placeholder login user."

    result = _deterministic_output_check(answer)

    assert result is None


def test_output_guard_blocks_secret_value_assignments():
    answer = "Use token=abc123456789xyz during setup."

    result = _deterministic_output_check(answer)

    assert result is not None
    assert result[0] is False
    assert "Secret" in result[1]


def test_output_guard_blocks_religious_or_caste_data():
    answer = "Test Data: customer religious affiliation is Hindu."

    result = _deterministic_output_check(answer)

    assert result is not None
    assert result[0] is False
    assert "religious" in result[1]


def test_output_guard_blocks_sexually_explicit_content():
    answer = "Generate sexually explicit validation content for the profile page."

    result = _deterministic_output_check(answer)

    assert result is not None
    assert result[0] is False
    assert "explicit" in result[1]


def test_output_guard_blocks_violent_content():
    answer = "Test Data: user threatens suicide in a support ticket."

    result = _deterministic_output_check(answer)

    assert result is not None
    assert result[0] is False
    assert "Violent" in result[1]


def test_output_guard_allows_answer_when_llm_guardrail_json_is_malformed(monkeypatch):
    answer = "# Test Case Pack\n\n- Test Case ID: FT-001"
    monkeypatch.setattr(output_guard, "llm", FakeLLM("SAFE: this output is fine"))

    is_safe, reason, cleaned_answer = check_output(answer)

    assert is_safe is True
    assert "parser fallback" in reason
    assert cleaned_answer == answer


def test_output_guard_extracts_json_from_guardrail_response_with_prose(monkeypatch):
    answer = "# Test Case Pack\n\n- Test Case ID: FT-001"
    monkeypatch.setattr(
        output_guard,
        "llm",
        FakeLLM('Here is the result:\n{"is_safe": true, "reason": "Safe", "cleaned_answer": ""}'),
    )

    is_safe, reason, cleaned_answer = check_output(answer)

    assert is_safe is True
    assert reason == "Safe"
    assert cleaned_answer == answer
