import json

# Input JSON file containing Jira issues
INPUT_JSON_FILE = "issues.json"
OUTPUT_CSV_FILE = "status_changes.csv"

def load_issues_from_file(filename):
    """Loads issues from a JSON file"""
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
