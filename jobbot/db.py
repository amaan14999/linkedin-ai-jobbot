import sqlite3
import os
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


def insert_job(job_id: str, title: str, company: str, job_url: str) -> None:
    """
    Saves a newly discovered job to the database so we never process it again.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (job_id, title, company, job_url) VALUES (?, ?, ?, ?)",
            (job_id, title, company, job_url),
        )
        conn.commit()
