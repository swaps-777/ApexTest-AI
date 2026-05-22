from services.jira_service import get_jira_issue

issue = get_jira_issue("SCRUM-5")

print(issue)