import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from services.response_normalizer import normalize_graph_result


def test_blocked_output_does_not_expose_generated_cases():
    result = normalize_graph_result(
        {
            "jira_key": "SCRUM-5",
            "jira_story": {"key": "SCRUM-5", "source": "mcp"},
            "is_safe_input": True,
            "is_safe_output": False,
            "output_rejection_reason": "Secret or credential-like content detected.",
            "functional_tests": [
                {
                    "id": "FT-001",
                    "title": "Verify valid login",
                    "steps": ["Open login", "Submit valid credentials"],
                }
            ],
            "final_answer": "# Test Case Pack",
        }
    )

    assert result["status"] == "blocked"
    assert result["summary"]["total_cases"] == 0
    assert result["test_cases"] == []
    assert result["traceability_matrix"] == []
    assert result["coverage_summary"] == []
    assert result["debug"]["counts"]["functional"] == 1

