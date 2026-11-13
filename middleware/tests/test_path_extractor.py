"""
Unit test untuk Modul D: Path Extractor (Fase 3)
==================================================
Menguji fungsi-fungsi di path_extractor.py:
- extract_file_path_from_prompt()   : ekstrak path dengan hierarki 3 prioritas
- detect_path_source()              : indikator sumber path untuk UI
- validate_path()                   : validasi keamanan path
- extract_and_validate_path()       : kombinasi ekstraksi + validasi + whitelist

CATATAN PENTING (perbaikan ValueError: too many values to unpack):
Sejak Fase 3 (Keamanan & Fallback), extract_and_validate_path() mengembalikan
EMPAT nilai, bukan tiga:
    (path, source, validation_error, warnings)
Kontrak ini dipakai oleh app/routers/approval.py dan tests/test_whitelist.py,
sehingga TIDAK boleh diubah. Test di file ini disesuaikan dengan kontrak baru.

Catatan lain:
- Konstanta BT dan FENCE didefinisikan secara lokal untuk menghindari
  ImportError jika modul utama belum mengekspornya.
- Dijalankan dengan: pytest tests/test_path_extractor.py -v
"""

import pytest

# ============================================================
# KONSTANTA LOKAL (untuk menghindari ImportError)
# ============================================================
BT = chr(96)
FENCE = BT * 3

try:
    from app.path_extractor import (
        extract_file_path_from_prompt,
        detect_path_source,
        validate_path,
        extract_and_validate_path,
    )
except ImportError as e:
    pytest.fail(
        f"Gagal mengimpor dari app.path_extractor: {e}. "
        "Pastikan file middleware/app/path_extractor.py sudah dibuat dan berisi fungsi-fungsi yang diperlukan."
    )


# ============================================================
# FIXTURE: Helper untuk membangun prompt dengan backtick
# ============================================================
@pytest.fixture
def bt():
    """Single backtick character."""
    return BT


# ============================================================
# TEST SUITE 1: extract_file_path_from_prompt()
# ============================================================
class TestExtractFilePathFromPrompt:
    """Test suite untuk fungsi utama: extract_file_path_from_prompt()"""

    def test_explicit_format_simple(self):
        prompt = "[FILE: hello.py] Buatkan file yang mencetak Halo"
        assert extract_file_path_from_prompt(prompt) == "hello.py"

    def test_explicit_format_with_directory(self):
        prompt = "[FILE: src/utils/helpers.py] Buatkan modul helper"
        assert extract_file_path_from_prompt(prompt) == "src/utils/helpers.py"

    def test_explicit_format_case_insensitive(self):
        assert extract_file_path_from_prompt("[file: main.py] buat") == "main.py"
        assert extract_file_path_from_prompt("[File: main.py] buat") == "main.py"

    def test_explicit_format_with_backtick_inside(self, bt):
        prompt = f"[FILE: {bt}app.js{bt}] Buatkan file"
        assert extract_file_path_from_prompt(prompt) == "app.js"

    def test_nl_keyword_file(self):
        prompt = "Buatkan file hello.py yang mencetak Halo"
        assert extract_file_path_from_prompt(prompt) == "hello.py"

    def test_nl_keyword_berkas(self):
        prompt = "Buatkan berkas config.yaml untuk database"
        assert extract_file_path_from_prompt(prompt) == "config.yaml"

    def test_nl_keyword_simpan_ke(self):
        prompt = "Simpan ke src/app.py ya"
        assert extract_file_path_from_prompt(prompt) == "src/app.py"

    def test_nl_backtick_quoted_filename(self, bt):
        prompt = f"Buatkan file {bt}app.js{bt} untuk backend Express"
        assert extract_file_path_from_prompt(prompt) == "app.js"

    def test_nl_standalone_filename_py(self):
        prompt = "Tolong buatkan main.py untuk aplikasi"
        assert extract_file_path_from_prompt(prompt) == "main.py"

    def test_fallback_manual_ambiguous(self):
        prompt = "Tolong buatkan script untuk backup database"
        assert extract_file_path_from_prompt(prompt) is None

    def test_empty_prompt(self):
        assert extract_file_path_from_prompt("") is None

    def test_none_prompt(self):
        assert extract_file_path_from_prompt(None) is None

    def test_priority_explicit_over_nl(self):
        prompt = "[FILE: correct.py] Buatkan file wrong.py"
        assert extract_file_path_from_prompt(prompt) == "correct.py"


