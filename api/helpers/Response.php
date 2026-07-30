<?php
declare(strict_types=1);

function json_response(bool $success, mixed $data, string $message, int $code = 200): never
{
    http_response_code($code);
    echo json_encode(
        ['success' => $success, 'data' => $data, 'message' => $message],
        JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES
    );
    exit();
}