<?php
declare(strict_types=1);

require_once __DIR__ . '/../middleware/AuthMiddleware.php';
require_once __DIR__ . '/../helpers/Response.php';

function auth_register(PDO $pdo, array $body): void
{
    $nama     = trim($body['nama']     ?? '');
    $username = trim($body['username'] ?? '');
    $pass     =      $body['password'] ?? '';

    if (!$nama || !$username || !$pass) {
        json_response(false, null, 'Nama, username, dan password wajib diisi', 400);
    }
    if (!preg_match('/^[a-zA-Z0-9._]{3,30}$/', $username)) {
        json_response(false, null, 'Username 3-30 karakter, hanya huruf, angka, titik, dan garis bawah', 400);
    }
    if (strlen($pass) < 8) {
        json_response(false, null, 'Password minimal 8 karakter', 400);
    }

    $hash = password_hash($pass, PASSWORD_BCRYPT);

    try {
        $stmt = $pdo->prepare(
            "INSERT INTO users (nama, username, password, role) VALUES (?, ?, ?, 'siswa')"
        );
        $stmt->execute([$nama, $username, $hash]);
        $user_id = (int)$pdo->lastInsertId();
        json_response(true, [
            'id'       => $user_id,
            'nama'     => $nama,
            'username' => $username,
            'role'     => 'siswa',
        ], 'Akun berhasil dibuat', 201);
    } catch (PDOException $e) {
        if (str_contains($e->getMessage(), 'Duplicate entry')) {
            json_response(false, null, 'Username sudah terdaftar', 409);
        }
        json_response(false, null, 'Gagal membuat akun', 500);
    }
}

function auth_login(PDO $pdo, array $body): void
{
    $username = trim($body['username'] ?? '');
    $pass     =      $body['password'] ?? '';
    $ip       = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';

    if (!$username || !$pass) {
        json_response(false, null, 'Username dan password wajib diisi', 400);
    }

    // Rate limit: max LOGIN_MAX_ATTEMPTS gagal per IP+username dalam LOGIN_WINDOW_SECONDS detik
    $rl = $pdo->prepare(
        "SELECT COUNT(*) FROM login_attempts
         WHERE ip = ? AND username = ? AND success = 0
           AND attempted_at > (NOW() - INTERVAL ? SECOND)"
    );
    $rl->execute([$ip, $username, LOGIN_WINDOW_SECONDS]);
    if ((int)$rl->fetchColumn() >= LOGIN_MAX_ATTEMPTS) {
        $minutes = (int)ceil(LOGIN_WINDOW_SECONDS / 60);
        json_response(false, null,
            "Terlalu banyak percobaan login. Coba lagi dalam $minutes menit.", 429);
    }

    $stmt = $pdo->prepare(
        "SELECT id, nama, username, password, role FROM users WHERE username = ?"
    );
    $stmt->execute([$username]);
    $user = $stmt->fetch();

    if (!$user || !password_verify($pass, $user['password'])) {
        $pdo->prepare("INSERT INTO login_attempts (ip, username, success) VALUES (?, ?, 0)")
            ->execute([$ip, $username]);
        json_response(false, null, 'Username atau password salah', 401);
    }

    // Sukses — catat + bersihkan attempts lama (best-effort, jangan blok login kalau gagal)
    try {
        $pdo->prepare("INSERT INTO login_attempts (ip, username, success) VALUES (?, ?, 1)")
            ->execute([$ip, $username]);
        $pdo->prepare(
            "DELETE FROM login_attempts WHERE attempted_at < (NOW() - INTERVAL 1 DAY)"
        )->execute();
    } catch (\Throwable) {}

    $token = encode_jwt((int)$user['id'], $user['role']);

    json_response(true, [
        'token' => $token,
        'user'  => [
            'id'       => (int)$user['id'],
            'nama'     => $user['nama'],
            'username' => $user['username'],
            'role'     => $user['role'],
        ],
    ], 'Login berhasil');
}

function auth_logout(PDO $pdo): void
{
    $payload = require_auth($pdo);

    $stmt = $pdo->prepare(
        "INSERT IGNORE INTO token_blacklist (jti, expires_at) VALUES (?, FROM_UNIXTIME(?))"
    );
    $stmt->execute([$payload->jti, $payload->exp]);

    json_response(true, null, 'Logout berhasil');
}

function auth_me(PDO $pdo): void
{
    $payload = require_auth($pdo);

    $stmt = $pdo->prepare(
        "SELECT id, nama, username, role FROM users WHERE id = ?"
    );
    $stmt->execute([(int)$payload->sub]);
    $user = $stmt->fetch();

    if (!$user) {
        json_response(false, null, 'User tidak ditemukan', 404);
    }

    json_response(true, [
        'id'       => (int)$user['id'],
        'nama'     => $user['nama'],
        'username' => $user['username'],
        'role'     => $user['role'],
    ], 'OK');
}