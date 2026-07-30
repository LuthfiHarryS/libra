<?php
declare(strict_types=1);

require_once __DIR__ . '/../middleware/AuthMiddleware.php';
require_once __DIR__ . '/../helpers/Response.php';

// Cek apakah request bawa JWT valid; kalau ya return user_id, kalau tidak null.
// Beda dengan require_auth() yang reject — ini optional auth.
function _maybe_user_id(PDO $pdo): ?int
{
    $auth_header = $_SERVER['HTTP_AUTHORIZATION']
        ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION']
        ?? '';
    if (!str_starts_with($auth_header, 'Bearer ')) return null;

    $payload = decode_jwt(substr($auth_header, 7));
    if ($payload === null) return null;

    $stmt = $pdo->prepare("SELECT 1 FROM token_blacklist WHERE jti = ?");
    $stmt->execute([$payload->jti]);
    if ($stmt->fetch()) return null;

    return (int)$payload->sub;
}

function books_list(PDO $pdo): void
{
    $page        = max(1, (int)($_GET['page']        ?? 1));
    $limit       = min(50, max(1, (int)($_GET['limit'] ?? 10)));
    $offset      = ($page - 1) * $limit;
    $q           = trim($_GET['q']           ?? '');
    $kategori_id = isset($_GET['kategori_id']) ? (int)$_GET['kategori_id'] : null;
    $user_id     = _maybe_user_id($pdo);

    $where  = [];
    $params = [];

    if ($q !== '') {
        $where[]  = "MATCH(b.judul, b.penulis, b.sinopsis) AGAINST (? IN BOOLEAN MODE)";
        $params[] = $q . '*';
    }
    if ($kategori_id !== null) {
        $where[]  = "b.kategori_id = ?";
        $params[] = $kategori_id;
    }

    $where_sql = $where ? 'WHERE ' . implode(' AND ', $where) : '';

    // Pengurutan dipilih lewat daftar putih. Nilai dari URL TIDAK BOLEH masuk ke
    // ORDER BY, karena bagian itu tidak bisa di-bind sebagai parameter PDO.
    // 'terbaru' memakai id sebagai pemecah seri: banyak buku hasil seed berbagi
    // created_at yang sama persis, sehingga tanpa itu urutannya tidak stabil
    // antarhalaman dan sebuah buku bisa muncul dua kali atau terlewat.
    $urutan = [
        'terbaru' => 'b.created_at DESC, b.id DESC',
        'az'      => 'b.judul ASC, b.id ASC',
    ];
    $sort      = (string)($_GET['sort'] ?? 'terbaru');
    $order_sql = $urutan[$sort] ?? $urutan['terbaru'];

    $stmt = $pdo->prepare("SELECT COUNT(*) FROM buku b $where_sql");
    $stmt->execute($params);
    $total = (int)$stmt->fetchColumn();

    // LEFT JOIN favorites untuk hitung is_favorite per row. Kalau user tidak login, kolom 0.
    $fav_join = $user_id !== null ? "LEFT JOIN favorites f ON f.buku_id = b.id AND f.user_id = ?" : '';
    $fav_col  = $user_id !== null ? "(f.user_id IS NOT NULL) AS is_favorite" : "0 AS is_favorite";

    $sql = "SELECT b.id, b.judul, b.penulis, b.isbn, b.cover_url,
                   b.stok_total, b.stok_tersedia, b.created_at,
                   k.id AS kategori_id, k.nama AS kategori_nama,
                   $fav_col
            FROM buku b
            JOIN kategori k ON b.kategori_id = k.id
            $fav_join
            $where_sql
            ORDER BY $order_sql
            LIMIT ? OFFSET ?";

    $stmt = $pdo->prepare($sql);

    $i = 1;
    if ($user_id !== null) {
        $stmt->bindValue($i++, $user_id, PDO::PARAM_INT);
    }
    foreach ($params as $val) {
        $stmt->bindValue($i++, $val);
    }
    $stmt->bindValue($i++, $limit, PDO::PARAM_INT);
    $stmt->bindValue($i,   $offset, PDO::PARAM_INT);
    $stmt->execute();
    $books = $stmt->fetchAll();

    // PDO return is_favorite sebagai string "1"/"0" — cast ke bool untuk JSON yang clean
    foreach ($books as &$b) {
        $b['is_favorite'] = (bool)(int)$b['is_favorite'];
    }
    unset($b);

    json_response(true, [
        'items'       => $books,
        'total'       => $total,
        'page'        => $page,
        'limit'       => $limit,
        'total_pages' => (int)ceil($total / max(1, $limit)),
    ], 'Berhasil');
}

