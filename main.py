import requests
import pandas as pd
import os
import google.generativeai as genai
import feedparser
import urllib.parse

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
    """
    Fetches the latest news headline from Google News RSS for the top stock.
    """
    try:
        encoded_name = urllib.parse.quote(stock_name)
        # Search for 'StockName share price india news'
        rss_url = f"https://news.google.com/rss/search?q={encoded_name}+share+price+india+news&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(rss_url)
        
        if feed.entries:
            title = feed.entries[0].title
            link = feed.entries[0].link
            # Clean up title (remove publisher name often found at end)
            title = title.split(' - ')[0]
            return f"\n📰 **News on {stock_name}:**\n[{title}]({link})"
        return ""
    except:
        return ""

def get_ai_analysis(stock_data_text):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
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
        
        dfs = pd.read_html(response.text)
        if not dfs:
            return "❌ No data table found.", ""
        
        df = dfs[0]
        df.columns = [clean_column_name(c) for c in df.columns]
        
        screen_name = url.strip().split('/')[-2].replace('-', ' ').title()
        report_section = f"📂 *{screen_name}*\n"
        
        raw_data_for_ai = f"Screen: {screen_name}\n"
        first_stock_news = ""

        for index, row in df.head(10).iterrows():
            name = row.get('Name', 'N/A')
            price = row.get('CMP Rs.', row.get('Current Price', 'N/A'))
            rsi = row.get('RSI', 'N/A')
            qtr_profit = row.get('Qtr Profit Var %', 'N/A')
            fii_chg = row.get('Chg in FII Hold %', 'N/A')
            
            # --- FEATURE A: NEWS FLASH (Only for the very first stock) ---
            if index == 0:
                first_stock_news = get_stock_news(name)

            # --- FEATURE D: CLICKABLE LINKS ---
            # Create a Screener link: https://www.screener.in/company/SYMBOL/
            # We guess the symbol is the first word of the name (Works 95% of the time)
            safe_symbol = name.split()[0] 
            link = f"https://www.screener.in/company/{safe_symbol}/"
            
            # Markdown format: [Text](URL)
            report_section += f"🔹 [{name}]({link}) | ₹{price}\n"
            report_section += f"   RSI: {rsi} | QtrPf: {qtr_profit}% | FII: {fii_chg}%\n\n"
            
            # Data for AI
            raw_data_for_ai += f"{name}: Price {price}, RSI {rsi}, Profit Var {qtr_profit}%, FII Chg {fii_chg}%\n"
            
        # Append the news at the very end of this screen's section
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
    
    # Run AI Analysis if data exists
    if combined_ai_data and GEMINI_API_KEY:
        ai_insight = get_ai_analysis(combined_ai_data)
        final_message += ai_insight
    
    send_telegram_message(final_message)
