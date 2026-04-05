import sqlite3
import os
from flask_bcrypt import Bcrypt
from contextlib import contextmanager

bcrypt = Bcrypt()

DB_NAME = "study_assistant.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        # Create Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            reset_token TEXT,
            reset_token_expiry DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Study Sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            source_text TEXT,
            summary TEXT,
            quiz TEXT,
            flashcards TEXT,
            plan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        conn.commit()

def add_user(username, email, password):
    hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
    try:
        with get_db() as conn:
            conn.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                         (username, email, hash_password))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username, password):
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and bcrypt.check_password_hash(user['password_hash'], password):
            return dict(user)
    return None

def get_user_by_id(user_id):
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return dict(user) if user else None

def get_user_by_email(email):
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        return dict(user) if user else None

def save_study_session(user_id, title, source_text, summary, quiz, flashcards, plan):
    with get_db() as conn:
        conn.execute('''
        INSERT INTO study_sessions (user_id, title, source_text, summary, quiz, flashcards, plan)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, title, source_text, summary, quiz, flashcards, plan))
        conn.commit()

def get_user_history(user_id):
    with get_db() as conn:
        history = conn.execute('SELECT * FROM study_sessions WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
        return [dict(row) for row in history]

def get_session_by_id(session_id, user_id):
    with get_db() as conn:
        session = conn.execute('SELECT * FROM study_sessions WHERE id = ? AND user_id = ?', (session_id, user_id)).fetchone()
        return dict(session) if session else None

def update_user_reset_token(email, token, expiry):
    with get_db() as conn:
        conn.execute('UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE email = ?',
                     (token, expiry, email))
        conn.commit()

def verify_reset_token(token):
    with get_db() as conn:
        # Use CURRENT_TIMESTAMP or datetime.now()
        # SQLite CURRENT_TIMESTAMP is UTC
        user = conn.execute('SELECT * FROM users WHERE reset_token = ? AND reset_token_expiry > CURRENT_TIMESTAMP', (token,)).fetchone()
        return dict(user) if user else None

def update_password(user_id, new_password):
    hash_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    with get_db() as conn:
        conn.execute('UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?',
                     (hash_password, user_id))
        conn.commit()