function book_get(PDO $pdo, int $id): void
{
    $user_id = _maybe_user_id($pdo);

    $fav_join = $user_id !== null ? "LEFT JOIN favorites f ON f.buku_id = b.id AND f.user_id = ?" : '';
    $fav_col  = $user_id !== null ? "(f.user_id IS NOT NULL) AS is_favorite" : "0 AS is_favorite";

    $sql = "SELECT b.id, b.judul, b.penulis, b.isbn, b.sinopsis, b.cover_url,
                   b.stok_total, b.stok_tersedia, b.created_at, b.updated_at,
                   k.id AS kategori_id, k.nama AS kategori_nama,
                   $fav_col
            FROM buku b
            JOIN kategori k ON b.kategori_id = k.id
            $fav_join
            WHERE b.id = ?";

    $stmt = $pdo->prepare($sql);
    $i = 1;
    if ($user_id !== null) {
        $stmt->bindValue($i++, $user_id, PDO::PARAM_INT);
    }
    $stmt->bindValue($i, $id, PDO::PARAM_INT);
    $stmt->execute();
    $book = $stmt->fetch();

    if (!$book) {
        json_response(false, null, 'Buku tidak ditemukan', 404);
    }

    $book['is_favorite'] = (bool)(int)$book['is_favorite'];
    json_response(true, $book, 'Berhasil');
}

function categories_list(PDO $pdo): void
{
    $stmt = $pdo->query("SELECT id, nama FROM kategori ORDER BY nama ASC");
    json_response(true, $stmt->fetchAll(), 'Berhasil');
}

/**
 * POST /api/books/upload-cover (multipart/form-data, field: "cover")
 * Upload + opsional kompresi TinyPNG → simpan ke uploads/covers/ → return URL.
 * Jika TINYPNG_API_KEY diisi di config, gambar dikompresi dulu sebelum disimpan.
 */
