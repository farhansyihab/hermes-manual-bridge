/**
 * approval.js - MODUL E: Sandbox Approval Panel + Keamanan & Fallback (Fase 3)
 * 
 * Menampilkan preview kode + info file sebelum tool call dikirim ke Hermes.
 * 
 * Prinsip: TIDAK ada penulisan file tanpa persetujuan user.
 * 
 * Fitur:
 * - Deteksi otomatis kode dalam respons DeepSeek
 * - Ekstraksi path dari prompt Hermes (3 prioritas)
 * - Indikator sumber path (Eksplisit/NL/Manual)
 * - Preview kode dengan syntax highlighting
 * - Validasi keamanan path (format + whitelist)
 * - Deteksi kode berbahaya
 * - Edit kode sebelum approve
 * - KEAMANAN & FALLBACK: Dialog input path manual
 * - KEAMANAN & FALLBACK: Tombol fallback ke mode teks biasa
 * - KEAMANAN & FALLBACK: Validasi whitelist direktori
 * 
 * Version: 1.1.0 (Keamanan & Fallback)
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
    checkWhitelist();  // KEAMANAN & FALLBACK: Cek whitelist
    
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
 * KEAMANAN & FALLBACK: Cek path terhadap whitelist direktori.
 * Tampilkan warning jika path di luar whitelist.
 */
async function checkWhitelist() {
    if (!AppState.detectedFilePath) return;
    
    try {
        const res = await fetch(CONFIG.ENDPOINTS.APPROVAL_CHECK_WHITELIST, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: AppState.detectedFilePath })
        });
        
        if (res.ok) {
            const data = await res.json();
            AppState.whitelistValid = data.is_valid;
            AppState.whitelistError = data.error_message;
            
            // Tampilkan warning whitelist di UI
            updateWhitelistWarning();
        }
    } catch (err) {
        console.error('Gagal cek whitelist:', err);
    }
}

/**
 * KEAMANAN & FALLBACK: Update warning whitelist di UI.
 */
function updateWhitelistWarning() {
    // Hapus warning whitelist lama jika ada
    const oldWarning = document.getElementById('whitelist-warning');
    if (oldWarning) oldWarning.remove();
    
    // Jika path tidak valid terhadap whitelist, tampilkan warning
    if (AppState.whitelistValid === false && AppState.whitelistError) {
        const warningDiv = document.createElement('div');
        warningDiv.id = 'whitelist-warning';
        warningDiv.className = 'warning-item warning-danger';
        warningDiv.innerHTML = '<span class="warning-icon">🚫</span>' +
            '<span>' + escapeHtml(AppState.whitelistError) + '</span>';
        
        // Tambahkan di atas approval warnings
        if (dom.approvalWarnings) {
            dom.approvalWarnings.insertBefore(warningDiv, dom.approvalWarnings.firstChild);
            dom.approvalWarnings.style.display = 'block';
        }
    }
}

/**
 * Toggle detail panel approval.
 */
function toggleApprovalDetails() {
    const isHidden = dom.approvalDetails.style.display === 'none';
    dom.approvalDetails.style.display = isHidden ? 'block' : 'none';
    dom.toggleIcon.textContent = isHidden ? '▼' : '▲';
}

/* ============================================================
 * KEAMANAN & FALLBACK: Dialog Input Path Manual
 * ============================================================ */

/**
 * Tampilkan dialog modal untuk input path manual.
 * Dipanggil ketika path tidak terdeteksi dan user klik "Edit".
 */
function showManualPathDialog() {
    // Buat modal jika belum ada
    let modal = document.getElementById('manual-path-modal');
    if (!modal) {
        modal = createManualPathModal();
        document.body.appendChild(modal);
    }
    
    // Set nilai awal
    const input = modal.querySelector('#manual-path-input');
    input.value = AppState.detectedFilePath || '';
    input.focus();
    
    // Tampilkan modal
    modal.style.display = 'flex';
}

/**
 * Buat elemen modal untuk input path manual.
 */
function createManualPathModal() {
    const modal = document.createElement('div');
    modal.id = 'manual-path-modal';
    modal.className = 'modal-overlay';
    modal.style.display = 'none';
    
    modal.innerHTML = '<div class="modal-content">' +
        '<div class="modal-header">' +
            '<h3>📝 Input Path File Manual</h3>' +
            '<button class="modal-close" onclick="closeManualPathDialog()">×</button>' +
        '</div>' +
        '<div class="modal-body">' +
            '<p>Masukkan path file yang akan ditulis (relatif terhadap project root):</p>' +
            '<input type="text" id="manual-path-input" class="manual-path-input" ' +
                'placeholder="' + CONFIG.MANUAL_INPUT_PLACEHOLDER + '" ' +
                'maxlength="' + CONFIG.MANUAL_INPUT_MAX_LENGTH + '">' +
            '<div class="modal-hint">' +
                '<strong>Contoh:</strong> src/utils/helpers.py, scripts/backup.sh<br>' +
                '<strong>Whitelist direktori:</strong> ' + CONFIG.WHITELISTED_DIRECTORIES.join(', ') +
            '</div>' +
            '<div id="manual-path-validation" class="manual-path-validation"></div>' +
        '</div>' +
        '<div class="modal-footer">' +
            '<button class="btn-modal btn-secondary" onclick="closeManualPathDialog()">Batal</button>' +
            '<button class="btn-modal btn-primary" onclick="saveManualPath()">💾 Simpan</button>' +
        '</div>' +
    '</div>';
    
    // Event listener untuk validasi real-time
    const input = modal.querySelector('#manual-path-input');
    input.addEventListener('input', function() {
        validateManualPathInput(this.value);
    });
    
    // Event listener untuk Enter key
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveManualPath();
        } else if (e.key === 'Escape') {
            closeManualPathDialog();
        }
    });
    
    return modal;
}

