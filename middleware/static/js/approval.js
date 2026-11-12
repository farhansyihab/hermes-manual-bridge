/**
 * approval.js - MODUL E: Sandbox Approval Panel
 * Menampilkan preview kode + info file sebelum tool call dikirim ke Hermes.
 * Prinsip: TIDAK ada penulisan file tanpa persetujuan user.
 * 
 * Fitur:
 * - Deteksi otomatis kode dalam respons DeepSeek
 * - Ekstraksi path dari prompt Hermes (3 prioritas)
 * - Indikator sumber path (Eksplisit/NL/Manual)
 * - Preview kode dengan syntax highlighting
 * - Validasi keamanan path
 * - Deteksi kode berbahaya
 * - Edit kode sebelum approve
 */

/**
 * Deteksi kode pada respons; tampilkan panel bila ada blok kode.
 */
function detectAndShowApprovalPanel() {
    const text = dom.responseArea.value;
    if (!text.trim()) {
        hideApprovalPanel();
        return;
    }

    const codeBlocks = extractCodeBlocks(text);
    if (codeBlocks.length === 0) {
        hideApprovalPanel();
        return;
    }

    AppState.detectedCodeBlocks = codeBlocks;
    
    const pathInfo = extractFilePathFromPrompt(dom.promptArea.value);
    AppState.detectedFilePath = pathInfo.path;
    AppState.detectedPathSource = pathInfo.source;

    showApprovalPanel();
}

/**
 * Tampilkan panel approval dengan semua informasi.
 */
function showApprovalPanel() {
    dom.approvalPanel.style.display = 'block';
    
    // Keluar dari mode edit kode bila sedang aktif
    if (AppState.isCodeEditMode) {
        AppState.isCodeEditMode = false;
        dom.codePreviewPre.style.display = 'block';
        dom.codeEditArea.style.display = 'none';
        dom.codeEditToggle.textContent = '✏️ Edit Kode';
    }

    updateFileInfo();
    updateCodePreview();
    checkForWarnings();
    
    AppState.approvalState = 'pending';
    updateApprovalButtons();
}

/**
 * Sembunyikan panel approval.
 */
function hideApprovalPanel() {
    dom.approvalPanel.style.display = 'none';
    resetApprovalState();
}

/**
 * Update bagian info file: nama, sumber path, bahasa, ukuran.
 * Ini adalah inti dari Modul E - menampilkan semua informasi yang diminta.
 */
function updateFileInfo() {
    // === NAMA FILE ===
    if (AppState.detectedFilePath) {
        dom.fileNameDisplay.textContent = AppState.detectedFilePath;
        dom.fileNameDisplay.classList.remove('no-path');
    } else {
        dom.fileNameDisplay.textContent = '⚠️ Tidak terdeteksi - Klik Edit untuk input manual';
        dom.fileNameDisplay.classList.add('no-path');
    }

    // === SUMBER PATH (Eksplisit/NL/Manual) ===
    const sourceInfo = getPathSourceInfo(AppState.detectedPathSource);
    dom.pathSourceBadge.className = 'path-source-badge source-' + AppState.detectedPathSource;
    dom.pathSourceBadge.textContent = sourceInfo.icon + ' ' + sourceInfo.description;
    
    // Tambahkan tooltip untuk penjelasan lebih detail
    dom.pathSourceBadge.title = getSourceExplanation(AppState.detectedPathSource);

    // === BAHASA & UKURAN ===
    if (AppState.detectedCodeBlocks.length > 0) {
        const first = AppState.detectedCodeBlocks[0];
        
        // Bahasa
        dom.languageDisplay.textContent = first.language;
        dom.languageDisplay.className = 'language-badge lang-' + first.language;
        
        // Ukuran
        const sizeInChars = first.content.length;
        const sizeInLines = first.content.split('\n').length;
        dom.sizeDisplay.textContent = `${sizeInChars} karakter (${sizeInLines} baris)`;
    }
}

/**
 * Dapatkan penjelasan detail untuk sumber path (untuk tooltip).
 */
function getSourceExplanation(source) {
    const explanations = {
        'explicit': 'Path diekstrak dari format eksplisit [FILE: path] yang di-instruct ke Hermes Agent. Ini adalah metode paling reliable (~95%+ akurasi).',
        'natural_language': 'Path diekstrak dari pola bahasa natural seperti "file hello.py", "berkas config.yaml", atau nama file yang dikutip backtick. Akurasi ~70-80%.',
        'manual': 'Path tidak terdeteksi secara otomatis. User perlu memasukkan path manual melalui dialog input.'
    };
    return explanations[source] || 'Sumber path tidak diketahui';
}

