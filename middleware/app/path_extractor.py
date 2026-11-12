"""
Modul: Path Extractor untuk Hermes Manual Bridge (Fase 3)
==========================================================

Fungsi utama: Mengekstrak path file dari prompt Hermes Agent dengan strategi hierarkis.

Prioritas Ekstraksi:
    1. Format Eksplisit: [FILE: path] - dari system prompt Hermes (Opsi A)
    2. Natural Language: pola bahasa natural (backward compatibility)
    3. Manual Fallback: return None → UI tampilkan dialog input manual

Konvensi:
    - Semua karakter backtick dibangun via chr(96) untuk menghindari
      triple backtick literal dalam source file.
    - Fungsi ini stateless dan thread-safe.
    - Return None jika path tidak terdeteksi (fallback ke UI manual).

Author: Hermes Manual Bridge Team
Version: 1.0.0
"""

import re
from typing import Optional, Tuple


# ============================================================
# KONSTANTA: Backtick dan Fence (dibangun secara programatik)
# ============================================================
BT = chr(96)  # Single backtick: `
FENCE = BT * 3  # Triple backtick: ```


# ============================================================
# POLA REGEX: Format Eksplisit [FILE: path]
# ============================================================
# Match: [FILE: path/to/file.ext] atau [file: path] (case-insensitive)
# Group 1: path file (tanpa kurung siku)
_EXPLICIT_RE = re.compile(
    r"\[FILE:\s*([^\]]+)\]",
    re.IGNORECASE
)


# ============================================================
# POLA REGEX: Natural Language Patterns (Fallback)
# ============================================================
# Pola nama file/path relatif: wajib punya ekstensi
_PATH_PATTERN = r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z0-9]+"

# Ekstensi umum untuk deteksi filename yang berdiri sendiri
_COMMON_EXTENSIONS = (
    r"py|js|ts|jsx|tsx|html|css|scss|json|yaml|yml|toml|ini|cfg|md|txt|csv|sql|"
    r"sh|bash|cpp|cc|c|h|hpp|java|go|rs|rb|php|lua|xml|env"
)

# Daftar pola natural language dengan prioritas
_NL_PATTERNS = [
    # "file hello.py" / "berkas config.yaml"
    re.compile(
        rf"(?:file|berkas)\s+{BT}?({_PATH_PATTERN}){BT}?",
        re.IGNORECASE
    ),
    
    # "named app.js" / "bernama backup.sh" / "dengan nama app.js"
    re.compile(
        rf"(?:named|bernama|dengan\s+nama)\s+{BT}?({_PATH_PATTERN}){BT}?",
        re.IGNORECASE
    ),
    
    # "simpan ke src/app.py" / "save to src/app.py" / "tulis ke file.py"
    re.compile(
        rf"(?:simpan\s+ke|save\s+to|tulis\s+ke)\s+{BT}?({_PATH_PATTERN}){BT}?",
        re.IGNORECASE
    ),
    
    # Nama file dikutip backtick tunggal: `app.js`
    re.compile(
        rf"{BT}({_PATH_PATTERN}){BT}",
        re.IGNORECASE
    ),
    
    # Nama file berdiri sendiri dengan ekstensi dikenal
    re.compile(
        rf"\b([A-Za-z0-9_-]+(?:\.{_COMMON_EXTENSIONS}))\b",
        re.IGNORECASE
    ),
]


