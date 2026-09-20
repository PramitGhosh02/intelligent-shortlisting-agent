"""
Intelligent Candidate Shortlisting Agent - Main Application

Entry point for the Gradio-based multi-agent recruitment tool.
Assembles all UI tabs and wires up event handlers.
"""

import gradio as gr

import config
from services.database import init_db
from ui.theme import get_theme, CUSTOM_CSS
from ui.tabs.job_input import create_job_input_tab, analyze_jd_handler, load_sample_jd
from ui.tabs.resume_upload import (
 create_resume_upload_tab,
 upload_and_parse_resumes,
 run_shortlisting_pipeline,
)
from ui.tabs.rankings import (
 create_rankings_tab,
 load_rankings,
 shortlist_top_n,
)
from ui.tabs.dashboard import create_dashboard_tab, load_dashboard
from ui.tabs.email_tab import (
 create_email_tab,
 load_shortlisted_candidates,
 send_emails_handler,
)
from ui.tabs.settings import create_settings_tab, load_settings


def build_app() -> gr.Blocks:
 """Builds and returns the complete Gradio application."""

 # Initialize the database
 init_db()

 theme = get_theme()

 with gr.Blocks(
  title=config.APP_TITLE,
 ) as app:

  # ── Header ───────────────────────────────────────────────
  gr.Markdown(
   f"""
   <div class="app-header">
    <h1>Intelligent Candidate Shortlisting Agent</h1>
    <p>AI-Powered Multi-Agent Recruitment Pipeline | v{config.APP_VERSION}</p>
   </div>
   """,
  )

  # ── Tabs ─────────────────────────────────────────────────
  with gr.Tabs() as tabs:
   # Tab 1: Job Description Input
   job_components = create_job_input_tab()

   # Tab 2: Resume Upload
   resume_components = create_resume_upload_tab()

   # Tab 3: Rankings
   ranking_components = create_rankings_tab()

   # Tab 4: Dashboard
   dash_components = create_dashboard_tab()

   # Tab 5: Email
   email_components = create_email_tab()

   # Tab 6: Settings
   settings_components = create_settings_tab()

  # ── Wire up cross-tab event handlers ─────────────────────

  # Resume upload uses job_id from job input tab
  resume_components["upload_btn"].click(
   fn=upload_and_parse_resumes,
   inputs=[resume_components["file_upload"], job_components["job_id_state"]],
   outputs=[resume_components["upload_status"], resume_components["parsed_table"]],
  )

  # Pipeline button uses job_id
  resume_components["pipeline_btn"].click(
   fn=run_shortlisting_pipeline,
   inputs=[job_components["job_id_state"]],
   outputs=[resume_components["pipeline_status"], resume_components["pipeline_results"]],
  )

  # Rankings refresh
  ranking_components["refresh_btn"].click(
   fn=load_rankings,
   inputs=[job_components["job_id_state"]],
   outputs=[
    ranking_components["rankings_table"],
    ranking_components["detail_view"],
    ranking_components["rankings_status"],
   ],
  )

  # Shortlist top N
  ranking_components["shortlist_btn"].click(
   fn=shortlist_top_n,
   inputs=[job_components["job_id_state"], ranking_components["top_n_slider"]],
   outputs=[ranking_components["rankings_table"], ranking_components["detail_view"], ranking_components["shortlist_status"]],
  )

  # Manual Shortlist Toggle
  from ui.tabs.rankings import toggle_shortlist, update_email
  ranking_components["manual_toggle_btn"].click(
   fn=toggle_shortlist,
   inputs=[job_components["job_id_state"], ranking_components["manual_cand_name"], ranking_components["shortlist_status"]],
   outputs=[ranking_components["rankings_table"], ranking_components["detail_view"], ranking_components["shortlist_status"]],
  )

  # Manual Email Update
  ranking_components["manual_email_btn"].click(
   fn=update_email,
   inputs=[job_components["job_id_state"], ranking_components["manual_cand_name"], ranking_components["manual_email_input"]],
   outputs=[ranking_components["rankings_table"], ranking_components["detail_view"], ranking_components["shortlist_status"]],
  )

  # Dashboard refresh
  dash_components["refresh_dash_btn"].click(
   fn=load_dashboard,
   inputs=[job_components["job_id_state"]],
   outputs=[
    dash_components["kpi_total"],
    dash_components["kpi_avg"],
    dash_components["kpi_shortlisted"],
    dash_components["kpi_gap"],
    dash_components["plot_dist"],
    dash_components["plot_skills"],
    dash_components["plot_top"],
    dash_components["summary_table"],
   ],
  )

  # Email tab
  email_components["load_email_btn"].click(
   fn=load_shortlisted_candidates,
   inputs=[job_components["job_id_state"]],
   outputs=[
    email_components["email_table"],
    email_components["email_template"],
    email_components["email_status"],
   ],
  )

  email_components["send_all_btn"].click(
   fn=send_emails_handler,
   inputs=[job_components["job_id_state"], email_components["email_template"]],
   outputs=[email_components["email_table"], email_components["email_status"]],
  )

  # ── Footer ───────────────────────────────────────────────
  gr.Markdown(
   "<center>"
   "<small> Powered by CrewAI Multi-Agent Framework | "
   "Built with Gradio | "
   f"v{config.APP_VERSION}</small>"
   "</center>"
  )

 return app

# Build the global app instance for Hugging Face Spaces
app = build_app()

if __name__ == "__main__":
  print(f"\n{'='*60}")
  print(f" Intelligent Candidate Shortlisting Agent")
  print(f" Version: {config.APP_VERSION}")
  print(f" Database: {config.DB_PATH}")
  print(f"{'='*60}\n")
  
  app.launch(
    share=False,
    server_name="0.0.0.0",
    server_port=7860,
    show_error=True,
    css=CUSTOM_CSS,
    theme=get_theme(),
  )
