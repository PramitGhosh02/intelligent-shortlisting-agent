"""
Tab 3: Candidate Rankings

Displays ranked candidates with scores, detailed reasoning, and shortlist management.
"""

import gradio as gr
import json
import traceback
import pandas as pd


def load_rankings(job_id) -> tuple:
 """
 Loads candidate rankings from the database.
 Returns (dataframe, detail_markdown, status).
 """
 if job_id is None:
  return pd.DataFrame(), "No job selected.", " Analyze a JD and run the pipeline first."

 try:
  from services.database import get_results

  results = get_results(job_id)
  if not results:
   return pd.DataFrame(), "No results yet.", " Run the shortlisting pipeline first."

  # Sort by match_score descending
  results.sort(key=lambda r: r.get("match_score", 0), reverse=True)

  # Build DataFrame
  rows = []
  for i, r in enumerate(results, 1):
   score = r.get("match_score", 0)
   if score >= 80:
    badge = ""
   elif score >= 60:
    badge = ""
   else:
    badge = ""

   strengths = json.loads(r.get("strengths_json", "[]")) if r.get("strengths_json") else []
   top_strengths = ", ".join(strengths[:3]) if strengths else "N/A"
   shortlisted_text = "Yes" if r.get("shortlisted") else "No"

   rows.append({
    "Rank": i,
    "Candidate": r.get("candidate_name", r.get("name", "Unknown")),
    "Score": f"{badge} {score:.1f}",
    "Top Strengths": top_strengths,
    "Shortlisted": shortlisted_text,
    "Email": r.get("candidate_email", ""),
   })

  df = pd.DataFrame(rows)

  # Build detail markdown
  detail = build_detail_markdown(results)

  return df, detail, f" Showing {len(results)} candidates ranked by match score."

 except Exception as e:
  traceback.print_exc()
  return pd.DataFrame(), "", f" Error loading rankings: {str(e)}"


def build_detail_markdown(results: list) -> str:
 """Builds detailed per-candidate markdown breakdown."""
 md_parts = ["## Detailed Candidate Analysis\n"]

 for i, r in enumerate(results, 1):
  score = r.get("match_score", 0)
  name = r.get("candidate_name", r.get("name", "Unknown"))

  md_parts.append(f"### {i}. {name} — Score: {score:.1f}/100\n")

  # Reasoning
  reasoning = r.get("reasoning", "No reasoning available.")
  md_parts.append(f"**Evaluation:** {reasoning}\n")

  # Strengths
  strengths = json.loads(r.get("strengths_json", "[]")) if r.get("strengths_json") else []
  if strengths:
   md_parts.append("**Strengths:**")
   for s in strengths:
    md_parts.append(f" - {s}")
   md_parts.append("")

  # Skill gaps
  gaps = json.loads(r.get("skill_gaps_json", "[]")) if r.get("skill_gaps_json") else []
  if gaps:
   md_parts.append("**Skill Gaps:**")
   for g in gaps:
    md_parts.append(f" - {g}")
   md_parts.append("")

  md_parts.append("---\n")

 return "\n".join(md_parts)


def toggle_shortlist(job_id, candidate_name, current_status) -> tuple:
 """Toggles shortlist status for a candidate and refreshes rankings."""
 if job_id is None:
  return pd.DataFrame(), "", " No job selected."
 try:
  from services.database import get_results, update_shortlist_status

  results = get_results(job_id)
  for r in results:
   cand_name = r.get("candidate_name", r.get("name", ""))
   if cand_name == candidate_name:
    new_status = not r.get("shortlisted", False)
    update_shortlist_status(r["id"], new_status)
    
    # Automatically refresh the table
    df, detail, _ = load_rankings(job_id)
    return df, detail, f"{' Shortlisted' if new_status else ' Removed from shortlist'}: {candidate_name}"

  df, detail, _ = load_rankings(job_id)
  return df, detail, f" Candidate not found: {candidate_name}"

 except Exception as e:
  return pd.DataFrame(), "", f" Error: {str(e)}"


def update_email(job_id, candidate_name, new_email) -> tuple:
 """Updates a candidate's email manually and refreshes rankings."""
 if job_id is None or not candidate_name:
  return pd.DataFrame(), "", " No job or candidate selected."
 try:
  from services.database import get_results, update_candidate_email
  results = get_results(job_id)
  for r in results:
   cand_name = r.get("candidate_name", r.get("name", ""))
   if cand_name == candidate_name:
    update_candidate_email(r["candidate_id"], new_email)
    df, detail, _ = load_rankings(job_id)
    return df, detail, f" Email updated for {candidate_name}"
  
  df, detail, _ = load_rankings(job_id)
  return df, detail, f" Candidate not found: {candidate_name}"
 except Exception as e:
  return pd.DataFrame(), "", f" Error: {str(e)}"


def shortlist_top_n(job_id, n: int) -> tuple:
 """Auto-shortlists the top N candidates by score and refreshes rankings."""
 if job_id is None:
  return pd.DataFrame(), "", " No job selected."

 try:
  from services.database import get_results, update_shortlist_status

  results = get_results(job_id)
  results.sort(key=lambda r: r.get("match_score", 0), reverse=True)

  count = 0
  for r in results:
   if count < n:
    update_shortlist_status(r["id"], True)
    count += 1
   else:
    update_shortlist_status(r["id"], False)

  # Automatically refresh the table
  df, detail, _ = load_rankings(job_id)
  return df, detail, f" Top {n} candidates shortlisted."

 except Exception as e:
  return pd.DataFrame(), "", f" Error: {str(e)}"


def create_rankings_tab() -> dict:
 """Creates the Rankings tab and returns component references."""
 with gr.Tab(" Rankings", id="rankings"):
  gr.Markdown("### Candidate Rankings\nView ranked candidates, detailed evaluations, and manage the shortlist.")

  with gr.Row():
   refresh_btn = gr.Button(" Refresh Rankings", variant="primary")
   with gr.Column(scale=1):
    top_n_slider = gr.Slider(
     label="Auto-shortlist top N",
     minimum=1,
     maximum=20,
     value=5,
     step=1,
    )
   shortlist_btn = gr.Button(" Shortlist Top N", variant="secondary")

  with gr.Row():
   with gr.Column(scale=2):
    manual_cand_name = gr.Textbox(label="Candidate Name (Exact Match)", placeholder="Enter name from table...")
   with gr.Column(scale=1):
    manual_toggle_btn = gr.Button("Toggle Shortlist Status", variant="primary")
   with gr.Column(scale=2):
    manual_email_input = gr.Textbox(label="Update Email", placeholder="Enter email address...")
   with gr.Column(scale=1):
    manual_email_btn = gr.Button("Save Email", variant="primary")

  rankings_status = gr.Markdown("")

  rankings_table = gr.Dataframe(
   label="Candidate Rankings",
   headers=["Rank", "Candidate", "Score", "Top Strengths", "Shortlisted", "Email"],
   interactive=False,
   wrap=True,
  )

  detail_view = gr.Markdown("", label="Detailed Analysis")
  shortlist_status = gr.Markdown("")

 return {
  "refresh_btn": refresh_btn,
  "rankings_table": rankings_table,
  "detail_view": detail_view,
  "rankings_status": rankings_status,
  "top_n_slider": top_n_slider,
  "shortlist_btn": shortlist_btn,
  "shortlist_status": shortlist_status,
  "manual_cand_name": manual_cand_name,
  "manual_toggle_btn": manual_toggle_btn,
  "manual_email_input": manual_email_input,
  "manual_email_btn": manual_email_btn,
 }
