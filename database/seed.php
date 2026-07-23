<?php
/**
 * LIBRA — Database Seed Script
 * Jalankan: php database/seed.php
 * atau via CLI: C:\xampp\php\php.exe database\seed.php
 *
 * Script ini idempoten — dapat dijalankan ulang jika data perlu di-reset.
 * Urutan INSERT: kategori → buku → users → peminjaman (FK-safe).
 */

declare(strict_types=1);

// ── Koneksi PDO (utf8mb4 wajib di DSN, bukan SET NAMES terpisah) ────────
try {
    $pdo = new PDO(
        'mysql:host=localhost;dbname=libra_db;charset=utf8mb4',
        'root',
        '',  // Default XAMPP: password root kosong. Ubah jika berbeda.
        [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]
    );
} catch (PDOException $e) {
    die("Koneksi gagal: " . $e->getMessage() . "\n");
}

echo "Koneksi berhasil. Mulai seeding...\n\n";

// ── TRUNCATE (urutan terbalik dari INSERT karena FK) ─────────────────────
$pdo->exec("SET FOREIGN_KEY_CHECKS=0");
$pdo->exec("TRUNCATE TABLE peminjaman");
$pdo->exec("TRUNCATE TABLE buku");
$pdo->exec("TRUNCATE TABLE users");
$pdo->exec("TRUNCATE TABLE kategori");
$pdo->exec("SET FOREIGN_KEY_CHECKS=1");
echo "Tabel dikosongkan.\n";

// ════════════════════════════════════════════════════════════════════════
// 1. INSERT KATEGORI (D-14: minimal 10, mencakup pelajaran SMP + umum)
// ════════════════════════════════════════════════════════════════════════
$kategoriList = [
    'Matematika',
    'IPA',
    'IPS',
    'Bahasa Indonesia',
    'Bahasa Inggris',
    'PKN',
    'Sejarah',
    'Biologi',
    'Fisika',
    'Kimia',
    'Fiksi',
    'Non-Fiksi',
    'Sains',
    'Teknologi',
    'Komik',
];

$stmtKategori = $pdo->prepare(
    "INSERT INTO kategori (nama) VALUES (?)"
);
foreach ($kategoriList as $nama) {
    $stmtKategori->execute([$nama]);
}

// Ambil kategori_id yang sudah dibuat
$kategoriMap = [];
foreach ($pdo->query("SELECT id, nama FROM kategori") as $row) {
    $kategoriMap[$row['nama']] = (int) $row['id'];
}
echo "Kategori: " . count($kategoriList) . " record inserted.\n";

