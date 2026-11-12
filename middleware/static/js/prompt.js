/**
 * prompt.js - Polling prompt dari Hermes + fitur Edit Prompt (audit trail).
 */

/**
 * Masuk / keluar mode edit prompt.
 */
function toggleEditPrompt() {
    if (!AppState.isEditMode) {
        AppState.isEditMode = true;
        dom.promptArea.readOnly = false;
        dom.promptArea.classList.add('editing');
        dom.editPromptBtn.textContent = '💾 Selesai Edit';
        dom.editPromptBtn.classList.remove('btn-secondary');
        dom.editPromptBtn.classList.add('btn-success');
        dom.revertPromptBtn.style.display = 'inline-block';
        dom.promptArea.focus();
    } else {
        exitEditMode();
    }
}

function exitEditMode() {
    AppState.isEditMode = false;
    dom.promptArea.readOnly = true;
    dom.promptArea.classList.remove('editing');
    dom.editPromptBtn.textContent = '✏️ Edit Prompt';
    dom.editPromptBtn.classList.remove('btn-success');
    dom.editPromptBtn.classList.add('btn-secondary');
    dom.revertPromptBtn.style.display = 'none';
    updateEditedBadge();
}

function revertPrompt() {
    if (AppState.originalPromptFromHermes === null) return;
    if (!confirm('Kembalikan prompt ke versi asli dari Hermes?')) return;
    dom.promptArea.value = AppState.originalPromptFromHermes;
    updateEditedBadge();
    detectAndShowApprovalPanel();
}

/**
 * Tampilkan badge "Edited" bila prompt berbeda dari versi asli Hermes.
 */
function updateEditedBadge() {
    if (AppState.originalPromptFromHermes === null) {
        dom.editedBadge.style.display = 'none';
        return;
    }
    const isEdited = dom.promptArea.value !== AppState.originalPromptFromHermes;
    dom.editedBadge.style.display = isEdited ? 'inline-block' : 'none';
}

/**
 * Polling GET /get_prompt (dipanggil berkala oleh main.js).
 */
async function checkPrompt() {
    try {
        const res = await fetch(CONFIG.ENDPOINTS.GET_PROMPT);
        const data = await res.json();

        if (data.status === 'waiting' && data.prompt) {
            const promptChanged =
                dom.promptArea.value !== data.prompt &&
                AppState.originalPromptFromHermes !== data.original_prompt;

            if (promptChanged) {
                AppState.originalPromptFromHermes = data.original_prompt || data.prompt;
                dom.promptArea.value = data.prompt;

                if (AppState.isEditMode) exitEditMode();

                dom.editPromptBtn.disabled = false;
                updateEditedBadge();
                setStatus('⏳ Prompt Diterima! Menunggu Jawaban Anda...', 'waiting');

                // Path bisa berubah karena prompt baru
                detectAndShowApprovalPanel();
            }
        } else {
            dom.editPromptBtn.disabled = true;
            setStatus('✅ Menunggu Hermes...', 'idle');
        }
    } catch (err) {
        console.error('Gagal mengecek prompt:', err);
    }
}

/**
 * Daftarkan event listener terkait prompt (dipanggil main.js).
 */
function initPromptEvents() {
    dom.promptArea.addEventListener('input', function () {
        updateEditedBadge();
        // Path diekstrak dari prompt, jadi perlu re-deteksi
        detectAndShowApprovalPanel();
    });
}