# ============================================================
# TEST SUITE 2: detect_path_source()
# ============================================================
class TestDetectPathSource:
    """Test suite untuk indikator sumber path di UI."""

    def test_source_explicit(self):
        prompt = "[FILE: hello.py] Buatkan file"
        assert detect_path_source(prompt) == "explicit"

    def test_source_nl_file_keyword(self):
        prompt = "Buatkan file hello.py"
        assert detect_path_source(prompt) == "natural_language"

    def test_source_manual_fallback(self):
        prompt = "Tolong buatkan script backup"
        assert detect_path_source(prompt) == "manual"

    def test_source_manual_empty(self):
        assert detect_path_source("") == "manual"


# ============================================================
# TEST SUITE 3: validate_path()
# ============================================================
class TestValidatePath:
    """Test suite untuk validasi keamanan path."""

    def test_valid_simple_filename(self):
        is_valid, error = validate_path("hello.py")
        assert is_valid is True
        assert error == ""

    def test_valid_path_with_directory(self):
        is_valid, error = validate_path("src/utils/helpers.py")
        assert is_valid is True
        assert error == ""

    def test_invalid_absolute_path_unix(self):
        is_valid, error = validate_path("/etc/passwd")
        assert is_valid is False
        assert "absolut" in error.lower()

    def test_invalid_path_traversal_simple(self):
        is_valid, error = validate_path("../secret.txt")
        assert is_valid is False
        assert "traversal" in error.lower()

    def test_invalid_suspicious_env(self):
        is_valid, error = validate_path(".env")
        assert is_valid is False
        assert "mencurigakan" in error.lower()

    def test_invalid_no_extension(self):
        is_valid, error = validate_path("hello")
        assert is_valid is False
        assert "ekstensi" in error.lower()

    def test_invalid_empty_path(self):
        is_valid, error = validate_path("")
        assert is_valid is False


# ============================================================
# TEST SUITE 4: extract_and_validate_path()
# Kontrak Fase 3: return 4-tuple (path, source, error, warnings)
# ============================================================
class TestExtractAndValidatePath:
    """Test suite untuk fungsi kombinasi ekstraksi + validasi + whitelist."""

    def test_returns_four_values(self):
        """Pastikan kontrak return tetap 4 nilai (dipakai approval.py)."""
        result = extract_and_validate_path("[FILE: hello.py] Buat")
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_combined_valid_explicit(self):
        path, source, error, warnings = extract_and_validate_path("[FILE: hello.py] Buat")
        assert path == "hello.py"
        assert source == "explicit"
        assert error == ""
        assert isinstance(warnings, list)
        assert warnings == []

    def test_combined_invalid_absolute(self):
        path, source, error, warnings = extract_and_validate_path("[FILE: /etc/passwd] Baca")
        assert path is None
        assert source == "explicit"
        assert "absolut" in error.lower()
        # Path sudah ditolak di validasi dasar, tidak lanjut ke cek whitelist
        assert warnings == []

    def test_combined_fallback_manual(self):
        path, source, error, warnings = extract_and_validate_path("Buatkan script backup")
        assert path is None
        assert source == "manual"
        assert error == ""
        assert warnings == []

    def test_combined_valid_subdirectory(self):
        path, source, error, warnings = extract_and_validate_path(
            "[FILE: src/utils/helpers.py] Buatkan modul helper"
        )
        assert path == "src/utils/helpers.py"
        assert source == "explicit"
        assert error == ""
        assert warnings == []


# ============================================================
# PARAMETRIZED TESTS
# ============================================================
@pytest.mark.parametrize(
    "prompt,expected_path,expected_source",
    [
        ("[FILE: hello.py] Buat", "hello.py", "explicit"),
        ("Buatkan file hello.py", "hello.py", "natural_language"),
        ("Buatkan berkas config.yaml", "config.yaml", "natural_language"),
        ("Simpan ke src/app.py", "src/app.py", "natural_language"),
        ("Buatkan script backup", None, "manual"),
        ("", None, "manual"),
    ],
)
def test_parametrized_extraction(prompt, expected_path, expected_source):
    path = extract_file_path_from_prompt(prompt)
    source = detect_path_source(prompt)
    assert path == expected_path
    assert source == expected_source


@pytest.mark.parametrize(
    "path,should_be_valid",
    [
        ("hello.py", True),
        ("src/utils/helpers.py", True),
        ("/etc/passwd", False),
        ("../secret.txt", False),
        (".env", False),
        ("password.txt", False),
        ("hello", False),
        ("", False),
    ],
)
def test_parametrized_validation(path, should_be_valid):
    is_valid, error = validate_path(path)
    assert is_valid == should_be_valid
    if not should_be_valid:
        assert error != ""
