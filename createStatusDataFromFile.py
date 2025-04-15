import json
from datetime import datetime

# Input JSON file containing Jira issues
INPUT_JSON_FILE = "issues.json"
OUTPUT_CSV_FILE = "status_changes.csv"

# Define the order of statuses as a constant
STATUSES = [
    "Neu", "Specification", "Ready for development",
    "In Progress", "Re-Work", "In Code Review", "Approval", "Done", "Closed"
]
FINAL_STATUSES = {"Done", "Closed"}



class IssueStatusHistory:
    """Encapsulates the status history for an issue."""
    def __init__(self, issue_id, issue_type):
        self.issue_id = issue_id
        self.issue_type = issue_type        
        # Each status change now includes the status, change date, and time spent (initially 0)
        self.status_changes = []
        self.first_final_state = ""  # New field to store the first occurrence of a final state

    def add_status_change(self, new_status, change_date):
        """Adds a status change to the history with initial time spent set to 0."""
        self.status_changes.append((new_status, change_date, 0))  # Time spent is initially 0

    def to_csv_lines(self):
        """Converts the status changes to CSV lines."""
        # Aggregate the changes into one line
        aggregated_line = self.aggregate_changedates_into_one_line()
        # Add the issue type beneath the issue ID
        return [aggregated_line]

    def aggregate_changedates_into_one_line(self):
        """Aggregates the changes for one issue into a single line."""

        # Create a dictionary to store the first change date for each status
        status_dates = {status: "" for status in STATUSES}

        # Populate the dictionary with the first occurrence of each status
        for new_status, change_date, _ in self.status_changes:
            if new_status in status_dates and not status_dates[new_status]:
                status_dates[new_status] = change_date

            # Check if the status is a final state and update first_final_state
            if new_status in FINAL_STATUSES:
                if not self.first_final_state or datetime.strptime(change_date, "%Y-%m-%dT%H:%M:%S.%f%z") < datetime.strptime(self.first_final_state, "%Y-%m-%dT%H:%M:%S.%f%z"):
                    self.first_final_state = change_date


        # Format the dates to "YYYY-MM-DD HH:MM:SS"
        formatted_first_final_state = self.format_date(self.first_final_state)
        formatted_status_dates = [self.format_date(status_dates[status]) for status in STATUSES]

        # Build the output line
        aggregated_line = [self.issue_id, self.issue_type, formatted_first_final_state] + formatted_status_dates
        return ",".join(aggregated_line)
    
    @staticmethod
    def format_date(date_str):
        """Formats a date string from ISO 8601 to 'YYYY-MM-DD HH:MM:SS'."""
        if not date_str:
            return ""
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d %H:%M:%S")


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

def calculate_status_timespans(issue_histories):
    """Iterates over all issues in the issue_histories dictionary and calculates time spent for each status change."""
    for issue_id, issue_history in issue_histories.items():
        print(f"Issue ID: {issue_id}")
        
        # Sort status changes by change_date to ensure chronological order
        issue_history.status_changes.sort(key=lambda x: x[1])
        
        for i, status_change in enumerate(issue_history.status_changes):
            new_status, change_date, _ = status_change
            
            # Parse the change_date into a datetime object
            current_date = datetime.strptime(change_date, "%Y-%m-%dT%H:%M:%S.%f%z")
            
            # Check if there is a next status change
            if i + 1 < len(issue_history.status_changes):
                next_change_date = datetime.strptime(
                    issue_history.status_changes[i + 1][1], "%Y-%m-%dT%H:%M:%S.%f%z"
                )
                # Calculate the time difference in seconds
                time_spent = (next_change_date - current_date).total_seconds()
            else:
                # If it's the last status change, set time_spent to 0
                time_spent = 0
            
            # Update the status change with the calculated time_spent
            issue_history.status_changes[i] = (new_status, change_date, time_spent)
            
            print(f"  Status: {new_status}, Date: {change_date}, Time Spent: {time_spent} seconds")


def extract_status_changes(issues):
    """Extracts status changes from issue changelogs."""
    issue_histories = {}

    for issue in issues.get("issues", []):
        issue_id = issue["key"]
        issue_type = issue.get("fields", {}).get("issuetype", {}).get("name", "Unknown")  # Extract issue type

        # Check if the issue already exists in the dictionary
        if issue_id not in issue_histories:
            issue_histories[issue_id] = IssueStatusHistory(issue_id, issue_type)

        issue_history = issue_histories[issue_id]

        for history in issue.get("changelog", {}).get("histories", []):
            for item in history.get("items", []):
                if item["field"] == "status":
                    new_status = item["toString"]
                    change_date = history["created"]
                    issue_history.add_status_change(new_status, change_date)

    calculate_status_timespans(issue_histories)

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
        header = ["Issue-id", "Issue-type", "First final state"] + STATUSES
        file.write(",".join(header) + "\n")
        file.write("\n".join(status_changes))

    print(f"Status changes exported to '{OUTPUT_CSV_FILE}'")

if __name__ == "__main__":
    main()
