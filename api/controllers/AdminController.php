<?php
declare(strict_types=1);

require_once __DIR__ . '/../middleware/AuthMiddleware.php';
require_once __DIR__ . '/../helpers/Response.php';
require_once __DIR__ . '/NotificationController.php';

/**
 * GET /api/admin/dashboard
 * Returns aggregate counts: total_buku, pinjaman_aktif, pending_count
 * Requires admin role.
 */
function admin_dashboard(PDO $pdo): void
{
    require_auth($pdo, 'admin');

    $total_buku     = (int)$pdo->query("SELECT COUNT(*) FROM buku")->fetchColumn();
    $pinjaman_aktif = (int)$pdo->query("SELECT COUNT(*) FROM peminjaman WHERE status = 'Dipinjam'")->fetchColumn();
    $pending_count  = (int)$pdo->query("SELECT COUNT(*) FROM peminjaman WHERE status = 'Pending'")->fetchColumn();
    $total_siswa    = (int)$pdo->query("SELECT COUNT(*) FROM users WHERE role = 'siswa'")->fetchColumn();

    // Top 5 buku paling dipinjam (status Dipinjam + Dikembalikan = pernah benar-benar dipinjam)
    $top = $pdo->query(
        "SELECT b.id, b.judul, b.penulis, COUNT(p.id) AS borrow_count
         FROM peminjaman p
         JOIN buku b ON p.buku_id = b.id
         WHERE p.status IN ('Dipinjam', 'Dikembalikan')
         GROUP BY b.id, b.judul, b.penulis
         ORDER BY borrow_count DESC
         LIMIT 5"
    )->fetchAll();

    // Buku overdue: status Dipinjam + tanggal_approve > 7 hari yang lalu, belum dikembalikan
    // Durasi pinjam default 7 hari (konsisten dengan frontend BORROW_DURATION_DAYS)
    $overdue = $pdo->query(
        "SELECT p.id, u.nama AS user_nama, b.judul, p.tanggal_approve,
                DATEDIFF(NOW(), DATE_ADD(p.tanggal_approve, INTERVAL 7 DAY)) AS days_overdue
         FROM peminjaman p
         JOIN users u ON p.user_id = u.id
         JOIN buku b  ON p.buku_id = b.id
         WHERE p.status = 'Dipinjam'
           AND p.tanggal_approve IS NOT NULL
           AND DATE_ADD(p.tanggal_approve, INTERVAL 7 DAY) < NOW()
         ORDER BY days_overdue DESC
         LIMIT 10"
    )->fetchAll();

    json_response(true, [
        'total_buku'     => $total_buku,
        'pinjaman_aktif' => $pinjaman_aktif,
        'pending_count'  => $pending_count,
        'total_siswa'    => $total_siswa,
        'top_books'      => $top,
        'overdue'        => $overdue,
    ], 'Berhasil');
}

/**
 * GET /api/admin/borrows[?status=Pending|Dipinjam|Dikembalikan|Ditolak]
 * Returns all borrow records joined with users and buku tables.
 * Optional ?status= filter.
 * Requires admin role.
 */
function admin_borrows_list(PDO $pdo): void
{
    require_auth($pdo, 'admin');

    $status = trim($_GET['status'] ?? '');
    $valid  = ['Pending', 'Dipinjam', 'Dikembalikan', 'Ditolak'];

    $where  = ($status !== '' && in_array($status, $valid, true)) ? 'WHERE p.status = ?' : '';
    $params = ($status !== '' && in_array($status, $valid, true)) ? [$status] : [];

    $stmt = $pdo->prepare(
        "SELECT p.id, p.user_id, u.nama AS user_nama, p.buku_id,
                b.judul, b.penulis, p.status,
                p.created_at AS tanggal_pinjam, p.tanggal_kembali,
                p.tanggal_approve, p.tanggal_reject
         FROM peminjaman p
         JOIN buku b ON p.buku_id = b.id
         JOIN users u ON p.user_id = u.id
         $where
         ORDER BY p.created_at DESC"
    );
    $stmt->execute($params);
    json_response(true, $stmt->fetchAll(), 'Berhasil');
}

