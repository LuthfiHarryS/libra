-- migrate_relative_urls.sql — Ubah URL aset dari absolut localhost ke relatif.
--
-- Sebelum: http://localhost:8080/uploads/covers/x.webp
-- Sesudah: /uploads/covers/x.webp
--
-- Alasan: React, API, dan file upload dilayani dari satu origin. URL relatif
-- otomatis benar di localhost maupun https://perpuslibra.web.id, jadi tidak perlu
-- migrasi lagi kalau domain berubah. URL absolut berisi "localhost" akan membuat
-- gambar tidak muncul sama sekali saat diakses dari perangkat lain.
--
-- Jalankan:
--   mysql -u root -p libra_db < database/migrate_relative_urls.sql

USE libra_db;

-- Cover buku (261 baris hasil seed_notes_books.php)
UPDATE buku
SET cover_url = CONCAT('/uploads/covers/', SUBSTRING_INDEX(cover_url, '/uploads/covers/', -1))
WHERE cover_url LIKE 'http://localhost:8080/uploads/covers/%';

-- Logo sekolah di system_settings
UPDATE system_settings
SET value = '/uploads/logo/logo.png'
WHERE `key` = 'logo_url'
  AND value LIKE 'http://localhost:8080/%';

-- Verifikasi: kedua angka di bawah harus 0
SELECT
    (SELECT COUNT(*) FROM buku WHERE cover_url LIKE 'http%localhost%')            AS sisa_cover_absolut,
    (SELECT COUNT(*) FROM system_settings WHERE value LIKE 'http%localhost%')     AS sisa_setting_absolut,
    (SELECT COUNT(*) FROM buku WHERE cover_url LIKE '/uploads/covers/%')          AS cover_relatif_ok;
