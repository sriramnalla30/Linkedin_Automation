"""
Database Manager for LinkedIn Automation
Tracks all connections, requests, and messages to avoid duplicates
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import os

class DatabaseManager:
    def __init__(self, db_path: str = "linkedin_automation.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table for tracking all contacts from CSV files
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                linkedin_url TEXT UNIQUE NOT NULL,
                email TEXT,
                company TEXT,
                position TEXT,
                location TEXT,
                contact_type TEXT,
                is_recruiter INTEGER DEFAULT 1,
                gender TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for tracking connection requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connection_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                linkedin_url TEXT NOT NULL,
                name TEXT,
                status TEXT DEFAULT 'pending',
                request_sent_at TIMESTAMP,
                accepted_at TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        ''')
        
        # Table for tracking sent messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages_sent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                linkedin_url TEXT NOT NULL,
                name TEXT,
                message_content TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        ''')
        
        # Table for tracking already connected people (your existing connections)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS existing_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                linkedin_url TEXT UNIQUE NOT NULL,
                name TEXT,
                is_recruiter INTEGER DEFAULT 0,
                message_sent INTEGER DEFAULT 0,
                connected_at TIMESTAMP,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for daily stats (rate limiting)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                connection_requests_sent INTEGER DEFAULT 0,
                messages_sent INTEGER DEFAULT 0
            )
        ''')
        
        # Table for research leads (from research agent)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                linkedin_url TEXT UNIQUE,
                email TEXT,
                company TEXT,
                position TEXT,
                location TEXT,
                lead_type TEXT,
                source TEXT,
                is_vit_alumni INTEGER DEFAULT 0,
                is_hr INTEGER DEFAULT 0,
                is_processed INTEGER DEFAULT 0,
                research_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for company research progress
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_research (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending',
                leads_found INTEGER DEFAULT 0,
                researched_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")
    
    # ==================== CONTACTS ====================
    
    def add_contact_from_csv(self, name: str, linkedin_url: str, email: str = None,
                             company: str = None, position: str = None, 
                             location: str = None, contact_type: str = None,
                             is_recruiter: bool = True, gender: str = None) -> bool:
        """Add a contact from CSV file"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO contacts 
                (name, linkedin_url, email, company, position, location, contact_type, is_recruiter, gender)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, linkedin_url, email, company, position, location, contact_type, 
                  1 if is_recruiter else 0, gender))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error adding contact: {e}")
            return False
        finally:
            conn.close()
    
    def get_contacts_to_connect(self) -> List[Dict]:
        """Get contacts who haven't been sent a connection request yet"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.name, c.linkedin_url, c.company, c.position, c.gender
            FROM contacts c
            WHERE c.is_recruiter = 1
            AND c.linkedin_url NOT IN (SELECT linkedin_url FROM connection_requests)
            AND c.linkedin_url NOT IN (SELECT linkedin_url FROM existing_connections)
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "linkedin_url": r[2], 
                 "company": r[3], "position": r[4], "gender": r[5]} for r in rows]
    
    # ==================== CONNECTION REQUESTS ====================
    
    def add_connection_request(self, linkedin_url: str, name: str = None, contact_id: int = None):
        """Record a sent connection request"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO connection_requests 
            (contact_id, linkedin_url, name, status, request_sent_at)
            VALUES (?, ?, ?, 'pending', ?)
        ''', (contact_id, linkedin_url, name, datetime.now()))
        conn.commit()
        conn.close()
        self._increment_daily_stat('connection_requests_sent')
    
    def mark_request_accepted(self, linkedin_url: str):
        """Mark a connection request as accepted"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE connection_requests 
            SET status = 'accepted', accepted_at = ?
            WHERE linkedin_url = ?
        ''', (datetime.now(), linkedin_url))
        conn.commit()
        conn.close()
    
    def get_pending_requests(self) -> List[Dict]:
        """Get all pending connection requests"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, contact_id, linkedin_url, name, request_sent_at
            FROM connection_requests
            WHERE status = 'pending'
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "contact_id": r[1], "linkedin_url": r[2], 
                 "name": r[3], "request_sent_at": r[4]} for r in rows]
    
    def get_accepted_not_messaged(self) -> List[Dict]:
        """Get accepted connections that haven't been messaged yet"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cr.id, cr.contact_id, cr.linkedin_url, cr.name, c.gender
            FROM connection_requests cr
            LEFT JOIN contacts c ON cr.contact_id = c.id
            WHERE cr.status = 'accepted'
            AND cr.linkedin_url NOT IN (SELECT linkedin_url FROM messages_sent)
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "contact_id": r[1], "linkedin_url": r[2], 
                 "name": r[3], "gender": r[4]} for r in rows]
    
    def is_request_already_sent(self, linkedin_url: str) -> bool:
        """Check if connection request was already sent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM connection_requests WHERE linkedin_url = ?', (linkedin_url,))
        result = cursor.fetchone() is not None
        conn.close()
        return result
    
    # ==================== MESSAGES ====================
    
    def add_message_sent(self, linkedin_url: str, name: str, message_content: str, contact_id: int = None):
        """Record a sent message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages_sent (contact_id, linkedin_url, name, message_content, sent_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (contact_id, linkedin_url, name, message_content, datetime.now()))
        conn.commit()
        conn.close()
        self._increment_daily_stat('messages_sent')
    
    def is_message_already_sent(self, linkedin_url: str) -> bool:
        """Check if message was already sent to this person"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM messages_sent WHERE linkedin_url = ?', (linkedin_url,))
        result = cursor.fetchone() is not None
        conn.close()
        return result
    
    # ==================== EXISTING CONNECTIONS ====================
    
    def add_existing_connection(self, linkedin_url: str, name: str, is_recruiter: bool = False):
        """Add an existing connection (from your LinkedIn)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO existing_connections 
                (linkedin_url, name, is_recruiter, message_sent)
                VALUES (?, ?, ?, 0)
            ''', (linkedin_url, name, 1 if is_recruiter else 0))
            conn.commit()
        except Exception as e:
            print(f"❌ Error adding existing connection: {e}")
        finally:
            conn.close()
    
    def mark_existing_connection_messaged(self, linkedin_url: str):
        """Mark an existing connection as messaged"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE existing_connections SET message_sent = 1 WHERE linkedin_url = ?
        ''', (linkedin_url,))
        conn.commit()
        conn.close()
    
    def get_existing_recruiters_not_messaged(self) -> List[Dict]:
        """Get existing recruiter connections that haven't been messaged"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, linkedin_url, name
            FROM existing_connections
            WHERE is_recruiter = 1 AND message_sent = 0
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "linkedin_url": r[1], "name": r[2]} for r in rows]
    
    def is_existing_connection(self, linkedin_url: str) -> bool:
        """Check if someone is already connected"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM existing_connections WHERE linkedin_url = ?', (linkedin_url,))
        result = cursor.fetchone() is not None
        conn.close()
        return result
    
    # ==================== DAILY STATS ====================
    
    def _get_today(self) -> str:
        return datetime.now().strftime('%Y-%m-%d')
    
    def _increment_daily_stat(self, stat_name: str):
        """Increment daily statistic"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = self._get_today()
        
        cursor.execute('SELECT id FROM daily_stats WHERE date = ?', (today,))
        if cursor.fetchone() is None:
            cursor.execute('INSERT INTO daily_stats (date) VALUES (?)', (today,))
        
        cursor.execute(f'UPDATE daily_stats SET {stat_name} = {stat_name} + 1 WHERE date = ?', (today,))
        conn.commit()
        conn.close()
    
    def get_daily_stats(self) -> Dict:
        """Get today's stats"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = self._get_today()
        cursor.execute('''
            SELECT connection_requests_sent, messages_sent 
            FROM daily_stats WHERE date = ?
        ''', (today,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"connection_requests_sent": row[0], "messages_sent": row[1]}
        return {"connection_requests_sent": 0, "messages_sent": 0}
    
    def can_send_more_requests(self, max_per_day: int) -> bool:
        """Check if we can send more connection requests today"""
        stats = self.get_daily_stats()
        return stats["connection_requests_sent"] < max_per_day
    
    def can_send_more_messages(self, max_per_day: int) -> bool:
        """Check if we can send more messages today"""
        stats = self.get_daily_stats()
        return stats["messages_sent"] < max_per_day
    
    # ==================== REPORTING ====================
    
    def get_summary(self) -> Dict:
        """Get overall summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM contacts WHERE is_recruiter = 1')
        total_contacts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM connection_requests WHERE status = "pending"')
        pending_requests = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM connection_requests WHERE status = "accepted"')
        accepted_requests = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM messages_sent')
        total_messages = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM existing_connections')
        existing_connections = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_contacts": total_contacts,
            "pending_requests": pending_requests,
            "accepted_requests": accepted_requests,
            "total_messages_sent": total_messages,
            "existing_connections": existing_connections
        }
    
    def print_summary(self):
        """Print a nice summary"""
        summary = self.get_summary()
        daily = self.get_daily_stats()
        
        print("\n" + "="*50)
        print("📊 LINKEDIN AUTOMATION SUMMARY")
        print("="*50)
        print(f"👥 Total Recruiter Contacts: {summary['total_contacts']}")
        print(f"⏳ Pending Requests: {summary['pending_requests']}")
        print(f"✅ Accepted Connections: {summary['accepted_requests']}")
        print(f"💬 Total Messages Sent: {summary['total_messages_sent']}")
        print(f"🔗 Existing Connections: {summary['existing_connections']}")
        print("-"*50)
        print(f"📅 TODAY's Stats:")
        print(f"   Connection Requests: {daily['connection_requests_sent']}")
        print(f"   Messages Sent: {daily['messages_sent']}")
        print("="*50 + "\n")
    
    # ==================== RESEARCH LEADS ====================
    
    def add_research_lead(self, name: str, linkedin_url: str = None, email: str = None,
                          company: str = None, position: str = None, location: str = None,
                          lead_type: str = None, source: str = None,
                          is_vit_alumni: bool = False, is_hr: bool = False) -> bool:
        """Add a research lead from the research agent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO research_leads 
                (name, linkedin_url, email, company, position, location, lead_type, source, is_vit_alumni, is_hr)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, linkedin_url, email, company, position, location, lead_type, source,
                  1 if is_vit_alumni else 0, 1 if is_hr else 0))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error adding research lead: {e}")
            return False
        finally:
            conn.close()
    
    def get_unprocessed_leads(self, company: str = None) -> List[Dict]:
        """Get research leads that haven't been processed yet"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if company:
            cursor.execute('''
                SELECT id, name, linkedin_url, email, company, position, location, lead_type, is_vit_alumni, is_hr
                FROM research_leads
                WHERE is_processed = 0 AND company = ?
            ''', (company,))
        else:
            cursor.execute('''
                SELECT id, name, linkedin_url, email, company, position, location, lead_type, is_vit_alumni, is_hr
                FROM research_leads
                WHERE is_processed = 0
            ''')
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "linkedin_url": r[2], "email": r[3],
                 "company": r[4], "position": r[5], "location": r[6], "lead_type": r[7],
                 "is_vit_alumni": r[8], "is_hr": r[9]} for r in rows]
    
    def mark_lead_processed(self, lead_id: int):
        """Mark a research lead as processed (added to contacts)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE research_leads SET is_processed = 1 WHERE id = ?', (lead_id,))
        conn.commit()
        conn.close()
    
    def get_leads_by_company(self, company: str) -> List[Dict]:
        """Get all leads for a specific company"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, linkedin_url, email, company, position, is_vit_alumni, is_hr
            FROM research_leads WHERE company LIKE ?
        ''', (f'%{company}%',))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "linkedin_url": r[2], "email": r[3],
                 "company": r[4], "position": r[5], "is_vit_alumni": r[6], "is_hr": r[7]} for r in rows]
    
    # ==================== COMPANY RESEARCH PROGRESS ====================
    
    def add_company_for_research(self, company_name: str) -> bool:
        """Add a company to the research queue"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO company_research (company_name, status)
                VALUES (?, 'pending')
            ''', (company_name,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error adding company: {e}")
            return False
        finally:
            conn.close()
    
    def get_next_company_to_research(self) -> Optional[str]:
        """Get the next company that needs research"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT company_name FROM company_research 
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def mark_company_researched(self, company_name: str, leads_found: int):
        """Mark a company as researched"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE company_research 
            SET status = 'completed', leads_found = ?, researched_at = ?
            WHERE company_name = ?
        ''', (leads_found, datetime.now(), company_name))
        conn.commit()
        conn.close()
    
    def get_research_progress(self) -> Dict:
        """Get research progress summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM company_research WHERE status = "pending"')
        pending = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM company_research WHERE status = "completed"')
        completed = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM research_leads')
        total_leads = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM research_leads WHERE is_processed = 0')
        unprocessed_leads = cursor.fetchone()[0]
        
        conn.close()
        return {
            "companies_pending": pending,
            "companies_completed": completed,
            "total_leads": total_leads,
            "unprocessed_leads": unprocessed_leads
        }


if __name__ == "__main__":
    # Test the database
    db = DatabaseManager()
    db.print_summary()
