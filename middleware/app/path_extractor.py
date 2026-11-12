"""
Modul: Path Extractor untuk Hermes Manual Bridge (Fase 3)
Fungsi utama: Mengekstrak path file dari prompt Hermes Agent dengan strategi hierarkis.

Prioritas Ekstraksi:
1. Format Eksplisit: [FILE: path] - dari system prompt Hermes (Opsi A)
2. Natural Language: pola bahasa natural (backward compatibility)
3. Manual Fallback: return None -> UI tampilkan dialog input manual

KEAMANAN & FALLBACK (Fase 3):
- Whitelist direktori: hanya path di dalam direktori yang di-whitelist yang diizinkan
- Validasi ekstensi file: hanya ekstensi yang diizinkan yang boleh ditulis
- Validasi ukuran file: mencegah file terlalu besar
- Fallback ke mode teks biasa jika parsing gagal

Konvensi:
- Semua karakter backtick dibangun via chr(96) untuk menghindari
triple backtick literal dalam source file.
- Fungsi ini stateless dan thread-safe.
- Return None jika path tidak terdeteksi (fallback ke UI manual).

Author: Hermes Manual Bridge Team
Version: 1.1.0 (Keamanan & Fallback)
"""
import re
import os
from pathlib import Path
from typing import Optional, Tuple, List
from .config import security_config


# ============================================================
# KONSTANTA: Backtick dan Fence (dibangun secara programatik)
# ============================================================
BT = chr(96)  # Single backtick
FENCE = BT * 3  # Triple backtick


# ============================================================
# POLA REGEX: Format Eksplisit [FILE: path]
# ============================================================
_EXPLICIT_RE = re.compile(
    r"\[FILE:\s*([^\]]+)\]",
    re.IGNORECASE
)


# ============================================================
# POLA REGEX: Natural Language Patterns (Fallback)
# ============================================================
_PATH_PATTERN = r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z0-9]+"

_COMMON_EXTENSIONS = (
    r"py|js|ts|jsx|tsx|html|css|scss|json|yaml|yml|toml|ini|cfg|md|txt|csv|sql|"
    r"sh|bash|cpp|cc|c|h|hpp|java|go|rs|rb|php|lua|xml|env"
)

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
    # Nama file dikutip backtick tunggal
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
        3. Return None -> UI menampilkan dialog input path manual
    
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
        - "explicit"         -> dari format [FILE: path]
        - "natural_language" -> dari pola bahasa natural
        - "manual"           -> tidak terdeteksi, perlu input manual
        
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
    
    Validasi yang dilakukan:
    1. Path tidak boleh kosong
    2. Path tidak boleh absolut (kecuali di whitelist)
    3. Path tidak boleh mengandung traversal (..)
    4. Path tidak boleh mencurigakan (/etc/, /proc/, dll)
    5. Path harus memiliki ekstensi
    
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
    
    # Validasi ekstensi (wajib punya ekstensi)
    if "." not in path:
        return False, "Path harus memiliki ekstensi file"
    
    return True, ""


