import requests
import pandas as pd
import os
import google.generativeai as genai
import feedparser
import urllib.parse
from bs4 import BeautifulSoup
from collections import Counter # <-- NEW: The tool that counts duplicates

# --- CONFIGURATION ---
BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
SCREENER_COOKIE = os.environ['SCREENER_COOKIE']
SCREENER_URLS = os.environ['SCREENER_URL'].split(',')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# --- SETUP AI ---
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except:
        pass

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
    return col_name.replace('\xa0', ' ').replace('  ', ' ').strip()

def get_stock_news(stock_name):
    try:
        encoded_name = urllib.parse.quote(stock_name)
        rss_url = f"https://news.google.com/rss/search?q={encoded_name}+share+price+india+news&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(rss_url)
        if feed.entries:
            title = feed.entries[0].title.split(' - ')[0]
            link = feed.entries[0].link
            return f"\n📰 **News on {stock_name}:**\n[{title}]({link})"
        return ""
    except:
        return ""

def get_ai_analysis(stock_data_text):
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        prompt = (
            f"DATA:\n{stock_data_text}\n"
            "TASK: Pick top 2 best stocks. CRITERIA: High QtrPf, RSI < 70, +FII. "
            "WARN: If RSI > 75 or Neg Profit. "
            "OUTPUT RULES: No emoji. No intro/outro words. "
            "Format: STOCK: [Name] | WHY: [Data]. "
            "Max 40 words total."
        )
        response = model.generate_content(prompt)
        return f"\n🤖 **AI:**\n{response.text}"
    except Exception as e:
        return f"\n⚠️ AI Error: {str(e)}"

def get_screener_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": SCREENER_COOKIE
    }
    
    # We create a list to track stock names for this specific screen
    found_stocks = [] 

    try:
        response = requests.get(url.strip(), headers=headers)
        if response.status_code != 200:
            return f"❌ Error: {response.status_code}", "", []
        
        # 1. Parse Table
        dfs = pd.read_html(response.text)
        if not dfs:
            return "❌ No data table found.", "", []
        df = dfs[0]
        df.columns = [clean_column_name(c) for c in df.columns]

        # 2. Parse Links
        soup = BeautifulSoup(response.text, 'html.parser')
        stock_links = []
        table_rows = soup.select("table tbody tr")
        
        for row in table_rows:
            link_tag = row.select_one("a[href*='/company/']")
            if link_tag:
                full_link = f"https://www.screener.in{link_tag['href']}"
                stock_links.append(full_link)
            else:
                stock_links.append(None)
        
        screen_name = url.strip().split('/')[-2].replace('-', ' ').title()
        report_section = f"📂 *{screen_name}*\n"
        
        raw_data_for_ai = f"Screen: {screen_name}\n"
        first_stock_news = ""

        # Loop through top 10 stocks
        for index, row in df.head(10).iterrows():
            name = row.get('Name', 'N/A')
            price = row.get('CMP Rs.', row.get('Current Price', 'N/A'))
            rsi = row.get('RSI', 'N/A')
            qtr_profit = row.get('Qtr Profit Var %', 'N/A')
            fii_chg = row.get('Chg in FII Hold %', 'N/A')
            
            # Add to list for Confluence Check
            found_stocks.append(name)

            if index == 0:
                first_stock_news = get_stock_news(name)

            if index < len(stock_links) and stock_links[index]:
                link = stock_links[index]
            else:
                safe_name = urllib.parse.quote(name)
                link = f"https://www.screener.in/search/?query={safe_name}"
            
            report_section += f"🔹 [{name}]({link}) | ₹{price}\n"
            report_section += f"   RSI: {rsi} | QtrPf: {qtr_profit}% | FII: {fii_chg}%\n\n"
            
            raw_data_for_ai += f"{name}: Price {price}, RSI {rsi}, Profit Var {qtr_profit}%, FII Chg {fii_chg}%\n"
            
        report_section += first_stock_news + "\n"
            
        return report_section, raw_data_for_ai, found_stocks

    except Exception as e:
        return f"❌ Error on {url}: {str(e)}\n", "", []

if __name__ == "__main__":
    final_report_body = ""
    combined_ai_data = ""
    all_found_stocks = []
    
    # 1. Fetch data from all screens
    for link in SCREENER_URLS:
        if len(link.strip()) > 5:
            text_output, ai_input, stock_list = get_screener_data(link)
            final_report_body += text_output
            final_report_body += "------------------\n"
            combined_ai_data += ai_input
            all_found_stocks.extend(stock_list)
    
    # 2. FEATURE: CONFLUENCE DETECTOR (Super Pick)
    # We count how many times each stock appears across ALL your screens
    stock_counts = Counter(all_found_stocks)
    super_picks = [stock for stock, count in stock_counts.items() if count > 1]
    
    header_message = "📊 **Daily Market Watch**\n\n"
    
    if super_picks:
        header_message += "🚨 **SUPER PICKS DETECTED** 🚨\n"
        header_message += "_(Stocks appearing in multiple screens)_\n"
        for pick in super_picks:
            count = stock_counts[pick]
            # Create a simple search link for the super pick
            safe_name = urllib.parse.quote(pick)
            link = f"https://www.screener.in/search/?query={safe_name}"
            header_message += f"🔥 [{pick}]({link}) found in {count} lists!\n"
        header_message += "\n" + "="*15 + "\n\n"

    # 3. Assemble Final Message
    final_message = header_message + final_report_body
    
    if combined_ai_data and GEMINI_API_KEY:
        ai_insight = get_ai_analysis(combined_ai_data)
        final_message += ai_insight
    
    send_telegram_message(final_message)
