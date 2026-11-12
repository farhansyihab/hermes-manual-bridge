/**
 * submit.js - Pengiriman respons ke Hermes (POST /submit_response).
 * Mendukung dua mode:
 *   1. Teks biasa (Fase 1)
 *   2. Tool call write_file (Fase 3, hasil approval Modul E)
 */

/**
 * Bangun payload yang dikirim ke backend.
 */
function buildSubmitPayload(isToolCall) {
    const payload = { response: dom.responseArea.value.trim() };

    if (isToolCall && AppState.detectedCodeBlocks.length > 0 && AppState.detectedFilePath) {
        payload.is_tool_call = true;
        payload.tool_call = {
            file_path: AppState.detectedFilePath,
            path_source: AppState.detectedPathSource,
            language: AppState.detectedCodeBlocks[0].language,
            content: AppState.detectedCodeBlocks[0].content
        };
    }

    // Sertakan prompt hasil edit user (audit trail)
    const currentPrompt = dom.promptArea.value;
    if (AppState.originalPromptFromHermes !== null &&
        currentPrompt !== AppState.originalPromptFromHermes) {
        payload.edited_prompt = currentPrompt;
    }

    return payload;
}

/**
 * Reset UI setelah respons sukses dikirim.
 */
function afterSubmitSuccess() {
    setStatus('🎉 Berhasil Dikirim! Menunggu tugas berikutnya...', 'sent');

    dom.responseArea.value = '';
    removeDraft();
    dom.submitBtn.disabled = true;
    dom.submitBtn.textContent = 'Kirim ke Hermes';

    hideApprovalPanel();
    resetPromptState();
    if (AppState.isEditMode) exitEditMode();
    dom.editPromptBtn.disabled = true;
    updateEditedBadge();

    setTimeout(function () {
        setStatus('✅ Menunggu Hermes...', 'idle');
    }, CONFIG.STATUS_RESET_DELAY_MS);
}

/**
 * Reset UI saat gagal kirim agar user bisa mencoba lagi.
 */
function afterSubmitFailure() {
    dom.submitBtn.disabled = false;
    dom.submitBtn.textContent = 'Kirim ke Hermes';
    if (AppState.approvalState !== 'pending') {
        AppState.approvalState = 'pending';
        updateApprovalButtons();
    }
}

/**
 * Kirim respons ke Hermes.
 * @param {boolean} isToolCall - true bila dipanggil dari tombol Approve
 */
async function submitResponse(isToolCall) {
    if (AppState.submitting) return;

    const userResponse = dom.responseArea.value.trim();
    if (!userResponse) return;

    if (isToolCall) commitCodeEdit();

    AppState.submitting = true;
    dom.submitBtn.disabled = true;
    dom.submitBtn.textContent = 'Mengirim...';
    setStatus('📤 Mengirim ke Hermes...', 'waiting');

    try {
        const res = await fetch(CONFIG.ENDPOINTS.SUBMIT_RESPONSE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(buildSubmitPayload(!!isToolCall))
        });

        if (res.ok) {
            afterSubmitSuccess();
        } else {
            alert('Gagal mengirim respons. Coba lagi.');
            afterSubmitFailure();
        }
    } catch (err) {
        console.error('Error submitting:', err);
        alert('Terjadi kesalahan jaringan.');
        afterSubmitFailure();
    } finally {
        AppState.submitting = false;
    }
}