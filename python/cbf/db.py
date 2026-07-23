"""
db.py — PyMySQL connection helper untuk CBF service.

Konfigurasi: localhost:3306, database libra_db, user root, no password.
Charset utf8mb4 wajib — matches schema.sql collation utf8mb4_unicode_ci.
"""
import pymysql
import pymysql.cursors


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
        host='localhost',
        user='root',
        password='',            # XAMPP default: no password
        database='libra_db',
        charset='utf8mb4',      # wajib — matches utf8mb4_unicode_ci schema
        cursorclass=pymysql.cursors.DictCursor  # fetchall() returns list of dicts
    )
