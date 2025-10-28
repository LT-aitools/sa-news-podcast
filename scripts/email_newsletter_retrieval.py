import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import os
from datetime import datetime
import pytz
from email.utils import parsedate_to_datetime
import sys
from scripts.secure_secrets import get_email_credentials

# Load email credentials from secure secrets
try:
    email_creds = get_email_credentials()
    if not all([email_creds['address'], email_creds['password']]):
        print("ERROR: Missing email credentials in secrets file")
        print("Please ensure email.address and email.password are set in ~/.config/sa-podcast/secrets.json")
        sys.exit(1)
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
    Retrieve newsletters from multiple South African news sources from your email
    
    Requires:
    - Email account credentials in .env file
    - Newsletter subscriptions to South African news sources
    """
    # Email account credentials from secure secrets
    email_creds = get_email_credentials()
    EMAIL = email_creds['address']
    PASSWORD = email_creds['password']
    IMAP_SERVER = email_creds['imap_server']
    
    # Define South African news sources to search for
    news_sources = [
        "dailymaverick.co.za",
        "*@heraldlive.co.za", 
        "*@*news24.com"
    ]
    
    mail = None
    try:
        print(f"Connecting to {IMAP_SERVER}...")
        # Connect to the email server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        print("Logging in...")
        mail.login(EMAIL, PASSWORD)
        print("Selecting inbox...")
        mail.select("INBOX")
        
        all_newsletters = []
        
        # Search for emails from each news source
        for source in news_sources:
            print(f"Searching for newsletters from {source}...")
            status, messages = mail.search(None, f'(FROM "{source}")')
            
            if status != "OK":
                print(f"Error searching emails from {source}: {status}")
                continue
                
            if not messages[0]:
                print(f"No newsletters found from {source}")
                continue
                
            # Get the last two email IDs for this source
            email_ids = messages[0].split()
            if len(email_ids) < 2:
                print(f"Only {len(email_ids)} newsletter(s) found from {source}")
                email_ids_to_fetch = email_ids
            else:
                email_ids_to_fetch = email_ids[-2:]  # Get the last 2 emails
                
            print(f"Found {len(email_ids)} newsletters from {source}, processing the last {len(email_ids_to_fetch)}")
            
            # Process each email from this source
            for email_id in email_ids_to_fetch:
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
                            except UnicodeDecodeError:
                                body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                                newsletter_content = body
                                break
                            except:
                                continue
                else:
                    content_type = msg.get_content_type()
                    if content_type == "text/html":
                        try:
                            newsletter_content = msg.get_payload(decode=True).decode('utf-8')
                        except UnicodeDecodeError:
                            newsletter_content = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                
                # Parse the HTML to extract just the newsletter content
                if newsletter_content:
                    soup = BeautifulSoup(newsletter_content, "html.parser")
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Get text content with proper line breaks
                    text_content = soup.get_text()
                    
                    # Clean up the text while preserving paragraph structure
                    lines = []
                    for line in text_content.splitlines():
                        line = line.strip()
                        if line:  # Only add non-empty lines
                            lines.append(line)
                    
                    # Join lines with proper spacing, preserving paragraph breaks
                    text_content = '\n\n'.join(lines)
                    
                    # Determine source name for display
                    source_name = source.replace("*@", "").replace("*", "")
                    if "dailymaverick" in source:
                        source_name = "Daily Maverick"
                    elif "heraldlive" in source:
                        source_name = "The Herald"
                    elif "news24" in source:
                        source_name = "News24"
                    
                    # Add to our collection
                    newsletter_data = {
                        'source': source_name,
                        'subject': subject,
                        'date': date_sast,
                        'content': text_content
                    }
                    all_newsletters.append(newsletter_data)
                    print(f"✅ Successfully processed newsletter from {source_name}: {subject}")
                else:
                    print(f"❌ No HTML content found in newsletter: {subject}")
        
        return all_newsletters
        
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
    Retrieves the content of the latest newsletters from multiple South African sources.
    """
    try:
        # Read the newsletter content
        with open('outputs/newsletter_content.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Error reading newsletter content: {e}")
        return "Error: Could not retrieve newsletter content."

if __name__ == "__main__":
    newsletters = fetch_newsletter_from_email()
    
    # Always open the file in write mode to either update with new content or clear old content
    with open("outputs/newsletter_content.txt", "w", encoding="utf-8") as f:
        if newsletters:
            combined_content = ""
            for newsletter in newsletters:
                print(f"Retrieved: {newsletter['source']} - {newsletter['subject']} ({newsletter['date']})")
                print("\nEXCERPT:")
                print(newsletter['content'][:500] + "...")
                
                # Combine content with clear separation and cleaner date format
                combined_content += f"=== {newsletter['source']}: {newsletter['subject']} - {newsletter['date']} ===\n\n"
                combined_content += newsletter['content'] + "\n\n"
            
            f.write(combined_content)
            print(f"\nFull newsletters saved to outputs/newsletter_content.txt")
        else:
            # Write a clear message when no recent newsletters are found
            message = "NO_RECENT_CONTENT: No newsletters found within the last 24 hours."
            f.write(message)
            print("\nNo recent newsletters found - cleared old content from file")