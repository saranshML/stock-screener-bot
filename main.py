import requests
import pandas as pd
import os

# --- CONFIGURATION ---
BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
SCREENER_COOKIE = os.environ['SCREENER_COOKIE']
SCREENER_URLS = os.environ['SCREENER_URL'].split(',')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

def get_screener_columns(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": SCREENER_COOKIE
    }
    
    try:
        response = requests.get(url.strip(), headers=headers)
        dfs = pd.read_html(response.text)
        if not dfs:
            return "❌ No tables found."
        
        df = dfs[0]
        
        # This is the magic part: It grabs the exact headers
        columns = list(df.columns)
        
        screen_name = url.strip().split('/')[-2]
        return f"🕵️ **Debug Report for {screen_name}**\n\nI see these columns:\n`{str(columns)}`"

    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    # We only check the FIRST screen to solve the mystery
    first_link = SCREENER_URLS[0]
    msg = get_screener_columns(first_link)
    send_telegram_message(msg)