/**
 * PUT /api/admin/borrow/:id/approve
 * Transitions status Pending -> Dipinjam, decrements stok_tersedia.
 * Uses PDO transaction + SELECT FOR UPDATE (same pattern as borrow_request).
 * Requires admin role.
 */
function admin_borrow_approve(PDO $pdo, int $borrow_id): void
{
    require_auth($pdo, 'admin');

    $pdo->beginTransaction();
    try {
        $s1 = $pdo->prepare(
            "SELECT p.id, p.status, p.buku_id, p.user_id, b.judul
             FROM peminjaman p JOIN buku b ON p.buku_id = b.id
             WHERE p.id = ? FOR UPDATE"
        );
        $s1->execute([$borrow_id]);
        $borrow = $s1->fetch();

        if (!$borrow) {
            $pdo->rollBack();
            json_response(false, null, 'Data peminjaman tidak ditemukan', 404);
        }
        if ($borrow['status'] !== 'Pending') {
            $pdo->rollBack();
            json_response(false, null, 'Hanya peminjaman Pending yang dapat disetujui', 422);
        }

        $s2 = $pdo->prepare(
            "UPDATE buku SET stok_tersedia = stok_tersedia - 1 WHERE id = ? AND stok_tersedia > 0"
        );
        $s2->execute([$borrow['buku_id']]);
        if ($s2->rowCount() === 0) {
            $pdo->rollBack();
            json_response(false, null, 'Stok buku tidak tersedia', 422);
        }

        $pdo->prepare(
            "UPDATE peminjaman SET status = 'Dipinjam', tanggal_approve = NOW() WHERE id = ?"
        )->execute([$borrow_id]);

        $pdo->commit();

        notif_create($pdo, (int)$borrow['user_id'], 'approved',
            'Pinjaman disetujui! 🎉',
            "\"{$borrow['judul']}\" sudah bisa diambil di perpustakaan. Durasi pinjam 7 hari.",
            '/pinjaman');

        json_response(true, ['id' => $borrow_id], 'Peminjaman berhasil disetujui');

    } catch (\Throwable $e) {
        $pdo->rollBack();
        json_response(false, null, 'Gagal memproses persetujuan', 500);
    }
}

/**
 * PUT /api/admin/borrow/:id/reject
 * Transitions status Pending -> Ditolak. No stok change.
 * No transaction needed (single UPDATE, no stok involved).
 * Requires admin role.
 */
function admin_borrow_reject(PDO $pdo, int $borrow_id): void
{
    require_auth($pdo, 'admin');

    $stmt = $pdo->prepare(
        "SELECT p.status, p.user_id, b.judul
         FROM peminjaman p JOIN buku b ON p.buku_id = b.id
         WHERE p.id = ?"
    );
    $stmt->execute([$borrow_id]);
    $borrow = $stmt->fetch();

    if (!$borrow) {
        json_response(false, null, 'Data peminjaman tidak ditemukan', 404);
    }
    if ($borrow['status'] !== 'Pending') {
        json_response(false, null, 'Hanya peminjaman Pending yang dapat ditolak', 422);
    }

    $pdo->prepare(
        "UPDATE peminjaman SET status = 'Ditolak', tanggal_reject = NOW() WHERE id = ?"
    )->execute([$borrow_id]);

    notif_create($pdo, (int)$borrow['user_id'], 'rejected',
        'Pinjaman ditolak',
        "Pengajuan pinjam \"{$borrow['judul']}\" tidak disetujui. Hubungi pustakawan untuk info lebih lanjut.",
        '/pinjaman');

    json_response(true, ['id' => $borrow_id], 'Peminjaman berhasil ditolak');
}

/**
 * PUT /api/admin/borrow/:id/return
 * Transitions status Dipinjam -> Dikembalikan, increments stok_tersedia.
 * Uses PDO transaction + SELECT FOR UPDATE.
 * Requires admin role.
 */
