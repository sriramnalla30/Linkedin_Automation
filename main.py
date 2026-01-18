"""
LinkedIn Automation - Main Runner
Run this script to start the automation
"""

import sys
import time
import argparse
from datetime import datetime

from config import DATABASE_PATH, CSV_FILE_PATH, SETTINGS
from database import DatabaseManager
from linkedin_bot import LinkedInBot
from csv_processor import process_csv_file


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════╗
║         🤖 LINKEDIN AUTOMATION BOT by Sriram 🤖            ║
║                                                            ║
║  Automate connection requests & personalized messages      ║
╚═══════════════════════════════════════════════════════════╝
    """)


def import_csv(csv_path: str = None):
    """Import contacts from CSV file"""
    db = DatabaseManager(DATABASE_PATH)
    csv_file = csv_path or CSV_FILE_PATH
    process_csv_file(csv_file, db)
    db.print_summary()


def send_connection_requests():
    """Send connection requests to contacts from CSV"""
    db = DatabaseManager(DATABASE_PATH)
    bot = LinkedInBot(db)
    
    try:
        if not bot.login():
            print("❌ Login failed. Please check credentials.")
            return
        
        # Get contacts to connect with
        contacts = db.get_contacts_to_connect()
        
        if not contacts:
            print("📭 No new contacts to connect with!")
            db.print_summary()
            return
        
        print(f"\n📋 Found {len(contacts)} contacts to connect with")
        
        successful = 0
        for contact in contacts:
            # Check daily limit
            if not db.can_send_more_requests(SETTINGS["max_connection_requests_per_day"]):
                print("\n⚠️ Daily connection request limit reached!")
                break
            
            success, status = bot.send_connection_request(
                profile_url=contact["linkedin_url"],
                name=contact["name"],
                contact_id=contact["id"]
            )
            
            if success:
                successful += 1
            
            # Random delay between requests
            bot._random_delay(5, 10)
        
        print(f"\n✅ Sent {successful} connection requests")
        db.print_summary()
        
    finally:
        input("\nPress Enter to close browser...")
        bot.close()


def check_and_message_accepted():
    """Check for accepted connections and send messages"""
    db = DatabaseManager(DATABASE_PATH)
    bot = LinkedInBot(db)
    
    try:
        if not bot.login():
            print("❌ Login failed. Please check credentials.")
            return
        
        # Check for accepted connections
        newly_accepted = bot.check_accepted_connections()
        print(f"\n✅ Found {len(newly_accepted)} newly accepted connections")
        
        # Get all accepted connections that need messages
        to_message = db.get_accepted_not_messaged()
        
        if not to_message:
            print("📭 No connections to message!")
            db.print_summary()
            return
        
        print(f"\n💬 {len(to_message)} connections need messages")
        
        successful = 0
        for contact in to_message:
            # Check daily limit
            if not db.can_send_more_messages(SETTINGS["max_messages_per_day"]):
                print("\n⚠️ Daily message limit reached!")
                break
            
            success, status = bot.send_message(
                profile_url=contact["linkedin_url"],
                name=contact["name"],
                gender=contact.get("gender"),
                contact_id=contact.get("contact_id")
            )
            
            if success:
                successful += 1
            
            # Random delay between messages
            bot._random_delay(10, 20)
        
        print(f"\n✅ Sent {successful} messages")
        db.print_summary()
        
    finally:
        input("\nPress Enter to close browser...")
        bot.close()


def full_automation():
    """Run complete automation cycle"""
    db = DatabaseManager(DATABASE_PATH)
    bot = LinkedInBot(db)
    
    try:
        if not bot.login():
            print("❌ Login failed. Please check credentials.")
            return
        
        print("\n" + "="*50)
        print("PHASE 1: Sending Connection Requests")
        print("="*50)
        
        contacts = db.get_contacts_to_connect()
        successful_requests = 0
        
        for contact in contacts:
            if not db.can_send_more_requests(SETTINGS["max_connection_requests_per_day"]):
                print("\n⚠️ Daily connection request limit reached!")
                break
            
            success, _ = bot.send_connection_request(
                profile_url=contact["linkedin_url"],
                name=contact["name"],
                contact_id=contact["id"]
            )
            
            if success:
                successful_requests += 1
            
            bot._random_delay(5, 10)
        
        print(f"\n✅ Sent {successful_requests} connection requests")
        
        print("\n" + "="*50)
        print("PHASE 2: Checking Accepted Connections")
        print("="*50)
        
        newly_accepted = bot.check_accepted_connections()
        
        print("\n" + "="*50)
        print("PHASE 3: Sending Messages to Accepted Connections")
        print("="*50)
        
        to_message = db.get_accepted_not_messaged()
        successful_messages = 0
        
        for contact in to_message:
            if not db.can_send_more_messages(SETTINGS["max_messages_per_day"]):
                print("\n⚠️ Daily message limit reached!")
                break
            
            success, _ = bot.send_message(
                profile_url=contact["linkedin_url"],
                name=contact["name"],
                gender=contact.get("gender"),
                contact_id=contact.get("contact_id")
            )
            
            if success:
                successful_messages += 1
            
            bot._random_delay(10, 20)
        
        print(f"\n✅ Sent {successful_messages} messages")
        
        db.print_summary()
        
    finally:
        input("\nPress Enter to close browser...")
        bot.close()


def scan_my_connections():
    """Scan your existing LinkedIn connections"""
    db = DatabaseManager(DATABASE_PATH)
    bot = LinkedInBot(db)
    
    try:
        if not bot.login():
            print("❌ Login failed.")
            return
        
        print("\n🔍 This will scan your existing connections.")
        print("   Recruiters found will be marked for messaging.")
        
        connections = bot.scan_existing_connections(is_recruiter=True)
        
        print(f"\n✅ Scanned {len(connections)} connections")
        db.print_summary()
        
    finally:
        input("\nPress Enter to close browser...")
        bot.close()


def show_status():
    """Show current status and statistics"""
    db = DatabaseManager(DATABASE_PATH)
    db.print_summary()
    
    # Show pending requests
    pending = db.get_pending_requests()
    if pending:
        print("\n⏳ Pending Connection Requests:")
        for p in pending[:10]:  # Show first 10
            print(f"   - {p['name']}")
        if len(pending) > 10:
            print(f"   ... and {len(pending) - 10} more")
    
    # Show accepted but not messaged
    to_message = db.get_accepted_not_messaged()
    if to_message:
        print("\n💬 Accepted - Need to Message:")
        for m in to_message[:10]:
            print(f"   - {m['name']}")
        if len(to_message) > 10:
            print(f"   ... and {len(to_message) - 10} more")


def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description='LinkedIn Automation Bot')
    parser.add_argument('action', nargs='?', default='menu',
                       choices=['menu', 'import', 'connect', 'message', 'full', 'scan', 'status'],
                       help='Action to perform')
    parser.add_argument('--csv', type=str, help='Path to CSV file for import')
    
    args = parser.parse_args()
    
    if args.action == 'menu':
        show_menu()
    elif args.action == 'import':
        import_csv(args.csv)
    elif args.action == 'connect':
        send_connection_requests()
    elif args.action == 'message':
        check_and_message_accepted()
    elif args.action == 'full':
        full_automation()
    elif args.action == 'scan':
        scan_my_connections()
    elif args.action == 'status':
        show_status()


def show_menu():
    """Interactive menu"""
    while True:
        print("\n" + "="*50)
        print("📋 MAIN MENU")
        print("="*50)
        print("1. 📄 Import contacts from CSV file")
        print("2. 🔗 Send connection requests")
        print("3. 💬 Check accepted & send messages")
        print("4. 🚀 Full automation (connect + check + message)")
        print("5. 🔍 Scan my existing connections")
        print("6. 📊 Show status")
        print("7. ❌ Exit")
        print("="*50)
        
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == '1':
            csv_path = input("Enter CSV file path (or press Enter for default): ").strip()
            import_csv(csv_path if csv_path else None)
        elif choice == '2':
            send_connection_requests()
        elif choice == '3':
            check_and_message_accepted()
        elif choice == '4':
            full_automation()
        elif choice == '5':
            scan_my_connections()
        elif choice == '6':
            show_status()
        elif choice == '7':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
