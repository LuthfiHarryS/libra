<?php
declare(strict_types=1);

require_once __DIR__ . '/../vendor/autoload.php';

use Firebase\JWT\JWT;
use Firebase\JWT\Key;
use Firebase\JWT\ExpiredException;
use Firebase\JWT\SignatureInvalidException;

// Load sensitive config (gitignored). Fail-fast kalau tidak ada — jangan jalan dengan default secret.
$config_path = __DIR__ . '/config.local.php';
if (!file_exists($config_path)) {
    http_response_code(500);
    echo json_encode(['success' => false, 'data' => null,
        'message' => 'Server misconfigured: config.local.php missing']);
    exit();
}
$config = require $config_path;

// CORS whitelist — hanya origin yang ada di config.CORS_ALLOWED_ORIGINS yang di-echo balik.
// Browser memblokir request kalau Origin tidak match Access-Control-Allow-Origin.
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && in_array($origin, $config['CORS_ALLOWED_ORIGINS'], true)) {
    header("Access-Control-Allow-Origin: $origin");
    header('Vary: Origin');
}
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Content-Type: application/json; charset=utf-8');

// Security headers — defense in depth
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: no-referrer');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit();
}

define('JWT_SECRET',         $config['JWT_SECRET']);
define('JWT_EXPIRY',         $config['JWT_EXPIRY']);
define('BATAS_PINJAM',       $config['BATAS_PINJAM']);
define('LOGIN_MAX_ATTEMPTS', $config['LOGIN_MAX_ATTEMPTS']);
define('LOGIN_WINDOW_SECONDS', $config['LOGIN_WINDOW_SECONDS']);
define('TINYPNG_API_KEY',    $config['TINYPNG_API_KEY'] ?? '');
define('CBF_URL',            rtrim($config['CBF_URL'] ?? 'http://127.0.0.1:5000', '/'));

try {
    $pdo = new PDO(
        "mysql:host={$config['DB_HOST']};dbname={$config['DB_NAME']};charset=utf8mb4",
        $config['DB_USER'],
        $config['DB_PASS'],
        [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]
    );
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'data' => null, 'message' => 'Database connection failed']);
    exit();
}

function generate_jti(): string
{
    $data = openssl_random_pseudo_bytes(16);
    $data[6] = chr(ord($data[6]) & 0x0f | 0x40);
    $data[8] = chr(ord($data[8]) & 0x3f | 0x80);
    return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
}

function encode_jwt(int $user_id, string $role): string
{
    $payload = [
        'sub'  => $user_id,
        'role' => $role,
        'jti'  => generate_jti(),
        'iat'  => time(),
        'exp'  => time() + JWT_EXPIRY,
    ];
    return JWT::encode($payload, JWT_SECRET, 'HS256');
}

function decode_jwt(string $token): ?object
{
    try {
        return JWT::decode($token, new Key(JWT_SECRET, 'HS256'));
    } catch (ExpiredException) {
        return null;
    } catch (SignatureInvalidException) {
        return null;
    } catch (\Exception) {
        return null;
    }
}