function admin_borrow_return(PDO $pdo, int $borrow_id): void
{
    require_auth($pdo, 'admin');

    $pdo->beginTransaction();
    try {
        $s1 = $pdo->prepare(
            "SELECT p.status, p.buku_id, p.user_id, b.judul
             FROM peminjaman p JOIN buku b ON p.buku_id = b.id
             WHERE p.id = ? FOR UPDATE"
        );
        $s1->execute([$borrow_id]);
        $borrow = $s1->fetch();

        if (!$borrow) {
            $pdo->rollBack();
            json_response(false, null, 'Data peminjaman tidak ditemukan', 404);
        }
        if ($borrow['status'] !== 'Dipinjam') {
            $pdo->rollBack();
            json_response(false, null, 'Hanya peminjaman Dipinjam yang dapat dikembalikan', 422);
        }

        $pdo->prepare(
            "UPDATE buku SET stok_tersedia = stok_tersedia + 1 WHERE id = ?"
        )->execute([$borrow['buku_id']]);

        $pdo->prepare(
            "UPDATE peminjaman SET status = 'Dikembalikan', tanggal_kembali = NOW() WHERE id = ?"
        )->execute([$borrow_id]);

        $pdo->commit();

        notif_create($pdo, (int)$borrow['user_id'], 'returned',
            'Buku berhasil dikembalikan ✅',
            "\"{$borrow['judul']}\" telah tercatat dikembalikan. Terima kasih!",
            '/pinjaman');

        json_response(true, ['id' => $borrow_id], 'Pengembalian berhasil dicatat');

    } catch (\Throwable $e) {
        $pdo->rollBack();
        json_response(false, null, 'Gagal memproses pengembalian', 500);
    }
}

/**
 * POST /api/admin/borrows/bulk-approve  { ids: [1,2,3] }
 * POST /api/admin/borrows/bulk-reject   { ids: [1,2,3] }
 *
 * Loop per-id memakai logic yang sama dengan approve/reject single — masing-masing
 * dalam transaksi sendiri agar kegagalan satu ID tidak rollback yang sukses.
 * Return ringkasan: success_count + failed[] dengan reason.
 */
function admin_borrow_bulk(PDO $pdo, array $body, string $action): void
{
    require_auth($pdo, 'admin');

    $ids = $body['ids'] ?? [];
    if (!is_array($ids) || count($ids) === 0) {
        json_response(false, null, 'ids wajib diisi (array of integer)', 422);
    }
    if (count($ids) > 100) {
        json_response(false, null, 'Maksimal 100 ID per batch', 422);
    }

    $success = [];
    $failed  = [];

    foreach ($ids as $raw) {
        $id = (int)$raw;
        if ($id <= 0) {
            $failed[] = ['id' => $raw, 'reason' => 'ID tidak valid'];
            continue;
        }

        try {
            if ($action === 'approve') {
                $pdo->beginTransaction();
                $s1 = $pdo->prepare(
                    "SELECT p.status, p.buku_id, p.user_id, b.judul
                     FROM peminjaman p JOIN buku b ON p.buku_id = b.id
                     WHERE p.id = ? FOR UPDATE"
                );
                $s1->execute([$id]);
                $borrow = $s1->fetch();
                if (!$borrow)                       { $pdo->rollBack(); $failed[] = ['id' => $id, 'reason' => 'Tidak ditemukan']; continue; }
                if ($borrow['status'] !== 'Pending'){ $pdo->rollBack(); $failed[] = ['id' => $id, 'reason' => 'Status bukan Pending']; continue; }

                $upd = $pdo->prepare(
                    "UPDATE buku SET stok_tersedia = stok_tersedia - 1 WHERE id = ? AND stok_tersedia > 0"
                );
                $upd->execute([$borrow['buku_id']]);
                if ($upd->rowCount() === 0) {
                    $pdo->rollBack();
                    $failed[] = ['id' => $id, 'reason' => 'Stok habis'];
                    continue;
                }

                $pdo->prepare(
                    "UPDATE peminjaman SET status = 'Dipinjam', tanggal_approve = NOW() WHERE id = ?"
                )->execute([$id]);
                $pdo->commit();

                notif_create($pdo, (int)$borrow['user_id'], 'approved',
                    'Pinjaman disetujui! 🎉',
                    "\"{$borrow['judul']}\" sudah bisa diambil di perpustakaan. Durasi pinjam 7 hari.",
                    '/pinjaman');
                $success[] = $id;

            } else { // reject
                $stmt = $pdo->prepare(
                    "SELECT p.status, p.user_id, b.judul
                     FROM peminjaman p JOIN buku b ON p.buku_id = b.id
                     WHERE p.id = ?"
                );
                $stmt->execute([$id]);
                $borrow = $stmt->fetch();
                if (!$borrow)                        { $failed[] = ['id' => $id, 'reason' => 'Tidak ditemukan']; continue; }
                if ($borrow['status'] !== 'Pending') { $failed[] = ['id' => $id, 'reason' => 'Status bukan Pending']; continue; }

                $pdo->prepare(
                    "UPDATE peminjaman SET status = 'Ditolak', tanggal_reject = NOW() WHERE id = ?"
                )->execute([$id]);

                notif_create($pdo, (int)$borrow['user_id'], 'rejected',
                    'Pinjaman ditolak',
                    "Pengajuan pinjam \"{$borrow['judul']}\" tidak disetujui. Hubungi pustakawan untuk info lebih lanjut.",
                    '/pinjaman');
                $success[] = $id;
            }
        } catch (\Throwable $e) {
            if ($pdo->inTransaction()) $pdo->rollBack();
            $failed[] = ['id' => $id, 'reason' => 'Gagal diproses'];
        }
    }

    $verb = $action === 'approve' ? 'disetujui' : 'ditolak';
    $msg = count($failed) === 0
        ? count($success) . " pinjaman berhasil $verb"
        : count($success) . " berhasil, " . count($failed) . " gagal";

    json_response(true, [
        'success_count' => count($success),
        'success_ids'   => $success,
        'failed'        => $failed,
    ], $msg);
}

