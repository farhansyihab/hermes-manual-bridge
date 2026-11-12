/**
 * config.js - Konstanta global aplikasi Hermes Manual Bridge.
 * 
 * KEAMANAN & FALLBACK (Fase 3):
 * - Tambah konfigurasi whitelist direktori
 * - Tambah konfigurasi untuk dialog manual input
 * - Tambah konfigurasi untuk mode fallback
 * 
 * Tidak boleh ada DOM access di sini, murni konfigurasi.
 * 
 * Version: 1.1.0 (Keamanan & Fallback)
 */
const CONFIG = {
    // Interval polling prompt dari Hermes (ms)
    POLL_INTERVAL_MS: 2000,
    
    // Key localStorage untuk draft jawaban
    DRAFT_STORAGE_KEY: 'hermes_draft_response',
    
    // Key lama (dibersihkan saat Clear Draft, backward compatibility)
    LEGACY_DRAFT_KEYS: ['hermes_draft'],
    LEGACY_DRAFT_PREFIX: 'draft_',
    
    // Delay reset badge status setelah sukses kirim (ms)
    STATUS_RESET_DELAY_MS: 3000,
    
    // Delay feedback tombol copy (ms)
    COPY_FEEDBACK_DELAY_MS: 1500,
    
    // Panjang maksimal preview prompt di daftar riwayat
    HISTORY_PREVIEW_LENGTH: 100,
    
    // ============================================================
    // ENDPOINT BACKEND
    // ============================================================
    ENDPOINTS: {
        GET_PROMPT: '/get_prompt',
        SUBMIT_RESPONSE: '/submit_response',
        HISTORY: '/history',
        HISTORY_CLEAR: '/history/clear',
        HISTORY_EXPORT: '/history/export/json',
        
        // KEAMANAN & FALLBACK: Endpoint baru
        APPROVAL_VALIDATE_PATH: '/approval/validate-path',
        APPROVAL_PATH_INFO: '/approval/path-info',
        APPROVAL_CHECK_WHITELIST: '/approval/check-whitelist',
        APPROVAL_WHITELIST_INFO: '/approval/whitelist-info',
        APPROVAL_VALIDATE_CONTENT: '/approval/validate-content',
        APPROVAL_SOURCE_INFO: '/approval/source-info'
    },
    
    // Path komponen bahasa Prism (autoloader)
    PRISM_LANGUAGES_PATH: 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/',
    
    // ============================================================
    // KEAMANAN & FALLBACK: Konfigurasi Whitelist
    // ============================================================
    // Daftar direktori yang di-whitelist (harus sinkron dengan backend)
    // UI akan menampilkan warning jika path di luar whitelist
    WHITELISTED_DIRECTORIES: [
        '/home/farhan/Proyek/Hermes'
        // Tambahkan direktori lain jika diperlukan
    ],
    
    // Pesan warning untuk path di luar whitelist
    WHITELIST_WARNING_MESSAGE: 'Path di luar direktori yang diizinkan. Hanya boleh menulis di direktori yang ter-whitelist.',
    
    // ============================================================
    // KEAMANAN & FALLBACK: Konfigurasi Dialog Manual
    // ============================================================
    // Maksimal panjang path input manual
    MANUAL_INPUT_MAX_LENGTH: 500,
    
    // Placeholder untuk input path manual
    MANUAL_INPUT_PLACEHOLDER: 'path/ke/file.ext',
    
    // ============================================================
    // KEAMANAN & FALLBACK: Konfigurasi Mode Fallback
    // ============================================================
    // Izinkan fallback ke mode teks biasa jika parsing gagal
    ENABLE_FALLBACK_TO_TEXT: true,
    
    // Pesan konfirmasi untuk fallback
    FALLBACK_CONFIRM_MESSAGE: 'Parsing gagal atau path tidak valid. Kirim sebagai teks biasa?',
    
    // Pesan warning untuk fallback
    FALLBACK_WARNING_MESSAGE: 'Respons akan dikirim sebagai teks biasa (bukan tool call). Hermes tidak akan menulis file.'
};