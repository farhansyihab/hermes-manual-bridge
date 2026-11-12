/**
 * tabs.js - Navigasi tab Dashboard / Riwayat.
 */

/**
 * Pindah tab.
 * @param {string} tabName - 'dashboard' | 'history'
 * @param {HTMLElement} btn - tombol tab yang diklik (diterima eksplisit,
 *                            tidak lagi bergantung pada window.event)
 */
function switchTab(tabName, btn) {
    document.querySelectorAll('.tab').forEach(function (t) {
        t.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(function (c) {
        c.classList.remove('active');
    });

    if (btn) {
        btn.classList.add('active');
    }

    const target = document.getElementById(tabName + '-tab');
    if (target) target.classList.add('active');

    if (tabName === 'history') {
        loadHistory();
    }
}