/**
 * Validasi input path manual secara real-time.
 */
async function validateManualPathInput(path) {
    const validationDiv = document.getElementById('manual-path-validation');
    if (!validationDiv) return;
    
    if (!path.trim()) {
        validationDiv.innerHTML = '';
        return;
    }
    
    try {
        const res = await fetch(CONFIG.ENDPOINTS.APPROVAL_VALIDATE_PATH, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });
        
        if (res.ok) {
            const data = await res.json();
            
            if (data.is_valid && data.whitelist_valid) {
                validationDiv.innerHTML = '<div class="validation-success">✅ Path valid dan diizinkan</div>';
            } else {
                let errorMsg = '';
                if (!data.is_valid) {
                    errorMsg = data.error_message;
                } else if (!data.whitelist_valid) {
                    errorMsg = data.whitelist_error;
                }
                validationDiv.innerHTML = '<div class="validation-error">❌ ' + escapeHtml(errorMsg) + '</div>';
            }
        }
    } catch (err) {
        console.error('Gagal validasi path:', err);
        validationDiv.innerHTML = '<div class="validation-error">❌ Error validasi</div>';
    }
}

/**
 * Simpan path manual yang diinput user.
 */
async function saveManualPath() {
    const input = document.querySelector('#manual-path-input');
    const newPath = input.value.trim();
    
    if (!newPath) {
        alert('⚠️ Path tidak boleh kosong!');
        return;
    }
    
    // Validasi path di backend
    try {
        const res = await fetch(CONFIG.ENDPOINTS.APPROVAL_VALIDATE_PATH, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: newPath })
        });
        
        if (res.ok) {
            const data = await res.json();
            
            if (!data.is_valid) {
                alert('❌ Path tidak valid: ' + data.error_message);
                return;
            }
            
            if (!data.whitelist_valid) {
                const confirmMsg = '⚠️ ' + data.whitelist_error + '\n\n' +
                    'Yakin ingin melanjutkan?';
                if (!confirm(confirmMsg)) {
                    return;
                }
            }
        }
    } catch (err) {
        console.error('Gagal validasi path:', err);
        alert('❌ Error validasi path');
        return;
    }
    
    // Simpan path
    AppState.detectedFilePath = newPath;
    AppState.detectedPathSource = 'manual';
    
    // Update UI
    updateFileInfo();
    checkForWarnings();
    checkWhitelist();
    
    // Tutup modal
    closeManualPathDialog();
}

/**
 * Tutup dialog input path manual.
 */
function closeManualPathDialog() {
    const modal = document.getElementById('manual-path-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Masuk ke mode edit nama file (legacy - sekarang pakai modal).
 */
function editFileName() {
    showManualPathDialog();
}

/**
 * Batalkan edit nama file (legacy).
 */
function cancelEditFileName() {
    closeManualPathDialog();
}

/* ============================================================
 * Edit kode sebelum approve
 * ============================================================ */

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

/* ============================================================
 * Aksi approval
 * ============================================================ */

/**
 * Approve kode dan kirim ke Hermes.
 */
function approveCode() {
    if (!AppState.detectedFilePath) {
        alert('⚠️ Path file belum ditentukan! Silakan edit dan input path terlebih dahulu.');
        showManualPathDialog();
        return;
    }
    
    // KEAMANAN & FALLBACK: Cek whitelist sebelum approve
    if (AppState.whitelistValid === false) {
        const confirmMsg = '⚠️ Path di luar direktori yang diizinkan!\n\n' +
            AppState.whitelistError + '\n\n' +
            'Yakin ingin melanjutkan?';
        if (!confirm(confirmMsg)) {
            return;
        }
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
 * KEAMANAN & FALLBACK: Kirim sebagai teks biasa (fallback mode).
 * Dipanggil ketika parsing gagal atau user pilih fallback.
 */
function sendAsFallback() {
    if (!CONFIG.ENABLE_FALLBACK_TO_TEXT) {
        alert('⚠️ Mode fallback tidak diizinkan dalam konfigurasi.');
        return;
    }
    
    const confirmMsg = CONFIG.FALLBACK_CONFIRM_MESSAGE + '\n\n' +
        CONFIG.FALLBACK_WARNING_MESSAGE;
    
    if (!confirm(confirmMsg)) return;
    
    // Set flag fallback
    AppState.isFallbackMode = true;
    
    // Kirim sebagai teks biasa
    submitResponse(false, true);
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
        
        if (dom.fallbackBtn) {
            dom.fallbackBtn.disabled = true;
        }
    }
    else if (state === 'rejected') {
        dom.rejectBtn.disabled = true;
        dom.rejectBtn.textContent = '❌ Ditolak';
        dom.rejectBtn.classList.add('btn-disabled');
        
        dom.approveBtn.disabled = true;
        dom.editApproveBtn.disabled = true;
        
        if (dom.fallbackBtn) {
            dom.fallbackBtn.disabled = true;
        }
    }
    else {
        dom.approveBtn.disabled = false;
        dom.approveBtn.textContent = '✅ Izinkan & Kirim';
        dom.approveBtn.classList.remove('btn-disabled');
        
        dom.rejectBtn.disabled = false;
        dom.rejectBtn.textContent = '❌ Tolak';
        dom.rejectBtn.classList.remove('btn-disabled');
        
        dom.editApproveBtn.disabled = false;
        
        if (dom.fallbackBtn) {
            dom.fallbackBtn.disabled = false;
        }
    }
}