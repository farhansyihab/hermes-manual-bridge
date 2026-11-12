"""
Unit test Modul D: Path Source Detector (Fase 3).

Menjalankan:
    cd /home/farhan/Proyek/Hermes/middleware
    pytest tests/test_detect_path_source.py -v

Catatan penting:
    Test ini dirancang agar SELALU konsisten dengan app.parser.
    Namun, app.path_extractor memiliki perilaku berbeda untuk beberapa
    kasus edge (lihat TestKnownInconsistencies). Lihat komentar
    "BUG LAMA" di app/detect_path_source.py untuk rencana perbaikan.

Backtick dibangun via chr(96) agar file ini tidak memuat tiga backtick literal.
"""

import pytest

from app.detect_path_source import (
    detect_path_source,
    get_source_description,
    get_source_icon,
    get_source_color,
    get_source_info,
)

BT = chr(96)


class TestExplicitSource:
    """Prioritas 1: format eksplisit [FILE: path]."""

    def test_explicit_simple(self):
        assert detect_path_source("[FILE: hello.py] Buatkan file") == "explicit"

    def test_explicit_with_directory(self):
        assert detect_path_source("[FILE: src/utils/helpers.py] Modul") == "explicit"

    def test_explicit_lowercase_tag(self):
        assert detect_path_source("[file: main.py] buat") == "explicit"

    def test_explicit_mixedcase_tag(self):
        assert detect_path_source("[File: main.py] buat") == "explicit"

    def test_explicit_with_spaces(self):
        assert detect_path_source("[FILE:   app.js   ] Buatkan file") == "explicit"

    def test_explicit_with_backtick_inside(self):
        prompt = "[FILE: " + BT + "app.js" + BT + "] Buatkan file"
        assert detect_path_source(prompt) == "explicit"

    def test_explicit_with_hyphen_and_dot_path(self):
        assert detect_path_source("[FILE: src/my-file_v2.0.py] Buat") == "explicit"

    def test_explicit_with_newline(self):
        assert detect_path_source("[FILE: hello.py]\nBuatkan file") == "explicit"

    def test_explicit_with_tab(self):
        assert detect_path_source("[FILE:\thello.py]\tBuatkan file") == "explicit"

    def test_explicit_empty_path_falls_back(self):
        assert detect_path_source("[FILE:    ] Buatkan file") == "manual"

    def test_explicit_backtick_only_path_falls_back(self):
        prompt = "[FILE: " + BT + BT + "] Buatkan file"
        assert detect_path_source(prompt) == "manual"


class TestNaturalLanguageKeywordBased:
    """Prioritas 2: pola bahasa natural berbasis kata kunci."""

    def test_nl_file_keyword(self):
        assert detect_path_source("Buatkan file hello.py yang mencetak Halo") == "natural_language"

    def test_nl_berkas_keyword(self):
        assert detect_path_source("Buatkan berkas config.yaml untuk database") == "natural_language"

    def test_nl_bernama_keyword(self):
        assert detect_path_source("Buat script bernama backup.sh untuk MySQL") == "natural_language"

    def test_nl_named_keyword(self):
        assert detect_path_source("Create a script named backup.sh please") == "natural_language"

    def test_nl_dengan_nama_keyword(self):
        assert detect_path_source("Buat script dengan nama backup.sh") == "natural_language"

    def test_nl_simpan_ke(self):
        assert detect_path_source("Simpan ke src/app.py ya") == "natural_language"

    def test_nl_save_to(self):
        assert detect_path_source("Save to src/app.py please") == "natural_language"

    def test_nl_tulis_ke(self):
        assert detect_path_source("Tulis ke file.py ya") == "natural_language"

    def test_nl_backtick_quoted(self):
        prompt = "Buatkan file " + BT + "app.js" + BT + " untuk backend Express"
        assert detect_path_source(prompt) == "natural_language"

    def test_nl_case_insensitive_keyword(self):
        assert detect_path_source("Buatkan FILE Hello.py") == "natural_language"
        assert detect_path_source("Buatkan BERKAS Config.yaml") == "natural_language"

    def test_nl_file_hello_without_extension_matches_old_bug(self):
        # BUG LAMA: dot mentah di _PATH_PATTERN membuat 'hello' ikut match.
        # Direplikasi agar konsisten dgn parser.py lama.
        assert detect_path_source("Buatkan file hello yang mencetak Halo") == "natural_language"

    def test_nl_backtick_hello_without_extension_matches_old_bug(self):
        prompt = "Buatkan file " + BT + "hello" + BT + " yang mencetak Halo"
        assert detect_path_source(prompt) == "natural_language"


