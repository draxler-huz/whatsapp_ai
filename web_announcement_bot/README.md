# 🚀 WhatsApp AI Announcement Bot

An AI-powered automation dashboard that takes rough notes, meeting reminders, or casual instructions and transforms them into professional, eye-catching WhatsApp announcements with emojis, bold headers, and clear call-to-actions, then automatically broadcasts them to target WhatsApp groups using Playwright browser automation.

Compatible with **Google Gemini API** (Google AI Studio) and **OpenAI**.

---

## ⚡ Quick Start Guide

### 1. Add Your Google API Key
Create a `.env` file in the `web_announcement_bot/` folder (copy `.env.example`) and paste your Google Gemini API key:
```ini
GOOGLE_API_KEY=AIzaSyYourActualGoogleKeyHere
```

> Optional: if you serve the dashboard from a different origin, set
> `CORS_ORIGINS` to a comma-separated list of allowed origins.

### 2. Start the Server
In your terminal, run:
```bash
python backend/main.py
```
*(Or double-click `start.bat`)*

### 3. Open the Dashboard
Navigate to:
👉 **`http://127.0.0.1:8050`**

---

## 📲 How to Use (4 Simple Steps)

1. **Step 1: Open WhatsApp & Scan QR**: Click the button to launch Chrome with WhatsApp Web. Scan the QR code once with your phone.
2. **Step 2: Choose Groups**: Click "Load Groups from WhatsApp" and pick the groups you want to message using checkboxes.
3. **Step 3: Upload / Draft Announcement**: Type notes or upload a `.txt` file, choose your tone style, and click "Generate AI Announcement".
4. **Step 4: Broadcast**: Click "Broadcast Now" and watch the bot send to each selected group automatically!
