"""
Smart Connection Check and Messaging
Uses notifications and connections page instead of visiting each profile
"""

from linkedin_bot import LinkedInBot
from database import DatabaseManager
from config import LINKEDIN_CREDENTIALS

def main():
    print("=" * 60)
    print("🚀 SMART CONNECTION CHECK & MESSAGING")
    print("=" * 60)
    
    db = DatabaseManager()
    bot = LinkedInBot(db)
    
    try:
        # Login
        print("\n1️⃣ Logging in...")
        if not bot.login():
            print("❌ Login failed!")
            return
        
        # Use the new smart method to check accepted connections
        print("\n2️⃣ Checking for accepted connections (Smart Mode)...")
        accepted = bot.check_accepted_connections()
        print(f"\n✅ Found {len(accepted)} newly accepted connections")
        
        # Get contacts needing messages
        print("\n3️⃣ Getting contacts that need messages...")
        contacts_needing_messages = bot.db.get_accepted_not_messaged()
        print(f"📧 {len(contacts_needing_messages)} contacts need messages:")
        for c in contacts_needing_messages:
            print(f"   - {c['name']}")
        
        # Send messages
        if contacts_needing_messages:
            print("\n4️⃣ Sending messages...")
            for contact in contacts_needing_messages:
                profile_url = contact.get('linkedin_url') or contact.get('profile_url')
                name = contact.get('name')
                gender = contact.get('gender')
                contact_id = contact.get('id')
                
                success, msg = bot.send_message(profile_url, name, gender, contact_id)
                if success:
                    print(f"   ✅ Messaged: {name}")
                else:
                    print(f"   ❌ Failed: {name} - {msg}")
        else:
            print("\n4️⃣ No messages to send")
        
        # Stats
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        pending_count = len(bot.db.get_pending_requests())
        accepted_not_messaged = len(bot.db.get_accepted_not_messaged())
        print(f"   ⏳ Pending requests: {pending_count}")
        print(f"   📬 Accepted needing messages: {accepted_not_messaged}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        bot.close()
        print("\n✅ Done!")

if __name__ == "__main__":
    main()
