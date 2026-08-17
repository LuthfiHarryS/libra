"""
impor_csv_perpustakaan.py — masukkan data buku dari CSV petugas ke libra_db.

Tanpa argumen: hanya melapor, tidak menulis apa pun.
  python impor_csv_perpustakaan.py
  python impor_csv_perpustakaan.py --terapkan

CSV berasal dari pencatatan manual petugas, jadi diperlakukan sebagai data
kotor: judul ganda, ISBN tidak valid, tahun terbit berisi "1", dan stok
ribuan untuk buku pelajaran. Semuanya dilaporkan, tidak ada yang diperbaiki
diam-diam.
"""
import argparse
import csv
import os
import re
import sys
from pathlib import Path

import pymysql
import pymysql.cursors

AKAR = Path(__file__).resolve().parents[2]
CSV_BAWAAN = AKAR / 'data_sekolah' / 'Database_Perpustakaan.csv'

DB = dict(
    host=os.environ.get('LIBRA_DB_HOST', 'localhost'),
    user=os.environ.get('LIBRA_DB_USER', 'root'),
    password=os.environ.get('LIBRA_DB_PASS', ''),
    database=os.environ.get('LIBRA_DB_NAME', 'libra_db'),
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
)

# Klasifikasi DDC tiga digit -> nama kategori yang sudah ada di libra_db.
# Tidak ada kategori baru yang dibuat: menambah kategori berarti mengubah
# yang sudah dipakai 237 buku lama dan panel rekomendasi.
DDC = {
    '004': 'Teknologi',
    '030': 'Non-Fiksi',
    '150': 'Non-Fiksi',
    '297': 'Agama',
    '330': 'IPS',
    '350': 'IPS',
    '371': 'Non-Fiksi',
    '390': 'IPS',
    '410': 'Bahasa Indonesia',
    '413': 'Bahasa Indonesia',
    '420': 'Bahasa Inggris',
    '499': 'Bahasa Indonesia',
    '500': 'Sains',
    '510': 'Matematika',
    '800': 'Bahasa Indonesia',
    '810': 'Bahasa Indonesia',
    '813': 'Fiksi',
    '899': 'Fiksi',
    '900': 'Sejarah',
    '930': 'Sejarah',
    '959': 'Sejarah',
}

# Kode 561 dipakai petugas untuk semua buku pelajaran, apa pun mata
# pelajarannya — 561 sebenarnya paleobotani. Karena kodenya tidak bisa
# dipercaya, kategorinya ditebak dari judul.
PELAJARAN = [
    ('INGGRIS', 'Bahasa Inggris'),
    ('PJOK', 'Olahraga'),
    ('PRAKARYA', 'Teknologi'),
    ('BASA SUNDA', 'Bahasa Indonesia'),
    ('BAHASA INDONESIA', 'Bahasa Indonesia'),
    ('ILMU PENGETAHUAN SOSIAL', 'IPS'),
    ('MATEMATIKA', 'Matematika'),
]
KATEGORI_CADANGAN = 'Non-Fiksi'


def rapikan(teks: str) -> str:
    """Rapatkan spasi ganda dan buang spasi tepi."""
    return re.sub(r'\s+', ' ', (teks or '')).strip()


def kunci_judul(judul: str) -> str:
    """Bentuk judul untuk pembandingan: huruf dan angka saja, huruf besar."""
    return re.sub(r'[^A-Z0-9]', '', rapikan(judul).upper())


def bersihkan_isbn(isbn: str) -> str:
    """
    Angka saja. ISBN yang panjangnya bukan 10 atau 13 dikembalikan apa
    adanya supaya tetap terlihat di laporan, bukan dibuang diam-diam.
    """
    return re.sub(r'[^0-9Xx]', '', isbn or '').upper()


# Gelar dan singkatan yang bukan bagian nama. Tanpa ini, "Risnawati, M. Pd"
# dan "Risnawati" bisa dianggap dua orang berbeda.
_BUKAN_NAMA = {
    'PROF', 'DRS', 'DRA', 'DR', 'IR', 'HJ', 'KH', 'DKK', 'DAN',
    'SPD', 'MPD', 'SPSI', 'SSOS', 'MSI', 'MSC', 'MHUM', 'SAG', 'LC',
    'TIM', 'CV', 'PT',
}


