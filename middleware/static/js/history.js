/**
 * history.js - Tab Riwayat Percakapan (SQLite di backend).
 * Render memakai string concatenation (bukan template literal) agar
 * source file ini bebas dari karakter backtick sepenuhnya.
 */

async function loadHistory() {
    try {
        const res = await fetch(CONFIG.ENDPOINTS.HISTORY);
        const data = await res.json();

        if (!data.conversations || data.conversations.length === 0) {
            dom.historyList.innerHTML = '<div class="empty-state">Belum ada riwayat percakapan</div>';
            return;
        }

        dom.historyList.innerHTML = data.conversations.map(renderHistoryItem).join('');
    } catch (err) {
        console.error('Gagal memuat riwayat:', err);
        dom.historyList.innerHTML = '<div class="empty-state">Gagal memuat riwayat</div>';
    }
}

/**
 * Render satu kartu riwayat.
 */
function renderHistoryItem(conv) {
    const prompt = conv.prompt || '';
    const wasEdited = conv.original_prompt && conv.original_prompt !== conv.prompt;
    const editedTag = wasEdited ? '<span class="history-edited-tag">✏️ Edited</span>' : '';

    const limit = CONFIG.HISTORY_PREVIEW_LENGTH;
    const preview = escapeHtml(prompt.substring(0, limit)) + (prompt.length > limit ? '...' : '');

    return '' +
        '<div class="history-item">' +
            '<div class="history-header">' +
                '<span class="history-id">#' + conv.id + ' ' + editedTag + '</span>' +
                '<span class="history-time">' + escapeHtml(formatTimestamp(conv.timestamp)) + '</span>' +
            '</div>' +
            '<div class="history-preview"><strong>Prompt:</strong> ' + preview + '</div>' +
            '<div class="history-actions">' +
                '<button class="btn-small" onclick="toggleDetails(' + conv.id + ')">👁️ Lihat Detail</button>' +
                '<button class="btn-small btn-danger" onclick="deleteConversation(' + conv.id + ')">🗑️ Hapus</button>' +
            '</div>' +
            '<div id="details-' + conv.id + '" class="history-details">' +
                renderHistoryDetails(conv, wasEdited) +
            '</div>' +
        '</div>';
}

/**
 * Render isi detail (prompt asli vs prompt edited, respons, info).
 */
function renderHistoryDetails(conv, wasEdited) {
    let html = '';

    if (wasEdited) {
        html += section('📝 Prompt Asli dari Hermes:', conv.original_prompt, 'history-content history-original');
        html += section('📥 Prompt yang Dikirim ke DeepSeek (Edited):', conv.prompt, 'history-content');
    } else {
        html += section('📥 Prompt:', conv.prompt, 'history-content');
    }

    html += section('📤 Response:', conv.response, 'history-content');

    html += '<div class="history-section">' +
                '<h4>ℹ️ Info:</h4>' +
                '<div>Model: ' + escapeHtml(conv.model) + '</div>' +
                '<div>Status: ' + escapeHtml(conv.status) + '</div>' +
            '</div>';

    return html;
}

function section(title, content, cssClass) {
    return '<div class="history-section">' +
               '<h4>' + title + '</h4>' +
               '<div class="' + cssClass + '">' + escapeHtml(content) + '</div>' +
           '</div>';
}

function toggleDetails(id) {
    const details = document.getElementById('details-' + id);
    if (details) details.classList.toggle('show');
}

async function deleteConversation(id) {
    if (!confirm('Yakin ingin menghapus percakapan ini?')) return;
    try {
        const res = await fetch(CONFIG.ENDPOINTS.HISTORY + '/' + id, { method: 'DELETE' });
        if (res.ok) {
            loadHistory();
        } else {
            alert('Gagal menghapus percakapan');
        }
    } catch (err) {
        console.error('Error deleting:', err);
        alert('Terjadi kesalahan jaringan');
    }
}

async function clearHistory() {
    if (!confirm('Yakin ingin menghapus SEMUA riwayat? Tindakan ini tidak bisa dibatalkan!')) return;
    try {
        const res = await fetch(CONFIG.ENDPOINTS.HISTORY_CLEAR, { method: 'DELETE' });
        if (res.ok) {
            loadHistory();
        } else {
            alert('Gagal menghapus riwayat');
        }
    } catch (err) {
        console.error('Error clearing:', err);
        alert('Terjadi kesalahan jaringan');
    }
}

async function exportHistory() {
    try {
        const res = await fetch(CONFIG.ENDPOINTS.HISTORY_EXPORT);
        const data = await res.json();
        const filename = 'hermes-history-' + new Date().toISOString().split('T')[0] + '.json';
        downloadJson(data, filename);
    } catch (err) {
        console.error('Error exporting:', err);
        alert('Gagal export riwayat');
    }
}