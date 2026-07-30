<?php
declare(strict_types=1);

require_once __DIR__ . '/../middleware/AuthMiddleware.php';
require_once __DIR__ . '/../helpers/Response.php';

/**
 * Helper internal — dipanggil dari AdminController saat approve/reject/return.
 * Tidak di-expose sebagai endpoint.
 */
function notif_create(PDO $pdo, int $user_id, string $type, string $title, ?string $body, ?string $link_url): void
{
    $stmt = $pdo->prepare(
        "INSERT INTO notifications (user_id, type, title, body, link_url)
         VALUES (?, ?, ?, ?, ?)"
    );
    $stmt->execute([$user_id, $type, $title, $body, $link_url]);
}

/**
 * GET /api/notifications[?limit=20]
 * Gabungan:
 *   1. Persisted notifications (approved/rejected/returned/info)
 *   2. Dinamis: reminder due-date untuk pinjaman aktif (3 hari sebelum + overdue)
 *
 * Reminder tidak masuk tabel — dihitung saat request. is_read selalu false untuk reminder
 * (karena dianggap "selalu relevan" sampai buku dikembalikan). Frontend bisa membedakan
 * via field `id` (string "reminder-N" vs integer).
 */
function notifications_list(PDO $pdo): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;
    $limit   = min(50, max(1, (int)($_GET['limit'] ?? 20)));

    $stmt = $pdo->prepare(
        "SELECT id, type, title, body, link_url, is_read, created_at
         FROM notifications
         WHERE user_id = ?
         ORDER BY created_at DESC
         LIMIT ?"
    );
    $stmt->bindValue(1, $user_id, PDO::PARAM_INT);
    $stmt->bindValue(2, $limit,   PDO::PARAM_INT);
    $stmt->execute();
    $persisted = $stmt->fetchAll();

    $persisted_out = array_map(fn($r) => [
        'id'         => (int)$r['id'],
        'type'       => $r['type'],
        'title'      => $r['title'],
        'body'       => $r['body'],
        'link_url'   => $r['link_url'],
        'is_read'    => (bool)(int)$r['is_read'],
        'created_at' => $r['created_at'],
    ], $persisted);

    // Reminder dinamis: pinjaman Dipinjam yang due dalam 3 hari atau telat
    // Pakai SAME konstanta 7 hari sebagai durasi pinjam (sinkron dengan AdminController.overdue)
    $rem = $pdo->prepare(
        "SELECT p.id, b.judul,
                DATE_ADD(p.tanggal_approve, INTERVAL 7 DAY) AS due_date,
                DATEDIFF(DATE_ADD(p.tanggal_approve, INTERVAL 7 DAY), CURDATE()) AS days_left
         FROM peminjaman p
         JOIN buku b ON p.buku_id = b.id
         WHERE p.user_id = ?
           AND p.status  = 'Dipinjam'
           AND p.tanggal_approve IS NOT NULL
           AND DATEDIFF(DATE_ADD(p.tanggal_approve, INTERVAL 7 DAY), CURDATE()) <= 3
         ORDER BY days_left ASC"
    );
    $rem->execute([$user_id]);

    $reminders = [];
    foreach ($rem->fetchAll() as $r) {
        $days = (int)$r['days_left'];
        if ($days < 0) {
            $title = "Buku terlambat " . abs($days) . " hari!";
            $body  = "\"{$r['judul']}\" sudah melewati batas pengembalian. Segera kembalikan ke perpustakaan.";
            $type  = 'info';
        } elseif ($days === 0) {
            $title = 'Kembalikan buku hari ini';
            $body  = "\"{$r['judul']}\" jatuh tempo hari ini.";
            $type  = 'info';
        } else {
            $title = "Buku jatuh tempo $days hari lagi";
            $body  = "\"{$r['judul']}\" harus dikembalikan dalam $days hari.";
            $type  = 'info';
        }

        $reminders[] = [
            'id'         => "reminder-{$r['id']}",   // string prefix supaya tidak bentrok dengan int id persisted
            'type'       => $type,
            'title'      => $title,
            'body'       => $body,
            'link_url'   => '/pinjaman',
            'is_read'    => false,
            'created_at' => date('Y-m-d H:i:s'),
        ];
    }

    // Gabung — reminder duluan (paling urgent), lalu persisted urut newest first
    $combined = array_merge($reminders, $persisted_out);

    // Hitung unread (persisted + jumlah reminders)
    $unread_persisted = 0;
    foreach ($persisted_out as $p) {
        if (!$p['is_read']) $unread_persisted++;
    }
    $unread = $unread_persisted + count($reminders);

    json_response(true, [
        'items'  => $combined,
        'unread' => $unread,
    ], 'Berhasil');
}

/**
 * POST /api/notifications/mark-read
 * Body: { ids: [int, ...] } — kalau kosong, mark semua sebagai read.
 * Reminder (id="reminder-N") di-filter out otomatis karena bukan integer.
 */
function notifications_mark_read(PDO $pdo, array $body): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;

    $ids = $body['ids'] ?? [];
    if (is_array($ids) && count($ids) > 0) {
        // Hanya cast integer-able (skip "reminder-*")
        $int_ids = array_values(array_filter(array_map(
            fn($x) => is_numeric($x) ? (int)$x : null, $ids
        ), fn($x) => $x !== null && $x > 0));

        if (count($int_ids) === 0) {
            json_response(true, ['marked' => 0], 'Tidak ada notif yang valid');
        }

        $placeholders = implode(',', array_fill(0, count($int_ids), '?'));
        $stmt = $pdo->prepare(
            "UPDATE notifications SET is_read = 1
             WHERE user_id = ? AND id IN ($placeholders)"
        );
        $stmt->execute(array_merge([$user_id], $int_ids));
        json_response(true, ['marked' => $stmt->rowCount()], 'Notif ditandai sudah dibaca');
    } else {
        // Mark all
        $stmt = $pdo->prepare("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0");
        $stmt->execute([$user_id]);
        json_response(true, ['marked' => $stmt->rowCount()], 'Semua notif ditandai sudah dibaca');
    }
}
