# core/lms_core/auth/email.py

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Initialize logging
logger = logging.getLogger(__name__)

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "noreply@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "password")
SMTP_FROM = os.getenv("SMTP_FROM", "LMS System <noreply@example.com>")


async def send_password_reset_email(email, username, reset_url):
    """
    Send a password reset email

    Args:
        email: Recipient email address
        username: Username of the recipient
        reset_url: Password reset URL
    """
    try:
        # Create multipart message
        msg = MIMEMultipart()
        msg["From"] = SMTP_FROM
        msg["To"] = email
        msg["Subject"] = "Password Reset - Learning Management System"

        # Email content
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset</h2>
            <p>Hello {username},</p>
            <p>We received a request to reset your password. If you didn't make this request, you can ignore this email.</p>
            <p>To reset your password, click the link below or copy and paste it into your browser:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>Best regards,<br>LMS Team</p>
        </body>
        </html>
        """

        # Plain text alternative
        text_content = f"""
        Password Reset

        Hello {username},

        We received a request to reset your password. If you didn't make this request, you can ignore this email.

        To reset your password, click the link below or copy and paste it into your browser:

        {reset_url}

        This link will expire in 24 hours.

        Best regards,
        LMS Team
        """

        # Add plain text body
        msg.attach(MIMEText(text_content, "plain"))

        # Add HTML body
        msg.attach(MIMEText(html_content, "html"))

        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, email, msg.as_string())

        logger.info(f"Password reset email sent to {email}")

        return True

    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        # Don't raise exception to prevent leaking email sending errors
        return False