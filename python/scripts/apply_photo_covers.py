"""
apply_photo_covers.py — Pakai foto sampul asli (folder "foto cover/") sebagai cover buku.

Alur: crop_book_photos.py -> photo_cover_map.py (pemetaan manual) -> skrip ini.

Foto asli dari rak perpustakaan lebih tepat daripada hasil pencarian Google Books,
jadi foto MENGGANTIKAN cover yang sudah ada — baik placeholder maupun hasil
Google Books.

Menulis WebP ke uploads/covers/ dan memperbarui books_with_covers.json
(cover_source -> "foto_asli"). Jalankan seed_notes_books.php sesudahnya.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).parent))
from photo_cover_map import PETA                      # noqa: E402
from photo_cover_map2 import PETA2                    # noqa: E402

# Dua sumber potongan: hasil deteksi langsung, dan sel hasil pemecahan foto grid.
SUMBER = [
    (Path(__file__).parent / "crops",  Path(__file__).parent / "crops_index.json",  PETA),
    (Path(__file__).parent / "crops2", Path(__file__).parent / "crops2_index.json", PETA2),
]

BOOKS_PATH = Path(__file__).parent / "books_with_covers.json"
COVERS_DIR = Path(r"D:\xampp\htdocs\libra\uploads\covers")

TARGET_W = 460
WEBP_QUALITY = 82

# Foto diambil dengan tangan: tepi sampul hampir selalu menyisakan sedikit latar.
# Pangkas tipis di keempat sisi supaya sampul terlihat rapi di grid katalog.
TRIM_FRAC = 0.015


def olah(path_crop, rot):
    im = Image.open(path_crop)
    im = ImageOps.exif_transpose(im)
    if rot:
        im = im.rotate(-rot, expand=True)      # PIL berlawanan jarum jam
    im = im.convert("RGB")

    w, h = im.size
    dx, dy = int(w * TRIM_FRAC), int(h * TRIM_FRAC)
    if w - 2 * dx > 100 and h - 2 * dy > 100:
        im = im.crop((dx, dy, w - dx, h - dy))

    if im.width > TARGET_W:
        im = im.resize((TARGET_W, round(im.height * TARGET_W / im.width)), Image.LANCZOS)
    return im


def main():
    books = json.loads(BOOKS_PATH.read_text(encoding="utf-8"))
    by_title = {b["judul"]: b for b in books}

    diganti, gagal = 0, []
    dari_placeholder = dari_gbooks = 0

    for crops_dir, index_path, peta in SUMBER:
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        for crop_i, (judul, rot) in sorted(peta.items()):
            buku = by_title.get(judul)
            if buku is None:
                gagal.append(f"judul tidak ada di katalog: {judul}")
                continue
            if crop_i >= len(idx):
                gagal.append(f"{index_path.name}: indeks {crop_i} di luar jangkauan")
                continue

            src = crops_dir / idx[crop_i]["file"]
            if not src.exists():
                gagal.append(f"potongan hilang: {src.name}")
                continue

            im = olah(src, rot)
            dest = COVERS_DIR / buku["cover_filename"]
            im.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)

            if buku["cover_source"] == "placeholder":
                dari_placeholder += 1
            elif buku["cover_source"] == "google_books":
                dari_gbooks += 1
            buku["cover_source"] = "foto_asli"
            buku["foto_sumber"] = idx[crop_i]["sumber"]
            diganti += 1
            print(f"  {judul[:52]:54} <- {src.name[:30]} rot={rot}")

    BOOKS_PATH.write_text(json.dumps(books, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    print(f"\n=== RINGKASAN ===")
    print(f"  Cover diganti foto asli : {diganti}")
    print(f"    menggantikan placeholder : {dari_placeholder}")
    print(f"    menggantikan Google Books: {dari_gbooks}")
    if gagal:
        print(f"  Gagal ({len(gagal)}):")
        for g in gagal:
            print("    - " + g)

    from collections import Counter
    print("\n  Sebaran sumber cover sekarang:")
    for k, v in Counter(b["cover_source"] for b in books).most_common():
        print(f"    {k:<14} {v}")


if __name__ == "__main__":
    main()
