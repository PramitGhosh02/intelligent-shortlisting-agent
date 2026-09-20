from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, LLM

class CandidateReportEntry(BaseModel):
    """Structured data model for a single candidate's report entry."""
    candidate_id: int = Field(description="The unique integer ID of the candidate provided in the prompt")
    rank: int = Field(description="Rank of the candidate in the shortlist")
    candidate_name: str = Field(description="Name of the candidate")
    match_score: float = Field(description="Match score of the candidate")
    recommendation: str = Field(description="Recommendation: Strongly Recommended, Recommended, Consider, or Not Recommended")
    summary: str = Field(description="Summary of the candidate's profile and match")
    strengths: List[str] = Field(default_factory=list, description="Top 3 key strengths")
    skill_gaps: List[str] = Field(default_factory=list, description="Key skill gaps")
    email: str = Field(description="The candidate's email address extracted from their resume, or 'Not available'")
    email_draft: str = Field(description="A draft email to send to the candidate or hiring manager")

class ShortlistReport(BaseModel):
    """Structured data model for the final shortlisting report."""
    job_title: str = Field(description="The job title for the shortlist")
    total_candidates: int = Field(description="Total number of candidates evaluated")
    shortlisted_count: int = Field(description="Number of candidates shortlisted")
    candidates: List[CandidateReportEntry] = Field(description="List of shortlisted candidates")
    executive_summary: str = Field(description="An executive summary of the shortlisting process and results")

def create_report_writer_agent(llm: LLM) -> Agent:
    """
    Creates and returns a CrewAI Agent for writing recruitment reports.
    """
    return Agent(
        role="Executive Recruitment Report Writer",
        goal="Compile comprehensive shortlisting reports with clear rankings, recommendations, and professional communication drafts",
        backstory="You are a senior recruitment communications specialist who creates executive-level talent acquisition reports. Expert at distilling complex evaluations into clear, actionable recommendations.",
        llm=llm,
        verbose=True,
        memory=False,
        allow_delegation=False
    )
