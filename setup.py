import sqlite3
import os
from pathlib import Path

# Ensure uploads directory exists
UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

# Initialize database
def setup_database():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
    ''')
    
    # Create documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    ''')
    
    # Create chat history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    ''')
    
    conn.commit()
    print("Database initialized successfully")
    conn.close()

# Test connection to LM Studio
def test_lm_studio_connection():
    """Test connection to LM Studio API"""
    import requests
    try:
        response = requests.post(
            "http://127.0.0.1:1234/v1/chat/completions",
            json={
                "model": "mistral-nemo-instruct-2407",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
        )
        if response.status_code == 200:
            print("LM Studio connection successful")
        else:
            print(f"LM Studio returned status code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"LM Studio connection failed: {e}")
        print("Make sure LM Studio is running and the model is loaded")

if __name__ == "__main__":
    setup_database()
    test_lm_studio_connection()