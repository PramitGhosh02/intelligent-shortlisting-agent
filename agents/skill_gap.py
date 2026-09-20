from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, LLM

class SkillGapReport(BaseModel):
  """Structured data model for identifying skill gaps."""
  candidate_name: str = Field(description="Name of the candidate")
  missing_critical_skills: List[str] = Field(description="List of missing critical skills")
  missing_preferred_skills: List[str] = Field(description="List of missing preferred skills")
  experience_gaps: List[str] = Field(description="Description of experience gaps")
  upskilling_recommendations: List[str] = Field(description="Actionable recommendations for upskilling")
  overall_gap_assessment: str = Field(description="Overall assessment: Minor, Moderate, or Significant")

def create_skill_gap_agent(llm: LLM) -> Agent:
  """
  Creates and returns a CrewAI Agent for identifying skill gaps.
  """
  return Agent(
    role="Talent Development & Skill Gap Advisor",
    goal="Identify precise skill gaps and provide actionable development recommendations for each candidate",
    backstory="You are a workforce development specialist who helps organizations understand not just what candidates lack, but how quickly they could bridge those gaps. Experience in L&D and talent development.",
    llm=llm,
    verbose=True,
    memory=False,
    allow_delegation=False
  )
