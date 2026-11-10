from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def web_ui():
    # Catatan: CSS sudah dipindahkan ke /static/style.css
    # agar file ini lebih ringkas dan mudah dirawat.
    return r"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hermes Manual Bridge Dashboard</title>
    <!-- External CSS (dipisahkan dari file ini) -->
    <link rel="stylesheet" href="/static/style.css">
    <!-- Prism.js CSS (tetap dari CDN karena library eksternal) -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css" rel="stylesheet">
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
                <div class="box-header">
                    <label for="promptArea">📥 Prompt dari Hermes Agent:</label>
                    <div class="prompt-actions">
                        <span id="editedBadge" class="edited-badge" style="display:none;">✏️ Edited</span>
                        <button id="editPromptBtn" class="btn-small btn-secondary" onclick="toggleEditPrompt()" disabled>
                            ✏️ Edit Prompt
                        </button>
                        <button id="revertPromptBtn" class="btn-small btn-danger" onclick="revertPrompt()" style="display:none;">
                            ↩️ Kembalikan Asli
                        </button>
                    </div>
                </div>
                <textarea id="promptArea" readonly placeholder="Belum ada prompt masuk..."></textarea>
                <div class="hint">💡 Copy teks di atas dan paste ke DeepSeek Chat di tab browser lain. Klik "Edit Prompt" untuk memodifikasi sebelum di-copy.</div>
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
        const editPromptBtn = document.getElementById('editPromptBtn');
        const revertPromptBtn = document.getElementById('revertPromptBtn');
        const editedBadge = document.getElementById('editedBadge');

        // State untuk fitur Edit Prompt
        let originalPromptFromHermes = null;  // Prompt asli dari Hermes (tidak berubah)
        let isEditMode = false;               // Apakah textarea sedang editable

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

        // === FITUR EDIT PROMPT ===
        function toggleEditPrompt() {
            if (!isEditMode) {
                // Masuk mode edit
                isEditMode = true;
                promptArea.readOnly = false;
                promptArea.classList.add('editing');
                editPromptBtn.textContent = '💾 Selesai Edit';
                editPromptBtn.classList.remove('btn-secondary');
                editPromptBtn.classList.add('btn-success');
                revertPromptBtn.style.display = 'inline-block';
                promptArea.focus();
            } else {
                // Keluar mode edit
                exitEditMode();
            }
        }

        function exitEditMode() {
            isEditMode = false;
            promptArea.readOnly = true;
            promptArea.classList.remove('editing');
            editPromptBtn.textContent = '✏️ Edit Prompt';
            editPromptBtn.classList.remove('btn-success');
            editPromptBtn.classList.add('btn-secondary');
            revertPromptBtn.style.display = 'none';

            // Tampilkan badge "Edited" jika prompt berbeda dari asli
            updateEditedBadge();
        }

        function revertPrompt() {
            if (originalPromptFromHermes === null) return;
            if (!confirm('Kembalikan prompt ke versi asli dari Hermes?')) return;
            promptArea.value = originalPromptFromHermes;
            updateEditedBadge();
        }

        function updateEditedBadge() {
            if (originalPromptFromHermes === null) {
                editedBadge.style.display = 'none';
                return;
            }
            const isEdited = promptArea.value !== originalPromptFromHermes;
            editedBadge.style.display = isEdited ? 'inline-block' : 'none';
        }

        // Deteksi perubahan manual di textarea (saat edit mode)
        promptArea.addEventListener('input', () => {
            updateEditedBadge();
        });

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
                    // Prompt baru dari Hermes - reset state edit
                    const promptChanged = promptArea.value !== data.prompt &&
                                         originalPromptFromHermes !== data.original_prompt;

                    if (promptChanged) {
                        // Simpan prompt asli dari Hermes
                        originalPromptFromHermes = data.original_prompt || data.prompt;
                        promptArea.value = data.prompt;

                        // Keluar dari edit mode jika sedang aktif
                        if (isEditMode) {
                            exitEditMode();
                        }

                        // Aktifkan tombol edit
                        editPromptBtn.disabled = false;
                        updateEditedBadge();

                        statusBadge.textContent = '⏳ Prompt Diterima! Menunggu Jawaban Anda...';
                        statusBadge.className = 'status status-waiting';
                    }
                } else {
                    // Idle - nonaktifkan tombol edit
                    editPromptBtn.disabled = true;
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

            // Siapkan payload - sertakan edited_prompt jika user mengedit
            const payload = { response: userResponse };
            const currentPrompt = promptArea.value;
            if (originalPromptFromHermes !== null && currentPrompt !== originalPromptFromHermes) {
                // User mengedit prompt - kirim versi edit sebagai 'edited_prompt'
                payload.edited_prompt = currentPrompt;
            }

            try {
                const res = await fetch('/submit_response', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    statusBadge.textContent = '🎉 Berhasil Dikirim! Menunggu tugas berikutnya...';
                    statusBadge.className = 'status status-sent';
                    responseArea.value = '';
                    localStorage.removeItem('hermes_draft_response');
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Kirim ke Hermes';
                    codePreview.style.display = 'none';

                    // Reset state prompt
                    originalPromptFromHermes = null;
                    if (isEditMode) exitEditMode();
                    editPromptBtn.disabled = true;
                    updateEditedBadge();

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
            const langPatterns = [
                { lang: 'python',     pattern: new RegExp(tripleBacktick + 'python', 'i') },
                { lang: 'javascript', pattern: new RegExp(tripleBacktick + 'javascript', 'i') },
                { lang: 'javascript', pattern: new RegExp(tripleBacktick + 'js', 'i') },
                { lang: 'bash',       pattern: new RegExp(tripleBacktick + 'bash', 'i') },
                { lang: 'bash',       pattern: new RegExp(tripleBacktick + 'sh', 'i') },
                { lang: 'bash',       pattern: new RegExp(tripleBacktick + 'shell', 'i') },
                { lang: 'json',       pattern: new RegExp(tripleBacktick + 'json', 'i') },
                { lang: 'html',       pattern: new RegExp(tripleBacktick + 'html', 'i') },
                { lang: 'css',        pattern: new RegExp(tripleBacktick + 'css', 'i') },
                { lang: 'yaml',       pattern: new RegExp(tripleBacktick + 'yaml', 'i') },
                { lang: 'yaml',       pattern: new RegExp(tripleBacktick + 'yml', 'i') },
                { lang: 'markdown',   pattern: new RegExp(tripleBacktick + 'markdown', 'i') },
                { lang: 'markdown',   pattern: new RegExp(tripleBacktick + 'md', 'i') },
                { lang: 'cpp',        pattern: new RegExp(tripleBacktick + 'cpp', 'i') },
                { lang: 'cpp',        pattern: new RegExp(tripleBacktick + 'c\\+\\+', 'i') },
                { lang: 'java',       pattern: new RegExp(tripleBacktick + 'java', 'i') },
                { lang: 'go',         pattern: new RegExp(tripleBacktick + 'go', 'i') },
                { lang: 'rust',       pattern: new RegExp(tripleBacktick + 'rust', 'i') },
                { lang: 'rust',       pattern: new RegExp(tripleBacktick + 'rs', 'i') },
                { lang: 'ruby',       pattern: new RegExp(tripleBacktick + 'ruby', 'i') },
                { lang: 'ruby',       pattern: new RegExp(tripleBacktick + 'rb', 'i') },
                { lang: 'php',        pattern: new RegExp(tripleBacktick + 'php', 'i') }
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
                const firstBlock = codeBlocks[0];
                const language = firstBlock.language;
                const code = firstBlock.content;
                previewLanguage.textContent = language;
                previewCode.textContent = code;
                previewCode.className = `language-${language} line-numbers`;
                Prism.highlightElement(previewCode);
                codePreview.style.display = 'block';
            }, 300);
        }

        // === HISTORY FUNCTIONS ===
        async function loadHistory() {
            try {
                const res = await fetch('/history');
                const data = await res.json();
                const historyList = document.getElementById('historyList');
                if (data.conversations.length === 0) {
                    historyList.innerHTML = '<div class="empty-state">Belum ada riwayat percakapan</div>';
                    return;
                }
                historyList.innerHTML = data.conversations.map(conv => {
                    // Deteksi apakah prompt pernah diedit
                    const wasEdited = conv.original_prompt &&
                                      conv.original_prompt !== conv.prompt;
                    const editedTag = wasEdited
                        ? '<span class="history-edited-tag">✏️ Edited</span>'
                        : '';

                    return `
                        <div class="history-item">
                            <div class="history-header">
                                <span class="history-id">#${conv.id} ${editedTag}</span>
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
                                ${wasEdited ? `
                                    <div class="history-section">
                                        <h4>📝 Prompt Asli dari Hermes:</h4>
                                        <div class="history-content history-original">${escapeHtml(conv.original_prompt)}</div>
                                    </div>
                                    <div class="history-section">
                                        <h4>📥 Prompt yang Dikirim ke DeepSeek (Edited):</h4>
                                        <div class="history-content">${escapeHtml(conv.prompt)}</div>
                                    </div>
                                ` : `
                                    <div class="history-section">
                                        <h4>📥 Prompt:</h4>
                                        <div class="history-content">${escapeHtml(conv.prompt)}</div>
                                    </div>
                                `}
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
                    `;
                }).join('');
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