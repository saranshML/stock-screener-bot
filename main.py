import requests
import pandas as pd
import os
import google.generativeai as genai
import feedparser
import urllib.parse
from bs4 import BeautifulSoup

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
        # Tries to use the standard free model
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
    
    try:
        response = requests.get(url.strip(), headers=headers)
        if response.status_code != 200:
            return f"❌ Error: {response.status_code}", ""
        
        # 1. Parse Table Data (Pandas)
        dfs = pd.read_html(response.text)
        if not dfs:
            return "❌ No data table found.", ""
        df = dfs[0]
        df.columns = [clean_column_name(c) for c in df.columns]

        # 2. Parse EXACT Links (BeautifulSoup)
        # This matches the 'href' hidden in the HTML to the row in the table
        soup = BeautifulSoup(response.text, 'html.parser')
        stock_links = []
        
        # We target the rows in the table body
        table_rows = soup.select("table tbody tr")
        
        for row in table_rows:
            # Find the anchor tag that points to '/company/...'
            link_tag = row.select_one("a[href*='/company/']")
            if link_tag:
                # Constructs: https://www.screener.in/company/INDOTECH/
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
            
            # Feature A: News (First stock only)
            if index == 0:
                first_stock_news = get_stock_news(name)

            # Feature D: REAL Clickable Links
            # We use the scraped link if available, otherwise fallback to search
            if index < len(stock_links) and stock_links[index]:
                link = stock_links[index]
            else:
                # Fallback: Search URL if scraping failed for some reason
                safe_name = urllib.parse.quote(name)
                link = f"https://www.screener.in/search/?query={safe_name}"
            
            report_section += f"🔹 [{name}]({link}) | ₹{price}\n"
            report_section += f"   RSI: {rsi} | QtrPf: {qtr_profit}% | FII: {fii_chg}%\n\n"
            
            raw_data_for_ai += f"{name}: Price {price}, RSI {rsi}, Profit Var {qtr_profit}%, FII Chg {fii_chg}%\n"
            
        report_section += first_stock_news + "\n"
            
        return report_section, raw_data_for_ai

    except Exception as e:
        return f"❌ Error on {url}: {str(e)}\n", ""

if __name__ == "__main__":
    final_message = "📊 **Daily Market Watch**\n\n"
    combined_ai_data = ""
    
    for link in SCREENER_URLS:
        if len(link.strip()) > 5:
            text_output, ai_input = get_screener_data(link)
            final_message += text_output
            final_message += "------------------\n"
            combined_ai_data += ai_input
    
    if combined_ai_data and GEMINI_API_KEY:
        ai_insight = get_ai_analysis(combined_ai_data)
        final_message += ai_insight
    
    send_telegram_message(final_message)
