# 🚀 Hermes Manual Bridge

**Human-in-the-Loop Middleware untuk Hermes Agent & DeepSeek Chat**

Hermes Manual Bridge adalah middleware web lokal yang menjadi jembatan antara [Hermes Agent](https://hermes-agent.nousresearch.com/) (Nous Research) dan DeepSeek Chat, memungkinkan Anda menggunakan model LLM cloud dengan kontrol penuh atas penulisan file ke sistem lokal.

## 📋 Daftar Isi

- [Tentang Proyek](#-tentang-proyek)
- [Fitur Utama](#-fitur-utama)
- [Cara Kerja](#-cara-kerja)
- [Instalasi](#-instalasi)
- [Konfigurasi Hermes](#-konfigurasi-hermes)
- [Penggunaan](#-penggunaan)
- [Keamanan](#-keamanan)
- [Struktur Proyek](#-struktur-proyek)
- [Status Pengembangan](#-status-pengembangan)
- [Kontribusi](#-kontribusi)
- [Lisensi](#-lisensi)

## 🎯 Tentang Proyek

### Mengapa Proyek Ini Dibuat?

1. **Edukasi**: Memahami cara kerja AI agent dan prompt engineering
2. **Kepatuhan**: Mematuhi Terms of Service DeepSeek dengan copy-paste manual
3. **Kontrol Penuh**: Setiap penulisan file ke hardisk harus disetujui user (sandbox manual)
4. **Optimasi Hardware**: Inferensi berat berjalan di cloud, bukan di laptop lokal
5. **Fleksibilitas**: Menggunakan model LLM terbaik tanpa vendor lock-in

### Konsep Dasar

Hermes Agent dikonfigurasi untuk mengirim request ke middleware lokal (`http://localhost:8000/v1`) alih-alih ke LLM sungguhan. User kemudian:

1. Menyalin prompt dari middleware ke DeepSeek Chat di browser
2. Menempelkan jawaban DeepSeek kembali ke middleware
3. Menyetujui atau menolak penulisan file melalui preview interaktif

Middleware meneruskan jawaban ke Hermes dalam format OpenAI Chat Completions yang valid.

## ✨ Fitur Utama

### ✅ Fase 1 & 2 (Selesai)

- **Mock OpenAI Gateway**: Endpoint `/v1/chat/completions` dengan mekanisme hold & wait
- **Web UI Dashboard**: Interface modern untuk copy-paste prompt dan respons
- **History Log**: Riwayat percakapan tersimpan di SQLite
- **Syntax Highlighting**: Preview kode dengan Prism.js
- **Edit Prompt**: Modifikasi prompt sebelum dikirim ke DeepSeek
- **Draft Management**: Draft jawaban tersimpan di localStorage untuk mencegah kehilangan data

### 🚀 Fase 3 (Selesai)

- **Code Parser Otomatis**: Deteksi blok kode dari respons DeepSeek
- **Path Extractor Hierarkis**: Ekstraksi target file dengan 3 prioritas:
  1. Format eksplisit `[FILE: path]` (~100% akurasi)
  2. Pola bahasa natural (`file hello.py`, `berkas config.yaml`, dll)
  3. Input manual via dialog UI
- **Sandbox Approval UI**: Preview interaktif dengan info lengkap:
  - Nama file dan path
  - Sumber path (eksplisit/natural/manual)
  - Bahasa pemrograman
  - Ukuran file (karakter & baris)
  - Isi kode dengan syntax highlighting
- **Keamanan Path**: Whitelist direktori, validasi ekstensi, blokir path traversal
- **Fallback Graceful**: Jika parsing gagal, kembali ke mode teks biasa tanpa error
- **Tool Call Builder**: Membungkus kode ke format OpenAI tool call `write_file`

## 🔄 Cara Kerja

### Alur Fase 1 (Teks Biasa)

```
Hermes Agent
    ↓ POST /v1/chat/completions
Middleware (FastAPI)
    ↓ Tahan koneksi (asyncio.Event)
User copy prompt → DeepSeek Chat
    ↓
User paste respons → Middleware
    ↓ POST /submit_response
Middleware bungkus ke JSON OpenAI
    ↓ HTTP 200
Hermes Agent menerima respons
```

### Alur Fase 3 (Parsing Otomatis & Write File)

```
Hermes Agent
    ↓ POST /v1/chat/completions
    ↓ Prompt: "[FILE: hello.py] Buatkan file..."
Middleware
    ↓ Ekstrak path: "hello.py" (explicit)
    ↓ Tahan koneksi
User copy prompt → DeepSeek Chat
    ↓
User paste respons (dengan kode) → Middleware
    ↓ Deteksi blok kode
    ↓ Tampilkan preview di UI
User review & klik "Izinkan"
    ↓ POST /submit_response (is_tool_call=true)
Middleware bungkus ke tool call write_file
    ↓ HTTP 200
Hermes Agent menerima tool call
    ↓
Hermes menulis file ke hardisk
```

## 📦 Instalasi

### Prasyarat

- Python 3.12+
- Hermes Agent v0.23.0+ ([unduh di sini](https://hermes-agent.nousresearch.com/))
- Git

### Langkah Instalasi

1. **Clone repository**

```bash
git clone https://github.com/farhansyihab/hermes-manual-bridge.git
cd hermes-manual-bridge
```

2. **Buat virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows
```

3. **Install dependencies**

```bash
pip install -r middleware/requirements.txt
```

4. **Jalankan middleware**

```bash
cd middleware
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Middleware akan berjalan di `http://localhost:8000`

## ⚙️ Konfigurasi Hermes

Edit file `~/.hermes/config.yaml`:

```yaml
model:
  default: "deepseek-manual"
  provider: "custom"
  base_url: "http://localhost:8000/v1"
  streaming: false   # WAJIB false

agent:
  system_prompt: |
    Kamu adalah asisten yang membantu user membuat file kode.
    PENTING: Setiap kali kamu meminta pembuatan file, WAJIB awali
    permintaan dengan format eksplisit:
    [FILE: path/ke/file.ext]
    Contoh:
    [FILE: scripts/backup.sh]
    Buatkan bash script untuk backup database MySQL...
    
    Format ini membantu middleware mendeteksi target file dengan akurat.
```

**Catatan**: Set timeout Hermes ke 1800 detik karena koneksi ditahan sampai user mengirim jawaban.

## 🖥️ Penggunaan

### 1. Akses Web UI

Buka browser ke `http://localhost:8000`

### 2. Tunggu Prompt dari Hermes

Dashboard akan menampilkan prompt dari Hermes Agent secara real-time (polling setiap 2 detik).

### 3. Copy Prompt ke DeepSeek

Salin teks dari "Prompt dari Hermes Agent" dan paste ke DeepSeek Chat di tab browser lain.

### 4. Paste Respons DeepSeek

Setelah DeepSeek memberikan jawaban, salin dan tempel ke "Jawaban dari DeepSeek".

### 5. Review & Approve (Fase 3)

Jika respons mengandung kode:

- **Sandbox Approval Panel** muncul otomatis
- Review: nama file, bahasa, ukuran, isi kode
- Pilih tindakan:
  - ✅ **Izinkan & Kirim**: Kirim sebagai tool call `write_file`
  - ✏️ **Edit & Izinkan**: Edit kode dulu, lalu kirim
  - ❌ **Tolak**: Kirim pesan penolakan ke Hermes
  - 📝 **Kirim sebagai Teks Biasa**: Fallback mode (tanpa tool call)

### 6. Kirim ke Hermes

Klik tombol "Kirim ke Hermes" atau tombol approval. Middleware akan melepaskan koneksi dan mengirim respons ke Hermes.

## 🔒 Keamanan

### Whitelist Direktori

Hanya file di dalam direktori yang di-whitelist yang boleh ditulis:

```python
WHITELISTED_DIRECTORIES = [
    "/home/farhan/Proyek/Hermes"  # Ganti dengan path project Anda
]
```

### Validasi Path

- ✅ Path relatif diizinkan
- ❌ Path absolut mencurigakan (`/etc/`, `/root/`, dll) diblokir
- ❌ Path traversal (`..`) diblokir
- ❌ Ekstensi tidak dikenal diblokir

### Approval Gate

**Tidak ada penulisan file tanpa persetujuan eksplisit user.** Setiap tool call `write_file` harus melewati preview dan approval di Web UI.

### Ukuran File

- Maksimum: 5 MB atau 10.000 baris
- File terlalu besar akan ditolak

## 📁 Struktur Proyek

```
hermes-manual-bridge/
├── middleware/
│   ├── app/
│   │   ├── main.py              # Entry point FastAPI
│   │   ├── config.py            # Konfigurasi keamanan
│   │   ├── parser.py            # Code parser & path extractor
│   │   ├── path_extractor.py    # Validasi path & whitelist
│   │   ├── detect_path_source.py # Deteksi sumber path
│   │   ├── tool_call_builder.py # Builder untuk tool call
│   │   ├── state.py             # State management (asyncio.Event)
│   │   ├── database.py          # SQLite connection
│   │   ├── history.py           # History service
│   │   └── routers/
│   │       ├── chat.py          # /v1/chat/completions
│   │       ├── ui.py            # Web UI
│   │       ├── history.py       # History endpoints
│   │       └── approval.py      # Approval & validation
│   ├── static/
│   │   ├── style.css
│   │   └── js/
│   │       ├── main.js
│   │       ├── parser.js
│   │       ├── approval.js
│   │       └── ...
│   ├── tests/                   # Unit tests (pytest)
│   └── data/
│       └── history.db           # SQLite database (auto-created)
├── Project.md                   # Dokumen konteks untuk AI
└── README.md                    # File ini
```

## 📊 Status Pengembangan

| Fase | Status | Deskripsi |
|------|--------|-----------|
| **Fase 1** | ✅ Selesai | Foundation: Mock gateway, Web UI dasar, alur teks biasa |
| **Fase 2** | ✅ Selesai | Robustness: History log, syntax highlighting, edit prompt, draft |
| **Fase 3** | ✅ Selesai | Advanced: Code parser, path extractor, approval UI, keamanan |
| **Fase 4** | 🔲 Belum dimulai | Hybrid: API key fallback, dashboard analitik, multiple tool calls |

### Kriteria Keberhasilan Fase 3

- ✅ Deteksi blok kode dengan akurasi > 90%
- ✅ Ekstraksi path format `[FILE: path]` dengan akurasi ~100%
- ✅ Backward compatibility dengan prompt lama (regex NL)
- ✅ User dapat approve/reject setiap tool call
- ✅ Hermes berhasil menulis file setelah approval
- ✅ Tidak ada regresi pada Fase 1

## 🧪 Testing

Jalankan unit tests:

```bash
cd middleware
pytest tests/ -v
```

Test spesifik:

```bash
pytest tests/test_parser.py -v
pytest tests/test_path_extractor.py -v
pytest tests/test_detect_path_source.py -v
```

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan:

1. Fork repository ini
2. Buat branch fitur (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buka Pull Request

### Konvensi Pengembangan

- Bahasa: Komentar dan dokumentasi dalam Bahasa Indonesia
- Python: Type hints, docstring, PEP 8
- Git: Commit kecil dengan pesan jelas
- Keamanan: Jangan commit `history.db` atau file rahasia

## 📄 Lisensi

Proyek ini dibuat untuk tujuan edukasi dan penggunaan pribadi.

## 🙏 Acknowledgments

- [Hermes Agent](https://hermes-agent.nousresearch.com/) - Nous Research
- [DeepSeek Chat](https://chat.deepseek.com/) - DeepSeek
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web modern
- [Prism.js](https://prismjs.com/) - Syntax highlighting

## 📞 Kontak

Untuk pertanyaan atau saran, silakan buka issue di repository ini.

---

**Catatan**: Proyek ini masih dalam pengembangan aktif. Fitur dan API dapat berubah tanpa pemberitahuan.