// ════════════════════════════════════════════════════════════════════════
// 2. INSERT BUKU (D-13: 30-50 buku; sinopsis bahasa Indonesia singkat)
//    Sinopsis diisi 2-3 kalimat Indonesia agar TF-IDF Phase 3 bermakna.
//    cover_url: placeholder https://placehold.co/200x300 (D-03)
//    isbn: nullable (D-02) — diisi untuk beberapa buku, NULL untuk lainnya
// ════════════════════════════════════════════════════════════════════════
$buku = [
    // Matematika
    [
        'kategori' => 'Matematika',
        'judul'    => 'Matematika Kelas 7 Kurikulum Merdeka',
        'penulis'  => 'Dicky Susanto',
        'isbn'     => '9786024074773',
        'sinopsis' => 'Buku pelajaran matematika untuk siswa SMP kelas 7 yang mencakup bilangan bulat, pecahan, aljabar dasar, dan geometri. Dilengkapi latihan soal dan pembahasan lengkap untuk membantu siswa memahami konsep dasar matematika.',
        'stok_total' => 5, 'stok_tersedia' => 4,
    ],
    [
        'kategori' => 'Matematika',
        'judul'    => 'Matematika Kelas 8 SMP',
        'penulis'  => "As'ari Abdur Rahman",
        'isbn'     => '9786024074786',
        'sinopsis' => 'Materi matematika kelas 8 meliputi sistem persamaan linear dua variabel, teorema Pythagoras, statistika, dan bangun ruang sisi datar. Cocok sebagai referensi belajar dan persiapan ujian.',
        'stok_total' => 4, 'stok_tersedia' => 4,
    ],
    [
        'kategori' => 'Matematika',
        'judul'    => 'Rumus Lengkap Matematika SMP',
        'penulis'  => 'Tim Ganesha Operation',
        'isbn'     => null,
        'sinopsis' => 'Kumpulan rumus matematika SMP dari kelas 7 hingga 9. Ringkas dan mudah diingat untuk persiapan ujian nasional dan olimpiade matematika tingkat SMP.',
        'stok_total' => 3, 'stok_tersedia' => 3,
    ],
    // IPA
    [
        'kategori' => 'IPA',
        'judul'    => 'Ilmu Pengetahuan Alam Kelas 7',
        'penulis'  => 'Wahono Widodo',
        'isbn'     => '9786024074809',
        'sinopsis' => 'Buku IPA terpadu untuk SMP kelas 7 yang membahas objek IPA dan pengamatannya, klasifikasi makhluk hidup, zat dan karakteristiknya, serta energi dalam kehidupan.',
        'stok_total' => 5, 'stok_tersedia' => 3,
    ],
    [
        'kategori' => 'IPA',
        'judul'    => 'IPA Terpadu Kelas 8',
        'penulis'  => 'Siti Zubaidah',
        'isbn'     => null,
        'sinopsis' => 'Materi IPA terpadu untuk kelas 8 mencakup gerak benda dan makhluk hidup, struktur dan fungsi tumbuhan, sistem pencernaan manusia, dan zat aditif makanan.',
        'stok_total' => 4, 'stok_tersedia' => 4,
    ],
    [
        'kategori' => 'Biologi',
        'judul'    => 'Biologi untuk SMP dan MTs',
        'penulis'  => 'Rini Solihat',
        'isbn'     => '9789790102774',
        'sinopsis' => 'Pembahasan mendalam biologi tingkat SMP meliputi sel, jaringan, organ, sistem organ manusia, reproduksi, genetika dasar, dan ekosistem. Dilengkapi gambar diagram yang jelas.',
        'stok_total' => 3, 'stok_tersedia' => 2,
    ],
    [
        'kategori' => 'Fisika',
        'judul'    => 'Fisika Dasar untuk SMP',
        'penulis'  => 'Mikrajuddin Abdullah',
        'isbn'     => null,
        'sinopsis' => 'Pengantar konsep fisika dasar untuk pelajar SMP: gerak lurus, gaya dan hukum Newton, tekanan, gelombang bunyi, cahaya, listrik statis, dan magnet. Penjelasan disertai contoh kehidupan sehari-hari.',
        'stok_total' => 4, 'stok_tersedia' => 4,
    ],
    [
        'kategori' => 'Kimia',
        'judul'    => 'Pengantar Kimia Dasar SMP',
        'penulis'  => 'Purba Michael',
        'isbn'     => '9789790105959',
        'sinopsis' => 'Buku pengantar kimia untuk siswa SMP yang membahas materi dan perubahan zat, atom dan molekul, tabel periodik unsur, ikatan kimia, serta reaksi kimia sederhana dalam kehidupan.',
        'stok_total' => 3, 'stok_tersedia' => 3,
    ],
    // IPS
    [
        'kategori' => 'IPS',
        'judul'    => 'Ilmu Pengetahuan Sosial Kelas 7',
        'penulis'  => 'Ahmad Mushlih',
        'isbn'     => '9786024074830',
        'sinopsis' => 'Buku IPS terpadu kelas 7 yang membahas kondisi geografis Indonesia, kehidupan masyarakat Indonesia pada masa praaksara, masa Hindu-Buddha, dan masa Islam.',
        'stok_total' => 5, 'stok_tersedia' => 5,
    ],
    [
        'kategori' => 'Sejarah',
        'judul'    => 'Sejarah Indonesia Masa Kolonial',
        'penulis'  => 'Marwati Djoened Poesponegoro',
        'isbn'     => '9789790084773',
        'sinopsis' => 'Kisah panjang Indonesia di bawah kekuasaan kolonial Belanda dan Jepang. Membahas VOC, cultuurstelsel, kebangkitan nasionalisme, pergerakan kemerdekaan, dan perjuangan bangsa menuju kemerdekaan 1945.',
        'stok_total' => 3, 'stok_tersedia' => 3,
    ],
    [
        'kategori' => 'Sejarah',
        'judul'    => 'Kerajaan-Kerajaan Nusantara',
        'penulis'  => 'Slamet Muljana',
        'isbn'     => null,
        'sinopsis' => 'Sejarah kerajaan-kerajaan besar di Nusantara: Sriwijaya, Majapahit, Demak, Mataram, dan kerajaan-kerajaan Islam di Kalimantan dan Sulawesi. Dilengkapi peta dan silsilah raja.',
        'stok_total' => 2, 'stok_tersedia' => 2,
    ],
    // Bahasa Indonesia
    [
        'kategori' => 'Bahasa Indonesia',
        'judul'    => 'Bahasa Indonesia Kelas 7 Kurikulum Merdeka',
        'penulis'  => 'Yuni Pratiwi',
        'isbn'     => '9786024074847',
        'sinopsis' => 'Buku bahasa Indonesia kelas 7 yang mencakup teks deskripsi, teks prosedur, teks laporan hasil observasi, puisi, dan teks narasi. Dilengkapi latihan menulis kreatif dan pemahaman bacaan.',
        'stok_total' => 5, 'stok_tersedia' => 5,
    ],
    [
        'kategori' => 'Bahasa Indonesia',
        'judul'    => 'Panduan Menulis Karya Ilmiah Remaja',
        'penulis'  => 'Djoko Saryono',
        'isbn'     => null,
        'sinopsis' => 'Panduan praktis menulis karya tulis ilmiah untuk pelajar SMP dan SMA: pemilihan topik, perumusan masalah, metode penelitian sederhana, dan teknik penulisan laporan yang benar.',
        'stok_total' => 3, 'stok_tersedia' => 3,
    ],
    // Bahasa Inggris
    [
        'kategori' => 'Bahasa Inggris',
        'judul'    => 'English for Nusantara Kelas 7',
        'penulis'  => 'Ika Lestari Damayanti',
        'isbn'     => '9786024074854',
        'sinopsis' => 'Buku bahasa Inggris kurikulum merdeka kelas 7 dengan pendekatan komunikatif. Berisi teks deskriptif, percakapan sehari-hari, cerita pendek, dan latihan listening, speaking, reading, writing.',
        'stok_total' => 5, 'stok_tersedia' => 4,
    ],
    [
        'kategori' => 'Bahasa Inggris',
        'judul'    => 'English Grammar for Junior High School',
        'penulis'  => 'Betty Schrampfer Azar',
        'isbn'     => '9780132330336',
        'sinopsis' => 'Panduan tata bahasa Inggris praktis untuk siswa SMP yang membahas present tense, past tense, future tense, modal verbs, prepositions, dan penulisan kalimat yang benar.',
        'stok_total' => 3, 'stok_tersedia' => 3,
    ],
    // PKN
    [
        'kategori' => 'PKN',
        'judul'    => 'Pendidikan Kewarganegaraan Kelas 8',
        'penulis'  => 'Lukman Surya Saputra',
        'isbn'     => '9786024074861',
        'sinopsis' => 'Buku PKN kelas 8 yang membahas Pancasila sebagai dasar negara, UUD 1945, lembaga-lembaga negara Indonesia, hak dan kewajiban warga negara, serta kebhinekaan dalam kerangka NKRI.',
        'stok_total' => 4, 'stok_tersedia' => 3,
    ],
    // Fiksi
    [
        'kategori' => 'Fiksi',
        'judul'    => 'Laskar Pelangi',
        'penulis'  => 'Andrea Hirata',
        'isbn'     => '9789793062792',
        'sinopsis' => 'Novel inspiratif tentang sepuluh anak Belitung yang berjuang mendapatkan pendidikan di SD Muhammadiyah yang hampir roboh. Kisah persahabatan, semangat belajar, dan mimpi-mimpi besar dari pelosok Indonesia.',
        'stok_total' => 5, 'stok_tersedia' => 3,
    ],
    [
        'kategori' => 'Fiksi',
        'judul'    => 'Bumi Manusia',
        'penulis'  => 'Pramoedya Ananta Toer',
        'isbn'     => '9789799731234',
        'sinopsis' => 'Novel pertama dari Tetralogi Buru karya Pramoedya Ananta Toer. Kisah Minke, pemuda Jawa yang terpelajar, dan perjuangannya melawan kolonialisme Belanda sambil menemukan cinta dan identitas bangsanya.',
        'stok_total' => 3, 'stok_tersedia' => 3,
    ],
    [
        'kategori' => 'Fiksi',
        'judul'    => 'Harry Potter dan Batu Bertuah',
        'penulis'  => 'J.K. Rowling',
        'isbn'     => '9786020634609',
        'sinopsis' => 'Harry Potter, seorang anak yatim piatu, menemukan dirinya adalah seorang penyihir dan diterima di Sekolah Sihir Hogwarts. Petualangan pertamanya mengungkap misteri kematian orang tuanya dan ancaman Voldemort.',
        'stok_total' => 4, 'stok_tersedia' => 2,
    ],
    [
        'kategori' => 'Fiksi',
        'judul'    => 'Sang Pemimpi',
        'penulis'  => 'Andrea Hirata',
        'isbn'     => '9789793062853',
        'sinopsis' => 'Kelanjutan Laskar Pelangi: Ikal dan Arai bermimpi melanjutkan studi ke Sorbonne, Perancis. Novel tentang keberanian bermimpi besar, semangat pantang menyerah, dan persahabatan sejati.',
        'stok_total' => 3, 'stok_tersedia' => 3,
    ],
    [
        'kategori' => 'Fiksi',
        'judul'    => 'Negeri 5 Menara',
        'penulis'  => 'Ahmad Fuadi',
        'isbn'     => '9789792247404',
        'sinopsis' => 'Kisah Alif Fikri, pemuda Minang yang belajar di Pondok Madani, pesantren modern di Jawa. Bersama lima sahabatnya, ia bermimpi menaklukkan dunia dengan mantra sakti man jadda wajada.',
        'stok_total' => 4, 'stok_tersedia' => 4,
    ],
    // Non-Fiksi
    [
        'kategori' => 'Non-Fiksi',
        'judul'    => 'Filosofi Teras',
        'penulis'  => 'Henry Manampiring',
        'isbn'     => '9786020636917',
        'sinopsis' => 'Pengantar filsafat Stoa untuk orang Indonesia. Membahas cara menghadapi kecemasan, amarah, dan ketidakpastian hidup menggunakan prinsip-prinsip Stoicisme yang terbukti selama ribuan tahun.',
        'stok_total' => 3, 'stok_tersedia' => 3,
    ],
    [
        'kategori' => 'Non-Fiksi',
        'judul'    => 'Atomic Habits',
        'penulis'  => 'James Clear',
        'isbn'     => '9786020642253',
        'sinopsis' => 'Panduan praktis membangun kebiasaan baik dan menghilangkan kebiasaan buruk. James Clear menjelaskan sistem perubahan 1% yang membawa dampak luar biasa dalam jangka panjang melalui empat hukum perubahan perilaku.',
        'stok_total' => 4, 'stok_tersedia' => 4,
    ],
    [
        'kategori' => 'Non-Fiksi',
        'judul'    => 'Sapiens: Riwayat Singkat Umat Manusia',
        'penulis'  => 'Yuval Noah Harari',
        'isbn'     => '9786020336862',
        'sinopsis' => 'Sejarah umat manusia dari zaman batu hingga era digital. Harari membahas revolusi kognitif, pertanian, penggabungan dunia, dan revolusi ilmu pengetahuan yang membentuk peradaban modern.',
        'stok_total' => 3, 'stok_tersedia' => 2,
    ],
    // Sains
    [
        'kategori' => 'Sains',
        'judul'    => 'A Brief History of Time',
        'penulis'  => 'Stephen Hawking',
        'isbn'     => '9786020330044',
        'sinopsis' => 'Pengantar populer kosmologi modern oleh fisikawan legendaris Stephen Hawking. Membahas big bang, lubang hitam, waktu, dan pertanyaan besar tentang asal usul serta masa depan alam semesta.',
        'stok_total' => 2, 'stok_tersedia' => 2,
    ],
    [
        'kategori' => 'Sains',
        'judul'    => 'Kenapa Langit Berwarna Biru',
        'penulis'  => 'Edwi Arief Sosiawan',
        'isbn'     => null,
        'sinopsis' => 'Menjawab pertanyaan-pertanyaan sains sehari-hari yang sering ditanyakan anak-anak: mengapa langit biru, bagaimana pelangi terbentuk, kenapa laut asin, dan misteri alam lainnya.',
        'stok_total' => 4, 'stok_tersedia' => 4,
    ],
    // Teknologi
    [
        'kategori' => 'Teknologi',
        'judul'    => 'Pengantar Pemrograman Python untuk Pemula',
        'penulis'  => 'Abdul Kadir',
        'isbn'     => '9786020460826',
        'sinopsis' => 'Buku pengantar pemrograman Python untuk siswa SMP dan SMA tanpa pengalaman coding sebelumnya. Dilengkapi latihan, studi kasus, dan proyek kecil yang menyenangkan.',
        'stok_total' => 5, 'stok_tersedia' => 5,
    ],
    [
        'kategori' => 'Teknologi',
        'judul'    => 'Cara Kerja Internet',
        'penulis'  => 'Andi Offline',
        'isbn'     => null,
        'sinopsis' => 'Penjelasan sederhana tentang bagaimana internet bekerja: protokol TCP/IP, DNS, HTTP, email, cloud computing, keamanan internet, dan literasi digital untuk pelajar.',
        'stok_total' => 3, 'stok_tersedia' => 3,
    ],
    [
        'kategori' => 'Teknologi',
        'judul'    => 'Kecerdasan Buatan untuk Pelajar',
        'penulis'  => 'Budi Rahardjo',
        'isbn'     => '9786024048587',
        'sinopsis' => 'Pengantar kecerdasan buatan (AI) dan machine learning yang ditujukan untuk pelajar SMP-SMA. Membahas sejarah AI, cara kerja neural network, dan aplikasi AI dalam kehidupan sehari-hari.',
        'stok_total' => 4, 'stok_tersedia' => 4,
    ],
    // Komik
    [
        'kategori' => 'Komik',
        'judul'    => 'Doraemon Vol. 1',
        'penulis'  => 'Fujiko F. Fujio',
        'isbn'     => '9789799204141',
        'sinopsis' => 'Petualangan Nobita dan robot kucing dari masa depan bernama Doraemon. Dengan kantong ajaibnya, Doraemon membantu Nobita menghadapi berbagai masalah sehari-hari dengan alat-alat futuristik.',
        'stok_total' => 5, 'stok_tersedia' => 5,
    ],
    [
        'kategori' => 'Komik',
        'judul'    => 'Naruto Vol. 1',
        'penulis'  => 'Masashi Kishimoto',
        'isbn'     => '9789799204158',
        'sinopsis' => 'Petualangan Naruto Uzumaki, ninja muda bersemangat yang bermimpi menjadi Hokage. Di dalam dirinya tersimpan chakra Rubah Ekor Sembilan yang membuatnya dijauhi warga desa.',
        'stok_total' => 4, 'stok_tersedia' => 4,
    ],
    [
        'kategori' => 'Komik',
        'judul'    => 'One Piece Vol. 1',
        'penulis'  => 'Eiichiro Oda',
        'isbn'     => '9789799204165',
        'sinopsis' => 'Petualangan Monkey D. Luffy, pemuda berambisi menjadi Raja Bajak Laut. Dengan tubuh yang bisa meregang seperti karet, Luffy memimpin kru Topi Jerami mengarungi Grand Line.',
        'stok_total' => 4, 'stok_tersedia' => 3,
    ],
    [
        'kategori' => 'Komik',
        'judul'    => 'Sains Komik: Tubuh Manusia',
        'penulis'  => 'Gomdori',
        'isbn'     => null,
        'sinopsis' => 'Buku sains bergambar yang menjelaskan cara kerja tubuh manusia melalui cerita komik yang menarik. Membahas sistem pencernaan, peredaran darah, sistem saraf, dan organ-organ penting lainnya.',
        'stok_total' => 5, 'stok_tersedia' => 5,
    ],
    [
        'kategori' => 'Komik',
        'judul'    => 'Sains Komik: Ekosistem Bumi',
        'penulis'  => 'Gomdori',
        'isbn'     => null,
        'sinopsis' => 'Eksplorasi ekosistem bumi melalui komik sains: hutan hujan tropis, laut dalam, padang rumput, gurun, dan kutub. Membahas rantai makanan, keseimbangan ekosistem, dan dampak perubahan iklim.',
        'stok_total' => 4, 'stok_tersedia' => 4,
    ],
];

