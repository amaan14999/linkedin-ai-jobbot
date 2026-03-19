from jobbot.models import Job


def append_job_to_sheet(job: Job, ai_analysis: dict) -> None:
    """
    MOCK FUNCTION: Simulates pushing data to Google Sheets.
    """
    print("\n" + "=" * 50)
    print(" 📊 [MOCK SHEET INSERTION] ")
    print(f" Title:        {job.title}")
    print(f" Company:      {job.company_name}")
    print(f" URL:          {job.job_url}")
    print(f" AI Score:     {ai_analysis.get('score', 'N/A')}")
    print(f" Improvements: {ai_analysis.get('improvements', 'N/A')}")
    print("=" * 50 + "\n")
