from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def web_ui():
    # Catatan: CSS sudah dipindahkan ke /static/style.css
    # agar file ini lebih ringkas dan mudah dirawat.
    #
    # PENTING: File ini TIDAK boleh memuat triple backtick literal.
    # Karakter backtick dibangun via chr(96) di JavaScript.
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
                <div class="hint">💡 Setelah paste, klik tombol di bawah untuk mengirim ke Hermes. Jika ada kode, panel approval akan muncul otomatis.</div>
                <br>
                <button id="submitBtn" onclick="submitResponse()" disabled>Kirim ke Hermes</button>

                <!-- ============================================ -->
                <!-- MODUL E: SANDBOX APPROVAL UI PANEL           -->
                <!-- Muncul otomatis saat kode terdeteksi         -->
                <!-- ============================================ -->
                <div id="approvalPanel" class="approval-panel" style="display: none;">
                    <div class="approval-header">
                        <div class="approval-title">
                            <span class="approval-icon">🔒</span>
                            <span>Sandbox Approval - Kode Terdeteksi</span>
                        </div>
                        <button class="btn-small btn-secondary" onclick="toggleApprovalDetails()">
                            <span id="toggleIcon">▼</span> Detail
                        </button>
                    </div>

                    <!-- File Info Section -->
                    <div id="approvalDetails" class="approval-details">
                        <div class="file-info-grid">
                            <div class="info-item">
                                <label>📄 Nama File:</label>
                                <div class="info-value">
                                    <span id="fileNameDisplay" class="file-name">-</span>
                                    <button class="btn-tiny btn-secondary" onclick="editFileName()">✏️ Edit</button>
                                </div>
                                <input type="text" id="fileNameInput" class="file-name-input" style="display:none;" placeholder="path/ke/file.ext">
                            </div>

                            <div class="info-item">
                                <label>🎯 Sumber Path:</label>
                                <div class="info-value">
                                    <span id="pathSourceBadge" class="path-source-badge">-</span>
                                </div>
                            </div>

                            <div class="info-item">
                                <label>💻 Bahasa:</label>
                                <div class="info-value">
                                    <span id="languageDisplay" class="language-badge">-</span>
                                </div>
                            </div>

                            <div class="info-item">
                                <label>📏 Ukuran:</label>
                                <div class="info-value">
                                    <span id="sizeDisplay">-</span>
                                </div>
                            </div>
                        </div>

                        <!-- Code Preview Section -->
                        <div class="code-preview-section">
                            <div class="preview-header">
                                <span>🔍 Preview Kode</span>
                                <div class="preview-actions">
                                    <button class="btn-tiny btn-secondary" onclick="copyCodeToClipboard()">📋 Copy</button>
                                    <button class="btn-tiny btn-secondary" onclick="toggleCodeEdit()">
                                        <span id="codeEditToggle">✏️ Edit Kode</span>
                                    </button>
                                </div>
                            </div>
                            <div class="preview-content">
                                <pre id="codePreviewPre" class="line-numbers"><code id="codePreviewCode"></code></pre>
                                <textarea id="codeEditArea" style="display:none;" class="code-edit-area"></textarea>
                            </div>
                        </div>

                        <!-- Warning/Info Messages -->
                        <div id="approvalWarnings" class="approval-warnings" style="display:none;">
                            <!-- Dynamic warnings will be inserted here -->
                        </div>

                        <!-- Approval Actions -->
                        <div class="approval-actions">
                            <button id="approveBtn" class="btn-approval btn-approve" onclick="approveCode()">
                                ✅ Izinkan & Kirim
                            </button>
                            <button id="editApproveBtn" class="btn-approval btn-edit-approve" onclick="editAndApprove()">
                                ✏️ Edit & Izinkan
                            </button>
                            <button id="rejectBtn" class="btn-approval btn-reject" onclick="rejectCode()">
                                ❌ Tolak
                            </button>
                        </div>
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

        // Approval Panel Elements
        const approvalPanel = document.getElementById('approvalPanel');
        const approvalDetails = document.getElementById('approvalDetails');
        const fileNameDisplay = document.getElementById('fileNameDisplay');
        const fileNameInput = document.getElementById('fileNameInput');
        const pathSourceBadge = document.getElementById('pathSourceBadge');
        const languageDisplay = document.getElementById('languageDisplay');
        const sizeDisplay = document.getElementById('sizeDisplay');
        const codePreviewPre = document.getElementById('codePreviewPre');
        const codePreviewCode = document.getElementById('codePreviewCode');
        const codeEditArea = document.getElementById('codeEditArea');
        const approvalWarnings = document.getElementById('approvalWarnings');

        const editPromptBtn = document.getElementById('editPromptBtn');
        const revertPromptBtn = document.getElementById('revertPromptBtn');
        const editedBadge = document.getElementById('editedBadge');

        // State untuk fitur Edit Prompt
        let originalPromptFromHermes = null;
        let isEditMode = false;

        // State untuk Approval Panel (Modul E)
        let detectedCodeBlocks = [];
        let detectedFilePath = null;
        let detectedPathSource = 'manual';
        let isCodeEditMode = false;
        let approvalState = 'pending'; // 'pending', 'approved', 'rejected'

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
                isEditMode = true;
                promptArea.readOnly = false;
                promptArea.classList.add('editing');
                editPromptBtn.textContent = '💾 Selesai Edit';
                editPromptBtn.classList.remove('btn-secondary');
                editPromptBtn.classList.add('btn-success');
                revertPromptBtn.style.display = 'inline-block';
                promptArea.focus();
            } else {
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

        promptArea.addEventListener('input', () => {
            updateEditedBadge();
        });

        // Mitigasi Risiko: Simpan draft jawaban di localStorage
        // DAN deteksi kode untuk tampilkan approval panel (Modul E)
        responseArea.addEventListener('input', () => {
            localStorage.setItem('hermes_draft_response', responseArea.value);
            submitBtn.disabled = responseArea.value.trim() === '';

            // MODUL E: Deteksi kode dan tampilkan approval panel
            detectAndShowApprovalPanel();
        });

        window.addEventListener('load', () => {
            const savedDraft = localStorage.getItem('hermes_draft_response');
            if (savedDraft) {
                responseArea.value = savedDraft;
                submitBtn.disabled = savedDraft.trim() === '';
                detectAndShowApprovalPanel();
            }
            checkPrompt();
        });

        setInterval(checkPrompt, 2000);

        async function checkPrompt() {
            try {
                const res = await fetch('/get_prompt');
                const data = await res.json();
                if (data.status === 'waiting' && data.prompt) {
                    const promptChanged = promptArea.value !== data.prompt &&
                                         originalPromptFromHermes !== data.original_prompt;
                    if (promptChanged) {
                        originalPromptFromHermes = data.original_prompt || data.prompt;
                        promptArea.value = data.prompt;
                        if (isEditMode) {
                            exitEditMode();
                        }
                        editPromptBtn.disabled = false;
                        updateEditedBadge();
                        statusBadge.textContent = '⏳ Prompt Diterima! Menunggu Jawaban Anda...';
                        statusBadge.className = 'status status-waiting';

                        // MODUL E: Re-detect approval panel karena prompt baru
                        detectAndShowApprovalPanel();
                    }
                } else {
                    editPromptBtn.disabled = true;
                    statusBadge.textContent = '✅ Menunggu Hermes...';
                    statusBadge.className = 'status status-idle';
                }
            } catch (err) {
                console.error('Gagal mengecek prompt:', err);
            }
        }

        // ============================================
        // MODUL E: SANDBOX APPROVAL UI LOGIC
        // ============================================

        /**
         * Deteksi kode dalam response dan tampilkan approval panel
         */
        function detectAndShowApprovalPanel() {
            const text = responseArea.value;

            if (!text.trim()) {
                hideApprovalPanel();
                return;
            }

            // Ekstrak blok kode
            const codeBlocks = extractCodeBlocks(text);

            if (codeBlocks.length === 0) {
                hideApprovalPanel();
                return;
            }

            // Simpan state
            detectedCodeBlocks = codeBlocks;

            // Ekstrak path dari prompt Hermes
            const promptText = promptArea.value;
            const pathInfo = extractFilePathFromPrompt(promptText);
            detectedFilePath = pathInfo.path;
            detectedPathSource = pathInfo.source;

            // Tampilkan approval panel
            showApprovalPanel();
        }

        /**
         * Tampilkan approval panel dengan informasi lengkap
         */
        function showApprovalPanel() {
            approvalPanel.style.display = 'block';

            // Reset edit mode kode jika aktif
            if (isCodeEditMode) {
                isCodeEditMode = false;
                codePreviewPre.style.display = 'block';
                codeEditArea.style.display = 'none';
                document.getElementById('codeEditToggle').textContent = '✏️ Edit Kode';
            }

            // Update file info
            updateFileInfo();

            // Update code preview
            updateCodePreview();

            // Check for warnings
            checkForWarnings();

            // Reset approval state
            approvalState = 'pending';
            updateApprovalButtons();
        }

        /**
         * Sembunyikan approval panel
         */
        function hideApprovalPanel() {
            approvalPanel.style.display = 'none';
            detectedCodeBlocks = [];
            detectedFilePath = null;
            detectedPathSource = 'manual';
            approvalState = 'pending';
        }

        /**
         * Update informasi file di panel
         */
        function updateFileInfo() {
            // File name
            if (detectedFilePath) {
                fileNameDisplay.textContent = detectedFilePath;
                fileNameDisplay.classList.remove('no-path');
            } else {
                fileNameDisplay.textContent = '⚠️ Tidak terdeteksi - Klik Edit untuk input manual';
                fileNameDisplay.classList.add('no-path');
            }

            // Path source badge
            const sourceInfo = getPathSourceInfo(detectedPathSource);
            pathSourceBadge.textContent = sourceInfo.description;
            pathSourceBadge.className = 'path-source-badge source-' + detectedPathSource;
            pathSourceBadge.innerHTML = sourceInfo.icon + ' ' + sourceInfo.description;

            // Language
            if (detectedCodeBlocks.length > 0) {
                const lang = detectedCodeBlocks[0].language;
                languageDisplay.textContent = lang;
                languageDisplay.className = 'language-badge lang-' + lang;
            }

            // Size
            if (detectedCodeBlocks.length > 0) {
                const size = detectedCodeBlocks[0].content.length;
                sizeDisplay.textContent = size + ' karakter';
            }
        }

        /**
         * Update preview kode dengan syntax highlighting
         */
        function updateCodePreview() {
            if (detectedCodeBlocks.length === 0) return;

            const firstBlock = detectedCodeBlocks[0];
            const language = firstBlock.language;
            const code = firstBlock.content;

            codePreviewCode.textContent = code;
            codePreviewCode.className = 'language-' + language + ' line-numbers';

            // Re-highlight dengan Prism
            Prism.highlightElement(codePreviewCode);
        }

        /**
         * Check untuk warning keamanan
         */
        function checkForWarnings() {
            const warnings = [];

            if (!detectedFilePath) {
                warnings.push({
                    type: 'warning',
                    icon: '⚠️',
                    message: 'Path file tidak terdeteksi. Silakan input manual sebelum approve.'
                });
            }

            if (detectedFilePath && isPathSuspicious(detectedFilePath)) {
                warnings.push({
                    type: 'danger',
                    icon: '🚨',
                    message: 'Path mencurigakan terdeteksi! Pastikan ini aman sebelum approve.'
                });
            }

            // Check untuk kode berbahaya (basic check)
            if (detectedCodeBlocks.length > 0) {
                const code = detectedCodeBlocks[0].content;
                const dangerousPatterns = containsDangerousCode(code);
                if (dangerousPatterns.length > 0) {
                    warnings.push({
                        type: 'danger',
                        icon: '🚨',
                        message: 'Kode mengandung command berpotensi berbahaya: ' + dangerousPatterns.join(', ') + '. Review dengan seksama!'
                    });
                }
            }

            // Tampilkan warnings
            if (warnings.length > 0) {
                approvalWarnings.innerHTML = warnings.map(w =>
                    '<div class="warning-item warning-' + w.type + '">' +
                    '<span class="warning-icon">' + w.icon + '</span>' +
                    '<span>' + w.message + '</span>' +
                    '</div>'
                ).join('');
                approvalWarnings.style.display = 'block';
            } else {
                approvalWarnings.style.display = 'none';
            }
        }

        /**
         * Toggle detail approval panel
         */
        function toggleApprovalDetails() {
            const isHidden = approvalDetails.style.display === 'none';
            approvalDetails.style.display = isHidden ? 'block' : 'none';
            document.getElementById('toggleIcon').textContent = isHidden ? '▼' : '▲';
        }

        /**
         * Edit nama file manual
         */
        function editFileName() {
            fileNameDisplay.style.display = 'none';
            fileNameInput.style.display = 'block';
            fileNameInput.value = detectedFilePath || '';
            fileNameInput.focus();

            // Save on blur or enter
            fileNameInput.onblur = saveFileName;
            fileNameInput.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    saveFileName();
                } else if (e.key === 'Escape') {
                    cancelEditFileName();
                }
            };
        }

        function saveFileName() {
            const newPath = fileNameInput.value.trim();
            if (newPath) {
                detectedFilePath = newPath;
                detectedPathSource = 'manual';
                updateFileInfo();
                checkForWarnings();
            }
            fileNameInput.style.display = 'none';
            fileNameDisplay.style.display = 'block';
        }

        function cancelEditFileName() {
            fileNameInput.style.display = 'none';
            fileNameDisplay.style.display = 'block';
        }

        /**
         * Toggle edit mode untuk kode
         */
        function toggleCodeEdit() {
            isCodeEditMode = !isCodeEditMode;

            if (isCodeEditMode) {
                // Switch to edit mode
                codePreviewPre.style.display = 'none';
                codeEditArea.style.display = 'block';
                codeEditArea.value = detectedCodeBlocks[0].content;
                document.getElementById('codeEditToggle').textContent = '💾 Selesai Edit';
            } else {
                // Switch back to preview
                const editedCode = codeEditArea.value;
                detectedCodeBlocks[0].content = editedCode;
                codeEditArea.style.display = 'none';
                codePreviewPre.style.display = 'block';
                document.getElementById('codeEditToggle').textContent = '✏️ Edit Kode';
                updateCodePreview();

                // Update size
                sizeDisplay.textContent = editedCode.length + ' karakter';
            }
        }

        /**
         * Copy kode ke clipboard
         */
        function copyCodeToClipboard() {
            const code = isCodeEditMode ? codeEditArea.value : detectedCodeBlocks[0].content;
            navigator.clipboard.writeText(code).then(() => {
                // Notifikasi singkat
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '✅ Tersalin!';
                setTimeout(() => { btn.textContent = originalText; }, 1500);
            }).catch(err => {
                console.error('Gagal copy:', err);
                alert('Gagal copy kode');
            });
        }

        /**
         * Approve kode - kirim ke Hermes sebagai tool call
         */
        function approveCode() {
            if (!detectedFilePath) {
                alert('⚠️ Path file belum ditentukan! Silakan edit dan input path terlebih dahulu.');
                editFileName();
                return;
            }

            approvalState = 'approved';
            updateApprovalButtons();

            // Submit response ke Hermes (akan dikirim sebagai tool call)
            submitResponse(true);
        }

        /**
         * Edit dan approve - masuk ke edit mode dulu
         */
        function editAndApprove() {
            if (!isCodeEditMode) {
                toggleCodeEdit();
            }
            // User akan edit kode, lalu klik "Izinkan & Kirim"
        }

        /**
         * Reject kode - kirim pesan penolakan
         */
        function rejectCode() {
            if (!confirm('Tolak kode ini? Hermes akan diminta untuk memperbaiki.')) return;

            approvalState = 'rejected';
            updateApprovalButtons();

            // Kirim response penolakan ke Hermes
            const rejectionMessage = 'Saya menolak untuk menulis file ini. Tolong perbaiki dan berikan versi yang lebih baik.';
            responseArea.value = rejectionMessage;
            localStorage.setItem('hermes_draft_response', rejectionMessage);
            submitResponse(false);
        }

        /**
         * Update state tombol approval
         */
        function updateApprovalButtons() {
            const approveBtn = document.getElementById('approveBtn');
            const editApproveBtn = document.getElementById('editApproveBtn');
            const rejectBtn = document.getElementById('rejectBtn');

            if (approvalState === 'approved') {
                approveBtn.disabled = true;
                approveBtn.textContent = '✅ Disetujui';
                approveBtn.classList.add('btn-disabled');
                editApproveBtn.disabled = true;
                rejectBtn.disabled = true;
            } else if (approvalState === 'rejected') {
                rejectBtn.disabled = true;
                rejectBtn.textContent = '❌ Ditolak';
                rejectBtn.classList.add('btn-disabled');
                approveBtn.disabled = true;
                editApproveBtn.disabled = true;
            } else {
                approveBtn.disabled = false;
                approveBtn.textContent = '✅ Izinkan & Kirim';
                approveBtn.classList.remove('btn-disabled');
                editApproveBtn.disabled = false;
                rejectBtn.disabled = false;
            }
        }

        // ============================================
        // HELPER FUNCTIONS - PARSING & DETECTION
        // ============================================

        /**
         * Ekstrak blok kode dari text
         * Menggunakan chr(96) untuk menghindari triple backtick literal
         */
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

        /**
         * Ekstrak path file dari prompt Hermes (hierarki 3 prioritas)
         * Konsisten dengan parser.py backend
         */
        function extractFilePathFromPrompt(prompt) {
            if (!prompt) {
                return { path: null, source: 'manual' };
            }

            const backtick = String.fromCharCode(96);

            // PRIORITAS 1: Format eksplisit [FILE: path]
            const explicitMatch = prompt.match(/\[FILE:\s*([^\]]+)\]/i);
            if (explicitMatch) {
                const path = explicitMatch[1].trim().replace(new RegExp(backtick, 'g'), '').trim();
                if (path) {
                    return { path: path, source: 'explicit' };
                }
            }

            // PRIORITAS 2: Natural language patterns
            const pathPattern = '[A-Za-z0-9_][A-Za-z0-9_./-]*\\.[A-Za-z0-9]+';
            const nlPatterns = [
                new RegExp('(?:file|berkas)\\s+' + backtick + '?(' + pathPattern + ')' + backtick + '?', 'i'),
                new RegExp('(?:named|bernama|dengan\\s+nama)\\s+' + backtick + '?(' + pathPattern + ')' + backtick + '?', 'i'),
                new RegExp('(?:simpan\\s+ke|save\\s+to|tulis\\s+ke)\\s+' + backtick + '?(' + pathPattern + ')' + backtick + '?', 'i'),
                new RegExp(backtick + '(' + pathPattern + ')' + backtick, 'i'),
                /\b([A-Za-z0-9_\-]+\.(?:py|js|ts|jsx|tsx|html|css|scss|json|yaml|yml|toml|ini|cfg|md|txt|csv|sql|sh|bash|cpp|cc|c|h|hpp|java|go|rs|rb|php|lua|xml|env))\b/i
            ];

            for (const pattern of nlPatterns) {
                const match = prompt.match(pattern);
                if (match) {
                    return { path: match[1], source: 'natural_language' };
                }
            }

            // PRIORITAS 3: Manual fallback
            return { path: null, source: 'manual' };
        }

        /**
         * Get info untuk path source (ikon, deskripsi, warna)
         */
        function getPathSourceInfo(source) {
            const sources = {
                'explicit': {
                    description: 'Format Eksplisit [FILE: ...]',
                    icon: '🎯'
                },
                'natural_language': {
                    description: 'Pola Bahasa Natural',
                    icon: '💬'
                },
                'manual': {
                    description: 'Input Manual Diperlukan',
                    icon: '✍️'
                }
            };
            return sources[source] || { description: 'Tidak Diketahui', icon: '❓' };
        }

        /**
         * Check apakah path mencurigakan (keamanan)
         */
        function isPathSuspicious(path) {
            const suspiciousPatterns = [
                /^\//,                              // Absolute path Unix
                /^[A-Za-z]:/,                       // Absolute path Windows
                /\.\./,                             // Path traversal
                /^\/etc\//,                         // Linux system
                /^\/proc\//,
                /^\/sys\//,
                /^\/dev\//,
                /^\/root\//,
                /\.ssh/i,
                /\.env$/i,
                /password/i,
                /secret/i,
                /private[_\-]?key/i
            ];

            for (const pattern of suspiciousPatterns) {
                if (pattern.test(path)) {
                    return true;
                }
            }
            return false;
        }

        /**
         * Check apakah kode mengandung command berbahaya
         * Returns array of detected dangerous patterns
         */
        function containsDangerousCode(code) {
            const dangerous = [];
            const patterns = [
                { pattern: /rm\s+-rf\s+\//, desc: 'rm -rf /' },
                { pattern: /rm\s+-rf\s+~/, desc: 'rm -rf ~' },
                { pattern: /mkfs\./, desc: 'mkfs (format disk)' },
                { pattern: /dd\s+if=/, desc: 'dd (disk destroyer)' },
                { pattern: /:\(\)\s*\{.*:\|:.*\}/, desc: 'fork bomb' },
                { pattern: /chmod\s+-R\s+777\s+\//, desc: 'chmod 777 /' },
                { pattern: /DROP\s+TABLE/i, desc: 'SQL DROP TABLE' },
                { pattern: /DROP\s+DATABASE/i, desc: 'SQL DROP DATABASE' },
                { pattern: /TRUNCATE\s+TABLE/i, desc: 'SQL TRUNCATE' },
                { pattern: /DELETE\s+FROM\s+\w+\s*;/i, desc: 'SQL DELETE tanpa WHERE' },
                { pattern: /os\.system\s*\(\s*['"]rm/, desc: 'Python os.system rm' },
                { pattern: /subprocess.*shell\s*=\s*True/, desc: 'subprocess shell=True' },
                { pattern: /eval\s*\(/, desc: 'eval() - code injection risk' },
                { pattern: /exec\s*\(/, desc: 'exec() - code execution' }
            ];

            for (const p of patterns) {
                if (p.pattern.test(code)) {
                    dangerous.push(p.desc);
                }
            }
            return dangerous;
        }

        // ============================================
        // SUBMIT RESPONSE (dengan dukungan tool call)
        // ============================================

        async function submitResponse(isToolCall = false) {
            const userResponse = responseArea.value.trim();
            if (!userResponse) return;

            submitBtn.disabled = true;
            submitBtn.textContent = 'Mengirim...';
            statusBadge.textContent = '📤 Mengirim ke Hermes...';
            statusBadge.className = 'status status-waiting';

            // Siapkan payload
            const payload = { response: userResponse };

            // Jika ini tool call (approve dari approval panel), sertakan metadata
            if (isToolCall && detectedCodeBlocks.length > 0 && detectedFilePath) {
                payload.is_tool_call = true;
                payload.tool_call = {
                    file_path: detectedFilePath,
                    path_source: detectedPathSource,
                    language: detectedCodeBlocks[0].language,
                    content: detectedCodeBlocks[0].content
                };
            }

            // Sertakan edited_prompt jika user mengedit prompt
            const currentPrompt = promptArea.value;
            if (originalPromptFromHermes !== null && currentPrompt !== originalPromptFromHermes) {
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

                    // Sembunyikan approval panel
                    hideApprovalPanel();

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
                    // Reset approval state agar user bisa coba lagi
                    if (approvalState !== 'pending') {
                        approvalState = 'pending';
                        updateApprovalButtons();
                    }
                }
            } catch (err) {
                console.error('Error submitting:', err);
                alert('Terjadi kesalahan jaringan.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Kirim ke Hermes';
                if (approvalState !== 'pending') {
                    approvalState = 'pending';
                    updateApprovalButtons();
                }
            }
        }

        // ============================================
        // HISTORY FUNCTIONS
        // ============================================

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