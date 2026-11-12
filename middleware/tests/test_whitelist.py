"""
Unit test untuk Keamanan & Fallback (Fase 3):
- Whitelist direktori validation
- File content validation
- Fallback mode

Menjalankan:
cd /home/farhan/Proyek/Hermes/middleware
pytest tests/test_whitelist.py -v

Version: 1.0.0
"""
import pytest
from app.config import security_config, SecurityConfig
from app.path_extractor import (
    validate_path_against_whitelist,
    validate_file_content,
    extract_and_validate_path,
)


class TestWhitelistConfig:
    """Test suite untuk konfigurasi whitelist."""
    
    def test_whitelist_not_empty(self):
        """Whitelist harus memiliki minimal satu direktori."""
        assert len(security_config.WHITELISTED_DIRECTORIES) > 0
    
    def test_whitelist_paths_are_absolute(self):
        """Semua path di whitelist harus absolut."""
        for path in security_config.WHITELISTED_DIRECTORIES:
            assert path.startswith("/"), f"Path harus absolut: {path}"
    
    def test_allowed_extensions_not_empty(self):
        """Daftar ekstensi yang diizinkan tidak boleh kosong."""
        assert len(security_config.ALLOWED_EXTENSIONS) > 0
    
    def test_max_file_size_positive(self):
        """Maksimal ukuran file harus positif."""
        assert security_config.MAX_FILE_SIZE_BYTES > 0
        assert security_config.MAX_FILE_SIZE_LINES > 0


class TestIsPathInWhitelist:
    """Test suite untuk fungsi is_path_in_whitelist()."""
    
    def test_path_in_project_root(self):
        """Path di dalam PROJECT_ROOT harus di-whitelist."""
        path = "/home/farhan/Proyek/Hermes/hello.py"
        assert security_config.is_path_in_whitelist(path) is True
    
    def test_path_in_subdirectory(self):
        """Path di subdirektori PROJECT_ROOT harus di-whitelist."""
        path = "/home/farhan/Proyek/Hermes/src/utils/helpers.py"
        assert security_config.is_path_in_whitelist(path) is True
    
    def test_path_outside_whitelist(self):
        """Path di luar whitelist harus ditolak."""
        path = "/etc/passwd"
        assert security_config.is_path_in_whitelist(path) is False
    
    def test_path_in_home_directory(self):
        """Path di home directory (di luar project) harus ditolak."""
        path = "/home/farhan/secret.txt"
        assert security_config.is_path_in_whitelist(path) is False
    
    def test_empty_path(self):
        """Path kosong harus ditolak."""
        assert security_config.is_path_in_whitelist("") is False
    
    def test_none_path(self):
        """Path None harus ditolak."""
        assert security_config.is_path_in_whitelist(None) is False


class TestIsExtensionAllowed:
    """Test suite untuk fungsi is_extension_allowed()."""
    
    def test_python_extension(self):
        """Ekstensi .py harus diizinkan."""
        assert security_config.is_extension_allowed("hello.py") is True
    
    def test_javascript_extension(self):
        """Ekstensi .js harus diizinkan."""
        assert security_config.is_extension_allowed("app.js") is True
    
    def test_html_extension(self):
        """Ekstensi .html harus diizinkan."""
        assert security_config.is_extension_allowed("index.html") is True
    
    def test_unknown_extension(self):
        """Ekstensi tidak dikenal harus ditolak."""
        assert security_config.is_extension_allowed("file.xyz") is False
    
    def test_no_extension(self):
        """File tanpa ekstensi harus ditolak."""
        assert security_config.is_extension_allowed("README") is False
    
    def test_empty_path(self):
        """Path kosong harus ditolak."""
        assert security_config.is_extension_allowed("") is False


class TestValidateFileSize:
    """Test suite untuk fungsi validate_file_size()."""
    
    def test_small_file(self):
        """File kecil harus valid."""
        content = "print('Hello')"
        is_valid, error = security_config.validate_file_size(content)
        assert is_valid is True
        assert error == ""
    
    def test_empty_file(self):
        """File kosong harus valid."""
        is_valid, error = security_config.validate_file_size("")
        assert is_valid is True
    
    def test_file_too_large_bytes(self):
        """File terlalu besar (bytes) harus ditolak."""
        # Buat content > 5 MB
        content = "x" * (6 * 1024 * 1024)
        is_valid, error = security_config.validate_file_size(content)
        assert is_valid is False
        assert "terlalu besar" in error.lower()
    
    def test_file_too_many_lines(self):
        """File terlalu banyak baris harus ditolak."""
        # Buat content > 10.000 baris
        content = "\n".join(["line"] * 11000)
        is_valid, error = security_config.validate_file_size(content)
        assert is_valid is False
        assert "terlalu banyak baris" in error.lower()


