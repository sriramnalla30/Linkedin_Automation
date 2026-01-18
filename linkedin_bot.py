"""
LinkedIn Automation Bot
Handles all LinkedIn operations: login, connect, message
"""

import time
import random
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementClickInterceptedException, StaleElementReferenceException
)

from database import DatabaseManager
from gender_detector import get_salutation, get_first_name, detect_gender
from profile_analyzer import analyze_profile, quick_student_check
from config import LINKEDIN_CREDENTIALS, SETTINGS, MESSAGE_TEMPLATE


class LinkedInBot:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.driver = None
        self.wait = None
        self.logged_in = False
        
    def _random_delay(self, min_sec: float = None, max_sec: float = None):
        """Add random human-like delay"""
        min_sec = min_sec or SETTINGS["delay_between_actions_min"]
        max_sec = max_sec or SETTINGS["delay_between_actions_max"]
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def _setup_driver(self):
        """Setup Chrome WebDriver with options"""
        print("🚀 Setting up Chrome browser...")
        
        chrome_options = Options()
        
        # Make browser less detectable
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Other useful options
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # User agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Try WITHOUT custom profile first (simpler, more reliable)
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Browser ready!")
            return
        except Exception as e:
            print(f"⚠️ First attempt failed: {e}")
        
        # Try with clean profile
        try:
            import shutil
            profile_path = os.path.join(os.getcwd(), "chrome_linkedin_profile")
            if os.path.exists(profile_path):
                shutil.rmtree(profile_path, ignore_errors=True)
            
            chrome_options.add_argument(f"--user-data-dir={profile_path}")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Browser ready!")
        except Exception as e:
            print(f"❌ Failed to start Chrome: {e}")
            raise
    
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
            
            # Enter email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            self._type_like_human(email_field, LINKEDIN_CREDENTIALS["email"])
            
            self._random_delay(1, 2)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            self._type_like_human(password_field, LINKEDIN_CREDENTIALS["password"])
            
            self._random_delay(1, 2)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            self._random_delay(3, 5)
            
            # Check for verification challenge
            if "checkpoint" in self.driver.current_url:
                print("⚠️  LinkedIn security checkpoint detected!")
                print("📱 Please complete the verification manually in the browser...")
                input("Press Enter after completing verification...")
            
            # Verify login success
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                print("✅ Login successful!")
                self.logged_in = True
                return True
            else:
                print("❌ Login may have failed. Current URL:", self.driver.current_url)
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def _type_like_human(self, element, text: str):
        """Type text with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def send_connection_request(self, profile_url: str, name: str = None, contact_id: int = None) -> Tuple[bool, str]:
        """
        Send a connection request to a profile (without note)
        Returns: (success: bool, status: str)
        """
        if not self.logged_in:
            return False, "Not logged in"
        
        # Check if already requested
        if self.db.is_request_already_sent(profile_url):
            print(f"   ⏭️ Already in database - skipping")
            return False, "Already requested"
        
        # Check daily limit
        if not self.db.can_send_more_requests(SETTINGS["max_connection_requests_per_day"]):
            return False, "Daily limit reached"
        
        try:
            print(f"\n👤 Visiting profile: {name or profile_url}")
            self.driver.get(profile_url)
            self._random_delay(4, 6)
            
            # Wait for page to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            except:
                pass
            
            # Check if already connected (look for Connect button first)
            print(f"   🔍 Checking connection status...")
            
            # First, try to find the Connect button
            connect_buttons = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@aria-label, 'Invite') or contains(@aria-label, 'Connect') or .//span[text()='Connect']]"
            )
            has_connect_button = any(b.is_displayed() for b in connect_buttons if 'connect' in (b.get_attribute('aria-label') or b.text or '').lower())
            
            if not has_connect_button:
                # Check if it's because they're already connected
                if self._is_already_connected():
                    print(f"   ✅ Already connected with {name}")
                    self.db.add_existing_connection(profile_url, name, is_recruiter=True)
                    return False, "Already connected"
                else:
                    # Check if pending
                    if self._has_pending_request():
                        print(f"   ⏳ Pending request already exists for {name}")
                        self.db.add_connection_request(profile_url, name, contact_id)
                        return False, "Pending request exists"
                    print(f"   ❌ Cannot find Connect button for {name}")
                    return False, "Connect button not found"
            
            print(f"   🔘 Found Connect button, clicking...")
            
            # Find and click Connect button
            connect_clicked = self._click_connect_button()
            
            if not connect_clicked:
                return False, "Connect button not found"
            
            self._random_delay(2, 3)
            
            # Handle "How do you know" modal - click Send without note
            if not self._handle_connection_modal():
                return False, "Failed to handle modal"
            
            # Record the request
            self.db.add_connection_request(profile_url, name, contact_id)
            print(f"🎉 Connection request sent to {name}!")
            
            return True, "Request sent"
            
        except Exception as e:
            print(f"❌ Error sending request: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    def _is_already_connected(self) -> bool:
        """Check if already connected with this person (1st degree connection)"""
        try:
            # Wait a bit for page to fully load
            self._random_delay(1, 2)
            
            # Get the page source to search for indicators
            page_text = self.driver.page_source
            
            # Method 1: Look for "1st" degree indicator in the profile header
            # This appears right after the name like "Basavaraj C · 1st"
            first_degree_selectors = [
                "//span[contains(@class, 'dist-value') and contains(text(), '1st')]",
                "//span[text()='1st']",
                "//span[contains(text(), '· 1st')]",
                "//*[contains(text(), '1st degree connection')]",
                "//span[contains(@class, 'distance-badge')]//span[contains(text(), '1st')]",
            ]
            
            for selector in first_degree_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if len(elements) > 0:
                    print(f"   📍 Found '1st' degree - CONNECTED!")
                    return True
            
            # Method 2: Check page source for "1st" patterns (more variations)
            first_patterns = ['· 1st', '>1st<', '"1st"', "'1st'", 'degree-icon--1st', '1st degree']
            for pattern in first_patterns:
                if pattern in page_text:
                    print(f"   📍 Found '{pattern}' in page - CONNECTED!")
                    return True
            
            # Method 3: Check if "Message" button exists AND "Connect" does NOT
            has_message = len(self.driver.find_elements(
                By.XPATH,
                "//button[.//span[text()='Message']]"
            )) > 0
            
            # Also check for message link/button with different patterns
            if not has_message:
                has_message = len(self.driver.find_elements(
                    By.XPATH,
                    "//a[contains(@href, 'messaging')]//span[text()='Message']"
                )) > 0
            
            # Check for Follow button (appears when connected instead of Connect)
            has_follow = len(self.driver.find_elements(
                By.XPATH,
                "//button[.//span[text()='Follow']]"
            )) > 0
            
            # Check if "Connect" exists anywhere on page
            has_connect = len(self.driver.find_elements(
                By.XPATH,
                "//button[.//span[text()='Connect']]"
            )) > 0 or 'Connect</span>' in page_text
            
            # Check for "Pending" (request sent but not accepted)
            has_pending = 'Pending' in page_text or len(self.driver.find_elements(
                By.XPATH,
                "//button[.//span[text()='Pending']]"
            )) > 0
            
            # Check for 2nd or 3rd degree
            has_2nd = '· 2nd' in page_text or '>2nd<' in page_text
            has_3rd = '· 3rd' in page_text or '>3rd<' in page_text
            
            if has_2nd or has_3rd:
                print(f"   📍 2nd/3rd degree - NOT connected")
                return False
            
            if has_pending:
                print(f"   📍 Request pending - NOT connected yet")
                return False
            
            # If Message exists but NO Connect and NO 2nd/3rd = likely Connected
            if has_message and not has_connect and not has_2nd and not has_3rd:
                print(f"   📍 Has Message, no Connect, no 2nd/3rd - CONNECTED!")
                return True
            
            # If Connect exists = NOT connected
            if has_connect:
                print(f"   📍 Connect button found - NOT connected")
                return False
            
            # NEW: If has Message button, likely connected (last resort)
            if has_message:
                print(f"   📍 Has Message button - assuming CONNECTED!")
                return True
            
            # Default: assume not connected if unclear
            print(f"   📍 Status unclear, assuming NOT connected")
            return False
            
        except Exception as e:
            print(f"   ⚠️ Connection check error: {e}")
            return False
    
    def _has_pending_request(self) -> bool:
        """Check if there's already a pending request"""
        try:
            pending = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@aria-label, 'Pending')]"
            )
            return len(pending) > 0
        except:
            return False
    
    def _click_connect_button(self) -> bool:
        """Find and click the Connect button - ONLY on main profile, not sidebar"""
        try:
            self._random_delay(1, 2)
            
            # IMPORTANT: Only look in the main profile section, NOT the sidebar
            # The main profile buttons are in the section with class containing 'pvs-profile-actions'
            # or within the main content area
            
            # First, try to find Connect button in the MAIN profile action buttons
            main_profile_selectors = [
                # Primary Connect button next to Message/Follow
                "//main//button[contains(@aria-label, 'Invite') and contains(@aria-label, 'to connect')]",
                "//main//button[.//span[text()='Connect']]",
                # In the profile actions section
                "//section[contains(@class, 'profile')]//button[contains(@aria-label, 'Connect')]",
                "//div[contains(@class, 'pvs-profile-actions')]//button[.//span[text()='Connect']]",
            ]
            
            for selector in main_profile_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            aria_label = button.get_attribute('aria-label') or ''
                            button_text = button.text.strip()
                            print(f"   🔘 Found main Connect button: {aria_label or button_text}")
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            self._random_delay(0.5, 1)
                            self.driver.execute_script("arguments[0].click();", button)
                            print(f"   ✅ Clicked Connect button")
                            return True
                except:
                    continue
            
            # If no direct Connect button, look in "More" dropdown
            print("   🔍 Connect not visible, checking 'More' menu...")
            try:
                # Find the "More" button in the MAIN profile area only
                more_selectors = [
                    "//main//button[.//span[text()='More']]",
                    "//div[contains(@class, 'pvs-profile-actions')]//button[contains(@aria-label, 'More')]",
                    "//section[contains(@class, 'artdeco-card')]//button[.//span[text()='More']]",
                ]
                
                more_button = None
                for selector in more_selectors:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            more_button = btn
                            break
                    if more_button:
                        break
                
                if more_button:
                    print(f"   🔘 Clicking 'More' button...")
                    self.driver.execute_script("arguments[0].click();", more_button)
                    self._random_delay(1.5, 2.5)
                    
                    # Now find "Connect" in the dropdown
                    dropdown_connect_selectors = [
                        "//div[contains(@class, 'artdeco-dropdown__content')]//span[text()='Connect']/ancestor::div[contains(@class, 'artdeco-dropdown__item')]",
                        "//div[contains(@class, 'dropdown')]//span[text()='Connect']/..",
                        "//li//span[text()='Connect']/..",
                        "//*[contains(@class, 'dropdown')]//*[text()='Connect']",
                    ]
                    
                    for selector in dropdown_connect_selectors:
                        try:
                            connect_options = self.driver.find_elements(By.XPATH, selector)
                            for option in connect_options:
                                if option.is_displayed():
                                    print(f"   🔘 Found 'Connect' in dropdown")
                                    self.driver.execute_script("arguments[0].click();", option)
                                    print(f"   ✅ Clicked Connect from More menu")
                                    return True
                        except:
                            continue
                    
                    print("   ❌ 'Connect' not found in dropdown")
            except Exception as e:
                print(f"   ⚠️ More menu error: {e}")
            
            print("   ❌ Connect button not found anywhere")
            return False
            
        except Exception as e:
            print(f"❌ Error clicking connect: {e}")
            return False
    
    def _handle_connection_modal(self) -> bool:
        """Handle the connection modal - send without note"""
        try:
            self._random_delay(2, 3)
            
            # Look for "Send without a note" button first (preferred)
            send_selectors = [
                "//button[@aria-label='Send without a note']",
                "//button[contains(@aria-label, 'Send without')]",
                "//button[.//span[text()='Send without a note']]",
                "//button[contains(text(), 'Send without')]",
                # Generic send button
                "//button[@aria-label='Send now']",
                "//button[@aria-label='Send']",
                "//button[.//span[text()='Send']]",
            ]
            
            for selector in send_selectors:
                try:
                    send_buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in send_buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"   🔘 Found send button: {button.get_attribute('aria-label') or button.text}")
                            self.driver.execute_script("arguments[0].click();", button)
                            print(f"   ✅ Clicked Send")
                            self._random_delay(1, 2)
                            return True
                except:
                    continue
            
            # Check if there's a "How do you know" modal
            try:
                # Sometimes LinkedIn asks "How do you know this person?"
                # Look for the modal and just click Send
                modal = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'send-invite')]")
                if modal:
                    # Find any Send button in the modal
                    send_btn = self.driver.find_element(By.XPATH, "//div[contains(@class, 'send-invite')]//button[contains(@aria-label, 'Send')]")
                    send_btn.click()
                    print(f"   ✅ Clicked Send in modal")
                    return True
            except:
                pass
            
            print(f"   ⚠️ No modal appeared - connection may have been sent directly")
            return True  # Assume success if no modal appeared
            
        except Exception as e:
            print(f"⚠️ Modal handling: {e}")
            return True  # Continue anyway
    
    def _get_profile_headline(self) -> str:
        """Extract the headline/title from the current profile page"""
        try:
            # Try multiple selectors for headline
            headline_selectors = [
                "//div[contains(@class, 'text-body-medium')]",
                "//div[contains(@class, 'headline')]",
                "//h2[contains(@class, 'headline')]",
                "//div[@data-generated-suggestion-target]"
            ]
            
            for selector in headline_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 5:
                            return text
                except:
                    continue
            
            return ""
        except:
            return ""
    
    def _is_working_professional(self, name: str, headline: str = None) -> Tuple[bool, str, str]:
        """
        Check if this person is a working professional (not a student)
        Uses Gemini AI for analysis
        
        Returns: (should_message: bool, gender: str, reason: str)
        """
        # Get headline from page if not provided
        if not headline:
            headline = self._get_profile_headline()
        
        print(f"   📋 Analyzing: {headline[:60]}..." if headline else "   📋 No headline found")
        
        # Quick local check first (no API call)
        if quick_student_check(headline):
            print(f"   ❌ STUDENT detected - skipping")
            return False, detect_gender(name), "Student profile"
        
        # Use Gemini for detailed analysis
        try:
            result = analyze_profile(name, headline)
            
            if result['is_student']:
                print(f"   ❌ STUDENT: {result['reason']}")
                return False, result['gender'], result['reason']
            
            if result['should_message']:
                print(f"   ✅ WORKING PROFESSIONAL: {result['reason']}")
                return True, result['gender'], result['reason']
            
            print(f"   ⚠️ UNCERTAIN: {result['reason']}")
            return False, result['gender'], result['reason']
            
        except Exception as e:
            print(f"   ⚠️ Analysis error: {e}")
            # Default to not messaging if unsure
            return False, detect_gender(name), "Analysis failed"
    
    def send_message(self, profile_url: str, name: str, gender: str = None, contact_id: int = None) -> Tuple[bool, str]:
        """
        Send a personalized message to a connection
        ONLY sends to working professionals, NOT to students
        Sends exactly ONE message - no conversation
        """
        if not self.logged_in:
            return False, "Not logged in"
        
        # Check if already messaged
        if self.db.is_message_already_sent(profile_url):
            return False, "Already messaged"
        
        # Check daily limit
        if not self.db.can_send_more_messages(SETTINGS["max_messages_per_day"]):
            return False, "Daily message limit reached"
        
        try:
            print(f"\n💬 Checking profile: {name}")
            self.driver.get(profile_url)
            self._random_delay(3, 5)
            
            # Check if actually connected
            if not self._is_already_connected():
                return False, "Not connected"
            
            # *** IMPORTANT: Check if this is a working professional ***
            should_message, detected_gender, reason = self._is_working_professional(name)
            
            if not should_message:
                print(f"   ⏭️ Skipping {name}: {reason}")
                # Mark as messaged to avoid checking again (with special note)
                self.db.add_message_sent(profile_url, name, f"SKIPPED: {reason}", contact_id)
                return False, f"Skipped: {reason}"
            
            # Use detected gender if not provided
            if gender is None:
                gender = detected_gender
            
            # Click Message button and wait for dialog
            if not self._click_message_button():
                # Try alternative: go to messaging directly
                print("   ⚠️ Trying direct messaging URL...")
                if not self._try_direct_message(profile_url, name):
                    return False, "Message button not found"
            
            # Wait for message modal to fully load
            self._random_delay(3, 5)
            
            # Compose personalized message
            first_name = get_first_name(name)
            salutation = get_salutation(name, gender)
            
            message = MESSAGE_TEMPLATE.format(
                name=first_name,
                salutation=salutation
            )
            
            # Type and send message
            if not self._type_and_send_message(message):
                return False, "Failed to send message"
            
            # Record the message
            self.db.add_message_sent(profile_url, name, message, contact_id)
            print(f"✅ Message sent to {first_name} {salutation}!")
            
            return True, "Message sent"
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False, str(e)
    
    def _click_message_button(self) -> bool:
        """Click the Message button on a profile"""
        try:
            # Wait for page to stabilize
            self._random_delay(2, 3)
            
            message_selectors = [
                # Main profile button - most common
                "//main//button[contains(@aria-label, 'Message')]",
                "//main//button[contains(., 'Message') and not(contains(@class, 'disabled'))]",
                # Any message button on page
                "//button[contains(@aria-label, 'Message')]",
                "//button[contains(., 'Message')]",
                # Link to messaging
                "//a[contains(@href, 'messaging')]"
            ]
            
            for selector in message_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            # Scroll into view
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                            self._random_delay(0.5, 1)
                            
                            # Use JavaScript click for reliability
                            self.driver.execute_script("arguments[0].click();", button)
                            print("   📝 Opened message dialog...")
                            
                            # Wait for dialog to appear
                            self._random_delay(2, 4)
                            return True
                except:
                    continue
            
            print("   ⚠️ Could not find Message button")
            return False
            
        except Exception as e:
            print(f"❌ Error clicking message button: {e}")
            return False
    
    def _try_direct_message(self, profile_url: str, name: str) -> bool:
        """Try to message by going to LinkedIn messaging page directly"""
        try:
            # Extract member ID from profile URL
            # Go to messaging inbox and start new conversation
            self.driver.get("https://www.linkedin.com/messaging/")
            self._random_delay(3, 5)
            
            # Click compose button
            compose_selectors = [
                "//button[contains(@class, 'msg-overlay-bubble-header__button')]",
                "//button[contains(@aria-label, 'compose')]",
                "//button[contains(@aria-label, 'New message')]",
                "//button[contains(., 'Compose')]"
            ]
            
            for selector in compose_selectors:
                try:
                    compose_btn = self.driver.find_element(By.XPATH, selector)
                    if compose_btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", compose_btn)
                        self._random_delay(2, 3)
                        
                        # Type name in the To: field
                        to_field = self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Type a name')]")
                        to_field.send_keys(name)
                        self._random_delay(2, 3)
                        
                        # Click on the autocomplete result
                        result = self.driver.find_element(By.XPATH, f"//li[contains(@class, 'msg-connections-typeahead')]")
                        result.click()
                        self._random_delay(1, 2)
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"   ⚠️ Direct message failed: {e}")
            return False
    
    def _type_and_send_message(self, message: str) -> bool:
        """Type the message and send it"""
        try:
            # Wait longer for modal to fully load
            time.sleep(5)
            
            from selenium.webdriver.common.action_chains import ActionChains
            
            # Try multiple approaches to find and type in message box
            message_sent = False
            
            # Approach 1: Find any visible contenteditable element
            for attempt in range(3):
                try:
                    # Look for contenteditable divs
                    editables = self.driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
                    for editable in editables:
                        try:
                            if editable.is_displayed() and editable.size['height'] > 20:
                                # Click to focus
                                self.driver.execute_script("arguments[0].focus();", editable)
                                time.sleep(0.5)
                                
                                # Clear and type using JavaScript
                                self.driver.execute_script(
                                    "arguments[0].innerHTML = arguments[1];",
                                    editable, message
                                )
                                time.sleep(0.5)
                                
                                # Trigger events
                                self.driver.execute_script("""
                                    var event = new Event('input', { bubbles: true });
                                    arguments[0].dispatchEvent(event);
                                """, editable)
                                
                                print(f"   📝 Typed message in contenteditable")
                                message_sent = True
                                break
                        except:
                            continue
                    if message_sent:
                        break
                except:
                    pass
                time.sleep(2)
            
            if not message_sent:
                # Approach 2: Use keyboard to type directly 
                try:
                    # Press Tab to focus on message area
                    actions = ActionChains(self.driver)
                    actions.send_keys(Keys.TAB).perform()
                    time.sleep(0.5)
                    
                    # Type the message
                    for char in message[:500]:  # Limit to 500 chars for safety
                        actions = ActionChains(self.driver)
                        actions.send_keys(char).perform()
                        time.sleep(0.01)
                    
                    print(f"   📝 Typed message using keyboard")
                    message_sent = True
                except Exception as e:
                    print(f"   ⚠️ Keyboard typing failed: {e}")
            
            if not message_sent:
                print("   ⚠️ Could not type message")
                return False
            
            time.sleep(2)
            
            # Find and click Send button
            send_clicked = False
            send_selectors = [
                "button.msg-form__send-button",
                "button[type='submit']",
                "button.msg-form__send-btn",
                "button.artdeco-button--primary"
            ]
            
            for selector in send_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        btn_text = btn.get_attribute("innerHTML").lower()
                        if btn.is_displayed() and btn.is_enabled() and ("send" in btn_text or btn.get_attribute("type") == "submit"):
                            self.driver.execute_script("arguments[0].click();", btn)
                            print(f"   📤 Clicked Send button")
                            send_clicked = True
                            break
                    if send_clicked:
                        break
                except:
                    continue
            
            if not send_clicked:
                # Try Ctrl+Enter to send
                try:
                    actions = ActionChains(self.driver)
                    actions.key_down(Keys.CONTROL).send_keys(Keys.RETURN).key_up(Keys.CONTROL).perform()
                    print(f"   📤 Sent using Ctrl+Enter")
                    send_clicked = True
                except:
                    pass
            
            time.sleep(2)
            return send_clicked
            
        except Exception as e:
            print(f"❌ Error typing message: {e}")
            return False
    
    def check_accepted_connections(self) -> List[Dict]:
        """
        Check which connection requests have been accepted
        BEST approach - checks Sent Invitations page
        People who accepted will NO LONGER appear in sent invitations!
        Returns list of newly accepted connections
        """
        if not self.logged_in:
            return []
        
        print("\n🔍 Checking for accepted connections...")
        
        newly_accepted = []
        pending_requests = self.db.get_pending_requests()
        
        if not pending_requests:
            print("   No pending requests to check")
            return []
        
        print(f"   📋 {len(pending_requests)} pending requests in database")
        
        # Build maps for matching
        pending_by_url = {}
        for req in pending_requests:
            url_key = req["linkedin_url"].split("?")[0].rstrip("/").lower()
            # Also handle /in/ variations
            if "/in/" in url_key:
                username = url_key.split("/in/")[-1].rstrip("/")
                pending_by_url[username] = req
            pending_by_url[url_key] = req
        
        # METHOD 1: Check "Sent Invitations" page
        # People who accepted will NOT appear here anymore!
        still_pending_usernames = set()
        
        try:
            print("   📤 Checking Sent Invitations page...")
            self.driver.get("https://www.linkedin.com/mynetwork/invitation-manager/sent/")
            self._random_delay(4, 6)
            
            # Scroll to load all invitations
            last_height = 0
            for scroll_attempt in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self._random_delay(1.5, 2.5)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Find all profile links on the page - these are STILL PENDING
            all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
            
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    if href and "/in/" in href:
                        # Extract username from URL
                        username = href.split("/in/")[-1].split("?")[0].rstrip("/").lower()
                        if username and len(username) > 1:
                            still_pending_usernames.add(username)
                except:
                    continue
            
            print(f"   📋 {len(still_pending_usernames)} invitations still pending on LinkedIn")
            
            # Debug: show some of the pending usernames
            if still_pending_usernames:
                sample = list(still_pending_usernames)[:5]
                print(f"   Sample pending: {sample}")
            
            # Now find who ACCEPTED = in our pending list but NOT in still_pending
            # BUT we need to VERIFY they're actually connected (not declined)
            potential_accepted = []
            for url_key, req in list(pending_by_url.items()):
                # Extract username from our URL
                if "/in/" in url_key:
                    our_username = url_key.split("/in/")[-1].rstrip("/").lower()
                else:
                    our_username = url_key.lower()
                
                # Check if this username is NOT in still pending list
                if our_username not in still_pending_usernames:
                    # This person is no longer in sent invitations
                    # Could be: accepted, declined, or withdrawn
                    if req not in potential_accepted:
                        potential_accepted.append(req)
            
            print(f"   🔍 {len(potential_accepted)} no longer in sent invitations - verifying...")
            
            # VERIFY each one by visiting their profile
            for req in potential_accepted:
                try:
                    name = req["name"]
                    profile_url = req["linkedin_url"]
                    print(f"   Verifying: {name}...")
                    
                    self.driver.get(profile_url)
                    self._random_delay(2, 3)
                    
                    if self._is_already_connected():
                        print(f"   ✅ {name} CONFIRMED ACCEPTED!")
                        self.db.mark_request_accepted(profile_url)
                        newly_accepted.append(req)
                    else:
                        # They declined or withdrew - mark as declined
                        print(f"   ❌ {name} - NOT connected (declined/expired)")
                        # Update status to declined
                        conn = self.db.get_connection()
                        cur = conn.cursor()
                        cur.execute("UPDATE connection_requests SET status = 'declined' WHERE linkedin_url = ?", 
                                   (profile_url,))
                        conn.commit()
                        conn.close()
                except Exception as e:
                    print(f"   ⚠️ Error verifying {req['name']}: {e}")
            
        except Exception as e:
            print(f"   ⚠️ Sent invitations check failed: {e}")
            import traceback
            traceback.print_exc()
        
        # METHOD 2: Also check Notifications as backup
        if len(newly_accepted) == 0:
            try:
                print("   📬 Also checking notifications...")
                self.driver.get("https://www.linkedin.com/notifications/")
                self._random_delay(3, 4)
                
                # Scroll to load more
                for _ in range(3):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    self._random_delay(1, 1.5)
                
                # Get page source and look for acceptance patterns
                page_source = self.driver.page_source
                
                # Find notification cards
                notif_cards = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div.nt-card, article.nt-card, div[class*='notification']")
                
                for card in notif_cards[:30]:
                    try:
                        card_text = card.text.lower()
                        if "accepted" in card_text:
                            # Find profile links in this card
                            links = card.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
                            for link in links:
                                href = link.get_attribute("href")
                                if href and "/in/" in href:
                                    username = href.split("/in/")[-1].split("?")[0].rstrip("/").lower()
                                    # Check if matches our pending
                                    for url_key, req in pending_by_url.items():
                                        if username in url_key or url_key in username:
                                            if req not in newly_accepted:
                                                name = req["name"]
                                                print(f"   ✅ {name} ACCEPTED! (from notifications)")
                                                self.db.mark_request_accepted(req["linkedin_url"])
                                                newly_accepted.append(req)
                                            break
                    except:
                        continue
                
            except Exception as e:
                print(f"   ⚠️ Notifications check failed: {e}")
        
        print(f"\n✅ Total newly accepted: {len(newly_accepted)}")
        for req in newly_accepted:
            print(f"   - {req['name']}")
        
        return newly_accepted
    
    def scan_existing_connections(self, is_recruiter: bool = True) -> List[Dict]:
        """
        Scan your existing connections to find recruiters
        This helps identify previous manual requests that got accepted
        """
        if not self.logged_in:
            return []
        
        print("\n🔍 Scanning existing connections...")
        
        # Go to My Network > Connections
        self.driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
        self._random_delay(3, 5)
        
        connections = []
        
        # Scroll and collect connections
        last_height = 0
        while True:
            # Get all connection cards
            connection_cards = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".mn-connection-card"
            )
            
            for card in connection_cards:
                try:
                    name_elem = card.find_element(By.CSS_SELECTOR, ".mn-connection-card__name")
                    link_elem = card.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
                    
                    name = name_elem.text.strip()
                    profile_url = link_elem.get_attribute("href")
                    
                    # Clean URL
                    if profile_url and "/in/" in profile_url:
                        profile_url = profile_url.split("?")[0]
                        
                        if not self.db.is_existing_connection(profile_url):
                            self.db.add_existing_connection(profile_url, name, is_recruiter)
                            connections.append({"name": name, "linkedin_url": profile_url})
                            print(f"  📌 Found: {name}")
                            
                except:
                    continue
            
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._random_delay(2, 3)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        print(f"✅ Found {len(connections)} connections")
        return connections
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logged_in = False
            print("🔒 Browser closed")


# Quick test
if __name__ == "__main__":
    from config import DATABASE_PATH
    
    db = DatabaseManager(DATABASE_PATH)
    bot = LinkedInBot(db)
    
    try:
        if bot.login():
            print("Login successful!")
            # Add your test code here
    finally:
        input("Press Enter to close browser...")
        bot.close()
