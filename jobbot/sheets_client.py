import os
import gspread
from datetime import datetime
from jobbot.models import Job


def get_sheet():
    """Authenticates and returns the first tab of your Google Sheet."""
    try:
        credentials_path = os.path.join(os.getcwd(), "google_credentials.json")
        client = gspread.service_account(filename=credentials_path)
    except FileNotFoundError:
        print("[!] google_credentials.json not found! Cannot connect to Sheets.")
        raise
    except Exception as e:
        print(f"[!] Google Auth failed: {e}")
        raise

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID is missing from your .env file.")

    spreadsheet = client.open_by_key(sheet_id)
    sheet = spreadsheet.sheet1

    # --- AUTOMATIC HEADER CHECK ---
    # Fetch the very first row to see if it has data
    first_row = sheet.row_values(1)
    expected_headers = [
        "Date Found",
        "Job Title",
        "Company",
        "AI Score",
        "Resume Improvements",
        "Link",
    ]
    # If the sheet is totally empty, OR if the first row doesn't contain our expected title
    if not first_row or "Job Title" not in first_row:
        # Insert the headers at the very top, pushing any existing data down to row 2
        sheet.insert_row(expected_headers, index=1)
        sheet.format("A1:F1", {"textFormat": {"bold": True}})
        print("    -> [INFO] Configured sheet with column headers.")

    return sheet


def append_job_to_sheet(job: Job, ai_analysis: dict) -> None:
    """
    Appends a new row to the master Google Sheet.
    """
    try:
        sheet = get_sheet()

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        new_row = [
            current_time,
            job.title,
            job.company_name,
            ai_analysis.get("score", "N/A"),
            ai_analysis.get("improvements", "N/A"),
            job.job_url,
        ]

        sheet.append_row(new_row)
        print(f"    -> [SUCCESS] Saved '{job.title}' to Google Sheets.")

    except Exception as e:
        print(f"    -> [!] Failed to save to Google Sheets: {e}")
