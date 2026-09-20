"""
Tab 1: Job Description Input

Allows users to input a job description and analyze it into structured requirements.
"""

import gradio as gr
import json
import traceback


def analyze_jd_handler(job_title: str, department: str, jd_text: str,
      min_exp: int, max_exp: int) -> tuple:
 """
 Analyzes the job description using the JD Analyzer agent.
 Returns (status_message, parsed_requirements_markdown, job_id).
 """
 if not jd_text.strip():
  return " Please enter a job description.", "", None

 try:
  from services.database import save_job, get_setting
  from services.llm_router import get_llm_from_settings
  from agents.jd_analyzer import create_jd_analyzer_agent, JobRequirements
  from crewai import Task, Crew, Process

  # Get LLM
  llm = get_llm_from_settings()
  if llm is None:
   return " No LLM configured. Please set up an API key in the Settings tab.", "", None

  # Create JD Analyzer agent and task
  jd_agent = create_jd_analyzer_agent(llm)

  full_jd = f"Job Title: {job_title}\nDepartment: {department}\n"
  full_jd += f"Experience Required: {min_exp}-{max_exp} years\n\n"
  full_jd += jd_text

  jd_task = Task(
   description=(
    f"Analyze the following job description and extract structured requirements:\n\n"
    f"{full_jd}\n\n"
    "Extract: title, required_skills, preferred_skills, min_experience_years, "
    "education_requirements, key_responsibilities, and a brief summary."
   ),
   expected_output="Structured job requirements in the specified format.",
   agent=jd_agent,
   output_pydantic=JobRequirements,
  )

  crew = Crew(agents=[jd_agent], tasks=[jd_task], process=Process.sequential, verbose=True)
  result = crew.kickoff()

  # Parse results
  if result.pydantic:
   reqs = result.pydantic
   reqs_dict = reqs.model_dump()
  else:
   reqs_dict = {
    "title": job_title,
    "required_skills": [],
    "preferred_skills": [],
    "min_experience_years": min_exp,
    "education_requirements": [],
    "key_responsibilities": [],
    "summary": result.raw,
   }

  # Save to database
  job_id = save_job(
   title=job_title or reqs_dict.get("title", "Untitled"),
   description=jd_text,
   requirements_json=json.dumps(reqs_dict),
  )

  # Format requirements as markdown
  md = format_requirements_markdown(reqs_dict)

  return f" Job description analyzed successfully! (Job ID: {job_id})", md, job_id

 except Exception as e:
  traceback.print_exc()
  return f" Error analyzing job description: {str(e)}", "", None


def format_requirements_markdown(reqs: dict) -> str:
 """Formats the parsed job requirements as a readable markdown string."""
 md_parts = [f"## Parsed Requirements for: {reqs.get('title', 'N/A')}\n"]

 if reqs.get("summary"):
  md_parts.append(f"**Summary:** {reqs['summary']}\n")

 if reqs.get("required_skills"):
  md_parts.append("### Required Skills")
  for skill in reqs["required_skills"]:
   md_parts.append(f"- {skill}")
  md_parts.append("")

 if reqs.get("preferred_skills"):
  md_parts.append("### Preferred Skills")
  for skill in reqs["preferred_skills"]:
   md_parts.append(f"- {skill}")
  md_parts.append("")

 exp = reqs.get("min_experience_years", 0)
 md_parts.append(f"### Minimum Experience: **{exp} years**\n")

 if reqs.get("education_requirements"):
  md_parts.append("### Education Requirements")
  for edu in reqs["education_requirements"]:
   md_parts.append(f"- {edu}")
  md_parts.append("")

 if reqs.get("key_responsibilities"):
  md_parts.append("### Key Responsibilities")
  for resp in reqs["key_responsibilities"]:
   md_parts.append(f"- {resp}")
  md_parts.append("")

 return "\n".join(md_parts)


def load_sample_jd() -> tuple:
 """Loads the sample job description for testing."""
 try:
  from config import SAMPLE_DATA_DIR
  sample_path = SAMPLE_DATA_DIR / "sample_jd.txt"
  if sample_path.exists():
   jd_text = sample_path.read_text(encoding="utf-8")
   return "Senior Python Developer", "Engineering", jd_text, 3, 7
 except Exception:
  pass

 # Fallback sample JD
 sample = """We are looking for a Senior Python Developer to join our engineering team.

Responsibilities:
- Design and develop scalable backend services using Python and FastAPI
- Build and maintain RESTful APIs and microservices architecture
- Implement data processing pipelines and ETL workflows
- Write comprehensive unit tests and integration tests
- Collaborate with frontend developers and DevOps engineers
- Participate in code reviews and mentor junior developers

Requirements:
- 3-7 years of professional Python development experience
- Strong knowledge of Python frameworks (Django, FastAPI, Flask)
- Experience with SQL databases (PostgreSQL, MySQL) and ORMs
- Familiarity with Docker, Kubernetes, and CI/CD pipelines
- Understanding of cloud services (AWS/GCP/Azure)
- Bachelor's degree in Computer Science or related field

Preferred:
- Experience with machine learning libraries (scikit-learn, TensorFlow)
- Knowledge of message queues (RabbitMQ, Kafka)
- Contributions to open source projects"""

 return "Senior Python Developer", "Engineering", sample, 3, 7


def create_job_input_tab() -> dict:
 """Creates the Job Description Input tab and returns component references."""
 with gr.Tab(" Job Description", id="job_input"):
  gr.Markdown("### Enter Job Description\nPaste or type the job description below. Click **Analyze JD** to extract structured requirements.")

  with gr.Row():
   with gr.Column(scale=1):
    job_title = gr.Textbox(
     label="Job Title",
     placeholder="e.g., Senior Python Developer",
     value="",
    )
    department = gr.Textbox(
     label="Department",
     placeholder="e.g., Engineering",
     value="",
    )
    with gr.Row():
     min_exp = gr.Number(label="Min Experience (years)", value=0, minimum=0, maximum=30)
     max_exp = gr.Number(label="Max Experience (years)", value=5, minimum=0, maximum=50)

    with gr.Row():
     analyze_btn = gr.Button(" Analyze JD", variant="primary", scale=2)
     sample_btn = gr.Button(" Load Sample", variant="secondary", scale=1)

   with gr.Column(scale=2):
    jd_text = gr.Textbox(
     label="Job Description",
     placeholder="Paste the full job description here...",
     lines=14,
     max_lines=30,
    )

  status = gr.Markdown("", elem_classes=["progress-area"])
  parsed_reqs = gr.Markdown("", label="Parsed Requirements")

  # Hidden state for job_id
  job_id_state = gr.State(value=None)

  # Event handlers
  analyze_btn.click(
   fn=analyze_jd_handler,
   inputs=[job_title, department, jd_text, min_exp, max_exp],
   outputs=[status, parsed_reqs, job_id_state],
  )

  sample_btn.click(
   fn=load_sample_jd,
   inputs=[],
   outputs=[job_title, department, jd_text, min_exp, max_exp],
  )

 return {
  "job_title": job_title,
  "jd_text": jd_text,
  "job_id_state": job_id_state,
  "status": status,
  "parsed_reqs": parsed_reqs,
 }
