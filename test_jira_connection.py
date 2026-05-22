import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

issue_key = "SCRUM-5"


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
    return "\n".join(line.strip() for line in "".join(text_parts).splitlines() if line.strip())


url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"

response = requests.get(
    url,
    headers={"Accept": "application/json"},
    auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN),
    timeout=30,
)

print("Status Code:", response.status_code)

if response.status_code == 200:
    data = response.json()
    fields = data["fields"]

    description_text = adf_to_text(fields.get("description"))

    print("Issue Key:", data.get("key"))
    print("Summary:", fields.get("summary"))
    print("Issue Type:", fields["issuetype"].get("name"))
    print("Status:", fields["status"].get("name"))
    print("\nDescription:")
    print(description_text)

else:
    print("Error:")
    print(response.text)