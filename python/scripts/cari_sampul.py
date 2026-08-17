"""
cari_sampul.py — carikan sampul untuk buku yang cover_url-nya masih kosong.

Tanpa argumen: hanya melapor.
  python cari_sampul.py
  python cari_sampul.py --terapkan
  python cari_sampul.py --terapkan --batas 20

Sumber, berurutan: Google Books lalu Open Library, keduanya dicari lewat
ISBN. Buku terbitan lokal (Pustaka Jaya, Kiblat, Emir, Erlangga) sering
tidak ada di kedua katalog itu, jadi sebagian buku memang tidak akan
ketemu — itu hasil yang wajar, bukan kegagalan skrip.

Sampul disimpan mengikuti pola yang sudah dipakai 262 berkas lama:
/uploads/covers/{judul-penulis}.webp
"""
import argparse
import io
import os
import re
import sys
import time
from pathlib import Path

import pymysql
import pymysql.cursors
import requests
from PIL import Image

TUJUAN = Path(os.environ.get(
    'LIBRA_COVER_DIR', r'D:\xampp\htdocs\libra\uploads\covers'))
URL_PUBLIK = '/uploads/covers/{nama}.webp'

DB = dict(
    host=os.environ.get('LIBRA_DB_HOST', 'localhost'),
    user=os.environ.get('LIBRA_DB_USER', 'root'),
    password=os.environ.get('LIBRA_DB_PASS', ''),
    database=os.environ.get('LIBRA_DB_NAME', 'libra_db'),
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
)

JEDA = 0.6           # detik antar permintaan, supaya tidak dibatasi server
LEBAR_MAKS = 500     # sampul lebih lebar dari ini tidak menambah apa pun di kartu
SESI = requests.Session()
SESI.headers['User-Agent'] = 'LIBRA-SMPN1Kemang/1.0 (proyek perpustakaan sekolah)'


def slug(teks: str) -> str:
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', teks.lower())).strip('-')


def nama_berkas(judul: str, penulis: str) -> str:
    return f"{slug(judul)}-{slug(penulis)}"[:120].strip('-')


def unduh(url: str):
    """
    (bytes, alasan). bytes None kalau gagal.

    Alasan dibedakan supaya "tidak ada di katalog" tidak tercampur dengan
    "dibatasi server" — keduanya terlihat sama dari luar, padahal yang satu
    berarti berhenti mencari dan yang lain berarti coba lagi nanti.
    """
    try:
        r = SESI.get(url, timeout=15)
    except requests.RequestException:
        return None, 'jaringan'

    if r.status_code == 429:
        return None, 'dibatasi'
    if r.status_code != 200 or not r.content:
        return None, 'tidak ada'
    if not r.headers.get('Content-Type', '').startswith('image/'):
        return None, 'bukan gambar'
    # Berkas di bawah 3 KB hampir pasti placeholder, bukan sampul asli.
    if len(r.content) < 3000:
        return None, 'placeholder'
    return r.content, 'ok'


