"""
Intelligent Candidate Shortlisting Agent - Configuration Module

Central configuration for paths, defaults, and environment management.
"""

import os
from pathlib import Path

# ─── Project Paths ───────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "shortlisting.db"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
SAMPLE_DATA_DIR.mkdir(exist_ok=True)

# ─── LLM Defaults ────────────────────────────────────────────────────────────

DEFAULT_LLM_PROVIDER = "gemini" # Options: "gemini", "openai", "ollama"

LLM_MODELS = {
  "gemini": [
    "gemini/gemini-3.8-flash",
    "gemini/gemini-3.7-flash",
    "gemini/gemini-3.6-flash",
    "gemini/gemini-2.5-flash",
  ],
  "openai": [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
  ],
  "ollama": [
    "ollama/llama3.2",
    "ollama/llama3.1",
    "ollama/mistral",
    "ollama/gemma2",
  ],
  "groq": [
    "groq/openai/gpt-oss-120b",
    "groq/openai/gpt-oss-20b",
    "groq/groq/compound",
    "groq/qwen/qwen3.8-27b",
  ]
}

DEFAULT_MODELS = {
  "gemini": "gemini/gemini-3.8-flash",
  "openai": "gpt-4o-mini",
  "ollama": "ollama/llama3.2",
  "groq": "groq/openai/gpt-oss-120b",
}

DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 4096

# ─── SMTP Defaults ───────────────────────────────────────────────────────────

DEFAULT_SMTP_SERVER = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587

# ─── Scoring Configuration ───────────────────────────────────────────────────

SCORE_THRESHOLDS = {
  "excellent": 80,  # Green badge
  "good": 60,    # Yellow badge
  "poor": 0,     # Red badge
}

SHORTLIST_THRESHOLD = 70 # Minimum score to auto-shortlist

# ─── Supported File Types ────────────────────────────────────────────────────

SUPPORTED_RESUME_EXTENSIONS = [".pdf", ".docx"]

# ─── App Metadata ────────────────────────────────────────────────────────────

APP_TITLE = "Intelligent Candidate Shortlisting Agent"
APP_VERSION = "1.0.0"
GRADIO_SERVER_PORT = 7860