function book_cover_upload(PDO $pdo): void
{
    require_auth($pdo, 'admin');

    if (!isset($_FILES['cover']) || $_FILES['cover']['error'] !== UPLOAD_ERR_OK) {
        json_response(false, null, 'File cover tidak ditemukan atau terjadi error upload', 422);
    }

    $file    = $_FILES['cover'];
    $allowed = ['image/jpeg', 'image/png', 'image/webp'];
    $finfo   = finfo_open(FILEINFO_MIME_TYPE);
    $mime    = finfo_file($finfo, $file['tmp_name']);
    finfo_close($finfo);

    if (!in_array($mime, $allowed, true)) {
        json_response(false, null, 'Hanya file JPG, PNG, atau WebP yang diizinkan', 422);
    }
    if ($file['size'] > 5 * 1024 * 1024) {
        json_response(false, null, 'Ukuran file maksimal 5 MB', 422);
    }

    // Diturunkan dari lokasi file ini, bukan path absolut Windows — server
    // produksi berjalan di Linux dengan struktur direktori yang berbeda.
    $dest_dir = dirname(__DIR__, 2) . DIRECTORY_SEPARATOR . 'uploads'
              . DIRECTORY_SEPARATOR . 'covers' . DIRECTORY_SEPARATOR;
    if (!is_dir($dest_dir)) {
        mkdir($dest_dir, 0755, true);
    }

    $ext      = $mime === 'image/png' ? 'png' : ($mime === 'image/webp' ? 'webp' : 'jpg');
    $filename = uniqid('cover_', true) . '.' . $ext;
    $dest     = $dest_dir . $filename;

    $tinypng_key = TINYPNG_API_KEY;

    if ($tinypng_key !== '') {
        // Kirim ke TinyPNG untuk kompresi, lalu download hasilnya
        $image_data = file_get_contents($file['tmp_name']);
        $ch = curl_init('https://api.tinify.com/shrink');
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => $image_data,
            CURLOPT_HTTPHEADER     => ['Content-Type: ' . $mime],
            CURLOPT_USERPWD        => 'api:' . $tinypng_key,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 30,
        ]);
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($http_code === 201) {
            $result      = json_decode($response, true);
            $output_url  = $result['output']['url'] ?? null;
            if ($output_url) {
                // Download file terkompresi dan simpan lokal
                $compressed = file_get_contents($output_url, false, stream_context_create([
                    'http' => ['header' => 'Authorization: Basic ' . base64_encode('api:' . $tinypng_key)]
                ]));
                if ($compressed !== false) {
                    file_put_contents($dest, $compressed);
                    $cover_url = '/uploads/covers/' . $filename;
                    json_response(true, ['cover_url' => $cover_url], 'Cover berhasil diupload dan dikompres');
                    return;
                }
            }
        }
        // TinyPNG gagal → fallback ke simpan tanpa kompresi
    }

    if (!move_uploaded_file($file['tmp_name'], $dest)) {
        json_response(false, null, 'Gagal menyimpan file cover', 500);
    }

    $cover_url = '/uploads/covers/' . $filename;
    json_response(true, ['cover_url' => $cover_url], 'Cover berhasil diupload');
}

