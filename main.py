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

def find_value(row, possible_names):
    """Helper to find a value from a list of possible column names."""
    for col in possible_names:
        if col in row:
            return row[col]
    return None # Not found

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
            return "❌ No data table found."
        
        df = dfs[0]
        
        screen_name = url.strip().split('/')[-2].replace('-', ' ').title()
        report_section = f"📂 *{screen_name}*\n"
        
        # --- DEBUG: If you get N/A, this helps us see what columns exist ---
        # Uncomment the next line if you are still stuck, it will send ALL column names to Telegram
        # return f"DEBUG: Columns found: {', '.join(df.columns)}"

        for index, row in df.head(5).iterrows():
            # 1. SMART SEARCH for Name
            name = find_value(row, ['Name', 'Company Name', 'Stock Name']) or 'Unknown'
            
            # 2. SMART SEARCH for Price (Checks multiple variations)
            price = find_value(row, ['CMP', 'Current Price', 'Price', 'CMP Rs.', 'Last Price'])
            
            # If price is STILL missing, show the first available column so we can debug
            if price is None:
                 price = "N/A"
            
            # 3. SMART SEARCH for other columns
            rsi = find_value(row, ['RSI', 'RSI 14', 'Relative Strength Index']) or 'N/A'
            qtr_profit = find_value(row, ['Qtr Profit Var %', 'YOY Qtr Profit Var %', 'Qtr Profit Growth']) or 'N/A'
            fii_chg = find_value(row, ['Chg in FII Hold %', 'Change in FII Hold %', 'FII Change']) or 'N/A'
            
            # 4. Format Message
            report_section += f"🔹 *{name}* | ₹{price} | RSI: {rsi}\n"
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
