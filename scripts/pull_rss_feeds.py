import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
from email.utils import parsedate_to_datetime

def convert_to_sast(date_str):
    """Convert date string to SAST timezone and format nicely"""
    try:
        # Parse the date string to datetime
        dt = parsedate_to_datetime(date_str)
        
        # Convert to SAST
        sast = pytz.timezone('Africa/Johannesburg')
        sast_time = dt.astimezone(sast)
        
        # Format in a readable way
        return sast_time.strftime('%a, %d %b %Y %H:%M (SAST)')
    except Exception as e:
        print(f"Error converting date: {e}")
        return date_str

def is_within_24_hours(date_str):
    """Check if the given date is within the last 24 hours"""
    try:
        # Parse the date string
        dt = parsedate_to_datetime(date_str)
        
        # Get current time in UTC
        now = datetime.now(pytz.UTC)
        
        # Calculate the time difference in hours
        time_diff_hours = (now - dt).total_seconds() / 3600
        
        # Debug logging
        print(f"Article timestamp: {dt}")
        print(f"Current timestamp: {now}")
        print(f"Hours old: {time_diff_hours:.1f}")
        print(f"Within 24h? {time_diff_hours <= 24}")
        
        # Strict 24-hour check
        return time_diff_hours <= 24
    except Exception as e:
        print(f"Error checking date: {e}")
        print(f"Problematic date string: {date_str}")
        return False

def write_rss_content_to_file(content, filename="outputs/rss_feeds_content.txt"):
    """Write RSS feed content to a file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    return filename

def process_feed_items(items, source_name):
    """Process RSS feed items with date filtering and SAST conversion"""
    content = []
    recent_count = 0
    skipped_count = 0
    
    print(f"\nProcessing {len(items)} items from {source_name}")
    
    for i, item in enumerate(items):
        title = item.find("title").text if item.find("title") is not None else "No title"
        pub_date = item.find("pubDate").text if item.find("pubDate") is not None else None
        link = item.find("link").text if item.find("link") is not None else "No link"
        description = item.find("description").text if item.find("description") is not None else "No description"
        
        print(f"\n{'='*50}")
        print(f"Checking article: {title}")
        print(f"Raw date from RSS: {pub_date}")
        
        # Skip articles older than 24 hours
        if not pub_date:
            print("❌ Skipping - No publication date")
            skipped_count += 1
            continue
            
        if not is_within_24_hours(pub_date):
            print("❌ Skipping - Article older than 24 hours")
            skipped_count += 1
            continue
        
        print("✅ Article is within 24 hours - including in feed")
        # Convert publication date to SAST
        sast_date = convert_to_sast(pub_date)
        recent_count += 1
        
        # Build article content
        article_content = f"\nARTICLE {recent_count} ({source_name})\nTitle: {title}\n"
        
        if source_name == "Google News SA":
            source = item.find("source").text if item.find("source") is not None else "Unknown source"
            article_content += f"Source: {source}\n"
        
        if description:
            article_content += f"Description: {description}\n"
            
        if source_name == "Mail & Guardian":
            content_elem = item.find(".//content:encoded", namespaces={"content": "http://purl.org/rss/1.0/modules/content/"})
            if content_elem is not None and content_elem.text:
                article_content += f"Full Content: {content_elem.text}\n"
        
        article_content += f"Published: {sast_date}\nLink: {link}\n"
        content.append(article_content)
    
    print(f"\nSummary for {source_name}:")
    print(f"Total items: {len(items)}")
    print(f"Recent items (< 24h): {recent_count}")
    print(f"Skipped items: {skipped_count}")
    
    return content, recent_count

def test_google_news_sa():
    """Test fetching news from Google News South Africa RSS feed"""
    feed_url = "https://news.google.com/rss?when:24h&hl=en-ZA&gl=ZA&ceid=ZA:en"
    
    try:
        print("Fetching Google News SA RSS feed...")
        response = requests.get(feed_url)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return None
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Find all items (news articles)
        items = root.findall(".//item")
        
        if not items:
            print("No news items found in the feed.")
            return None
        
        content, recent_count = process_feed_items(items, "Google News SA")
        print(f"Found {recent_count} recent news items (last 24 hours).\n")
        
        return "\n".join(content) if content else None
    
    except Exception as e:
        print(f"Error fetching or parsing RSS feed: {e}")
        return None

def test_sundaytimes_rss():
    """Test fetching RSS from Sunday Times"""
    feed_url = "https://www.timeslive.co.za/rss/?publication=sunday-times&section=news"
    
    try:
        print("\nFetching Sunday Times RSS feed...")
        response = requests.get(feed_url)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return None
        
        # Parse XML
        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        
        if not items:
            print("No news items found in the feed.")
            return None
        
        content, recent_count = process_feed_items(items, "Sunday Times")
        print(f"Found {recent_count} recent news items (last 24 hours).\n")
        
        return "\n".join(content) if content else None
    
    except Exception as e:
        print(f"Error fetching or parsing RSS feed: {e}")
        return None

def test_daily_maverick_rss():
    """Test fetching RSS from Daily Maverick"""
    feed_url = "https://www.dailymaverick.co.za/dmrss/"
    
    try:
        print("\nFetching Daily Maverick RSS feed...")
        response = requests.get(feed_url)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return None
        
        # Parse XML
        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        
        if not items:
            print("No news items found in the feed.")
            return None
        
        content, recent_count = process_feed_items(items, "Daily Maverick")
        print(f"Found {recent_count} recent news items (last 24 hours).\n")
        
        return "\n".join(content) if content else None
    
    except Exception as e:
        print(f"Error fetching or parsing RSS feed: {e}")
        return None

def test_mailguardian_rss():
    """Test fetching RSS from Mail & Guardian"""
    feed_url = "https://mg.co.za/feed/"
    
    try:
        print("\nFetching Mail & Guardian RSS feed...")
        response = requests.get(feed_url)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return None
        
        # Parse XML
        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        
        if not items:
            print("No news items found in the feed.")
            return None
        
        content, recent_count = process_feed_items(items, "Mail & Guardian")
        print(f"Found {recent_count} recent news items (last 24 hours).\n")
        
        return "\n".join(content) if content else None
    
    except Exception as e:
        print(f"Error fetching or parsing RSS feed: {e}")
        return None

def get_all_rss_content():
    """Get content from all RSS feeds and combine them"""
    all_content = []
    
    # Get content from each feed
    google_content = test_google_news_sa()
    if google_content:
        all_content.append("\nGOOGLE NEWS SA FEED\n" + "="*50 + "\n" + google_content)
    
    sundaytimes_content = test_sundaytimes_rss()
    if sundaytimes_content:
        all_content.append("\nSUNDAY TIMES FEED\n" + "="*50 + "\n" + sundaytimes_content)
    
    daily_maverick_content = test_daily_maverick_rss()
    if daily_maverick_content:
        all_content.append("\nDAILY MAVERICK FEED\n" + "="*50 + "\n" + daily_maverick_content)
    
    mailguardian_content = test_mailguardian_rss()
    if mailguardian_content:
        all_content.append("\nMAIL & GUARDIAN FEED\n" + "="*50 + "\n" + mailguardian_content)
    
    # Combine all content
    combined_content = "\n\n".join(all_content)
    
    # Write to file
    filename = write_rss_content_to_file(combined_content)
    print(f"\nAll RSS feed content has been written to {filename}")
    
    return combined_content

if __name__ == "__main__":
    print("Testing South African News RSS Feeds")
    print("=" * 50)
    
    get_all_rss_content()
    
    print("\nRSS Feed Testing Complete!") 