"""
Modul Konfigurasi: Keamanan & Fallback untuk Hermes Manual Bridge.
Berisi pengaturan whitelist direktori dan parameter keamanan lainnya.

WHITELIST DIREKTORI:
Hanya file di dalam direktori yang ter-whitelist yang boleh ditulis oleh Hermes.
Ini mencegah Hermes menulis file ke lokasi sensitif seperti /etc/, /root/, dll.

Konfigurasi ini dimuat sekali saat aplikasi startup dan digunakan oleh:
- path_extractor.py (validate_path_against_whitelist)
- approval.py router (endpoint /approval/check-whitelist)
- UI approval.js (tampilkan warning jika path di luar whitelist)

Version: 1.0.0
"""
import os
from pathlib import Path
from typing import List, Dict, Any


class SecurityConfig:
    """Konfigurasi keamanan untuk Hermes Manual Bridge."""
    
    # ============================================================
    # WHITELIST DIREKTORI
    # ============================================================
    # Hanya file di dalam direktori ini yang boleh ditulis oleh Hermes.
    # Path harus absolut dan normalized (tanpa trailing slash).
    #
    # Default: /home/farhan/Proyek/Hermes (root project)
    # User bisa menambahkan direktori lain sesuai kebutuhan.
    # ============================================================
    
    # Root project directory (default)
    PROJECT_ROOT = Path("/home/farhan/Proyek/Hermes")
    
    # Daftar direktori yang di-whitelist (absolut path)
    # Tambahkan direktori lain di sini jika diperlukan
    WHITELISTED_DIRECTORIES: List[str] = [
        str(PROJECT_ROOT),
        # Contoh tambahan (uncomment jika diperlukan):
        # "/home/farhan/Proyek/Lain",
        # "/home/farhan/Documents/HermesProjects",
    ]
    
    # ============================================================
    # EKSTENSI FILE YANG DIIZINKAN
    # ============================================================
    # Hanya file dengan ekstensi ini yang boleh ditulis.
    # Mencegah penulisan file executable atau file sistem.
    # ============================================================
    
    ALLOWED_EXTENSIONS: List[str] = [
        # Programming languages
        "py", "js", "ts", "jsx", "tsx", "html", "css", "scss",
        "json", "yaml", "yml", "toml", "ini", "cfg",
        "md", "txt", "csv", "sql",
        "sh", "bash",
        "cpp", "cc", "c", "h", "hpp",
        "java", "go", "rs", "rb", "php", "lua",
        "xml", "env",
        # Config files
        "conf", "config",
        # Data files
        "log",
    ]
    
    # ============================================================
    # BATASAN UKURAN FILE
    # ============================================================
    # Mencegah penulisan file yang terlalu besar (potensi DoS)
    # ============================================================
    
    MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    MAX_FILE_SIZE_LINES: int = 10000  # 10.000 baris
    
    # ============================================================
    # MODE FALLBACK
    # ============================================================
    # Jika parsing gagal, sistem bisa fallback ke mode teks biasa
    # ============================================================
    
    ENABLE_FALLBACK_TO_TEXT: bool = True  # Izinkan fallback ke teks biasa
    FALLBACK_WARNING_MESSAGE: str = (
        "Parsing gagal. Respons akan dikirim sebagai teks biasa."
    )
    
    # ============================================================
    # DIALOG MANUAL INPUT
    # ============================================================
    # Pengaturan untuk dialog input path manual
    # ============================================================
    
    MANUAL_INPUT_MAX_LENGTH: int = 500  # Maksimal panjang path input
    MANUAL_INPUT_PLACEHOLDER: str = "path/ke/file.ext"
    
    @classmethod
    def get_whitelist_info(cls) -> Dict[str, Any]:
        """
        Dapatkan informasi whitelist untuk ditampilkan di UI.
        
        Returns:
            Dict dengan daftar direktori yang di-whitelist dan info lainnya.
        """
        return {
            "whitelisted_directories": cls.WHITELISTED_DIRECTORIES,
            "allowed_extensions": cls.ALLOWED_EXTENSIONS,
            "max_file_size_bytes": cls.MAX_FILE_SIZE_BYTES,
            "max_file_size_lines": cls.MAX_FILE_SIZE_LINES,
            "enable_fallback_to_text": cls.ENABLE_FALLBACK_TO_TEXT,
        }
    
    @classmethod
    def is_path_in_whitelist(cls, path: str) -> bool:
        """
        Cek apakah path berada di dalam direktori yang di-whitelist.
        
        Args:
            path: Path file yang akan dicek (relatif atau absolut)
            
        Returns:
            True jika path berada di dalam whitelist, False jika tidak.
            
        Contoh:
            >>> SecurityConfig.is_path_in_whitelist("/home/farhan/Proyek/Hermes/hello.py")
            True
            >>> SecurityConfig.is_path_in_whitelist("/etc/passwd")
            False
        """
        if not path:
            return False
        
        try:
            # Normalize path
            path_obj = Path(path).resolve()
            path_str = str(path_obj)
            
            # Cek apakah path berada di dalam salah satu direktori whitelist
            for whitelist_dir in cls.WHITELISTED_DIRECTORIES:
                whitelist_path = Path(whitelist_dir).resolve()
                whitelist_str = str(whitelist_path)
                
                # Path harus dimulai dengan whitelist directory
                if path_str.startswith(whitelist_str + os.sep) or path_str == whitelist_str:
                    return True
            
            return False
        except Exception:
            # Jika ada error dalam validasi, tolak path
            return False
    
    @classmethod
    def is_extension_allowed(cls, path: str) -> bool:
        """
        Cek apakah ekstensi file diizinkan.
        
        Args:
            path: Path file yang akan dicek
            
        Returns:
            True jika ekstensi diizinkan, False jika tidak.
        """
        if not path:
            return False
        
        try:
            path_obj = Path(path)
            ext = path_obj.suffix.lower().lstrip(".")
            
            # Jika tidak ada ekstensi, tolak
            if not ext:
                return False
            
            return ext in cls.ALLOWED_EXTENSIONS
        except Exception:
            return False
    
    @classmethod
    def validate_file_size(cls, content: str) -> tuple:
        """
        Validasi ukuran file (bytes dan lines).
        
        Args:
            content: Isi file yang akan divalidasi
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not content:
            return True, ""
        
        # Cek ukuran dalam bytes
        size_bytes = len(content.encode("utf-8"))
        if size_bytes > cls.MAX_FILE_SIZE_BYTES:
            return False, f"File terlalu besar: {size_bytes} bytes (maksimal {cls.MAX_FILE_SIZE_BYTES} bytes)"
        
        # Cek jumlah baris
        lines = content.count("\n") + 1
        if lines > cls.MAX_FILE_SIZE_LINES:
            return False, f"File terlalu banyak baris: {lines} baris (maksimal {cls.MAX_FILE_SIZE_LINES} baris)"
        
        return True, ""


# Singleton instance untuk kemudahan akses
security_config = SecurityConfig()
