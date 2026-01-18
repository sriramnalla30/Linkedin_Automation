# 🤖 LinkedIn Automation Bot

Automate your LinkedIn outreach for job/internship applications.

## Features

✅ **Send Connection Requests** - Automatically connect with recruiters (without notes)  
✅ **Track Pending Requests** - Database tracks all sent requests  
✅ **Detect Accepted Connections** - Automatically checks who accepted  
✅ **Send Personalized Messages** - Auto-sends your message with their name & Sir/Ma'am  
✅ **Prevent Duplicates** - Never sends duplicate requests or messages  
✅ **Gender Detection** - Automatically determines Sir/Ma'am from name  
✅ **Rate Limiting** - Prevents account restrictions  
✅ **Human-like Behavior** - Random delays between actions  

## Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Chrome Browser
Make sure you have Google Chrome installed.

### 3. Configure Settings
Edit `config.py` to:
- Update your message template if needed
- Adjust rate limits (default: 25 requests/day, 50 messages/day)

## Usage

### Interactive Menu
```bash
python main.py
```
This opens an interactive menu with all options.

### Command Line Options

```bash
# Import contacts from CSV
python main.py import --csv "path/to/contacts.csv"

# Send connection requests only
python main.py connect

# Check accepted connections and send messages
python main.py message

# Full automation (connect + check + message)
python main.py full

# Scan your existing connections
python main.py scan

# Show status and statistics
python main.py status
```

## How It Works

### Phase 1: Import Contacts
- Load your CSV file with recruiter contacts
- Contacts are saved to SQLite database
- Gender is auto-detected for Sir/Ma'am

### Phase 2: Send Connection Requests
- Bot logs into your LinkedIn
- Sends connection requests (without notes)
- Tracks all pending requests

### Phase 3: Check Accepted & Message
- Checks which requests got accepted
- Sends personalized message to accepted connections
- Never sends duplicate messages

## CSV Format

Your CSV should have these columns (flexible naming):
- `Person_Name` or `Name`
- `LinkedIn_URL` or `LinkedIn`
- `Company` (optional)
- `Position` or `Title` (optional)

Example:
```csv
Person_Name,LinkedIn_URL,Company,Position
John Doe,https://linkedin.com/in/johndoe,Google,Tech Recruiter
```

## Safety Features

- **Rate Limiting**: Max 25 connections/day, 50 messages/day
- **Random Delays**: 3-8 seconds between actions
- **Duplicate Prevention**: Database tracks all activity
- **Session Persistence**: Stays logged in between runs

## ⚠️ Important Notes

1. **LinkedIn may detect automation** - Use responsibly
2. **Don't spam** - Keep daily limits low
3. **Security checkpoint** - You may need to verify manually sometimes
4. **Backup your database** - `linkedin_automation.db` contains all your tracking data

## Files Structure

```
📁 Linkedin_Automation/
├── 📄 main.py              # Main runner with menu
├── 📄 linkedin_bot.py      # Selenium automation
├── 📄 database.py          # SQLite tracking
├── 📄 csv_processor.py     # CSV import
├── 📄 gender_detector.py   # Sir/Ma'am detection
├── 📄 profile_analyzer.py  # Profile analysis
├── 📄 research_agent.py    # Company research agent
├── 📄 deep_research_agent.py # Advanced research with SerpAPI
├── 📄 auto_scheduler.py    # Background automation scheduler
├── 📄 config.example.py    # Example config (copy to config.py)
├── 📄 requirements.txt     # Python dependencies
├── 📄 START_AUTOMATION.bat # One-click automation starter
└── 📄 .gitignore           # Protect credentials
```

## Quick Start

1. Clone the repo
2. Copy `config.example.py` to `config.py`
3. Fill in your credentials in `config.py`
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `python main.py`

## Troubleshooting

### "Chrome not found"
- Install Google Chrome
- Or use webdriver-manager: `pip install webdriver-manager`

### "Login failed"
- Check credentials in `config.py`
- LinkedIn may have changed their UI - update selectors

### "Security checkpoint"
- Complete the verification manually in the browser
- Press Enter to continue

## Author

Built by **Sriram** for job hunting automation.

---
⚠️ **Disclaimer**: Use at your own risk. LinkedIn may restrict accounts that use automation. Keep your usage moderate and human-like.
