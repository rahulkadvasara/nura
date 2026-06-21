"""
Nura - Email Service
SMTP email provider integration
"""

import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Handles sending transactional emails using SMTP"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        # Fallback sender email if SMTP_USER is not configured
        self.sender_email = settings.SMTP_USER or "no-reply@nura.health"

    async def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
        """Core method to send email via SMTP"""
        if not self.smtp_host or not self.smtp_user or not self.smtp_password:
            # Fallback for development if credentials are not present
            logger.warning(
                f"[SMTP Mock] Sending email to {to_email} | Subject: {subject} | Plain: {text_content or html_content[:100]}..."
            )
            return True

        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.APP_NAME} <{self.sender_email}>"
        message["To"] = to_email
        message["Subject"] = subject

        if text_content:
            message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        try:
            # Connect and send
            use_tls = self.smtp_port == 465
            start_tls = self.smtp_port == 587 or (self.smtp_port != 465 and not use_tls)

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=use_tls,
                start_tls=start_tls,
            )
            logger.info(f"Email successfully sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

    async def send_otp_email(self, email: str, otp: str, purpose_label: str = "registration") -> bool:
        """Sends an OTP email for verification"""
        subject = f"Your {settings.APP_NAME} Verification OTP"
        purpose_text = purpose_label.replace("_", " ")

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <h2>Welcome to {settings.APP_NAME}</h2>
                <p>Hello,</p>
                <p>Please use the following 6-digit One-Time Password (OTP) to complete your {purpose_text}:</p>
                <div style="font-size: 24px; font-weight: bold; background-color: #f0f0f0; padding: 15px; text-align: center; border-radius: 5px; letter-spacing: 5px; margin: 20px 0; max-width: 200px;">
                    {otp}
                </div>
                <p>This OTP is valid for 10 minutes. If you did not request this code, please ignore this email.</p>
                <br/>
                <p>Best regards,<br/>The {settings.APP_NAME} Team</p>
            </body>
        </html>
        """
        text_content = (
            f"Hello,\n\n"
            f"Please use the following 6-digit One-Time Password (OTP) to complete your {purpose_text}:\n\n"
            f"{otp}\n\n"
            f"This OTP is valid for 10 minutes. If you did not request this, please ignore this email.\n\n"
            f"Best regards,\n"
            f"The {settings.APP_NAME} Team"
        )

        return await self._send_email(email, subject, html_content, text_content)
