<?php
declare(strict_types=1);

require_once __DIR__ . '/../middleware/AuthMiddleware.php';
require_once __DIR__ . '/../helpers/Response.php';

/**
 * PUT /api/users/me  { nama }
 * Update nama user yang sedang login.
 */
function profile_update(PDO $pdo, array $body): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;

    $nama = trim($body['nama'] ?? '');
    if ($nama === '') {
        json_response(false, null, 'Nama wajib diisi', 400);
    }
    if (mb_strlen($nama) < 2 || mb_strlen($nama) > 100) {
        json_response(false, null, 'Nama harus 2-100 karakter', 400);
    }

    $stmt = $pdo->prepare("UPDATE users SET nama = ? WHERE id = ?");
    $stmt->execute([$nama, $user_id]);

    json_response(true, ['nama' => $nama], 'Profil berhasil diperbarui');
}

/**
 * POST /api/auth/change-password  { old_password, new_password }
 * Verifikasi password lama, lalu hash + simpan password baru.
 * Tidak invalidate JWT — biarkan user tetap login dengan token saat ini.
 */
function profile_change_password(PDO $pdo, array $body): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;

    $old = $body['old_password'] ?? '';
    $new = $body['new_password'] ?? '';

    if (!$old || !$new) {
        json_response(false, null, 'Password lama dan baru wajib diisi', 400);
    }
    if (strlen($new) < 8) {
        json_response(false, null, 'Password baru minimal 8 karakter', 400);
    }
    if ($old === $new) {
        json_response(false, null, 'Password baru harus berbeda dari yang lama', 400);
    }

    $stmt = $pdo->prepare("SELECT password FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $row = $stmt->fetch();

    if (!$row || !password_verify($old, $row['password'])) {
        json_response(false, null, 'Password lama salah', 401);
    }

    $hash = password_hash($new, PASSWORD_BCRYPT);
    $pdo->prepare("UPDATE users SET password = ? WHERE id = ?")->execute([$hash, $user_id]);

    json_response(true, null, 'Password berhasil diganti');
}

/**
 * GET /api/users/me/stats
 * Statistik untuk halaman profil siswa:
 *   - total_pinjam   : jumlah pinjaman pernah dibuat (semua status)
 *   - total_active   : Pending + Dipinjam saat ini
 *   - total_returned : Dikembalikan
 *   - total_favorit  : jumlah buku favorit
 *   - top_kategori   : kategori paling sering dipinjam (single string atau null)
 */
function profile_stats(PDO $pdo): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;

    $s = $pdo->prepare("SELECT COUNT(*) FROM peminjaman WHERE user_id = ?");
    $s->execute([$user_id]);
    $total_pinjam = (int)$s->fetchColumn();

    $s = $pdo->prepare("SELECT COUNT(*) FROM peminjaman WHERE user_id = ? AND status IN ('Pending','Dipinjam')");
    $s->execute([$user_id]);
    $total_active = (int)$s->fetchColumn();

    $s = $pdo->prepare("SELECT COUNT(*) FROM peminjaman WHERE user_id = ? AND status = 'Dikembalikan'");
    $s->execute([$user_id]);
    $total_returned = (int)$s->fetchColumn();

    $s = $pdo->prepare("SELECT COUNT(*) FROM favorites WHERE user_id = ?");
    $s->execute([$user_id]);
    $total_favorit = (int)$s->fetchColumn();

    $s = $pdo->prepare(
        "SELECT k.nama, COUNT(*) AS c
         FROM peminjaman p
         JOIN buku b     ON p.buku_id = b.id
         JOIN kategori k ON b.kategori_id = k.id
         WHERE p.user_id = ?
         GROUP BY k.id, k.nama
         ORDER BY c DESC
         LIMIT 1"
    );
    $s->execute([$user_id]);
    $top = $s->fetch();

    json_response(true, [
        'total_pinjam'   => $total_pinjam,
        'total_active'   => $total_active,
        'total_returned' => $total_returned,
        'total_favorit'  => $total_favorit,
        'top_kategori'   => $top ? $top['nama'] : null,
    ], 'Berhasil');
}
