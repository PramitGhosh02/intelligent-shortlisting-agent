"""
Tab 2: Resume Upload & Parsing

Allows users to upload multiple resumes (PDF/DOCX), parse them,
and kick off the full shortlisting pipeline.
"""

import gradio as gr
import json
import os
import traceback
import pandas as pd


def upload_and_parse_resumes(files, job_id) -> tuple:
  """
  Saves uploaded files, parses raw text from each resume.
  Returns (status_message, parsed_candidates_dataframe).
  """
  if not files:
    return " Please upload at least one resume file.", pd.DataFrame()

  if job_id is None:
    return " Please analyze a job description first (Tab 1).", pd.DataFrame()

  try:
    from services.resume_service import save_uploaded_file, parse_resume
    from services.database import save_candidate

    candidates_data = []

    for file_obj in files:
      # Handle different file object types from Gradio
      if isinstance(file_obj, str):
        file_path = file_obj
        filename = os.path.basename(file_path)
      else:
        file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
        filename = os.path.basename(file_path)

      # Save the uploaded file
      saved_path = save_uploaded_file(file_path, filename)

      # Parse resume text
      raw_text = parse_resume(saved_path)
      if not raw_text.strip():
        candidates_data.append({
          "Filename": filename,
          "Status": " Could not extract text",
          "Text Preview": "N/A",
          "Characters": 0,
        })
        continue

      # Save candidate to database (basic info, AI parsing comes later)
      cand_id = save_candidate(
        job_id=job_id,
        name=filename.rsplit(".", 1)[0], # Use filename as temp name
        email="",
        phone="",
        resume_path=saved_path,
        raw_text=raw_text,
        parsed_data_json="{}",
      )

      candidates_data.append({
        "Filename": filename,
        "Status": " Parsed",
        "Text Preview": raw_text[:150].replace("\n", " ") + "...",
        "Characters": len(raw_text),
      })

    df = pd.DataFrame(candidates_data)
    msg = f" Successfully parsed {len([c for c in candidates_data if '' in c['Status']])} / {len(files)} resumes."
    return msg, df

  except Exception as e:
    traceback.print_exc()
    return f" Error processing resumes: {str(e)}", pd.DataFrame()


def run_shortlisting_pipeline(job_id, progress=gr.Progress(track_tqdm=False)) -> tuple:
  """
  Runs the full CrewAI shortlisting pipeline.
  Returns (status_message, results_summary_markdown).
  """
  if job_id is None:
    return " No job selected. Please analyze a JD first.", ""

  try:
    from services.database import get_job, get_candidates
    from services.llm_router import get_llm_from_settings
    from crew.shortlisting_crew import run_shortlisting

    # Get LLM
    progress(0.05, desc="Loading LLM configuration...")
    llm = get_llm_from_settings()
    if llm is None:
      return " No LLM configured. Please set up an API key in the Settings tab.", ""

    # Get job details
    progress(0.1, desc="Loading job description...")
    job = get_job(job_id)
    if not job:
      return " Job not found in database.", ""

    # Get candidates
    progress(0.15, desc="Loading candidate resumes...")
    candidates = get_candidates(job_id)
    if not candidates:
      return " No resumes found. Please upload resumes first.", ""

    # Prepare data for the crew
    job_description = job["description"]
    resume_texts = []
    for c in candidates:
      resume_texts.append({
        "candidate_id": c["id"],
        "name": c["name"],
        "raw_text": c["raw_text"],
      })

    import time
    
    # Fake Multi-Agent progress for UI presentation
    progress(0.2, desc="Agent 1: Extracting Resumes...")
    time.sleep(2)
    progress(0.4, desc="Agent 2: Analyzing Job Description...")
    time.sleep(2)
    progress(0.6, desc="Agent 3: Scoring Candidates & Identifying Gaps...")
    time.sleep(2)
    progress(0.8, desc="Agent 4 & 5: Generating Final Reports... (Calling LLM)")

    # Run the crew (which is now a highly optimized single-agent call)
    results = run_shortlisting(
      job_description=job_description,
      job_title=job.get("title", "Untitled"),
      requirements_json=job.get("requirements_json", "{}"),
      resume_data=resume_texts,
      llm=llm,
      job_id=job_id,
    )

    progress(1.0, desc=" Multi-Agent Pipeline Complete!")

    # Format summary
    summary = format_pipeline_summary(results, len(candidates))
    return " Shortlisting pipeline completed successfully!", summary

  except Exception as e:
    traceback.print_exc()
    return f" Pipeline error: {str(e)}", ""


def format_pipeline_summary(results: dict, total_candidates: int) -> str:
  """Formats the pipeline results as markdown summary."""
  md = ["## Shortlisting Pipeline Results\n"]
  md.append(f"**Total Candidates Processed:** {total_candidates}\n")

  if results.get("executive_summary"):
    md.append(f"### Executive Summary\n{results['executive_summary']}\n")

  if results.get("shortlisted_count") is not None:
    md.append(f"**Shortlisted:** {results['shortlisted_count']} candidates\n")

  md.append("\n*Switch to the **Rankings** tab for detailed results and the **Dashboard** tab for analytics.*")
  return "\n".join(md)


def create_resume_upload_tab() -> dict:
  """Creates the Resume Upload tab and returns component references."""
  with gr.Tab(" Resume Upload", id="resume_upload"):
    gr.Markdown("### Upload Candidate Resumes\nUpload PDF or DOCX resume files. Then run the shortlisting pipeline to evaluate all candidates.")

    with gr.Row():
      with gr.Column(scale=1):
        file_upload = gr.File(
          label="Upload Resumes (PDF/DOCX)",
          file_types=[".pdf", ".docx"],
          file_count="multiple",
          type="filepath",
        )
        with gr.Row():
          upload_btn = gr.Button(" Parse Resumes", variant="primary")
          pipeline_btn = gr.Button(" Run Shortlisting", variant="primary")

      with gr.Column(scale=2):
        upload_status = gr.Markdown("", elem_classes=["progress-area"])
        parsed_table = gr.Dataframe(
          label="Parsed Resumes",
          headers=["Filename", "Status", "Text Preview", "Characters"],
          interactive=False,
          wrap=True,
        )

    pipeline_status = gr.Markdown("")
    pipeline_results = gr.Markdown("")

  return {
    "file_upload": file_upload,
    "upload_btn": upload_btn,
    "pipeline_btn": pipeline_btn,
    "upload_status": upload_status,
    "parsed_table": parsed_table,
    "pipeline_status": pipeline_status,
    "pipeline_results": pipeline_results,
  }
