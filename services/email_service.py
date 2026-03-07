# shared/ses_notifier.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = "grc36025@gmail.com"   # your email
SMTP_PASS = "AWSGoodLuck@25"  # your app password

def send_stage_notification(to_email, subject, instance_id, stage_name, action_required):
    body_html = f"""
    <html><body style="font-family:Segoe UI,sans-serif;padding:20px;">
        <h2 style="color:#1E3A5F;">GRC360 — Workflow Update</h2>
        <table style="border-collapse:collapse;width:100%;">
            <tr><td><b>Instance</b></td><td>#{instance_id}</td></tr>
            <tr><td><b>Stage</b></td><td>{stage_name}</td></tr>
            <tr><td><b>Action</b></td><td style="color:#DC3545;">{action_required}</td></tr>
        </table>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_email, msg.as_string())