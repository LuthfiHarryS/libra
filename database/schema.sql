-- LIBRA Digital Library — Database Schema
-- MariaDB 10.4.32 (via XAMPP) — sintaks kompatibel MySQL 8
-- Encoding: utf8mb4_unicode_ci (per D-17)
--
-- PENTING: Jalankan schema.sql ini SETELAH my.ini diubah dan MariaDB di-restart.
-- my.ini: C:\xampp\mysql\bin\my.ini
-- Ubah baris: collation-server=utf8mb4_general_ci  -->  collation-server=utf8mb4_unicode_ci
-- Kemudian restart MariaDB via XAMPP Control Panel.
--
-- Urutan eksekusi:
--   1. Edit my.ini + restart MariaDB (collation-server=utf8mb4_unicode_ci)
--   2. Jalankan schema.sql ini (DDL)
--   3. Jalankan seed.php (data awal + bcrypt passwords)
--
-- Cara menjalankan:
--   OPSI A — MySQL CLI:
--     C:\xampp\mysql\bin\mysql.exe -u root < database\schema.sql
--   OPSI B — phpMyAdmin:
--     Buka http://localhost/phpmyadmin → tab "SQL" → paste isi file ini → klik "Go"

CREATE DATABASE IF NOT EXISTS libra_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE libra_db;

-- ============================================================
-- Tabel 1: kategori
-- Tidak ada FK dependency — dibuat pertama
-- Relasi 1:N ke tabel buku (D-07)
-- ============================================================
CREATE TABLE IF NOT EXISTS kategori (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nama       VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Tabel 2: buku
-- FK ke kategori; FULLTEXT index pada judul+penulis+sinopsis (D-05)
-- stok_total + stok_tersedia terpisah (D-01)
-- isbn nullable (D-02), cover_url nullable (D-03), sinopsis nullable (D-04)
-- FULLTEXT didefinisikan di CREATE TABLE — bukan ALTER TABLE setelah INSERT
-- ============================================================
CREATE TABLE IF NOT EXISTS buku (
    id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    kategori_id   INT UNSIGNED NOT NULL,
    judul         VARCHAR(255) NOT NULL,
    penulis       VARCHAR(255) NOT NULL,
    isbn          VARCHAR(20)  NULL,
    sinopsis      TEXT         NULL,
    cover_url     VARCHAR(500) NULL,
    stok_total    INT UNSIGNED NOT NULL DEFAULT 1,
    stok_tersedia INT UNSIGNED NOT NULL DEFAULT 1,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (kategori_id) REFERENCES kategori(id),
    FULLTEXT KEY ft_buku (judul, penulis, sinopsis)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Tabel 3: users
-- username UNIQUE (login identity — no email); role ENUM (D-09)
-- password VARCHAR(255) untuk bcrypt 60-char
-- Tidak ada kolom akademik (kelas/NIS) — per D-08
-- updated_at: ON UPDATE CURRENT_TIMESTAMP untuk audit trail
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nama       VARCHAR(255) NOT NULL,
    username   VARCHAR(50)  NOT NULL,
    password   VARCHAR(255) NOT NULL,
    role       ENUM('siswa', 'admin') NOT NULL DEFAULT 'siswa',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Tabel 4: peminjaman
-- FK ke users + buku (InnoDB enforce real-time — urutan INSERT: kategori→buku→users→peminjaman)
-- 4 kolom timestamp (D-11): created_at NOT NULL, 3 nullable per status transition
-- status ENUM 4 nilai (D-10), default 'Pending'
-- Batas pinjam 3 buku: TIDAK di DB — hardcoded di PHP (D-12)
-- ============================================================
CREATE TABLE IF NOT EXISTS peminjaman (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED NOT NULL,
    buku_id         INT UNSIGNED NOT NULL,
    status          ENUM('Pending', 'Dipinjam', 'Dikembalikan', 'Ditolak') NOT NULL DEFAULT 'Pending',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tanggal_approve DATETIME NULL,
    tanggal_kembali DATETIME NULL,
    tanggal_reject  DATETIME NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (buku_id) REFERENCES buku(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Verifikasi setelah eksekusi (jalankan manual di MySQL CLI atau phpMyAdmin):
--
--   -- V1: Semua 4 tabel terbentuk
--   SHOW TABLES;
--   -- Expected: buku, kategori, peminjaman, users
--
--   -- V2: FULLTEXT index ada dan benar
--   SHOW INDEX FROM buku WHERE Index_type = 'FULLTEXT';
--   -- Expected: 1 row, Key_name='ft_buku', Column_name='judul'
--
--   -- V3: Charset dan collation benar
--   SHOW CREATE TABLE buku;
--   -- Expected mengandung: CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci, FULLTEXT KEY `ft_buku`
--
--   -- V4: Charset tabel users benar
--   SHOW CREATE TABLE users;
--   -- Expected mengandung: CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci, UNIQUE KEY `uk_username`
--
--   -- V5: FK constraint tabel peminjaman terbentuk
--   SHOW CREATE TABLE peminjaman;
--   -- Expected: FOREIGN KEY (user_id) REFERENCES users(id)
--   --           FOREIGN KEY (buku_id) REFERENCES buku(id)
--
--   -- V6: Collation server aktif (harus dijalankan setelah restart MariaDB)
--   SHOW VARIABLES LIKE 'collation_server';
--   -- Expected: utf8mb4_unicode_ci
-- ============================================================

-- ============================================================
-- Phase 7: Admin logo upload (D-06)
-- system_settings: key-value store untuk konfigurasi sistem
-- ============================================================
CREATE TABLE IF NOT EXISTS system_settings (
    id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `key` VARCHAR(100) NOT NULL,
    value TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- P3 — Notifikasi in-app
-- notifications: event log untuk siswa (approved/rejected/returned)
-- Reminder due-date di-generate dinamis di endpoint (tidak butuh row di sini)
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED NOT NULL,
    type        ENUM('approved','rejected','returned','info') NOT NULL,
    title       VARCHAR(150) NOT NULL,
    body        VARCHAR(500) NULL,
    link_url    VARCHAR(200) NULL,             -- frontend path saat klik notif
    is_read     TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_user_unread (user_id, is_read, created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- P2 — Wishlist/Favorit
-- favorites: relasi many-to-many user ↔ buku. Composite PK mencegah duplikat.
-- ON DELETE CASCADE: kalau user/buku dihapus, favorit terikutkan.
-- ============================================================
CREATE TABLE IF NOT EXISTS favorites (
    user_id    INT UNSIGNED NOT NULL,
    buku_id    INT UNSIGNED NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, buku_id),
    INDEX idx_user    (user_id, created_at),
    INDEX idx_buku    (buku_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (buku_id) REFERENCES buku(id)  ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Security hardening: rate limit /auth/login (post-Phase 7 P0 fix)
-- login_attempts: catat percobaan login per IP+username untuk block brute force
-- Dibersihkan via window query — tidak perlu cron khusus
-- ============================================================
CREATE TABLE IF NOT EXISTS login_attempts (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ip         VARCHAR(45)  NOT NULL,                  -- IPv4 max 15, IPv6 max 45
    username   VARCHAR(150) NOT NULL,
    success    TINYINT(1)   NOT NULL DEFAULT 0,
    attempted_at DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_lookup  (ip, username, attempted_at),
    INDEX idx_cleanup (attempted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