# ============================================================
# FUNGSI BARU (Fase 3): validate_path_against_whitelist()
# ============================================================
def validate_path_against_whitelist(path: str, base_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validasi path terhadap whitelist direktori.
    
    Fungsi ini memastikan bahwa path file berada di dalam direktori
    yang di-whitelist. Ini mencegah Hermes menulis file ke lokasi
    sensitif di luar project directory.
    
    Args:
        path: Path file yang akan divalidasi (relatif atau absolut)
        base_dir: Direktori dasar untuk resolve path relatif.
                  Jika None, gunakan PROJECT_ROOT dari config.
    
    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True jika path di dalam whitelist, False jika tidak
        - error_message: Pesan error jika tidak valid, kosong jika valid
        
    Contoh:
        >>> validate_path_against_whitelist("hello.py")
        (True, '')  # Karena PROJECT_ROOT di-whitelist
        >>> validate_path_against_whitelist("/etc/passwd")
        (False, 'Path di luar direktori yang diizinkan')
    """
    if not path or not isinstance(path, str):
        return False, "Path tidak boleh kosong"
    
    path = path.strip()
    if not path:
        return False, "Path tidak boleh kosong"
    
    try:
        # Jika path relatif, resolve terhadap base_dir
        if not os.path.isabs(path):
            if base_dir is None:
                base_dir = str(security_config.PROJECT_ROOT)
            full_path = os.path.join(base_dir, path)
        else:
            full_path = path
        
        # Normalize path
        full_path = os.path.normpath(full_path)
        
        # Cek apakah path berada di dalam whitelist
        if not security_config.is_path_in_whitelist(full_path):
            return False, (
                f"Path di luar direktori yang diizinkan. "
                f"Hanya boleh menulis di: {', '.join(security_config.WHITELISTED_DIRECTORIES)}"
            )
        
        return True, ""
    except Exception as e:
        return False, f"Error validasi whitelist: {str(e)}"


# ============================================================
# FUNGSI BARU (Fase 3): validate_file_content()
# ============================================================
def validate_file_content(content: str) -> Tuple[bool, str]:
    """
    Validasi isi file (ukuran, dll).
    
    Args:
        content: Isi file yang akan divalidasi
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not content:
        return True, ""  # File kosong diizinkan
    
    is_valid, error_msg = security_config.validate_file_size(content)
    if not is_valid:
        return False, error_msg
    
    return True, ""


# ============================================================
# FUNGSI UTILITAS: extract_and_validate_path()
# ============================================================
def extract_and_validate_path(prompt: str, base_dir: Optional[str] = None) -> Tuple[Optional[str], str, str, List[str]]:
    """
    Fungsi lengkap: ekstrak path dari prompt + validasi keamanan + whitelist.
    
    Args:
        prompt: Prompt dari Hermes Agent
        base_dir: Direktori dasar untuk resolve path relatif (opsional)
    
    Returns:
        Tuple (path, source, validation_error, warnings)
        - path: Path yang diekstrak (None jika gagal)
        - source: Sumber path ("explicit" / "natural_language" / "manual")
        - validation_error: Pesan error jika path tidak valid, kosong jika valid
        - warnings: Daftar warning (misal: path di luar whitelist)
        
    Contoh:
        >>> path, source, error, warnings = extract_and_validate_path("[FILE: hello.py] Buat")
        >>> print(f"Path: {path}, Source: {source}, Error: {error}, Warnings: {warnings}")
        Path: hello.py, Source: explicit, Error: , Warnings: []
    """
    # Ekstrak path
    path = extract_file_path_from_prompt(prompt)
    
    # Deteksi sumber
    source = detect_path_source(prompt)
    
    # Validasi jika path ditemukan
    validation_error = ""
    warnings = []
    
    if path:
        # Validasi dasar
        is_valid, error_msg = validate_path(path)
        if not is_valid:
            validation_error = error_msg
            path = None  # Reset path jika tidak valid
        else:
            # Validasi whitelist
            is_whitelisted, whitelist_error = validate_path_against_whitelist(path, base_dir)
            if not is_whitelisted:
                warnings.append(whitelist_error)
                # Jangan reset path, biarkan user decide di UI
    
    return path, source, validation_error, warnings


# ============================================================
# FUNGSI BARU (Fase 3): get_whitelist_info()
# ============================================================
def get_whitelist_info() -> dict:
    """
    Dapatkan informasi whitelist untuk ditampilkan di UI.
    
    Returns:
        Dict dengan daftar direktori yang di-whitelist dan info lainnya.
    """
    return security_config.get_whitelist_info()


# ============================================================
# TESTING: Contoh penggunaan (jika file dijalankan langsung)
# ============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("Testing Path Extractor Module (dengan Keamanan & Fallback)")
    print("=" * 70)
    
    # Test case
    test_prompts = [
        "[FILE: hello.py] Buatkan file yang mencetak Halo",
        "[FILE: src/utils/helpers.py] Buatkan modul helper",
        "Buatkan file hello.py yang mencetak Halo",
        "Buatkan berkas config.yaml untuk database",
        "Buat script bernama backup.sh untuk MySQL",
        "Simpan ke src/app.py ya",
        f"Buatkan file {BT}app.js{BT} untuk backend",
        "Tolong buatkan index.html untuk landing page",
        "Tolong buatkan script untuk backup database",  # Ambigu -> None
        "[FILE: /etc/passwd] Baca file",  # Berbahaya -> invalid
        "[FILE: ../secret.txt] Akses",  # Traversal -> invalid
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nTest {i}: {prompt[:60]}...")
        path, source, error, warnings = extract_and_validate_path(prompt)
        print(f"  Path: {path}")
        print(f"  Source: {source}")
        if error:
            print(f"  Error: {error}")
        if warnings:
            print(f"  Warnings: {warnings}")
    
    print("\n" + "=" * 70)
    print("Testing Whitelist Validation")
    print("=" * 70)
    
    whitelist_tests = [
        "hello.py",
        "src/utils/helpers.py",
        "/home/farhan/Proyek/Hermes/hello.py",
        "/etc/passwd",
        "../secret.txt",
    ]
    
    for path in whitelist_tests:
        is_valid, error = validate_path_against_whitelist(path)
        print(f"\nPath: {path}")
        print(f"  Valid: {is_valid}")
        if error:
            print(f"  Error: {error}")
    
    print("\n" + "=" * 70)
    print("Testing selesai!")
    print("=" * 70)
