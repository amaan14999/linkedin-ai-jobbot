import sqlite3
import os
from datetime import date
from jobbot.models import Job

DB_PATH = os.getenv("DB_PATH", "data/jobs.db")


def init_db() -> None:
    """
    Creates the database file and the 'jobs' table if they don't already exist.
    Run this once when the application starts.
    """

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Table to store unique job entries
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                job_url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Table to track API usage for rate limiting
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_usage (
                date TEXT PRIMARY KEY,
                requests INTEGER DEFAULT 0
            )
        """
        )
        conn.commit()


def is_duplicate(job_id: str) -> bool:
    """
    Queries the database to see if we have already saved this job_id.
    Returns True if found, False if it is brand new.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,))
        result = cursor.fetchone()
        return result is not None


def insert_job(job: Job) -> None:
    """
    Saves a newly discovered job to the database so we never process it again.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (job_id, title, company, job_url) VALUES (?, ?, ?, ?)",
            (job.job_id, job.title, job.company_name, job.job_url),
        )
        conn.commit()


def get_daily_api_requests() -> int:
    """
    Returns the number of Gemini API calls made today. Used for rate limiting.
    """
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT requests FROM api_usage where date = ?", (today,))
        result = cursor.fetchone()
        return result[0] if result else 0


def increment_api_requests() -> None:
    """
    Increases today's API usage counter
    """
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO api_usage (date, requests) 
            VALUES (?, 1) 
            ON CONFLICT(date) DO UPDATE SET requests = requests + 1
        """,
            (today,),
        )
        conn.commit()
