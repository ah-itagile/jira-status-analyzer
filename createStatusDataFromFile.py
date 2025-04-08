import json

# Input JSON file containing Jira issues
INPUT_JSON_FILE = "issues.json"
OUTPUT_CSV_FILE = "status_changes.csv"

class IssueStatusHistory:
    """Encapsulates the status history for an issue."""
    def __init__(self, issue_id):
        self.issue_id = issue_id
        # Each status change now includes the status, change date, and time spent (initially 0)
        self.status_changes = []

    def add_status_change(self, new_status, change_date):
        """Adds a status change to the history with initial time spent set to 0."""
        self.status_changes.append((new_status, change_date, 0))  # Time spent is initially 0

    def to_csv_lines(self):
        """Converts the status changes to CSV lines."""
        return [
            f"{self.issue_id},{new_status},{change_date},{time_spent}"
            for new_status, change_date, time_spent in self.status_changes
        ]


def load_issues_from_file(filename):
    """Loads issues from a JSON file."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON from '{filename}'.")
        return None

def extract_status_changes(issues):
    """Extracts status changes from issue changelogs."""
    issue_histories = {}

    for issue in issues.get("issues", []):
        issue_id = issue["key"]

        # Check if the issue already exists in the dictionary
        if issue_id not in issue_histories:
            issue_histories[issue_id] = IssueStatusHistory(issue_id)

        issue_history = issue_histories[issue_id]

        for history in issue.get("changelog", {}).get("histories", []):
            for item in history.get("items", []):
                if item["field"] == "status":
                    new_status = item["toString"]
                    change_date = history["created"]
                    issue_history.add_status_change(new_status, change_date)

    # Flatten the histories into CSV lines
    status_changes = []
    for issue_history in issue_histories.values():
        status_changes.extend(issue_history.to_csv_lines())

    return status_changes

def main():
    issues = load_issues_from_file(INPUT_JSON_FILE)
    if not issues:
        return

    status_changes = extract_status_changes(issues)

    # Save to file
    with open(OUTPUT_CSV_FILE, "w") as file:
        file.write("Issue-id,new status,date\n")
        file.write("\n".join(status_changes))

    print(f"Status changes exported to '{OUTPUT_CSV_FILE}'")

if __name__ == "__main__":
    main()
