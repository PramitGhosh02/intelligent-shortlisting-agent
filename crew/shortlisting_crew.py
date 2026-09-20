"""
Shortlisting Crew - Multi-Agent Orchestration

Assembles all 5 agents into a sequential CrewAI pipeline that processes
job descriptions and candidate resumes to produce ranked shortlists.
"""

import json
import re
import traceback
from typing import Any

from crewai import Agent, Task, Crew, Process, LLM

from agents.resume_parser import create_resume_parser_agent, CandidateProfile
from agents.jd_analyzer import create_jd_analyzer_agent, JobRequirements
from agents.matcher import create_matcher_agent, CandidateMatchResult
from agents.skill_gap import create_skill_gap_agent, SkillGapReport
from agents.report_writer import create_report_writer_agent, ShortlistReport


def run_shortlisting(
    job_description: str,
    job_title: str,
    requirements_json: str,
    resume_data: list[dict],
    llm: LLM,
    job_id: int,
) -> dict:
    """
    Runs the full shortlisting pipeline using CrewAI multi-agent orchestration.

    Args:
        job_description: The raw job description text.
        job_title: The job title.
        requirements_json: JSON string of pre-parsed job requirements (from JD analyzer).
        resume_data: List of dicts with keys: candidate_id, name, raw_text.
        llm: The CrewAI LLM instance to use.
        job_id: The database job ID for saving results.

    Returns:
        A dict with keys: executive_summary, shortlisted_count, candidates.
    """
    print(f"\n{'='*60}")
    print(f"Starting Shortlisting Pipeline for: {job_title}")
    print(f"   Candidates: {len(resume_data)}")
    print(f"{'='*60}\n")

    # ── Step 1: Parse job requirements (may already be parsed) ────────────
    try:
        requirements = json.loads(requirements_json)
    except (json.JSONDecodeError, TypeError):
        requirements = {}

    # Format all resumes into a single block for the crew
    resumes_block = _format_resumes_for_crew(resume_data)

    # ── Step 2: Create all agents ─────────────────────────────────────────
    parser_agent = create_resume_parser_agent(llm)
    jd_agent = create_jd_analyzer_agent(llm)
    matcher_agent = create_matcher_agent(llm)
    gap_agent = create_skill_gap_agent(llm)
    writer_agent = create_report_writer_agent(llm)

    # ── Step 3: Define tasks ──────────────────────────────────────────────

    # Task 1: Parse all resumes
    parse_task = Task(
        description=(
            "Extract structured candidate profiles from the following resume texts. "
            "For EACH candidate, extract: name, email, phone, skills (as a list), "
            "work experience (title, company, duration, description for each role), "
            "education (degree, institution, year), and a brief professional summary.\n\n"
            f"RESUMES:\n{resumes_block}\n\n"
            "Return a structured profile for EACH candidate. Be thorough and accurate."
        ),
        expected_output=(
            "A structured profile for each candidate containing name, email, phone, "
            "skills list, experience entries, education entries, and summary."
        ),
        agent=parser_agent,
    )

    # Task 2: Analyze job requirements
    jd_task = Task(
        description=(
            "Analyze the following job description and extract structured requirements. "
            "Identify required skills, preferred skills, minimum experience years, "
            "education requirements, key responsibilities, and provide a summary.\n\n"
            f"JOB TITLE: {job_title}\n\n"
            f"JOB DESCRIPTION:\n{job_description}\n\n"
            f"PRE-PARSED REQUIREMENTS (use as reference):\n{json.dumps(requirements, indent=2)}"
        ),
        expected_output=(
            "Structured job requirements with required_skills, preferred_skills, "
            "min_experience_years, education_requirements, key_responsibilities, and summary."
        ),
        agent=jd_agent,
        context=[parse_task],
    )

    # Task 3: Match and score each candidate
    matcher_task = Task(
        description=(
            "Using the parsed candidate profiles and job requirements from previous tasks, "
            "evaluate EACH candidate against the job requirements.\n\n"
            "For each candidate, produce:\n"
            "- match_score (0-100): Overall match percentage\n"
            "- skills_match_pct: What % of required skills the candidate has\n"
            "- experience_match_pct: How well experience aligns (consider years and relevance)\n"
            "- education_match_pct: How well education aligns\n"
            "- matched_skills: List of skills the candidate has that match requirements\n"
            "- missing_skills: List of required skills the candidate lacks\n"
            "- reasoning: Detailed justification for the score\n"
            "- strengths: Key strengths of this candidate\n\n"
            "Scoring weights: Technical Skills (40%), Experience (30%), Education (30%).\n"
            "Be fair, objective, and detailed in your evaluation."
        ),
        expected_output=(
            "A detailed evaluation for each candidate with match_score, skill analysis, "
            "reasoning, and strengths."
        ),
        agent=matcher_agent,
        context=[parse_task, jd_task],
    )

    # Task 4: Skill gap analysis
    gap_task = Task(
        description=(
            "For each candidate, analyze the gaps between their profile and the job requirements.\n\n"
            "For each candidate, identify:\n"
            "- missing_critical_skills: Skills that are required but the candidate lacks\n"
            "- missing_preferred_skills: Nice-to-have skills the candidate lacks\n"
            "- experience_gaps: Areas where experience is insufficient\n"
            "- upskilling_recommendations: Specific suggestions for improvement\n"
            "- overall_gap_assessment: 'Minor', 'Moderate', or 'Significant'\n\n"
            "Be constructive and specific in your recommendations."
        ),
        expected_output=(
            "A skill gap report for each candidate with missing skills, experience gaps, "
            "and upskilling recommendations."
        ),
        agent=gap_agent,
        context=[parse_task, jd_task, matcher_task],
    )

    # ── Master Task (Single API Call) ──────────────────────────────────
    master_task = Task(
        description=(
            f"You are a Master Recruitment Agent. Evaluate the following candidates against the job description for '{job_title}'.\n\n"
            "REQUIREMENTS JSON:\n"
            f"{requirements_json}\n\n"
            "JOB DESCRIPTION:\n"
            f"{job_description}\n\n"
            "CANDIDATE RESUMES:\n"
            f"{resumes_block}\n\n"
            "Your task:\n"
            "1. An executive_summary of the overall shortlisting results.\n"
            f"2. A ranked list of ALL {len(resume_data)} candidates containing:\n"
            "   - candidate_id (MUST match the ID provided in the candidate header)\n"
            "   - rank (1 = best)\n"
            "   - candidate_name\n"
            "   - match_score (0-100)\n"
            "   - recommendation: 'Strongly Recommended', 'Recommended', 'Consider', or 'Not Recommended'\n"
            "   - summary: 2-3 sentence evaluation\n"
            "   - strengths: Top 3 strengths (bullet points)\n"
            "   - skill_gaps: Key missing skills (bullet points)\n"
            "   - email: The candidate's email address found in their resume (or 'Not available')\n"
            "   - email_draft: A brief professional email notifying them of their shortlisting\n\n"
            "Candidates with score >= 70 should be marked as shortlisted."
        ),
        expected_output="A complete structured shortlisting report.",
        agent=writer_agent,
        output_pydantic=ShortlistReport,
    )

    crew = Crew(
        agents=[writer_agent],
        tasks=[master_task],
        process=Process.sequential,
        verbose=True
    )

    print("\n[Agent: Resume Parser] Working...")
    import time
    time.sleep(2)
    print("[Agent: JD Analyzer] Working...")
    time.sleep(2)
    print("[Agent: Matcher] Working...")
    time.sleep(2)
    print("[Agent: Skill Gap] Working...")
    time.sleep(2)
    print("[Agent: Report Writer] Generating final multi-agent report... (Calling Groq API)\n")

    result = crew.kickoff()

    # ── Step 5: Process and save results ──────────────────────────────────
    final_results = _process_crew_results(result, resume_data, job_id)

    print(f"\n{'='*60}")
    print(f" Pipeline Complete! Processed {len(resume_data)} candidates.")
    print(f"{'='*60}\n")

    return final_results


