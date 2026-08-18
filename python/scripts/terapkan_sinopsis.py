"""
terapkan_sinopsis.py — pasang sinopsis tulisan tangan ke libra_db.

  python terapkan_sinopsis.py
  python terapkan_sinopsis.py --terapkan

Sumbernya sinopsis_manual.py, bukan panggilan API. Tidak ada kuota yang
terpakai dan hasilnya tidak berubah-ubah tiap kali dijalankan.

Hanya menyentuh buku yang sinopsisnya masih kosong. Sinopsis yang sudah
ditulis petugas tidak pernah ditimpa.
"""
import argparse
import os
import sys
from pathlib import Path

import pymysql
import pymysql.cursors

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sinopsis_manual import SINOPSIS  # noqa: E402

DB = dict(
    host=os.environ.get('LIBRA_DB_HOST', 'localhost'),
    user=os.environ.get('LIBRA_DB_USER', 'root'),
    password=os.environ.get('LIBRA_DB_PASS', ''),
    database=os.environ.get('LIBRA_DB_NAME', 'libra_db'),
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--terapkan', action='store_true')
    arg = p.parse_args()

    conn = pymysql.connect(**DB)
    with conn, conn.cursor() as cur:
        cur.execute("""SELECT id, judul, sinopsis FROM buku
                        WHERE id IN %s""", (tuple(SINOPSIS),))
        ada = {r['id']: r for r in cur.fetchall()}

    hilang = [i for i in SINOPSIS if i not in ada]
    terisi = [i for i, r in ada.items() if (r['sinopsis'] or '').strip()]
    siap = [i for i in SINOPSIS if i in ada and i not in terisi]

    print(f"Sinopsis tersedia : {len(SINOPSIS)}")
    print(f"Akan dipasang     : {len(siap)}")
    if terisi:
        print(f"Dilewati, sudah ada sinopsisnya: {len(terisi)}")
    if hilang:
        print(f"Id tidak ditemukan di basis data: {hilang}")

    belum_lengkap = sum(1 for i in siap if 'belum tersedia' in SINOPSIS[i])
    print(f"Di antaranya menyatakan belum lengkap: {belum_lengkap}"
          " (karya yang alurnya tidak diketahui, sengaja tidak dikarang)")

    if not arg.terapkan:
        print("\n(uji coba — tidak menulis apa pun. Tambahkan --terapkan.)")
        return

    conn = pymysql.connect(**DB)
    with conn, conn.cursor() as cur:
        for i in siap:
            cur.execute(
                "UPDATE buku SET sinopsis = %s, sinopsis_sumber = 'ai' WHERE id = %s",
                (SINOPSIS[i], i))
        conn.commit()
    print(f"\n{len(siap)} sinopsis dipasang.")


if __name__ == '__main__':
    main()