$stmtBuku = $pdo->prepare(
    "INSERT INTO buku (kategori_id, judul, penulis, isbn, sinopsis, cover_url, stok_total, stok_tersedia)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
);

foreach ($buku as $b) {
    $stmtBuku->execute([
        $kategoriMap[$b['kategori']],
        $b['judul'],
        $b['penulis'],
        $b['isbn'],
        $b['sinopsis'],
        null, // cover_url null — frontend pakai Open Library (ISBN) atau gradient placeholder
        $b['stok_total'],
        $b['stok_tersedia'],
    ]);
}
echo "Buku: " . count($buku) . " record inserted.\n";

// ════════════════════════════════════════════════════════════════════════
// 3. INSERT USERS — bcrypt hash (D-16)
//    password_hash menghasilkan 60 karakter; VARCHAR(255) future-proof
// ════════════════════════════════════════════════════════════════════════
$stmtUser = $pdo->prepare(
    "INSERT INTO users (nama, username, password, role) VALUES (?, ?, ?, ?)"
);

$users = [
    [
        'nama'     => 'Luthfi',
        'username' => 'luthfi1',
        'password' => password_hash('Luthfi123', PASSWORD_BCRYPT),
        'role'     => 'siswa',
    ],
    [
        'nama'     => 'Admin',
        'username' => 'admin',
        'password' => password_hash('admin123', PASSWORD_BCRYPT),
        'role'     => 'admin',
    ],
];

