"""
Tab 4: Analytics Dashboard

Displays visual analytics with Plotly charts: score distribution,
skill coverage, top candidates, and KPI summary cards.
"""

import gradio as gr
import json
import traceback
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def load_dashboard(job_id) -> tuple:
 """
 Loads dashboard analytics from the database.
 Returns (total_kpi, avg_kpi, shortlisted_kpi, gap_kpi,
    score_dist_plot, skill_coverage_plot, top_candidates_plot, summary_df).
 """
 empty = ("—", "—", "—", "—", None, None, None, pd.DataFrame())

 if job_id is None:
  return empty

 try:
  from services.database import get_results, get_job

  results = get_results(job_id)
  if not results:
   return empty

  job = get_job(job_id)
  job_reqs = json.loads(job.get("requirements_json", "{}")) if job else {}

  # ── KPIs ──────────────────────────────────────────────────
  scores = [r.get("match_score", 0) for r in results]
  total_candidates = str(len(results))
  avg_score = f"{sum(scores) / len(scores):.1f}" if scores else "0"
  shortlisted_count = str(sum(1 for r in results if r.get("shortlisted")))

  # Calculate gap rate
  gap_candidates = 0
  for r in results:
   gaps = json.loads(r.get("skill_gaps_json", "[]")) if r.get("skill_gaps_json") else []
   if len(gaps) > 2:
    gap_candidates += 1
  gap_rate = f"{(gap_candidates / len(results) * 100):.0f}%" if results else "0%"

  # ── Score Distribution Histogram ──────────────────────────
  score_df = pd.DataFrame({"Match Score": scores})
  fig_dist = px.histogram(
   score_df,
   x="Match Score",
   nbins=10,
   title="Score Distribution",
   template="plotly_white",
   color_discrete_sequence=["#4f46e5"],
  )
  fig_dist.update_layout(
   xaxis_title="Match Score",
   yaxis_title="Number of Candidates",
   margin=dict(l=40, r=20, t=50, b=40),
   bargap=0.1,
  )
  fig_dist.add_vline(x=70, line_dash="dash", line_color="green",
       annotation_text="Shortlist Threshold (70)")

  # ── Skill Coverage Bar Chart ──────────────────────────────
  required_skills = job_reqs.get("required_skills", [])
  fig_skills = create_skill_coverage_chart(results, required_skills)

  # ── Top Candidates Horizontal Bar ─────────────────────────
  sorted_results = sorted(results, key=lambda r: r.get("match_score", 0), reverse=True)
  top_10 = sorted_results[:10]
  top_names = [r.get("candidate_name", r.get("name", "?")) for r in top_10]
  top_scores = [r.get("match_score", 0) for r in top_10]

  colors = []
  for s in top_scores:
   if s >= 80:
    colors.append("#16a34a")
   elif s >= 60:
    colors.append("#ca8a04")
   else:
    colors.append("#dc2626")

  fig_top = go.Figure(go.Bar(
   x=top_scores,
   y=top_names,
   orientation="h",
   marker_color=colors,
   text=[f"{s:.1f}" for s in top_scores],
   textposition="auto",
  ))
  fig_top.update_layout(
   title="Top 10 Candidates by Score",
   xaxis_title="Match Score",
   yaxis=dict(autorange="reversed"),
   template="plotly_white",
   margin=dict(l=120, r=20, t=50, b=40),
   height=400,
  )

  # ── Summary Table ─────────────────────────────────────────
  summary_rows = []
  for i, r in enumerate(sorted_results, 1):
   strengths = json.loads(r.get("strengths_json", "[]")) if r.get("strengths_json") else []
   gaps = json.loads(r.get("skill_gaps_json", "[]")) if r.get("skill_gaps_json") else []
   summary_rows.append({
    "Rank": i,
    "Candidate": r.get("candidate_name", r.get("name", "Unknown")),
    "Score": r.get("match_score", 0),
    "Strengths": len(strengths),
    "Gaps": len(gaps),
    "Shortlisted": "Yes" if r.get("shortlisted") else "No",
   })
  summary_df = pd.DataFrame(summary_rows)

  return (
   total_candidates, avg_score, shortlisted_count, gap_rate,
   fig_dist, fig_skills, fig_top, summary_df,
  )

 except Exception as e:
  traceback.print_exc()
  return empty


def create_skill_coverage_chart(results: list, required_skills: list):
 """Creates a bar chart showing what % of candidates have each required skill."""
 if not required_skills:
  fig = go.Figure()
  fig.update_layout(title="Skill Coverage (No required skills defined)", template="plotly_white")
  return fig

 skill_counts = {skill: 0 for skill in required_skills}
 total = len(results)

 for r in results:
  strengths = json.loads(r.get("strengths_json", "[]")) if r.get("strengths_json") else []
  strengths_lower = [s.lower() for s in strengths]
  for skill in required_skills:
   if any(skill.lower() in s for s in strengths_lower):
    skill_counts[skill] += 1

 skills = list(skill_counts.keys())
 percentages = [(skill_counts[s] / total * 100) if total > 0 else 0 for s in skills]

 colors = ["#16a34a" if p >= 70 else "#ca8a04" if p >= 40 else "#dc2626" for p in percentages]

 fig = go.Figure(go.Bar(
  x=skills,
  y=percentages,
  marker_color=colors,
  text=[f"{p:.0f}%" for p in percentages],
  textposition="auto",
 ))
 fig.update_layout(
  title="Skill Coverage Across Candidates",
  xaxis_title="Required Skill",
  yaxis_title="% of Candidates",
  yaxis=dict(range=[0, 105]),
  template="plotly_white",
  margin=dict(l=40, r=20, t=50, b=80),
 )
 return fig


def create_dashboard_tab() -> dict:
 """Creates the Analytics Dashboard tab and returns component references."""
 with gr.Tab(" Dashboard", id="dashboard"):
  gr.Markdown("### Analytics Dashboard\nVisual overview of shortlisting results and candidate metrics.")

  refresh_dash_btn = gr.Button(" Refresh Dashboard", variant="primary")

  # KPI Cards
  with gr.Row():
   kpi_total = gr.Textbox(
    label=" Total Candidates",
    value="—",
    interactive=False,
    elem_classes=["metric-card"],
   )
   kpi_avg = gr.Textbox(
    label=" Average Score",
    value="—",
    interactive=False,
    elem_classes=["metric-card"],
   )
   kpi_shortlisted = gr.Textbox(
    label=" Shortlisted",
    value="—",
    interactive=False,
    elem_classes=["metric-card"],
   )
   kpi_gap = gr.Textbox(
    label=" High Gap Rate",
    value="—",
    interactive=False,
    elem_classes=["metric-card"],
   )

  # Charts Row 1
  with gr.Row():
   plot_dist = gr.Plot(label="Score Distribution")
   plot_skills = gr.Plot(label="Skill Coverage")

  # Charts Row 2
  with gr.Row():
   plot_top = gr.Plot(label="Top Candidates")

  # Summary Table
  summary_table = gr.Dataframe(
   label="Complete Summary",
   headers=["Rank", "Candidate", "Score", "Strengths", "Gaps", "Shortlisted"],
   interactive=False,
  )

 return {
  "refresh_dash_btn": refresh_dash_btn,
  "kpi_total": kpi_total,
  "kpi_avg": kpi_avg,
  "kpi_shortlisted": kpi_shortlisted,
  "kpi_gap": kpi_gap,
  "plot_dist": plot_dist,
  "plot_skills": plot_skills,
  "plot_top": plot_top,
  "summary_table": summary_table,
 }
