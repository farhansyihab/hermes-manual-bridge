import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Path database - di dalam root project
PROJECT_ROOT = Path("/home/farhan/Proyek/Hermes")
DATA_DIR = PROJECT_ROOT / "middleware" / "data"
DB_PATH = DATA_DIR / "history.db"


def ensure_data_dir():
    """Pastikan direktori data ada"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Dapatkan koneksi SQLite"""
    ensure_data_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager untuk koneksi database"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    """Inisialisasi database dan buat tabel jika belum ada"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                model TEXT,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0
            )
        """)
        # Index untuk query cepat
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON conversations(timestamp DESC)
        """)