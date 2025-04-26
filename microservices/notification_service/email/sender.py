# Email notification sender
import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from microservices.notification_service.schemas import EmailNotification

# Initialize logging
logger = logging.getLogger(__name__)

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "noreply@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "password")
SMTP_FROM = os.getenv("SMTP_FROM", "LMS System <noreply@example.com>")


async def send_email(notification: EmailNotification):
    """
    Send an email notification

    Args:
        notification: The email notification to send
    """
    try:
        # Create multipart message
        msg = MIMEMultipart()
        msg["From"] = SMTP_FROM
        msg["To"] = notification.recipient_email
        msg["Subject"] = notification.subject

        # Add CC and BCC if provided
        if notification.cc:
            msg["Cc"] = ", ".join(notification.cc)
        if notification.bcc:
            msg["Bcc"] = ", ".join(notification.bcc)

        # Add plain text body
        msg.attach(MIMEText(notification.body, "plain"))

        # Add HTML body if provided
        if notification.html_body:
            msg.attach(MIMEText(notification.html_body, "html"))

        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)

            recipients = [notification.recipient_email]
            if notification.cc:
                recipients.extend(notification.cc)
            if notification.bcc:
                recipients.extend(notification.bcc)

            server.sendmail(SMTP_FROM, recipients, msg.as_string())

        logger.info(f"Email sent to {notification.recipient_email} with subject: {notification.subject}")

        return True

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise