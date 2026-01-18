"""
Email Sender for LinkedIn Research Agent
Sends personalized cold emails to leads with found email addresses
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import EMAIL_SETTINGS, EMAIL_SUBJECT, MESSAGE_TEMPLATE

class EmailSender:
    def __init__(self):
        self.sender_email = EMAIL_SETTINGS.get("sender_email")
        self.sender_password = EMAIL_SETTINGS.get("sender_password")
        self.smtp_server = EMAIL_SETTINGS.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = EMAIL_SETTINGS.get("smtp_port", 587)
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.sender_email and self.sender_password)
    
    def create_email_body(self, name: str, salutation: str = "Sir") -> str:
        """Create personalized email body from template"""
        # Use the same message template as LinkedIn
        message = MESSAGE_TEMPLATE.format(name=name, salutation=salutation)
        return message
    
    def send_email(self, to_email: str, name: str, salutation: str = "Sir") -> bool:
        """Send a personalized email"""
        if not self.is_configured():
            print("❌ Email not configured. Please set sender_password in config.py")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = EMAIL_SUBJECT
            msg["From"] = self.sender_email
            msg["To"] = to_email
            
            # Create body
            body = self.create_email_body(name, salutation)
            
            # Add plain text
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            print(f"✅ Email sent to {name} ({to_email})")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("❌ Email authentication failed. Check your app password.")
            return False
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False


def setup_gmail_app_password():
    """Instructions for setting up Gmail App Password"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           HOW TO SET UP GMAIL APP PASSWORD                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  1. Go to: https://myaccount.google.com/security             ║
║                                                               ║
║  2. Enable 2-Step Verification if not already enabled        ║
║                                                               ║
║  3. Go to: https://myaccount.google.com/apppasswords         ║
║                                                               ║
║  4. Create a new app password:                                ║
║     - App: "Mail"                                             ║
║     - Device: "Windows Computer"                              ║
║                                                               ║
║  5. Copy the 16-character password                            ║
║                                                               ║
║  6. Paste it in config.py under:                              ║
║     EMAIL_SETTINGS["sender_password"] = "your-app-password"  ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    setup_gmail_app_password()