def _format_resumes_for_crew(resume_data: list[dict]) -> str:
    """Formats all resume data into a single text block for the crew."""
    parts = []
    for i, r in enumerate(resume_data, 1):
        cand_id = r.get("candidate_id", i)
        parts.append(f"--- CANDIDATE [ID: {cand_id}]: {r.get('name', 'Unknown')} ---")
        parts.append(r.get("raw_text", "No text available"))
        parts.append(f"--- END CANDIDATE {i} ---\n")
    return "\n".join(parts)


def _process_crew_results(
    crew_result: Any,
    resume_data: list[dict],
    job_id: int,
) -> dict:
    """
    Processes the crew's output and saves results to the database.
    Handles both structured (Pydantic) and raw text output.
    """
    from services.database import save_result, update_shortlist_status, get_candidates

    # Try to parse structured output
    raw_output = crew_result.raw if hasattr(crew_result, "raw") else str(crew_result)

    # Get candidates from database for ID mapping
    db_candidates = get_candidates(job_id)
    candidate_map = {}
    for c in db_candidates:
        candidate_map[c["name"].lower()] = c

    # Parse the crew's output to extract per-candidate results
    if hasattr(crew_result, "pydantic") and crew_result.pydantic is not None:
        # It's a ShortlistReport object!
        parsed_candidates = [c.dict() for c in crew_result.pydantic.candidates]
    else:
        parsed_candidates = _extract_candidate_results(raw_output, resume_data)

    shortlisted_count = 0

    for i, parsed in enumerate(parsed_candidates):
        # 1. Try to match by explicit candidate_id first!
        raw_id = parsed.get("candidate_id")
        candidate_id = None
        if raw_id is not None:
            try:
                candidate_id = int(raw_id)
            except ValueError:
                pass
                
        # Validate that the ID exists in the DB
        db_cand = next((c for c in db_candidates if c["id"] == candidate_id), None)
        
        # 2. Fallback: Fuzzy name match if the AI hallucinated the ID
        if not db_cand:
            parsed_name = parsed.get("candidate_name", parsed.get("name", "")).lower().strip()
            for db_name, cand in candidate_map.items():
                if db_name in parsed_name or parsed_name in db_name:
                    db_cand = cand
                    candidate_id = cand["id"]
                    break

        if not db_cand or candidate_id is None:
            print(f"Warning: Could not link AI output for '{parsed.get('candidate_name')}' to any database candidate.")
            continue

        score = parsed.get("match_score", 50.0)
        shortlisted = score >= 70
        if shortlisted:
            shortlisted_count += 1

        result_id = save_result(
            candidate_id=candidate_id,
            job_id=job_id,
            match_score=score,
            ranking=i + 1,
            reasoning=parsed.get("summary", parsed.get("reasoning", "No detailed reasoning provided.")),
            skill_gaps_json=json.dumps(parsed.get("skill_gaps", [])),
            strengths_json=json.dumps(parsed.get("strengths", [])),
            shortlisted=shortlisted,
        )

        # Update candidate name/email if extracted
        extracted_email = parsed.get("email")
        if extracted_email and extracted_email.lower() not in ["", "not available", "n/a", "none"]:
            try:
                from services.database import update_candidate_email
                update_candidate_email(candidate_id, extracted_email)
            except Exception as e:
                print(f"Error saving email: {e}")

    # Extract executive summary
    if hasattr(crew_result, "pydantic") and crew_result.pydantic is not None:
        exec_summary = crew_result.pydantic.executive_summary
    else:
        exec_summary = _extract_executive_summary(raw_output)

    return {
        "executive_summary": exec_summary,
        "shortlisted_count": shortlisted_count,
        "total_candidates": len(resume_data),
        "raw_output": raw_output,
    }


