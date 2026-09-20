"""
Tab 5: Email Notifications

Allows sending shortlist notification emails to selected candidates.
"""

import gradio as gr
import json
import traceback
import pandas as pd


def load_shortlisted_candidates(job_id) -> tuple:
  """
  Loads shortlisted candidates for email sending.
  Returns (dataframe, email_template, status).
  """
  if job_id is None:
    return pd.DataFrame(), get_default_template(), " No job selected."

  try:
    from services.database import get_results, get_job

    results = get_results(job_id)
    job = get_job(job_id)
    job_title = job.get("title", "the position") if job else "the position"

    shortlisted = [r for r in results if r.get("shortlisted")]

    if not shortlisted:
      return (
        pd.DataFrame(),
        get_default_template(job_title),
        " No candidates shortlisted yet. Use the Rankings tab to shortlist candidates.",
      )

    rows = []
    for r in shortlisted:
      rows.append({
        "Candidate": r.get("candidate_name", r.get("name", "Unknown")),
        "Email": r.get("candidate_email", "Not available") if r.get("candidate_email") else "Not available",
        "Score": f"{r.get('match_score', 0):.1f}",
        "Status": " Pending",
      })

    df = pd.DataFrame(rows)
    return df, get_default_template(job_title), f" {len(shortlisted)} candidates ready for notification."

  except Exception as e:
    traceback.print_exc()
    return pd.DataFrame(), get_default_template(), f" Error: {str(e)}"


def get_default_template(job_title: str = "the position") -> str:
  """Returns the default email template."""
  return f"""Dear {{candidate_name}},

Congratulations! We are pleased to inform you that you have been shortlisted for the position of {job_title}.

Your application stood out among many qualified candidates, and we were impressed by your skills and experience. Your match score of {{match_score}}% demonstrates a strong alignment with our requirements.

Next Steps:
1. We will contact you shortly to schedule an interview
2. Please prepare a brief presentation about your relevant experience
3. Keep an eye on your email for further communications

We look forward to speaking with you!

Best regards,
HR Team"""


def send_emails_handler(job_id, email_template: str, send_all: bool = True) -> tuple:
  """
  Sends notification emails to shortlisted candidates.
  Returns (updated_dataframe, status_message).
  """
  if job_id is None:
    return pd.DataFrame(), " No job selected."

  try:
    from services.database import get_results, get_job, get_all_settings
    from services.email_service import send_shortlist_email

    settings = get_all_settings()
    smtp_config = {
      "server": settings.get("smtp_server", "smtp.gmail.com"),
      "port": int(settings.get("smtp_port", "587")),
      "username": settings.get("smtp_username", ""),
      "password": settings.get("smtp_password", ""),
      "sender_email": settings.get("smtp_sender", settings.get("smtp_username", "")),
    }

    if not smtp_config["username"] or not smtp_config["password"]:
      return pd.DataFrame(), " SMTP not configured. Please set up email settings in the Settings tab."

    results = get_results(job_id)
    job = get_job(job_id)
    job_title = job.get("title", "the position") if job else "the position"

    shortlisted = [r for r in results if r.get("shortlisted")]
    if not shortlisted:
      return pd.DataFrame(), " No shortlisted candidates to email."

    rows = []
    sent_count = 0
    failed_count = 0

    for r in shortlisted:
      candidate_name = r.get("candidate_name", r.get("name", "Unknown"))
      email = r.get("candidate_email", "")

      if not email or email == "Not available":
        rows.append({
          "Candidate": candidate_name,
          "Email": "N/A",
          "Score": f"{r.get('match_score', 0):.1f}",
          "Status": " No email",
        })
        continue

      # Personalize template
      personalized = email_template.replace("{candidate_name}", candidate_name)
      personalized = personalized.replace("{match_score}", f"{r.get('match_score', 0):.1f}")

      success, msg = send_shortlist_email(
        to_email=email,
        candidate_name=candidate_name,
        job_title=job_title,
        match_score=r.get("match_score", 0),
        smtp_config=smtp_config,
      )

      if success:
        rows.append({
          "Candidate": candidate_name,
          "Email": email,
          "Score": f"{r.get('match_score', 0):.1f}",
          "Status": " Sent",
        })
        sent_count += 1
      else:
        rows.append({
          "Candidate": candidate_name,
          "Email": email,
          "Score": f"{r.get('match_score', 0):.1f}",
          "Status": f" Failed: {msg}",
        })
        failed_count += 1

    df = pd.DataFrame(rows)
    status = f" Sent: {sent_count} | Failed: {failed_count} | Skipped (no email): {len(shortlisted) - sent_count - failed_count}"
    return df, status

  except Exception as e:
    traceback.print_exc()
    return pd.DataFrame(), f" Error sending emails: {str(e)}"


def create_email_tab() -> dict:
  """Creates the Email Notifications tab and returns component references."""
  with gr.Tab(" Email", id="email"):
    gr.Markdown("### Email Notifications\nSend shortlist notifications to selected candidates.")

    with gr.Row():
      with gr.Column(scale=1):
        load_email_btn = gr.Button(" Load Shortlisted", variant="primary")
        send_all_btn = gr.Button(" Send All Emails", variant="primary")
        email_status = gr.Markdown("")

      with gr.Column(scale=2):
        email_template = gr.Textbox(
          label="Email Template",
          lines=15,
          value=get_default_template(),
          info="Use {candidate_name} and {match_score} as placeholders.",
        )

    email_table = gr.Dataframe(
      label="Email Status",
      headers=["Candidate", "Email", "Score", "Status"],
      interactive=False,
      wrap=True,
    )

  return {
    "load_email_btn": load_email_btn,
    "send_all_btn": send_all_btn,
    "email_status": email_status,
    "email_template": email_template,
    "email_table": email_table,
  }
