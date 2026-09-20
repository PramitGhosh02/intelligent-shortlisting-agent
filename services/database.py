"""
SQLite database service using Python's built-in sqlite3 module.
"""
import sqlite3
import json
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

import config

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db() -> None:
    """Creates the database and all tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                requirements_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER REFERENCES jobs(id),
                name TEXT,
                email TEXT,
                phone TEXT,
                resume_path TEXT,
                raw_text TEXT,
                parsed_data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER REFERENCES candidates(id),
                job_id INTEGER REFERENCES jobs(id),
                match_score REAL,
                ranking INTEGER,
                reasoning TEXT,
                skill_gaps_json TEXT,
                strengths_json TEXT,
                shortlisted BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully.")

def save_job(title: str, description: str, requirements_json: str) -> int:
    """Saves a new job to the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (title, description, requirements_json) VALUES (?, ?, ?)",
            (title, description, requirements_json)
        )
        conn.commit()
        return cursor.lastrowid

def get_job(job_id: int) -> dict:
    """Retrieves a job by its ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}

def get_latest_job() -> dict:
    """Retrieves the most recently created job."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else {}

def save_candidate(job_id: int, name: str, email: str, phone: str, resume_path: str, raw_text: str, parsed_data_json: str) -> int:
    """Saves a new candidate to the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO candidates (job_id, name, email, phone, resume_path, raw_text, parsed_data_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, name, email, phone, resume_path, raw_text, parsed_data_json)
        )
        conn.commit()
        return cursor.lastrowid

def get_candidates(job_id: int) -> List[Dict[str, Any]]:
    """Retrieves all candidates for a specific job."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE job_id = ?", (job_id,))
        return [dict(row) for row in cursor.fetchall()]

def save_result(candidate_id: int, job_id: int, match_score: float, ranking: int, reasoning: str, skill_gaps_json: str, strengths_json: str, shortlisted: bool) -> int:
    """Saves a result to the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO results (candidate_id, job_id, match_score, ranking, reasoning, skill_gaps_json, strengths_json, shortlisted) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (candidate_id, job_id, match_score, ranking, reasoning, skill_gaps_json, strengths_json, shortlisted)
        )
        conn.commit()
        return cursor.lastrowid

def get_results(job_id: int) -> List[Dict[str, Any]]:
    """Retrieves all results for a specific job, including candidate info."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, c.name as candidate_name, c.email as candidate_email 
            FROM results r
            JOIN candidates c ON r.candidate_id = c.id
            WHERE r.job_id = ?
            ORDER BY r.ranking ASC
        ''', (job_id,))
        return [dict(row) for row in cursor.fetchall()]

def update_candidate_email(candidate_id: int, email: str) -> None:
    """Updates the email address for a candidate."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE candidates SET email = ? WHERE id = ?", (email, candidate_id))
        conn.commit()

def update_shortlist_status(result_id: int, shortlisted: bool) -> None:
    """Updates the shortlist status for a result."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE results SET shortlisted = ? WHERE id = ?",
            (1 if shortlisted else 0, result_id)
        )
        conn.commit()

def get_setting(key: str) -> Optional[str]:
    """Retrieves a setting by key."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else None

def save_setting(key: str, value: str) -> None:
    """Saves or updates a setting."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?",
            (key, value, value)
        )
        conn.commit()

def get_all_settings() -> Dict[str, str]:
    """Retrieves all settings."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {row['key']: row['value'] for row in cursor.fetchall()}
