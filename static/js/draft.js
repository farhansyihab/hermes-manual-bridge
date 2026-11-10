// Fitur Clear Draft untuk menghapus draft jawaban dari localStorage
document.addEventListener('DOMContentLoaded', function() {
    const clearDraftBtn = document.getElementById('clear-draft-btn');
    
    if (clearDraftBtn) {
        clearDraftBtn.addEventListener('click', function() {
            // Konfirmasi sebelum menghapus untuk mencegah aksi tidak sengaja
            if (confirm('Yakin ingin menghapus semua draft jawaban yang tersimpan?')) {
                
                // Membersihkan semua key di localStorage yang terkait draft
                // Sesuaikan prefix 'draft_' dengan key yang digunakan di aplikasi Anda
                const keysToRemove = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && (key.startsWith('draft_') || key === 'hermes_draft')) {
                        keysToRemove.push(key);
                    }
                }
                
                keysToRemove.forEach(key => localStorage.removeItem(key));
                
                // Reset form input agar tidak menampilkan data lama secara visual
                document.querySelectorAll('form').forEach(form => form.reset());
                
                // Notifikasi berhasil (bisa diganti dengan toast/notification UI jika ada)
                alert('Draft jawaban berhasil dihapus!');
            }
        });
    }
});