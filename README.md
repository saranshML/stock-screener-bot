This is the final step\! Below is a professional `README.md` file you can add to your repository, followed by a **Step-by-Step Guide** that you can share with anyone (or use yourself) to set this up from scratch.

### **Part 1: The `README.md` File**

Create a new file in your repository named `README.md` and paste this raw code. It serves as the "Front Page" of your project.

```markdown
# 📈 AI-Powered Daily Stock Screener Bot

A fully automated, zero-cost stock market assistant that runs on the cloud. This bot scrapes your private or public screens from [Screener.in](https://www.screener.in), analyzes them using **Google Gemini AI**, and delivers a smart executive summary to your **Telegram** every morning.

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-green?style=for-the-badge&logo=githubactions)
![Gemini AI](https://img.shields.io/badge/AI-Gemini_Pro-orange?style=for-the-badge&logo=google)

## ✨ Features

* **📊 Multi-Screen Tracking:** Monitors multiple Screener.in watchlists simultaneously.
* **🚨 Super-Pick Detector:** Identifies "Confluence" stocks that appear in multiple screens (e.g., a stock that is both "Undervalued" AND "Momentum").
* **🤖 AI Analyst:** Uses Google's **Gemini 2.5 Pro** to review the data, identify red flags, and provide a strict technical verdict.
* **📰 Smart News:** Automatically fetches the latest top headline for the #1 ranked stock.
* **🔗 Deep Integration:** One-click links to stock pages (Screener.in) and automated sector heatmaps.
* **☁️ 100% Free & Cloud-Based:** Runs on GitHub Actions (no server required).

## 🛠️ Tech Stack
* **Core:** Python 3.10
* **Data Fetching:** `requests`, `beautifulsoup4`
* **AI Engine:** `google-generativeai`
* **Automation:** GitHub Actions (Cron Job)
* **Notifications:** Telegram Bot API

## 🚀 Quick Setup

### 1. Fork this Repository
Click the **Fork** button at the top right of this page to create your own copy.

### 2. Set up Secrets
Go to **Settings > Secrets and variables > Actions** and add the following keys:

| Secret Name | Description |
| :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your numeric Chat ID |
| `SCREENER_COOKIE` | Your `sessionid` cookie from Screener.in |
| `SCREENER_URL` | Comma-separated list of your Screen URLs |
| `GEMINI_API_KEY` | Free API key from Google AI Studio |

### 3. Run it!
Go to the **Actions** tab, select **Daily Stock Screener**, and click **Run Workflow**.

---
*Disclaimer: This tool is for educational purposes only. Not financial advice.*
```

-----

### **Part 2: Step-by-Step Guide for New Users**

Here is the detailed manual you can give to a friend (or follow yourself on a new account) to set this up in 10 minutes.

#### **Phase 1: Get the Keys (The "ID Cards")**

**1. Get Telegram Credentials**

  * Open Telegram and search for **@BotFather**.
  * Send `/newbot`, name it, and get your **API Token**.
  * Search for **@userinfobot** and click Start to get your numeric **Chat ID**.

**2. Get Screener Cookie (The "Key" to your screens)**

  * Log in to [Screener.in](https://www.screener.in) on your Desktop (Chrome/Edge).
  * Right-click anywhere on the page \> **Inspect** (or press F12).
  * Go to the **Network** tab.
  * Refresh the page.
  * Click the first request in the list (usually says `dashboard` or the screen name).
  * Scroll down to **Request Headers** \> find `Cookie`.
  * Copy the **entire value** (it looks like `csrftoken=...; sessionid=...`).

**3. Get AI Key (Free)**

  * Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
  * Click **Create API Key**.
  * Copy the key string.

-----

#### **Phase 2: Set Up the Cloud Robot**

**1. Get the Code**

  * Go to the GitHub repository.
  * Click **Fork** (Top Right). This creates a copy in *your* account so you can edit it privately.

**2. Save Your Passwords**

  * In your new repo, go to **Settings** (Top Menu).
  * On the left sidebar, click **Secrets and variables** \> **Actions**.
  * Click **New repository secret** (Green Button).
  * Add these 5 Secrets exactly as written:

| Name | Value to Paste |
| :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Your Bot Token (from Phase 1) |
| `TELEGRAM_CHAT_ID` | Your User ID (from Phase 1) |
| `SCREENER_COOKIE` | The long cookie string (from Phase 1) |
| `GEMINI_API_KEY` | The Google AI Key (from Phase 1) |
| `SCREENER_URL` | Your screen links, separated by commas.<br>*(Example: `https://screener.in/A,https://screener.in/B`)* |

**3. Activate the Automation**

  * Click the **Actions** tab.
  * You will see a warning: *"Workflows aren't being run on this forked repository"*.
  * Click the green button **I understand my workflows, go ahead and enable them**.

**4. Test Run**

  * Click **Daily Stock Screener** on the left sidebar.
  * Click **Run workflow** \> **Run workflow**.
  * Wait 30 seconds. You should get a message on Telegram\! 📱

-----

### **Phase 3: Customization (Optional)**

**How to change the time?**

1.  Go to `.github/workflows/daily_screen.yml`.
2.  Edit the line `- cron: '30 3 * * *'`.
3.  Use a [Cron Converter](https://crontab.guru/) to find your time. (Note: GitHub uses UTC time, so subtract 5 hours 30 mins from IST).

**How to add more screens?**

1.  Go to **Settings \> Secrets**.
2.  Edit `SCREENER_URL`.
3.  Add the new link after a comma: `...,https://www.screener.in/screens/NEW/`

### **Troubleshooting**

  * **Error 403/404:** Your cookie expired. Log out and log back in to Screener, get a fresh cookie, and update the Secret.
  * **"AI Error":** Your Google API key might be invalid, or you hit a limit. Check Google AI Studio.
  * **No Message:** Check the "Actions" tab logs. If it says "Process completed with exit code 1", click into it to see the error.
