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

def clean_column_name(col_name):
    """
    Removes invisible characters (\xa0) and double spaces 
    so 'CMP  Rs.' becomes 'CMP Rs.'
    """
    return col_name.replace('\xa0', ' ').replace('  ', ' ').strip()

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
        
        # --- THE FIX: Clean all column headers automatically ---
        df.columns = [clean_column_name(c) for c in df.columns]
        
        screen_name = url.strip().split('/')[-2].replace('-', ' ').title()
        report_section = f"📂 *{screen_name}*\n"

        # Processing the stocks
        for index, row in df.head(10).iterrows(): # Shows Top 10
            
            # Now we use the clean names based on your debug report
            name = row.get('Name', 'N/A')
            price = row.get('CMP Rs.', row.get('Current Price', 'N/A'))
            rsi = row.get('RSI', 'N/A')
            qtr_profit = row.get('Qtr Profit Var %', 'N/A')
            fii_chg = row.get('Chg in FII Hold %', 'N/A')
            
            # --- Format the output message ---
            report_section += f"🔹 *{name}* | ₹{price}\n"
            report_section += f"   RSI: {rsi} | QtrPf: {qtr_profit}% | FII: {fii_chg}%\n\n"
            
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
