import os

from jobbot.models import Job
from jobbot import db
from jobbot import linkedin_client
from jobbot import gemini_client
from jobbot import sheets_client
from jobbot.config import load_config


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
    # Initialize DB to ensure our tables exist
    db.init_db()

    # Load your resume into memory
    resume_text = load_resume()

    cfg = load_config()
    li_cfg = cfg["linkedin"]
    min_score = cfg["app"]["min_ai_score"]

    # The Fast Sweep: Grab the lightweight job cards.
    jobs = linkedin_client.fetch_jobs(
        keywords=li_cfg["keywords"],
        location=li_cfg["location"],
        hours=hours,
        experience_levels=li_cfg["experience_levels"],
        f_WT=li_cfg["f_WT"],
        easy_apply=li_cfg["easy_apply"],
        company_ids=li_cfg["company_ids"],
        filter_out_companies=li_cfg["filter_out_companies"],
        max_results=li_cfg["results_wanted"],
    )

    if not jobs:
        print("[*] No jobs found in this cycle.")
        return

    new_jobs_count = 0

    # Process the jobs one by one
    for job in jobs:

        if db.is_duplicate(job.job_id):
            continue

        new_jobs_count += 1
        print(f"\n[+] New Job Found: {job.title} at {job.company_name}")

        print("    -> Fetching full description...")
        description = linkedin_client.fetch_description(job.job_url)
        job.description = description or "Description could not be loaded."

        print("    -> Analyzing match with Gemini...")
        ai_result = gemini_client.analyze_job_match(resume_text, job.description)
        score = ai_result.get("score", 0)

        # Only push to Google Sheets if the score is greater than 6
        if score > min_score:
            print(f"    -> High Score ({score}/10)! Saving to Google Sheets...")
            sheets_client.append_job_to_sheet(job, ai_result)
        else:
            print(f"    -> Score too low ({score}/10). Skipping sheet upload.")

        # We save it regardless of the score, so we never waste API calls grading it again.
        db.insert_job(job)

    print(
        f"\n[*] Cycle complete. Processed {new_jobs_count} new jobs out of {len(jobs)} fetched."
    )
