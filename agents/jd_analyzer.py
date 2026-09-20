from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, LLM

class JobRequirements(BaseModel):
    """Structured data model for job requirements."""
    title: str = Field(description="The job title")
    required_skills: List[str] = Field(description="A list of required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="A list of preferred skills")
    min_experience_years: int = Field(default=0, description="Minimum years of experience required")
    education_requirements: List[str] = Field(default_factory=list, description="List of education requirements")
    key_responsibilities: List[str] = Field(default_factory=list, description="List of key responsibilities")
    summary: str = Field(default="", description="Summary of the job description")

def create_jd_analyzer_agent(llm: LLM) -> Agent:
    """
    Creates and returns a CrewAI Agent for analyzing job descriptions.
    """
    return Agent(
        role="Job Description Analysis Expert",
        goal="Parse job descriptions to extract structured requirements for precise candidate matching",
        backstory="You are a talent acquisition strategist who understands how to decode job postings, identifying explicit and implicit requirements, with deep understanding of industry terminology.",
        llm=llm,
        verbose=True,
        memory=False,
        allow_delegation=False
    )
