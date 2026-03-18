import os

from jobbot.models import Job
from jobbot import db
from jobbot import linkedin_client
from jobbot import gemini_client
from jobbot import sheets_client


def load_resume() -> str:
    """Helper function to load your base resume from the text file."""
    try:
        with open("my_resume.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("[!] my_resume.txt not found. Please create it in the root folder.")
        return "Resume not provided."


def run_cycle(hours: int) -> None:
    """
    The main workflow: Scrape -> Filter -> Fetch Text -> Analyze -> Save.
    """
    # 1. Initialize DB to ensure our tables exist
    db.init_db()

    # 2. Load your resume into memory
    resume_text = load_resume()

    # 3. The Fast Sweep: Grab the lightweight job cards.
    # We are plugging in your specific targets here.
    jobs = linkedin_client.fetch_jobs(
        keywords="software engineer",
        location="Bengaluru",
        hours=hours,
        experience_levels="2",
        filter_out_companies=[
            "Wipro",
            "Infosys",
            "Turing",
            "Accenture services Pvt Ltd",
        ],
    )

    if not jobs:
        print("[*] No jobs found in this cycle.")
        return

    new_jobs_count = 0

    # 4. Process the jobs one by one
    for job in jobs:
        # THE FILTER: If we already saw this Job ID, skip it instantly.
        if db.is_duplicate(job.job_id):
            continue

        new_jobs_count += 1
        print(f"\n[+] New Job Found: {job.title} at {job.company_name}")

        # THE HEAVY LIFT: Now that we know it's new, fetch the massive description text.
        print("    -> Fetching full description...")
        description = linkedin_client.fetch_description(job.job_url)
        job.description = description or "Description could not be loaded."

        # THE AI ANALYSIS: Ask Gemini to grade the match
        print("    -> Analyzing match with Gemini...")
        ai_result = gemini_client.analyze_job_match(resume_text, job.description)

        # Extract the score (default to 0 if something went wrong)
        score = ai_result.get("score", 0)

        # THE SAVE: Only push to Google Sheets if the score is greater than 6
        if score > 6:
            print(f"    -> High Score ({score}/10)! Saving to Google Sheets...")
            sheets_client.append_job_to_sheet(job, ai_result)
        else:
            print(f"    -> Score too low ({score}/10). Skipping sheet upload.")

        # Finally, record this job in our SQLite database.
        # We save it regardless of the score, so we never waste API calls grading it again.
        db.insert_job(job.job_id, job.title, job.company_name, job.job_url)

    print(
        f"\n[*] Cycle complete. Processed {new_jobs_count} new jobs out of {len(jobs)} fetched."
    )
