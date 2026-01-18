# LinkedIn Automation Configuration - EXAMPLE
# ⚠️ COPY this file to config.py and fill in your credentials
# ⚠️ NEVER commit config.py to git!

LINKEDIN_CREDENTIALS = {
    "email": "your_email@gmail.com",
    "password": "your_password"
}

# Gemini API Key for profile analysis (get from Google AI Studio)
GEMINI_API_KEY = "your_gemini_api_key"

# Research Agent API Keys
SERPAPI_KEY = "your_serpapi_key"  # Get from serpapi.com
GOOGLE_SEARCH_API_KEY = "your_google_api_key"  # Get from Google Cloud Console

# Email settings (for cold emails)
EMAIL_SETTINGS = {
    "sender_email": "your_email@gmail.com",
    "sender_password": "",  # Gmail App Password
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
}

# Email subject for cold emails
EMAIL_SUBJECT = "Your Subject Here"

# Rate limiting settings (to avoid LinkedIn restrictions)
SETTINGS = {
    "max_connection_requests_per_day": 25,
    "max_messages_per_day": 50,
    "delay_between_actions_min": 3,
    "delay_between_actions_max": 8,
    "check_accepted_interval_minutes": 30,
}

# Your personalized message template
# {name} will be replaced with recipient's first name
# {salutation} will be replaced with Sir/Ma'am based on gender
MESSAGE_TEMPLATE = """Hi {name} {salutation},

Your personalized message here.

Best regards"""

# Database file path
DATABASE_PATH = "linkedin_automation.db"

# CSV file path
CSV_FILE_PATH = "your_contacts.csv"