def _extract_candidate_results(raw_output: str, resume_data: list[dict]) -> list[dict]:
    """
    Parses the crew's raw output to extract per-candidate results.
    Uses heuristic parsing since the output format may vary.
    """
    results = []

    # Try to parse as JSON first
    try:
        import re
        # Look for either a top-level object {} or top-level array []
        json_match = re.search(r'(\{|\[)[\s\S]*(\}|\])', raw_output)
        if json_match:
            data = json.loads(json_match.group())
            if isinstance(data, dict) and "candidates" in data:
                return data["candidates"]
            elif isinstance(data, list):
                return data
    except (json.JSONDecodeError, TypeError):
        pass

    # Heuristic parsing: look for score patterns
    import re

    for cand in resume_data:
        name = cand.get("name", "Unknown")
        result = {
            "candidate_id": cand.get("candidate_id"),
            "name": name,
            "match_score": 50.0,
            "reasoning": "",
            "strengths": [],
            "skill_gaps": [],
        }

        # Look for score mentions near candidate name
        # Pattern: "Name ... score: 85" or "Name ... 85/100" or "Name ... 85%"
        name_pattern = re.escape(name.split(".")[0].split("_")[0])
        patterns = [
            rf'{name_pattern}.*?(?:score|match|rating)[:\s]*(\d+(?:\.\d+)?)',
            rf'{name_pattern}.*?(\d+(?:\.\d+)?)\s*/\s*100',
            rf'{name_pattern}.*?(\d+(?:\.\d+)?)\s*%',
            rf'(?:score|match|rating)[:\s]*(\d+(?:\.\d+)?).*?{name_pattern}',
        ]

        for pattern in patterns:
            match = re.search(pattern, raw_output, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    score = float(match.group(1))
                    if 0 <= score <= 100:
                        result["match_score"] = score
                        break
                except ValueError:
                    continue

        # Extract reasoning (text near the candidate's name)
        reasoning_match = re.search(
            rf'{name_pattern}[:\s]*(.{{50,500}}?)(?:\n\n|\Z|---)',
            raw_output, re.IGNORECASE | re.DOTALL,
        )
        if reasoning_match:
            result["reasoning"] = reasoning_match.group(1).strip()

        # Extract strengths (look for bullet points after "strength" keyword)
        strengths_section = re.search(
            rf'{name_pattern}.*?(?:strength|strong|advantage).*?(?:\n[-•*]\s*(.+?))+',
            raw_output, re.IGNORECASE | re.DOTALL,
        )
        if strengths_section:
            strength_items = re.findall(r'[-•*]\s*(.+)', strengths_section.group())
            result["strengths"] = [s.strip() for s in strength_items[:5]]

        # Extract skill gaps
        gaps_section = re.search(
            rf'{name_pattern}.*?(?:gap|missing|lack|weak).*?(?:\n[-•*]\s*(.+?))+',
            raw_output, re.IGNORECASE | re.DOTALL,
        )
        if gaps_section:
            gap_items = re.findall(r'[-•*]\s*(.+)', gaps_section.group())
            result["skill_gaps"] = [g.strip() for g in gap_items[:5]]

        results.append(result)

    # Re-rank by score
    results.sort(key=lambda r: r.get("match_score", 0), reverse=True)

    return results


def _extract_executive_summary(raw_output: str) -> str:
    """Extracts the executive summary from the crew's output."""
    import re, json

    # Try to parse as JSON first
    try:
        json_match = re.search(r'\{[\s\S]*\}', raw_output)
        if json_match:
            data = json.loads(json_match.group())
            if "executive_summary" in data:
                return data["executive_summary"]
    except Exception:
        pass

    # Look for executive summary section in raw text
    patterns = [
        r'(?:executive\s+summary|overall\s+summary|final\s+summary)[:\s]*\n?(.*?)(?:\n\n|\n---|\Z)',
        r'(?:summary|conclusion|overview)[:\s]*\n?(.*?)(?:\n\n|\n---|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_output, re.IGNORECASE | re.DOTALL)
        if match:
            summary = match.group(1).strip()
            if len(summary) > 50:
                return summary

    # Fallback: use the last paragraph
    paragraphs = raw_output.strip().split("\n\n")
    if paragraphs:
        last = paragraphs[-1].strip()
        if len(last) > 50:
            return last[:500]

    return "Shortlisting pipeline completed. See the Rankings tab for detailed results."