/**
 * Render preview kode + syntax highlighting via Prism.
 */
function updateCodePreview() {
    if (AppState.detectedCodeBlocks.length === 0) return;

    const first = AppState.detectedCodeBlocks[0];
    dom.codePreviewCode.textContent = first.content;
    dom.codePreviewCode.className = 'language-' + first.language + ' line-numbers';

    if (window.Prism) {
        Prism.highlightElement(dom.codePreviewCode);
    }
}

/**
 * Kumpulkan & tampilkan warning keamanan.
 */
function checkForWarnings() {
    const warnings = [];

    // Warning 1: Path tidak terdeteksi
    if (!AppState.detectedFilePath) {
        warnings.push({
            type: 'warning',
            icon: '⚠️',
            message: 'Path file tidak terdeteksi. Silakan input manual sebelum approve.'
        });
    } 
    // Warning 2: Path mencurigakan
    else if (isPathSuspicious(AppState.detectedFilePath)) {
        warnings.push({
            type: 'danger',
            icon: '🚨',
            message: 'Path mencurigakan terdeteksi! Pastikan ini aman sebelum approve.'
        });
    }

    // Warning 3: Kode berbahaya
    if (AppState.detectedCodeBlocks.length > 0) {
        const dangerous = containsDangerousCode(AppState.detectedCodeBlocks[0].content);
        if (dangerous.length > 0) {
            warnings.push({
                type: 'danger',
                icon: '🚨',
                message: 'Kode mengandung command berpotensi berbahaya: ' + 
                         dangerous.join(', ') + '. Review dengan seksama!'
            });
        }
    }

    // Tampilkan atau sembunyikan warnings
    if (warnings.length === 0) {
        dom.approvalWarnings.style.display = 'none';
        dom.approvalWarnings.innerHTML = '';
        return;
    }

    dom.approvalWarnings.innerHTML = warnings.map(function(w) {
        return '<div class="warning-item warning-' + w.type + '">' +
               '<span class="warning-icon">' + w.icon + '</span>' +
               '<span>' + escapeHtml(w.message) + '</span>' +
               '</div>';
    }).join('');
    
    dom.approvalWarnings.style.display = 'block';
}

/**
 * Toggle detail panel approval.
 */
function toggleApprovalDetails() {
    const isHidden = dom.approvalDetails.style.display === 'none';
    dom.approvalDetails.style.display = isHidden ? 'block' : 'none';
    dom.toggleIcon.textContent = isHidden ? '▼' : '▲';
}

/* =========================================================
 * Edit nama file manual (Prioritas 3 - fallback)
 * ========================================================= */

/**
 * Masuk ke mode edit nama file.
 */
function editFileName() {
    dom.fileNameDisplay.style.display = 'none';
    dom.fileNameInput.style.display = 'block';
    dom.fileNameInput.value = AppState.detectedFilePath || '';
    dom.fileNameInput.focus();
    
    dom.fileNameInput.onblur = saveFileName;
    dom.fileNameInput.onkeydown = function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveFileName();
        } else if (e.key === 'Escape') {
            cancelEditFileName();
        }
    };
}

/**
 * Simpan nama file yang diedit.
 */
function saveFileName() {
    const newPath = dom.fileNameInput.value.trim();
    
    if (newPath) {
        AppState.detectedFilePath = newPath;
        AppState.detectedPathSource = 'manual';
        updateFileInfo();
        checkForWarnings();
    }
    
    dom.fileNameInput.style.display = 'none';
    dom.fileNameDisplay.style.display = 'block';
}

/**
 * Batalkan edit nama file.
 */
function cancelEditFileName() {
    dom.fileNameInput.onblur = null;
    dom.fileNameInput.style.display = 'none';
    dom.fileNameDisplay.style.display = 'block';
}

/* =========================================================
 * Edit kode sebelum approve
 * ========================================================= */

/**
 * Toggle mode edit kode.
 */
