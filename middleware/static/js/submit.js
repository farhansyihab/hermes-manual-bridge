/**
 * submit.js - Pengiriman respons ke Hermes (POST /submit_response).
 * 
 * MENDUKUNG 3 MODE (Fase 3 - Keamanan & Fallback):
 * 1. Mode Tool Call: kirim sebagai tool call write_file (default)
 * 2. Mode Fallback: kirim sebagai teks biasa (jika parsing gagal)
 * 3. Mode Teks Biasa: kirim sebagai teks biasa (backward compatibility)
 * 
 * Version: 1.1.0 (Keamanan & Fallback)
 */

/**
 * Bangun payload yang dikirim ke backend.
 * 
 * @param {boolean} isToolCall - true jika kirim sebagai tool call
 * @param {boolean} isFallback - true jika kirim sebagai fallback (teks biasa)
 * @returns {object} Payload untuk POST /submit_response
 */
function buildSubmitPayload(isToolCall, isFallback) {
    const payload = {
        response: dom.responseArea.value.trim()
    };
    
    // KEAMANAN & FALLBACK: Flag untuk mode fallback
    if (isFallback) {
        payload.is_fallback = true;
        payload.is_tool_call = false;
    }
    
    // Mode tool call
    else if (isToolCall && AppState.detectedCodeBlocks.length > 0 && AppState.detectedFilePath) {
        payload.is_tool_call = true;
        payload.is_fallback = false;
        payload.tool_call = {
            file_path: AppState.detectedFilePath,
            path_source: AppState.detectedPathSource,
            language: AppState.detectedCodeBlocks[0].language,
            content: AppState.detectedCodeBlocks[0].content
        };
    }
    
    // Mode teks biasa (default)
    else {
        payload.is_tool_call = false;
        payload.is_fallback = false;
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
    
    setTimeout(function() {
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
 * 
 * @param {boolean} isToolCall - true bila dipanggil dari tombol Approve
 * @param {boolean} isFallback - true bila dipanggil dari tombol Fallback
 */
async function submitResponse(isToolCall, isFallback) {
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
            body: JSON.stringify(buildSubmitPayload(!!isToolCall, !!isFallback))
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