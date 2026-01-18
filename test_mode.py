"""
Test Mode - Safely test the LinkedIn automation without actually sending anything
"""

from config import DATABASE_PATH, CSV_FILE_PATH, MESSAGE_TEMPLATE
from database import DatabaseManager
from csv_processor import process_csv_file
from gender_detector import get_first_name, get_salutation, detect_gender
from profile_analyzer import analyze_profile, quick_student_check


def test_csv_import():
    """Test 1: Check if CSV import works"""
    print("\n" + "="*60)
    print("🧪 TEST 1: CSV Import")
    print("="*60)
    
    db = DatabaseManager(DATABASE_PATH)
    
    # Show current state
    print("\n📊 Current Database State:")
    db.print_summary()
    
    # Process CSV
    print("\n📄 Processing CSV file...")
    process_csv_file(CSV_FILE_PATH, db)
    
    # Get contacts ready to connect
    contacts = db.get_contacts_to_connect()
    
    print(f"\n✅ {len(contacts)} contacts ready for connection requests:")
    for i, c in enumerate(contacts, 1):
        gender = c.get('gender', detect_gender(c['name']))
        salutation = "Sir" if gender == 'male' else "Ma'am" if gender == 'female' else "Sir/Ma'am"
        print(f"   {i}. {c['name']} ({salutation}) - {c.get('position', 'N/A')[:40]}")
    
    return len(contacts) > 0


def test_gender_detection():
    """Test 2: Check gender detection"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Gender Detection (Sir/Ma'am)")
    print("="*60)
    
    db = DatabaseManager(DATABASE_PATH)
    contacts = db.get_contacts_to_connect()
    
    print("\n👤 Gender Detection Results:")
    for c in contacts:
        name = c['name']
        gender = detect_gender(name)
        first_name = get_first_name(name)
        salutation = get_salutation(name)
        print(f"   {name:25} → {first_name} {salutation}")
    
    return True


def test_message_preview():
    """Test 3: Preview messages that would be sent"""
    print("\n" + "="*60)
    print("🧪 TEST 3: Message Preview")
    print("="*60)
    
    db = DatabaseManager(DATABASE_PATH)
    contacts = db.get_contacts_to_connect()
    
    if not contacts:
        print("❌ No contacts to preview")
        return False
    
    # Show message for first contact
    contact = contacts[0]
    first_name = get_first_name(contact['name'])
    salutation = get_salutation(contact['name'])
    
    message = MESSAGE_TEMPLATE.format(name=first_name, salutation=salutation)
    
    print(f"\n📧 Sample message for: {contact['name']}")
    print("-" * 50)
    print(message[:500] + "..." if len(message) > 500 else message)
    print("-" * 50)
    
    return True


def test_profile_analysis():
    """Test 4: Test student vs professional detection"""
    print("\n" + "="*60)
    print("🧪 TEST 4: Student vs Professional Detection")
    print("="*60)
    
    test_headlines = [
        ("Praseeth VM", "Talent Acquisition Partner - Tech/Data/Product at Uniphore"),
        ("Rahul Kumar", "B.Tech CSE Student at VIT Vellore | Aspiring Developer"),
        ("Bismita Deka", "Talent Acquisition Specialist at Uniphore"),
        ("Neha Singh", "Final Year Student | Looking for Opportunities"),
        ("Ravi Mayuram", "CTO & EVP Engineering at Uniphore"),
    ]
    
    print("\n🔍 Profile Analysis:")
    for name, headline in test_headlines:
        is_student = quick_student_check(headline)
        gender = detect_gender(name)
        salutation = "Sir" if gender == 'male' else "Ma'am"
        status = "❌ SKIP (Student)" if is_student else "✅ MESSAGE (Professional)"
        print(f"   {name} ({salutation}): {status}")
        print(f"      Headline: {headline[:50]}...")
    
    return True


def test_database_tracking():
    """Test 5: Test duplicate prevention"""
    print("\n" + "="*60)
    print("🧪 TEST 5: Duplicate Prevention")
    print("="*60)
    
    db = DatabaseManager(DATABASE_PATH)
    
    # Check various tracking
    test_url = "https://linkedin.com/in/test-user"
    
    print("\n🔒 Duplicate Prevention Check:")
    print(f"   Request already sent to {test_url}? {db.is_request_already_sent(test_url)}")
    print(f"   Message already sent to {test_url}? {db.is_message_already_sent(test_url)}")
    print(f"   Already connected with {test_url}? {db.is_existing_connection(test_url)}")
    
    # Show daily limits
    stats = db.get_daily_stats()
    print(f"\n📊 Today's Activity:")
    print(f"   Connection requests sent: {stats['connection_requests_sent']}/25")
    print(f"   Messages sent: {stats['messages_sent']}/50")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║          🧪 LINKEDIN AUTOMATION - TEST MODE 🧪             ║
║                                                            ║
║   Testing without actually connecting or messaging         ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    tests = [
        ("CSV Import", test_csv_import),
        ("Gender Detection", test_gender_detection),
        ("Message Preview", test_message_preview),
        ("Profile Analysis", test_profile_analysis),
        ("Database Tracking", test_database_tracking),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✅ PASS" if result else "❌ FAIL"))
        except Exception as e:
            results.append((name, f"❌ ERROR: {e}"))
    
    print("\n" + "="*60)
    print("📋 TEST RESULTS SUMMARY")
    print("="*60)
    for name, result in results:
        print(f"   {name}: {result}")
    
    print("\n" + "="*60)
    print("🎯 NEXT STEPS:")
    print("="*60)
    print("   1. If all tests pass, run: python main.py")
    print("   2. Choose option 2 to send connection requests")
    print("   3. Wait for people to accept")
    print("   4. Run option 3 to check accepted & send messages")
    print("   5. Or use option 4 for full automation")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
