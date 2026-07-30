<?php
/**
 * LIBRA — Seed katalog nyata Perpustakaan SMPN 1 Kemang
 * Jalankan: D:\xampp\php\php.exe database\seed_notes_books.php
 *
 * Mengganti seluruh isi tabel buku dengan inventaris fisik hasil pendataan
 * (6 file notes_*.txt -> parse_notes.py -> fetch_notes_covers.py).
 * Berbeda dari seed_famous_books.php yang berisi 150 judul terkenal untuk demo:
 * data ini adalah koleksi yang benar-benar ada di rak.
 *
 * Tabel users TIDAK disentuh. kategori ditambah bila ada kategori baru.
 * peminjaman & favorites di-TRUNCATE karena FK ke buku_id — lalu peminjaman
 * demo diisi ulang supaya /recommend/personal (CBF) tetap punya data.
 *
 * Prasyarat: python/scripts/books_with_covers.json sudah dihasilkan
 * oleh fetch_notes_covers.py, dan file .webp sudah ada di uploads/covers/.
 */

declare(strict_types=1);

$jsonPath = __DIR__ . '/../python/scripts/books_with_covers.json';
if (!file_exists($jsonPath)) {
    die("File tidak ditemukan: $jsonPath\nJalankan fetch_notes_covers.py terlebih dahulu.\n");
}

$books = json_decode(file_get_contents($jsonPath), true, 512, JSON_THROW_ON_ERROR);
echo "Dimuat " . count($books) . " buku dari books_with_covers.json\n\n";

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

// ── Kosongkan hanya tabel yang bergantung pada buku_id ───────────────────
$pdo->exec("SET FOREIGN_KEY_CHECKS=0");
$pdo->exec("TRUNCATE TABLE favorites");
$pdo->exec("TRUNCATE TABLE peminjaman");
$pdo->exec("TRUNCATE TABLE buku");
$pdo->exec("SET FOREIGN_KEY_CHECKS=1");
echo "Tabel buku, peminjaman, favorites dikosongkan (kategori & users tetap).\n";

// ── Peta kategori nama -> id, tambah yang belum ada ──────────────────────
$kategoriMap = [];
foreach ($pdo->query("SELECT id, nama FROM kategori") as $row) {
    $kategoriMap[$row['nama']] = (int) $row['id'];
}

$kategoriBaru = [];
foreach ($books as $b) {
    if (!isset($kategoriMap[$b['kategori']])) {
        $kategoriBaru[$b['kategori']] = true;
    }
}
foreach (array_keys($kategoriBaru) as $nama) {
    $pdo->prepare("INSERT INTO kategori (nama) VALUES (?)")->execute([$nama]);
}
if ($kategoriBaru) {
    foreach ($pdo->query("SELECT id, nama FROM kategori") as $row) {
        $kategoriMap[$row['nama']] = (int) $row['id'];
    }
    echo "Kategori baru ditambahkan: " . implode(', ', array_keys($kategoriBaru)) . "\n";
}

// ── INSERT buku ──────────────────────────────────────────────────────────
$stmtBuku = $pdo->prepare(
    "INSERT INTO buku (kategori_id, judul, penulis, isbn, sinopsis, cover_url, stok_total, stok_tersedia)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
);

$coverAsli = 0;
$coverPlaceholder = 0;
$totalEksemplar = 0;
$coverHilang = [];

$coversDir = 'D:/xampp/htdocs/libra/uploads/covers/';

foreach ($books as $b) {
    $file = $b['cover_filename'];
    $coverUrl = null;

    // Jangan tulis cover_url kalau filenya tidak benar-benar ada di disk —
    // lebih baik NULL (fallback BookCard jalan) daripada gambar rusak.
    if ($file && file_exists($coversDir . $file)) {
        $coverUrl = 'http://localhost:8080/uploads/covers/' . $file;
        if ($b['cover_source'] === 'google_books') {
            $coverAsli++;
        } else {
            $coverPlaceholder++;
        }
    } else {
        $coverHilang[] = $b['judul'];
    }

    $stok = max(1, (int) $b['stok']);
    $totalEksemplar += $stok;

    $stmtBuku->execute([
        $kategoriMap[$b['kategori']],
        $b['judul'],
        $b['penulis'],
        $b['isbn'] ?: null,
        $b['sinopsis'],
        $coverUrl,
        $stok,
        $stok,
    ]);
}

echo "\nBuku: " . count($books) . " judul, {$totalEksemplar} eksemplar.\n";
echo "  Cover asli (Google Books) : $coverAsli\n";
echo "  Cover placeholder         : $coverPlaceholder\n";
if ($coverHilang) {
    echo "  File cover tidak ada      : " . count($coverHilang) . "\n";
    foreach (array_slice($coverHilang, 0, 10) as $t) {
        echo "    - $t\n";
    }
}

