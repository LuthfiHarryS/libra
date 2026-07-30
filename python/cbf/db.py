"""
db.py — PyMySQL connection helper untuk CBF service.

Kredensial dibaca dari environment variable supaya server produksi tidak perlu
memakai root tanpa password seperti XAMPP. Default-nya sengaja dibiarkan sama
dengan XAMPP agar dev lokal tetap jalan tanpa setup tambahan.

Charset utf8mb4 wajib — matches schema.sql collation utf8mb4_unicode_ci.
"""
import os

import pymysql
import pymysql.cursors

DB_HOST = os.environ.get('LIBRA_DB_HOST', 'localhost')
DB_USER = os.environ.get('LIBRA_DB_USER', 'root')
DB_PASS = os.environ.get('LIBRA_DB_PASS', '')
DB_NAME = os.environ.get('LIBRA_DB_NAME', 'libra_db')


def get_db_connection() -> pymysql.connections.Connection:
    """
    Buka koneksi PyMySQL ke libra_db.

    CRITICAL: cursorclass HARUS di connect(), BUKAN di cursor().
    Menaruh cursorclass di cursor() akan raise TypeError di PyMySQL 1.x.
    (RESEARCH.md Pitfall 6)

    Returns:
        pymysql.connections.Connection dengan DictCursor aktif.
        Caller bertanggung jawab untuk menutup koneksi (gunakan 'with conn:').
    """
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4',      # wajib — matches utf8mb4_unicode_ci schema
        cursorclass=pymysql.cursors.DictCursor  # fetchall() returns list of dicts
    )
