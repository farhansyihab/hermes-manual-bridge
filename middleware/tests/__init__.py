"""
Test package initialization untuk Hermes Manual Bridge.
Folder ini berisi unit test untuk semua modul Fase 1-3.

Struktur test:
- test_parser.py            : Test untuk Modul D (parser.py)
- test_path_extractor.py    : Test untuk Modul D (path_extractor.py)
- test_detect_path_source.py: Test untuk Modul D (detect_path_source.py)

Menjalankan semua test:
    cd /home/farhan/Proyek/Hermes/middleware
    pytest tests/ -v

Menjalankan test spesifik:
    pytest tests/test_detect_path_source.py -v
    pytest tests/test_detect_path_source.py::TestDetectPathSourceExplicit -v
"""