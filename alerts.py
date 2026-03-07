import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os

logger = logging.getLogger(__name__)

class AlertSystem:
    """Handles sending email alerts for critical failures."""

    def __init__(self, smtp_config: dict):
        self.smtp_host = smtp_config.get("host")
        self.smtp_port = smtp_config.get("port")
        self.email = smtp_config.get("email")
        self.password = smtp_config.get("password")
        self.recipient = smtp_config.get("recipient")

        # Check if the alert system is configured
        self.is_configured = all([self.smtp_host, self.smtp_port, self.email, self.password, self.recipient])
        if not self.is_configured:
            logger.warning("Alert system is not fully configured. No alerts will be sent.")

    def send_alert(self, subject: str, message: str):
        """Sends an email alert if the system is configured."""
        if not self.is_configured:
            return

        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = self.recipient
        msg['Subject'] = f"[YouTube Automation Alert] {subject}"
        
        msg.attach(MIMEText(message, 'plain'))
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            logger.info(f"Alert sent successfully to {self.recipient}")
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")

    def alert_failure(self, error_message: str):
        """Sends a standardized failure alert."""
        subject = "Video Creation Failed"
        message = (
            "The YouTube automation script encountered a critical error.\n\n"
            f"Error Details:\n{error_message}\n\n"
            "Please check the logs for more information."
        )
        self.send_alert(subject, message)
