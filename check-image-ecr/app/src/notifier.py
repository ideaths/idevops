import os
import smtplib
from email.mime.text import MIMEText
from typing import Optional

import requests
import structlog


logger = structlog.get_logger()


def notify_slack(message: str):
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        logger.warning("slack_webhook_missing")
        return
    try:
        resp = requests.post(webhook, json={"text": message}, timeout=10)
        if resp.status_code >= 300:
            logger.error("slack_notify_failed", status=resp.status_code, body=resp.text)
    except Exception as e:
        logger.error("slack_notify_error", error=str(e))


def notify_email(subject: str, body: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "25"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    to_addr = os.getenv("ALERT_EMAIL_TO")
    from_addr = os.getenv("ALERT_EMAIL_FROM", to_addr or smtp_user or "noreply@example.com")

    if not smtp_server or not to_addr:
        logger.warning("email_config_missing")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as s:
            if smtp_user and smtp_pass:
                s.starttls()
                s.login(smtp_user, smtp_pass)
            s.sendmail(from_addr, [to_addr], msg.as_string())
    except Exception as e:
        logger.error("email_send_error", error=str(e))