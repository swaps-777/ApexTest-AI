import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from services import jira_service


class FakeResponse:
    def __init__(self, status_code, payload=None, text="", reason=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.reason = reason
        self.headers = {}

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def test_normalize_jira_base_url_strips_copied_page_path():
    assert (
        jira_service._normalize_jira_base_url("https://team.atlassian.net/jira/software/projects/SCRUM")
        == "https://team.atlassian.net"
    )


def test_get_jira_issue_retries_transient_503(monkeypatch):
    calls = []
    responses = [
        FakeResponse(503, {"message": "", "status": 503}),
        FakeResponse(
            200,
            {
                "key": "SCRUM-5",
                "fields": {
                    "summary": "Sample story",
                    "description": None,
                    "issuetype": {"name": "Story"},
                    "status": {"name": "To Do"},
                    "priority": {"name": "Medium"},
                    "labels": [],
                    "components": [],
                },
            },
        ),
    ]

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return responses.pop(0)

    monkeypatch.setenv("JIRA_BASE_URL", "team.atlassian.net/jira/software")
    monkeypatch.setenv("JIRA_EMAIL", "qa@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "fake-token")
    monkeypatch.setattr(jira_service.requests, "get", fake_get)
    monkeypatch.setattr(jira_service.time, "sleep", lambda _: None)

    result = jira_service.get_jira_issue("SCRUM-5")

    assert result["success"] is True
    assert result["key"] == "SCRUM-5"
    assert len(calls) == 2
    assert calls[0][0] == "https://team.atlassian.net/rest/api/3/issue/SCRUM-5"
    assert calls[0][1]["headers"]["User-Agent"] == "ApexTest-Jira-MCP/1.0"


def test_get_jira_issue_returns_clear_error_after_503(monkeypatch):
    monkeypatch.setenv("JIRA_BASE_URL", "https://team.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "qa@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "fake-token")
    monkeypatch.setattr(
        jira_service.requests,
        "get",
        lambda *_, **__: FakeResponse(503, {"message": "", "status": 503}),
    )
    monkeypatch.setattr(jira_service.time, "sleep", lambda _: None)

    result = jira_service.get_jira_issue("SCRUM-5")

    assert result["success"] is False
    assert result["status_code"] == 503
    assert result["retryable"] is True
    assert "team.atlassian.net" in result["error"]

