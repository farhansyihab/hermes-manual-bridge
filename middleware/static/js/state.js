/**
 * state.js - State aplikasi terpusat.
 * 
 * Semua modul membaca/menulis lewat objek AppState agar tidak ada
 * variabel global bertebaran dan alur data mudah dilacak.
 * 
 * KEAMANAN & FALLBACK (Fase 3):
 * - Tambah state untuk whitelist validation
 * - Tambah state untuk fallback mode
 * 
 * Version: 1.1.0 (Keamanan & Fallback)
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
    
    // === KEAMANAN & FALLBACK: Whitelist ===
    whitelistValid: null,           // null | true | false
    whitelistError: null,           // string error message
    
    // === KEAMANAN & FALLBACK: Fallback Mode ===
    isFallbackMode: false,          // true jika user pilih fallback
    
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
    
    // KEAMANAN & FALLBACK: Reset whitelist state
    AppState.whitelistValid = null;
    AppState.whitelistError = null;
    
    // KEAMANAN & FALLBACK: Reset fallback mode
    AppState.isFallbackMode = false;
}

/**
 * Reset state prompt (setelah respons terkirim / tugas baru).
 */
function resetPromptState() {
    AppState.originalPromptFromHermes = null;
    AppState.isEditMode = false;
}