class TestStandaloneFilenameBehavior:
    """
    Perilaku aktual pola standalone filename (mengikuti bug lama).

    Karena bug di regex (dot tidak di-escape), semua ekstensi yang ada di
    _EXT list akan match karena '.' regex cocok dengan literal dot di input.
    Ini konsisten dengan parser.py.
    """

    @pytest.mark.parametrize(
        "filename",
        [
            "main.py",
            "index.js",
            "app.ts",
            "index.html",
            "style.css",
            "config.json",
            "config.yaml",
            "backup.sh",
            "main.cpp",
            "readme.md",
            "data.csv",
            "query.sql",
            "main.go",
            "app.rb",
        ],
    )
    def test_standalone_filename_detected(self, filename):
        # BUG LAMA: semua ekstensi match karena '.' regex = any char
        prompt = "Tolong buatkan " + filename + " untuk aplikasi"
        assert detect_path_source(prompt) == "natural_language"

    def test_standalone_py_detected(self):
        assert detect_path_source("buat main.py sekarang") == "natural_language"

    def test_standalone_sh_detected(self):
        assert detect_path_source("buat backup.sh sekarang") == "natural_language"

    def test_standalone_html_detected(self):
        # BUG LAMA: index.html match karena '.' regex cocok dengan literal dot
        assert detect_path_source("buat index.html sekarang") == "natural_language"


class TestManualFallback:
    """Prioritas 3: tidak terdeteksi -> input manual."""

    def test_manual_ambiguous(self):
        assert detect_path_source("Tolong buatkan script untuk backup database") == "manual"

    def test_manual_no_file_reference(self):
        assert detect_path_source("Buatkan fungsi untuk menghitung fibonacci") == "manual"

    def test_manual_empty_string(self):
        assert detect_path_source("") == "manual"

    def test_manual_none(self):
        assert detect_path_source(None) == "manual"

    def test_manual_whitespace(self):
        assert detect_path_source("   ") == "manual"

    def test_manual_tabs(self):
        assert detect_path_source("\t\t") == "manual"

    def test_manual_newlines(self):
        assert detect_path_source("\n\n") == "manual"

    @pytest.mark.parametrize("value", [123, 0, True, False, [], {}, (), 3.14])
    def test_manual_non_string(self, value):
        assert detect_path_source(value) == "manual"

    def test_manual_bracket_without_file_tag(self):
        assert detect_path_source("[TODO] Buatkan script backup") == "manual"

    def test_manual_version_number_not_false_positive(self):
        # Angka versi tidak boleh dianggap path
        assert detect_path_source("upgrade ke versi 2.0 sekarang") == "manual"


class TestPriorityHierarchy:
    """Pastikan urutan prioritas benar."""

    def test_explicit_beats_natural_language(self):
        prompt = "[FILE: correct.py] Buatkan file wrong.py"
        assert detect_path_source(prompt) == "explicit"

    def test_natural_language_beats_manual(self):
        prompt = "Buatkan file hello.py dan script backup"
        assert detect_path_source(prompt) == "natural_language"

    def test_multiple_explicit_tags(self):
        prompt = "[FILE: first.py] dan [FILE: second.py]"
        assert detect_path_source(prompt) == "explicit"

    def test_path_tag_is_not_file_tag(self):
        # [PATH: ...] bukan format eksplisit; 'hello.py' tetap terdeteksi NL
        assert detect_path_source("[PATH: hello.py] Buatkan file") == "natural_language"


