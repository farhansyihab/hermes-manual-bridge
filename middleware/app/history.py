import json
from typing import List, Dict, Optional
from .database import get_db, init_db


class HistoryService:
    """Service untuk mengelola riwayat percakapan"""
    
    def __init__(self):
        init_db()
    
    def save_conversation(
        self, 
        prompt: str, 
        response: str,
        model: str = "deepseek-manual",
        status: str = "completed"
    ) -> int:
        """
        Simpan percakapan ke database
        Returns: ID dari record yang baru dibuat
        """
        with get_db() as conn:
            cursor = conn.execute(
                """
                INSERT INTO conversations (prompt, response, model, status)
                VALUES (?, ?, ?, ?)
                """,
                (prompt, response, model, status)
            )
            return cursor.lastrowid
    
    def get_recent(self, limit: int = 50) -> List[Dict]:
        """Ambil percakapan terbaru"""
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT id, timestamp, prompt, response, status, model
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_id(self, conversation_id: int) -> Optional[Dict]:
        """Ambil percakapan berdasarkan ID"""
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT id, timestamp, prompt, response, status, model
                FROM conversations
                WHERE id = ?
                """,
                (conversation_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all(self) -> List[Dict]:
        """Ambil semua percakapan"""
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT id, timestamp, prompt, response, status, model
                FROM conversations
                ORDER BY timestamp DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_by_id(self, conversation_id: int) -> bool:
        """Hapus percakapan berdasarkan ID"""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            return cursor.rowcount > 0
    
    def clear_all(self) -> int:
        """Hapus semua percakapan. Returns jumlah record yang dihapus"""
        with get_db() as conn:
            cursor = conn.execute("DELETE FROM conversations")
            return cursor.rowcount
    
    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """
        Export semua percakapan ke JSON
        Jika filepath diberikan, simpan ke file
        Returns: JSON string
        """
        conversations = self.get_all()
        json_str = json.dumps(conversations, indent=2, ensure_ascii=False)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def get_stats(self) -> Dict:
        """Dapatkan statistik percakapan"""
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    MIN(timestamp) as first_conversation,
                    MAX(timestamp) as last_conversation
                FROM conversations
            """)
            stats = dict(cursor.fetchone())
            return stats


# Singleton instance
history_service = HistoryService()