/**
 * GET /api/admin/borrows/export[?status=&from=&to=]
 * Streaming CSV download — UTF-8 with BOM agar Excel buka benar.
 * Filter sama dengan /admin/borrows + range tanggal_pinjam.
 */
function admin_borrows_export(PDO $pdo): void
{
    require_auth($pdo, 'admin');

    $status = trim($_GET['status'] ?? '');
    $from   = trim($_GET['from']   ?? '');
    $to     = trim($_GET['to']     ?? '');
    $valid  = ['Pending', 'Dipinjam', 'Dikembalikan', 'Ditolak'];

    $where  = [];
    $params = [];
    if ($status !== '' && in_array($status, $valid, true)) {
        $where[]  = 'p.status = ?';
        $params[] = $status;
    }
    if (preg_match('/^\d{4}-\d{2}-\d{2}$/', $from)) {
        $where[]  = 'p.created_at >= ?';
        $params[] = "$from 00:00:00";
    }
    if (preg_match('/^\d{4}-\d{2}-\d{2}$/', $to)) {
        $where[]  = 'p.created_at <= ?';
        $params[] = "$to 23:59:59";
    }
    $where_sql = $where ? 'WHERE ' . implode(' AND ', $where) : '';

    $stmt = $pdo->prepare(
        "SELECT p.id, u.nama AS siswa, u.username,
                b.judul, b.penulis, p.status,
                p.created_at AS tanggal_pinjam,
                p.tanggal_approve, p.tanggal_reject, p.tanggal_kembali
         FROM peminjaman p
         JOIN users u ON p.user_id = u.id
         JOIN buku  b ON p.buku_id = b.id
         $where_sql
         ORDER BY p.created_at DESC"
    );
    $stmt->execute($params);

    // Override JSON content-type yang di-set di bootstrap.php
    while (ob_get_level() > 0) ob_end_clean();
    header_remove('Content-Type');
    $filename = 'pinjaman_' . date('Y-m-d_His') . '.csv';
    header('Content-Type: text/csv; charset=utf-8');
    header("Content-Disposition: attachment; filename=\"$filename\"");

    $out = fopen('php://output', 'w');
    fwrite($out, "\xEF\xBB\xBF");  // UTF-8 BOM agar Excel render karakter ID benar
    fputcsv($out, [
        'ID', 'Siswa', 'Username', 'Judul Buku', 'Penulis', 'Status',
        'Tanggal Pinjam', 'Tanggal Disetujui', 'Tanggal Ditolak', 'Tanggal Dikembalikan'
    ]);
    while ($row = $stmt->fetch()) {
        fputcsv($out, [
            $row['id'], $row['siswa'], $row['username'],
            $row['judul'], $row['penulis'], $row['status'],
            $row['tanggal_pinjam'],
            $row['tanggal_approve'] ?? '',
            $row['tanggal_reject']  ?? '',
            $row['tanggal_kembali'] ?? '',
        ]);
    }
    fclose($out);
    exit();
}