function toggleCodeEdit() {
    if (AppState.detectedCodeBlocks.length === 0) return;

    AppState.isCodeEditMode = !AppState.isCodeEditMode;

    if (AppState.isCodeEditMode) {
        dom.codePreviewPre.style.display = 'none';
        dom.codeEditArea.style.display = 'block';
        dom.codeEditArea.value = AppState.detectedCodeBlocks[0].content;
        dom.codeEditToggle.textContent = '💾 Selesai Edit';
        dom.codeEditArea.focus();
    } else {
        const editedCode = dom.codeEditArea.value;
        AppState.detectedCodeBlocks[0].content = editedCode;
        
        dom.codeEditArea.style.display = 'none';
        dom.codePreviewPre.style.display = 'block';
        dom.codeEditToggle.textContent = '✏️ Edit Kode';
        
        updateCodePreview();
        
        const sizeInChars = editedCode.length;
        const sizeInLines = editedCode.split('\n').length;
        dom.sizeDisplay.textContent = `${sizeInChars} karakter (${sizeInLines} baris)`;
        
        checkForWarnings();
    }
}

/**
 * Sinkronkan isi textarea edit kode ke state (dipanggil sebelum submit).
 */
function commitCodeEdit() {
    if (AppState.isCodeEditMode && AppState.detectedCodeBlocks.length > 0) {
        AppState.detectedCodeBlocks[0].content = dom.codeEditArea.value;
    }
}

/**
 * Copy kode ke clipboard.
 */
function copyCodeToClipboard(btn) {
    if (AppState.detectedCodeBlocks.length === 0) return;

    const code = AppState.isCodeEditMode 
        ? dom.codeEditArea.value 
        : AppState.detectedCodeBlocks[0].content;

    navigator.clipboard.writeText(code).then(function() {
        if (!btn) return;
        
        const originalText = btn.textContent;
        btn.textContent = '✅ Tersalin!';
        
        setTimeout(function() {
            btn.textContent = originalText;
        }, CONFIG.COPY_FEEDBACK_DELAY_MS);
    }).catch(function(err) {
        console.error('Gagal copy:', err);
        alert('Gagal copy kode');
    });
}

/* =========================================================
 * Aksi approval
 * ========================================================= */

/**
 * Approve kode dan kirim ke Hermes.
 */
function approveCode() {
    if (!AppState.detectedFilePath) {
        alert('⚠️ Path file belum ditentukan! Silakan edit dan input path terlebih dahulu.');
        editFileName();
        return;
    }

    commitCodeEdit();
    AppState.approvalState = 'approved';
    updateApprovalButtons();
    submitResponse(true);
}

/**
 * Edit kode lalu approve.
 */
function editAndApprove() {
    if (!AppState.isCodeEditMode) {
        toggleCodeEdit();
    }
    // User lanjut mengedit, lalu klik "Izinkan & Kirim"
}

/**
 * Tolak kode dan kirim pesan penolakan ke Hermes.
 */
function rejectCode() {
    if (!confirm('Tolak kode ini? Hermes akan diminta untuk memperbaiki.')) return;

    AppState.approvalState = 'rejected';
    updateApprovalButtons();

    const rejectionMessage = 'Saya menolak untuk menulis file ini. Tolong perbaiki dan berikan versi yang lebih baik.';
    dom.responseArea.value = rejectionMessage;
    saveDraft(rejectionMessage);
    
    submitResponse(false);
}

/**
 * Update status tombol approval berdasarkan state.
 */
function updateApprovalButtons() {
    const state = AppState.approvalState;

    if (state === 'approved') {
        dom.approveBtn.disabled = true;
        dom.approveBtn.textContent = '✅ Disetujui';
        dom.approveBtn.classList.add('btn-disabled');
        
        dom.editApproveBtn.disabled = true;
        dom.rejectBtn.disabled = true;
    } 
    else if (state === 'rejected') {
        dom.rejectBtn.disabled = true;
        dom.rejectBtn.textContent = '❌ Ditolak';
        dom.rejectBtn.classList.add('btn-disabled');
        
        dom.approveBtn.disabled = true;
        dom.editApproveBtn.disabled = true;
    } 
    else {
        dom.approveBtn.disabled = false;
        dom.approveBtn.textContent = '✅ Izinkan & Kirim';
        dom.approveBtn.classList.remove('btn-disabled');
        
        dom.rejectBtn.disabled = false;
        dom.rejectBtn.textContent = '❌ Tolak';
        dom.rejectBtn.classList.remove('btn-disabled');
        
        dom.editApproveBtn.disabled = false;
    }
}