foreach ($users as $u) {
    $stmtUser->execute([$u['nama'], $u['username'], $u['password'], $u['role']]);
}
echo "Users: " . count($users) . " record inserted.\n";

// Ambil user_id untuk seed peminjaman
$siswaId = (int) $pdo->query("SELECT id FROM users WHERE username='luthfi1'")->fetchColumn();
$adminId = (int) $pdo->query("SELECT id FROM users WHERE username='admin'")->fetchColumn();

// Ambil beberapa buku_id untuk seed peminjaman
$bukuIds = $pdo->query("SELECT id FROM buku ORDER BY id LIMIT 20")->fetchAll(PDO::FETCH_COLUMN);

// ════════════════════════════════════════════════════════════════════════
// 4. INSERT PEMINJAMAN (D-15: 10-20 record, status campuran)
//    Dipinjam + Dikembalikan agar Phase 3 /recommend/personal punya data
//    Urutan insert SETELAH users dan buku — FK constraint aman
// ════════════════════════════════════════════════════════════════════════
$stmtPinjam = $pdo->prepare(
    "INSERT INTO peminjaman (user_id, buku_id, status, created_at, tanggal_approve, tanggal_kembali, tanggal_reject)
     VALUES (?, ?, ?, ?, ?, ?, ?)"
);