/**
 * POST /api/admin/logo (multipart/form-data, field name: "logo")
 * Saves PNG/JPG to uploads/logo/logo.png relatif terhadap akar aplikasi (overwrites).
 * Upserts logo_url = '/uploads/logo/logo.png' into system_settings.
 * Requires admin role.
 */
function admin_logo_upload(PDO $pdo): void
{
    require_auth($pdo, 'admin');

    if (!isset($_FILES['logo']) || $_FILES['logo']['error'] !== UPLOAD_ERR_OK) {
        json_response(false, null, 'File logo tidak ditemukan atau terjadi error upload', 422);
    }

    $file    = $_FILES['logo'];
    $allowed = ['image/png', 'image/jpeg'];
    $finfo   = finfo_open(FILEINFO_MIME_TYPE);
    $mime    = finfo_file($finfo, $file['tmp_name']);
    finfo_close($finfo);

    if (!in_array($mime, $allowed, true)) {
        json_response(false, null, 'Hanya file PNG dan JPG yang diizinkan', 422);
    }

    // Diturunkan dari lokasi file ini, bukan path absolut Windows — server
    // produksi berjalan di Linux dengan struktur direktori yang berbeda.
    $dest_dir = dirname(__DIR__, 2) . DIRECTORY_SEPARATOR . 'uploads'
              . DIRECTORY_SEPARATOR . 'logo' . DIRECTORY_SEPARATOR;
    if (!is_dir($dest_dir)) {
        mkdir($dest_dir, 0755, true);
    }

    $dest = $dest_dir . 'logo.png';
    if (!move_uploaded_file($file['tmp_name'], $dest)) {
        json_response(false, null, 'Gagal menyimpan file logo', 500);
    }

    $logo_url = '/uploads/logo/logo.png';

    $stmt = $pdo->prepare(
        "INSERT INTO system_settings (`key`, value) VALUES ('logo_url', ?)
         ON DUPLICATE KEY UPDATE value = ?"
    );
    $stmt->execute([$logo_url, $logo_url]);

    json_response(true, ['logo_url' => $logo_url], 'Logo berhasil diperbarui');
}

/**
 * GET /api/settings/logo
 * Returns {logo_url} from system_settings. No auth required (public — Navbar reads it).
 */
function settings_logo_get(PDO $pdo): void
{
    $stmt = $pdo->prepare("SELECT value FROM system_settings WHERE `key` = 'logo_url'");
    $stmt->execute();
    $row = $stmt->fetch();
    json_response(true, ['logo_url' => $row ? $row['value'] : null], 'Berhasil');
}

/**
 * GET /api/recommend/personal[?limit=5]
 * Proxies to Flask http://localhost:5000/recommend/personal?user_id=N&limit=N
 * CURLOPT_CONNECTTIMEOUT=3, CURLOPT_TIMEOUT=5. Fallback [] if Flask down.
 * Requires auth (any role — user_id from JWT sub).
 */
function recommend_personal_proxy(PDO $pdo): void
{
    $user    = require_auth($pdo);
    $user_id = (int)$user->sub;
    $limit   = min(20, max(1, (int)($_GET['limit'] ?? 5)));
    $url     = CBF_URL . "/recommend/personal?user_id={$user_id}&limit={$limit}";

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

/**
 * GET /api/popular[?limit=5]
 * Proxies to Flask http://localhost:5000/popular?limit=N
 * CURLOPT_CONNECTTIMEOUT=3, CURLOPT_TIMEOUT=5. Fallback [] if Flask down.
 * No auth required (public endpoint).
 */
function popular_proxy(PDO $pdo): void
{
    $limit = min(20, max(1, (int)($_GET['limit'] ?? 5)));
    $url   = CBF_URL . "/popular?limit={$limit}";

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
        json_response(true, [], 'Populer tidak tersedia', 200);
    }

    $data = json_decode($raw, true);
    json_response(true, is_array($data) ? $data : [], 'Berhasil');
}

