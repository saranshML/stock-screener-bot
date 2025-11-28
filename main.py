import requests
import pandas as pd
import os
import time

# --- CONFIGURATION (Loaded from GitHub Secrets) ---
BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
SCREENER_COOKIE = os.environ['SCREENER_COOKIE']
SCREENER_URL = os.environ['SCREENER_URL']

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def get_screener_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": SCREENER_COOKIE
    }
    
    response = requests.get(SCREENER_URL, headers=headers)
    
    if response.status_code != 200:
        return f"❌ Error fetching Screener data. Status: {response.status_code}"
    
    try:
        # Read the HTML table into a DataFrame
        dfs = pd.read_html(response.text)
        if not dfs:
            return "❌ No tables found on the Screener page."
        
        # Usually the main stock table is the first one
        df = dfs[0]
        
        # Clean up: Keep top 10 stocks and relevant columns
        # Adjust 'Name' and 'CMP' if columns are named differently in your screen
        result_msg = f"📊 **Daily Stock Screener Report**\n\n"
        
        for index, row in df.head(10).iterrows():
            # Customize these column names based on your actual Screen columns
            name = row.get('Name', 'N/A')
            price = row.get('CMP', row.get('Current Price', 'N/A'))
            pe = row.get('P/E', 'N/A')
            
            result_msg += f"🔹 *{name}* | ₹{price} | PE: {pe}\n"
            
        result_msg += f"\n[View Full Screen]({SCREENER_URL})"
        return result_msg

    except Exception as e:
        return f"❌ Error parsing data: {str(e)}"

if __name__ == "__main__":
    msg = get_screener_data()
    send_telegram_message(msg)