$peminjaman = [
    // Dikembalikan (riwayat untuk rekomendasi personal Phase 3)
    [$siswaId, $bukuIds[0],  'Dikembalikan', '2025-03-01 09:00:00', '2025-03-02 10:00:00', '2025-03-16 14:00:00', null],
    [$siswaId, $bukuIds[2],  'Dikembalikan', '2025-03-05 10:00:00', '2025-03-06 08:00:00', '2025-03-20 09:00:00', null],
    [$siswaId, $bukuIds[6],  'Dikembalikan', '2025-03-10 11:00:00', '2025-03-11 09:00:00', '2025-03-25 10:00:00', null],
    [$siswaId, $bukuIds[9],  'Dikembalikan', '2025-03-15 08:00:00', '2025-03-16 10:00:00', '2025-03-30 11:00:00', null],
    [$siswaId, $bukuIds[12], 'Dikembalikan', '2025-04-01 09:00:00', '2025-04-02 08:00:00', '2025-04-15 14:00:00', null],
    // Dipinjam (sedang dipinjam — stok_tersedia sudah berkurang di data buku)
    [$siswaId, $bukuIds[15], 'Dipinjam',     '2025-04-20 10:00:00', '2025-04-21 09:00:00', null,                  null],
    [$siswaId, $bukuIds[16], 'Dipinjam',     '2025-04-22 11:00:00', '2025-04-23 10:00:00', null,                  null],
    // Ditolak
    [$siswaId, $bukuIds[3],  'Ditolak',      '2025-04-25 09:00:00', null,                  null, '2025-04-25 16:00:00'],
    // Pending (menunggu approval)
    [$siswaId, $bukuIds[17], 'Pending',       '2025-05-01 08:00:00', null,                  null, null],
    // Lebih banyak riwayat
    [$siswaId, $bukuIds[1],  'Dikembalikan', '2025-02-10 09:00:00', '2025-02-11 10:00:00', '2025-02-25 09:00:00', null],
    [$siswaId, $bukuIds[4],  'Dikembalikan', '2025-02-15 10:00:00', '2025-02-16 08:00:00', '2025-03-01 11:00:00', null],
    [$siswaId, $bukuIds[7],  'Dikembalikan', '2025-02-20 11:00:00', '2025-02-21 09:00:00', '2025-03-06 10:00:00', null],
    [$siswaId, $bukuIds[10], 'Dikembalikan', '2025-03-20 08:00:00', '2025-03-21 10:00:00', '2025-04-05 14:00:00', null],
    [$siswaId, $bukuIds[13], 'Dipinjam',     '2025-05-05 09:00:00', '2025-05-06 08:00:00', null,                  null],
];

