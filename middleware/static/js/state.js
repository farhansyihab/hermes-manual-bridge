/**
 * state.js - State aplikasi terpusat.
 * Semua modul membaca/menulis lewat objek AppState agar tidak ada
 * variabel global bertebaran dan alur data mudah dilacak.
 */
const AppState = {
    // === Fitur Edit Prompt ===
    originalPromptFromHermes: null,
    isEditMode: false,

    // === Modul E: Approval Panel ===
    detectedCodeBlocks: [],
    detectedFilePath: null,
    detectedPathSource: 'manual',   // 'explicit' | 'natural_language' | 'manual'
    isCodeEditMode: false,
    approvalState: 'pending',       // 'pending' | 'approved' | 'rejected'

    // === Flags internal ===
    submitting: false
};

/**
 * Reset state approval ke kondisi awal.
 */
function resetApprovalState() {
    AppState.detectedCodeBlocks = [];
    AppState.detectedFilePath = null;
    AppState.detectedPathSource = 'manual';
    AppState.isCodeEditMode = false;
    AppState.approvalState = 'pending';
}

/**
 * Reset state prompt (setelah respons terkirim / tugas baru).
 */
function resetPromptState() {
    AppState.originalPromptFromHermes = null;
    AppState.isEditMode = false;
}