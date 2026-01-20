# 🤖 LinkedIn Outreach Automation

An intelligent LinkedIn automation system that streamlines professional networking and job search outreach. This tool automates the entire workflow from researching target companies to sending personalized connection requests and follow-up messages.

---

## 🎬 Demo Video

[![Watch Demo](https://img.shields.io/badge/▶️_Watch_Demo-Google_Drive-4285F4?style=for-the-badge&logo=googledrive&logoColor=white)](https://drive.google.com/file/d/1RGs2ls-RjNtG59NE880ri6QxV67Ib0tM/view?usp=sharing)

**[▶️ Click here to watch the full demo](https://drive.google.com/file/d/1RGs2ls-RjNtG59NE880ri6QxV67Ib0tM/view?usp=sharing)**

---

## 📋 What Does This Project Do?

This automation tool helps job seekers and professionals efficiently expand their LinkedIn network by automating repetitive outreach tasks while maintaining a personalized, human-like approach.

### The Complete Workflow:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LINKEDIN OUTREACH AUTOMATION                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   📋 STEP 1: COMPANY RESEARCH                                               │
│   ┌──────────────────────────────────────────────────────────────────┐      │
│   │  Input: List of target companies (e.g., Google, Microsoft...)    │      │
│   │  Output: 10 best contacts per company                            │      │
│   │                                                                  │      │
│   │  Who we find:                                                    │      │
│   │  • 🎯 Hiring Managers (AI/ML, Engineering leads)                 │      │
│   │  • 👔 HR & Talent Acquisition professionals                      │      │
│   │  • 🎓 Alumni from your college working at the company            │      │
│   └──────────────────────────────────────────────────────────────────┘      │
│                              ⬇️                                             │
│   📤 STEP 2: SEND CONNECTION REQUESTS                                       │
│   ┌──────────────────────────────────────────────────────────────────┐      │
│   │  • Automatically visits each LinkedIn profile                    │      │
│   │  • Sends connection request (without note for higher acceptance) │      │
│   │  • Tracks all pending requests in database                       │      │
│   │  • Rate limited: 25 requests/day to avoid restrictions           │      │
│   └──────────────────────────────────────────────────────────────────┘      │
│                              ⬇️                                             │
│   🔍 STEP 3: SMART ACCEPTANCE DETECTION                                     │
│   ┌──────────────────────────────────────────────────────────────────┐      │
│   │  Instead of checking each profile (slow & suspicious), we:       │      │
│   │  • Check "Sent Invitations" page for pending requests            │      │
│   │  • Compare with our database to find who accepted                │      │
│   │  • Verify by checking if they're now "1st degree" connection     │      │
│   │  • Runs automatically every 30 minutes in background             │      │
│   └──────────────────────────────────────────────────────────────────┘      │
│                              ⬇️                                             │
│   💬 STEP 4: SEND PERSONALIZED MESSAGES                                     │
│   ┌──────────────────────────────────────────────────────────────────┐      │
│   │  When someone accepts:                                           │      │
│   │  • Opens their profile                                           │      │
│   │  • Detects gender for proper salutation (Sir/Ma'am)              │      │
│   │  • Checks if working professional (skips students)               │      │
│   │  • Sends personalized message with their name                    │      │
│   │  • Records in database to prevent duplicates                     │      │
│   └──────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🔬 Research Agent
- **SerpAPI Integration**: Uses Google search to find LinkedIn profiles at target companies
- **Smart Filtering**: Prioritizes hiring managers, HR professionals, and alumni
- **Location Filtering**: Focus on specific regions (e.g., India only)
- **Hire Potential Scoring**: Ranks contacts 0-10 based on likelihood to help with job search

### 🤖 Connection Automation
- **Anti-Detection Measures**: Random delays, human-like behavior patterns
- **Session Persistence**: Uses Chrome profile to stay logged in
- **Duplicate Prevention**: Never sends duplicate requests
- **Rate Limiting**: Configurable daily limits (default: 25 requests/day)

### 🔍 Smart Detection System
- **Efficient Checking**: Scans "Sent Invitations" page instead of visiting every profile
- **Verification**: Confirms "1st degree" status before messaging
- **Background Scheduler**: Runs every 30 minutes automatically

### 💬 Personalized Messaging
- **Name Extraction**: Uses first name for personal touch
- **Gender Detection**: Automatically determines Sir/Ma'am from name
- **Professional Filtering**: Only messages working professionals (skips students)
- **Template System**: Customizable message templates with variables

### 📊 Database Tracking
- **SQLite Database**: Tracks all contacts, requests, and messages
- **Status Tracking**: Pending → Accepted → Messaged
- **Analytics**: Success rates, daily stats, conversion metrics

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.8+** | Core programming language |
| **Selenium WebDriver** | Browser automation with anti-detection |
| **SQLite** | Local database for tracking |
| **SerpAPI** | Google search for finding profiles |
| **Gemini API** | AI-powered profile analysis (optional) |
| **Chrome** | Browser with persistent session |

---

## 📁 Project Structure

```
📦 Linkedin_Automation/
├── 🤖 Core Automation
│   ├── linkedin_bot.py        # Main Selenium automation logic
│   ├── database.py            # SQLite database management
│   └── auto_scheduler.py      # Background scheduler (every 30 min)
│
├── 🔬 Research Module
│   ├── deep_research_agent.py # SerpAPI + LinkedIn research
│   ├── research_agent.py      # Company contact finder
│   └── linkedin_researcher.py # Direct LinkedIn search
│
├── 🧠 Intelligence
│   ├── profile_analyzer.py    # AI-powered profile analysis
│   ├── gender_detector.py     # Name-based gender detection
│   └── csv_processor.py       # Import contacts from CSV
│
├── 📧 Communication
│   └── email_sender.py        # Cold email functionality
│
├── 🚀 Runners
│   ├── main.py                # Interactive menu
│   ├── run_smart_check.py     # Quick check & message
│   ├── run_research.py        # Research companies
│   └── START_AUTOMATION.bat   # One-click background start
│
└── ⚙️ Configuration
    ├── config.example.py      # Template (copy to config.py)
    ├── requirements.txt       # Python dependencies
    └── companies_to_apply.txt # Target company list
```

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/sriramnalla30/Linkedin_Automation.git
cd Linkedin_Automation
pip install -r requirements.txt
```

### 2. Configure
```bash
# Copy example config and fill in your credentials
cp config.example.py config.py
```

Edit `config.py`:
```python
LINKEDIN_CREDENTIALS = {
    "email": "your_email@gmail.com",
    "password": "your_password"
}

SERPAPI_KEY = "your_serpapi_key"  # For research agent
```

### 3. Add Target Companies
Edit `companies_to_apply.txt`:
```
Google
Microsoft
Amazon
Meta
OpenAI
```

### 4. Run Research Agent
```bash
python run_research.py
```
This finds 10 best contacts per company (HR, Hiring Managers, Alumni).

### 5. Start Automation
```bash
# Interactive menu
python main.py

# OR one-click background automation
# Double-click: START_AUTOMATION.bat
```

---

## 📊 How It Works - Detailed Flow

### Phase 1: Research 🔬
```
Input: "TrueFoundry" (company name)
         ↓
    SerpAPI Search:
    • "TrueFoundry AI ML hiring manager LinkedIn India"
    • "TrueFoundry HR talent acquisition LinkedIn"  
    • "TrueFoundry VIT alumni LinkedIn"
         ↓
    Found 83 LinkedIn profiles
         ↓
    Visit & Analyze top 20 profiles
         ↓
    Score each person (0-10) based on:
    • Job title relevance
    • Hiring authority
    • Alumni connection
         ↓
Output: 10 best contacts with scores
    • Parth Kathuria (CTO) - Score: 10/10
    • Avinash Gupta (ML Lead) - Score: 9/10
    • HR Manager - Score: 8/10
```

### Phase 2: Connect 📤
```
Load contacts from database
         ↓
For each contact:
    • Open LinkedIn profile
    • Check if already connected
    • Click "Connect" button
    • Wait 3-8 seconds (random)
         ↓
Track in database: status = "pending"
         ↓
Stop at daily limit (25/day)
```

### Phase 3: Detect Acceptances 🔍
```
Every 30 minutes:
         ↓
    Go to "Sent Invitations" page
         ↓
    Get list of pending invitations
         ↓
    Compare with our database
         ↓
    If someone NOT in pending list:
        → They accepted OR declined
         ↓
    Visit their profile to verify
        → Check for "1st" degree badge
         ↓
    If connected → Mark as "accepted"
```

### Phase 4: Message 💬
```
Get all accepted contacts not yet messaged
         ↓
For each contact:
    • Open their profile
    • Click "Message" button
    • Personalize message:
        - "Hi {FirstName} {Sir/Ma'am}..."
    • Send message
         ↓
Mark in database: messaged = true
```

---

## ⚙️ Configuration Options

```python
SETTINGS = {
    "max_connection_requests_per_day": 25,   # Daily limit
    "max_messages_per_day": 50,              # Message limit
    "delay_between_actions_min": 3,          # Minimum delay (seconds)
    "delay_between_actions_max": 8,          # Maximum delay (seconds)
    "check_accepted_interval_minutes": 30,   # Background check interval
}
```

---

## 🔒 Safety Features

| Feature | Description |
|---------|-------------|
| **Rate Limiting** | Respects LinkedIn's limits to avoid restrictions |
| **Random Delays** | 3-8 second delays mimic human behavior |
| **Session Persistence** | Uses Chrome profile, no repeated logins |
| **Duplicate Prevention** | Database ensures no duplicate requests/messages |
| **Anti-Detection** | Disables automation flags in Chrome |

---

## 📈 Results & Metrics

The bot tracks all activity and provides analytics:

- **Connections Sent**: Total requests sent
- **Acceptance Rate**: % of requests accepted
- **Messages Sent**: Total personalized messages
- **Pending Requests**: Waiting for response
- **Daily Stats**: Track progress over time

---

## ⚠️ Disclaimer

This tool is for educational purposes. Use responsibly and in accordance with LinkedIn's Terms of Service. The author is not responsible for any account restrictions resulting from automation.

**Best Practices:**
- Keep daily limits low (20-25 requests/day)
- Use personalized, genuine messages
- Don't spam - target relevant connections only
- Take breaks between sessions

---

## 👨‍💻 Author

**Sriram Nalla**  
Final Year Computer Science Student | VIT Vellore

- 🔗 [LinkedIn](https://www.linkedin.com/in/sri-ram-nalla-6a2a3324b/)
- 📧 sriramnalla30@gmail.com
- 💻 [GitHub](https://github.com/sriramnalla30)

---

## 🌟 Star This Repo

If this project helped you, please give it a ⭐ on GitHub!

[![GitHub stars](https://img.shields.io/github/stars/sriramnalla30/Linkedin_Automation?style=social)](https://github.com/sriramnalla30/Linkedin_Automation)

---
