# ⚡ ScoutAI — Autonomous Job Hunting & Application Radar

ScoutAI is an autonomous AI agent that discovers, scores, and applies to job openings across company career portals and ATS platforms (LinkedIn, Greenhouse, Lever, Ashby, Workday, etc.).

---

## ✨ Features

- **🎯 AI Candidate Profile & Tailored Scoring**: Upload your resume (PDF/TXT) or paste profile text for LLM extraction and match compatibility percentage scoring.
- **⚡ Auto-Apply (Playwright Automation)**:
  - **🛡️ Assisted Mode (Review before submit)**: Fills in application forms, answers screening questions, attaches resume, and stages at final review in your browser.
  - **⚡ Full Auto Mode**: Direct automatic submission for top-matching positions.
- **📧 Automated Email Digest**: Dispatches top 5 matching jobs or auto-apply execution reports via Gmail SMTP.
- **🛡️ Human-in-the-Loop Verification**: Automatically handles login gates and Cloudflare/CAPTCHA challenges with live browser continuation.
- **🌐 Modern Dark-Themed Web UI**: Interactive dashboard with real-time SSE progress streaming and one-click auto-apply buttons.

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/Sampurna1524/ScoutAI.git
cd ScoutAI
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment
Copy `.env.example` to `backend/.env` and add your API keys:
```bash
cp .env.example backend/.env
```

Configure your credentials in `backend/.env`:
- `GEMINI_API_KEY`: Google Gemini API key
- `GROQ_API_KEY`: Groq API key (optional fallback)
- `SMTP_USER` & `SMTP_PASS`: Gmail address and Google App Password for email notifications.

### 3. Run ScoutAI
```bash
# Windows 1-click launcher:
start_scoutai.bat

# Or run via Python:
python run.py
```
Open **[http://127.0.0.1:8000/ui](http://127.0.0.1:8000/ui)** in your browser.

---

## 🧪 Running Tests

```bash
python backend/test_suite.py
```