class TestValidatePathAgainstWhitelist:
    """Test suite untuk fungsi validate_path_against_whitelist()."""
    
    def test_relative_path_in_whitelist(self):
        """Path relatif di dalam whitelist harus valid."""
        is_valid, error = validate_path_against_whitelist("hello.py")
        assert is_valid is True
        assert error == ""
    
    def test_relative_path_with_subdirectory(self):
        """Path relatif dengan subdirektori harus valid."""
        is_valid, error = validate_path_against_whitelist("src/utils/helpers.py")
        assert is_valid is True
    
    def test_absolute_path_in_whitelist(self):
        """Path absolut di dalam whitelist harus valid."""
        path = "/home/farhan/Proyek/Hermes/hello.py"
        is_valid, error = validate_path_against_whitelist(path)
        assert is_valid is True
    
    def test_absolute_path_outside_whitelist(self):
        """Path absolut di luar whitelist harus ditolak."""
        path = "/etc/passwd"
        is_valid, error = validate_path_against_whitelist(path)
        assert is_valid is False
        assert "di luar" in error.lower() or "diizinkan" in error.lower()
    
    def test_empty_path(self):
        """Path kosong harus ditolak."""
        is_valid, error = validate_path_against_whitelist("")
        assert is_valid is False
    
    def test_none_path(self):
        """Path None harus ditolak."""
        is_valid, error = validate_path_against_whitelist(None)
        assert is_valid is False


class TestValidateFileContent:
    """Test suite untuk fungsi validate_file_content()."""
    
    def test_valid_content(self):
        """Content valid harus lolos."""
        content = "print('Hello')"
        is_valid, error = validate_file_content(content)
        assert is_valid is True
    
    def test_empty_content(self):
        """Content kosong harus valid."""
        is_valid, error = validate_file_content("")
        assert is_valid is True
    
    def test_content_too_large(self):
        """Content terlalu besar harus ditolak."""
        content = "x" * (6 * 1024 * 1024)
        is_valid, error = validate_file_content(content)
        assert is_valid is False


class TestExtractAndValidatePathWithWhitelist:
    """Test suite untuk extract_and_validate_path() dengan whitelist."""
    
    def test_explicit_path_in_whitelist(self):
        """Path eksplisit di dalam whitelist harus valid."""
        prompt = "[FILE: hello.py] Buatkan file"
        path, source, error, warnings = extract_and_validate_path(prompt)
        assert path == "hello.py"
        assert source == "explicit"
        assert error == ""
        assert len(warnings) == 0
    
    def test_natural_language_path_in_whitelist(self):
        """Path natural language di dalam whitelist harus valid."""
        prompt = "Buatkan file hello.py"
        path, source, error, warnings = extract_and_validate_path(prompt)
        assert path == "hello.py"
        assert source == "natural_language"
        assert error == ""
    
    def test_manual_fallback(self):
        """Prompt tanpa path harus fallback ke manual."""
        prompt = "Tolong buatkan script backup"
        path, source, error, warnings = extract_and_validate_path(prompt)
        assert path is None
        assert source == "manual"
        assert error == ""


class TestIntegrationScenarios:
    """Integration test untuk skenario keamanan & fallback."""
    
    def test_scenario_1_safe_file_creation(self):
        """Skenario 1: Pembuatan file aman di dalam whitelist."""
        prompt = "[FILE: src/utils/helpers.py] Buatkan modul helper"
        path, source, error, warnings = extract_and_validate_path(prompt)
        
        assert path == "src/utils/helpers.py"
        assert source == "explicit"
        assert error == ""
        
        # Validasi whitelist
        is_whitelisted, whitelist_error = validate_path_against_whitelist(path)
        assert is_whitelisted is True
    
    def test_scenario_2_dangerous_path_rejected(self):
        """Skenario 2: Path berbahaya harus ditolak."""
        prompt = "[FILE: /etc/passwd] Baca file"
        path, source, error, warnings = extract_and_validate_path(prompt)
        
        # Path harus ditolak karena absolut
        assert error != ""
        assert "absolut" in error.lower()
    
    def test_scenario_3_file_too_large(self):
        """Skenario 3: File terlalu besar harus ditolak."""
        large_content = "x" * (6 * 1024 * 1024)
        is_valid, error = validate_file_content(large_content)
        
        assert is_valid is False
        assert "terlalu besar" in error.lower()
    
    def test_scenario_4_fallback_mode(self):
        """Skenario 4: Fallback ke mode teks biasa."""
        # Jika parsing gagal, sistem bisa fallback ke teks biasa
        prompt = "Tolong buatkan script untuk backup database"
        path, source, error, warnings = extract_and_validate_path(prompt)
        
        assert path is None
        assert source == "manual"
        
        # Di UI, user bisa pilih "Kirim sebagai Teks Biasa"
        # Ini akan mengirim respons tanpa tool call


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
