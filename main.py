import requests
import pandas as pd
import os
import time

# --- CONFIGURATION ---
BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
SCREENER_COOKIE = os.environ['SCREENER_COOKIE']
# Now we expect a comma-separated string of URLs
SCREENER_URLS = os.environ['SCREENER_URL'].split(',')

def send_telegram_message(message):
    # Telegram has a limit of ~4096 chars. If message is too long, we might need to split it,
    # but for 3 screens, this simple version usually works fine.
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

def get_screener_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": SCREENER_COOKIE
    }
    
    try:
        response = requests.get(url.strip(), headers=headers)
        if response.status_code != 200:
            return f"❌ Error: {response.status_code}"
        
        dfs = pd.read_html(response.text)
        if not dfs:
            return "❌ No data"
        
        df = dfs[0]
        
        # Extract a readable name from the URL (e.g., 'coffee-can-portfolio')
        screen_name = url.strip().split('/')[-2].replace('-', ' ').title()
        
        report_section = f"📂 *{screen_name}*\n"
        
        # Get top 5 stocks from this screen to save space
        for index, row in df.head(10).iterrows():
            name = row.get('Name', 'N/A')
            price = row.get('CMP', row.get('Current Price', 'N/A'))
            pe = row.get('P/E', 'N/A')
            report_section += f"🔹 {name} | ₹{price} | PE: {pe}\n"
            
        return report_section + "\n"

    except Exception as e:
        return f"❌ Error on {url}: {str(e)}\n"

if __name__ == "__main__":
    final_message = "📊 **Daily Market Watch**\n\n"
    
    for link in SCREENER_URLS:
        if len(link.strip()) > 5: # simple check to ignore empty strings
            final_message += get_screener_data(link)
            final_message += "------------------\n"
    
    send_telegram_message(final_message)
