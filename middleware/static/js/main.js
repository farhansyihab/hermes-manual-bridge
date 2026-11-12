/**
 * main.js - Bootstrap aplikasi.
 * Dimuat TERAKHIR, setelah semua modul lain tersedia.
 */

/**
 * Konfigurasi Prism autoloader (untuk bahasa yang belum ter-load).
 */
function initPrism() {
    if (window.Prism && Prism.plugins && Prism.plugins.autoloader) {
        Prism.plugins.autoloader.languages_path = CONFIG.PRISM_LANGUAGES_PATH;
    }
}

/**
 * Event listener untuk textarea jawaban DeepSeek:
 * - simpan draft (mitigasi kehilangan data saat refresh)
 * - aktif/nonaktifkan tombol kirim
 * - deteksi kode untuk approval panel (Modul E)
 */
function initResponseEvents() {
    dom.responseArea.addEventListener('input', function () {
        saveDraft(dom.responseArea.value);
        dom.submitBtn.disabled = dom.responseArea.value.trim() === '';
        detectAndShowApprovalPanel();
    });
}

function bootstrap() {
    initDom();
    initPrism();
    initPromptEvents();
    initResponseEvents();

    dom.submitBtn.disabled = true;
    restoreDraft();

    checkPrompt();
    setInterval(checkPrompt, CONFIG.POLL_INTERVAL_MS);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
} else {
    bootstrap();
}