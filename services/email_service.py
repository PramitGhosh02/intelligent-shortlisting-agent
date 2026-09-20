"""
Email service for sending candidate notifications.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

def send_shortlist_email(to_email: str, candidate_name: str, job_title: str, match_score: float, smtp_config: Dict[str, str]) -> Tuple[bool, str]:
  """Sends an HTML email notification to shortlisted candidates."""
  try:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Congratulations! You have been shortlisted for {job_title}'
    msg['From'] = smtp_config.get('sender_email', smtp_config.get('username'))
    msg['To'] = to_email

    html_content = f"""
    <html>
     <body>
      <h2>Congratulations, {candidate_name}!</h2>
      <p>We are thrilled to inform you that you have been shortlisted for the <strong>{job_title}</strong> position.</p>
      <p>Your profile scored a match of <strong>{match_score}%</strong> against our requirements.</p>
      <p>Our recruitment team will be in touch with you shortly to discuss the next steps in the interview process.</p>
      <br>
      <p>Best regards,</p>
      <p>The Recruitment Team</p>
     </body>
    </html>
    """
    
    part = MIMEText(html_content, 'html')
    msg.attach(part)

    server = smtplib.SMTP(smtp_config['server'], int(smtp_config['port']))
    server.starttls()
    server.login(smtp_config['username'], smtp_config['password'])
    server.send_message(msg)
    server.quit()
    
    return True, "Email sent successfully"
  except Exception as e:
    error_msg = f"Failed to send email: {str(e)}"
    logger.error(error_msg)
    return False, error_msg

def test_smtp_connection(smtp_config: Dict[str, str]) -> Tuple[bool, str]:
  """Tests the SMTP connection using the provided configuration."""
  try:
    server = smtplib.SMTP(smtp_config['server'], int(smtp_config['port']))
    server.starttls()
    server.login(smtp_config['username'], smtp_config['password'])
    server.quit()
    return True, "SMTP connection successful"
  except Exception as e:
    error_msg = f"SMTP connection failed: {str(e)}"
    logger.error(error_msg)
    return False, error_msg
