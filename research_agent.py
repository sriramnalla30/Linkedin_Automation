"""
LinkedIn Research Agent
Finds HR/Talent Acquisition professionals and VIT alumni at target companies
Uses Google Custom Search API or SerpAPI for search
"""

import re
import time
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime
from database import DatabaseManager
from config import SERPAPI_KEY, GOOGLE_SEARCH_API_KEY

# Google Custom Search Engine ID - You need to create one at https://programmablesearchengine.google.com/
GOOGLE_CSE_ID = "a1b2c3d4e5f6g7h8i"  # Will need to be updated

class ResearchAgent:
    def __init__(self, use_serpapi: bool = True):
        self.db = DatabaseManager()
        self.serpapi_key = SERPAPI_KEY
        self.google_api_key = GOOGLE_SEARCH_API_KEY
        self.use_serpapi = use_serpapi
        self.leads_per_company = 10
        self.search_delay = 3  # seconds between searches to avoid rate limiting
        
    def load_companies_from_file(self, filepath: str = "companies_to_apply.txt") -> List[str]:
        """Load companies from the text file and add to database"""
        companies = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract company name (before the dash)
                        company_name = line.split(' - ')[0].strip()
                        if company_name:
                            companies.append(company_name)
                            self.db.add_company_for_research(company_name)
            print(f"✅ Loaded {len(companies)} companies from {filepath}")
            return companies
        except Exception as e:
            print(f"❌ Error loading companies: {e}")
            return []
    
    def search_google(self, query: str) -> List[Dict]:
        """Search Google using SerpAPI and return results"""
        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.serpapi_key,
                "num": 20,  # Get more results
                "gl": "in",  # India
                "hl": "en"
            }
            
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("organic_results", [])
            else:
                print(f"❌ SerpAPI error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def extract_linkedin_info(self, result: Dict) -> Optional[Dict]:
        """Extract LinkedIn profile information from a search result"""
        link = result.get("link", "")
        
        # Only process LinkedIn profile URLs
        if "linkedin.com/in/" not in link:
            return None
        
        # Clean the URL
        linkedin_url = link.split("?")[0]  # Remove query params
        
        # Extract info from title and snippet
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        
        # Try to extract name from title (usually "Name - Position - Company | LinkedIn")
        name = ""
        position = ""
        
        # Parse title: "Name - Position - Company | LinkedIn" or "Name | LinkedIn"
        if " | LinkedIn" in title:
            parts = title.replace(" | LinkedIn", "").split(" - ")
            if len(parts) >= 1:
                name = parts[0].strip()
            if len(parts) >= 2:
                position = parts[1].strip()
        else:
            name = title.split(" - ")[0].strip()
        
        if not name:
            return None
        
        # Check if India location is mentioned
        full_text = f"{title} {snippet}".lower()
        india_keywords = ["india", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad", 
                         "chennai", "pune", "noida", "gurgaon", "gurugram", "kolkata"]
        
        is_india = any(kw in full_text for kw in india_keywords)
        
        # Check for VIT alumni
        vit_keywords = ["vit", "vellore institute of technology", "vit university", "vit vellore", "vit chennai"]
        is_vit = any(kw in full_text for kw in vit_keywords)
        
        # Check for HR/Talent Acquisition
        hr_keywords = ["hr", "human resource", "talent acquisition", "recruiter", "recruiting",
                      "hiring", "people operations", "hrbp", "talent partner", "staffing"]
        is_hr = any(kw in full_text for kw in hr_keywords)
        
        return {
            "name": name,
            "linkedin_url": linkedin_url,
            "position": position,
            "snippet": snippet,
            "is_india": is_india,
            "is_vit": is_vit,
            "is_hr": is_hr
        }
    
    def search_hr_at_company(self, company: str) -> List[Dict]:
        """Search for HR/Talent Acquisition professionals at a company"""
        print(f"\n🔍 Searching HR/Talent Acquisition at {company}...")
        
        queries = [
            f'"{company}" HR India site:linkedin.com/in',
            f'"{company}" "Talent Acquisition" India site:linkedin.com/in',
            f'"{company}" Recruiter India site:linkedin.com/in',
            f'"{company}" "Human Resources" India site:linkedin.com/in',
            f'"{company}" "People Operations" India site:linkedin.com/in',
        ]
        
        all_leads = []
        seen_urls = set()
        
        for query in queries:
            print(f"   🔎 Query: {query[:60]}...")
            results = self.search_google(query)
            
            for result in results:
                info = self.extract_linkedin_info(result)
                if info and info["linkedin_url"] not in seen_urls:
                    info["company"] = company
                    info["lead_type"] = "HR"
                    info["source"] = "serpapi_google"
                    all_leads.append(info)
                    seen_urls.add(info["linkedin_url"])
            
            time.sleep(self.search_delay)
        
        # Filter for India-based leads
        india_leads = [l for l in all_leads if l.get("is_india", False) or l.get("is_hr", False)]
        print(f"   ✅ Found {len(india_leads)} HR leads at {company}")
        return india_leads[:5]  # Return up to 5 HR leads
    
    def search_vit_alumni_at_company(self, company: str) -> List[Dict]:
        """Search for VIT alumni at a company"""
        print(f"\n🎓 Searching VIT alumni at {company}...")
        
        queries = [
            f'"{company}" VIT India site:linkedin.com/in',
            f'"{company}" "Vellore Institute of Technology" India site:linkedin.com/in',
            f'"{company}" "VIT University" India site:linkedin.com/in',
            f'"{company}" "VIT Vellore" site:linkedin.com/in',
        ]
        
        all_leads = []
        seen_urls = set()
        
        for query in queries:
            print(f"   🔎 Query: {query[:60]}...")
            results = self.search_google(query)
            
            for result in results:
                info = self.extract_linkedin_info(result)
                if info and info["linkedin_url"] not in seen_urls:
                    info["company"] = company
                    info["lead_type"] = "VIT_Alumni"
                    info["source"] = "serpapi_google"
                    info["is_vit"] = True
                    all_leads.append(info)
                    seen_urls.add(info["linkedin_url"])
            
            time.sleep(self.search_delay)
        
        # Filter for India-based VIT alumni
        india_leads = [l for l in all_leads if l.get("is_india", False) or l.get("is_vit", False)]
        print(f"   ✅ Found {len(india_leads)} VIT alumni at {company}")
        return india_leads[:5]  # Return up to 5 VIT alumni leads
    
    def research_company(self, company: str) -> List[Dict]:
        """Research a single company - find HR + VIT alumni"""
        print(f"\n{'='*60}")
        print(f"🏢 RESEARCHING: {company}")
        print(f"{'='*60}")
        
        all_leads = []
        seen_urls = set()
        
        # Search for HR/Talent Acquisition
        hr_leads = self.search_hr_at_company(company)
        for lead in hr_leads:
            if lead["linkedin_url"] not in seen_urls:
                all_leads.append(lead)
                seen_urls.add(lead["linkedin_url"])
        
        # Search for VIT alumni
        vit_leads = self.search_vit_alumni_at_company(company)
        for lead in vit_leads:
            if lead["linkedin_url"] not in seen_urls:
                all_leads.append(lead)
                seen_urls.add(lead["linkedin_url"])
        
        # Save leads to database
        saved_count = 0
        for lead in all_leads:
            success = self.db.add_research_lead(
                name=lead.get("name", ""),
                linkedin_url=lead.get("linkedin_url"),
                company=company,
                position=lead.get("position", ""),
                location="India",
                lead_type=lead.get("lead_type", ""),
                source=lead.get("source", "serpapi"),
                is_vit_alumni=lead.get("is_vit", False),
                is_hr=lead.get("is_hr", False)
            )
            if success:
                saved_count += 1
        
        # Mark company as researched
        self.db.mark_company_researched(company, saved_count)
        
        print(f"\n✅ Research complete for {company}")
        print(f"   📊 Total leads found: {len(all_leads)}")
        print(f"   💾 New leads saved: {saved_count}")
        
        return all_leads
    
    def research_next_company(self) -> Optional[str]:
        """Research the next company in queue"""
        company = self.db.get_next_company_to_research()
        if company:
            self.research_company(company)
            return company
        else:
            print("✅ No more companies to research!")
            return None
    
    def research_all_companies(self, max_companies: int = None):
        """Research all companies (or up to max_companies)"""
        count = 0
        while True:
            company = self.research_next_company()
            if not company:
                break
            count += 1
            if max_companies and count >= max_companies:
                print(f"\n⏸️ Pausing after {count} companies. Run again to continue.")
                break
            # Wait between companies to avoid rate limiting
            print(f"\n⏳ Waiting 30 seconds before next company...")
            time.sleep(30)
    
    def transfer_leads_to_contacts(self, company: str = None) -> int:
        """Transfer unprocessed leads to the contacts table for automation"""
        leads = self.db.get_unprocessed_leads(company)
        transferred = 0
        
        for lead in leads:
            if lead.get("linkedin_url"):
                # Add to contacts table
                success = self.db.add_contact_from_csv(
                    name=lead["name"],
                    linkedin_url=lead["linkedin_url"],
                    company=lead.get("company", ""),
                    position=lead.get("position", ""),
                    location="India",
                    is_recruiter=True,
                    gender=None  # Will be detected by gender_detector
                )
                
                if success:
                    self.db.mark_lead_processed(lead["id"])
                    transferred += 1
                    print(f"   ✅ Added: {lead['name']} ({lead.get('company', 'Unknown')})")
        
        print(f"\n📊 Transferred {transferred} leads to contacts for automation")
        return transferred
    
    def print_leads_summary(self, company: str = None):
        """Print summary of found leads"""
        if company:
            leads = self.db.get_leads_by_company(company)
            print(f"\n{'='*60}")
            print(f"📋 LEADS FOR: {company}")
            print(f"{'='*60}")
        else:
            leads = self.db.get_unprocessed_leads()
            print(f"\n{'='*60}")
            print(f"📋 ALL UNPROCESSED LEADS")
            print(f"{'='*60}")
        
        for i, lead in enumerate(leads, 1):
            vit_tag = "🎓VIT" if lead.get("is_vit_alumni") else ""
            hr_tag = "👔HR" if lead.get("is_hr") else ""
            print(f"{i}. {lead['name']} - {lead.get('position', 'N/A')}")
            print(f"   🏢 {lead.get('company', 'N/A')} {vit_tag} {hr_tag}")
            print(f"   🔗 {lead.get('linkedin_url', 'N/A')}")
            if lead.get("email"):
                print(f"   📧 {lead['email']}")
            print()
        
        # Print progress
        progress = self.db.get_research_progress()
        print(f"\n{'='*60}")
        print(f"📊 RESEARCH PROGRESS")
        print(f"{'='*60}")
        print(f"🏢 Companies Completed: {progress['companies_completed']}")
        print(f"⏳ Companies Pending: {progress['companies_pending']}")
        print(f"👥 Total Leads Found: {progress['total_leads']}")
        print(f"📝 Unprocessed Leads: {progress['unprocessed_leads']}")


def main():
    """Main function to run the research agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LinkedIn Research Agent")
    parser.add_argument("--load", action="store_true", help="Load companies from file")
    parser.add_argument("--research", type=str, help="Research a specific company")
    parser.add_argument("--research-next", action="store_true", help="Research next company in queue")
    parser.add_argument("--research-all", action="store_true", help="Research all companies")
    parser.add_argument("--max", type=int, default=1, help="Max companies to research at once")
    parser.add_argument("--transfer", action="store_true", help="Transfer leads to contacts")
    parser.add_argument("--summary", action="store_true", help="Show leads summary")
    parser.add_argument("--company", type=str, help="Filter by company name")
    
    args = parser.parse_args()
    
    agent = ResearchAgent()
    
    if args.load:
        agent.load_companies_from_file()
    
    if args.research:
        agent.research_company(args.research)
    
    if args.research_next:
        agent.research_next_company()
    
    if args.research_all:
        agent.research_all_companies(max_companies=args.max)
    
    if args.transfer:
        agent.transfer_leads_to_contacts(args.company)
    
    if args.summary:
        agent.print_leads_summary(args.company)
    
    # If no args, show help
    if not any([args.load, args.research, args.research_next, args.research_all, args.transfer, args.summary]):
        parser.print_help()
        print("\n" + "="*60)
        print("EXAMPLE USAGE:")
        print("="*60)
        print("1. Load companies:        python research_agent.py --load")
        print("2. Research one company:  python research_agent.py --research 'TrueFoundry'")
        print("3. Research next in queue: python research_agent.py --research-next")
        print("4. Research all (1/day):  python research_agent.py --research-all --max 1")
        print("5. Transfer to contacts:  python research_agent.py --transfer")
        print("6. Show summary:          python research_agent.py --summary")


if __name__ == "__main__":
    main()
