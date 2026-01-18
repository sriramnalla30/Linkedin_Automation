"""
Deep Research Agent with SerpAPI + LinkedIn
Comprehensive research to find people who can hire for Applied AI roles

This agent:
1. Uses SerpAPI to search Google for LinkedIn profiles
2. Visits each LinkedIn profile for detailed info
3. Analyzes if they can hire a fresher for Applied AI role
4. Creates comprehensive lead profiles with scoring
5. Takes 1 day per company for thorough research
"""

import time
import random
import re
import json
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from database import DatabaseManager
from config import LINKEDIN_CREDENTIALS, SERPAPI_KEY, GOOGLE_SEARCH_API_KEY


class DeepResearchAgent:
    """
    Comprehensive research agent for finding hiring contacts at companies.
    
    Target Profile Types:
    1. AI/ML Managers, Leads, Directors - Can directly hire for AI roles
    2. HR/Talent Acquisition - Handle the hiring process
    3. VIT Alumni - College connection for networking
    
    Research Process:
    1. SerpAPI Google search for LinkedIn profiles
    2. Visit each profile on LinkedIn
    3. Extract detailed information
    4. Analyze hiring potential
    5. Score and rank leads
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.serpapi_key = SERPAPI_KEY
        self.driver = None
        self.wait = None
        self.logged_in = False
        self.research_log = []
        self.leads_data = []
        
        # Search queries for different profile types
        self.search_templates = {
            "ai_roles": [
                '"{company}" "AI Manager" India site:linkedin.com/in',
                '"{company}" "Machine Learning" Manager India site:linkedin.com/in',
                '"{company}" "Applied AI" India site:linkedin.com/in',
                '"{company}" "ML Lead" India site:linkedin.com/in',
                '"{company}" "AI Engineering" India site:linkedin.com/in',
                '"{company}" "Data Science" Manager India site:linkedin.com/in',
                '"{company}" "Director" AI India site:linkedin.com/in',
                '"{company}" "Head of AI" India site:linkedin.com/in',
            ],
            "hr_roles": [
                '"{company}" "Talent Acquisition" India site:linkedin.com/in',
                '"{company}" HR Manager India site:linkedin.com/in',
                '"{company}" "Technical Recruiter" India site:linkedin.com/in',
                '"{company}" Recruiter India site:linkedin.com/in',
            ],
            "vit_alumni": [
                '"{company}" "VIT" India site:linkedin.com/in',
                '"{company}" "Vellore Institute of Technology" site:linkedin.com/in',
                '"{company}" "VIT Vellore" site:linkedin.com/in',
            ]
        }
    
    def _log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.research_log.append(log_entry)
    
    def _random_delay(self, min_sec: float = 2, max_sec: float = 5):
        """Human-like delay"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    # ==================== SERPAPI SEARCH ====================
    
    def search_google_serpapi(self, query: str) -> List[Dict]:
        """Search Google using SerpAPI"""
        self._log(f"🔍 SerpAPI: {query[:60]}...")
        
        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.serpapi_key,
                "num": 15,
                "gl": "in",  # India
                "hl": "en"
            }
            
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("organic_results", [])
                self._log(f"   ✅ Got {len(results)} results")
                return results
            else:
                self._log(f"   ❌ SerpAPI error: {response.status_code}", "ERROR")
                return []
        except Exception as e:
            self._log(f"   ❌ Request error: {e}", "ERROR")
            return []
    
    def extract_profiles_from_serp(self, results: List[Dict]) -> List[Dict]:
        """Extract LinkedIn profile info from SERP results"""
        profiles = []
        seen_urls = set()
        
        for result in results:
            link = result.get("link", "")
            
            # Only LinkedIn profile URLs
            if "linkedin.com/in/" not in link:
                continue
            
            # Clean URL
            linkedin_url = link.split("?")[0]
            
            if linkedin_url in seen_urls:
                continue
            seen_urls.add(linkedin_url)
            
            # Extract info from title and snippet
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            # Parse name from title
            name = ""
            position = ""
            if " - " in title:
                parts = title.replace(" | LinkedIn", "").split(" - ")
                name = parts[0].strip()
                if len(parts) > 1:
                    position = parts[1].strip()
            else:
                name = title.replace(" | LinkedIn", "").strip()
            
            # Check for India
            full_text = f"{title} {snippet}".lower()
            india_keywords = ["india", "bangalore", "bengaluru", "mumbai", "delhi", 
                            "hyderabad", "chennai", "pune", "noida", "gurgaon", "kolkata"]
            is_india = any(kw in full_text for kw in india_keywords)
            
            # Check for VIT
            is_vit = "vit" in full_text or "vellore" in full_text
            
            # Check for AI/ML
            ai_keywords = ["ai", "machine learning", "ml", "data science", "deep learning", "nlp"]
            is_ai = any(kw in full_text for kw in ai_keywords)
            
            # Check for HR
            hr_keywords = ["hr", "talent", "recruiter", "hiring", "human resource"]
            is_hr = any(kw in full_text for kw in hr_keywords)
            
            profiles.append({
                "name": name,
                "linkedin_url": linkedin_url,
                "position_from_serp": position,
                "snippet": snippet[:200],
                "is_india": is_india,
                "is_vit": is_vit,
                "is_ai": is_ai,
                "is_hr": is_hr,
                "source": "serpapi"
            })
        
        return profiles
    
    # ==================== LINKEDIN BROWSER ====================
    
    def _setup_driver(self):
        """Setup Chrome browser"""
        self._log("🚀 Setting up Chrome browser...")
        
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._log("✅ Browser ready!")
    
    def login_linkedin(self) -> bool:
        """Login to LinkedIn"""
        if self.driver is None:
            self._setup_driver()
        
        self._log("🔐 Logging into LinkedIn...")
        
        try:
            self.driver.get("https://www.linkedin.com/login")
            self._random_delay(2, 4)
            
            if "feed" in self.driver.current_url:
                self._log("✅ Already logged in!")
                self.logged_in = True
                return True
            
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.clear()
            for char in LINKEDIN_CREDENTIALS["email"]:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            for char in LINKEDIN_CREDENTIALS["password"]:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self._random_delay(1, 2)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            self._random_delay(3, 5)
            
            if "feed" in self.driver.current_url or "checkpoint" not in self.driver.current_url:
                self._log("✅ Login successful!")
                self.logged_in = True
                return True
            else:
                self._log("⚠️ Verification needed. Complete manually.")
                input("Press Enter after completing verification...")
                self.logged_in = True
                return True
                
        except Exception as e:
            self._log(f"❌ Login failed: {e}", "ERROR")
            return False
    
    def get_profile_details(self, linkedin_url: str, basic_info: Dict = None) -> Dict:
        """
        Visit LinkedIn profile and extract detailed information
        """
        if not self.logged_in:
            if not self.login_linkedin():
                return {}
        
        self._log(f"   📖 Visiting: {linkedin_url.split('/in/')[-1][:30]}...")
        
        details = {
            "linkedin_url": linkedin_url,
            "name": basic_info.get("name", "") if basic_info else "",
            "headline": "",
            "location": "",
            "about": "",
            "current_company": "",
            "current_position": "",
            "experience_summary": "",
            "education": "",
            "is_vit_alumni": basic_info.get("is_vit", False) if basic_info else False,
            "is_india": basic_info.get("is_india", False) if basic_info else False,
            "is_ai_role": basic_info.get("is_ai", False) if basic_info else False,
            "is_hr_role": basic_info.get("is_hr", False) if basic_info else False,
            "connection_degree": "",
            "hire_potential_score": 0,
            "can_hire_fresher": False,
            "analysis": "",
            "profile_error": False
        }
        
        try:
            self.driver.get(linkedin_url)
            self._random_delay(3, 5)
            
            page_source = self.driver.page_source.lower()
            
            # Check for profile errors
            if "this page doesn" in page_source or "profile is not available" in page_source:
                self._log(f"   ⚠️ Profile not available")
                details["profile_error"] = True
                return details
            
            # Get name
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.text-heading-xlarge, h1.inline")
                details["name"] = name_elem.text.strip()
            except:
                if not details["name"]:
                    details["name"] = linkedin_url.split("/in/")[-1].replace("-", " ").title().rstrip("/")
            
            # Get headline (position)
            try:
                headline_selectors = [
                    "div.text-body-medium.break-words",
                    "div.text-body-medium",
                    ".pv-text-details__left-panel .text-body-medium"
                ]
                for sel in headline_selectors:
                    try:
                        elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                        if elem.text.strip():
                            details["headline"] = elem.text.strip()
                            break
                    except:
                        continue
            except:
                pass
            
            # Get location
            try:
                location_elem = self.driver.find_element(By.CSS_SELECTOR, "span.text-body-small.inline")
                details["location"] = location_elem.text.strip()
            except:
                pass
            
            # Get connection degree
            try:
                if "1st" in page_source:
                    details["connection_degree"] = "1st"
                elif "2nd" in page_source:
                    details["connection_degree"] = "2nd"
                elif "3rd" in page_source:
                    details["connection_degree"] = "3rd"
            except:
                pass
            
            # Scroll to load content
            self.driver.execute_script("window.scrollTo(0, 800);")
            self._random_delay(1, 2)
            
            # Check for VIT in page
            if "vit" in page_source or "vellore institute" in page_source:
                details["is_vit_alumni"] = True
            
            # Check location for India
            india_keywords = ["india", "bangalore", "bengaluru", "mumbai", "delhi", 
                            "hyderabad", "chennai", "pune", "noida", "gurgaon"]
            if any(kw in details["location"].lower() for kw in india_keywords):
                details["is_india"] = True
            if any(kw in page_source for kw in india_keywords):
                details["is_india"] = True
            
            # Check for AI/ML in headline
            headline_lower = details["headline"].lower()
            ai_keywords = ["ai", "artificial intelligence", "machine learning", "ml", 
                          "deep learning", "data science", "nlp", "computer vision", "applied ai"]
            if any(kw in headline_lower for kw in ai_keywords):
                details["is_ai_role"] = True
            
            # Check for HR
            hr_keywords = ["hr", "human resource", "talent acquisition", "recruiter", "hiring"]
            if any(kw in headline_lower for kw in hr_keywords):
                details["is_hr_role"] = True
            
            # Extract about section
            try:
                about_section = self.driver.find_element(By.CSS_SELECTOR, "div.pv-shared-text-with-see-more, section.pv-about-section")
                details["about"] = about_section.text[:300]
            except:
                pass
            
            # Analyze hire potential
            details = self._analyze_hire_potential(details)
            
            self._log(f"   ✅ {details['name'][:25]} | Score: {details['hire_potential_score']}/10 | {details['analysis'][:40]}...")
            
            return details
            
        except Exception as e:
            self._log(f"   ❌ Profile error: {e}", "ERROR")
            details["profile_error"] = True
            return details
    
    def _analyze_hire_potential(self, details: Dict) -> Dict:
        """
        Analyze if this person can hire a fresher for Applied AI role.
        
        Scoring:
        - Senior AI/ML position: +4
        - HR/TA role: +3
        - VIT alumni: +2
        - India location: +1
        - Manager/Lead/Director: +2
        - Hiring keywords: +2
        """
        score = 0
        reasons = []
        
        headline = details.get("headline", "").lower()
        about = details.get("about", "").lower()
        combined = f"{headline} {about}"
        
        # AI/ML role
        if details.get("is_ai_role"):
            score += 3
            reasons.append("AI/ML role")
        
        # HR/TA role
        if details.get("is_hr_role"):
            score += 3
            reasons.append("HR/Recruiter")
        
        # Senior position
        senior_keywords = ["manager", "lead", "director", "vp", "head", "principal", "senior", "staff"]
        if any(kw in headline for kw in senior_keywords):
            score += 2
            reasons.append("Senior position")
        
        # Founder/CTO - high influence
        founder_keywords = ["founder", "co-founder", "cto", "ceo", "chief"]
        if any(kw in headline for kw in founder_keywords):
            score += 3
            reasons.append("Leadership/Founder")
        
        # VIT alumni
        if details.get("is_vit_alumni"):
            score += 2
            reasons.append("VIT Alumni")
        
        # India
        if details.get("is_india"):
            score += 1
            reasons.append("India")
        
        # Hiring keywords
        hiring_keywords = ["hiring", "looking for", "growing team", "building"]
        if any(kw in combined for kw in hiring_keywords):
            score += 2
            reasons.append("Actively hiring!")
        
        # Already connected
        if details.get("connection_degree") == "1st":
            score += 1
            reasons.append("Already connected")
        
        # Cap at 10
        score = min(score, 10)
        
        details["hire_potential_score"] = score
        details["can_hire_fresher"] = score >= 5
        details["analysis"] = " | ".join(reasons) if reasons else "Low potential"
        
        return details
    
    # ==================== MAIN RESEARCH FLOW ====================
    
    def research_company(self, company_name: str, leads_needed: int = 10) -> List[Dict]:
        """
        Comprehensive research on a company
        
        Process:
        1. Use SerpAPI to search for AI/ML, HR, and VIT alumni
        2. Collect unique LinkedIn profiles
        3. Visit each profile on LinkedIn
        4. Analyze and score each person
        5. Return top leads sorted by score
        """
        start_time = datetime.now()
        
        self._log("\n" + "="*70)
        self._log(f"🏢 DEEP RESEARCH: {company_name}")
        self._log("="*70)
        self._log(f"🎯 Target: {leads_needed} high-quality leads")
        self._log(f"📍 Focus: Applied AI roles, HR/TA, VIT Alumni")
        self._log(f"📍 Location: India only")
        self._log("="*70 + "\n")
        
        all_profiles = []
        seen_urls = set()
        
        # Phase 1: SerpAPI searches
        self._log("\n" + "="*50)
        self._log("📋 PHASE 1: SERPAPI GOOGLE SEARCHES")
        self._log("="*50)
        
        # AI/ML roles search
        self._log("\n🤖 Searching AI/ML roles...")
        for query_template in self.search_templates["ai_roles"]:
            query = query_template.format(company=company_name)
            results = self.search_google_serpapi(query)
            profiles = self.extract_profiles_from_serp(results)
            
            for p in profiles:
                if p["linkedin_url"] not in seen_urls:
                    p["search_category"] = "AI/ML"
                    seen_urls.add(p["linkedin_url"])
                    all_profiles.append(p)
            
            self._random_delay(2, 4)
        
        # HR/TA search
        self._log("\n👔 Searching HR/Talent Acquisition...")
        for query_template in self.search_templates["hr_roles"]:
            query = query_template.format(company=company_name)
            results = self.search_google_serpapi(query)
            profiles = self.extract_profiles_from_serp(results)
            
            for p in profiles:
                if p["linkedin_url"] not in seen_urls:
                    p["search_category"] = "HR/TA"
                    seen_urls.add(p["linkedin_url"])
                    all_profiles.append(p)
            
            self._random_delay(2, 4)
        
        # VIT alumni search
        self._log("\n🎓 Searching VIT Alumni...")
        for query_template in self.search_templates["vit_alumni"]:
            query = query_template.format(company=company_name)
            results = self.search_google_serpapi(query)
            profiles = self.extract_profiles_from_serp(results)
            
            for p in profiles:
                if p["linkedin_url"] not in seen_urls:
                    p["search_category"] = "VIT"
                    seen_urls.add(p["linkedin_url"])
                    all_profiles.append(p)
            
            self._random_delay(2, 4)
        
        self._log(f"\n📊 Total unique profiles from SerpAPI: {len(all_profiles)}")
        
        # Filter for India-related profiles first
        india_profiles = [p for p in all_profiles if p.get("is_india") or p.get("is_vit")]
        other_profiles = [p for p in all_profiles if not (p.get("is_india") or p.get("is_vit"))]
        
        # Prioritize India profiles, then others
        sorted_profiles = india_profiles + other_profiles
        
        # Phase 2: LinkedIn profile visits
        self._log("\n" + "="*50)
        self._log("📋 PHASE 2: LINKEDIN PROFILE ANALYSIS")
        self._log("="*50)
        
        detailed_leads = []
        profiles_to_visit = sorted_profiles[:20]  # Visit up to 20 profiles
        
        for i, profile in enumerate(profiles_to_visit, 1):
            self._log(f"\n[{i}/{len(profiles_to_visit)}] {profile.get('name', 'Unknown')[:30]}")
            
            details = self.get_profile_details(profile["linkedin_url"], profile)
            
            if not details.get("profile_error"):
                details["company"] = company_name
                details["search_category"] = profile.get("search_category", "Other")
                
                # Only keep India-based or VIT alumni
                if details.get("is_india") or details.get("is_vit_alumni"):
                    detailed_leads.append(details)
                else:
                    self._log(f"   ⏭️ Skipped (Not India-based)")
            
            # Longer delay between profile visits to avoid detection
            self._random_delay(5, 10)
        
        # Sort by hire potential score
        detailed_leads.sort(key=lambda x: x.get("hire_potential_score", 0), reverse=True)
        
        # Take top leads
        final_leads = detailed_leads[:leads_needed]
        
        # Phase 3: Save to database
        self._log("\n" + "="*50)
        self._log("📋 PHASE 3: SAVING TO DATABASE")
        self._log("="*50)
        
        saved_count = 0
        for lead in final_leads:
            success = self.db.add_research_lead(
                name=lead.get("name", ""),
                linkedin_url=lead.get("linkedin_url", ""),
                company=company_name,
                position=lead.get("headline", ""),
                location=lead.get("location", "India"),
                lead_type=lead.get("search_category", ""),
                source="deep_research_serpapi",
                is_vit_alumni=lead.get("is_vit_alumni", False),
                is_hr=lead.get("is_hr_role", False)
            )
            if success:
                saved_count += 1
                self._log(f"   ✅ Saved: {lead.get('name', 'Unknown')[:30]}")
        
        self.db.mark_company_researched(company_name, saved_count)
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        
        self._log("\n" + "="*70)
        self._log(f"✅ RESEARCH COMPLETE: {company_name}")
        self._log("="*70)
        self._log(f"⏱️ Duration: {duration:.1f} minutes")
        self._log(f"📊 SerpAPI profiles found: {len(all_profiles)}")
        self._log(f"📊 Profiles analyzed: {len(profiles_to_visit)}")
        self._log(f"📊 India-based leads: {len(detailed_leads)}")
        self._log(f"📊 Leads saved: {saved_count}")
        self._log("="*70)
        
        # Print detailed lead info
        self._log("\n📋 TOP LEADS (sorted by hire potential):\n")
        for i, lead in enumerate(final_leads, 1):
            score = lead.get("hire_potential_score", 0)
            tags = []
            if lead.get("is_ai_role"): tags.append("🤖AI")
            if lead.get("is_hr_role"): tags.append("👔HR")
            if lead.get("is_vit_alumni"): tags.append("🎓VIT")
            if lead.get("connection_degree") == "1st": tags.append("🤝Connected")
            
            tag_str = " ".join(tags)
            
            self._log(f"{i}. {lead.get('name', 'Unknown')} [Score: {score}/10] {tag_str}")
            self._log(f"   📍 {lead.get('headline', 'N/A')[:60]}")
            self._log(f"   📍 {lead.get('location', 'India')}")
            self._log(f"   🔗 {lead.get('linkedin_url', '')}")
            self._log(f"   💡 {lead.get('analysis', '')}")
            self._log("")
        
        # Save log to file
        self._save_log(company_name)
        
        self.leads_data = final_leads
        return final_leads
    
    def _save_log(self, company_name: str):
        """Save research log to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_{company_name}_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.research_log))
        
        self._log(f"\n📝 Log saved: {filename}")
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            self._log("🔒 Browser closed")


def main():
    """Run deep research"""
    import sys
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║            DEEP RESEARCH AGENT (SerpAPI + LinkedIn)                       ║
║    Comprehensive research for Applied AI job opportunities               ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  This agent will:                                                         ║
║  1. Search Google via SerpAPI for LinkedIn profiles                      ║
║  2. Find AI/ML Managers, HR/TA, VIT Alumni                               ║
║  3. Visit each profile for detailed analysis                             ║
║  4. Score hiring potential (0-10)                                        ║
║  5. Save top 10 leads with full analysis                                 ║
║                                                                           ║
║  Location: India only | Focus: Applied AI roles                          ║
║                                                                           ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    agent = DeepResearchAgent()
    
    try:
        if len(sys.argv) > 1:
            company = " ".join(sys.argv[1:])
        else:
            company = input("Enter company name: ").strip()
        
        if company:
            agent.research_company(company, leads_needed=10)
            
            # Ask to transfer
            print("\n" + "="*50)
            transfer = input("Transfer leads to contacts for automation? (y/n): ").strip().lower()
            if transfer == 'y':
                leads = agent.db.get_unprocessed_leads(company)
                transferred = 0
                for lead in leads:
                    if lead.get("linkedin_url"):
                        success = agent.db.add_contact_from_csv(
                            name=lead["name"],
                            linkedin_url=lead["linkedin_url"],
                            company=lead.get("company", ""),
                            position=lead.get("position", ""),
                            location="India",
                            is_recruiter=True
                        )
                        if success:
                            agent.db.mark_lead_processed(lead["id"])
                            transferred += 1
                print(f"✅ Transferred {transferred} leads to contacts!")
        else:
            print("No company specified.")
    
    finally:
        agent.close()


if __name__ == "__main__":
    main()
