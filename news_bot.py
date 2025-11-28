import requests
import os
import json
import feedparser
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime
import time

# --- CONFIGURATION ---
BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID'] # Single ID or "ID1,ID2"
SCREENER_COOKIE = os.environ['SCREENER_COOKIE']

# Keywords that trigger an alert (You can add more)
ALERT_KEYWORDS = [
    "result", "dividend", "split", "bonus", "buyback", 
    "acquisition", "merger", "deal", "order", "resign", 
    "fraud", "audit", "profit", "loss", "approved"
]

def send_telegram(message):
    ids = CHAT_ID.split(',')
    for user_id in ids:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": user_id.strip(), "text": message, "parse_mode": "Markdown", "disable_web_page_preview": True}
        requests.post(url, json=payload)

def load_seen_news():
    try:
        with open('seen_news.json', 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_seen_news(seen_set):
    # Keep only last 500 items to prevent file from getting too big
    recent_items = list(seen_set)[-500:] 
    with open('seen_news.json', 'w') as f:
        json.dump(recent_items, f)

# --- SOURCE 1: SCREENER OFFICIAL FEED ---
def check_screener_feed(seen_ids):
    print("Checking Screener Feed...")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": SCREENER_COOKIE
    }
    
    # This page shows updates specifically for YOUR watchlist
    url = "https://www.screener.in/feed/"
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Screener feed items are usually in <li> tags with specific classes
        items = soup.find_all('li', class_='list-group-item')
        
        new_alerts = []
        
        for item in items:
            # Extract Company Name
            company_tag = item.find('a', href=True)
            if not company_tag: continue
            company = company_tag.text.strip()
            link = "https://www.screener.in" + company_tag['href']
            
            # Extract The Announcement Text
            text_div = item.find('div')
            if not text_div: continue
            full_text = text_div.text.strip().lower()
            
            # Create a unique ID for this news (Company + First 20 chars of text)
            news_id = f"{company}_{full_text[:20]}"
            
            if news_id in seen_ids:
                continue

            # Check for Keywords
            if any(key in full_text for key in ALERT_KEYWORDS):
                # Clean up the text for display
                display_text = text_div.text.strip().replace('\n', ' ')
                msg = f"📢 **{company} Update**\n{display_text}\n[View Details]({link})"
                new_alerts.append(msg)
                seen_ids.add(news_id)
                
        return new_alerts
        
    except Exception as e:
        print(f"Screener Error: {e}")
        return []

# --- SOURCE 2: GOOGLE NEWS (For Deals/Rumors) ---
def check_google_news(watchlist, seen_ids):
    print("Checking Google News...")
    new_alerts = []
    
    # We combine stocks into batches to save API calls
    # Query: "(StockA OR StockB) AND (Deal OR Acquisition OR Split)"
    batch_size = 10
    
    for i in range(0, len(watchlist), batch_size):
        batch = watchlist[i:i+batch_size]
        query_stocks = " OR ".join([f'"{name}"' for name in batch])
        query_topics = "(deal OR acquisition OR merger OR order win OR fraud)"
        
        full_query = f"({query_stocks}) AND {query_topics} when:1d"
        encoded_query = urllib.parse.quote(full_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries:
            news_id = entry.link
            if news_id in seen_ids: continue
            
            # Double check: Ensure stock name is actually in title (reduces noise)
            if any(stock.lower() in entry.title.lower() for stock in batch):
                msg = f"📰 **News Alert**\n{entry.title}\n[Read Article]({entry.link})"
                new_alerts.append(msg)
                seen_ids.add(news_id)
                
    return new_alerts

def get_watchlist_from_screener():
    # Re-uses your existing logic to get the list of names for Google News
    headers = {"Cookie": SCREENER_COOKIE, "User-Agent": "Mozilla/5.0"}
    # Use your MAIN watchlist URL here
    url = os.environ['SCREENER_URL'].split(',')[0] 
    try:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, 'lxml')
        links = soup.select("table tbody tr a[href*='/company/']")
        return [link.text.strip() for link in links]
    except:
        return []

if __name__ == "__main__":
    seen_news = load_seen_news()
    
    # 1. Official Filings
    filing_alerts = check_screener_feed(seen_news)
    for msg in filing_alerts:
        send_telegram(msg)
        time.sleep(1) # Pause to avoid spam block
        
    # 2. Media News (Optional - Uncomment if you want Google News too)
    # watchlist = get_watchlist_from_screener()
    # if watchlist:
    #     media_alerts = check_google_news(watchlist, seen_news)
    #     for msg in media_alerts:
    #         send_telegram(msg)
    
    save_seen_news(seen_news)
