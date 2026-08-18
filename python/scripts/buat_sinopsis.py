"""
buat_sinopsis.py — isi sinopsis kosong dengan bantuan Gemini.

Tanpa argumen: hanya melapor.
  python buat_sinopsis.py
  python buat_sinopsis.py --terapkan
  python buat_sinopsis.py --terapkan --batas 10

116 buku hasil impor dari catatan petugas tidak punya sinopsis, sehingga
chatbot selalu menjawab "datanya belum tersedia" untuk buku-buku itu.

Yang perlu disadari: teks yang dihasilkan berasal dari model bahasa, bukan
dari petugas perpustakaan. Karena itu:

  - Model diminta menjawab persis "TIDAK TAHU" bila tidak benar-benar
    mengenali bukunya. Buku yang dijawab begitu dibiarkan kosong, bukan
    diisi karangan.
  - Untuk buku pelajaran dan referensi, penjelasan berdasarkan judul dan
    mata pelajarannya diperbolehkan — itu bukan karangan, melainkan
    keterangan yang memang terbaca dari judulnya.
  - Setiap hasil ditandai pada kolom sinopsis_sumber = 'ai', sehingga
    sewaktu-waktu dapat ditinjau atau dihapus:

      SELECT judul FROM buku WHERE sinopsis_sumber = 'ai';
      UPDATE buku SET sinopsis = NULL, sinopsis_sumber = NULL
       WHERE sinopsis_sumber = 'ai';
"""
import argparse
import os
import sys
import time
from pathlib import Path

import pymysql
import pymysql.cursors

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chatbot.muat_env import muat_env  # noqa: E402

muat_env()

from chatbot import gemini  # noqa: E402

DB = dict(
    host=os.environ.get('LIBRA_DB_HOST', 'localhost'),
    user=os.environ.get('LIBRA_DB_USER', 'root'),
    password=os.environ.get('LIBRA_DB_PASS', ''),
    database=os.environ.get('LIBRA_DB_NAME', 'libra_db'),
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
)

JEDA = 1.2
TANDA_TIDAK_TAHU = 'TIDAK TAHU'

PERINTAH = """Kamu pustakawan yang menulis sinopsis singkat untuk katalog
perpustakaan SMP.

Tulis 2-3 kalimat tentang buku berikut, dalam Bahasa Indonesia yang mudah
dipahami siswa SMP.

Aturan:
- Kalau buku ini karya fiksi atau karya tertentu yang TIDAK benar-benar kamu
  kenali, jawab persis: TIDAK TAHU
- Kalau ini buku pelajaran, kamus, atau buku referensi yang isinya jelas dari
  judul dan mata pelajarannya, jelaskan isinya secara umum. Itu diperbolehkan.
- Jangan mengarang nama tokoh, alur cerita, atau penghargaan.
- Jangan menulis pembuka seperti "Buku ini" berulang kali, langsung saja.
- Jangan memakai format markdown.

Judul    : {judul}
Penulis  : {penulis}
Kategori : {kategori}"""


def siapkan_kolom(cur):
    """Tambahkan sinopsis_sumber bila belum ada. Aman dijalankan berulang."""
    cur.execute("""SELECT COUNT(*) AS ada
                     FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'buku'
                      AND COLUMN_NAME = 'sinopsis_sumber'""")
    if cur.fetchone()['ada']:
        return False
    cur.execute("ALTER TABLE buku ADD COLUMN sinopsis_sumber VARCHAR(10) NULL")
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--terapkan', action='store_true')
    p.add_argument('--batas', type=int, default=0)
    arg = p.parse_args()

    if not gemini.tersedia():
        sys.exit("GEMINI_API_KEY belum diisi di .env")

    conn = pymysql.connect(**DB)
    with conn, conn.cursor() as cur:
        cur.execute("""SELECT b.id, b.judul, b.penulis, k.nama AS kategori
                         FROM buku b
                         JOIN kategori k ON k.id = b.kategori_id
                        WHERE b.sinopsis IS NULL OR b.sinopsis = ''
                        ORDER BY b.id""")
        daftar = cur.fetchall()
        if arg.batas:
            daftar = daftar[:arg.batas]

        print(f"Buku tanpa sinopsis : {len(daftar)}")
        if not arg.terapkan:
            print("\n(uji coba — tidak menulis apa pun. Tambahkan --terapkan.)")
            return

        if siapkan_kolom(cur):
            conn.commit()
            print("Kolom sinopsis_sumber ditambahkan.")
        print()

        terisi = tidak_tahu = gagal = 0
        for i, b in enumerate(daftar, 1):
            teks = gemini.teks_bebas(PERINTAH.format(**b))
            time.sleep(JEDA)

            if not teks:
                gagal += 1
                print(f"[{i:>3}/{len(daftar)}] -- gagal      {b['judul'][:48]}")
                continue

            bersih = teks.strip()
            if TANDA_TIDAK_TAHU in bersih.upper()[:40]:
                tidak_tahu += 1
                print(f"[{i:>3}/{len(daftar)}] -- tidak tahu {b['judul'][:48]}")
                continue

            cur.execute(
                "UPDATE buku SET sinopsis = %s, sinopsis_sumber = 'ai' WHERE id = %s",
                (bersih, b['id']))
            conn.commit()
            terisi += 1
            print(f"[{i:>3}/{len(daftar)}] ok           {b['judul'][:48]}")

        print(f"\nTerisi {terisi}, dijawab tidak tahu {tidak_tahu}, gagal {gagal},"
              f" dari {len(daftar)} buku.")
        if tidak_tahu:
            print("Yang dijawab 'tidak tahu' sengaja dibiarkan kosong —"
                  " menunggu sinopsis dari petugas.")


if __name__ == '__main__':
    main()
