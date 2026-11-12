/**
 * config.js - Konstanta global aplikasi Hermes Manual Bridge.
 * Tidak boleh ada DOM access di sini, murni konfigurasi.
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

    // Endpoint backend
    ENDPOINTS: {
        GET_PROMPT: '/get_prompt',
        SUBMIT_RESPONSE: '/submit_response',
        HISTORY: '/history',
        HISTORY_CLEAR: '/history/clear',
        HISTORY_EXPORT: '/history/export/json'
    },

    // Path komponen bahasa Prism (autoloader)
    PRISM_LANGUAGES_PATH: 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/'
};