function book_create(PDO $pdo, array $body): void
{
    require_auth($pdo, 'admin');

    $judul       = trim($body['judul']       ?? '');
    $penulis     = trim($body['penulis']      ?? '');
    $kategori_id = isset($body['kategori_id']) ? (int)$body['kategori_id'] : 0;
    $isbn        = trim($body['isbn']         ?? '') ?: null;
    $sinopsis    = trim($body['sinopsis']      ?? '') ?: null;
    $cover_url   = trim($body['cover_url']    ?? '') ?: null;
    $stok_total  = isset($body['stok_total']) ? max(0, (int)$body['stok_total']) : 1;

    if (!$judul || !$penulis || !$kategori_id) {
        json_response(false, null, 'Judul, penulis, dan kategori_id wajib diisi', 400);
    }

    $chk = $pdo->prepare("SELECT 1 FROM kategori WHERE id = ?");
    $chk->execute([$kategori_id]);
    if (!$chk->fetch()) {
        json_response(false, null, 'Kategori tidak ditemukan', 400);
    }

    $stmt = $pdo->prepare(
        "INSERT INTO buku (kategori_id, judul, penulis, isbn, sinopsis, cover_url, stok_total, stok_tersedia)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    );
    $stmt->execute([$kategori_id, $judul, $penulis, $isbn, $sinopsis, $cover_url,
                    $stok_total, $stok_total]);
    $new_id = (int)$pdo->lastInsertId();

    json_response(true, ['id' => $new_id], 'Buku berhasil ditambahkan', 201);
}

function book_update(PDO $pdo, int $id, array $body): void
{
    require_auth($pdo, 'admin');

    $chk = $pdo->prepare("SELECT stok_total, stok_tersedia FROM buku WHERE id = ?");
    $chk->execute([$id]);
    $existing = $chk->fetch();
    if (!$existing) {
        json_response(false, null, 'Buku tidak ditemukan', 404);
    }

    $set    = [];
    $params = [];

    if (isset($body['judul']) && trim($body['judul']) !== '') {
        $set[]    = "judul = ?";
        $params[] = trim($body['judul']);
    }
    if (isset($body['penulis']) && trim($body['penulis']) !== '') {
        $set[]    = "penulis = ?";
        $params[] = trim($body['penulis']);
    }
    if (isset($body['kategori_id'])) {
        $set[]    = "kategori_id = ?";
        $params[] = (int)$body['kategori_id'];
    }
    if (array_key_exists('isbn', $body)) {
        $set[]    = "isbn = ?";
        // Cast ke string dulu: array_key_exists bernilai true meski isinya null,
        // sedangkan trim(null) adalah TypeError fatal di PHP 8.
        $params[] = trim((string)($body['isbn'] ?? '')) ?: null;
    }
    if (array_key_exists('sinopsis', $body)) {
        $set[]    = "sinopsis = ?";
        $params[] = trim((string)($body['sinopsis'] ?? '')) ?: null;
    }
    if (array_key_exists('cover_url', $body)) {
        $set[]    = "cover_url = ?";
        $params[] = trim((string)($body['cover_url'] ?? '')) ?: null;
    }
    if (isset($body['stok_total'])) {
        $new_stok_total    = max(0, (int)$body['stok_total']);
        $delta             = $new_stok_total - (int)$existing['stok_total'];
        $new_stok_tersedia = max(0, (int)$existing['stok_tersedia'] + $delta);
        $set[]    = "stok_total = ?";
        $params[] = $new_stok_total;
        $set[]    = "stok_tersedia = ?";
        $params[] = $new_stok_tersedia;
    }

    if (empty($set)) {
        json_response(false, null, 'Tidak ada field yang diupdate', 400);
    }

    $params[] = $id;
    $stmt = $pdo->prepare("UPDATE buku SET " . implode(', ', $set) . " WHERE id = ?");
    $stmt->execute($params);

    json_response(true, ['id' => $id], 'Buku berhasil diupdate');
}

function book_delete(PDO $pdo, int $id): void
{
    require_auth($pdo, 'admin');

    $chk = $pdo->prepare("SELECT 1 FROM buku WHERE id = ?");
    $chk->execute([$id]);
    if (!$chk->fetch()) {
        json_response(false, null, 'Buku tidak ditemukan', 404);
    }

    // Buku yang sedang dipinjam atau sedang diajukan TIDAK boleh dihapus:
    // eksemplar fisiknya ada di tangan siswa, dan menghapus datanya akan
    // menghilangkan jejak siapa yang memegangnya.
    //
    // Riwayat yang sudah selesai (Dikembalikan/Ditolak) tidak menghalangi
    // penghapusan, tetapi harus dihapus lebih dulu karena FK peminjaman->buku
    // tidak memakai ON DELETE CASCADE. Baris favorites terhapus otomatis.
    $stmt = $pdo->prepare(
        "SELECT COUNT(*) FROM peminjaman
         WHERE buku_id = ? AND status IN ('Pending', 'Dipinjam')"
    );
    $stmt->execute([$id]);
    $aktif = (int) $stmt->fetchColumn();

    if ($aktif > 0) {
        json_response(false, ['peminjaman_aktif' => $aktif],
            "Tidak dapat menghapus: buku ini sedang dipinjam atau diajukan oleh $aktif siswa. "
            . "Selesaikan pengembalian atau tolak pengajuannya terlebih dahulu.", 422);
    }

    $pdo->beginTransaction();
    try {
        $stmt = $pdo->prepare("DELETE FROM peminjaman WHERE buku_id = ?");
        $stmt->execute([$id]);
        $riwayat_terhapus = $stmt->rowCount();

        $pdo->prepare("DELETE FROM buku WHERE id = ?")->execute([$id]);
        $pdo->commit();
    } catch (\Throwable $e) {
        $pdo->rollBack();
        json_response(false, null, 'Gagal menghapus buku', 500);
    }

    json_response(true, ['id' => $id, 'riwayat_terhapus' => $riwayat_terhapus],
        $riwayat_terhapus > 0
            ? "Buku berhasil dihapus beserta $riwayat_terhapus riwayat peminjaman"
            : 'Buku berhasil dihapus');
}