# ============================================================
# FUNGSI UTAMA: extract_file_path_from_prompt()
# ============================================================
def extract_file_path_from_prompt(prompt: str) -> Optional[str]:
    """
    Ekstrak path file dari prompt Hermes dengan strategi hierarkis.
    
    Prioritas:
        1. Format eksplisit [FILE: path] - dari system prompt Hermes (Opsi A)
        2. Pola bahasa natural (backward compatibility dengan prompt lama)
        3. Return None → UI menampilkan dialog input path manual
    
    Args:
        prompt: Prompt dari Hermes Agent (string)
    
    Returns:
        String path bila terdeteksi, None bila tidak terdeteksi.
    
    Contoh:
        >>> extract_file_path_from_prompt("[FILE: hello.py] Buatkan file")
        'hello.py'
        
        >>> extract_file_path_from_prompt("Buatkan file hello.py yang mencetak Halo")
        'hello.py'
        
        >>> extract_file_path_from_prompt("Tolong buatkan script backup") is None
        True
        
        >>> extract_file_path_from_prompt("[FILE: src/utils/helpers.py] Modul helper")
        'src/utils/helpers.py'
        
        >>> extract_file_path_from_prompt("Simpan ke src/app.py ya")
        'src/app.py'
    
    Catatan:
        - Fungsi ini case-insensitive untuk format [FILE:] dan pola NL.
        - Spasi di awal/akhir path akan di-strip.
        - Jika multiple match ditemukan, yang pertama (paling awal) akan digunakan.
    """
    # Validasi input
    if not prompt or not isinstance(prompt, str):
        return None
    
    prompt = prompt.strip()
    if not prompt:
        return None
    
    # ========================================================
    # PRIORITAS 1: Format Eksplisit [FILE: path]
    # ========================================================
    explicit_match = _EXPLICIT_RE.search(prompt)
    if explicit_match:
        path = explicit_match.group(1).strip()
        # Hapus backtick jika ada di dalam kurung siku
        path = path.strip(BT).strip()
        if path:
            return path
    
    # ========================================================
    # PRIORITAS 2: Pola Natural Language (Fallback)
    # ========================================================
    for pattern in _NL_PATTERNS:
        match = pattern.search(prompt)
        if match:
            path = match.group(1).strip()
            if path:
                return path
    
    # ========================================================
    # PRIORITAS 3: Return None (Fallback ke UI Manual)
    # ========================================================
    return None


# ============================================================
# FUNGSI PENDUKUNG: detect_path_source()
# ============================================================
def detect_path_source(prompt: str) -> str:
    """
    Tentukan sumber path untuk indikator di UI.
    
    Args:
        prompt: Prompt dari Hermes Agent
    
    Returns:
        Salah satu dari:
        - "explicit"         → dari format [FILE: path]
        - "natural_language" → dari pola bahasa natural
        - "manual"           → tidak terdeteksi, perlu input manual
    
    Contoh:
        >>> detect_path_source("[FILE: hello.py] Buatkan file")
        'explicit'
        
        >>> detect_path_source("Buatkan file hello.py")
        'natural_language'
        
        >>> detect_path_source("Tolong buatkan script")
        'manual'
    """
    if not prompt or not isinstance(prompt, str):
        return "manual"
    
    prompt = prompt.strip()
    if not prompt:
        return "manual"
    
    # Cek format eksplisit
    explicit_match = _EXPLICIT_RE.search(prompt)
    if explicit_match:
        path = explicit_match.group(1).strip().strip(BT).strip()
        if path:
            return "explicit"
    
    # Cek pola natural language
    for pattern in _NL_PATTERNS:
        if pattern.search(prompt):
            return "natural_language"
    
    # Fallback
    return "manual"