/**
 * GET /api/admin/students[?q=nama][&page=1][&limit=20]
 * Daftar siswa terdaftar beserta ringkasan aktivitas peminjamannya.
 *
 * Kolom password sengaja TIDAK pernah diambil dari basis data — bukan hanya
 * disembunyikan saat keluaran — supaya hash tidak melewati lapisan aplikasi
 * sama sekali.
 * Requires admin role.
 */
function admin_students_list(PDO $pdo): void
{
    require_auth($pdo, 'admin');

    $q     = trim($_GET['q'] ?? '');
    $page  = max(1, (int)($_GET['page'] ?? 1));
    $limit = min(50, max(1, (int)($_GET['limit'] ?? 20)));
    $skip  = ($page - 1) * $limit;

    $where  = "WHERE u.role = 'siswa'";
    $params = [];
    if ($q !== '') {
        $where .= " AND (u.nama LIKE ? OR u.username LIKE ?)";
        $params[] = "%$q%";
        $params[] = "%$q%";
    }

    $stmtTotal = $pdo->prepare("SELECT COUNT(*) FROM users u $where");
    $stmtTotal->execute($params);
    $total = (int) $stmtTotal->fetchColumn();

    // LIMIT/OFFSET disisipkan sebagai integer hasil cast, bukan placeholder,
    // karena PDO dengan emulasi dimatikan mengirimkannya sebagai string.
    $stmt = $pdo->prepare(
        "SELECT u.id, u.nama, u.username, u.created_at,
                COUNT(p.id)                                                   AS total_pinjam,
                SUM(p.status IN ('Pending','Dipinjam'))                       AS pinjaman_aktif,
                SUM(p.status = 'Dipinjam'
                    AND p.tanggal_approve IS NOT NULL
                    AND DATE_ADD(p.tanggal_approve, INTERVAL 7 DAY) < NOW())  AS terlambat,
                MAX(p.created_at)                                             AS terakhir_pinjam
         FROM users u
         LEFT JOIN peminjaman p ON p.user_id = u.id
         $where
         GROUP BY u.id, u.nama, u.username, u.created_at
         ORDER BY u.nama
         LIMIT $limit OFFSET $skip"
    );
    $stmt->execute($params);
    $items = $stmt->fetchAll();

    foreach ($items as &$row) {
        $row['total_pinjam']   = (int) $row['total_pinjam'];
        $row['pinjaman_aktif'] = (int) $row['pinjaman_aktif'];
        $row['terlambat']      = (int) $row['terlambat'];
    }
    unset($row);

    json_response(true, [
        'items'       => $items,
        'total'       => $total,
        'page'        => $page,
        'limit'       => $limit,
        'total_pages' => (int) ceil($total / $limit),
    ], 'Berhasil');
}

/**
 * GET /api/admin/students/:id
 * Detail satu siswa beserta seluruh riwayat peminjamannya.
 * Requires admin role.
 */