def dari_openlibrary(isbn: str):
    """
    default=false penting: tanpa itu Open Library membalas gambar abu-abu
    1x1 dengan status 200, dan setiap buku akan terlihat "ketemu".
    """
    return unduh(
        f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false")


def dari_google(isbn: str, percobaan: int = 3):
    """
    Google Books dicoba belakangan karena batas lajunya ketat untuk
    permintaan tanpa kunci API. 429 ditunggu dengan jeda menaik, bukan
    dianggap 'buku tidak ada'.
    """
    tunggu = 2
    for _ in range(percobaan):
        try:
            r = SESI.get('https://www.googleapis.com/books/v1/volumes',
                         params={'q': f'isbn:{isbn}'}, timeout=15)
        except requests.RequestException:
            return None, 'jaringan'

        if r.status_code == 429:
            time.sleep(tunggu)
            tunggu *= 2
            continue
        if r.status_code != 200:
            return None, 'tidak ada'

        try:
            item = (r.json().get('items') or [None])[0]
        except (ValueError, IndexError):
            return None, 'tidak ada'
        if not item:
            return None, 'tidak ada'

        tautan = item.get('volumeInfo', {}).get('imageLinks') or {}
        for kunci in ('extraLarge', 'large', 'medium', 'small', 'thumbnail'):
            if tautan.get(kunci):
                # &edge=curl menambahkan lipatan palsu di gambar.
                url = (tautan[kunci].replace('&edge=curl', '')
                                    .replace('http://', 'https://'))
                return unduh(url)
        return None, 'tanpa gambar'

    return None, 'dibatasi'


def simpan_webp(isi: bytes, tujuan: Path) -> bool:
    try:
        gambar = Image.open(io.BytesIO(isi))
        gambar.load()
    except Exception:
        return False

    if gambar.mode not in ('RGB', 'L'):
        gambar = gambar.convert('RGB')
    if gambar.width > LEBAR_MAKS:
        tinggi = round(gambar.height * LEBAR_MAKS / gambar.width)
        gambar = gambar.resize((LEBAR_MAKS, tinggi), Image.LANCZOS)

    tujuan.parent.mkdir(parents=True, exist_ok=True)
    gambar.save(tujuan, 'WEBP', quality=82, method=6)
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--terapkan', action='store_true')
    p.add_argument('--batas', type=int, default=0, help='hentikan setelah N buku')
    p.add_argument('--tanpa-google', action='store_true',
                   help='Open Library saja — dipakai saat Google sedang membatasi')
    arg = p.parse_args()

    conn = pymysql.connect(**DB)
    with conn, conn.cursor() as cur:
        cur.execute("""SELECT id, judul, penulis, isbn
                         FROM buku
                        WHERE (cover_url IS NULL OR cover_url = '')
                          AND isbn IS NOT NULL AND isbn <> ''
                        ORDER BY id""")
        daftar = cur.fetchall()

        cur.execute("""SELECT COUNT(*) AS n FROM buku
                        WHERE (cover_url IS NULL OR cover_url = '')
                          AND (isbn IS NULL OR isbn = '')""")
        tanpa_isbn = cur.fetchone()['n']

        if arg.batas:
            daftar = daftar[:arg.batas]

        print(f"Buku tanpa sampul & punya ISBN : {len(daftar)}")
        if tanpa_isbn:
            print(f"Buku tanpa sampul & tanpa ISBN : {tanpa_isbn} (tidak bisa dicari)")
        if not arg.terapkan:
            print("\n(uji coba — tidak mengunduh apa pun. Tambahkan --terapkan.)")
            return
        print(f"Tujuan: {TUJUAN}\n")

        ketemu = {'openlibrary': 0, 'google': 0}
        gagal = {}
        for i, b in enumerate(daftar, 1):
            isbn = re.sub(r'[^0-9X]', '', (b['isbn'] or '').upper())

            # Open Library lebih dulu: batas lajunya longgar, sehingga
            # Google hanya dipakai untuk sisa yang benar-benar perlu.
            isi, alasan = dari_openlibrary(isbn)
            sumber = 'openlibrary'
            if isi is None and not arg.tanpa_google:
                isi, alasan = dari_google(isbn)
                sumber = 'google'

            if isi is None:
                gagal[alasan] = gagal.get(alasan, 0) + 1
                print(f"[{i:>3}/{len(daftar)}] -- {alasan:<12} {b['judul'][:50]}")
                time.sleep(JEDA)
                continue

            nama = nama_berkas(b['judul'], b['penulis'])
            if not simpan_webp(isi, TUJUAN / f"{nama}.webp"):
                gagal['gambar rusak'] = gagal.get('gambar rusak', 0) + 1
                print(f"[{i:>3}/{len(daftar)}] -- gambar rusak {b['judul'][:50]}")
                time.sleep(JEDA)
                continue

            cur.execute("UPDATE buku SET cover_url = %s WHERE id = %s",
                        (URL_PUBLIK.format(nama=nama), b['id']))
            conn.commit()
            ketemu[sumber] += 1
            print(f"[{i:>3}/{len(daftar)}] ok {sumber:<12} {b['judul'][:50]}")
            time.sleep(JEDA)

        total = sum(ketemu.values())
        print(f"\nKetemu {total} dari {len(daftar)} buku "
              f"(Open Library {ketemu['openlibrary']}, Google {ketemu['google']}).")
        if gagal:
            print("Yang tidak dapat sampul:")
            for alasan, n in sorted(gagal.items(), key=lambda x: -x[1]):
                print(f"  {alasan:<14} {n}")
            if gagal.get('dibatasi'):
                print("\n'dibatasi' berarti Google menolak sementara, bukan buku"
                      " tidak ada. Jalankan lagi nanti untuk sisa itu.")


if __name__ == '__main__':
    main()
