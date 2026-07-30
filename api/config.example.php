<?php
declare(strict_types=1);

/**
 * config.example.php — template config. Salin ke config.local.php dan isi nilainya.
 *
 * Cara generate JWT_SECRET dan CHATBOT_TRAIN_KEY:
 *   php -r "echo bin2hex(random_bytes(32));"
 */
return [
    'JWT_SECRET' => 'GANTI-DENGAN-64-CHAR-HEX-RANDOM',
    'JWT_EXPIRY' => 7200,

    // Di produksi React dan API dilayani dari origin yang sama, jadi CORS tidak
    // terpakai. Daftar ini hanya untuk dev (Vite di port lain).
    'CORS_ALLOWED_ORIGINS' => [
        'http://localhost:5173',
        'http://localhost:4173',
        'http://127.0.0.1:5173',
    ],

    // Layanan Flask CBF. Dipanggil server-to-server oleh PHP, tidak pernah dari
    // browser — biarkan terikat ke loopback dan jangan dibuka ke publik.
    'CBF_URL' => 'http://127.0.0.1:5000',

    'CHATBOT_TRAIN_KEY' => 'GANTI-DENGAN-SECRET-STRING',

    'LOGIN_MAX_ATTEMPTS' => 5,
    'LOGIN_WINDOW_SECONDS' => 900,

    'BATAS_PINJAM' => 3,

    'DB_HOST' => 'localhost',
    'DB_NAME' => 'libra_db',
    'DB_USER' => 'root',
    'DB_PASS' => '',
];
