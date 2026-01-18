"""
Auto Scheduler - Runs automatically to check for accepted connections
This script checks periodically for accepted connections and sends messages

For truly automatic operation:
1. Run this script manually: python auto_scheduler.py
2. OR set up Windows Task Scheduler (see setup_scheduler.bat)
"""

import time
import sys
import os
from datetime import datetime

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_PATH, SETTINGS
from database import DatabaseManager
from linkedin_bot import LinkedInBot


def log(message: str):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    
    # Also log to file
    with open("automation_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def check_and_message():
    """
    Check for accepted connections and send messages
    This is the main function that runs periodically
    """
    log("🔄 Starting check cycle...")
    
    db = DatabaseManager(DATABASE_PATH)
    bot = LinkedInBot(db)
    
    try:
        # Login
        log("🔐 Logging into LinkedIn...")
        if not bot.login():
            log("❌ Login failed!")
            return False
        
        log("✅ Logged in successfully")
        
        # Check for accepted connections
        log("🔍 Checking for accepted connections...")
        pending = db.get_pending_requests()
        log(f"   Found {len(pending)} pending requests to check")
        
        newly_accepted = bot.check_accepted_connections()
        log(f"✅ {len(newly_accepted)} new acceptances found!")
        
        # Send messages to accepted connections
        to_message = db.get_accepted_not_messaged()
        log(f"💬 {len(to_message)} connections need messages")
        
        messages_sent = 0
        for contact in to_message:
            if not db.can_send_more_messages(SETTINGS["max_messages_per_day"]):
                log("⚠️ Daily message limit reached!")
                break
            
            success, status = bot.send_message(
                profile_url=contact["linkedin_url"],
                name=contact["name"],
                gender=contact.get("gender"),
                contact_id=contact.get("contact_id")
            )
            
            if success:
                messages_sent += 1
                log(f"   ✅ Messaged: {contact['name']}")
            else:
                log(f"   ⏭️ Skipped: {contact['name']} - {status}")
            
            # Delay between messages
            bot._random_delay(10, 20)
        
        log(f"📊 Cycle complete: {messages_sent} messages sent")
        db.print_summary()
        
        return True
        
    except Exception as e:
        log(f"❌ Error: {e}")
        return False
        
    finally:
        bot.close()
        log("🔒 Browser closed")


def run_once():
    """Run the check once and exit"""
    log("="*50)
    log("🚀 LINKEDIN AUTO-CHECKER (Single Run)")
    log("="*50)
    check_and_message()
    log("✅ Done!")


def run_continuous(interval_minutes: int = 60):
    """
    Run continuously, checking every X minutes
    Keep this running in background to auto-detect accepts
    """
    log("="*50)
    log(f"🚀 LINKEDIN AUTO-CHECKER (Continuous - Every {interval_minutes} min)")
    log("="*50)
    log("Press Ctrl+C to stop")
    
    while True:
        try:
            check_and_message()
            
            log(f"😴 Sleeping for {interval_minutes} minutes...")
            log(f"   Next check at: {datetime.now().strftime('%H:%M')} + {interval_minutes} min")
            
            # Sleep in small intervals so we can catch Ctrl+C
            for _ in range(interval_minutes * 60):
                time.sleep(1)
                
        except KeyboardInterrupt:
            log("\n⛔ Stopped by user")
            break
        except Exception as e:
            log(f"❌ Error: {e}")
            log("   Waiting 5 minutes before retry...")
            time.sleep(300)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Auto Scheduler')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in minutes (default: 30)')
    
    args = parser.parse_args()
    
    if args.once:
        run_once()
    else:
        run_continuous(args.interval)
