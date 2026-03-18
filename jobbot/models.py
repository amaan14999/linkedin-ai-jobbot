from dataclasses import dataclass
from typing import Optional


@dataclass
class Job:
    job_id: str
    job_url: str
    title: str
    company_name: str
    description: Optional[str] = None
