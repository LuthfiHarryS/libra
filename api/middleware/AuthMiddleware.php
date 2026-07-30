<?php
declare(strict_types=1);

function require_auth(PDO $pdo, ?string $required_role = null): object
{
    // mod_rewrite mengubah HTTP_AUTHORIZATION → REDIRECT_HTTP_AUTHORIZATION
    $auth_header = $_SERVER['HTTP_AUTHORIZATION']
        ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION']
        ?? '';
    if (!str_starts_with($auth_header, 'Bearer ')) {
        http_response_code(401);
        echo json_encode(['success' => false, 'data' => null, 'message' => 'Token diperlukan'],
                         JSON_UNESCAPED_UNICODE);
        exit();
    }
    $token = substr($auth_header, 7);

    $payload = decode_jwt($token);
    if ($payload === null) {
        http_response_code(401);
        echo json_encode(['success' => false, 'data' => null,
                          'message' => 'Token tidak valid atau sudah kadaluarsa'],
                         JSON_UNESCAPED_UNICODE);
        exit();
    }

    $pdo->exec("DELETE FROM token_blacklist WHERE expires_at < NOW()");

    $stmt = $pdo->prepare("SELECT 1 FROM token_blacklist WHERE jti = ?");
    $stmt->execute([$payload->jti]);
    if ($stmt->fetch()) {
        http_response_code(401);
        echo json_encode(['success' => false, 'data' => null, 'message' => 'Token telah di-logout'],
                         JSON_UNESCAPED_UNICODE);
        exit();
    }

    if ($required_role !== null && $payload->role !== $required_role) {
        http_response_code(403);
        echo json_encode(['success' => false, 'data' => null, 'message' => 'Akses ditolak: hanya admin'],
                         JSON_UNESCAPED_UNICODE);
        exit();
    }

    return $payload;
}