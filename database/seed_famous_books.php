<?php
/**
 * LIBRA — Seed 150 Buku Terkenal (50 Indonesia + 100 Luar Negeri)
 * Jalankan: C:\xampp\php\php.exe (atau D:\xampp\php\php.exe) database\seed_famous_books.php
 *
 * Mengganti seluruh isi tabel buku dengan 150 judul terkenal yang punya cover asli
 * (diunduh via python/scripts/fetch_covers.py dari Open Library / Wikipedia).
 * Tabel kategori dan users TIDAK disentuh. peminjaman & favorites di-TRUNCATE
 * karena FK ke buku_id — lalu peminjaman demo diisi ulang dengan buku_id baru
 * supaya /recommend/personal (CBF) tetap punya data untuk diuji.
 *
 * Prasyarat: python/scripts/famous_books_with_covers.json sudah dihasilkan
 * oleh fetch_covers.py.
 */

declare(strict_types=1);

$jsonPath = __DIR__ . '/../python/scripts/famous_books_with_covers.json';
if (!file_exists($jsonPath)) {
    die("File tidak ditemukan: $jsonPath\nJalankan fetch_covers.py terlebih dahulu.\n");
}

$books = json_decode(file_get_contents($jsonPath), true, 512, JSON_THROW_ON_ERROR);
echo "Dimuat " . count($books) . " buku dari famous_books_with_covers.json\n\n";

try {
    $pdo = new PDO(
        'mysql:host=localhost;dbname=libra_db;charset=utf8mb4',
        'root',
        '',
        [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]
    );
} catch (PDOException $e) {
    die("Koneksi gagal: " . $e->getMessage() . "\n");
}

echo "Koneksi berhasil.\n";

// ── TRUNCATE hanya tabel yang bergantung pada buku_id ────────────────────
$pdo->exec("SET FOREIGN_KEY_CHECKS=0");
$pdo->exec("TRUNCATE TABLE favorites");
$pdo->exec("TRUNCATE TABLE peminjaman");
$pdo->exec("TRUNCATE TABLE buku");
$pdo->exec("SET FOREIGN_KEY_CHECKS=1");
echo "Tabel buku, peminjaman, favorites dikosongkan (kategori & users tetap).\n";

// ── Peta kategori nama -> id (kategori sudah ada dari schema/seed awal) ──
$kategoriMap = [];
foreach ($pdo->query("SELECT id, nama FROM kategori") as $row) {
    $kategoriMap[$row['nama']] = (int) $row['id'];
}

$missingKategori = [];
foreach ($books as $b) {
    if (!isset($kategoriMap[$b['kategori']])) {
        $missingKategori[$b['kategori']] = true;
    }
}
foreach (array_keys($missingKategori) as $nama) {
    $pdo->prepare("INSERT INTO kategori (nama) VALUES (?)")->execute([$nama]);
}
if ($missingKategori) {
    foreach ($pdo->query("SELECT id, nama FROM kategori") as $row) {
        $kategoriMap[$row['nama']] = (int) $row['id'];
    }
    echo "Kategori baru ditambahkan: " . implode(', ', array_keys($missingKategori)) . "\n";
}

// ── INSERT 150 buku ───────────────────────────────────────────────────────
$stmtBuku = $pdo->prepare(
    "INSERT INTO buku (kategori_id, judul, penulis, isbn, sinopsis, cover_url, stok_total, stok_tersedia)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
);

$countWithCover = 0;
$countWithoutCover = 0;
$noCoverTitles = [];

foreach ($books as $b) {
    $coverUrl = null;
    if (!empty($b['cover_filename'])) {
        $coverUrl = 'http://localhost:8080/uploads/covers/' . $b['cover_filename'];
        $countWithCover++;
    } else {
        $countWithoutCover++;
        $noCoverTitles[] = $b['judul'];
    }

    $isbn = $b['isbn'] ?? null;
    if ($isbn !== null) {
        $isbn = (string) $isbn;
    }

    $stmtBuku->execute([
        $kategoriMap[$b['kategori']],
        $b['judul'],
        $b['penulis'],
        $isbn,
        $b['sinopsis'],
        $coverUrl,
        3,
        3,
    ]);
}

