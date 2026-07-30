"""
parse_notes.py — Ubah 6 file notes_*.txt (inventaris fisik perpustakaan SMPN 1 Kemang)
menjadi dataset buku ternormalisasi.

Format sumber:
  * notes_*205405/205409/205414/205419/205424 : "Judul, Penulis, Stok"
  * notes_*205401 (daftar matematika)         : format bebas tanpa koma -> dikoreksi manual
    lewat tabel MANUAL_MATH di bawah.

Output: python/scripts/books_from_notes.json
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = Path(__file__).parent / "books_from_notes.json"

# File notes berformat "Judul, Penulis, Stok"
CSV_NOTES = [
    "notes_20260727205405.txt",
    "notes_20260727205409.txt",
    "notes_20260727205414.txt",
    "notes_20260727205419.txt",
    "notes_20260727205424.txt",
]
# File notes matematika — format tidak konsisten (judul/penulis tertukar, koma hilang)
MATH_NOTE = "notes_20260727205401.txt"

# Judul yang MENGANDUNG koma — aturan "koma pertama = batas judul" tidak berlaku.
# Nilai = jumlah koma yang termasuk bagian judul.
TITLE_HAS_COMMA = {
    "Ayo, Mengukur Jarak": 1,
    "Nabi Ilyasa a.s, Murid Nabi Ilyas a.s": 1,
    "Stella, Love Is Not Blind": 1,
    "Asam, Basa, dan Garam di Lingkungan Kita": 2,
    "Berat, Waktu dan Pengukuran": 1,
    "Berpikir dengan IQ, EQ, dan SQ": 2,
    "Memahami Unsur, Senyawa, dan Campuran": 2,
}

# notes_...205401 direkonstruksi manual: (judul, penulis, stok)
MANUAL_MATH = [
    ("Penerapan KPK dan FPB", "D. Astuti", 4),
    ("Belajar Mudah Jarimatika", "Dra. Dionisia Indriati", 1),
    ("Penjumlahan dan Pengurangan", "Hj. Sri Kartini, S.Pd.", 4),
    ("Sistem Persamaan Linear Dua Variabel", "Deni Evilina", 2),
    ("Mengenal Pangkat Tak Sebenarnya", "Deni Evilina", 4),
    ("Asyiknya Belajar Bangun Datar dan Bangun Ruang", "Deni Evilina", 1),
    ("Membuat Jaring-Jaring Bangun Ruang", "Deni Evilina", 2),
    ("Persamaan dan Pertidaksamaan Linear Satu Variabel", "Tidak Tertera", 4),
    ("Serba-Serbi Bilangan", "Retno Rianti", 4),
    ("Siapa Bilang Matematika Sulit 3", "Dra. Siswanto", 1),
    ("Ayo Mengenal Diagram", "Tidak Tertera", 1),
    ("Belajar Konsep Kesebangunan", "Tidak Tertera", 1),
    ("Penerapan Pengolahan Data Siswa", "Tri Ari Cahyono, S.Kom.", 4),
    ("Mengenal Persen dan Permil", "Bunga C. M.", 4),
    ("Pangkat dan Akar Pangkat", "D. Astuti", 4),
    ("Menggambar dengan Jangka", "Hery Widodo", 4),
    ("Kupas Tuntas Matematika", "Yuli R.", 1),
    ("Sudut dan Luas Segi Banyak", "Tri Yulianto", 4),
    ("Mengenal Bangun dan Belajar Pecahan", "PT Gading Tri Prima", 1),
    ("Mengenal Waktu dan Pengukuran", "Hj. Sri Kartini, S.Pd.", 4),
    ("Mengenal Garis-Garis pada Segitiga", "Rani Mustikasari", 3),
    ("Seluk-Beluk Lingkaran", "D. Astuti, A.Md.", 2),
]

# Baris yang rusak di sumber — diperbaiki eksplisit, bukan ditebak parser.
#   "...Namiek. S, 2l3"      -> stok salah ketik; diambil 2 (nilai terkecil yang masuk akal)
#   "ikatan kimia, ... 2"    -> koma sebelum stok hilang
LINE_FIXES = {
    "Belajar Karate Secara Sistematis, Namiek. S, 2l3":
        "Belajar Karate Secara Sistematis, Namiek S., 2",
    "ikatan kimia, muhammad rahman 2":
        "Ikatan Kimia, Muhammad Rahman, 2",
}

# Koreksi ejaan penulis yang berbeda antar-file untuk buku yang sama
AUTHOR_FIXES = {
    "b.c. tyas": "D.C. Tyas",
    "retno riani": "Retno Rianti",
    "reino rianyu": "Retno Rianti",
    "rofiata pohan": "Renata Pohan",
}


def norm_key(title: str) -> str:
    """Kunci dedup: lowercase, tanpa diakritik/tanda baca, spasi tunggal."""
    t = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-z0-9]+", " ", t.lower())
    return t.strip()


def parse_csv_line(line: str):
    """'Judul, Penulis, Stok' -> (judul, penulis, stok). None kalau tidak bisa diurai."""
    line = LINE_FIXES.get(line.strip(), line).strip().rstrip(",")
    if not line:
        return None

    m = re.search(r",\s*(\d+)\s*$", line)
    if not m:
        return None
    stok = int(m.group(1))
    body = line[: m.start()].strip()

    parts = [p.strip() for p in body.split(",")]
    # Judul default = segmen pertama; sisanya penulis (penulis sering mengandung koma).
    n_title_parts = 1
    for judul_khusus, extra in TITLE_HAS_COMMA.items():
        if body.startswith(judul_khusus):
            n_title_parts = 1 + extra
            break

    judul = ", ".join(parts[:n_title_parts]).strip()
    penulis = ", ".join(parts[n_title_parts:]).strip() or "Tidak Tertera"
    if not judul:
        return None
    return judul, penulis, stok


def tidy_author(penulis: str) -> str:
    return AUTHOR_FIXES.get(penulis.lower().strip(), penulis.strip())


def main():
    records = {}      # norm_key -> record
    unparsed = []

    def add(judul, penulis, stok, sumber):
        key = norm_key(judul)
        penulis = tidy_author(penulis)
        if key in records:
            r = records[key]
            # Stok: ambil nilai terbesar — baris duplikat = rak yang sama dicatat dua kali,
            # bukan dua eksemplar terpisah.
            r["stok"] = max(r["stok"], stok)
            if r["penulis"] in ("Tidak Tertera", "") and penulis != "Tidak Tertera":
                r["penulis"] = penulis
            r["sumber"].append(sumber)
        else:
            records[key] = {
                "judul": judul,
                "penulis": penulis,
                "stok": stok,
                "sumber": [sumber],
            }

    for fname in CSV_NOTES:
        path = ROOT / fname
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, raw in enumerate(lines[1:], start=2):   # baris 1 = timestamp
            if not raw.strip():
                continue
            parsed = parse_csv_line(raw)
            if parsed is None:
                unparsed.append(f"{fname}:{lineno}: {raw.strip()}")
                continue
            judul, penulis, stok = parsed
            add(judul, penulis, stok, f"{fname}:{lineno}")

    for judul, penulis, stok in MANUAL_MATH:
        add(judul, penulis, stok, f"{MATH_NOTE}:manual")

    out = sorted(records.values(), key=lambda r: r["judul"].lower())
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    dupes = [r for r in out if len(r["sumber"]) > 1]
    print(f"Judul unik      : {len(out)}")
    print(f"Total eksemplar : {sum(r['stok'] for r in out)}")
    print(f"Baris duplikat  : {len(dupes)}")
    for r in dupes:
        print(f"   - {r['judul']}  (stok {r['stok']}, {len(r['sumber'])}x dicatat)")
    if unparsed:
        print(f"\nGAGAL DIURAI ({len(unparsed)}):")
        for u in unparsed:
            print("   " + u)


if __name__ == "__main__":
    main()
