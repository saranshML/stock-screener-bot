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
# Handle multiple Chat IDs if you shared the bot
CHAT_ID = os.environ['TELEGRAM_CHAT_ID'] 
SCREENER_COOKIE = os.environ['SCREENER_COOKIE']

# UPDATED KEYWORDS based on your screenshot
ALERT_KEYWORDS = [
    # Positive/Neutral
    "result", "dividend", "split", "bonus", "buyback", 
    "acquisition", "merger", "deal", "order", "profit", "fine", "penalty", "fraud", "investigation", "search", "raid", "concern",
    "disclosure", "non-compliance", "loss"
]

def send_telegram(message):
    # Splits "ID1,ID2" into a list and sends to everyone
    ids = CHAT_ID.split(',')
    for user_id in ids:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": user_id.strip(), 
            "text": message, 
            "parse_mode": "Markdown", 
            "disable_web_page_preview": True
        }
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")

def load_seen_news():
    try:
        with open('seen_news.json', 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_seen_news(seen_set):
    recent_items = list(seen_set)[-500:] 
    with open('seen_news.json', 'w') as f:
        json.dump(recent_items, f)

# --- SOURCE 1: SCREENER DASHBOARD ---
def check_screener_feed(seen_ids):
    print("Checking Screener Dashboard...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Cookie": SCREENER_COOKIE
    }
    
    # FIX: Changed URL to the main dashboard as per your screenshot
    url = "https://www.screener.in/"
    
    try:
        response = requests.get(url, headers=headers)
        
        # Security Check
        if "Login" in response.text or "Register" in response.text:
            print("❌ Cookie Expired! Please update Secret.")
            return []

        soup = BeautifulSoup(response.text, 'lxml')
        
        # In the Dashboard, feed items are usually in a list
        # We look for ALL list items to be safe
        items = soup.find_all('li')
        
        new_alerts = []
        
        for item in items:
            # 1. Find Company Link (It's usually bold or inside an anchor tag)
            company_tag = item.find('a', href=True)
            if not company_tag: continue
            
            # Filter: Ensure the link is actually a company page (contains /company/)
            if "/company/" not in company_tag['href']:
                continue

            company = company_tag.text.strip()
            link = "https://www.screener.in" + company_tag['href']
            
            # 2. Get the announcement text
            # Usually the text is just adjacent to the link or in a div
            full_text_blob = item.text.lower().strip()
            
            # Create a unique ID for this specific news event
            # We use first 30 chars of text to make it unique
            news_id = f"{company}_{full_text_blob[:30]}"
            
            if news_id in seen_ids:
                continue

            # 3. Keyword Check
            if any(key in full_text_blob for key in ALERT_KEYWORDS):
                # Clean up the text for display (remove extra spaces)
                display_text = " ".join(item.text.split())
                
                # Format: "Broadcom: Result Declared..."
                msg = f"📢 **{company} Alert**\n{display_text}\n[View Details]({link})"
                new_alerts.append(msg)
                seen_ids.add(news_id)
                
        return new_alerts
        
    except Exception as e:
        print(f"Screener Error: {e}")
        return []

if __name__ == "__main__":
    seen_news = load_seen_news()
    
    filing_alerts = check_screener_feed(seen_news)
    
    if filing_alerts:
        print(f"Found {len(filing_alerts)} new alerts.")
        for msg in filing_alerts:
            send_telegram(msg)
            time.sleep(1)
    else:
        print("No new relevant news found.")
    
    save_seen_news(seen_news)
