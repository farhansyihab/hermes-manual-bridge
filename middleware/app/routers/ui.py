"""
Router Web UI (Modul B) - Hermes Manual Bridge.
REFAKTOR v0.3.0:
File ini sebelumnya > 1000 baris karena memuat seluruh JavaScript inline.
Sekarang HANYA memuat markup HTML + daftar tag <script>.
Seluruh logika JavaScript dipindah ke middleware/static/js/ dan dipecah
per tanggung jawab.

MODUL E: Sandbox Approval Panel sudah terintegrasi di HTML ini.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def web_ui():
    return r"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hermes Manual Bridge Dashboard</title>
    
    <!-- CSS lokal -->
    <link rel="stylesheet" href="/static/style.css">
    
    <!-- Prism.js CSS (library eksternal, tetap dari CDN) -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css" rel="stylesheet">
</head>
<body>
    <div class="header">
        <h1>🚀 Hermes Manual Bridge</h1>
        <span id="statusBadge" class="status status-idle">Menunggu Hermes...</span>
    </div>

    <div class="tabs">
        <button class="tab active" onclick="switchTab('dashboard', this)">📊 Dashboard</button>
        <button class="tab" onclick="switchTab('history', this)">📜 Riwayat</button>
    </div>

    <!-- ================================================== -->
    <!-- TAB: DASHBOARD                                     -->
    <!-- ================================================== -->
    <div id="dashboard-tab" class="tab-content active">
        <div class="container">
            <!-- BOX 1: Prompt dari Hermes -->
            <div class="box">
                <div class="box-header">
                    <label for="promptArea">📥 Prompt dari Hermes Agent:</label>
                    <div class="prompt-actions">
                        <span id="editedBadge" class="edited-badge" style="display:none;">✏️ Edited</span>
                        <button id="editPromptBtn" class="btn-small btn-secondary"
                                onclick="toggleEditPrompt()" disabled>
                            ✏️ Edit Prompt
                        </button>
                        <button id="revertPromptBtn" class="btn-small btn-danger"
                                onclick="revertPrompt()" style="display:none;">
                            ↩️ Kembalikan Asli
                        </button>
                    </div>
                </div>
                <textarea id="promptArea" readonly placeholder="Belum ada prompt masuk..."></textarea>
                <div class="hint">
                    💡 Copy teks di atas dan paste ke DeepSeek Chat di tab browser lain.
                    Klik "Edit Prompt" untuk memodifikasi sebelum di-copy.
                </div>
            </div>

            <!-- BOX 2: Jawaban DeepSeek -->
            <div class="box">
                <div class="box-header">
                    <label for="responseArea">📤 Jawaban dari DeepSeek (Paste di sini):</label>
                    <div class="prompt-actions">
                        <button id="clearDraftBtn" class="btn-small btn-secondary"
                                onclick="clearDraftWithConfirm()">
                            🧹 Clear Draft
                        </button>
                    </div>
                </div>
                <textarea id="responseArea" placeholder="Paste jawaban DeepSeek di sini..."></textarea>
                <div class="hint">
                    💡 Setelah paste, klik tombol di bawah untuk mengirim ke Hermes.
                    Jika ada kode, panel approval akan muncul otomatis.
                </div>
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
                    
                    <div id="approvalDetails" class="approval-details">
                        <!-- File Info Grid -->
                        <div class="file-info-grid">
                            <!-- Nama File -->
                            <div class="info-item">
                                <label>📄 Nama File:</label>
                                <div class="info-value">
                                    <span id="fileNameDisplay" class="file-name">-</span>
                                    <button class="btn-tiny btn-secondary" onclick="editFileName()">✏️ Edit</button>
                                </div>
                                <input type="text" id="fileNameInput" class="file-name-input"
                                       style="display:none;" placeholder="path/ke/file.ext">
                            </div>

                            <!-- Sumber Path (Eksplisit/NL/Manual) -->
                            <div class="info-item">
                                <label>🎯 Sumber Path:</label>
                                <div class="info-value">
                                    <span id="pathSourceBadge" class="path-source-badge">-</span>
                                </div>
                            </div>

                            <!-- Bahasa -->
                            <div class="info-item">
                                <label>💻 Bahasa:</label>
                                <div class="info-value">
                                    <span id="languageDisplay" class="language-badge">-</span>
                                </div>
                            </div>

                            <!-- Ukuran -->
                            <div class="info-item">
                                <label>📏 Ukuran:</label>
                                <div class="info-value">
                                    <span id="sizeDisplay">-</span>
                                </div>
                            </div>
                        </div>

                        <!-- Code Preview -->
                        <div class="code-preview-section">
                            <div class="preview-header">
                                <span>🔍 Preview Kode</span>
                                <div class="preview-actions">
                                    <button class="btn-tiny btn-secondary"
                                            onclick="copyCodeToClipboard(this)">📋 Copy</button>
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

                        <!-- Warning / Info -->
                        <div id="approvalWarnings" class="approval-warnings" style="display:none;"></div>

                        <!-- Approval Actions -->
                        <div class="approval-actions">
                            <button id="approveBtn" class="btn-approval btn-approve" onclick="approveCode()">
                                ✅ Izinkan &amp; Kirim
                            </button>
                            <button id="editApproveBtn" class="btn-approval btn-edit-approve" onclick="editAndApprove()">
                                ✏️ Edit &amp; Izinkan
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

    <!-- ================================================== -->
    <!-- TAB: RIWAYAT                                       -->
    <!-- ================================================== -->
    <div id="history-tab" class="tab-content">
        <div class="box">
            <div class="history-toolbar">
                <h2 class="history-title">📜 Riwayat Percakapan</h2>
                <div class="history-toolbar-actions">
                    <button class="btn-small btn-secondary" onclick="exportHistory()">📥 Export JSON</button>
                    <button class="btn-small btn-danger" onclick="clearHistory()">🗑️ Hapus Semua</button>
                </div>
            </div>
            <div id="historyList">
                <div class="empty-state">Memuat riwayat...</div>
            </div>
        </div>
    </div>

    <!-- ================================================== -->
    <!-- Prism.js (syntax highlighting)                     -->
    <!-- ================================================== -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.js"></script>

    <!-- ================================================== -->
    <!-- Aplikasi: modul JS terpisah (URUTAN PENTING!)      -->
    <!-- ================================================== -->
    <script src="/static/js/config.js"></script>
    <script src="/static/js/utils.js"></script>
    <script src="/static/js/dom.js"></script>
    <script src="/static/js/state.js"></script>
    <script src="/static/js/parser.js"></script>
    <script src="/static/js/tabs.js"></script>
    <script src="/static/js/draft.js"></script>
    <script src="/static/js/prompt.js"></script>
    <script src="/static/js/approval.js"></script>
    <script src="/static/js/submit.js"></script>
    <script src="/static/js/history.js"></script>
    <script src="/static/js/main.js"></script>
</body>
</html>
"""