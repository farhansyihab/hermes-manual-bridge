"""
Modul D: Code Parser & Path Extractor (Fase 3)

Menyediakan:
- extract_code_blocks()          : deteksi blok kode berpagar (fenced) dari respons DeepSeek
- extract_file_path_from_prompt(): ekstrak path file dari prompt Hermes (hierarki 3 prioritas)
- detect_path_source()           : indikator sumber path untuk UI
- detect_language_from_content() : tebak bahasa dari isi kode
- enhance_code_blocks()          : lengkapi label bahasa yang kosong

Catatan penting:
    Semua karakter pagar kode (backtick) dibangun lewat chr(96) agar source file
    ini tidak pernah memuat urutan tiga backtick literal. Ini menjaga file tetap
    utuh saat dikirim lewat tool yang memakai fenced code block.
"""
import re
from typing import List, Dict, Optional

# Backtick tunggal dan pagar tiga karakter, dibangun secara programatik.
BT = chr(96)
FENCE = BT * 3

# Pola nama file / path relatif: wajib punya ekstensi.
_PATH = r"[A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z0-9]+"

# Ekstensi umum untuk deteksi filename yang berdiri sendiri.
_EXT = (
    r"py|js|ts|jsx|tsx|html|css|scss|json|yaml|yml|toml|ini|cfg|md|txt|csv|sql|"
    r"sh|bash|cpp|cc|c|h|hpp|java|go|rs|rb|php|lua|xml|env"
)

# PRIORITAS 1: format eksplisit yang di-instruct ke Hermes, mis. [FILE: src/main.py]
_EXPLICIT_RE = re.compile(r"\[FILE:\s*([^\]]+)\]", re.IGNORECASE)

# PRIORITAS 2: pola bahasa natural (backward compatibility dengan prompt lama).
_NL_PATTERNS = [
    # "file hello.py" / "berkas config.yaml"
    re.compile(rf"(?:file|berkas)\s+{BT}?({_PATH}){BT}?", re.IGNORECASE),
    # "named app.js" / "bernama backup.sh" / "dengan nama app.js"
    re.compile(rf"(?:named|bernama|dengan\s+nama)\s+{BT}?({_PATH}){BT}?", re.IGNORECASE),
    # "simpan ke src/app.py" / "save to src/app.py"
    re.compile(rf"(?:simpan\s+ke|save\s+to|tulis\s+ke)\s+{BT}?({_PATH}){BT}?", re.IGNORECASE),
    # nama file dikutip backtick tunggal
    re.compile(rf"{BT}({_PATH}){BT}"),
    # nama file berdiri sendiri dengan ekstensi dikenal
    re.compile(rf"\b([A-Za-z0-9_\-]+\.(?:{_EXT}))\b", re.IGNORECASE),
]

# Pola blok kode berpagar: pagar, label bahasa opsional, newline, isi, pagar tutup.
_CODE_BLOCK_RE = re.compile(
    re.escape(FENCE) + r"[ \t]*([A-Za-z0-9_+.\-]*)[ \t]*\r?\n(.*?)" + re.escape(FENCE),
    re.DOTALL,
)


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    Deteksi semua blok kode berpagar dalam respons DeepSeek.

    Args:
        text: Teks respons yang mungkin mengandung blok kode.

    Returns:
        List dict berstruktur: [{"language": "python", "content": "..."}, ...]
        Blok tanpa label bahasa diberi language "plaintext".
        Isi blok di-strip dari whitespace di awal/akhir.
    """
    if not text:
        return []

    blocks: List[Dict[str, str]] = []
    for lang, content in _CODE_BLOCK_RE.findall(text):
        blocks.append({
            "language": (lang or "").strip().lower() or "plaintext",
            "content": content.strip(),
        })
    return blocks


def extract_file_path_from_prompt(prompt: str) -> Optional[str]:
    """
    Ekstrak path file dari prompt Hermes dengan strategi hierarkis.

    Prioritas 1: format eksplisit [FILE: path]
    Prioritas 2: pola bahasa natural (file/berkas/named/bernama, kutipan backtick,
                 atau nama file berekstensi yang berdiri sendiri)
    Prioritas 3: return None, UI menampilkan dialog input path manual

    Args:
        prompt: Prompt dari Hermes Agent.

    Returns:
        String path bila terdeteksi, None bila tidak.

    Contoh:
        >>> extract_file_path_from_prompt("[FILE: hello.py] Buatkan file")
        'hello.py'
        >>> extract_file_path_from_prompt("Buatkan file hello.py yang mencetak Halo")
        'hello.py'
        >>> extract_file_path_from_prompt("Tolong buatkan script backup") is None
        True
    """
    if not prompt:
        return None

    # PRIORITAS 1
    explicit = _EXPLICIT_RE.search(prompt)
    if explicit:
        path = explicit.group(1).strip().strip(BT).strip()
        if path:
            return path

    # PRIORITAS 2
    for pattern in _NL_PATTERNS:
        match = pattern.search(prompt)
        if match:
            path = match.group(1).strip()
            if path:
                return path

    # PRIORITAS 3
    return None


def detect_path_source(prompt: str) -> str:
    """
    Tentukan sumber path untuk indikator di UI.

    Returns:
        "explicit"         -> dari format [FILE: path]
        "natural_language" -> dari pola bahasa natural
        "manual"           -> tidak terdeteksi, perlu input manual
    """
    if not prompt:
        return "manual"

    explicit = _EXPLICIT_RE.search(prompt)
    if explicit and explicit.group(1).strip().strip(BT).strip():
        return "explicit"

    for pattern in _NL_PATTERNS:
        if pattern.search(prompt):
            return "natural_language"

    return "manual"


def detect_language_from_content(content: str) -> str:
    """
    Tebak bahasa pemrograman dari isi kode bila label bahasa tidak tersedia.

    Returns:
        Salah satu: python, javascript, bash, json, plaintext.
    """
    if not content:
        return "plaintext"

    text = content.strip()

    # Python
    if re.search(r"\bdef\s+\w+\s*\(", text) or re.search(r"^\s*(import|from)\s+\w+", text, re.MULTILINE):
        return "python"

    # JavaScript
    if re.search(r"\bfunction\s+\w+\s*\(", text) or re.search(r"\b(const|let|var)\s+\w+\s*=", text):
        return "javascript"

    # Bash
    if text.startswith("#!") and ("bash" in text.splitlines()[0] or "sh" in text.splitlines()[0]):
        return "bash"
    if re.search(r"^\s*(echo|fi|done|then)\b", text, re.MULTILINE):
        return "bash"

    # JSON
    if re.match(r"^[\{\[]", text) and re.search(r"[\}\]]$", text):
        return "json"

    return "plaintext"


def enhance_code_blocks(blocks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Lengkapi label bahasa yang kosong/plaintext lewat deteksi isi kode.

    Tidak mengubah list input (setiap dict disalin lebih dulu).
    """
    enhanced: List[Dict[str, str]] = []
    for block in blocks:
        item = dict(block)
        if item.get("language", "plaintext") in ("", "plaintext"):
            item["language"] = detect_language_from_content(item.get("content", ""))
        enhanced.append(item)
    return enhanced