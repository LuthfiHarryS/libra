<?php
declare(strict_types=1);

require_once __DIR__ . '/../middleware/AuthMiddleware.php';
require_once __DIR__ . '/../helpers/Response.php';

function borrow_request(PDO $pdo, array $body): void
{
    $user    = require_auth($pdo, 'siswa');
    $user_id = (int)$user->sub;

    $book_id = isset($body['book_id']) ? (int)$body['book_id'] : 0;
    if ($book_id <= 0) {
        json_response(false, null, 'book_id wajib diisi', 422);
    }

    $pdo->beginTransaction();
    try {
        $s1 = $pdo->prepare("SELECT stok_tersedia FROM buku WHERE id = ? FOR UPDATE");
        $s1->execute([$book_id]);
        $book = $s1->fetch();

        if (!$book) {
            $pdo->rollBack();
            json_response(false, null, 'Buku tidak ditemukan', 404);
        }
        if ((int)$book['stok_tersedia'] <= 0) {
            $pdo->rollBack();
            json_response(false, null, 'Stok buku tidak tersedia', 422);
        }

        $s2 = $pdo->prepare(
            "SELECT COUNT(*) FROM peminjaman WHERE user_id = ? AND status IN ('Pending','Dipinjam')"
        );
        $s2->execute([$user_id]);
        if ((int)$s2->fetchColumn() >= BATAS_PINJAM) {
            $pdo->rollBack();
            json_response(false, null,
                'Kamu sudah mencapai batas maksimal ' . BATAS_PINJAM . ' pinjaman aktif', 422);
        }

        $s3 = $pdo->prepare(
            "SELECT 1 FROM peminjaman WHERE user_id = ? AND buku_id = ? AND status IN ('Pending','Dipinjam')"
        );
        $s3->execute([$user_id, $book_id]);
        if ($s3->fetch()) {
            $pdo->rollBack();
            json_response(false, null, 'Kamu sudah meminjam buku ini', 422);
        }

        $ins = $pdo->prepare(
            "INSERT INTO peminjaman (user_id, buku_id, status) VALUES (?, ?, 'Pending')"
        );
        $ins->execute([$user_id, $book_id]);
        $new_id = (int)$pdo->lastInsertId();

        $pdo->commit();
        json_response(true, ['id' => $new_id], 'Permintaan peminjaman berhasil dikirim', 201);

    } catch (\Throwable $e) {
        $pdo->rollBack();
        json_response(false, null, 'Gagal memproses peminjaman', 500);
    }
}

function borrow_status(PDO $pdo): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;

    $stmt = $pdo->prepare(
        "SELECT p.id, p.buku_id, b.judul, b.penulis, b.cover_url,
                p.status, p.created_at AS tanggal_pinjam,
                p.tanggal_approve, p.tanggal_reject, p.tanggal_kembali
         FROM peminjaman p
         JOIN buku b ON p.buku_id = b.id
         WHERE p.user_id = ?
         ORDER BY p.created_at DESC"
    );
    $stmt->execute([$user_id]);
    json_response(true, $stmt->fetchAll(), 'Berhasil');
}

function borrow_get(PDO $pdo, int $id): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;

    $stmt = $pdo->prepare(
        "SELECT p.id, p.user_id, p.buku_id, b.judul, b.penulis, b.cover_url,
                p.status, p.created_at AS tanggal_pinjam, p.tanggal_kembali
         FROM peminjaman p
         JOIN buku b ON p.buku_id = b.id
         WHERE p.id = ?"
    );
    $stmt->execute([$id]);
    $row = $stmt->fetch();

    if (!$row) {
        json_response(false, null, 'Data peminjaman tidak ditemukan', 404);
    }
    if ((int)$row['user_id'] !== $user_id) {
        json_response(false, null, 'Akses ditolak', 403);
    }

    unset($row['user_id']);
    json_response(true, $row, 'Berhasil');
}

function recommend_proxy(PDO $pdo, int $book_id): void
{
    $chk = $pdo->prepare("SELECT 1 FROM buku WHERE id = ?");
    $chk->execute([$book_id]);
    if (!$chk->fetch()) {
        json_response(false, null, 'Buku tidak ditemukan', 404);
    }

    $limit = min(20, max(1, (int)($_GET['limit'] ?? 5)));
    $url   = CBF_URL . "/recommend?book_id={$book_id}&limit={$limit}";

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 5,
        CURLOPT_CONNECTTIMEOUT => 3,
        CURLOPT_FOLLOWLOCATION => false,
    ]);
    $raw  = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);

    if ($err !== '' || $code !== 200 || $raw === false) {
        json_response(true, [], 'Rekomendasi tidak tersedia', 200);
    }

    $data = json_decode($raw, true);
    json_response(true, is_array($data) ? $data : [], 'Berhasil');
}
