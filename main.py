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
        
        screen_name = url.strip().split('/')[-2].replace('-', ' ').title()
        report_section = f"📂 *{screen_name}*\n"
        
        # Change '5' to '10' or '15' if you want more stocks
        for index, row in df.head(5).iterrows():
            # 1. Basic Info
            name = row.get('Name', 'N/A')
            price = row.get('Current Price', row.get('Current Price', 'N/A'))
            
            # 2. Fetch New Columns (Exact spelling matches Screener headers)
            # We use .get() so it won't crash if a column is missing from one of your screens
            rsi = row.get('RSI', 'N/A')
            qtr_profit = row.get('Qtr Profit Var %', 'N/A')
            fii_chg = row.get('Chg in FII Hold %', 'N/A')
            
            # 3. Format the Message
            # Line 1: Name, Price, RSI
            report_section += f"🔹 *{name}* | ₹{price} | RSI: {rsi}\n"
            # Line 2: Profit Var & FII Change (Indented slightly)
            report_section += f"   └ QtrPf: {qtr_profit}% | FII: {fii_chg}%\n\n"
            
        return report_section

    except Exception as e:
        return f"❌ Error on {url}: {str(e)}\n"

if __name__ == "__main__":
    final_message = "📊 **Daily Market Watch**\n\n"
    
    for link in SCREENER_URLS:
        if len(link.strip()) > 5:
            final_message += get_screener_data(link)
            final_message += "------------------\n"
    
    send_telegram_message(final_message)
