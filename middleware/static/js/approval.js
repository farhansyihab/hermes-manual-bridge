/**
 * approval.js - MODUL E: Sandbox Approval Panel.
 * Menampilkan preview kode + info file sebelum tool call dikirim ke Hermes.
 * Prinsip: TIDAK ada penulisan file tanpa persetujuan user.
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

function hideApprovalPanel() {
    dom.approvalPanel.style.display = 'none';
    resetApprovalState();
}

/**
 * Update bagian info file: nama, sumber path, bahasa, ukuran.
 */
function updateFileInfo() {
    // Nama file
    if (AppState.detectedFilePath) {
        dom.fileNameDisplay.textContent = AppState.detectedFilePath;
        dom.fileNameDisplay.classList.remove('no-path');
    } else {
        dom.fileNameDisplay.textContent = '⚠️ Tidak terdeteksi - Klik Edit untuk input manual';
        dom.fileNameDisplay.classList.add('no-path');
    }

    // Sumber path
    const sourceInfo = getPathSourceInfo(AppState.detectedPathSource);
    dom.pathSourceBadge.className = 'path-source-badge source-' + AppState.detectedPathSource;
    dom.pathSourceBadge.textContent = sourceInfo.icon + ' ' + sourceInfo.description;

    // Bahasa & ukuran
    if (AppState.detectedCodeBlocks.length > 0) {
        const first = AppState.detectedCodeBlocks[0];
        dom.languageDisplay.textContent = first.language;
        dom.languageDisplay.className = 'language-badge lang-' + first.language;
        dom.sizeDisplay.textContent = first.content.length + ' karakter';
    }
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

    if (!AppState.detectedFilePath) {
        warnings.push({
            type: 'warning',
            icon: '⚠️',
            message: 'Path file tidak terdeteksi. Silakan input manual sebelum approve.'
        });
    } else if (isPathSuspicious(AppState.detectedFilePath)) {
        warnings.push({
            type: 'danger',
            icon: '🚨',
            message: 'Path mencurigakan terdeteksi! Pastikan ini aman sebelum approve.'
        });
    }

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

    if (warnings.length === 0) {
        dom.approvalWarnings.style.display = 'none';
        dom.approvalWarnings.innerHTML = '';
        return;
    }

    dom.approvalWarnings.innerHTML = warnings.map(function (w) {
        return '<div class="warning-item warning-' + w.type + '">' +
               '<span class="warning-icon">' + w.icon + '</span>' +
               '<span>' + escapeHtml(w.message) + '</span>' +
               '</div>';
    }).join('');
    dom.approvalWarnings.style.display = 'block';
}

function toggleApprovalDetails() {
    const isHidden = dom.approvalDetails.style.display === 'none';
    dom.approvalDetails.style.display = isHidden ? 'block' : 'none';
    dom.toggleIcon.textContent = isHidden ? '▼' : '▲';
}

/* =========================================================
   Edit nama file manual (Prioritas 3 - fallback)
   ========================================================= */
function editFileName() {
    dom.fileNameDisplay.style.display = 'none';
    dom.fileNameInput.style.display = 'block';
    dom.fileNameInput.value = AppState.detectedFilePath || '';
    dom.fileNameInput.focus();

    dom.fileNameInput.onblur = saveFileName;
    dom.fileNameInput.onkeydown = function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveFileName();
        } else if (e.key === 'Escape') {
            cancelEditFileName();
        }
    };
}

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

function cancelEditFileName() {
    dom.fileNameInput.onblur = null;
    dom.fileNameInput.style.display = 'none';
    dom.fileNameDisplay.style.display = 'block';
}

/* =========================================================
   Edit kode sebelum approve
   ========================================================= */
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
        dom.sizeDisplay.textContent = editedCode.length + ' karakter';
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
 * @param {HTMLElement} btn - tombol pemicu (untuk feedback visual)
 */
function copyCodeToClipboard(btn) {
    if (AppState.detectedCodeBlocks.length === 0) return;

    const code = AppState.isCodeEditMode
        ? dom.codeEditArea.value
        : AppState.detectedCodeBlocks[0].content;

    navigator.clipboard.writeText(code).then(function () {
        if (!btn) return;
        const originalText = btn.textContent;
        btn.textContent = '✅ Tersalin!';
        setTimeout(function () {
            btn.textContent = originalText;
        }, CONFIG.COPY_FEEDBACK_DELAY_MS);
    }).catch(function (err) {
        console.error('Gagal copy:', err);
        alert('Gagal copy kode');
    });
}

/* =========================================================
   Aksi approval
   ========================================================= */
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

function editAndApprove() {
    if (!AppState.isCodeEditMode) {
        toggleCodeEdit();
    }
    // User lanjut mengedit, lalu klik "Izinkan & Kirim"
}

function rejectCode() {
    if (!confirm('Tolak kode ini? Hermes akan diminta untuk memperbaiki.')) return;

    AppState.approvalState = 'rejected';
    updateApprovalButtons();

    const rejectionMessage = 'Saya menolak untuk menulis file ini. Tolong perbaiki dan berikan versi yang lebih baik.';
    dom.responseArea.value = rejectionMessage;
    saveDraft(rejectionMessage);
    submitResponse(false);
}

function updateApprovalButtons() {
    const state = AppState.approvalState;

    if (state === 'approved') {
        dom.approveBtn.disabled = true;
        dom.approveBtn.textContent = '✅ Disetujui';
        dom.approveBtn.classList.add('btn-disabled');
        dom.editApproveBtn.disabled = true;
        dom.rejectBtn.disabled = true;
    } else if (state === 'rejected') {
        dom.rejectBtn.disabled = true;
        dom.rejectBtn.textContent = '❌ Ditolak';
        dom.rejectBtn.classList.add('btn-disabled');
        dom.approveBtn.disabled = true;
        dom.editApproveBtn.disabled = true;
    } else {
        dom.approveBtn.disabled = false;
        dom.approveBtn.textContent = '✅ Izinkan & Kirim';
        dom.approveBtn.classList.remove('btn-disabled');
        dom.rejectBtn.disabled = false;
        dom.rejectBtn.textContent = '❌ Tolak';
        dom.rejectBtn.classList.remove('btn-disabled');
        dom.editApproveBtn.disabled = false;
    }
}