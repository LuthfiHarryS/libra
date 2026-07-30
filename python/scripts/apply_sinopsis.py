"""
apply_sinopsis.py — Terapkan sinopsis tulisan tangan + koreksi kategori.

Menulis ke DUA tempat supaya tidak hilang:
  1. tabel buku di MySQL (yang dipakai aplikasi sekarang)
  2. books_with_covers.json (sumber seed_notes_books.php, agar seeding ulang
     tidak mengembalikan sinopsis template)

Koreksi kategori diperlukan karena tebak_kategori() di fetch_notes_covers.py
mencocokkan kata kunci sebagai substring, sehingga "akar" cocok di dalam
"bakar" dan "islam" cocok di nama penulis "Islami". Aturan itu cukup baik untuk
mayoritas judul, tapi kasus di bawah harus ditimpa manual.
"""
import json
import sys
from pathlib import Path

import pymysql

sys.path.insert(0, str(Path(__file__).parent))
from sinopsis_data import SINOPSIS            # noqa: E402

BOOKS_PATH = Path(__file__).parent / "books_with_covers.json"

# judul -> kategori yang benar
KOREKSI_KATEGORI = {
    # "akar" cocok sebagai substring di "bakar"
    "Tanaman Penghasil Bahan Bakar": "Sains",
    # "islam" cocok di nama penulis "Kania Islami Dewi"
    "Seni Mengajarkan Matematika Berbasis Kecerdasan Majemuk": "Matematika",
    # aturan "the " (Bahasa Inggris) diperiksa sebelum "bleach" (Komik)
    "Bleach 10: Tattoo on the Sky": "Komik",
    # novel, bukan buku biologi — "mata" dan "pohon" ada di judul
    "Air Mata Sang Pohon Purba": "Fiksi",
    # "manusia" ada di judul, tapi isinya filsafat
    "Pandangan Hidup Manusia": "Non-Fiksi",
    "Etiket Pergaulan (Sebuah Buku Pegangan)": "IPS",
    # cerita berbahasa Inggris, bukan materi IPS
    "Baby Squirrel Learnt A Lesson and Other Stories": "Bahasa Inggris",
    # keduanya materi pengukuran di pelajaran matematika
    "Mengenal Waktu dan Pengukuran": "Matematika",
    "Berat, Waktu dan Pengukuran": "Matematika",
    # novel terjemahan, bukan buku pelajaran Bahasa Inggris
    "Lord of the Shadows: Penguasa Kegelapan": "Fiksi",
    # sastra Sunda
    "Nu Ngageugeuh Legok Kiara": "Fiksi",
    # roman sejarah Mataram
    "Amangkurat: Mendung Memekat di Langit Mataram": "Sejarah",
}


def db():
    return pymysql.connect(host='localhost', user='root', password='',
                           database='libra_db', charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)


def main():
    conn = db()
    books = json.loads(BOOKS_PATH.read_text(encoding="utf-8"))
    by_title = {b["judul"]: b for b in books}

    updated_sin = 0
    updated_kat = 0
    tidak_ketemu = []

    with conn.cursor() as cur:
        # Peta kategori nama -> id
        cur.execute("SELECT id, nama FROM kategori")
        kat_map = {r["nama"]: r["id"] for r in cur.fetchall()}

        # ── Koreksi kategori dulu, supaya hitungan akhir mencerminkan hasilnya
        for judul, kategori in KOREKSI_KATEGORI.items():
            if kategori not in kat_map:
                cur.execute("INSERT INTO kategori (nama) VALUES (%s)", (kategori,))
                conn.commit()
                cur.execute("SELECT id FROM kategori WHERE nama=%s", (kategori,))
                kat_map[kategori] = cur.fetchone()["id"]

            # rowcount tidak bisa dipakai untuk mendeteksi judul yang tidak ada:
            # MySQL mengembalikan 0 juga ketika nilainya memang sudah sama
            # (skrip ini idempoten). Cek keberadaan barisnya secara terpisah.
            cur.execute("SELECT id FROM buku WHERE judul=%s", (judul,))
            if cur.fetchone() is None:
                tidak_ketemu.append(f"[kategori] judul tidak ada di tabel: {judul}")
                continue

            cur.execute("UPDATE buku SET kategori_id=%s WHERE judul=%s",
                        (kat_map[kategori], judul))
            updated_kat += 1

            if judul in by_title:
                by_title[judul]["kategori"] = kategori

        # ── Sinopsis
        for judul, sinopsis in SINOPSIS.items():
            cur.execute("SELECT id FROM buku WHERE judul=%s", (judul,))
            if cur.fetchone() is None:
                tidak_ketemu.append(f"[sinopsis] judul tidak ada di tabel: {judul}")
                continue

            cur.execute("UPDATE buku SET sinopsis=%s WHERE judul=%s", (sinopsis, judul))
            updated_sin += 1

            if judul in by_title:
                by_title[judul]["sinopsis"] = sinopsis
            else:
                tidak_ketemu.append(f"[json] tidak ada di books_with_covers: {judul}")

    conn.commit()
    BOOKS_PATH.write_text(json.dumps(books, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    print(f"Sinopsis diperbarui : {updated_sin}")
    print(f"Kategori dikoreksi  : {updated_kat}")
    if tidak_ketemu:
        print(f"\nTIDAK COCOK ({len(tidak_ketemu)}):")
        for t in tidak_ketemu:
            print("  " + t)

    # ── Verifikasi
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total,
                   SUM(sinopsis LIKE '"%jenjang SMP%') AS sisa_template,
                   SUM(sinopsis IS NULL OR sinopsis='') AS kosong,
                   ROUND(AVG(CHAR_LENGTH(sinopsis))) AS rata2
            FROM buku
        """)
        r = cur.fetchone()
        print(f"\n=== VERIFIKASI ===")
        print(f"  Total buku          : {r['total']}")
        print(f"  Sisa sinopsis template: {r['sisa_template']}")
        print(f"  Sinopsis kosong     : {r['kosong']}")
        print(f"  Rata-rata panjang   : {r['rata2']} karakter")

        cur.execute("""
            SELECT k.nama, COUNT(b.id) AS jml FROM kategori k
            JOIN buku b ON b.kategori_id=k.id
            GROUP BY k.nama ORDER BY jml DESC
        """)
        print("\n  Sebaran kategori:")
        for row in cur.fetchall():
            print(f"    {row['nama']:<18} {row['jml']}")

    conn.close()


if __name__ == "__main__":
    main()
