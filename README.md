# 🎯 Intelligent Candidate Shortlisting Agent

An AI-powered multi-agent recruitment tool that automates resume screening using CrewAI, Gradio, and flexible LLM backends.

## ✨ Features

- **📄 Resume Parsing** — Upload PDF/DOCX resumes, auto-extract text
- **🔍 JD Analysis** — AI-powered job description parsing into structured requirements
- **🤖 Multi-Agent Pipeline** — 5 specialized CrewAI agents working sequentially:
  1. Resume Parser Agent
  2. JD Analyzer Agent
  3. Matching & Scoring Agent
  4. Skill Gap Analyst Agent
  5. Report Writer Agent
- **🏆 Candidate Ranking** — Score-based ranking (0-100) with detailed reasoning
- **📊 Analytics Dashboard** — Plotly charts: score distribution, skill coverage, top candidates
- **📧 Email Notifications** — Customizable email templates with SMTP support
- **⚙️ Flexible LLM** — Supports Google Gemini (free), OpenAI, or Ollama (local)
- **💾 Persistent Storage** — SQLite database for jobs, candidates, and results

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The app launches at **http://localhost:7860**

### 3. Configure Settings

1. Go to the **⚙️ Settings** tab
2. Select your LLM provider (Gemini recommended for free tier)
3. Enter your API key
4. Click **Save** and **Test Connection**

### 4. Use the Pipeline

1. **📄 Job Description** tab → Paste a JD or load the sample → Click "Analyze JD"
2. **📁 Resume Upload** tab → Upload resumes → Click "Parse Resumes" → Click "Run Shortlisting"
3. **🏆 Rankings** tab → View ranked candidates → Shortlist top N
4. **📊 Dashboard** tab → View analytics charts
5. **📧 Email** tab → Send notifications to shortlisted candidates

## 🔑 Getting API Keys

| Provider | Free Tier | How to Get |
|:---|:---|:---|
| **Google Gemini** | ✅ 15 RPM, 1M tokens/day | [Google AI Studio](https://aistudio.google.com/apikey) |
| **OpenAI** | ❌ Paid | [platform.openai.com](https://platform.openai.com/api-keys) |
| **Ollama** | ✅ Fully local | [ollama.com](https://ollama.com) → `ollama pull llama3.2` |

## 🛠️ Tech Stack

- **Framework**: CrewAI (Multi-Agent AI)
- **UI**: Gradio
- **Database**: SQLite
- **Charts**: Plotly
- **Resume Parsing**: PyMuPDF + python-docx
- **Language**: Python 3.10+

## 📁 Project Structure

```
├── app.py                     # Main entry point
├── config.py                  # Configuration
├── requirements.txt           # Dependencies
├── agents/                    # CrewAI agent definitions
│   ├── resume_parser.py
│   ├── jd_analyzer.py
│   ├── matcher.py
│   ├── skill_gap.py
│   └── report_writer.py
├── crew/
│   └── shortlisting_crew.py  # Crew orchestration
├── services/
│   ├── database.py            # SQLite operations
│   ├── resume_service.py      # PDF/DOCX parsing
│   ├── llm_router.py          # LLM backend routing
│   └── email_service.py       # SMTP email service
├── ui/
│   ├── theme.py               # Custom Gradio theme
│   └── tabs/                  # 6 UI tabs
│       ├── job_input.py
│       ├── resume_upload.py
│       ├── rankings.py
│       ├── dashboard.py
│       ├── email_tab.py
│       └── settings.py
├── data/                      # Runtime data (auto-created)
└── sample_data/               # Sample JD for testing
```

## 📝 License

Academic Project — Flexi CA3
