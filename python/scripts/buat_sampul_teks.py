"""
buat_sampul_teks.py — sampul tipografi untuk buku yang tidak dapat sampul asli.

Tanpa argumen: hanya melapor.
  python buat_sampul_teks.py
  python buat_sampul_teks.py --terapkan

Sebagian besar koleksi SMPN 1 Kemang terbitan lokal (Emir, Esensi, Kiblat,
Pustaka Jaya) tidak terdaftar di Google Books maupun Open Library, jadi
sampul aslinya memang tidak bisa dicari. Kotak abu-abu kosong di katalog
lebih buruk daripada sampul teks yang dirancang rapi.

Hasilnya disimpan terpisah di /uploads/covers/dibuat/ supaya mudah dikenali
dan ditimpa begitu foto sampul asli dari sekolah tersedia:

    SELECT * FROM buku WHERE cover_url LIKE '%/covers/dibuat/%';
"""
import argparse
import colorsys
import hashlib
import os
import re
import sys
from pathlib import Path

import pymysql
import pymysql.cursors
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chatbot.muat_env import muat_env  # noqa: E402

muat_env()

TUJUAN = Path(os.environ.get(
    'LIBRA_COVER_DIR', r'D:\xampp\htdocs\libra\uploads\covers')) / 'dibuat'
URL_PUBLIK = '/uploads/covers/dibuat/{nama}.webp'

DB = dict(
    host=os.environ.get('LIBRA_DB_HOST', 'localhost'),
    user=os.environ.get('LIBRA_DB_USER', 'root'),
    password=os.environ.get('LIBRA_DB_PASS', ''),
    database=os.environ.get('LIBRA_DB_NAME', 'libra_db'),
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
)

LEBAR, TINGGI = 500, 750   # perbandingan 2:3, sama dengan sampul buku
TEPI = 46

FONT_DIR = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts'
FONT_TEBAL = ['segoeuib.ttf', 'arialbd.ttf', 'calibrib.ttf', 'DejaVuSans-Bold.ttf']
FONT_BIASA = ['segoeui.ttf', 'arial.ttf', 'calibri.ttf', 'DejaVuSans.ttf']


def muat_font(pilihan, ukuran):
    for nama in pilihan:
        jalur = FONT_DIR / nama
        if jalur.exists():
            return ImageFont.truetype(str(jalur), ukuran)
    return ImageFont.load_default()


def slug(teks: str) -> str:
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', teks.lower())).strip('-')


def warna_kategori(kategori: str):
    """
    Warna diturunkan dari nama kategori, bukan diacak: buku dari kategori
    yang sama selalu mendapat warna yang sama, sehingga rak terlihat
    berkelompok dan sengaja, bukan tambal sulam.
    """
    angka = int(hashlib.md5(kategori.encode('utf-8')).hexdigest()[:8], 16)
    rona = (angka % 360) / 360
    gelap = tuple(round(c * 255) for c in colorsys.hls_to_rgb(rona, 0.20, 0.42))
    terang = tuple(round(c * 255) for c in colorsys.hls_to_rgb(rona, 0.62, 0.48))
    return gelap, terang


def bungkus(teks, font, lebar_maks, gambar):
    baris, sekarang = [], ''
    for kata in teks.split():
        coba = f"{sekarang} {kata}".strip()
        if gambar.textlength(coba, font=font) <= lebar_maks or not sekarang:
            sekarang = coba
        else:
            baris.append(sekarang)
            sekarang = kata
    if sekarang:
        baris.append(sekarang)
    return baris


def buat(judul: str, penulis: str, kategori: str) -> Image.Image:
    gelap, terang = warna_kategori(kategori)
    kanvas = Image.new('RGB', (LEBAR, TINGGI), gelap)
    d = ImageDraw.Draw(kanvas)
    lebar_teks = LEBAR - TEPI * 2

    # Pita kategori di atas — penanda cepat saat kartu dilihat sekilas.
    d.rectangle([0, 0, LEBAR, 8], fill=terang)
    f_kategori = muat_font(FONT_BIASA, 19)
    d.text((TEPI, 44), kategori.upper(), font=f_kategori, fill=terang)

    # Judul menyusut sampai muat maksimal enam baris, supaya judul panjang
    # tidak tumpah keluar kanvas.
    for ukuran in (52, 46, 40, 35, 30, 26, 22):
        f_judul = muat_font(FONT_TEBAL, ukuran)
        baris = bungkus(judul, f_judul, lebar_teks, d)
        if len(baris) <= 6:
            break

    tinggi_baris = ukuran + 10
    mulai = (TINGGI - len(baris) * tinggi_baris) // 2 - 40
    for i, b in enumerate(baris):
        d.text((TEPI, mulai + i * tinggi_baris), b, font=f_judul, fill=(245, 245, 245))

    # Penulis di bawah, dipisahkan garis tipis.
    f_penulis = muat_font(FONT_BIASA, 22)
    baris_penulis = bungkus(penulis, f_penulis, lebar_teks, d)[:2]
    dasar = TINGGI - TEPI - len(baris_penulis) * 30
    d.rectangle([TEPI, dasar - 26, TEPI + 60, dasar - 24], fill=terang)
    for i, b in enumerate(baris_penulis):
        d.text((TEPI, dasar + i * 30), b, font=f_penulis, fill=(215, 215, 215))

    return kanvas


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--terapkan', action='store_true')
    p.add_argument('--batas', type=int, default=0)
    arg = p.parse_args()

    conn = pymysql.connect(**DB)
    with conn, conn.cursor() as cur:
        cur.execute("""SELECT b.id, b.judul, b.penulis, k.nama AS kategori
                         FROM buku b
                         JOIN kategori k ON k.id = b.kategori_id
                        WHERE b.cover_url IS NULL OR b.cover_url = ''
                        ORDER BY b.id""")
        daftar = cur.fetchall()
        if arg.batas:
            daftar = daftar[:arg.batas]

        print(f"Buku tanpa sampul : {len(daftar)}")
        if not arg.terapkan:
            print("\n(uji coba — tidak menulis apa pun. Tambahkan --terapkan.)")
            return

        TUJUAN.mkdir(parents=True, exist_ok=True)
        print(f"Tujuan: {TUJUAN}\n")

        for i, b in enumerate(daftar, 1):
            nama = f"{slug(b['judul'])}-{slug(b['penulis'])}"[:120].strip('-')
            buat(b['judul'], b['penulis'], b['kategori']).save(
                TUJUAN / f"{nama}.webp", 'WEBP', quality=88, method=6)
            cur.execute("UPDATE buku SET cover_url = %s WHERE id = %s",
                        (URL_PUBLIK.format(nama=nama), b['id']))
            if i % 20 == 0 or i == len(daftar):
                conn.commit()
                print(f"  {i}/{len(daftar)}")
        conn.commit()
        print(f"\n{len(daftar)} sampul teks dibuat.")


if __name__ == '__main__':
    main()
