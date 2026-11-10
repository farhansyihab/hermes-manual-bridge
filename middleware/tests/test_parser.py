"""
Unit tests untuk Modul D: Code Parser
"""
import pytest
from app.parser import extract_code_blocks, detect_language_from_content, enhance_code_blocks


class TestExtractCodeBlocks:
    """Test suite untuk fungsi extract_code_blocks()"""
    
    def test_single_python_block(self):
        """Test deteksi single blok Python"""
        text = """
        Berikut kode Python: