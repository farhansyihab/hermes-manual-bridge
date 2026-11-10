from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from .history import history_service

app = FastAPI(
    title="Hermes Manual Bridge",
    description="Human-in-the-Loop Middleware untuk Hermes Agent <-> DeepSeek",
    version="0.2.1"
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
    return r"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hermes Manual Bridge Dashboard</title>
    
    <!-- Prism.js CSS -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css" rel="stylesheet">
    
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            max-width: 900px; 
            margin: 2rem auto; 
            padding: 0 1rem; 
            background-color: #f4f4f9; 
            color: #333; 
        }
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            border-bottom: 2px solid #ddd; 
            padding-bottom: 1rem; 
            margin-bottom: 1.5rem; 
        }
        .status { 
            padding: 0.5rem 1rem; 
            border-radius: 4px; 
            font-weight: bold; 
            font-size: 0.9rem; 
        }
        .status-idle { 
            background-color: #e0e0e0; 
            color: #555; 
        }
        .status-waiting { 
            background-color: #fff3cd; 
            color: #856404; 
            animation: pulse 2s infinite; 
        }
        .status-sent { 
            background-color: #d4edda; 
            color: #155724; 
        }
        @keyframes pulse { 
            0% { opacity: 1; } 
            50% { opacity: 0.6; } 
            100% { opacity: 1; } 
        }
        .container { 
            display: flex; 
            flex-direction: column; 
            gap: 1.5rem; 
        }
        .box { 
            background: white; 
            padding: 1.5rem; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        label { 
            display: block; 
            font-weight: bold; 
            margin-bottom: 0.5rem; 
            color: #555; 
        }
        textarea { 
            width: 100%; 
            min-height: 150px; 
            padding: 0.75rem; 
            border: 1px solid #ccc; 
            border-radius: 4px; 
            font-family: "Courier New", Courier, monospace; 
            font-size: 0.9rem; 
            box-sizing: border-box; 
            resize: vertical; 
        }
        textarea[readonly] { 
            background-color: #f8f9fa; 
            color: #495057; 
        }
        button { 
            background-color: #007bff; 
            color: white; 
            border: none; 
            padding: 0.75rem 1.5rem; 
            border-radius: 4px; 
            font-size: 1rem; 
            cursor: pointer; 
            transition: background 0.2s; 
        }
        button:hover { 
            background-color: #0056b3; 
        }
        button:disabled { 
            background-color: #ccc; 
            cursor: not-allowed; 
        }
        .hint { 
            font-size: 0.85rem; 
            color: #666; 
            margin-top: 0.5rem; 
        }
        
        /* Tab Navigation */
        .tabs { 
            display: flex; 
            gap: 0.5rem; 
            margin-bottom: 1.5rem; 
            border-bottom: 2px solid #ddd; 
        }
        .tab { 
            padding: 0.75rem 1.5rem; 
            cursor: pointer; 
            border: none; 
            background: none; 
            font-size: 1rem; 
            color: #666; 
            border-bottom: 3px solid transparent; 
            transition: all 0.2s; 
        }
        .tab:hover { 
            color: #007bff; 
        }
        .tab.active { 
            color: #007bff; 
            border-bottom-color: #007bff; 
            font-weight: bold; 
        }
        .tab-content { 
            display: none; 
        }
        .tab-content.active { 
            display: block; 
        }
        
        /* History Styles */
        .history-item { 
            background: white; 
            padding: 1rem; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            margin-bottom: 1rem; 
        }
        .history-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 0.5rem; 
        }
        .history-id { 
            font-weight: bold; 
            color: #007bff; 
        }
        .history-time { 
            font-size: 0.85rem; 
            color: #666; 
        }
        .history-preview { 
            font-size: 0.9rem; 
            color: #555; 
            margin: 0.5rem 0; 
            white-space: nowrap; 
            overflow: hidden; 
            text-overflow: ellipsis; 
        }
        .history-details { 
            display: none; 
            margin-top: 1rem; 
            padding-top: 1rem; 
            border-top: 1px solid #eee; 
        }
        .history-details.show { 
            display: block; 
        }
        .history-section { 
            margin-bottom: 1rem; 
        }
        .history-section h4 { 
            margin: 0 0 0.5rem 0; 
            color: #333; 
        }
        .history-content { 
            background: #f8f9fa; 
            padding: 0.75rem; 
            border-radius: 4px; 
            font-family: monospace; 
            font-size: 0.85rem; 
            white-space: pre-wrap; 
            word-wrap: break-word; 
            max-height: 300px; 
            overflow-y: auto; 
        }
        .btn-small { 
            padding: 0.4rem 0.8rem; 
            font-size: 0.85rem; 
        }
        .btn-danger { 
            background-color: #dc3545; 
        }
        .btn-danger:hover { 
            background-color: #c82333; 
        }
        .btn-secondary { 
            background-color: #6c757d; 
        }
        .btn-secondary:hover { 
            background-color: #5a6268; 
        }
        .history-actions { 
            display: flex; 
            gap: 0.5rem; 
            margin-top: 0.5rem; 
        }
        .empty-state { 
            text-align: center; 
            padding: 3rem; 
            color: #999; 
        }
        
        /* Syntax Highlighting Preview */
        .preview-container {
            margin-top: 1rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }
        .preview-header {
            background: #2d2d2d;
            color: #fff;
            padding: 0.5rem 1rem;
            font-size: 0.85rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .preview-language {
            background: #007bff;
            padding: 0.2rem 0.6rem;
            border-radius: 3px;
            font-weight: bold;
        }
        .preview-content {
            max-height: 400px;
            overflow-y: auto;
            background: #2d2d2d;
        }
        .preview-content pre {
            margin: 0;
            padding: 1rem;
            background: #2d2d2d;
        }
        .preview-content code {
            font-size: 0.9rem;
            line-height: 1.5;
        }
        .no-code-hint {
            text-align: center;
            padding: 2rem;
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Hermes Manual Bridge</h1>
        <span id="statusBadge" class="status status-idle">Menunggu Hermes...</span>
    </div>
    
    <div class="tabs">
        <button class="tab active" onclick="switchTab('dashboard')">📊 Dashboard</button>
        <button class="tab" onclick="switchTab('history')">📜 Riwayat</button>
    </div>
    
    <!-- Dashboard Tab -->
    <div id="dashboard-tab" class="tab-content active">
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
                
                <!-- Preview dengan Syntax Highlighting -->
                <div id="codePreview" class="preview-container" style="display: none;">
                    <div class="preview-header">
                        <span>🔍 Preview Kode (Syntax Highlighted)</span>
                        <span id="previewLanguage" class="preview-language">auto</span>
                    </div>
                    <div class="preview-content">
                        <pre><code id="previewCode" class="line-numbers"></code></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- History Tab -->
    <div id="history-tab" class="tab-content">
        <div class="box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h2 style="margin: 0;">📜 Riwayat Percakapan</h2>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="btn-small btn-secondary" onclick="exportHistory()">📥 Export JSON</button>
                    <button class="btn-small btn-danger" onclick="clearHistory()">🗑️ Hapus Semua</button>
                </div>
            </div>
            <div id="historyList">
                <div class="empty-state">Memuat riwayat...</div>
            </div>
        </div>
    </div>
    
    <!-- Prism.js JavaScript -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.js"></script>
    
    <script>
        const promptArea = document.getElementById('promptArea');
        const responseArea = document.getElementById('responseArea');
        const submitBtn = document.getElementById('submitBtn');
        const statusBadge = document.getElementById('statusBadge');
        const codePreview = document.getElementById('codePreview');
        const previewCode = document.getElementById('previewCode');
        const previewLanguage = document.getElementById('previewLanguage');
        
        // Configure Prism autoloader
        Prism.plugins.autoloader.languages_path = "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/";
        
        // Tab switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tabName + '-tab').classList.add('active');
            if (tabName === 'history') {
                loadHistory();
            }
        }
        
        // Mitigasi Risiko: Simpan draft jawaban di localStorage
        responseArea.addEventListener('input', () => {
            localStorage.setItem('hermes_draft_response', responseArea.value);
            submitBtn.disabled = responseArea.value.trim() === '';
            updateCodePreview();
        });
        
        window.addEventListener('load', () => {
            const savedDraft = localStorage.getItem('hermes_draft_response');
            if (savedDraft) {
                responseArea.value = savedDraft;
                submitBtn.disabled = savedDraft.trim() === '';
                updateCodePreview();
            }
            checkPrompt();
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
                    codePreview.style.display = 'none';
                    
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
        
        // === SYNTAX HIGHLIGHTING FUNCTIONS ===
        
        function detectLanguage(text) {
            const backtick = String.fromCharCode(96);
            const tripleBacktick = backtick + backtick + backtick;
            
            // Deteksi code block dengan bahasa eksplisit
            const langPatterns = [
                { lang: 'python', pattern: new RegExp(tripleBacktick + 'python', 'i') },
                { lang: 'javascript', pattern: new RegExp(tripleBacktick + 'javascript', 'i') },
                { lang: 'javascript', pattern: new RegExp(tripleBacktick + 'js', 'i') },
                { lang: 'bash', pattern: new RegExp(tripleBacktick + 'bash', 'i') },
                { lang: 'bash', pattern: new RegExp(tripleBacktick + 'sh', 'i') },
                { lang: 'bash', pattern: new RegExp(tripleBacktick + 'shell', 'i') },
                { lang: 'json', pattern: new RegExp(tripleBacktick + 'json', 'i') },
                { lang: 'html', pattern: new RegExp(tripleBacktick + 'html', 'i') },
                { lang: 'css', pattern: new RegExp(tripleBacktick + 'css', 'i') },
                { lang: 'yaml', pattern: new RegExp(tripleBacktick + 'yaml', 'i') },
                { lang: 'yaml', pattern: new RegExp(tripleBacktick + 'yml', 'i') },
                { lang: 'markdown', pattern: new RegExp(tripleBacktick + 'markdown', 'i') },
                { lang: 'markdown', pattern: new RegExp(tripleBacktick + 'md', 'i') },
                { lang: 'cpp', pattern: new RegExp(tripleBacktick + 'cpp', 'i') },
                { lang: 'cpp', pattern: new RegExp(tripleBacktick + 'c\\+\\+', 'i') },
                { lang: 'java', pattern: new RegExp(tripleBacktick + 'java', 'i') },
                { lang: 'go', pattern: new RegExp(tripleBacktick + 'go', 'i') },
                { lang: 'rust', pattern: new RegExp(tripleBacktick + 'rust', 'i') },
                { lang: 'rust', pattern: new RegExp(tripleBacktick + 'rs', 'i') },
                { lang: 'ruby', pattern: new RegExp(tripleBacktick + 'ruby', 'i') },
                { lang: 'ruby', pattern: new RegExp(tripleBacktick + 'rb', 'i') },
                { lang: 'php', pattern: new RegExp(tripleBacktick + 'php', 'i') }
            ];
            
            for (const { lang, pattern } of langPatterns) {
                if (pattern.test(text)) {
                    return lang;
                }
            }
            
            // Auto-detect berdasarkan konten
            if (/\bdef\s+\w+\s*\(/.test(text) || /\bimport\s+\w+/.test(text)) {
                return 'python';
            }
            if (/\bfunction\s+\w+\s*\(/.test(text) || /\bconst\s+\w+\s*=/.test(text)) {
                return 'javascript';
            }
            if (/^#!\/bin\/bash/.test(text) || /^\s*(echo|if|then|fi|for|do|done)/.test(text)) {
                return 'bash';
            }
            if (/^\s*[\{\[]/.test(text) && /[\}\]]\s*$/.test(text)) {
                return 'json';
            }
            
            return 'plaintext';
        }
        
        function extractCodeBlocks(text) {
            const backtick = String.fromCharCode(96);
            const tripleBacktick = backtick + backtick + backtick;
            
            // Pattern untuk match code blocks
            const pattern = new RegExp(tripleBacktick + '(\\w+)?\\s*\\n([\\s\\S]*?)' + tripleBacktick, 'g');
            const blocks = [];
            let match;
            
            while ((match = pattern.exec(text)) !== null) {
                blocks.push({
                    language: match[1] || 'plaintext',
                    content: match[2].trim()
                });
            }
            
            return blocks;
        }
        
        let previewDebounceTimer;
        
        function updateCodePreview() {
            clearTimeout(previewDebounceTimer);
            
            previewDebounceTimer = setTimeout(() => {
                const text = responseArea.value;
                
                if (!text.trim()) {
                    codePreview.style.display = 'none';
                    return;
                }
                
                const codeBlocks = extractCodeBlocks(text);
                
                if (codeBlocks.length === 0) {
                    codePreview.style.display = 'none';
                    return;
                }
                
                // Tampilkan preview untuk code block pertama (atau gabungkan semua)
                const firstBlock = codeBlocks[0];
                const language = firstBlock.language;
                const code = firstBlock.content;
                
                previewLanguage.textContent = language;
                previewCode.textContent = code;
                previewCode.className = `language-${language} line-numbers`;
                
                // Apply syntax highlighting
                Prism.highlightElement(previewCode);
                
                codePreview.style.display = 'block';
            }, 300); // Debounce 300ms
        }
        
        // History functions
        async function loadHistory() {
            try {
                const res = await fetch('/history');
                const data = await res.json();
                const historyList = document.getElementById('historyList');
                
                if (data.conversations.length === 0) {
                    historyList.innerHTML = '<div class="empty-state">Belum ada riwayat percakapan</div>';
                    return;
                }
                
                historyList.innerHTML = data.conversations.map(conv => `
                    <div class="history-item">
                        <div class="history-header">
                            <span class="history-id">#${conv.id}</span>
                            <span class="history-time">${new Date(conv.timestamp).toLocaleString('id-ID')}</span>
                        </div>
                        <div class="history-preview">
                            <strong>Prompt:</strong> ${escapeHtml(conv.prompt.substring(0, 100))}${conv.prompt.length > 100 ? '...' : ''}
                        </div>
                        <div class="history-actions">
                            <button class="btn-small" onclick="toggleDetails(${conv.id})">👁️ Lihat Detail</button>
                            <button class="btn-small btn-danger" onclick="deleteConversation(${conv.id})">🗑️ Hapus</button>
                        </div>
                        <div id="details-${conv.id}" class="history-details">
                            <div class="history-section">
                                <h4>📥 Prompt:</h4>
                                <div class="history-content">${escapeHtml(conv.prompt)}</div>
                            </div>
                            <div class="history-section">
                                <h4>📤 Response:</h4>
                                <div class="history-content">${escapeHtml(conv.response)}</div>
                            </div>
                            <div class="history-section">
                                <h4>ℹ️ Info:</h4>
                                <div>Model: ${conv.model}</div>
                                <div>Status: ${conv.status}</div>
                            </div>
                        </div>
                    </div>
                `).join('');
            } catch (err) {
                console.error('Gagal memuat riwayat:', err);
                document.getElementById('historyList').innerHTML = '<div class="empty-state">Gagal memuat riwayat</div>';
            }
        }
        
        function toggleDetails(id) {
            const details = document.getElementById('details-' + id);
            details.classList.toggle('show');
        }
        
        async function deleteConversation(id) {
            if (!confirm('Yakin ingin menghapus percakapan ini?')) return;
            
            try {
                const res = await fetch('/history/' + id, { method: 'DELETE' });
                if (res.ok) {
                    loadHistory();
                } else {
                    alert('Gagal menghapus percakapan');
                }
            } catch (err) {
                console.error('Error deleting:', err);
                alert('Terjadi kesalahan jaringan');
            }
        }
        
        async function clearHistory() {
            if (!confirm('Yakin ingin menghapus SEMUA riwayat? Tindakan ini tidak bisa dibatalkan!')) return;
            
            try {
                const res = await fetch('/history/clear', { method: 'DELETE' });
                if (res.ok) {
                    loadHistory();
                } else {
                    alert('Gagal menghapus riwayat');
                }
            } catch (err) {
                console.error('Error clearing:', err);
                alert('Terjadi kesalahan jaringan');
            }
        }
        
        async function exportHistory() {
            try {
                const res = await fetch('/history/export/json');
                const data = await res.json();
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'hermes-history-' + new Date().toISOString().split('T')[0] + '.json';
                a.click();
                URL.revokeObjectURL(url);
            } catch (err) {
                console.error('Error exporting:', err);
                alert('Gagal export riwayat');
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
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
    
    # Simpan ke history
    if state.current_prompt:
        history_service.save_conversation(
            prompt=state.current_prompt,
            response=user_response,
            model="deepseek-manual"
        )
    
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

# --- 5. HISTORY ENDPOINTS ---
@app.get("/history")
async def get_history(limit: int = 50):
    """Ambil riwayat percakapan"""
    conversations = history_service.get_recent(limit)
    return {"conversations": conversations, "count": len(conversations)}

@app.get("/history/{conversation_id}")
async def get_conversation(conversation_id: int):
    """Ambil detail percakapan berdasarkan ID"""
    conv = history_service.get_by_id(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@app.delete("/history/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Hapus percakapan berdasarkan ID"""
    deleted = history_service.delete_by_id(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "id": conversation_id}

@app.delete("/history/clear")
async def clear_history():
    """Hapus semua riwayat percakapan"""
    count = history_service.clear_all()
    return {"status": "cleared", "count": count}

@app.get("/history/export/json")
async def export_history_json():
    """Export semua riwayat ke JSON"""
    import json
    json_str = history_service.export_to_json()
    return JSONResponse(content=json.loads(json_str))

@app.get("/history/stats")
async def get_history_stats():
    """Dapatkan statistik riwayat"""
    stats = history_service.get_stats()
    return stats

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "hermes-middleware", "version": "0.2.1"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
