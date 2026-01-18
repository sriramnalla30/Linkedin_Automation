"""
LinkedIn Research Agent (Selenium-based)
Searches LinkedIn directly for HR/Talent Acquisition and VIT alumni
No external API needed - uses your LinkedIn account
"""

import time
import random
import re
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from database import DatabaseManager
from config import LINKEDIN_CREDENTIALS


class LinkedInResearcher:
    """Research leads directly from LinkedIn search"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
        self.driver = None
        self.wait = None
        self.logged_in = False
        self.leads_per_company = 10
    
    def _random_delay(self, min_sec: float = 2, max_sec: float = 5):
        """Human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _setup_driver(self):
        """Setup Chrome browser"""
        print("🚀 Setting up Chrome browser for research...")
        
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
        print("✅ Browser ready!")
    
    def login(self) -> bool:
        """Login to LinkedIn"""
        if self.driver is None:
            self._setup_driver()
        
        print("\n🔐 Logging into LinkedIn...")
        
        try:
            self.driver.get("https://www.linkedin.com/login")
            self._random_delay(2, 4)
            
            # Check if already logged in
            if "feed" in self.driver.current_url:
                print("✅ Already logged in!")
                self.logged_in = True
                return True
            
            # Enter credentials
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.clear()
            email_field.send_keys(LINKEDIN_CREDENTIALS["email"])
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(LINKEDIN_CREDENTIALS["password"])
            
            self._random_delay(1, 2)
            
            # Click login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            self._random_delay(3, 5)
            
            # Check if login successful
            if "feed" in self.driver.current_url or "checkpoint" not in self.driver.current_url:
                print("✅ Login successful!")
                self.logged_in = True
                return True
            else:
                print("⚠️ Login may require verification. Please complete manually.")
                input("Press Enter after completing verification...")
                self.logged_in = True
                return True
                
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def search_people(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search LinkedIn for people matching query"""
        if not self.logged_in:
            if not self.login():
                return []
        
        print(f"\n🔍 Searching: {query}")
        
        leads = []
        seen_urls = set()
        
        try:
            # Go to LinkedIn search
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={query.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER"
            self.driver.get(search_url)
            self._random_delay(4, 6)
            
            # Wait for results to load
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-results-container")))
            except:
                print("   ⚠️ No search results container found")
            
            # Scroll to load more results
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self._random_delay(1, 2)
            
            # Try multiple selectors for profile cards
            profile_cards = []
            selectors_to_try = [
                "li.reusable-search__result-container",
                "div.entity-result",
                "li.search-result",
                "div.search-result__wrapper",
                "[data-view-name='search-entity-result-universal-template']"
            ]
            
            for selector in selectors_to_try:
                profile_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if profile_cards:
                    print(f"   📋 Found {len(profile_cards)} results using: {selector[:30]}...")
                    break
            
            if not profile_cards:
                # Try to find all links to profiles
                print("   ⚠️ No cards found, trying direct link extraction...")
                all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
                for link in all_links[:max_results]:
                    try:
                        href = link.get_attribute("href")
                        if href and "/in/" in href and href not in seen_urls:
                            clean_url = href.split("?")[0]
                            if clean_url not in seen_urls:
                                seen_urls.add(clean_url)
                                text = link.text.strip() or "Unknown"
                                name = text.split("\n")[0] if text else "Unknown"
                                if name and name != "Unknown" and len(name) > 2:
                                    leads.append({
                                        "name": name,
                                        "linkedin_url": clean_url,
                                        "position": "",
                                        "location": "India",
                                        "is_india": True,
                                        "is_hr": False,
                                        "is_vit": False
                                    })
                                    print(f"   ✅ Found: {name}")
                    except:
                        continue
                
                print(f"\n   📊 Found {len(leads)} profiles")
                return leads
            
            for card in profile_cards[:max_results]:
                try:
                    # Get profile link - try multiple selectors
                    profile_url = None
                    for link_sel in ["a.app-aware-link", "a[href*='/in/']", "a"]:
                        try:
                            link_elem = card.find_element(By.CSS_SELECTOR, link_sel)
                            href = link_elem.get_attribute("href")
                            if href and "/in/" in href:
                                profile_url = href.split("?")[0]
                                break
                        except:
                            continue
                    
                    if not profile_url or profile_url in seen_urls:
                        continue
                    seen_urls.add(profile_url)
                    
                    # Get name - try multiple selectors
                    name = ""
                    for name_sel in ["span.entity-result__title-text", ".entity-result__title-text a span", "span[dir='ltr']", "a span"]:
                        try:
                            name_elem = card.find_element(By.CSS_SELECTOR, name_sel)
                            name = name_elem.text.strip().split("\n")[0]
                            if name:
                                break
                        except:
                            continue
                    
                    if not name:
                        # Extract from URL
                        name = profile_url.split("/in/")[-1].replace("-", " ").title()
                    
                    # Get headline/position
                    headline = ""
                    for head_sel in ["div.entity-result__primary-subtitle", ".entity-result__primary-subtitle", "p.subline-level-1"]:
                        try:
                            headline_elem = card.find_element(By.CSS_SELECTOR, head_sel)
                            headline = headline_elem.text.strip()
                            if headline:
                                break
                        except:
                            continue
                    
                    # Get location
                    location = ""
                    for loc_sel in ["div.entity-result__secondary-subtitle", ".entity-result__secondary-subtitle", "p.subline-level-2"]:
                        try:
                            location_elem = card.find_element(By.CSS_SELECTOR, loc_sel)
                            location = location_elem.text.strip()
                            if location:
                                break
                        except:
                            continue
                    
                    # Check if India location
                    india_keywords = ["india", "bangalore", "bengaluru", "mumbai", "delhi", 
                                     "hyderabad", "chennai", "pune", "noida", "gurgaon", "kolkata"]
                    is_india = any(kw in location.lower() for kw in india_keywords)
                    
                    # Check for HR keywords
                    hr_keywords = ["hr", "human resource", "talent acquisition", "recruiter", 
                                  "recruiting", "hiring", "people operations", "hrbp"]
                    is_hr = any(kw in headline.lower() for kw in hr_keywords)
                    
                    # Check for VIT
                    is_vit = "vit" in headline.lower() or "vellore" in headline.lower()
                    
                    lead = {
                        "name": name,
                        "linkedin_url": profile_url,
                        "position": headline,
                        "location": location,
                        "is_india": is_india,
                        "is_hr": is_hr,
                        "is_vit": is_vit
                    }
                    
                    leads.append(lead)
                    print(f"   ✅ Found: {name} - {headline[:50]}...")
                    
                except Exception as e:
                    continue
            
            print(f"\n   📊 Found {len(leads)} profiles")
            return leads
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def research_company_hr(self, company: str) -> List[Dict]:
        """Find HR/Talent Acquisition at a company"""
        print(f"\n{'='*60}")
        print(f"🏢 RESEARCHING HR at: {company}")
        print(f"{'='*60}")
        
        queries = [
            f"{company} HR India",
            f"{company} Talent Acquisition India",
            f"{company} Recruiter India",
        ]
        
        all_leads = []
        seen_urls = set()
        
        for query in queries:
            leads = self.search_people(query, max_results=5)
            for lead in leads:
                if lead["linkedin_url"] not in seen_urls:
                    # Filter for India only
                    if lead.get("is_india") or lead.get("is_hr"):
                        lead["company"] = company
                        lead["lead_type"] = "HR"
                        lead["source"] = "linkedin_search"
                        all_leads.append(lead)
                        seen_urls.add(lead["linkedin_url"])
            
            self._random_delay(5, 10)  # Longer delay between searches
        
        return all_leads[:5]  # Max 5 HR leads
    
    def research_company_vit_alumni(self, company: str) -> List[Dict]:
        """Find VIT alumni at a company"""
        print(f"\n{'='*60}")
        print(f"🎓 RESEARCHING VIT ALUMNI at: {company}")
        print(f"{'='*60}")
        
        queries = [
            f"{company} VIT",
            f"{company} Vellore Institute of Technology",
        ]
        
        all_leads = []
        seen_urls = set()
        
        for query in queries:
            leads = self.search_people(query, max_results=5)
            for lead in leads:
                if lead["linkedin_url"] not in seen_urls:
                    lead["company"] = company
                    lead["lead_type"] = "VIT_Alumni"
                    lead["source"] = "linkedin_search"
                    lead["is_vit"] = True
                    all_leads.append(lead)
                    seen_urls.add(lead["linkedin_url"])
            
            self._random_delay(5, 10)
        
        return all_leads[:5]  # Max 5 VIT alumni
    
    def research_company(self, company: str) -> List[Dict]:
        """Research a company - find HR + VIT alumni"""
        all_leads = []
        seen_urls = set()
        
        # Find HR
        hr_leads = self.research_company_hr(company)
        for lead in hr_leads:
            if lead["linkedin_url"] not in seen_urls:
                all_leads.append(lead)
                seen_urls.add(lead["linkedin_url"])
        
        # Find VIT alumni
        vit_leads = self.research_company_vit_alumni(company)
        for lead in vit_leads:
            if lead["linkedin_url"] not in seen_urls:
                all_leads.append(lead)
                seen_urls.add(lead["linkedin_url"])
        
        # Save to database
        saved_count = 0
        for lead in all_leads:
            success = self.db.add_research_lead(
                name=lead.get("name", ""),
                linkedin_url=lead.get("linkedin_url"),
                company=company,
                position=lead.get("position", ""),
                location=lead.get("location", "India"),
                lead_type=lead.get("lead_type", ""),
                source="linkedin_search",
                is_vit_alumni=lead.get("is_vit", False),
                is_hr=lead.get("is_hr", False)
            )
            if success:
                saved_count += 1
        
        self.db.mark_company_researched(company, saved_count)
        
        print(f"\n{'='*60}")
        print(f"✅ RESEARCH COMPLETE: {company}")
        print(f"   📊 Total leads: {len(all_leads)}")
        print(f"   💾 Saved to DB: {saved_count}")
        print(f"{'='*60}")
        
        return all_leads
    
    def load_companies(self, filepath: str = "companies_to_apply.txt") -> List[str]:
        """Load companies from file"""
        companies = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        company_name = line.split(' - ')[0].strip()
                        if company_name:
                            companies.append(company_name)
                            self.db.add_company_for_research(company_name)
            print(f"✅ Loaded {len(companies)} companies")
            return companies
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def research_next_company(self) -> Optional[str]:
        """Research next company in queue"""
        company = self.db.get_next_company_to_research()
        if company:
            self.research_company(company)
            return company
        return None
    
    def transfer_leads_to_contacts(self) -> int:
        """Transfer leads to contacts for automation"""
        leads = self.db.get_unprocessed_leads()
        transferred = 0
        
        for lead in leads:
            if lead.get("linkedin_url"):
                success = self.db.add_contact_from_csv(
                    name=lead["name"],
                    linkedin_url=lead["linkedin_url"],
                    company=lead.get("company", ""),
                    position=lead.get("position", ""),
                    location="India",
                    is_recruiter=True
                )
                if success:
                    self.db.mark_lead_processed(lead["id"])
                    transferred += 1
                    print(f"   ✅ {lead['name']}")
        
        print(f"\n📊 Transferred {transferred} leads to contacts")
        return transferred
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("🔒 Browser closed")


def main():
    """Interactive research session"""
    import sys
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║         LINKEDIN RESEARCH AGENT (Direct Search)              ║
║   Find HR/Talent Acquisition + VIT Alumni at Companies       ║
╠══════════════════════════════════════════════════════════════╣
║  Uses your LinkedIn account to search directly               ║
║  No external API needed - 100% free!                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    researcher = LinkedInResearcher()
    
    try:
        if len(sys.argv) > 1:
            action = sys.argv[1]
            
            if action == "load":
                researcher.load_companies()
            elif action == "research":
                if len(sys.argv) > 2:
                    researcher.research_company(sys.argv[2])
                else:
                    researcher.research_next_company()
            elif action == "transfer":
                researcher.transfer_leads_to_contacts()
            elif action == "next":
                researcher.research_next_company()
        else:
            # Interactive menu
            while True:
                print("\n" + "="*50)
                print("RESEARCH MENU")
                print("="*50)
                print("1. Load companies from file")
                print("2. Research next company")
                print("3. Research specific company")
                print("4. Transfer leads to automation")
                print("5. Show progress")
                print("0. Exit")
                
                choice = input("Choice: ").strip()
                
                if choice == "1":
                    researcher.load_companies()
                elif choice == "2":
                    researcher.research_next_company()
                elif choice == "3":
                    company = input("Company name: ").strip()
                    if company:
                        researcher.research_company(company)
                elif choice == "4":
                    researcher.transfer_leads_to_contacts()
                elif choice == "5":
                    progress = researcher.db.get_research_progress()
                    print(f"\n📊 Progress:")
                    print(f"   Companies done: {progress['companies_completed']}")
                    print(f"   Companies pending: {progress['companies_pending']}")
                    print(f"   Total leads: {progress['total_leads']}")
                elif choice == "0":
                    break
    finally:
        researcher.close()


if __name__ == "__main__":
    main()
