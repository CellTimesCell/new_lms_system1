# core/lms_core/auth/email.py
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
import json
from typing import Dict, List, Optional

# Initialize logging
logger = logging.getLogger(__name__)

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "noreply@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "password")
SMTP_FROM = os.getenv("SMTP_FROM", "LMS System <noreply@example.com>")

# Check if using external notification service
USE_NOTIFICATION_SERVICE = os.getenv("USE_NOTIFICATION_SERVICE", "False").lower() == "true"
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")


async def send_email_via_service(recipient_email: str, subject: str, body: str, html_body: Optional[str] = None):
    """
    Send email via the notification microservice
    """
    try:
        # Create notification payload
        payload = {
            "recipient_id": 0,  # This would normally be the user ID
            "recipient_email": recipient_email,
            "subject": subject,
            "body": body,
            "html_body": html_body
        }

        # Send to notification service
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{NOTIFICATION_SERVICE_URL}/notifications/email",
                    json=payload,
                    headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200 or response.status == 202:
                    logger.info(f"Email sent to {recipient_email} via notification service")
                    return True
                else:
                    logger.error(f"Failed to send email via notification service: {await response.text()}")
                    return False

    except Exception as e:
        logger.error(f"Error sending email via notification service: {str(e)}")
        return False


async def send_email_direct(recipient_email: str, subject: str, body: str, html_body: Optional[str] = None):
    """
    Send email directly via SMTP
    """
    try:
        # Create multipart message
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_FROM
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Add plain text body
        msg.attach(MIMEText(body, "plain"))

        # Add HTML body if provided
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, recipient_email, msg.as_string())

        logger.info(f"Email sent to {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


async def send_email(recipient_email: str, subject: str, body: str, html_body: Optional[str] = None):
    """
    Send email (either direct or via notification service)
    """
    if USE_NOTIFICATION_SERVICE:
        return await send_email_via_service(recipient_email, subject, body, html_body)
    else:
        return await send_email_direct(recipient_email, subject, body, html_body)


async def send_password_reset_email(email: str, username: str, reset_url: str):
    """
    Send a password reset email

    Args:
        email: Recipient email address
        username: Username of the recipient
        reset_url: Password reset URL
    """
    subject = "Password Reset - Learning Management System"

    # Email content
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333;">
        <div style="max-width: a600px; margin: 0 auto; background-color: #f8f8f8; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h2 style="color: #4A6FDC;">Password Reset</h2>
            <p>Hello {username},</p>
            <p>We received a request to reset your password. If you didn't make this request, you can ignore this email.</p>
            <p>To reset your password, click the button below:</p>
            <p style="text-align: center;">
                <a href="{reset_url}" 
                   style="display: inline-block; background-color: #4A6FDC; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-weight: bold;">
                   Reset Password
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="background-color: #e9e9e9; padding: 10px; border-radius: 3px; word-break: break-all;">
                <a href="{reset_url}">{reset_url}</a>
            </p>
            <p>This link will expire in 24 hours.</p>
            <p>Best regards,<br>LMS Team</p>
        </div>
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

    return await send_email(email, subject, text_content, html_content)


async def send_verification_email(email: str, username: str, verification_url: str):
    """
    Send an email verification email

    Args:
        email: Recipient email address
        username: Username of the recipient
        verification_url: Email verification URL
    """
    subject = "Verify Your Email - Learning Management System"

    # Email content
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333;">
        <div style="max-width: a600px; margin: 0 auto; background-color: #f8f8f8; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h2 style="color: #4A6FDC;">Email Verification</h2>
            <p>Hello {username},</p>
            <p>Thank you for registering with our Learning Management System. To complete your registration, please verify your email address.</p>
            <p style="text-align: center;">
                <a href="{verification_url}" 
                   style="display: inline-block; background-color: #4A6FDC; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-weight: bold;">
                   Verify Email
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="background-color: #e9e9e9; padding: 10px; border-radius: 3px; word-break: break-all;">
                <a href="{verification_url}">{verification_url}</a>
            </p>
            <p>This link will expire in 3 days.</p>
            <p>Best regards,<br>LMS Team</p>
        </div>
    </body>
    </html>
    """

    # Plain text alternative
    text_content = f"""
    Email Verification

    Hello {username},

    Thank you for registering with our Learning Management System. To complete your registration, please verify your email address.

    Please click the link below or copy and paste it into your browser:

    {verification_url}

    This link will expire in 3 days.

    Best regards,
    LMS Team
    """

    return await send_email(email, subject, text_content, html_content)


async def send_welcome_email(email: str, username: str):
    """
    Send a welcome email after registration and verification

    Args:
        email: Recipient email address
        username: Username of the recipient
    """
    subject = "Welcome to the Learning Management System"

    # Email content
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333;">
        <div style="max-width: a600px; margin: 0 auto; background-color: #f8f8f8; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h2 style="color: #4A6FDC;">Welcome to the LMS!</h2>
            <p>Hello {username},</p>
            <p>Thank you for joining our Learning Management System. Your account has been successfully activated.</p>
            <p>With your account, you can:</p>
            <ul>
                <li>Enroll in courses</li>
                <li>Access learning materials</li>
                <li>Submit assignments</li>
                <li>Track your progress</li>
                <li>Interact with instructors and other students</li>
            </ul>
            <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
            <p>Happy learning!</p>
            <p>Best regards,<br>LMS Team</p>
        </div>
    </body>
    </html>
    """

    # Plain text alternative
    text_content = f"""
    Welcome to the Learning Management System!

    Hello {username},

    Thank you for joining our Learning Management System. Your account has been successfully activated.

    With your account, you can:
    - Enroll in courses
    - Access learning materials
    - Submit assignments
    - Track your progress
    - Interact with instructors and other students

    If you have any questions or need assistance, please don't hesitate to contact our support team.

    Happy learning!

    Best regards,
    LMS Team
    """

    return await send_email(email, subject, text_content, html_content)