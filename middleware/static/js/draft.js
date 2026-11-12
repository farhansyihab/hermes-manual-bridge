/**
 * draft.js - Mitigasi risiko kehilangan data: draft jawaban di localStorage.
 * Menggantikan static/js/draft.js versi lama (root) yang tidak ter-mount.
 */

function saveDraft(text) {
    try {
        localStorage.setItem(CONFIG.DRAFT_STORAGE_KEY, text);
    } catch (err) {
        console.warn('Gagal menyimpan draft:', err);
    }
}

function readDraft() {
    try {
        return localStorage.getItem(CONFIG.DRAFT_STORAGE_KEY) || '';
    } catch (err) {
        console.warn('Gagal membaca draft:', err);
        return '';
    }
}

function removeDraft() {
    try {
        localStorage.removeItem(CONFIG.DRAFT_STORAGE_KEY);
    } catch (err) {
        console.warn('Gagal menghapus draft:', err);
    }
}

/**
 * Restore draft ke textarea saat halaman dibuka.
 */
function restoreDraft() {
    const saved = readDraft();
    if (!saved) return;
    dom.responseArea.value = saved;
    dom.submitBtn.disabled = saved.trim() === '';
    detectAndShowApprovalPanel();
}

/**
 * Handler tombol "Clear Draft" (dipanggil dari onclick HTML).
 */
function clearDraftWithConfirm() {
    if (!confirm('Yakin ingin menghapus draft jawaban yang tersimpan?')) return;

    removeDraft();

    // Bersihkan key lama bila ada (backward compatibility)
    try {
        CONFIG.LEGACY_DRAFT_KEYS.forEach(function (key) {
            localStorage.removeItem(key);
        });
        const legacy = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.indexOf(CONFIG.LEGACY_DRAFT_PREFIX) === 0) {
                legacy.push(key);
            }
        }
        legacy.forEach(function (key) {
            localStorage.removeItem(key);
        });
    } catch (err) {
        console.warn('Gagal membersihkan draft lama:', err);
    }

    dom.responseArea.value = '';
    dom.submitBtn.disabled = true;
    hideApprovalPanel();
}