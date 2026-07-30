"""
split_grid_crops.py — Pecah potongan berisi beberapa buku menjadi sampul terpisah.

crop_book_photos.py sengaja membuang kotak yang memuat >=2 buku, karena itu foto
grid (2x2 / 2x3), bukan satu sampul. Tapi buku-buku di dalamnya saling bersentuhan
sehingga konturnya menyatu dan tidak pernah terdeteksi satu per satu.

Skrip ini menanganinya dengan projection profile: di sela antar-sampul, kerapatan
tepi turun tajam. Lembah terdalam pada profil gradien dipakai sebagai garis potong,
vertikal dan horizontal.

Input : indeks potongan yang ditandai grid (GRID_CROPS di bawah)
Output: python/scripts/crops2/<asal>__r<r>c<c>.jpg + crops2_index.json
"""
import json
from pathlib import Path

import cv2
import numpy as np

CROPS_DIR = Path(__file__).parent / "crops"
INDEX_PATH = Path(__file__).parent / "crops_index.json"
OUT_DIR = Path(__file__).parent / "crops2"
OUT_INDEX = Path(__file__).parent / "crops2_index.json"

# Indeks potongan (dari crops_index.json) yang isinya beberapa buku sekaligus.
# Ditentukan dengan membaca contact sheet, bukan otomatis.
GRID_CROPS = [
    2, 4, 7, 12, 33, 34, 35, 38, 45, 49, 53, 55, 56, 59, 64, 74, 82, 83, 85,
    87, 89, 93, 95, 98, 99, 101, 103, 105, 107, 109, 110, 112, 113, 115, 116,
]

# Sampul tunggal punya rasio tinggi/lebar sekitar ini; dipakai untuk menolak
# hasil pecahan yang jelas bukan satu sampul utuh.
AR_MIN, AR_MAX = 1.05, 2.05
MIN_SISI = 110          # piksel; di bawah ini terlalu kecil untuk jadi cover


def profil_gradien(gray, sumbu):
    """Rata-rata magnitudo gradien tiap baris (sumbu=0) atau kolom (sumbu=1)."""
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    prof = mag.mean(axis=sumbu)
    # Haluskan supaya noise tidak terbaca sebagai lembah
    k = max(5, len(prof) // 40 | 1)
    return cv2.GaussianBlur(prof.reshape(-1, 1), (1, k), 0).ravel()


def cari_potongan(prof, panjang, maks_belah=2):
    """Cari sampai `maks_belah` lembah terdalam di bagian tengah profil.

    Sela antar-buku ada di tengah, bukan di tepi — 22% pertama dan terakhir
    diabaikan supaya bayangan pinggir foto tidak dikira sela.
    """
    lo, hi = int(panjang * 0.22), int(panjang * 0.78)
    if hi - lo < 40:
        return []

    tengah = prof[lo:hi]
    ambang = np.percentile(prof, 35)
    kandidat = []
    i = 0
    while i < len(tengah):
        if tengah[i] < ambang:
            j = i
            while j < len(tengah) and tengah[j] < ambang:
                j += 1
            # Pusat lembah
            kandidat.append((lo + (i + j) // 2, tengah[i:j].mean(), j - i))
            i = j
        else:
            i += 1

    # Lembah paling dalam dan paling lebar dulu
    kandidat.sort(key=lambda c: (c[1], -c[2]))
    dipakai = []
    for pos, _, _ in kandidat:
        if all(abs(pos - d) > panjang * 0.18 for d in dipakai):
            dipakai.append(pos)
        if len(dipakai) >= maks_belah:
            break
    return sorted(dipakai)


def petak(img):
    """Bagi citra jadi sel-sel grid berdasarkan sela vertikal & horizontal."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    x_cut = cari_potongan(profil_gradien(gray, 0), w, maks_belah=2)
    y_cut = cari_potongan(profil_gradien(gray, 1), h, maks_belah=2)

    xs = [0] + x_cut + [w]
    ys = [0] + y_cut + [h]

    sel = []
    for r in range(len(ys) - 1):
        for c in range(len(xs) - 1):
            y0, y1, x0, x1 = ys[r], ys[r + 1], xs[c], xs[c + 1]
            sub = img[y0:y1, x0:x1]
            sh, sw = sub.shape[:2]
            if sh < MIN_SISI or sw < MIN_SISI:
                continue
            if not (AR_MIN <= sh / sw <= AR_MAX):
                continue
            sel.append(((r, c), sub))
    return sel


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for lama in OUT_DIR.glob("*.jpg"):
        lama.unlink()

    idx = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    hasil = []

    for k in GRID_CROPS:
        if k >= len(idx):
            continue
        src = CROPS_DIR / idx[k]["file"]
        img = cv2.imread(str(src))
        if img is None:
            continue

        sel = petak(img)
        if len(sel) < 2:          # gagal dipecah, tidak berguna
            print(f"  crop {k:>3}: gagal dipecah")
            continue

        for (r, c), sub in sel:
            nama = f"crop{k:03d}__r{r}c{c}.jpg"
            cv2.imwrite(str(OUT_DIR / nama), sub, [cv2.IMWRITE_JPEG_QUALITY, 92])
            hasil.append({"file": nama, "dari_crop": k,
                          "sumber": idx[k]["sumber"], "sel": [r, c]})
        print(f"  crop {k:>3}: {len(sel)} sel")

    OUT_INDEX.write_text(json.dumps(hasil, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"\nTotal {len(hasil)} sel dari {len(GRID_CROPS)} potongan grid.")


if __name__ == "__main__":
    main()