echo "\nBuku: " . count($books) . " record inserted.\n";
echo "  Dengan cover asli : $countWithCover\n";
echo "  Tanpa cover       : $countWithoutCover\n";
if ($noCoverTitles) {
    echo "  Judul tanpa cover:\n";
    foreach ($noCoverTitles as $t) {
        echo "    - $t\n";
    }
}

// ── Re-seed peminjaman demo (agar /recommend/personal Phase 3 punya data) ─
$siswaId = (int) $pdo->query("SELECT id FROM users WHERE username='luthfi1'")->fetchColumn();
if ($siswaId > 0) {
    $bukuIds = $pdo->query("SELECT id FROM buku ORDER BY id LIMIT 20")->fetchAll(PDO::FETCH_COLUMN);

    $stmtPinjam = $pdo->prepare(
        "INSERT INTO peminjaman (user_id, buku_id, status, created_at, tanggal_approve, tanggal_kembali, tanggal_reject)
         VALUES (?, ?, ?, ?, ?, ?, ?)"
    );

    $peminjaman = [
        [$siswaId, $bukuIds[0],  'Dikembalikan', '2025-03-01 09:00:00', '2025-03-02 10:00:00', '2025-03-16 14:00:00', null],
        [$siswaId, $bukuIds[2],  'Dikembalikan', '2025-03-05 10:00:00', '2025-03-06 08:00:00', '2025-03-20 09:00:00', null],
        [$siswaId, $bukuIds[6],  'Dikembalikan', '2025-03-10 11:00:00', '2025-03-11 09:00:00', '2025-03-25 10:00:00', null],
        [$siswaId, $bukuIds[9],  'Dikembalikan', '2025-03-15 08:00:00', '2025-03-16 10:00:00', '2025-03-30 11:00:00', null],
        [$siswaId, $bukuIds[12], 'Dikembalikan', '2025-04-01 09:00:00', '2025-04-02 08:00:00', '2025-04-15 14:00:00', null],
        [$siswaId, $bukuIds[15], 'Dipinjam',     '2025-04-20 10:00:00', '2025-04-21 09:00:00', null,                  null],
        [$siswaId, $bukuIds[16], 'Dipinjam',     '2025-04-22 11:00:00', '2025-04-23 10:00:00', null,                  null],
        [$siswaId, $bukuIds[3],  'Ditolak',      '2025-04-25 09:00:00', null,                  null, '2025-04-25 16:00:00'],
        [$siswaId, $bukuIds[17], 'Pending',      '2025-05-01 08:00:00', null,                  null, null],
    ];

    foreach ($peminjaman as $p) {
        $stmtPinjam->execute($p);
    }
    echo "\nPeminjaman demo: " . count($peminjaman) . " record inserted untuk user '$siswaId' (luthfi1).\n";
} else {
    echo "\nUser 'luthfi1' tidak ditemukan — peminjaman demo dilewati.\n";
}

// ── VERIFIKASI ─────────────────────────────────────────────────────────────
echo "\n=== VERIFIKASI ===\n";
echo "Jumlah buku       : " . $pdo->query("SELECT COUNT(*) FROM buku")->fetchColumn() . "\n";
echo "Jumlah buku+cover : " . $pdo->query("SELECT COUNT(*) FROM buku WHERE cover_url IS NOT NULL")->fetchColumn() . "\n";
echo "Jumlah kategori   : " . $pdo->query("SELECT COUNT(*) FROM kategori")->fetchColumn() . "\n";
echo "Jumlah peminjaman : " . $pdo->query("SELECT COUNT(*) FROM peminjaman")->fetchColumn() . "\n";
echo "Jumlah users      : " . $pdo->query("SELECT COUNT(*) FROM users")->fetchColumn() . " (tidak diubah)\n";

$ftTest = $pdo->query(
    "SELECT COUNT(*) FROM buku WHERE MATCH(judul, penulis, sinopsis) AGAINST ('cinta' IN BOOLEAN MODE)"
)->fetchColumn();
echo "\nFULLTEXT test ('cinta'): {$ftTest} hasil\n";

echo "\nSeeding selesai.\n";
