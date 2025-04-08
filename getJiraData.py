import requests
import json

# Jira Configuration
JIRA_INSTANCE = "https://your-jira-instance.atlassian.net"
BOARD_ID = "your-board-id"
USERNAME = "your-email@example.com"
API_TOKEN = "your-api-token"

# API URL with JQL to filter issues updated in the last 6 months
JQL_QUERY = "updated>=-26w"
API_URL = f"{JIRA_INSTANCE}/rest/agile/1.0/board/{BOARD_ID}/issue"
#GET https://brunata.atlassian.net/rest/agile/1.0/board/28/issue?jql=updated>=-26w&expand=changelog&startAt=0&maxResults=100

# Headers for authentication
HEADERS = {
    "Accept": "application/json"
}

AUTH = (USERNAME, API_TOKEN)

def fetch_issues(start_at=0, max_results=1000):
    """Fetch issues updated in the last 6 months with changelog"""
    params = {
        "jql": JQL_QUERY,
        "expand": "changelog",
        "startAt": start_at,
        "maxResults": max_results
    }
    response = requests.get(API_URL, headers=HEADERS, auth=AUTH, params=params)
    
    if response.status_code != 200:
        print("Error fetching issues:", response.text)
        return None

    return response.json()

def extract_status_changes(issues):
    """Extracts status changes from issue changelogs"""
    status_changes = []

    for issue in issues.get("issues", []):
        issue_id = issue["key"]

        for history in issue.get("changelog", {}).get("histories", []):
            for item in history.get("items", []):
                if item["field"] == "status":
                    new_status = item["toString"]
                    change_date = history["created"]
                    status_changes.append(f"{issue_id},{new_status},{change_date}")

    return status_changes

def main():
    start_at = 0
    all_status_changes = []

    while True:
        print(f"Fetching issues starting from {start_at}...")
        issues = fetch_issues(start_at)

        if not issues or "issues" not in issues:
            break

        all_status_changes.extend(extract_status_changes(issues))

        start_at += len(issues["issues"])
        if start_at >= issues["total"]:
            break

    # Save to file
    with open("status_changes.csv", "w") as file:
        file.write("Issue-id,new status,date\n")
        file.write("\n".join(all_status_changes))

    print("Status changes exported to 'status_changes.csv'")

if __name__ == "__main__":
    main()
