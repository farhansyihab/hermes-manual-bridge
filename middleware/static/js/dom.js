/**
 * dom.js - Registry referensi elemen DOM.
 * Semua modul mengakses elemen lewat objek `dom`, contoh: dom.promptArea
 * initDom() dipanggil sekali oleh main.js saat bootstrap.
 */

const DOM_IDS = [
    // Dashboard - prompt & response
    'promptArea',
    'responseArea',
    'submitBtn',
    'statusBadge',
    'clearDraftBtn',

    // Fitur Edit Prompt
    'editPromptBtn',
    'revertPromptBtn',
    'editedBadge',

    // Modul E - Approval Panel
    'approvalPanel',
    'approvalDetails',
    'toggleIcon',
    'fileNameDisplay',
    'fileNameInput',
    'pathSourceBadge',
    'languageDisplay',
    'sizeDisplay',
    'codePreviewPre',
    'codePreviewCode',
    'codeEditArea',
    'codeEditToggle',
    'approvalWarnings',
    'approveBtn',
    'editApproveBtn',
    'rejectBtn',

    // Tab Riwayat
    'historyList'
];

const dom = {};

function initDom() {
    DOM_IDS.forEach(function (id) {
        dom[id] = document.getElementById(id);
    });
    return dom;
}