class TestSourceDescription:
    """Helper: get_source_description()."""

    def test_description_explicit(self):
        desc = get_source_description("explicit")
        assert "Eksplisit" in desc
        assert "[FILE:" in desc

    def test_description_natural_language(self):
        assert "Bahasa" in get_source_description("natural_language")

    def test_description_manual(self):
        assert "Manual" in get_source_description("manual")

    def test_description_unknown(self):
        assert get_source_description("unknown") == "Tidak Diketahui"

    def test_description_empty(self):
        assert get_source_description("") == "Tidak Diketahui"


class TestSourceIcon:
    """Helper: get_source_icon()."""

    def test_icon_explicit(self):
        assert get_source_icon("explicit") == "\U0001F3AF"

    def test_icon_natural_language(self):
        assert get_source_icon("natural_language") == "\U0001F4AC"

    def test_icon_manual(self):
        assert get_source_icon("manual") == "\u270D\uFE0F"

    def test_icon_unknown(self):
        assert get_source_icon("unknown") == "\u2753"

    def test_icon_empty(self):
        assert get_source_icon("") == "\u2753"


class TestSourceColor:
    """Helper: get_source_color()."""

    @pytest.mark.parametrize("source", ["explicit", "natural_language", "manual", "unknown", ""])
    def test_color_is_hex(self, source):
        color = get_source_color(source)
        assert color.startswith("#")
        assert len(color) == 7

    def test_color_values_differ(self):
        colors = {
            get_source_color("explicit"),
            get_source_color("natural_language"),
            get_source_color("manual"),
        }
        assert len(colors) == 3


class TestSourceInfo:
    """Helper: get_source_info()."""

    @pytest.mark.parametrize("source", ["explicit", "natural_language", "manual"])
    def test_info_keys(self, source):
        info = get_source_info(source)
        assert set(info.keys()) == {"source", "description", "icon", "color"}
        assert info["source"] == source
        assert isinstance(info["description"], str) and info["description"]
        assert isinstance(info["icon"], str) and info["icon"]
        assert info["color"].startswith("#")

    def test_info_unknown_fallback(self):
        info = get_source_info("unknown")
        assert info["description"] == "Tidak Diketahui"
        assert info["icon"] == "\u2753"


class TestEdgeCases:
    """Kasus khusus dan ketahanan fungsi."""

    def test_very_long_prompt(self):
        prompt = "[FILE: hello.py] " + ("x" * 10000)
        assert detect_path_source(prompt) == "explicit"

    def test_unicode_prompt(self):
        prompt = "[FILE: hello.py] Buatkan file yang mencetak Halo \U0001F389"
        assert detect_path_source(prompt) == "explicit"

    def test_mixed_whitespace_padding(self):
        prompt = "  \t\n  [FILE: hello.py]  \t\n  Buatkan file  "
        assert detect_path_source(prompt) == "explicit"

    def test_idempotent(self):
        prompt = "Buatkan file hello.py"
        assert detect_path_source(prompt) == detect_path_source(prompt) == "natural_language"


class TestIntegrationBlueprint:
    """Skenario Fase 3 sesuai Blueprint bagian 10.3."""

    def test_skenario_1_explicit(self):
        prompt = '[FILE: hello.py] Buatkan file yang mencetak "Halo dari Hermes!"'
        source = detect_path_source(prompt)
        assert source == "explicit"
        assert get_source_info(source)["icon"] == "\U0001F3AF"

    def test_skenario_2_natural_language(self):
        prompt = 'Buatkan file hello.py yang mencetak "Halo"'
        source = detect_path_source(prompt)
        assert source == "natural_language"
        assert get_source_info(source)["icon"] == "\U0001F4AC"

    def test_skenario_3_manual(self):
        prompt = "Tolong buatkan script untuk backup database"
        source = detect_path_source(prompt)
        assert source == "manual"
        assert get_source_info(source)["icon"] == "\u270D\uFE0F"

    def test_ui_payload_ready(self):
        source = detect_path_source("[FILE: hello.py] Buatkan file")
        info = get_source_info(source)
        assert info["source"] in ("explicit", "natural_language", "manual")
        assert len(info["color"]) == 7


