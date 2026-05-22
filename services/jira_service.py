import os
import re
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")


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


def get_jira_issue(issue_key: str) -> dict:
    """
    Fetches a JIRA issue and returns clean normalized story data.
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"

    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN),
        timeout=30,
    )

    if response.status_code != 200:
        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text,
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
        "url": f"{JIRA_BASE_URL}/browse/{data.get('key')}",
    }