"""
Run Research Agent - Simplified runner script
Research companies and find HR + VIT alumni leads
"""

import sys
import argparse
from research_agent import ResearchAgent

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           LINKEDIN RESEARCH AGENT                             ║
║   Find HR/Talent Acquisition + VIT Alumni at Companies       ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  This agent will:                                             ║
║  1. Search Google for LinkedIn profiles                       ║
║  2. Find HR/Talent Acquisition professionals in India         ║
║  3. Find VIT alumni working at target companies               ║
║  4. Save leads to database for LinkedIn automation            ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    agent = ResearchAgent()
    
    if len(sys.argv) > 1:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("action", choices=["load", "research", "transfer", "summary", "all"])
        parser.add_argument("--company", type=str, help="Specific company name")
        args = parser.parse_args()
        
        if args.action == "load":
            agent.load_companies_from_file()
            agent.print_leads_summary()
            
        elif args.action == "research":
            if args.company:
                agent.research_company(args.company)
            else:
                agent.research_next_company()
            agent.print_leads_summary()
            
        elif args.action == "transfer":
            agent.transfer_leads_to_contacts(args.company)
            
        elif args.action == "summary":
            agent.print_leads_summary(args.company)
            
        elif args.action == "all":
            # Load companies and research first one
            agent.load_companies_from_file()
            agent.research_next_company()
            agent.print_leads_summary()
    else:
        # Interactive menu
        while True:
            print("\n" + "="*50)
            print("RESEARCH AGENT MENU")
            print("="*50)
            print("1. Load companies from file")
            print("2. Research next company")
            print("3. Research specific company")
            print("4. Transfer leads to automation")
            print("5. Show leads summary")
            print("6. Research all companies (slow)")
            print("0. Exit")
            print("="*50)
            
            choice = input("Enter choice (0-6): ").strip()
            
            if choice == "1":
                agent.load_companies_from_file()
                
            elif choice == "2":
                company = agent.research_next_company()
                if company:
                    agent.print_leads_summary(company)
                    
            elif choice == "3":
                company = input("Enter company name: ").strip()
                if company:
                    agent.research_company(company)
                    agent.print_leads_summary(company)
                    
            elif choice == "4":
                agent.transfer_leads_to_contacts()
                print("✅ Leads transferred! Run main.py to send connection requests.")
                
            elif choice == "5":
                agent.print_leads_summary()
                
            elif choice == "6":
                confirm = input("This will research ALL companies. Continue? (y/n): ")
                if confirm.lower() == 'y':
                    max_companies = input("Max companies per session (default: all): ").strip()
                    max_companies = int(max_companies) if max_companies else None
                    agent.research_all_companies(max_companies)
                    
            elif choice == "0":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")


if __name__ == "__main__":
    main()
