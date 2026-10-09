# 📅 Deadline Tracker AI

> **An intelligent vision-based academic assistant that turns course syllabi, timetables, and assignment sheets into organized schedules and delivers email reminder digests right to your inbox.**

---

## 🌟 Overview

**Deadline Tracker AI** is an AI-powered productivity app built for students and lifelong learners. Instead of manually typing out dozens of assignment deadlines, exam dates, and grading weights from complex PDF or printed syllabi, you simply take a photo or upload an image.

Powered by **Google Gemini Vision**, the app reads and understands the document, extracts a chronological list of deliverables, highlights high-priority milestones, and lets you ask questions. With the integrated **Gmail Action Tool**, you can dispatch a personalized, structured deadline digest directly to your email address with one click.

---

## 🚀 Key Features

- **📸 Multimodal Vision Scanning:** Upload or snap a photo of any syllabus, exam timetable, or assignment handout (PNG, JPG, WEBP).
- **🤖 Intelligent Extraction:** Accurately extracts dates, days, course names, deliverables, submission portals, weights, and priorities.
- **🛡️ Graceful Degradation:** If an uploaded image is blurry or doesn't contain deadlines, the AI politely explains what is missing and guides you on what to submit.
- **💬 Contextual Chat & Q&A:** Ask follow-up questions about exam policies, assignment criteria, or request a study timeline.
- **📧 One-Click Email Digest:** Uses Python's built-in `smtplib` over SSL to send an executive reminder directly to your inbox via Gmail SMTP.
- **🎯 Frictionless Onboarding:** Quick onboarding flow to save your name and recipient email address, easily editable in the sidebar.

---

## 🏗️ Project Architecture

```
nxtwave project/
├── .streamlit/
│   ├── secrets.toml.example     # Template for API keys & email credentials
│   └── secrets.toml             # Local secrets (ignored by Git)
├── app.py                       # Main Streamlit application & UI
├── prompts.py                   # Specialized system prompts & digest templates
├── requirements.txt             # Project dependencies
├── .gitignore                   # Excludes secrets, venv, and cache
└── README.md                    # Project documentation
```

---

## 🛠️ Tech Stack

- **Frontend / Framework:** [Streamlit](https://streamlit.io/)
- **Vision & LLM:** [Google Gemini 1.5 Flash](https://aistudio.google.com/) via `google-generativeai`
- **Action Tool:** Gmail SMTP (`smtplib` + `email.mime`)
- **Image Processing:** `Pillow` (PIL)

---

## ⚙️ Getting Started Locally

### 1. Clone the Repository
```bash
git clone <your-github-repo-url>
cd <repo-folder>
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Secrets
Create a `.streamlit/secrets.toml` file inside the `.streamlit/` folder by copying the example template:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Open `.streamlit/secrets.toml` and fill in your keys:
```toml
# 1. Google Gemini API Key (from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY = "your_actual_gemini_api_key"

# 2. Gmail SMTP Credentials
GMAIL_ADDRESS = "your_email@gmail.com"
GMAIL_APP_PASSWORD = "your_16_character_app_password"
```

> 💡 **How to generate a Gmail App Password:**
> 1. Visit your [Google Account Security](https://myaccount.google.com/security) page.
> 2. Ensure **2-Step Verification** is turned **ON**.
> 3. Go to [App Passwords](https://myaccount.google.com/apppasswords).
> 4. Create an App Password for App: `Mail` and Device: `Other (Streamlit App)`.
> 5. Copy the generated 16-character code into `GMAIL_APP_PASSWORD`.

### 5. Run the Application
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 🌐 Deploying to Streamlit Community Cloud

1. Push your code to a public or private GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Deadline Tracker AI"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```
2. Navigate to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3. Click **"New app"**, select your repository and branch (`main`), with main file path `app.py`.
4. Under **Advanced Settings**, paste the contents of your `.streamlit/secrets.toml` into the **Secrets** field.
5. Click **"Deploy"**!

---

## 📝 License
This project is open-source and created as part of the AI Vision Chatbot Workshop.
