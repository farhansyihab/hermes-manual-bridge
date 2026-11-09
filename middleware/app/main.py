from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

app = FastAPI(
    title="Hermes Manual Bridge",
    description="Human-in-the-Loop Middleware untuk Hermes Agent <-> DeepSeek",
    version="0.1.0"
)

# --- 1. STATE MANAGEMENT ---
class BridgeState:
    def __init__(self):
        self.current_prompt: Optional[str] = None
        self.response_event = asyncio.Event()
        self.final_response: Optional[Dict[str, Any]] = None
        self.is_waiting: bool = False

state = BridgeState()

# --- 2. PYDANTIC MODELS (OpenAI Compatible) ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

# --- 3. WEB UI DASHBOARD (Modul B) ---
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
        </div>

        <script>
            const promptArea = document.getElementById('promptArea');
            const responseArea = document.getElementById('responseArea');
            const submitBtn = document.getElementById('submitBtn');
            const statusBadge = document.getElementById('statusBadge');

            // Mitigasi Risiko: Simpan draft jawaban di localStorage agar tidak hilang saat refresh
            responseArea.addEventListener('input', () => {
                localStorage.setItem('hermes_draft_response', responseArea.value);
                submitBtn.disabled = responseArea.value.trim() === '';
            });

            // Muat draft saat halaman dibuka
            window.addEventListener('load', () => {
                const savedDraft = localStorage.getItem('hermes_draft_response');
                if (savedDraft) {
                    responseArea.value = savedDraft;
                    submitBtn.disabled = savedDraft.trim() === '';
                }
                checkPrompt(); // Cek segera saat load
            });

            // Polling setiap 2 detik untuk cek prompt baru
            setInterval(checkPrompt, 2000);

            async function checkPrompt() {
                try {
                    const res = await fetch('/get_prompt');
                    const data = await res.json();
                    
                    if (data.status === 'waiting' && data.prompt) {
                        // Hanya update jika prompt berubah, agar tidak mengganggu user
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
        </script>
    </body>
    </html>
    """

# --- 4. API ENDPOINTS ---

@app.get("/get_prompt")
async def get_prompt():
    if state.current_prompt:
        return {"prompt": state.current_prompt, "status": "waiting"}
    return {"prompt": None, "status": "idle"}

@app.post("/submit_response")
async def submit_response(request: Request):
    body = await request.json()
    user_response = body.get("response", "")
    
    # Bungkus ke format JSON standar OpenAI
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
    
    # Lepaskan kunci asyncio.Event
    state.response_event.set()
    return {"status": "submitted", "message": "Respons dikirim ke Hermes"}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    last_message = request.messages[-1].content
    state.current_prompt = last_message
    
    # Reset state untuk tugas baru
    state.response_event.clear()
    state.final_response = None
    state.is_waiting = True
    
    print(f"[Hermes Request] Prompt diterima: {last_message[:100]}...")
    
    # HOLD & WAIT
    try:
        await state.response_event.wait()
    except Exception as e:
        print(f"Error waiting for event: {e}")
    finally:
        state.is_waiting = False
        state.current_prompt = None
        
    return JSONResponse(content=state.final_response)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "hermes-middleware"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
