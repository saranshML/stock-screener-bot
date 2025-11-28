import requests
import pandas as pd
import os
import google.generativeai as genai

# --- CONFIGURATION ---
BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
SCREENER_COOKIE = os.environ['SCREENER_COOKIE']
SCREENER_URLS = os.environ['SCREENER_URL'].split(',')
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

# --- SETUP AI ---
genai.configure(api_key=GEMINI_API_KEY)

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

def get_ai_analysis(stock_data_text):
    """
    Sends the raw stock list to Gemini and asks for a summary.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (
            "You are a strict financial analyst. Here is a list of stocks from a screener:\n\n"
            f"{stock_data_text}\n\n"
            "Task: Briefly analyze the top 2 most promising stocks based on the data provided (RSI, Profit Growth, FII). "
            "Highlight any red flags (like high RSI > 70 or negative profit). "
            "Keep the response under 100 words. Use emojis."
        )
        response = model.generate_content(prompt)
        return f"\n🤖 **AI Analyst Insights:**\n{response.text}"
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
        
        # String to hold data for the AI to read
        raw_data_for_ai = f"Screen: {screen_name}\n"

        for index, row in df.head(10).iterrows():
            name = row.get('Name', 'N/A')
            price = row.get('CMP Rs.', row.get('Current Price', 'N/A'))
            rsi = row.get('RSI', 'N/A')
            qtr_profit = row.get('Qtr Profit Var %', 'N/A')
            fii_chg = row.get('Chg in FII Hold %', 'N/A')
            
            # Format for Telegram
            report_section += f"🔹 *{name}* | ₹{price}\n"
            report_section += f"   RSI: {rsi} | QtrPf: {qtr_profit}% | FII: {fii_chg}%\n\n"
            
            # Format for AI (Raw text)
            raw_data_for_ai += f"{name}: Price {price}, RSI {rsi}, Profit Var {qtr_profit}%, FII Chg {fii_chg}%\n"
            
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
    
    # --- Trigger AI Analysis ---
    if combined_ai_data:
        ai_insight = get_ai_analysis(combined_ai_data)
        final_message += ai_insight
    
    send_telegram_message(final_message)
