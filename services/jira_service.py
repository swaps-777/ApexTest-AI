import os
import re
import time
from urllib.parse import urlparse

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

JIRA_TIMEOUT_SECONDS = 30
JIRA_MAX_ATTEMPTS = 3
JIRA_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


def get_jira_config_status() -> dict:
    """
    Returns safe JIRA configuration status without exposing secret values.
    """
    base_url, _, _, missing = _get_jira_config()
    return {
        "JIRA_BASE_URL": bool(os.getenv("JIRA_BASE_URL")),
        "JIRA_EMAIL": bool(os.getenv("JIRA_EMAIL")),
        "JIRA_API_TOKEN": bool(os.getenv("JIRA_API_TOKEN")),
        "JIRA_BASE_HOST": urlparse(base_url).netloc if base_url else None,
        "missing": missing,
    }


def _get_jira_config() -> tuple[str | None, str | None, str | None, list[str]]:
    base_url = _normalize_jira_base_url(os.getenv("JIRA_BASE_URL"))
    email = (os.getenv("JIRA_EMAIL") or "").strip()
    api_token = (os.getenv("JIRA_API_TOKEN") or "").strip()

    missing = [
        name
        for name, value in {
            "JIRA_BASE_URL": base_url,
            "JIRA_EMAIL": email,
            "JIRA_API_TOKEN": api_token,
        }.items()
        if not value
    ]

    return base_url or None, email or None, api_token or None, missing


def _normalize_jira_base_url(raw_base_url: str | None) -> str:
    value = (raw_base_url or "").strip().strip('"').strip("'").rstrip("/")
    if not value:
        return ""

    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"

    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return value

    return f"{parsed.scheme}://{parsed.netloc}"


def _jira_headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "User-Agent": "ApexTest-Jira-MCP/1.0",
    }


def adf_to_text(adf):
    """
    Converts Atlassian Document Format into plain text.
    """
    if not adf:
        return ""

    text_parts = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                text_parts.append(node.get("text", ""))

            if node.get("type") in ["paragraph", "heading", "listItem"]:
                text_parts.append("\n")

            for child in node.get("content", []):
                walk(child)

            if node.get("type") in ["paragraph", "heading", "listItem"]:
                text_parts.append("\n")

        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(adf)
    return "\n".join(
        line.strip()
        for line in "".join(text_parts).splitlines()
        if line.strip()
    )


def extract_acceptance_criteria(description_text):
    """
    Extracts acceptance criteria from story description.
    Assumes the description contains a heading like:
    Acceptance Criteria:
    """
    if not description_text:
        return []

    pattern = r"Acceptance Criteria[:\s]*(.*)"
    match = re.search(pattern, description_text, re.IGNORECASE | re.DOTALL)

    if not match:
        return []

    ac_text = match.group(1).strip()

    lines = [
        line.strip(" -•0123456789.").strip()
        for line in ac_text.splitlines()
        if line.strip()
    ]

    return [line for line in lines if line]


def _fetch_jira_issue(url: str, email: str, api_token: str) -> requests.Response:
    last_response = None
    for attempt in range(1, JIRA_MAX_ATTEMPTS + 1):
        response = requests.get(
            url,
            headers=_jira_headers(),
            auth=HTTPBasicAuth(email, api_token),
            timeout=JIRA_TIMEOUT_SECONDS,
        )
        last_response = response

        if response.status_code not in JIRA_RETRY_STATUS_CODES:
            return response

        if attempt < JIRA_MAX_ATTEMPTS:
            retry_after = response.headers.get("Retry-After")
            delay = int(retry_after) if retry_after and retry_after.isdigit() else attempt * 2
            print(
                f"[JIRA REST] HTTP {response.status_code} from Jira. "
                f"Retrying attempt {attempt + 1}/{JIRA_MAX_ATTEMPTS} in {delay}s.",
                flush=True,
            )
            time.sleep(delay)

    return last_response


def _parse_error_response(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return text or response.reason or f"HTTP {response.status_code}"

    if isinstance(payload, dict):
        messages = []
        if payload.get("message"):
            messages.append(str(payload["message"]))
        if payload.get("errorMessages"):
            messages.extend(str(item) for item in payload["errorMessages"])
        if payload.get("errors"):
            messages.append(str(payload["errors"]))
        return "; ".join(messages) or str(payload)

    return str(payload)


def get_jira_issue(issue_key: str) -> dict:
    """
    Fetches a JIRA issue and returns clean normalized story data.
    """
    base_url, email, api_token, missing = _get_jira_config()
    if missing:
        return {
            "success": False,
            "error": (
                "Missing JIRA configuration: "
                f"{', '.join(missing)}. Set these Railway service variables and redeploy."
            ),
            "missing_config": missing,
        }

    url = f"{base_url}/rest/api/3/issue/{issue_key}"

    try:
        response = _fetch_jira_issue(url, email, api_token)
    except requests.RequestException as exc:
        return {
            "success": False,
            "error": f"Could not reach Jira at {urlparse(base_url).netloc}: {exc}",
            "jira_base_host": urlparse(base_url).netloc,
        }

    if response.status_code != 200:
        error = _parse_error_response(response)
        retryable = response.status_code in JIRA_RETRY_STATUS_CODES
        return {
            "success": False,
            "status_code": response.status_code,
            "error": (
                f"Jira returned HTTP {response.status_code} from {urlparse(base_url).netloc}: {error}"
                + (" after retrying. Check Atlassian status, Jira site URL, and Railway outbound access." if retryable else "")
            ),
            "retryable": retryable,
            "jira_base_host": urlparse(base_url).netloc,
        }

    data = response.json()
    fields = data.get("fields", {})

    description_text = adf_to_text(fields.get("description"))
    acceptance_criteria = extract_acceptance_criteria(description_text)

    return {
        "success": True,
        "key": data.get("key"),
        "summary": fields.get("summary"),
        "description": description_text,
        "acceptance_criteria": acceptance_criteria,
        "issue_type": fields.get("issuetype", {}).get("name"),
        "status": fields.get("status", {}).get("name"),
        "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
        "labels": fields.get("labels", []),
        "components": [c.get("name") for c in fields.get("components", [])],
        "url": f"{base_url}/browse/{data.get('key')}",
    }
