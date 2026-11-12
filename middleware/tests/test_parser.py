"""
Unit test Modul D: Code Parser & Path Extractor.

Sama seperti parser.py, file test ini tidak memuat tiga backtick literal.
Pagar kode dibangun dari chr(96) * 3 lewat helper fence().
"""
from app.parser import (
    BT,
    FENCE,
    extract_code_blocks,
    extract_file_path_from_prompt,
    detect_path_source,
    detect_language_from_content,
    enhance_code_blocks,
)


def fence(lang: str, code: str) -> str:
    """Bangun satu blok kode berpagar tanpa menulis backtick literal."""
    return FENCE + lang + "\n" + code + "\n" + FENCE


class TestExtractCodeBlocks:
    """Test suite untuk extract_code_blocks()"""

    def test_single_python_block(self):
        text = "Berikut kode Python:\n" + fence("python", "print('Hello')")
        result = extract_code_blocks(text)
        assert len(result) == 1
        assert result[0]["language"] == "python"
        assert result[0]["content"] == "print('Hello')"

    def test_multiple_blocks(self):
        text = fence("python", "print('A')") + "\n\n" + fence("javascript", "console.log('B')")
        result = extract_code_blocks(text)
        assert len(result) == 2
        assert result[0]["language"] == "python"
        assert result[1]["language"] == "javascript"

    def test_block_without_language(self):
        text = fence("", "some code")
        result = extract_code_blocks(text)
        assert len(result) == 1
        assert result[0]["language"] == "plaintext"
        assert result[0]["content"] == "some code"

    def test_no_code_blocks(self):
        assert extract_code_blocks("Ini hanya teks biasa tanpa kode") == []

    def test_empty_text(self):
        assert extract_code_blocks("") == []

    def test_multiline_code(self):
        code = "def hello():\n    print('Hello')\n    return True"
        result = extract_code_blocks(fence("python", code))
        assert len(result) == 1
        assert result[0]["content"] == code

    def test_language_normalized_lowercase(self):
        result = extract_code_blocks(fence("Python", "x = 1"))
        assert result[0]["language"] == "python"


class TestExtractFilePath:
    """Test suite untuk extract_file_path_from_prompt()"""

    def test_explicit_format_priority_1(self):
        prompt = "[FILE: hello.py] Buatkan file yang mencetak Halo"
        assert extract_file_path_from_prompt(prompt) == "hello.py"
        assert detect_path_source(prompt) == "explicit"

    def test_explicit_format_with_path(self):
        prompt = "[FILE: src/utils/helpers.py] Buatkan modul helper"
        assert extract_file_path_from_prompt(prompt) == "src/utils/helpers.py"
        assert detect_path_source(prompt) == "explicit"

    def test_explicit_format_with_spaces(self):
        assert extract_file_path_from_prompt("[FILE:   app.js   ] Buatkan file") == "app.js"

    def test_explicit_format_lowercase_tag(self):
        assert extract_file_path_from_prompt("[file: main.py] buat") == "main.py"

    def test_natural_language_file_keyword(self):
        prompt = "Buatkan file hello.py yang mencetak Halo"
        assert extract_file_path_from_prompt(prompt) == "hello.py"
        assert detect_path_source(prompt) == "natural_language"

    def test_natural_language_berkas_keyword(self):
        prompt = "Buatkan berkas config.yaml untuk database"
        assert extract_file_path_from_prompt(prompt) == "config.yaml"
        assert detect_path_source(prompt) == "natural_language"

    def test_natural_language_named_keyword(self):
        prompt = "Buat script bernama backup.sh untuk MySQL"
        assert extract_file_path_from_prompt(prompt) == "backup.sh"
        assert detect_path_source(prompt) == "natural_language"

    def test_natural_language_simpan_ke(self):
        prompt = "Simpan ke src/app.py ya"
        assert extract_file_path_from_prompt(prompt) == "src/app.py"

    def test_backtick_quoted_filename(self):
        prompt = "Buatkan file " + BT + "app.js" + BT + " untuk backend Express"
        assert extract_file_path_from_prompt(prompt) == "app.js"
        assert detect_path_source(prompt) == "natural_language"

    def test_standalone_filename_with_extension(self):
        prompt = "Tolong buatkan index.html untuk landing page"
        assert extract_file_path_from_prompt(prompt) == "index.html"
        assert detect_path_source(prompt) == "natural_language"

    def test_fallback_manual_priority_3(self):
        prompt = "Tolong buatkan script untuk backup database"
        assert extract_file_path_from_prompt(prompt) is None
        assert detect_path_source(prompt) == "manual"

    def test_empty_prompt(self):
        assert extract_file_path_from_prompt("") is None
        assert detect_path_source("") == "manual"

    def test_none_prompt(self):
        assert extract_file_path_from_prompt(None) is None
        assert detect_path_source(None) == "manual"

    def test_case_insensitive(self):
        assert extract_file_path_from_prompt("Buatkan FILE Hello.py yang mencetak Halo") == "Hello.py"

    def test_multiple_extensions(self):
        cases = [
            ("Buat file script.py", "script.py"),
            ("Buat file app.js", "app.js"),
            ("Buat file style.css", "style.css"),
            ("Buat file config.json", "config.json"),
            ("Buat file data.yaml", "data.yaml"),
            ("Buat file readme.md", "readme.md"),
            ("Buat file backup.sh", "backup.sh"),
            ("Buat file main.cpp", "main.cpp"),
        ]
        for prompt, expected in cases:
            assert extract_file_path_from_prompt(prompt) == expected, prompt

    def test_priority_explicit_over_natural_language(self):
        prompt = "[FILE: correct.py] Buatkan file wrong.py"
        assert extract_file_path_from_prompt(prompt) == "correct.py"
        assert detect_path_source(prompt) == "explicit"


