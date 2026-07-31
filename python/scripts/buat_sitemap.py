"""
buat_sitemap.py — Bangkitkan react/public/sitemap.xml dari katalog di MySQL.

Jalankan ulang setiap kali katalog berubah, lalu build ulang React dan deploy.
Sitemap yang usang lebih merugikan daripada tidak ada: Google akan meminta URL
buku yang sudah dihapus, menerima 200 berisi index.html karena fallback SPA di
Nginx, lalu menandainya sebagai soft 404.

Hanya rute PUBLIK yang dimasukkan. /pinjaman, /favorit, /profil, dan /admin/*
dijaga PrivateRoute sehingga crawler hanya akan melihat halaman kosong.

Pemakaian:
    python python/scripts/buat_sitemap.py
    python python/scripts/buat_sitemap.py --basis https://perpuslibra.web.id
"""
import argparse
import os
from pathlib import Path
from xml.sax.saxutils import escape

import pymysql
import pymysql.cursors

BASIS_BAWAAN = 'https://perpuslibra.web.id'
KELUARAN = Path(__file__).resolve().parents[2] / 'react' / 'public' / 'sitemap.xml'


def ambil_buku():
    conn = pymysql.connect(
        host=os.environ.get('LIBRA_DB_HOST', 'localhost'),
        user=os.environ.get('LIBRA_DB_USER', 'root'),
        password=os.environ.get('LIBRA_DB_PASS', ''),
        database=os.environ.get('LIBRA_DB_NAME', 'libra_db'),
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
    )
    with conn, conn.cursor() as cur:
        cur.execute(
            """SELECT id, GREATEST(COALESCE(updated_at, created_at), created_at) AS diubah
               FROM buku ORDER BY id"""
        )
        return list(cur.fetchall())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--basis', default=BASIS_BAWAAN, help='URL dasar situs, tanpa garis miring akhir')
    arg = p.parse_args()
    basis = arg.basis.rstrip('/')

    buku = ambil_buku()

    baris = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    # Beranda mengalihkan ke /katalog, jadi /katalog yang diberi prioritas tertinggi.
    baris += [
        '  <url>',
        f'    <loc>{escape(basis)}/</loc>',
        '    <changefreq>weekly</changefreq>',
        '    <priority>0.8</priority>',
        '  </url>',
        '  <url>',
        f'    <loc>{escape(basis)}/katalog</loc>',
        '    <changefreq>daily</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>',
    ]

    for b in buku:
        baris.append('  <url>')
        baris.append(f'    <loc>{escape(basis)}/buku/{b["id"]}</loc>')
        if b['diubah']:
            baris.append(f'    <lastmod>{b["diubah"].strftime("%Y-%m-%d")}</lastmod>')
        baris.append('    <changefreq>monthly</changefreq>')
        baris.append('    <priority>0.6</priority>')
        baris.append('  </url>')

    baris.append('</urlset>')

    KELUARAN.parent.mkdir(parents=True, exist_ok=True)
    KELUARAN.write_text('\n'.join(baris) + '\n', encoding='utf8')

    print(f'sitemap ditulis : {KELUARAN}')
    print(f'jumlah URL      : {len(buku) + 2}  ({len(buku)} halaman buku + beranda + katalog)')
    print(f'basis           : {basis}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
