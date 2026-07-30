<?php
declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/helpers/Response.php';

$body = json_decode(file_get_contents('php://input'), true) ?? [];

$uri    = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'];

$path = preg_replace('#^/api#', '', $uri);
$path = rtrim($path, '/') ?: '/';

if ($method === 'POST' && $path === '/auth/register') {
    require_once __DIR__ . '/controllers/AuthController.php';
    auth_register($pdo, $body);

} elseif ($method === 'POST' && $path === '/auth/login') {
    require_once __DIR__ . '/controllers/AuthController.php';
    auth_login($pdo, $body);

} elseif ($method === 'POST' && $path === '/auth/logout') {
    require_once __DIR__ . '/controllers/AuthController.php';
    auth_logout($pdo);

} elseif ($method === 'GET' && $path === '/auth/me') {
    require_once __DIR__ . '/controllers/AuthController.php';
    auth_me($pdo);

} elseif ($method === 'GET' && $path === '/books') {
    require_once __DIR__ . '/controllers/BookController.php';
    books_list($pdo);

} elseif ($method === 'GET' && $path === '/categories') {
    require_once __DIR__ . '/controllers/BookController.php';
    categories_list($pdo);

} elseif ($method === 'POST' && $path === '/books/upload-cover') {
    require_once __DIR__ . '/controllers/BookController.php';
    book_cover_upload($pdo);

} elseif ($method === 'POST' && $path === '/books') {
    require_once __DIR__ . '/controllers/BookController.php';
    book_create($pdo, $body);

} elseif ($method === 'GET' && preg_match('#^/books/(\d+)/recommend$#', $path, $m)) {
    require_once __DIR__ . '/controllers/BorrowController.php';
    recommend_proxy($pdo, (int)$m[1]);

} elseif ($method === 'GET' && preg_match('#^/books/(\d+)$#', $path, $m)) {
    require_once __DIR__ . '/controllers/BookController.php';
    book_get($pdo, (int)$m[1]);

} elseif ($method === 'PUT' && preg_match('#^/books/(\d+)$#', $path, $m)) {
    require_once __DIR__ . '/controllers/BookController.php';
    book_update($pdo, (int)$m[1], $body);

} elseif ($method === 'DELETE' && preg_match('#^/books/(\d+)$#', $path, $m)) {
    require_once __DIR__ . '/controllers/BookController.php';
    book_delete($pdo, (int)$m[1]);

} elseif ($method === 'POST' && $path === '/borrow') {
    require_once __DIR__ . '/controllers/BorrowController.php';
    borrow_request($pdo, $body);

} elseif ($method === 'GET' && $path === '/borrow/status') {
    require_once __DIR__ . '/controllers/BorrowController.php';
    borrow_status($pdo);

} elseif ($method === 'GET' && preg_match('#^/borrow/(\d+)$#', $path, $m)) {
    require_once __DIR__ . '/controllers/BorrowController.php';
    borrow_get($pdo, (int)$m[1]);

} elseif ($method === 'PUT' && preg_match('#^/admin/borrow/(\d+)/approve$#', $path, $m)) {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_borrow_approve($pdo, (int)$m[1]);

} elseif ($method === 'PUT' && preg_match('#^/admin/borrow/(\d+)/reject$#', $path, $m)) {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_borrow_reject($pdo, (int)$m[1]);

} elseif ($method === 'PUT' && preg_match('#^/admin/borrow/(\d+)/return$#', $path, $m)) {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_borrow_return($pdo, (int)$m[1]);

} elseif ($method === 'POST' && $path === '/admin/borrows/bulk-approve') {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_borrow_bulk($pdo, $body, 'approve');

} elseif ($method === 'POST' && $path === '/admin/borrows/bulk-reject') {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_borrow_bulk($pdo, $body, 'reject');

} elseif ($method === 'GET' && $path === '/admin/borrows/export') {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_borrows_export($pdo);

} elseif ($method === 'GET' && $path === '/admin/borrows') {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_borrows_list($pdo);

} elseif ($method === 'DELETE' && preg_match('#^/admin/students/(\d+)$#', $path, $m)) {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_student_delete($pdo, (int)$m[1]);

} elseif ($method === 'GET' && preg_match('#^/admin/students/(\d+)$#', $path, $m)) {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_student_detail($pdo, (int)$m[1]);

} elseif ($method === 'GET' && $path === '/admin/students') {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_students_list($pdo);

} elseif ($method === 'GET' && $path === '/admin/dashboard') {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_dashboard($pdo);

} elseif ($method === 'POST' && $path === '/admin/logo') {
    require_once __DIR__ . '/controllers/AdminController.php';
    admin_logo_upload($pdo);

} elseif ($method === 'GET' && $path === '/settings/logo') {
    require_once __DIR__ . '/controllers/AdminController.php';
    settings_logo_get($pdo);

} elseif ($method === 'GET' && $path === '/recommend/personal') {
    require_once __DIR__ . '/controllers/AdminController.php';
    recommend_personal_proxy($pdo);

} elseif ($method === 'GET' && $path === '/popular') {
    require_once __DIR__ . '/controllers/AdminController.php';
    popular_proxy($pdo);

} elseif ($method === 'GET' && $path === '/favorites') {
    require_once __DIR__ . '/controllers/FavoriteController.php';
    favorites_list($pdo);

} elseif ($method === 'POST' && $path === '/favorites') {
    require_once __DIR__ . '/controllers/FavoriteController.php';
    favorite_add($pdo, $body);

} elseif ($method === 'DELETE' && preg_match('#^/favorites/(\d+)$#', $path, $m)) {
    require_once __DIR__ . '/controllers/FavoriteController.php';
    favorite_remove($pdo, (int)$m[1]);

} elseif ($method === 'GET' && $path === '/notifications') {
    require_once __DIR__ . '/controllers/NotificationController.php';
    notifications_list($pdo);

} elseif ($method === 'POST' && $path === '/notifications/mark-read') {
    require_once __DIR__ . '/controllers/NotificationController.php';
    notifications_mark_read($pdo, $body);

} elseif ($method === 'PUT' && $path === '/users/me') {
    require_once __DIR__ . '/controllers/ProfileController.php';
    profile_update($pdo, $body);

} elseif ($method === 'GET' && $path === '/users/me/stats') {
    require_once __DIR__ . '/controllers/ProfileController.php';
    profile_stats($pdo);

} elseif ($method === 'POST' && $path === '/auth/change-password') {
    require_once __DIR__ . '/controllers/ProfileController.php';
    profile_change_password($pdo, $body);

} else {
    json_response(false, null, 'Endpoint tidak ditemukan', 404);
}