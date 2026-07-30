<?php
declare(strict_types=1);

require_once __DIR__ . '/../middleware/AuthMiddleware.php';
require_once __DIR__ . '/../helpers/Response.php';

/**
 * GET /api/favorites
 * List buku yang di-favorit oleh user (urut terbaru dulu).
 */
function favorites_list(PDO $pdo): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;

    $stmt = $pdo->prepare(
        "SELECT b.id, b.judul, b.penulis, b.isbn, b.cover_url,
                b.stok_total, b.stok_tersedia, b.created_at,
                k.id AS kategori_id, k.nama AS kategori_nama,
                f.created_at AS favorited_at
         FROM favorites f
         JOIN buku b     ON f.buku_id = b.id
         JOIN kategori k ON b.kategori_id = k.id
         WHERE f.user_id = ?
         ORDER BY f.created_at DESC"
    );
    $stmt->execute([$user_id]);
    json_response(true, $stmt->fetchAll(), 'Berhasil');
}

/**
 * POST /api/favorites { book_id }
 * Tambah buku ke favorit. Idempotent: INSERT IGNORE.
 */
function favorite_add(PDO $pdo, array $body): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;
    $book_id = isset($body['book_id']) ? (int)$body['book_id'] : 0;

    if ($book_id <= 0) {
        json_response(false, null, 'book_id wajib diisi', 422);
    }

    $chk = $pdo->prepare("SELECT 1 FROM buku WHERE id = ?");
    $chk->execute([$book_id]);
    if (!$chk->fetch()) {
        json_response(false, null, 'Buku tidak ditemukan', 404);
    }

    $stmt = $pdo->prepare(
        "INSERT IGNORE INTO favorites (user_id, buku_id) VALUES (?, ?)"
    );
    $stmt->execute([$user_id, $book_id]);

    json_response(true, ['book_id' => $book_id], 'Ditambahkan ke favorit', 201);
}

/**
 * DELETE /api/favorites/:book_id
 * Hapus dari favorit. Idempotent: tidak error kalau belum favorit.
 */
function favorite_remove(PDO $pdo, int $book_id): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;

    $stmt = $pdo->prepare("DELETE FROM favorites WHERE user_id = ? AND buku_id = ?");
    $stmt->execute([$user_id, $book_id]);

    json_response(true, ['book_id' => $book_id], 'Dihapus dari favorit');
}
