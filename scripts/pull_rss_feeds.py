import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def write_rss_content_to_file(content, filename="rss_feeds_content.txt"):
    """Write RSS feed content to a file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    return filename

def test_google_news_sa():
    """Test fetching news from Google News South Africa RSS feed"""
    feed_url = "https://news.google.com/rss?when:24h&hl=en-ZA&gl=ZA&ceid=ZA:en"
    content = []
    
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
        
        print(f"Found {len(items)} news items.\n")
        
        # Collect all items
        for i, item in enumerate(items):
            title = item.find("title").text if item.find("title") is not None else "No title"
            source = item.find("source").text if item.find("source") is not None else "Unknown source"
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else "Unknown date"
            link = item.find("link").text if item.find("link") is not None else "No link"
            
            article_content = f"\nARTICLE {i+1}\nTitle: {title}\nSource: {source}\nPublished: {pub_date}\nLink: {link}\n"
            content.append(article_content)
        
        return "\n".join(content)
    
    except Exception as e:
        print(f"Error fetching or parsing RSS feed: {e}")
        return None

def test_sundaytimes_rss():
    """Test fetching RSS from Sunday Times (included for comparison)"""
    feed_url = "https://www.timeslive.co.za/rss/?publication=sunday-times&section=news"
    content = []
    
    try:
        print("\nFetching Sunday Times RSS feed...")
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
        
        print(f"Found {len(items)} news items.\n")
        
        # Collect all items
        for i, item in enumerate(items):
            title = item.find("title").text if item.find("title") is not None else "No title"
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else "Unknown date"
            link = item.find("link").text if item.find("link") is not None else "No link"
            description = item.find("description").text if item.find("description") is not None else "No description"
            
            article_content = f"\nARTICLE {i+1}\nTitle: {title}\nDescription: {description}\nPublished: {pub_date}\nLink: {link}\n"
            content.append(article_content)
        
        return "\n".join(content)
    
    except Exception as e:
        print(f"Error fetching or parsing RSS feed: {e}")
        return None

def test_daily_maverick_rss():
    """Test fetching RSS from Daily Maverick"""
    feed_url = "https://www.dailymaverick.co.za/dmrss/"
    content = []
    
    try:
        print("\nFetching Daily Maverick RSS feed...")
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
        
        print(f"Found {len(items)} news items.\n")
        
        # Collect all items
        for i, item in enumerate(items):
            title = item.find("title").text if item.find("title") is not None else "No title"
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else "Unknown date"
            link = item.find("link").text if item.find("link") is not None else "No link"
            description = item.find("description").text if item.find("description") is not None else "No description"
            
            article_content = f"\nARTICLE {i+1}\nTitle: {title}\nDescription: {description}\nPublished: {pub_date}\nLink: {link}\n"
            content.append(article_content)
        
        return "\n".join(content)
    
    except Exception as e:
        print(f"Error fetching or parsing RSS feed: {e}")
        return None

def test_mailguardian_rss():
    """Test fetching RSS from Mail & Guardian (included for comparison)"""
    feed_url = "https://mg.co.za/feed/"
    content = []
    
    try:
        print("\nFetching Mail-Guardian RSS feed...")
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
        
        print(f"Found {len(items)} news items.\n")
        
        # Collect all items
        for i, item in enumerate(items):
            title = item.find("title").text if item.find("title") is not None else "No title"
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else "Unknown date"
            link = item.find("link").text if item.find("link") is not None else "No link"
            description = item.find("description").text if item.find("description") is not None else "No description"
            
            # Get the full content if available (Mail & Guardian specific)
            content_elem = item.find(".//content:encoded", namespaces={"content": "http://purl.org/rss/1.0/modules/content/"})
            full_content = content_elem.text if content_elem is not None else "No full content available"
            
            article_content = f"\nARTICLE {i+1}\nTitle: {title}\nDescription: {description}\nFull Content: {full_content}\nPublished: {pub_date}\nLink: {link}\n"
            content.append(article_content)
        
        return "\n".join(content)
    
    except Exception as e:
        print(f"Error fetching or parsing RSS feed: {e}")
        return None

def get_all_rss_content():
    """
    Retrieves content from all RSS feeds.
    """
    try:
        # Read the RSS feeds content
        with open('outputs/rss_feeds_content.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Error reading RSS feeds content: {e}")
        return "Error: Could not retrieve RSS feeds content."

if __name__ == "__main__":
    print("Testing South African News RSS Feeds")
    print("=" * 50)
    
    get_all_rss_content()
    
    print("\nRSS Feed Testing Complete!")
    
    # Save to file
    with open("outputs/rss_feeds_content.txt", "w", encoding="utf-8") as f:
        f.write(combined_content)
    
    print(f"\nFull RSS feeds content saved to outputs/rss_feeds_content.txt") 