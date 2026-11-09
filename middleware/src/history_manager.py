import sqlite3
import json
import os
from datetime import datetime

class HistoryManager:
    """
    Manages chat history using SQLite for robust local storage.
    Provides functionalities to save, retrieve, clear, and export chat logs.
    """
    
    def __init__(self, db_path="chat_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database and create the history table if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            ''')
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[Error] Gagal menginisialisasi database: {e}")

    def save_message(self, role, content):
        """Save a single message to the database."""
        timestamp = datetime.now().isoformat()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO history (timestamp, role, content)
                VALUES (?, ?, ?)
            ''', (timestamp, role, content))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[Error] Gagal menyimpan pesan: {e}")

    def get_history(self, limit=None):
        """Retrieve chat history. Optionally limit the number of recent messages."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if limit:
                cursor.execute('''
                    SELECT role, content FROM history 
                    ORDER BY id DESC LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()
                rows.reverse()
            else:
                cursor.execute('''
                    SELECT role, content FROM history 
                    ORDER BY id ASC
                ''')
                rows = cursor.fetchall()
                
            conn.close()
            return [{'role': row[0], 'content': row[1]} for row in rows]
        except sqlite3.Error as e:
            print(f"[Error] Gagal mengambil riwayat: {e}")
            return []

    def export_to_json(self, filepath="chat_history_export.json"):
        """Export the entire chat history to a JSON file."""
        history = self.get_history()
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return filepath
        except IOError as e:
            print(f"[Error] Gagal mengekspor ke JSON: {e}")
            return None

    def clear_history(self):
        """Clear all messages from the local database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM history')
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[Error] Gagal menghapus riwayat: {e}")