"""
cocokkan_cover_asli.py — Cocokkan berkas di folder "asli/" ke judul katalog.

Folder asli/ berisi sampul yang dikumpulkan manual dengan pola nama
"<Judul>, <Penulis>,.<ext>". Pola itu tidak dapat dipecah dengan memotong pada
koma pertama, karena sebagian judul sendiri mengandung koma
("Ayo, Mengukur Jarak", "Asam, Basa, dan Garam di Lingkungan Kita").

Karena itu pencocokan dilakukan atas SELURUH nama berkas terhadap gabungan
"judul penulis" tiap buku, memakai rasio kemiripan. Ambang sengaja tinggi:
sampul yang salah pasang lebih merugikan daripada sampul yang terlewat.

Mode:
  python cocokkan_cover_asli.py            -> hanya laporan, tidak menulis apa pun
  python cocokkan_cover_asli.py --terapkan -> konversi ke WebP dan timpa cover
"""
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from PIL import Image

AKAR = Path(__file__).resolve().parents[2]
SUMBER = AKAR / 'asli'
BOOKS = Path(__file__).parent / 'books_with_covers.json'
COVERS = Path(r'D:\xampp\htdocs\libra\uploads\covers')

TARGET_W = 460
WEBP_QUALITY = 82

# Di bawah ambang ini pasangan dianggap tidak meyakinkan dan dilaporkan untuk
# diperiksa manual, bukan dipasang diam-diam.
AMBANG = 0.82

# Berkas yang namanya terlalu ringkas atau salah ketik sehingga tidak terjangkau
# pencocokan otomatis. Dipetakan manual setelah diperiksa satu per satu.
PETA_MANUAL = {
    'pemain sepak bola berprestasi 1.jpg': 'Mempersiapkan Pemain Sepak Bola Berprestasi (1)',
    'pemain voli berprestasi.jpg':         'Mempersiapkan Pemain Voli Berprestasi',
    'penerapan kpk dan fpb dalam kehidupan sehari-hari.jpg': 'Penerapan KPK dan FPB',
    'seni mengajarkan matematika.jpg':     'Seni Mengajarkan Matematika Berbasis Kecerdasan Majemuk',
    'asam basa dan garam.jpg':             'Asam, Basa, dan Garam di Lingkungan Kita',
    'etiket pergaulan.jpg':                'Etiket Pergaulan (Sebuah Buku Pegangan)',
    'sains untun pemula 10.jpg':           'Sains untuk Pemula 10: Mari Bermain Molekul',
    'sains untuk pemula 3.jpg':            'Sains untuk Pemula 3: Mari Bermain Tumbukan dan Gesekan',
    'sains untun pemula 4.jpg':            'Sains untuk Pemula 4: Mari Bermain Pesawat Sederhana',
    'sains untun pemula 9.jpg':            'Sains untuk Pemula 9: Mari Bermain Elektromagnet',
}

# Bukan sampul tunggal: foto dua buku berdampingan dalam posisi terotasi.
# Kedua judulnya sudah punya sampul dari proses sebelumnya.
LEWATI = {'IMG_20260727_113803.jpg'}


def norm(t: str) -> str:
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', ' ', t.lower()).strip()


def bersihkan_nama(p: Path) -> str:
    """Buang ekstensi dan koma/spasi menggantung di akhir nama berkas."""
    return re.sub(r'[,\s]+$', '', p.stem)


def main():
    terapkan = '--terapkan' in sys.argv
    buku = json.loads(BOOKS.read_text(encoding='utf-8'))

    # Dua bentuk pembanding: "judul penulis" dan "judul" saja
    kandidat = []
    for b in buku:
        kandidat.append((norm(f"{b['judul']} {b['penulis']}"), b))
        kandidat.append((norm(b['judul']), b))

    berkas = sorted([p for p in SUMBER.iterdir()
                     if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp', '.jfif')])

    cocok, ragu, gagal = [], [], []
    terpakai = {}

    by_judul = {b['judul']: b for b in buku}

    for p in berkas:
        if p.name in LEWATI:
            continue

        if p.name in PETA_MANUAL:
            judul = PETA_MANUAL[p.name]
            assert judul in by_judul, f'judul manual tidak ada di katalog: {judul}'
            terpakai[judul] = (p, 1.0)
            cocok.append((p.name, judul, 1.0))
            continue

        target = norm(bersihkan_nama(p))
        terbaik, skor = None, 0.0
        for kunci, b in kandidat:
            r = SequenceMatcher(None, target, kunci).ratio()
            if r > skor:
                terbaik, skor = b, r

        if terbaik is None:
            gagal.append((p.name, 0.0))
        elif skor >= AMBANG:
            judul = terbaik['judul']
            # Dua berkas bisa mengarah ke judul yang sama; ambil skor tertinggi
            if judul in terpakai and terpakai[judul][1] >= skor:
                ragu.append((p.name, judul, skor, 'duplikat, kalah skor'))
            else:
                terpakai[judul] = (p, skor)
                cocok.append((p.name, judul, skor))
        else:
            gagal.append((p.name, skor, terbaik['judul']))

    print(f"Berkas di asli/      : {len(berkas)}")
    print(f"Cocok (>= {AMBANG})    : {len(terpakai)}")
    print(f"Duplikat dilewati    : {len(ragu)}")
    print(f"Tidak cocok          : {len(gagal)}")

    if gagal:
        print(f"\n=== TIDAK COCOK ({len(gagal)}) — perlu diperiksa manual ===")
        for g in sorted(gagal, key=lambda x: -x[1])[:40]:
            dugaan = f'  (terdekat: {g[2]})' if len(g) > 2 else ''
            print(f"  [{g[1]:.2f}] {g[0]}{dugaan}")

    if ragu:
        print(f"\n=== DUPLIKAT ({len(ragu)}) ===")
        for r in ragu:
            print(f"  [{r[2]:.2f}] {r[0]} -> {r[1]}  ({r[3]})")

    # Pasangan berskor pas-pasan paling rawan salah — tampilkan untuk ditinjau
    batas_tinjau = sorted(((j, s) for j, (_, s) in terpakai.items()), key=lambda x: x[1])[:15]
    print(f"\n=== 15 KECOCOKAN TERLEMAH (tinjau bila ragu) ===")
    for judul, skor in batas_tinjau:
        print(f"  [{skor:.3f}] {judul}")

    if not terapkan:
        print("\n(mode laporan — tidak ada berkas yang diubah)")
        print("Jalankan ulang dengan --terapkan untuk memasang sampul.")
        return

    # ── Terapkan ─────────────────────────────────────────────────────────
    by_title = {b['judul']: b for b in buku}
    diganti = 0
    for judul, (p, skor) in terpakai.items():
        b = by_title[judul]
        im = Image.open(p)
        im = im.convert('RGB')
        if im.width > TARGET_W:
            im = im.resize((TARGET_W, round(im.height * TARGET_W / im.width)), Image.LANCZOS)
        im.save(COVERS / b['cover_filename'], 'WEBP', quality=WEBP_QUALITY, method=6)
        b['cover_source'] = 'foto_asli_kurasi'
        b['sumber_berkas'] = p.name
        diganti += 1

    BOOKS.write_text(json.dumps(buku, ensure_ascii=False, indent=2), encoding='utf-8')

    from collections import Counter
    print(f"\n{diganti} sampul dipasang dari folder asli/")
    print("Sebaran sumber cover sekarang:")
    for k, v in Counter(b['cover_source'] for b in buku).most_common():
        print(f"  {k:<20} {v}")


if __name__ == '__main__':
    main()
