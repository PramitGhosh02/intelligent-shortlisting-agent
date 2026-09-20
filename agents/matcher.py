from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, LLM

class CandidateMatchResult(BaseModel):
  """Structured data model for the result of matching a candidate against job requirements."""
  candidate_name: str = Field(description="Name of the candidate")
  match_score: float = Field(description="Overall match score (0-100)")
  skills_match_pct: float = Field(description="Percentage match for skills")
  experience_match_pct: float = Field(description="Percentage match for experience")
  education_match_pct: float = Field(description="Percentage match for education")
  matched_skills: List[str] = Field(description="List of skills that match")
  missing_skills: List[str] = Field(description="List of required skills that are missing")
  strengths: List[str] = Field(description="Key strengths of the candidate for this role")
  reasoning: str = Field(description="Detailed reasoning for the match scores")

def create_matcher_agent(llm: LLM) -> Agent:
  """
  Creates and returns a CrewAI Agent for matching candidates to job requirements.
  """
  return Agent(
    role="Candidate Evaluation & Scoring Expert",
    goal="Precisely evaluate each candidate against job requirements and produce accurate match scores with detailed justification",
    backstory="You are a data-driven recruitment analyst who uses systematic evaluation frameworks, weighing technical skills (40%), experience (30%), and education (30%) to produce fair, unbiased assessments.",
    llm=llm,
    verbose=True,
    memory=False,
    allow_delegation=False
  )
