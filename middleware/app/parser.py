"""
Modul D: Code Parser & Path Extractor (Fase 3)
Fungsi untuk mendeteksi dan mengekstrak blok kode dari respons DeepSeek.
"""
import re
from typing import List, Dict


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    Deteksi semua blok kode dalam respons DeepSeek.
    
    Args:
        text: Teks respons dari DeepSeek yang mungkin mengandung blok kode
        
    Returns:
        List of dictionaries dengan struktur:
        [{"language": "python", "content": "..."}, ...]
        
    Contoh:
        >>> text = '''
        ... Berikut contoh kode: