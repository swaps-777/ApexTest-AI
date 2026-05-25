import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from guardrails.output_guard import _deterministic_output_check


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


def test_output_guard_blocks_secret_value_assignments():
    answer = "Use token=abc123456789xyz during setup."

    result = _deterministic_output_check(answer)

    assert result is not None
    assert result[0] is False
    assert "Secret" in result[1]
