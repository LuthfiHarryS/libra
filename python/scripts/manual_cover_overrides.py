"""
manual_cover_overrides.py — Terapkan URL cover spesifik yang ditemukan manual
via halaman disambiguasi Wikipedia (mis. "Belenggu (novel)" bukan "Belenggu").
"""
import json
import re
import subprocess
import unicodedata
from pathlib import Path

RESULT_PATH = Path(__file__).parent / "famous_books_with_covers.json"
COVERS_DIR = Path(r"D:\xampp\htdocs\libra\uploads\covers")

OVERRIDES = {
    "Belenggu": ("https://upload.wikimedia.org/wikipedia/id/4/45/Belenggu_cover.jpg", "wikipedia_id"),
    "Ranah 3 Warna": ("https://upload.wikimedia.org/wikipedia/id/2/26/Sampul_buku_Ranah_3_Warna.jpg", "wikipedia_id"),
    "Cinta Brontosaurus": ("https://upload.wikimedia.org/wikipedia/id/a/ad/Cinta_Brontosaurus_2.jpg", "wikipedia_id"),
    "Kambing Jantan: Catatan Harian Seorang Cowok Blangsak": ("https://upload.wikimedia.org/wikipedia/id/1/1a/Kambing_Jantan_buku_2.jpg", "wikipedia_id"),
    "Dilan: Dia adalah Dilanku Tahun 1990": ("https://upload.wikimedia.org/wikipedia/id/1/19/Dilan_1990_%28poster%29.jpg", "wikipedia_id_poster"),
}


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:60]


def main():
    results = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    by_title = {r["judul"]: r for r in results}

    for judul, (url, source) in OVERRIDES.items():
        r = by_title.get(judul)
        if not r:
            print(f"SKIP (tidak ditemukan di dataset): {judul}")
            continue
        filename = f"{slugify(judul)}-{slugify(r['penulis'])}.jpg"
        dest = COVERS_DIR / filename
        proc = subprocess.run(["curl", "-sL", "--max-time", "20", "-o", str(dest), url], capture_output=True)
        if proc.returncode == 0 and dest.exists() and dest.stat().st_size > 2000:
            r["cover_filename"] = filename
            r["cover_source"] = source
            r["cover_error"] = None
            print(f"OK: {judul} -> {filename} ({dest.stat().st_size} bytes)")
        else:
            print(f"GAGAL: {judul} — {proc.stderr.decode(errors='ignore')[:200]}")

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    still_missing = [r["judul"] for r in results if not r["cover_filename"]]
    total_with = len(results) - len(still_missing)
    print(f"\n=== TOTAL: {total_with}/{len(results)} buku punya cover ===")
    print(f"Tanpa cover ({len(still_missing)}):")
    for t in still_missing:
        print(f"  - {t}")


if __name__ == "__main__":
    main()
