/**
 * parser.js - Parsing respons DeepSeek & ekstraksi path dari prompt Hermes.
 * KONSISTENSI: logika di sini mirrors app/parser.py dan app/path_extractor.py.
 * Jika regex diubah, update juga modul Python terkait beserta unit test-nya.
 * 
 * Karakter backtick dibangun via String.fromCharCode(96) agar source file
 * ini tidak pernah memuat urutan tiga backtick literal.
 */

const BACKTICK = String.fromCharCode(96);

/**
 * Ekstrak semua blok kode berpagar (fenced) dari teks.
 * @param {string} text - Teks respons dari DeepSeek
 * @returns {Array<{language: string, content: string}>}
 */
function extractCodeBlocks(text) {
    if (!text) return [];

    const fence = BACKTICK + BACKTICK + BACKTICK;
    const pattern = new RegExp(fence + '(\\w+)?\\s*\\n([\\s\\S]*?)' + fence, 'g');
    
    const blocks = [];
    let match;
    
    while ((match = pattern.exec(text)) !== null) {
        blocks.push({
            language: (match[1] || 'plaintext').toLowerCase(),
            content: match[2].trim()
        });
    }

    return blocks;
}

/**
 * Ekstrak path file dari prompt Hermes (hierarki 3 prioritas).
 * 
 * Prioritas 1: Format eksplisit [FILE: path]
 * Prioritas 2: Pola bahasa natural
 * Prioritas 3: Manual fallback (path = null)
 * 
 * @param {string} prompt - Prompt dari Hermes Agent
 * @returns {{path: (string|null), source: string}}
 */
function extractFilePathFromPrompt(prompt) {
    if (!prompt) {
        return { path: null, source: 'manual' };
    }

    // PRIORITAS 1: [FILE: path]
    const explicitMatch = prompt.match(/\[FILE:\s*([^\]]+)\]/i);
    if (explicitMatch) {
        const path = explicitMatch[1]
            .trim()
            .replace(new RegExp(BACKTICK, 'g'), '')
            .trim();
        
        if (path) {
            return { path: path, source: 'explicit' };
        }
    }

    // PRIORITAS 2: pola bahasa natural
    const pathPattern = '[A-Za-z0-9_][A-Za-z0-9_./-]*\\.[A-Za-z0-9]+';
    const nlPatterns = [
        new RegExp('(?:file|berkas)\\s+' + BACKTICK + '?(' + pathPattern + ')' + BACKTICK + '?', 'i'),
        new RegExp('(?:named|bernama|dengan\\s+nama)\\s+' + BACKTICK + '?(' + pathPattern + ')' + BACKTICK + '?', 'i'),
        new RegExp('(?:simpan\\s+ke|save\\s+to|tulis\\s+ke)\\s+' + BACKTICK + '?(' + pathPattern + ')' + BACKTICK + '?', 'i'),
        new RegExp(BACKTICK + '(' + pathPattern + ')' + BACKTICK, 'i'),
        /\b([A-Za-z0-9_-]+\.(?:py|js|ts|jsx|tsx|html|css|scss|json|yaml|yml|toml|ini|cfg|md|txt|csv|sql|sh|bash|cpp|cc|c|h|hpp|java|go|rs|rb|php|lua|xml|env))\b/i
    ];

    for (let i = 0; i < nlPatterns.length; i++) {
        const match = prompt.match(nlPatterns[i]);
        if (match) {
            return { path: match[1], source: 'natural_language' };
        }
    }

    // PRIORITAS 3: fallback manual
    return { path: null, source: 'manual' };
}

/**
 * Metadata tampilan untuk indikator sumber path.
 * Konsisten dengan app/detect_path_source.py (ikon & deskripsi).
 * 
 * @param {string} source - 'explicit' | 'natural_language' | 'manual'
 * @returns {{description: string, icon: string, color: string}}
 */
function getPathSourceInfo(source) {
    const sources = {
        'explicit': { 
            description: 'Format Eksplisit [FILE: ...]', 
            icon: '🎯',
            color: '#28a745'
        },
        'natural_language': { 
            description: 'Pola Bahasa Natural', 
            icon: '💬',
            color: '#ffc107'
        },
        'manual': { 
            description: 'Input Manual Diperlukan', 
            icon: '✍️',
            color: '#dc3545'
        }
    };

    return sources[source] || { 
        description: 'Tidak Diketahui', 
        icon: '❓',
        color: '#6c757d'
    };
}

/**
 * Cek apakah path berpotensi berbahaya.
 * Mirrors validate_path() di app/path_extractor.py.
 * 
 * @param {string} path - Path file yang akan dicek
 * @returns {boolean} - true jika mencurigakan
 */
function isPathSuspicious(path) {
    if (!path) return false;

    const suspiciousPatterns = [
        /^\//,                  // absolute path Unix
        /^[A-Za-z]:/,           // absolute path Windows
        /\.\./,                 // path traversal
        /^\/etc\//,
        /^\/proc\//,
        /^\/sys\//,
        /^\/dev\//,
        /^\/root\//,
        /\.ssh/i,
        /\.env$/i,
        /password/i,
        /secret/i,
        /private[_-]?key/i
    ];

    return suspiciousPatterns.some(function(pattern) {
        return pattern.test(path);
    });
}

/**
 * Deteksi command/pola kode berbahaya (basic heuristic).
 * 
 * @param {string} code - Isi kode yang akan dicek
 * @returns {string[]} - daftar deskripsi pola yang terdeteksi
 */
function containsDangerousCode(code) {
    if (!code) return [];

    const patterns = [
        { pattern: /rm\s+-rf\s+\//, desc: 'rm -rf /' },
        { pattern: /rm\s+-rf\s+~/, desc: 'rm -rf ~' },
        { pattern: /mkfs\./, desc: 'mkfs (format disk)' },
        { pattern: /dd\s+if=/, desc: 'dd (disk destroyer)' },
        { pattern: /:\(\)\s*\{.*:\|:.*\}/, desc: 'fork bomb' },
        { pattern: /chmod\s+-R\s+777\s+\//, desc: 'chmod 777 /' },
        { pattern: /DROP\s+TABLE/i, desc: 'SQL DROP TABLE' },
        { pattern: /DROP\s+DATABASE/i, desc: 'SQL DROP DATABASE' },
        { pattern: /TRUNCATE\s+TABLE/i, desc: 'SQL TRUNCATE' },
        { pattern: /DELETE\s+FROM\s+\w+\s*;/i, desc: 'SQL DELETE tanpa WHERE' },
        { pattern: /os\.system\s*\(\s*['"]rm/, desc: 'Python os.system rm' },
        { pattern: /subprocess\.shell\s*=\s*True/, desc: 'subprocess shell=True' },
        { pattern: /eval\s*\(/, desc: 'eval() - code injection risk' },
        { pattern: /exec\s*\(/, desc: 'exec() - code execution' }
    ];

    const found = [];
    patterns.forEach(function(p) {
        if (p.pattern.test(code)) found.push(p.desc);
    });

    return found;
}