class TestDetectLanguageFromContent:
    """Test suite untuk detect_language_from_content()"""

    def test_detect_python_def(self):
        assert detect_language_from_content("def hello():\n    print('Hello')") == "python"

    def test_detect_python_import(self):
        assert detect_language_from_content("import os\nimport sys") == "python"

    def test_detect_javascript_function(self):
        assert detect_language_from_content("function hello() {\n  console.log('Hi');\n}") == "javascript"

    def test_detect_javascript_const(self):
        assert detect_language_from_content("const x = 10;\nconst y = 20;") == "javascript"

    def test_detect_bash_shebang(self):
        assert detect_language_from_content("#!/bin/bash\necho 'Hello'") == "bash"

    def test_detect_json(self):
        assert detect_language_from_content('{"key": "value"}') == "json"

    def test_detect_plaintext(self):
        assert detect_language_from_content("Just some random text") == "plaintext"

    def test_empty_content(self):
        assert detect_language_from_content("") == "plaintext"


class TestEnhanceCodeBlocks:
    """Test suite untuk enhance_code_blocks()"""

    def test_enhance_plaintext_block(self):
        blocks = [{"language": "plaintext", "content": "def hello():\n    print('Hello')"}]
        assert enhance_code_blocks(blocks)[0]["language"] == "python"

    def test_preserve_labeled_block(self):
        blocks = [{"language": "javascript", "content": "console.log('Hello')"}]
        assert enhance_code_blocks(blocks)[0]["language"] == "javascript"

    def test_input_not_mutated(self):
        blocks = [{"language": "plaintext", "content": "import os"}]
        enhance_code_blocks(blocks)
        assert blocks[0]["language"] == "plaintext"


class TestIntegrationScenarios:
    """Integration test skenario Blueprint Fase 3"""

    def test_skenario_1_explicit_format(self):
        hermes_prompt = '[FILE: hello.py] Buatkan file yang mencetak "Halo dari Hermes!"'
        deepseek_response = "Berikut isi file:\n" + fence("python", "print('Halo dari Hermes!')")

        path = extract_file_path_from_prompt(hermes_prompt)
        source = detect_path_source(hermes_prompt)
        blocks = extract_code_blocks(deepseek_response)

        assert path == "hello.py"
        assert source == "explicit"
        assert len(blocks) == 1
        assert blocks[0]["language"] == "python"
        assert "Halo dari Hermes!" in blocks[0]["content"]

    def test_skenario_2_natural_language(self):
        hermes_prompt = 'Buatkan file hello.py yang mencetak "Halo"'
        deepseek_response = fence("python", "print('Halo')")

        assert extract_file_path_from_prompt(hermes_prompt) == "hello.py"
        assert detect_path_source(hermes_prompt) == "natural_language"
        assert len(extract_code_blocks(deepseek_response)) == 1

    def test_skenario_3_ambiguous_fallback(self):
        hermes_prompt = "Tolong buatkan script untuk backup database"
        assert extract_file_path_from_prompt(hermes_prompt) is None
        assert detect_path_source(hermes_prompt) == "manual"

    def test_skenario_4_unlabeled_block_enhanced(self):
        deepseek_response = fence("", "def run():\n    return 42")
        blocks = enhance_code_blocks(extract_code_blocks(deepseek_response))
        assert blocks[0]["language"] == "python"


class TestSourceHasNoLiteralFence:
    """Jaga-jaga: source parser.py tidak boleh memuat tiga backtick literal."""

    def test_parser_source_clean(self):
        import app.parser as parser_module
        with open(parser_module.__file__, "r", encoding="utf-8") as handle:
            source = handle.read()
        # Pastikan tidak ada triple backtick literal
        assert FENCE not in source, "Source file tidak boleh memuat triple backtick literal"
        # Tidak perlu mengharuskan backtick tunggal ada, karena bisa dibangun via chr(96)