from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel


@dataclass
class Job:
    job_id: str
    job_url: str
    title: str
    company_name: str
    description: Optional[str] = None


class DimensionScores(BaseModel):
    hard_skills_match: int
    experience_level_alignment: int
    project_impact_alignment: int
    responsibility_complexity_match: int
    education_certification: int
    keywords_ats_compatibility: int


class JobAnalysis(BaseModel):
    score: int
    dimension_scores: DimensionScores
    missing_critical_skills: list[str]
    matching_strengths: list[str]
    improvements: str