foreach ($peminjaman as $p) {
    $stmtPinjam->execute($p);
}
echo "Peminjaman: " . count($peminjaman) . " record inserted.\n";

// ════════════════════════════════════════════════════════════════════════
// 5. VERIFIKASI RINGKAS
// ════════════════════════════════════════════════════════════════════════
echo "\n=== VERIFIKASI SEED ===\n";
echo "Jumlah kategori : " . $pdo->query("SELECT COUNT(*) FROM kategori")->fetchColumn() . "\n";
echo "Jumlah buku     : " . $pdo->query("SELECT COUNT(*) FROM buku")->fetchColumn() . "\n";
echo "Jumlah users    : " . $pdo->query("SELECT COUNT(*) FROM users")->fetchColumn() . "\n";
echo "Jumlah pinjaman : " . $pdo->query("SELECT COUNT(*) FROM peminjaman")->fetchColumn() . "\n";

// Verifikasi password bcrypt
$pwCheck = $pdo->query("SELECT username, LEFT(password,4) AS prefix FROM users")->fetchAll();
echo "\nVerifikasi bcrypt:\n";
foreach ($pwCheck as $row) {
    $status = ($row['prefix'] === '$2y$') ? 'OK' : 'ERROR - bukan bcrypt!';
    echo "  {$row['username']}: prefix={$row['prefix']} => {$status}\n";
}

// Verifikasi FULLTEXT
$ftTest = $pdo->query(
    "SELECT COUNT(*) FROM buku WHERE MATCH(judul, penulis, sinopsis) AGAINST ('matematika' IN BOOLEAN MODE)"
)->fetchColumn();
echo "\nFULLTEXT test ('matematika'): {$ftTest} hasil\n";

echo "\nSeeding selesai. Jalankan verifikasi SQL lengkap di phpMyAdmin untuk konfirmasi akhir.\n";
