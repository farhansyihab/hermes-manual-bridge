"""
Modul D (Fase 3): Path Source Detector untuk Hermes Manual Bridge.

Fungsi utama detect_path_source() menentukan dari mana path file berasal,
untuk ditampilkan sebagai indikator di Web UI (Modul E).

Hierarki deteksi:
  1. "explicit"         -> format [FILE: path] dari system prompt Hermes
  2. "natural_language" -> pola bahasa natural (backward compatibility)
  3. "manual"           -> tidak terdeteksi, UI minta input path manual

KONSISTENSI MODUL LAIN:
  Regex di sini direplikasi PERSIS dari app/parser.py agar kedua modul
  menghasilkan keputusan yang identik. Termasuk bug lama pada pola
  standalone filename (dot tidak di-escape). Lihat komentar "BUG LAMA"
  di bawah untuk lokasi perbaikan jika ingin meningkatkan akurasi.

Catatan: karakter backtick dibangun via chr(96) agar source file ini tidak
pernah memuat urutan tiga backtick literal.

Version: 1.0.3
"""

import re

__all__ = [
    "detect_path_source",
    "get_source_description",
    "get_source_icon",
    "get_source_color",
    "get_source_info",
    "BT",
    "FENCE",
]

BT = chr(96)
FENCE = BT * 3

# BUG LAMA (direplikasi dari parser.py): '.' di _PATH_PATTERN tidak di-escape
# sehingga berarti 'any character', bukan literal dot. Efek samping: "file hello"
# bisa match walau tanpa ekstensi, tetapi ini konsisten dengan parser.py.
_PATH_PATTERN = r"[A-Za-z0-9_][A-Za-z0-9_./-]*.[A-Za-z0-9]+"

_EXT = (
    r"py|js|ts|jsx|tsx|html|css|scss|json|yaml|yml|toml|ini|cfg|md|txt|csv|sql|"
    r"sh|bash|cpp|cc|c|h|hpp|java|go|rs|rb|php|lua|xml|env"
)

_EXPLICIT_RE = re.compile(r"\[FILE:\s*([^\]]+)\]", re.IGNORECASE)

_NL_PATTERNS = [
    re.compile(r"(?:file|berkas)\s+" + BT + r"?(" + _PATH_PATTERN + r")" + BT + r"?", re.IGNORECASE),
    re.compile(r"(?:named|bernama|dengan\s+nama)\s+" + BT + r"?(" + _PATH_PATTERN + r")" + BT + r"?", re.IGNORECASE),
    re.compile(r"(?:simpan\s+ke|save\s+to|tulis\s+ke)\s+" + BT + r"?(" + _PATH_PATTERN + r")" + BT + r"?", re.IGNORECASE),
    re.compile(BT + r"(" + _PATH_PATTERN + r")" + BT, re.IGNORECASE),
    # BUG LAMA (direplikasi dari parser.py): '.' di depan (?:{_EXT}) tidak di-escape.
    # Di parser.py: rf "\b([A-Za-z0-9_-]+.(?:{_EXT}))\b"
    # Ini kebetulan membuat 'index.html' match karena '.' regex cocok dengan literal dot.
    # Perbaikan (opsional, ubah juga di parser.py):
    #   r"\b([A-Za-z0-9_-]+(?:\.(?:" + _EXT + r")))\b"
    re.compile(r"\b([A-Za-z0-9_-]+.(?:" + _EXT + r"))\b", re.IGNORECASE),
]

_SOURCE_DESCRIPTIONS = {
    "explicit": "Format Eksplisit [FILE: ...]",
    "natural_language": "Pola Bahasa Natural",
    "manual": "Input Manual Diperlukan",
}

_SOURCE_ICONS = {
    "explicit": "\U0001F3AF",
    "natural_language": "\U0001F4AC",
    "manual": "\u270D\uFE0F",
}

_SOURCE_COLORS = {
    "explicit": "#28a745",
    "natural_language": "#ffc107",
    "manual": "#dc3545",
}


def detect_path_source(prompt):
    """
    Tentukan sumber path untuk indikator di UI.

    Args:
        prompt: Prompt dari Hermes Agent (string).

    Returns:
        "explicit" | "natural_language" | "manual"

    Contoh:
        detect_path_source("[FILE: hello.py] Buatkan file") -> "explicit"
        detect_path_source("Buatkan file hello.py")         -> "natural_language"
        detect_path_source("Tolong buatkan script backup")  -> "manual"
        detect_path_source(None)                            -> "manual"
    """
    if not prompt or not isinstance(prompt, str):
        return "manual"

    text = prompt.strip()
    if not text:
        return "manual"

    explicit = _EXPLICIT_RE.search(text)
    if explicit:
        path = explicit.group(1).strip().strip(BT).strip()
        if path:
            return "explicit"

    for pattern in _NL_PATTERNS:
        if pattern.search(text):
            return "natural_language"

    return "manual"


def get_source_description(source):
    """Deskripsi human-readable (Bahasa Indonesia) untuk sumber path."""
    return _SOURCE_DESCRIPTIONS.get(source, "Tidak Diketahui")


def get_source_icon(source):
    """Ikon emoji untuk indikator sumber path di UI."""
    return _SOURCE_ICONS.get(source, "\u2753")


def get_source_color(source):
    """Warna hex untuk styling indikator sumber path di UI."""
    return _SOURCE_COLORS.get(source, "#6c757d")


def get_source_info(source):
    """Kembalikan dict lengkap (source, description, icon, color) untuk JSON UI."""
    return {
        "source": source,
        "description": get_source_description(source),
        "icon": get_source_icon(source),
        "color": get_source_color(source),
    }


if __name__ == "__main__":
    samples = [
        "[FILE: hello.py] Buatkan file yang mencetak Halo",
        "[FILE: src/utils/helpers.py] Buatkan modul helper",
        "Buatkan file hello.py yang mencetak Halo",
        "Buatkan berkas config.yaml untuk database",
        "Buat script bernama backup.sh untuk MySQL",
        "Simpan ke src/app.py ya",
        "Buatkan file " + BT + "app.js" + BT + " untuk backend",
        "Tolong buatkan index.html untuk landing page",
        "Tolong buatkan script untuk backup database",
        "",
        None,
    ]
    for i, item in enumerate(samples, 1):
        src = detect_path_source(item)
        info = get_source_info(src)
        label = (str(item)[:55] or "(empty)")
        print(i, "|", src, "|", info["icon"], info["description"], "|", label)