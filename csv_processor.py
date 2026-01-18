"""
CSV Processor for LinkedIn Automation
Imports contacts from CSV files into the database
"""

import csv
import os
from typing import List, Dict
from database import DatabaseManager
from gender_detector import detect_gender


def process_csv_file(csv_path: str, db: DatabaseManager) -> Dict:
    """
    Process a CSV file and import contacts into the database
    Returns stats about the import
    """
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return {"success": False, "error": "File not found"}
    
    stats = {
        "total_rows": 0,
        "imported": 0,
        "skipped": 0,
        "errors": 0
    }
    
    print(f"\n📄 Processing CSV: {csv_path}")
    print("-" * 50)
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            stats["total_rows"] += 1
            
            try:
                # Extract data from CSV (adjust column names as needed)
                name = row.get('Person_Name', row.get('Name', row.get('name', '')))
                linkedin_url = row.get('LinkedIn_URL', row.get('LinkedIn', row.get('linkedin_url', '')))
                email = row.get('Email', row.get('email', ''))
                company = row.get('Company', row.get('company', ''))
                position = row.get('Position', row.get('position', row.get('Title', '')))
                location = row.get('Location', row.get('location', ''))
                contact_type = row.get('Contact_Type', row.get('contact_type', ''))
                
                # Skip if no LinkedIn URL or if it's not a person (job posting, company page)
                if not linkedin_url or not name:
                    stats["skipped"] += 1
                    continue
                
                # Skip company pages and job postings
                if 'company' in linkedin_url.lower() or 'jobs' in linkedin_url.lower():
                    print(f"⏭️  Skipping (not a person): {name}")
                    stats["skipped"] += 1
                    continue
                
                # Determine if this is a recruiter/company person (not friend/junior)
                is_recruiter = _is_recruiter_contact(position, contact_type, name)
                
                # Detect gender
                gender = detect_gender(name)
                
                # Add to database
                success = db.add_contact_from_csv(
                    name=name,
                    linkedin_url=linkedin_url,
                    email=email,
                    company=company,
                    position=position,
                    location=location,
                    contact_type=contact_type,
                    is_recruiter=is_recruiter,
                    gender=gender
                )
                
                if success:
                    print(f"✅ Imported: {name} ({position}) - Gender: {gender}")
                    stats["imported"] += 1
                else:
                    print(f"⏭️  Already exists: {name}")
                    stats["skipped"] += 1
                    
            except Exception as e:
                print(f"❌ Error processing row: {e}")
                stats["errors"] += 1
    
    print("-" * 50)
    print(f"📊 Import Summary:")
    print(f"   Total Rows: {stats['total_rows']}")
    print(f"   Imported: {stats['imported']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Errors: {stats['errors']}")
    
    return stats


def _is_recruiter_contact(position: str, contact_type: str, name: str) -> bool:
    """
    Determine if this contact is a recruiter/company person
    (not a friend, junior, or random connection)
    """
    if not position and not contact_type:
        return False
    
    position_lower = (position or '').lower()
    contact_type_lower = (contact_type or '').lower()
    
    # Keywords that indicate this is a recruiter/hiring person
    recruiter_keywords = [
        'talent', 'recruit', 'hr', 'human resource', 'hiring', 'staffing',
        'ta ', 'ta-', 'acquisition', 'people', 'ceo', 'cto', 'cfo', 'coo',
        'founder', 'co-founder', 'director', 'manager', 'lead', 'head',
        'vp', 'vice president', 'chief', 'principal', 'senior', 'staff',
        'engineer', 'scientist', 'researcher', 'developer', 'architect',
        'analyst', 'consultant', 'specialist', 'advisor', 'partner'
    ]
    
    # Check if any recruiter keyword is present
    for keyword in recruiter_keywords:
        if keyword in position_lower or keyword in contact_type_lower:
            return True
    
    # Check contact type specifically
    if 'hr' in contact_type_lower or 'tech' in contact_type_lower:
        return True
    
    return False


def process_multiple_csvs(csv_folder: str, db: DatabaseManager) -> Dict:
    """
    Process all CSV files in a folder
    """
    all_stats = {
        "files_processed": 0,
        "total_imported": 0,
        "total_skipped": 0
    }
    
    for filename in os.listdir(csv_folder):
        if filename.endswith('.csv'):
            csv_path = os.path.join(csv_folder, filename)
            stats = process_csv_file(csv_path, db)
            
            if stats.get("success") != False:
                all_stats["files_processed"] += 1
                all_stats["total_imported"] += stats.get("imported", 0)
                all_stats["total_skipped"] += stats.get("skipped", 0)
    
    return all_stats


if __name__ == "__main__":
    # Test CSV processing
    from config import CSV_FILE_PATH, DATABASE_PATH
    
    db = DatabaseManager(DATABASE_PATH)
    
    # Process the default CSV file
    process_csv_file(CSV_FILE_PATH, db)
    
    # Show summary
    db.print_summary()