function admin_student_detail(PDO $pdo, int $user_id): void
{
    require_auth($pdo, 'admin');

    $stmt = $pdo->prepare(
        "SELECT id, nama, username, created_at FROM users WHERE id = ? AND role = 'siswa'"
    );
    $stmt->execute([$user_id]);
    $siswa = $stmt->fetch();

    if (!$siswa) {
        json_response(false, null, 'Siswa tidak ditemukan', 404);
    }

    $stmt = $pdo->prepare(
        "SELECT p.id, p.status, p.created_at AS tanggal_pinjam,
                p.tanggal_approve, p.tanggal_kembali, p.tanggal_reject,
                b.id AS buku_id, b.judul, b.penulis, k.nama AS kategori_nama,
                CASE WHEN p.status = 'Dipinjam' AND p.tanggal_approve IS NOT NULL
                     THEN DATEDIFF(NOW(), DATE_ADD(p.tanggal_approve, INTERVAL 7 DAY))
                     ELSE NULL END AS hari_terlambat
         FROM peminjaman p
         JOIN buku b     ON b.id = p.buku_id
         JOIN kategori k ON k.id = b.kategori_id
         WHERE p.user_id = ?
         ORDER BY p.created_at DESC"
    );
    $stmt->execute([$user_id]);
    $riwayat = $stmt->fetchAll();

    $ringkasan = [
        'total'        => count($riwayat),
        'aktif'        => 0,
        'dikembalikan' => 0,
        'ditolak'      => 0,
        'terlambat'    => 0,
    ];
    foreach ($riwayat as $r) {
        if     ($r['status'] === 'Dikembalikan') $ringkasan['dikembalikan']++;
        elseif ($r['status'] === 'Ditolak')      $ringkasan['ditolak']++;
        else                                     $ringkasan['aktif']++;
        if ($r['hari_terlambat'] !== null && (int)$r['hari_terlambat'] > 0) {
            $ringkasan['terlambat']++;
        }
    }

    json_response(true, [
        'siswa'     => $siswa,
        'ringkasan' => $ringkasan,
        'riwayat'   => $riwayat,
    ], 'Berhasil');
}

/**
 * DELETE /api/admin/students/:id
 * Hapus akun siswa beserta riwayat peminjamannya.
 *
 * Dua pengaman yang disengaja:
 *
 * 1. Hanya baris ber-role 'siswa' yang dapat dihapus. Akun admin tidak dapat
 *    disentuh lewat endpoint ini, sehingga tidak ada jalur untuk menghapus
 *    admin terakhir dan mengunci diri dari sistem.
 *
 * 2. Siswa yang masih memiliki peminjaman berstatus Pending atau Dipinjam
 *    TIDAK dapat dihapus. Buku fisiknya sedang berada di tangan siswa itu;
 *    menghapus akunnya akan menghilangkan jejak siapa yang memegang buku
 *    sekaligus membuat stok_tersedia tidak pernah kembali.
 *
 * Riwayat yang sudah selesai (Dikembalikan/Ditolak) ikut terhapus, karena FK
 * peminjaman->users tidak memakai ON DELETE CASCADE. favorites dan
 * notifications terhapus otomatis oleh cascade-nya masing-masing.
 *
 * Requires admin role.
 */
function admin_student_delete(PDO $pdo, int $user_id): void
{
    require_auth($pdo, 'admin');

    $stmt = $pdo->prepare("SELECT id, nama, role FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $target = $stmt->fetch();

    if (!$target) {
        json_response(false, null, 'Siswa tidak ditemukan', 404);
    }
    if ($target['role'] !== 'siswa') {
        json_response(false, null, 'Hanya akun siswa yang dapat dihapus melalui halaman ini', 403);
    }

    $stmt = $pdo->prepare(
        "SELECT COUNT(*) FROM peminjaman
         WHERE user_id = ? AND status IN ('Pending', 'Dipinjam')"
    );
    $stmt->execute([$user_id]);
    $aktif = (int) $stmt->fetchColumn();

    if ($aktif > 0) {
        json_response(false, ['pinjaman_aktif' => $aktif],
            "Tidak dapat menghapus: siswa ini masih memiliki $aktif peminjaman aktif. "
            . "Selesaikan pengembalian atau tolak pengajuannya terlebih dahulu.", 422);
    }

    $pdo->beginTransaction();
    try {
        $stmt = $pdo->prepare("DELETE FROM peminjaman WHERE user_id = ?");
        $stmt->execute([$user_id]);
        $riwayat_terhapus = $stmt->rowCount();

        $pdo->prepare("DELETE FROM users WHERE id = ? AND role = 'siswa'")->execute([$user_id]);

        $pdo->commit();
    } catch (\Throwable $e) {
        $pdo->rollBack();
        json_response(false, null, 'Gagal menghapus akun siswa', 500);
    }

    json_response(true, [
        'id'               => $user_id,
        'nama'             => $target['nama'],
        'riwayat_terhapus' => $riwayat_terhapus,
    ], "Akun siswa \"{$target['nama']}\" berhasil dihapus");
}