// ── Re-seed peminjaman demo (agar /recommend/personal punya data) ────────
$siswaId = (int) $pdo->query("SELECT id FROM users WHERE username='luthfi1'")->fetchColumn();
if ($siswaId > 0) {
    // Ambil buku dari kategori Matematika supaya rekomendasi CBF punya sinyal
    // yang jelas untuk didemokan, bukan buku acak lintas kategori.
    $bukuIds = $pdo->query(
        "SELECT b.id FROM buku b
         JOIN kategori k ON k.id = b.kategori_id
         WHERE k.nama = 'Matematika' ORDER BY b.id LIMIT 20"
    )->fetchAll(PDO::FETCH_COLUMN);

    if (count($bukuIds) >= 9) {
        $stmtPinjam = $pdo->prepare(
            "INSERT INTO peminjaman (user_id, buku_id, status, created_at, tanggal_approve, tanggal_kembali, tanggal_reject)
             VALUES (?, ?, ?, ?, ?, ?, ?)"
        );

        $peminjaman = [
            [$siswaId, $bukuIds[0], 'Dikembalikan', '2026-03-01 09:00:00', '2026-03-02 10:00:00', '2026-03-16 14:00:00', null],
            [$siswaId, $bukuIds[1], 'Dikembalikan', '2026-03-05 10:00:00', '2026-03-06 08:00:00', '2026-03-20 09:00:00', null],
            [$siswaId, $bukuIds[2], 'Dikembalikan', '2026-03-10 11:00:00', '2026-03-11 09:00:00', '2026-03-25 10:00:00', null],
            [$siswaId, $bukuIds[3], 'Dikembalikan', '2026-03-15 08:00:00', '2026-03-16 10:00:00', '2026-03-30 11:00:00', null],
            [$siswaId, $bukuIds[4], 'Dikembalikan', '2026-04-01 09:00:00', '2026-04-02 08:00:00', '2026-04-15 14:00:00', null],
            [$siswaId, $bukuIds[5], 'Dipinjam',     '2026-04-20 10:00:00', '2026-04-21 09:00:00', null, null],
            [$siswaId, $bukuIds[6], 'Dipinjam',     '2026-04-22 11:00:00', '2026-04-23 10:00:00', null, null],
            [$siswaId, $bukuIds[7], 'Ditolak',      '2026-04-25 09:00:00', null, null, '2026-04-25 16:00:00'],
            [$siswaId, $bukuIds[8], 'Pending',      '2026-05-01 08:00:00', null, null, null],
        ];

        foreach ($peminjaman as $p) {
            $stmtPinjam->execute($p);
        }
        // stok_tersedia harus mencerminkan 2 buku yang masih dipinjam
        $pdo->prepare("UPDATE buku SET stok_tersedia = GREATEST(stok_tersedia - 1, 0) WHERE id IN (?, ?)")
            ->execute([$bukuIds[5], $bukuIds[6]]);

        echo "\nPeminjaman demo: " . count($peminjaman) . " record untuk user id $siswaId (luthfi1).\n";
    } else {
        echo "\nBuku Matematika kurang dari 9 — peminjaman demo dilewati.\n";
    }
} else {
    echo "\nUser 'luthfi1' tidak ditemukan — peminjaman demo dilewati.\n";
}

// ── VERIFIKASI ───────────────────────────────────────────────────────────
echo "\n=== VERIFIKASI ===\n";
echo "Jumlah buku       : " . $pdo->query("SELECT COUNT(*) FROM buku")->fetchColumn() . "\n";
echo "Jumlah buku+cover : " . $pdo->query("SELECT COUNT(*) FROM buku WHERE cover_url IS NOT NULL")->fetchColumn() . "\n";
echo "Jumlah buku+ISBN  : " . $pdo->query("SELECT COUNT(*) FROM buku WHERE isbn IS NOT NULL")->fetchColumn() . "\n";
echo "Total eksemplar   : " . $pdo->query("SELECT SUM(stok_total) FROM buku")->fetchColumn() . "\n";
echo "Jumlah kategori   : " . $pdo->query("SELECT COUNT(*) FROM kategori")->fetchColumn() . "\n";
echo "Jumlah peminjaman : " . $pdo->query("SELECT COUNT(*) FROM peminjaman")->fetchColumn() . "\n";
echo "Jumlah users      : " . $pdo->query("SELECT COUNT(*) FROM users")->fetchColumn() . " (tidak diubah)\n";

echo "\nBuku per kategori:\n";
$rows = $pdo->query(
    "SELECT k.nama, COUNT(b.id) AS jml FROM kategori k
     LEFT JOIN buku b ON b.kategori_id = k.id
     GROUP BY k.id, k.nama HAVING jml > 0 ORDER BY jml DESC"
);
foreach ($rows as $r) {
    printf("  %-20s %d\n", $r['nama'], $r['jml']);
}

$ftTest = $pdo->query(
    "SELECT COUNT(*) FROM buku WHERE MATCH(judul, penulis, sinopsis) AGAINST ('matematika' IN BOOLEAN MODE)"
)->fetchColumn();
echo "\nFULLTEXT test ('matematika'): {$ftTest} hasil\n";

echo "\nSeeding selesai.\n";
