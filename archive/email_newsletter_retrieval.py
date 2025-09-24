# ABOUTME: Email newsletter retrieval for SA News Podcast
# ABOUTME: Fetches daily news content from email newsletters

import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import os
from datetime import datetime
import pytz
from email.utils import parsedate_to_datetime
import sys
from secure_secrets import get_secrets

# Load email credentials from secure secrets
try:
    secrets = get_secrets()
    email_creds = secrets.get_email_credentials()
except Exception as e:
    print(f"ERROR: Failed to load email credentials: {e}")
    sys.exit(1)

def convert_to_sast(date_str):
    """
    Convert email date string to SAST timezone and format nicely
    """
    try:
        # Parse the email date string to datetime
        dt = parsedate_to_datetime(date_str)
        
        # Convert to SAST
        sast = pytz.timezone('Africa/Johannesburg')
        sast_time = dt.astimezone(sast)
        
        # Format in a readable way with SAST explicitly mentioned
        return sast_time.strftime('%a, %d %b %Y %H:%M (SAST)')
    except Exception as e:
        print(f"Error converting date: {e}")
        return date_str

def is_within_24_hours(date_str):
    """Check if the given date is within the last 24 hours"""
    try:
        # Parse the date string
        print(f"\nDEBUG: Raw date string: {date_str}")
        dt = parsedate_to_datetime(date_str)
        print(f"DEBUG: Parsed datetime: {dt}")
        
        # Get current time in UTC
        now = datetime.now(pytz.UTC)
        print(f"DEBUG: Current UTC time: {now}")
        
        # Calculate the time difference in hours
        time_diff_hours = (now - dt).total_seconds() / 3600
        
        # Debug logging
        print(f"DEBUG: Newsletter timestamp: {dt}")
        print(f"DEBUG: Current timestamp: {now}")
        print(f"DEBUG: Hours old: {time_diff_hours:.1f}")
        print(f"DEBUG: Within 24h? {time_diff_hours <= 24}")
        
        # Strict 24-hour check
        return time_diff_hours <= 24
    except Exception as e:
        print(f"ERROR: Error checking date: {e}")
        print(f"ERROR: Problematic date string: {date_str}")
        return False

def fetch_newsletter_from_email():
    """
    Retrieve the last two Daily Maverick First Thing or Afternoon Thing newsletters from your email
    
    Requires:
    - Email account credentials in .env file
    - Daily Maverick newsletter subscription
    """
    # Email account credentials
    EMAIL = email_creds["address"]
    PASSWORD = email_creds["password"]
    IMAP_SERVER = email_creds["imap_server"]
    
    mail = None
    try:
        print(f"Connecting to {IMAP_SERVER}...")
        # Connect to the email server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        print("Logging in...")
        mail.login(EMAIL, PASSWORD)
        print("Selecting inbox...")
        mail.select("INBOX")
        
        # Search for emails from Daily Maverick
        print("Searching for Daily Maverick newsletters...")
        status, messages = mail.search(None, '(FROM "dailymaverick.co.za")')
        
        if status != "OK":
            print(f"Error searching emails: {status}")
            return None
            
        if not messages[0]:
            print("No Daily Maverick newsletters found")
            return None
        
        # Get the last two email IDs
        email_ids = messages[0].split()[-2:]  # Get the last two emails
        # Reverse the order so newest is first
        email_ids.reverse()
        
        newsletters = []
        for email_id in email_ids:
            # Fetch the email
            print(f"Fetching email {email_id.decode()}...")
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                print(f"Failed to fetch email {email_id}")
                continue
            
            # Parse the email
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Get email subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            
            print(f"\nProcessing newsletter: {subject}")
            print(f"Date: {msg['Date']}")
            
            # Check if the email is within 24 hours
            if not is_within_24_hours(msg["Date"]):
                print(f"Skipping newsletter - older than 24 hours: {subject}")
                continue
                
            # Convert date to SAST
            date_sast = convert_to_sast(msg["Date"])
            print(f"Processing newsletter: {subject} (SAST: {date_sast})")
            
            # Extract the HTML content
            newsletter_content = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/html":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8')
                            newsletter_content = body
                            break
                        except:
                            continue
            else:
                content_type = msg.get_content_type()
                if content_type == "text/html":
                    newsletter_content = msg.get_payload(decode=True).decode('utf-8')
            
            # Parse the HTML to extract just the newsletter content
            if newsletter_content:
                soup = BeautifulSoup(newsletter_content, "html.parser")
                
                # Extract main content (this will need adjusting based on the actual email structure)
                main_content = soup.find("div", {"class": "content"}) or soup.find("table", {"class": "main"})
                
                if main_content:
                    # Clean up the content by removing images, styling, etc.
                    for img in main_content.find_all("img"):
                        img.decompose()
                    
                    # Get all text paragraphs
                    paragraphs = [p.get_text().strip() for p in main_content.find_all("p")]
                    
                    # Join paragraphs with newlines
                    cleaned_content = "\n\n".join(filter(None, paragraphs))
                    
                    newsletters.append({
                        "subject": subject,
                        "date": date_sast,  # Use SAST date
                        "content": cleaned_content
                    })
                else:
                    # If we couldn't find the main content container, return all text
                    text_content = soup.get_text().strip()
                    newsletters.append({
                        "subject": subject,
                        "date": date_sast,  # Use SAST date
                        "content": text_content
                    })
        
        return newsletters if newsletters else None
        
    except Exception as e:
        print(f"Error retrieving newsletters: {e}")
        return None
    finally:
        try:
            mail.close()
        except:
            pass
        try:
            mail.logout()
        except:
            pass

def get_latest_newsletter_content():
    """
    Retrieves the content of the latest two Daily Maverick newsletters.
    """
    try:
        # Read the Daily Maverick newsletter content
        with open('outputs/daily_maverick_first_thing.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Error reading newsletter content: {e}")
        return "Error: Could not retrieve newsletter content."

if __name__ == "__main__":
    newsletters = fetch_newsletter_from_email()
    
    # Always open the file in write mode to either update with new content or clear old content
    with open("outputs/daily_maverick_first_thing.txt", "w", encoding="utf-8") as f:
        if newsletters:
            combined_content = ""
            for newsletter in newsletters:
                print(f"Retrieved: {newsletter['subject']} ({newsletter['date']})")
                print("\nEXCERPT:")
                print(newsletter['content'][:500] + "...")
                
                # Combine content with clear separation and cleaner date format
                combined_content += f"=== {newsletter['subject']} - {newsletter['date']} ===\n\n"
                combined_content += newsletter['content'] + "\n\n"
            
            f.write(combined_content)
            print(f"\nFull newsletters saved to outputs/daily_maverick_first_thing.txt")
        else:
            # Write a clear message when no recent newsletters are found
            message = "NO_RECENT_CONTENT: No newsletters found within the last 24 hours."
            f.write(message)
            print("\nNo recent newsletters found - cleared old content from file")