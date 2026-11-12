"""
Menjamin root middleware/ masuk sys.path sehingga 'from app.parser import ...'
selalu resolves saat pytest dijalankan dari direktori mana pun.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))