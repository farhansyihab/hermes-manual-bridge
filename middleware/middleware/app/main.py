from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import sqlite3
import json
import os
from datetime import datetime

# ==========================================
# 0. HISTORY MANAGER (Fase 2: Robustness)
# ==========================================
class HistoryManager:
    def __init__(self, db_path="chat_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            ''')
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[Error] Gagal menginisialisasi database: {e}")

    def save_message(self, role: str, content: str):
        timestamp = datetime.now().isoformat()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO history (timestamp, role, content) VALUES (?, ?, ?)', (timestamp, role, content))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[Error] Gagal menyimpan pesan: {e}")

    def get_history(self, limit: Optional[int] = None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if limit:
                cursor.execute('SELECT role, content FROM history ORDER BY id DESC LIMIT ?', (limit,))
                rows = cursor.fetchall()
                rows.reverse() # Urutkan dari lama ke baru untuk ditampilkan
            else:
                cursor.execute('SELECT role, content FROM history ORDER BY id ASC')
                rows = cursor.fetchall()
            conn.close()
            return [{'role': row[0], 'content': row[1]} for row in rows]
        except sqlite3.Error as e:
            print(f"[Error] Gagal mengambil riwayat: {e}")
            return []

    def export_to_json(self, filepath: str = "chat_history_export.json"):
        history = self.get_history()
        try:
            abs_path = os.path.abspath(filepath)
            with open(abs_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return abs_path
        except IOError as e:
            print(f"[Error] Gagal mengekspor ke JSON: {e}")
            return None

    def clear_history(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM history')
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted_count
        except sqlite3.Error as e:
            print(f"[Error] Gagal menghapus riwayat: {e}")
            return 0

# Inisialisasi global
history_mgr = HistoryManager(db_path="chat_history.db")

# ==========================================
# 1. STATE MANAGEMENT
# ==========================================
class BridgeState:
    def __init__(self):
        self.current_prompt: Optional[str] = None
        self.response_event = asyncio.Event()
        self.final_response: Optional[Dict[str, Any]] = None
        self.is_waiting: bool = False

state = BridgeState()

# ==========================================
# 2. PYDANTIC MODELS (OpenAI Compatible)
# ==========================================
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

# ==========================================
# 3. FASTAPI APP INITIALIZATION
# ==========================================
app = FastAPI(
    title="Hermes Manual Bridge",
    description="Human-in-the-Loop Middleware untuk Hermes Agent <-> DeepSeek",
    version="0.2.0" # Updated version for Phase 2
)

# ==========================================
# 4. WEB UI DASHBOARD (Modul B + History UI)
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def web_ui():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hermes Manual Bridge Dashboard</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; background-color: #f4f4f9; color: #333; }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ddd; padding-bottom: 1rem; margin-bottom: 1.5rem; }
            .status { padding: 0.5rem 1rem; border-radius: 4px; font-weight: bold; font-size: 0.9rem; }
            .status-idle { background-color: #e0e0e0; color: #555; }
            .status-waiting { background-color: #fff3cd; color: #856404; animation: pulse 2s infinite; }
            .status-sent { background-color: #d4edda; color: #155724; }
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
            .container { display: flex; flex-direction: column; gap: 1.5rem; }
            .box { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            label { display: block; font-weight: bold; margin-bottom: 0.5rem; color: #555; }
            textarea { width: 100%; min-height: 150px; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; font-family: "Courier New", Courier, monospace; font-size: 0.9rem; box-sizing: border-box; resize: vertical; }
            textarea[readonly] { background-color: #f8f9fa; color: #495057; }
            button { background-color: #007bff; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 4px; font-size: 1rem; cursor: pointer; transition: background 0.2s; }
            button:hover { background-color: #0056b3; }
            button:disabled { background-color: #ccc; cursor: not-allowed; }
            .hint { font-size: 0.85rem; color: #666; margin-top: 0.5rem; }
            .btn-group { display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
            .btn-sm { padding: 0.5rem 1rem; font-size: 0.9rem; }
            .btn-success { background-color: #28a745; }
            .btn-success:hover { background-color: #218838; }
            .btn-info { background-color: #17a2b8; }
            .btn-info:hover { background-color: #138496; }
            .btn-danger { background-color: #dc3545; }
            .btn-danger:hover { background-color: #c82333; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Hermes Manual Bridge</h1>
            <span id="statusBadge" class="status status-idle">Menunggu Hermes...</span>
        </div>
        <div class="container">
            <div class="box">
                <label for="promptArea">📥 Prompt dari Hermes Agent:</label>
                <textarea id="promptArea" readonly placeholder="Belum ada prompt masuk..."></textarea>
                <div class="hint">💡 Copy teks di atas dan paste ke DeepSeek Chat di tab browser lain.</div>
            </div>
            <div class="box">
                <label for="responseArea">📤 Jawaban dari DeepSeek (Paste di sini):</label>
                <textarea id="responseArea" placeholder="Paste jawaban DeepSeek di sini..."></textarea>
                <div class="hint">💡 Setelah paste, klik tombol di bawah untuk mengirim ke Hermes.</div>
                <br>
                <button id="submitBtn" onclick="submitResponse()" disabled>Kirim ke Hermes</button>
            </div>
            
            <!-- FITUR BARU: RIWAYAT PERCAKAPAN -->
            <div class="box">
                <label>📜 Riwayat Percakapan:</label>
                <div class="btn-group">
                    <button class="btn-sm btn-success" onclick="loadHistory()">Muat Riwayat</button>
                    <button class="btn-sm btn-info" onclick="exportHistory()">Ekspor ke JSON</button>
                    <button class="btn-sm btn-danger" onclick="clearHistory()">Hapus Riwayat</button>
                </div>
                <textarea id="historyArea" readonly style="min-height: 200px; font-size: 0.85rem;" placeholder="Klik 'Muat Riwayat' untuk melihat percakapan tersimpan..."></textarea>
            </div>
        </div>
        <script>
            const promptArea = document.getElementById('promptArea');
            const responseArea = document.getElementById('responseArea');
            const submitBtn = document.getElementById('submitBtn');
            const statusBadge = document.getElementById('statusBadge');
            const historyArea = document.getElementById('historyArea');

            responseArea.addEventListener('input', () => {
                localStorage.setItem('hermes_draft_response', responseArea.value);
                submitBtn.disabled = responseArea.value.trim() === '';
            });

            window.addEventListener('load', () => {
                const savedDraft = localStorage.getItem('hermes_draft_response');
                if (savedDraft) {
                    responseArea.value = savedDraft;
                    submitBtn.disabled = savedDraft.trim() === '';
                }
                checkPrompt();
                loadHistory(); // Muat riwayat saat halaman dibuka
            });

            setInterval(checkPrompt, 2000);

            async function checkPrompt() {
                try {
                    const res = await fetch('/get_prompt');
                    const data = await res.json();
                    if (data.status === 'waiting' && data.prompt) {
                        if (promptArea.value !== data.prompt) {
                            promptArea.value = data.prompt;
                            statusBadge.textContent = '⏳ Prompt Diterima! Menunggu Jawaban Anda...';
                            statusBadge.className = 'status status-waiting';
                        }
                    } else {
                        statusBadge.textContent = '✅ Menunggu Hermes...';
                        statusBadge.className = 'status status-idle';
                    }
                } catch (err) {
                    console.error('Gagal mengecek prompt:', err);
                }
            }

            async function submitResponse() {
                const userResponse = responseArea.value.trim();
                if (!userResponse) return;
                submitBtn.disabled = true;
                submitBtn.textContent = 'Mengirim...';
                statusBadge.textContent = '📤 Mengirim ke Hermes...';
                statusBadge.className = 'status status-waiting';
                try {
                    const res = await fetch('/submit_response', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ response: userResponse })
                    });
                    if (res.ok) {
                        statusBadge.textContent = '🎉 Berhasil Dikirim! Menunggu tugas berikutnya...';
                        statusBadge.className = 'status status-sent';
                        responseArea.value = '';
                        localStorage.removeItem('hermes_draft_response');
                        submitBtn.disabled = true;
                        submitBtn.textContent = 'Kirim ke Hermes';
                        setTimeout(() => {
                            statusBadge.textContent = '✅ Menunggu Hermes...';
                            statusBadge.className = 'status status-idle';
                        }, 3000);
                        loadHistory(); // Refresh riwayat setelah kirim
                    } else {
                        alert('Gagal mengirim respons. Coba lagi.');
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Kirim ke Hermes';
                    }
                } catch (err) {
                    console.error('Error submitting:', err);
                    alert('Terjadi kesalahan jaringan.');
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Kirim ke Hermes';
                }
            }

            // --- FUNGSI RIWAYAT BARU ---
            async function loadHistory() {
                try {
                    const res = await fetch('/history?limit=20');
                    const data = await res.json();
                    if (data.length === 0) {
                        historyArea.value = "Belum ada riwayat percakapan.";
                        return;
                    }
                    historyArea.value = data.map(msg => `[${msg.role.toUpperCase()}]: ${msg.content}`).join('\n\n---\n\n');
                } catch (err) {
                    console.error('Gagal memuat riwayat:', err);
                }
            }

            async function exportHistory() {
                try {
                    const res = await fetch('/history/export', { method: 'POST' });
                    const data = await res.json();
                    if (data.status === 'ok') {
                        alert('Berhasil diekspor ke: ' + data.filepath);
                    } else {
                        alert('Gagal mengekspor: ' + (data.detail || 'Unknown error'));
                    }
                } catch (err) {
                    console.error('Gagal mengekspor:', err);
                }
            }

            async function clearHistory() {
                if (!confirm('Apakah Anda yakin ingin menghapus SEMUA riwayat percakapan? Tindakan ini tidak dapat dibatalkan.')) return;
                try {
                    const res = await fetch('/history/clear', { method: 'POST' });
                    const data = await res.json();
                    if (data.status === 'ok') {
                        alert('Riwayat berhasil dihapus.');
                        historyArea.value = 'Belum ada riwayat percakapan.';
                    } else {
                        alert('Gagal menghapus: ' + (data.detail || 'Unknown error'));
                    }
                } catch (err) {
                    console.error('Gagal menghapus:', err);
                }
            }
        </script>
    </body>
    </html>
    """

# ==========================================
# 5. API ENDPOINTS
# ==========================================
@app.get("/get_prompt")
async def get_prompt():
    if state.current_prompt:
        return {"prompt": state.current_prompt, "status": "waiting"}
    return {"prompt": None, "status": "idle"}

@app.post("/submit_response")
async def submit_response(request: Request):
    body = await request.json()
    user_response = body.get("response", "")
    
    # SIMPAN KE RIWAYAT
    history_mgr.save_message("assistant", user_response)
    
    state.final_response = {
        "id": "chatcmpl-manual-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "deepseek-manual",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": user_response
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }
    state.response_event.set()
    return {"status": "submitted", "message": "Respons dikirim ke Hermes"}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    last_message = request.messages[-1].content
    state.current_prompt = last_message
    
    # SIMPAN KE RIWAYAT
    history_mgr.save_message("user", last_message)
    
    state.response_event.clear()
    state.final_response = None
    state.is_waiting = True
    print(f"[Hermes Request] Prompt diterima: {last_message[:100]}...")
    
    try:
        await state.response_event.wait()
    except Exception as e:
        print(f"Error waiting for event: {e}")
    finally:
        state.is_waiting = False
        state.current_prompt = None
        
    return JSONResponse(content=state.final_response)

# ==========================================
# 6. HISTORY ENDPOINTS (Fase 2)
# ==========================================
@app.get("/history")
async def get_history(limit: Optional[int] = None):
    return history_mgr.get_history(limit=limit)

@app.post("/history/export")
async def export_history():
    filepath = history_mgr.export_to_json("chat_history_export.json")
    if filepath:
        return {"status": "ok", "filepath": filepath}
    return {"status": "error", "detail": "Gagal mengekspor"}

@app.post("/history/clear")
async def clear_history():
    count = history_mgr.clear_history()
    return {"status": "ok", "deleted_count": count}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "hermes-middleware"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)