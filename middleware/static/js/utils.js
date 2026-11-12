/**
 * utils.js - Helper umum (tanpa state, tanpa logika bisnis).
 */

/**
 * Escape teks agar aman disisipkan sebagai HTML.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text === null || text === undefined ? '' : String(text);
    return div.innerHTML;
}

/**
 * Update badge status di header.
 * @param {string} text  - teks status
 * @param {string} kind  - 'idle' | 'waiting' | 'sent'
 */
function setStatus(text, kind) {
    if (!dom.statusBadge) return;
    dom.statusBadge.textContent = text;
    dom.statusBadge.className = 'status status-' + (kind || 'idle');
}

/**
 * Format timestamp SQLite (UTC) ke locale Indonesia.
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return '-';
    // Timestamp SQLite "YYYY-MM-DD HH:MM:SS" perlu diconvert agar diparse sbg UTC
    const iso = String(timestamp).replace(' ', 'T');
    const date = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
    if (isNaN(date.getTime())) return String(timestamp);
    return date.toLocaleString('id-ID');
}

/**
 * Trigger download objek JSON sebagai file.
 */
function downloadJson(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}