class TestConsistencyWithParser:
    """
    Jaga konsistensi dengan parser.py yang sudah ada.

    Jika suatu hari Anda memperbaiki bug regex di detect_path_source.py,
    WAJIB perbaiki juga di parser.py secara serentak.
    """

    @pytest.mark.parametrize(
        "prompt",
        [
            "[FILE: hello.py] Buatkan file",
            "Buatkan file hello.py yang mencetak Halo",
            "Tolong buatkan script untuk backup database",
            "Buatkan berkas config.yaml untuk database",
            "Buat script bernama backup.sh untuk MySQL",
            "Tolong buatkan main.py untuk aplikasi",
            "Tolong buatkan index.html untuk landing page",
        ],
    )
    def test_same_result_as_parser(self, prompt):
        from app.parser import detect_path_source as parser_detect
        assert detect_path_source(prompt) == parser_detect(prompt)


class TestConsistencyWithPathExtractor:
    """
    Jaga konsistensi dengan path_extractor.py untuk kasus umum.

    PERHATIAN: path_extractor.py memiliki perilaku berbeda untuk beberapa
    kasus edge (lihat TestKnownInconsistencies). Jika Anda ingin konsistensi
    penuh, perlu update path_extractor.py juga.
    """

    @pytest.mark.parametrize(
        "prompt",
        [
            "[FILE: hello.py] Buatkan file",
            "Buatkan file hello.py yang mencetak Halo",
            "Simpan ke src/app.py ya",
            "Tolong buatkan script untuk backup database",
            "",
            "Buatkan berkas config.yaml untuk database",
            "Buat script bernama backup.sh untuk MySQL",
            "Buatkan file " + BT + "app.js" + BT + " untuk backend",
            "[FILE: correct.py] Buatkan file wrong.py",
            "Tolong buatkan main.py untuk aplikasi",
        ],
    )
    def test_same_result_as_path_extractor(self, prompt):
        from app.path_extractor import detect_path_source as legacy_detect
        assert detect_path_source(prompt) == legacy_detect(prompt)


class TestKnownInconsistencies:
    """
    Dokumentasikan perbedaan perilaku antara parser.py dan path_extractor.py.

    Ini adalah kasus edge di mana kedua modul lama menghasilkan output berbeda.
    Modul baru ini konsisten dengan parser.py (yang lebih lenient).
    Jika Anda ingin mengubah perilaku, update ketiga modul secara serentak.
    """

    def test_index_html_parser_vs_path_extractor(self):
        """
        Prompt ini menghasilkan output berbeda di modul lama:
        - parser.py: natural_language (karena bug regex)
        - path_extractor.py: manual (regex lebih ketat)
        - detect_path_source.py: natural_language (konsisten dgn parser.py)
        """
        prompt = "Tolong buatkan index.html untuk landing page"

        from app.parser import detect_path_source as parser_detect
        from app.path_extractor import detect_path_source as path_extractor_detect

        # Dokumentasikan perbedaan
        parser_result = parser_detect(prompt)
        path_extractor_result = path_extractor_detect(prompt)
        new_module_result = detect_path_source(prompt)

        assert parser_result == "natural_language"
        assert path_extractor_result == "manual"
        assert new_module_result == parser_result  # Konsisten dengan parser.py


class TestSourceHasNoLiteralFence:
    """Jaga-jaga: source modul tidak boleh memuat tiga backtick literal."""

    def test_module_source_clean(self):
        import app.detect_path_source as module
        with open(module.__file__, "r", encoding="utf-8") as handle:
            source = handle.read()
        assert (chr(96) * 3) not in source