# ============================================================
# FUNGSI PENDUKUNG: validate_path()
# ============================================================
def validate_path(path: str) -> Tuple[bool, str]:
    """
    Validasi path file untuk keamanan (whitelist/blacklist).
    
    Args:
        path: Path file yang akan divalidasi
    
    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True jika path aman, False jika berbahaya
        - error_message: Pesan error jika tidak valid, kosong jika valid
    
    Contoh:
        >>> validate_path("hello.py")
        (True, '')
        
        >>> validate_path("/etc/passwd")
        (False, 'Path absolut tidak diizinkan')
        
        >>> validate_path("../secret.txt")
        (False, 'Path traversal tidak diizinkan')
    """
    if not path or not isinstance(path, str):
        return False, "Path tidak boleh kosong"
    
    path = path.strip()
    
    # Block path absolut (dimulai dengan / atau drive letter Windows)
    if path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        return False, "Path absolut tidak diizinkan"
    
    # Block path traversal (..)
    if ".." in path:
        return False, "Path traversal (..) tidak diizinkan"
    
    # Block path yang mencurigakan
    suspicious_patterns = [
        r"/etc/",
        r"/proc/",
        r"/sys/",
        r"/dev/",
        r"/root/",
        r"/home/[^/]+/\.ssh",
        r"\.env$",
        r"password",
        r"secret",
        r"private[_-]?key",
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, path, re.IGNORECASE):
            return False, f"Path mencurigakan terdeteksi: {path}"
    
    # Validasi format path (hanya karakter yang diizinkan)
    if not re.match(r"^[A-Za-z0-9_./-]+$", path):
        return False, "Path mengandung karakter tidak valid"
    
    # Validasi ekstensi (opsional, bisa disesuaikan)
    if "." not in path:
        return False, "Path harus memiliki ekstensi file"
    
    return True, ""


# ============================================================
# FUNGSI UTILITAS: extract_and_validate_path()
# ============================================================
def extract_and_validate_path(prompt: str) -> Tuple[Optional[str], str, str]:
    """
    Fungsi lengkap: ekstrak path dari prompt + validasi keamanan.
    
    Args:
        prompt: Prompt dari Hermes Agent
    
    Returns:
        Tuple (path, source, validation_error)
        - path: Path yang diekstrak (None jika gagal)
        - source: Sumber path ("explicit" / "natural_language" / "manual")
        - validation_error: Pesan error jika path tidak valid, kosong jika valid
    
    Contoh:
        >>> path, source, error = extract_and_validate_path("[FILE: hello.py] Buat")
        >>> print(f"Path: {path}, Source: {source}, Error: {error}")
        Path: hello.py, Source: explicit, Error: 
        
        >>> path, source, error = extract_and_validate_path("[FILE: /etc/passwd]")
        >>> print(f"Path: {path}, Source: {source}, Error: {error}")
        Path: /etc/passwd, Source: explicit, Error: Path absolut tidak diizinkan
    """
    # Ekstrak path
    path = extract_file_path_from_prompt(prompt)
    
    # Deteksi sumber
    source = detect_path_source(prompt)
    
    # Validasi jika path ditemukan
    validation_error = ""
    if path:
        is_valid, error_msg = validate_path(path)
        if not is_valid:
            validation_error = error_msg
            path = None  # Reset path jika tidak valid
    
    return path, source, validation_error


# ============================================================
# TESTING: Contoh penggunaan (jika file dijalankan langsung)
# ============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("Testing Path Extractor Module")
    print("=" * 70)
    
    # Test case 1: Format eksplisit
    test_prompts = [
        "[FILE: hello.py] Buatkan file yang mencetak Halo",
        "[FILE: src/utils/helpers.py] Buatkan modul helper",
        "Buatkan file hello.py yang mencetak Halo",
        "Buatkan berkas config.yaml untuk database",
        "Buat script bernama backup.sh untuk MySQL",
        "Simpan ke src/app.py ya",
        f"Buatkan file {BT}app.js{BT} untuk backend",
        "Tolong buatkan index.html untuk landing page",
        "Tolong buatkan script untuk backup database",  # Ambigu → None
        "[FILE: /etc/passwd] Baca file",  # Berbahaya → invalid
        "[FILE: ../secret.txt] Akses",  # Traversal → invalid
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nTest {i}: {prompt[:60]}...")
        path, source, error = extract_and_validate_path(prompt)
        print(f"  Path: {path}")
        print(f"  Source: {source}")
        if error:
            print(f"  Error: {error}")
    
    print("\n" + "=" * 70)
    print("Testing selesai!")
    print("=" * 70)
