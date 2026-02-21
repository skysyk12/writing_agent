import sqlite3
import json
from datetime import datetime

DB_NAME = "ielts_coach.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create essays table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS essays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_type TEXT NOT NULL,
        topic TEXT NOT NULL,
        user_content TEXT NOT NULL,
        ai_analysis TEXT,  -- JSON string
        created_at TEXT,
        status TEXT DEFAULT 'active'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kaoyan_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_type TEXT NOT NULL,
        paper_type TEXT NOT NULL,
        topic TEXT NOT NULL,
        user_content TEXT NOT NULL,
        total_score REAL,
        language_score REAL,
        structure_score REAL,
        logic_score REAL,
        ai_analysis TEXT,
        created_at TEXT,
        status TEXT DEFAULT 'active'
    )
    ''')
    
    conn.commit()
    conn.close()