def token_penulis(penulis: str) -> set:
    """
    Kata-kata yang benar-benar menandai identitas penulis.

    Dipakai untuk mencocokkan "A. FUADI" dengan "Ahmad Fuadi": keduanya
    berbagi FUADI. Kata pendek dibuang karena inisial dan kata sambung
    terlalu sering bertabrakan.
    """
    kata = re.findall(r'[A-Z]+', rapikan(penulis).upper())
    return {k for k in kata if len(k) >= 4 and k not in _BUKAN_NAMA}


def penulis_sama(a: str, b: str) -> bool:
    ta, tb = token_penulis(a), token_penulis(b)
    return bool(ta and tb and (ta & tb))


def kategori_untuk(klasifikasi: str, judul: str) -> str:
    kode = rapikan(klasifikasi)
    if kode.startswith('561'):
        atas = judul.upper()
        for kata, nama in PELAJARAN:
            if kata in atas:
                return nama
        return KATEGORI_CADANGAN
    return DDC.get(kode[:3], KATEGORI_CADANGAN)


def baca_csv(jalur: Path):
    baris = []
    with open(jalur, encoding='utf-8-sig', newline='') as f:
        for i, r in enumerate(csv.DictReader(f), start=2):  # baris 1 = header
            judul = rapikan(r.get('Judul'))
            if not judul:
                continue

            sub = rapikan(r.get('Sub Judul'))
            penulis = rapikan(r.get('Penulis')) or 'Tidak diketahui'

            try:
                stok = int(rapikan(r.get('Stok')) or 0)
            except ValueError:
                stok = 0

            baris.append({
                'baris': i,
                'judul': f"{judul}: {sub}" if sub else judul,
                'judul_asli': judul,
                'penulis': penulis,
                'isbn': bersihkan_isbn(r.get('ISBN')),
                'stok': max(stok, 0),
                'kategori': kategori_untuk(r.get('Klasifikasi Buku'), judul),
                'klasifikasi': rapikan(r.get('Klasifikasi Buku')),
                'tahun': rapikan(r.get('Tahun Terbit')),
                'penerbit': rapikan(r.get('Penerbit')),
            })
    return baris


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--csv', default=str(CSV_BAWAAN))
    p.add_argument('--terapkan', action='store_true',
                   help='benar-benar menulis ke basis data')
    arg = p.parse_args()

    jalur = Path(arg.csv)
    if not jalur.exists():
        sys.exit(f"CSV tidak ditemukan: {jalur}")

    baris = baca_csv(jalur)
    print(f"Baris terbaca : {len(baris)}")

    # ── Ganda di dalam CSV ────────────────────────────────────────────────
    per_isbn, per_judul = {}, {}
    ganda_isbn, ganda_judul = [], []
    for b in baris:
        if b['isbn']:
            if b['isbn'] in per_isbn:
                ganda_isbn.append((per_isbn[b['isbn']], b))
            else:
                per_isbn[b['isbn']] = b

        k = kunci_judul(b['judul']) + '|' + kunci_judul(b['penulis'])
        if k in per_judul:
            ganda_judul.append((per_judul[k], b))
        else:
            per_judul[k] = b

    # ── Bandingkan dengan isi basis data ─────────────────────────────────
    conn = pymysql.connect(**DB)
    with conn, conn.cursor() as cur:
        cur.execute("SELECT id, nama FROM kategori")
        id_kategori = {r['nama']: r['id'] for r in cur.fetchall()}

        cur.execute("SELECT id, judul, penulis, isbn FROM buku")
        lama = cur.fetchall()
        isbn_lama = {bersihkan_isbn(r['isbn']): r for r in lama if r['isbn']}
        # Judul saja terlalu kasar sebagai penanda buku yang sama: CSV ini
        # memuat dua "PANDUAN PENDIDIKAN ANTIKORUPSI UNTUK SISWA SMP/MTS"
        # dengan penulis dan ISBN berbeda — dua buku, bukan satu.
        # Judul saja terlalu longgar, judul+penulis persis terlalu ketat.
        # Yang dipakai: judul sama DAN penulis berbagi satu kata nama.
        judul_lama = {}
        for r in lama:
            judul_lama.setdefault(kunci_judul(r['judul']), []).append(r)

        baru, sudah_ada, mirip = [], [], []
        terpakai_isbn = set()
        terpakai_judul = {}

        for b in baris:
            kj = kunci_judul(b['judul'])

            kembar_db = next((r for r in judul_lama.get(kj, [])
                              if penulis_sama(r['penulis'], b['penulis'])), None)
            kembar_csv = next((x for x in terpakai_judul.get(kj, [])
                               if penulis_sama(x['penulis'], b['penulis'])), None)

            if b['isbn'] and b['isbn'] in isbn_lama:
                sudah_ada.append((b, isbn_lama[b['isbn']], 'ISBN sama dengan DB'))
            elif kembar_db:
                sudah_ada.append((b, kembar_db, 'judul & penulis sama dengan DB'))
            elif b['isbn'] and b['isbn'] in terpakai_isbn:
                sudah_ada.append((b, None, 'ISBN ganda di CSV'))
            elif kembar_csv:
                sudah_ada.append((b, kembar_csv, 'judul & penulis ganda di CSV'))
            else:
                # Judul sama tetapi tidak satu pun kata nama penulis bertemu:
                # kemungkinan besar buku berbeda, jadi tetap dimasukkan dan
                # ditandai supaya petugas memeriksanya sendiri.
                serupa = judul_lama.get(kj) or terpakai_judul.get(kj)
                if serupa:
                    mirip.append((b, serupa[0], 'judul sama, penulis beda'))
                baru.append(b)
                if b['isbn']:
                    terpakai_isbn.add(b['isbn'])
                terpakai_judul.setdefault(kj, []).append(b)

        # ── Laporan ───────────────────────────────────────────────────────
        print(f"Dilewati (duplikat)    : {len(sudah_ada)}")
        print(f"Akan ditambahkan       : {len(baru)}")

        if ganda_isbn:
            print(f"\nISBN ganda di dalam CSV ({len(ganda_isbn)}):")
            for a, b in ganda_isbn:
                print(f"  baris {a['baris']} & {b['baris']}: {b['isbn']} — {b['judul'][:55]}")

        if ganda_judul:
            print(f"\nJudul+penulis ganda di dalam CSV ({len(ganda_judul)}):")
            for a, b in ganda_judul:
                print(f"  baris {a['baris']} & {b['baris']}: {b['judul'][:60]}")

        if sudah_ada:
            print(f"\nDilewati karena duplikat ({len(sudah_ada)}):")
            for b, r, sebab in sudah_ada:
                print(f"  baris {b['baris']:>3} [{sebab}] {b['judul'][:55]}")

        if mirip:
            print(f"\nTETAP DITAMBAHKAN tetapi perlu diperiksa petugas ({len(mirip)}):")
            for b, r, sebab in mirip:
                print(f"  baris {b['baris']:>3} [{sebab}] {b['judul'][:50]}")
                print(f"        CSV : {b['penulis'][:60]}")
                print(f"        DB  : {r['penulis'][:60]}")

        aneh = [b for b in baris if not b['tahun'].isdigit() or len(b['tahun']) != 4]
        if aneh:
            print(f"\nTahun terbit tidak masuk akal ({len(aneh)}) — kolom ini tidak"
                  f" disimpan, jadi tidak menghalangi impor:")
            for b in aneh:
                print(f"  baris {b['baris']:>3} tahun='{b['tahun']}' — {b['judul'][:50]}")

        isbn_aneh = [b for b in baris if b['isbn'] and len(b['isbn']) not in (10, 13)]
        if isbn_aneh:
            print(f"\nISBN panjangnya bukan 10/13 ({len(isbn_aneh)}) — tetap disimpan:")
            for b in isbn_aneh:
                print(f"  baris {b['baris']:>3} '{b['isbn']}' — {b['judul'][:50]}")

        sebaran = {}
        for b in baru:
            sebaran[b['kategori']] = sebaran.get(b['kategori'], 0) + 1
        print("\nSebaran kategori buku baru:")
        for nama, n in sorted(sebaran.items(), key=lambda x: -x[1]):
            print(f"  {nama:<18} {n}")

        print("\nKolom CSV yang TIDAK tertampung tabel buku:")
        print("  Penerbit, Tahun Terbit, Lokasi Buku, Keadaan Buku,")
        print("  Kode Awal Eksemplar, Petugas Input, dan seluruh kolom penerimaan.")

        if not arg.terapkan:
            print("\n(uji coba — tidak ada yang ditulis. Tambahkan --terapkan.)")
            return

        for b in baru:
            cur.execute(
                """INSERT INTO buku (kategori_id, judul, penulis, isbn,
                                     stok_total, stok_tersedia)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (id_kategori.get(b['kategori'], id_kategori[KATEGORI_CADANGAN]),
                 b['judul'][:255], b['penulis'][:255], b['isbn'][:20] or None,
                 b['stok'], b['stok']),
            )
        conn.commit()
        print(f"\n{len(baru)} buku ditambahkan.")


if __name__ == '__main__':
    main()
