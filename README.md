# 🚀 WhatsApp AI Suite

A dual-ecosystem project combining an **AI Web Announcement & Broadcast Bot** and an **Android Executive Group Digest & Summarizer App**.

---

## 📂 Repository Architecture

```
whatsapp_ai/
├── .github/workflows/
│   └── build.yml               # Automated Cloud CI/CD to build Android APK on GitHub
├── mobile_summarizer_app/      # Android App (WA Summarizer Pro Executive Edition)
│   ├── App.js                  # Full React Native app with Notification Listener
│   ├── index.js                # Expo entry point (registers the root component)
│   ├── preview_3d.html         # Interactive 3D WebGL simulator & testbench
│   ├── build_apk.bat           # 1-Click local/cloud APK compiler
│   ├── app.json                # Android system permissions & config
│   ├── assets/                 # App icon + adaptive icon
│   └── package.json            # Node.js dependencies
└── web_announcement_bot/       # FastAPI + Google Gemini Announcement Broadcaster
    ├── backend/
    │   ├── main.py             # FastAPI backend API
    │   ├── ai_agent.py         # Google Gemini AI formatting engine
    │   └── whatsapp_bot.py     # Playwright automation driver
    ├── frontend/
    │   └── index.html          # Web dashboard
    └── start.bat               # 1-Click desktop launcher
```

---

## 📱 1. Mobile App: WA Summarizer Pro (Android)

An on-device WhatsApp group notification aggregator and intelligence engine:
- **Zero-Ban Risk**: Hooks directly into Android's native `NotificationListenerService` rather than WhatsApp web clients or unauthorized APIs.
- **Sheng & Swahili Context Lexicon**: Static prompt caching recognizing Kenyan urban slang (e.g. *form ni gani*, *wasee*, *rada*, *pesa/ganji*) and filtering out conversational noise (*sasa, poa, mambo*).
- **Deterministic Structured JSON**: Zero filler tokens with strict schema parsing.
- **Sliding Window Batching**: Gathers updates over 15m, 1h, or 4h windows before calling Gemini Flash.
- **Floating PIP Mode & Direct WhatsApp Deep-Linking**: Jump straight from any summary card into the relevant WhatsApp group (`whatsapp://app`).
- **Zero-Cloud Memory Mode**: Purges raw text logs from memory immediately upon compiling the digest.

### 🔨 Getting the Android APK:
- **Automated GitHub Actions**: Go to the **Actions** tab in this repository, click **Build Android APK**, and download the compiled APK under **Artifacts**!

---

## 🌐 2. Web App: WhatsApp AI Announcement Bot

A local automation dashboard that takes rough meeting notes or casual instructions and transforms them into professional announcements before broadcasting to target WhatsApp groups via Playwright:
- Fast AI formatting powered by **Google Gemini API** (secure header auth).
- Group sidebar scraper & checkbox recipient selector.
- Pre-flight confirmation modal before dispatch.
- Retry button for partially failed broadcasts.

### 🏃‍♂️ Running the Web Bot Locally:
```bash
cd web_announcement_bot
# Configure your Gemini API key in .env
python backend/main.py
# Or double-click start.bat
```
Visit `http://127.0.0.1:8050` in your browser.
