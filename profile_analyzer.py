"""
Profile Analyzer using Gemini AI
Determines if a LinkedIn profile is a working professional or student
"""

from google import genai
from google.genai import types
from typing import Dict, Tuple
import re

# Configure Gemini
GEMINI_API_KEY = "AIzaSyAahIF4PK_Bs5aYFX11z_k3ZDm_zX3gy5I"

# Create client
client = genai.Client(api_key=GEMINI_API_KEY)


def analyze_profile(name: str, headline: str, position: str = None) -> Dict:
    """
    Analyze a LinkedIn profile to determine:
    1. Is this a working professional (not a student)?
    2. Should we send them a job-seeking message?
    3. What is their likely gender?
    
    Returns: {
        'is_working_professional': bool,
        'is_student': bool,
        'should_message': bool,
        'gender': 'male' | 'female' | 'unknown',
        'reason': str
    }
    """
    
    # Combine available info
    profile_info = f"Name: {name}"
    if headline:
        profile_info += f"\nHeadline: {headline}"
    if position:
        profile_info += f"\nPosition: {position}"
    
    prompt = f"""Analyze this LinkedIn profile and answer these questions:

{profile_info}

1. Is this person currently WORKING at a company (employee, not student/intern at college)?
2. Is this person a STUDENT (undergraduate, graduate, pursuing degree)?
3. Should a job-seeker send them a professional message asking for opportunities?
4. What is the person's likely gender based on their name?

IMPORTANT RULES:
- Students, undergraduates, people "studying at", "pursuing degree", "aspiring", "fresher looking for" = DO NOT MESSAGE
- Working professionals with job titles (Engineer, Manager, Recruiter, Developer, etc.) = OK TO MESSAGE
- Company founders, CEOs, CTOs, HR, Recruiters = DEFINITELY MESSAGE
- People with "Student", "Pursuing", "Studying", "B.Tech", "M.Tech", "Aspirant" in headline = DO NOT MESSAGE

Respond in this exact format:
IS_WORKING: YES or NO
IS_STUDENT: YES or NO
SHOULD_MESSAGE: YES or NO
GENDER: MALE or FEMALE or UNKNOWN
REASON: Brief explanation
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        result_text = response.text.upper()
        
        # Parse response
        is_working = "IS_WORKING: YES" in result_text
        is_student = "IS_STUDENT: YES" in result_text
        should_message = "SHOULD_MESSAGE: YES" in result_text
        
        # Parse gender
        if "GENDER: FEMALE" in result_text:
            gender = "female"
        elif "GENDER: MALE" in result_text:
            gender = "male"
        else:
            gender = "unknown"
        
        # Extract reason
        reason = "AI Analysis"
        if "REASON:" in result_text:
            reason_match = re.search(r'REASON:\s*(.+?)(?:\n|$)', result_text, re.IGNORECASE)
            if reason_match:
                reason = reason_match.group(1).strip()
        
        return {
            'is_working_professional': is_working and not is_student,
            'is_student': is_student,
            'should_message': should_message and not is_student,
            'gender': gender,
            'reason': reason
        }
        
    except Exception as e:
        print(f"⚠️ Gemini API error: {e}")
        # Fallback to rule-based detection
        return fallback_analyze(name, headline, position)


def fallback_analyze(name: str, headline: str, position: str = None) -> Dict:
    """
    Fallback rule-based analysis when Gemini is unavailable
    """
    text = f"{headline or ''} {position or ''}".lower()
    
    # Student indicators - DO NOT MESSAGE
    student_keywords = [
        'student', 'studying', 'pursuing', 'undergraduate', 'graduate',
        'b.tech', 'm.tech', 'btech', 'mtech', 'b.e', 'm.e', 'bca', 'mca',
        'fresher', 'aspiring', 'looking for', 'seeking', 'learner',
        'college', 'university', 'institute', 'school', 'academy',
        'intern at college', 'campus', 'batch of', 'class of',
        'final year', 'third year', 'second year', 'first year',
        'passout', 'pass out', 'graduated from', 'alumnus looking'
    ]
    
    # Working professional indicators - OK TO MESSAGE
    professional_keywords = [
        'engineer', 'developer', 'manager', 'director', 'lead', 'head',
        'recruiter', 'talent', 'hr', 'human resource', 'hiring',
        'ceo', 'cto', 'cfo', 'coo', 'founder', 'co-founder', 'owner',
        'vp', 'vice president', 'president', 'chief', 'officer',
        'architect', 'scientist', 'researcher', 'analyst', 'consultant',
        'specialist', 'advisor', 'partner', 'associate', 'senior',
        'principal', 'staff', 'team lead', 'tech lead', 'project',
        'product', 'program', 'operations', 'business', 'sales',
        'marketing', 'finance', 'legal', 'admin', 'executive',
        'working at', 'employed at', 'at google', 'at microsoft',
        'at amazon', 'at meta', 'at apple', 'at netflix'
    ]
    
    is_student = any(kw in text for kw in student_keywords)
    is_professional = any(kw in text for kw in professional_keywords)
    
    # Gender detection from name
    from gender_detector import detect_gender
    gender = detect_gender(name)
    
    should_message = is_professional and not is_student
    
    reason = "Student profile - skip" if is_student else "Working professional - OK" if is_professional else "Unknown profile type"
    
    return {
        'is_working_professional': is_professional and not is_student,
        'is_student': is_student,
        'should_message': should_message,
        'gender': gender,
        'reason': reason
    }


def quick_student_check(headline: str) -> bool:
    """
    Quick check if headline indicates a student (fast, no API call)
    Returns True if likely a student
    """
    if not headline:
        return False
    
    text = headline.lower()
    
    student_indicators = [
        'student', 'studying', 'pursuing', 'b.tech', 'm.tech', 'btech', 'mtech',
        'undergraduate', 'graduate student', 'fresher', 'aspiring', 'learner',
        'college', 'university', 'batch of', 'class of', 'final year',
        '1st year', '2nd year', '3rd year', '4th year', 'year student'
    ]
    
    return any(indicator in text for indicator in student_indicators)


# Test the analyzer
if __name__ == "__main__":
    test_profiles = [
        ("Praseeth VM", "Talent Acquisition Partner - Tech/Data/Product at Uniphore"),
        ("Rahul Kumar", "B.Tech CSE Student at VIT Vellore | Aspiring Software Developer"),
        ("Bismita Deka", "Talent Acquisition Specialist at Uniphore | Actively Hiring"),
        ("Neha Singh", "Final Year Student | Looking for Opportunities"),
        ("Ravi Mayuram", "CTO & EVP Engineering at Uniphore"),
        ("Amit Sharma", "Software Engineer at Google"),
        ("Priya Patel", "Pursuing M.Tech in AI/ML at IIT Delhi"),
    ]
    
    print("Profile Analysis Test:")
    print("=" * 70)
    
    for name, headline in test_profiles:
        result = analyze_profile(name, headline)
        status = "✅ MESSAGE" if result['should_message'] else "❌ SKIP"
        gender = "Sir" if result['gender'] == 'male' else "Ma'am" if result['gender'] == 'female' else "?"
        print(f"\n{name} ({gender})")
        print(f"  Headline: {headline[:50]}...")
        print(f"  {status} - {result['reason']}")
