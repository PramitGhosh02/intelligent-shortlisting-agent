from typing import List, Dict, Any
from pydantic import BaseModel, Field
from crewai import Agent, LLM

class CandidateProfile(BaseModel):
    """Structured data model for a candidate profile."""
    name: str = Field(description="The name of the candidate")
    email: str = Field(default="", description="The email address of the candidate")
    phone: str = Field(default="", description="The phone number of the candidate")
    skills: List[str] = Field(default_factory=list, description="A list of skills possessed by the candidate")
    experience: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="A list of experiences. Each dict should have keys: title, company, duration, description"
    )
    education: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="A list of education history. Each dict should have keys: degree, institution, year"
    )
    summary: str = Field(default="", description="A brief summary of the candidate")

def create_resume_parser_agent(llm: LLM) -> Agent:
    """
    Creates and returns a CrewAI Agent for parsing resumes.
    """
    return Agent(
        role="Senior Resume Intelligence Specialist",
        goal="Extract comprehensive structured candidate information from raw resume text with high accuracy",
        backstory="You are an expert at parsing resumes across formats, extracting key information even from poorly formatted documents. You have 15+ years of HR tech experience.",
        llm=llm,
        verbose=True,
        memory=False,
        allow_delegation=False
    )
