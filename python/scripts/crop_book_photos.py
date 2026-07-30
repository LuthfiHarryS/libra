"""
crop_book_photos.py — Potong sampul buku dari foto rak di folder "foto cover/".

Foto sumber berisi 1 sampai 6 buku per frame, dalam orientasi campur (potret,
lanskap, terotasi 90 derajat), dengan tangan/kaki/lantai ikut terfoto.
Skrip ini mencari bidang segi empat besar yang menyerupai sampul buku, meluruskan
perspektifnya, lalu menyimpan tiap sampul sebagai file terpisah.

Hasil potongan MASIH perlu dicocokkan ke judul secara manual — lihat
match_photo_covers.py. Skrip ini sengaja longgar (lebih baik kelebihan potongan
yang nanti dibuang daripada ada sampul yang terlewat).

Output: python/scripts/crops/<nama_foto>_<n>.jpg + crops_index.json
"""
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "foto cover"
OUT_DIR = Path(__file__).parent / "crops"
INDEX_PATH = Path(__file__).parent / "crops_index.json"

# Lebar kerja saat deteksi. Foto asli 900-1600px; mengecilkan dulu membuat
# kontur jauh lebih stabil terhadap tekstur karpet dan noise kamera.
WORK_W = 900

# Sampul buku SMP di koleksi ini rasio tinggi:lebar sekitar 1.3-1.6.
# Rentang dilebarkan agar buku yang terpotong sedikit tetap tertangkap.
AR_MIN, AR_MAX = 1.15, 1.85

MIN_AREA_FRAC = 0.020   # buku terkecil dalam grid 2x3 masih di atas 2% frame
MAX_AREA_FRAC = 0.92


def urutkan_titik(pts):
    """Urutkan 4 titik jadi kiri-atas, kanan-atas, kanan-bawah, kiri-bawah."""
    pts = pts.reshape(4, 2).astype("float32")
    hasil = np.zeros((4, 2), dtype="float32")
    jumlah = pts.sum(axis=1)
    hasil[0] = pts[np.argmin(jumlah)]
    hasil[2] = pts[np.argmax(jumlah)]
    selisih = np.diff(pts, axis=1)
    hasil[1] = pts[np.argmin(selisih)]
    hasil[3] = pts[np.argmax(selisih)]
    return hasil


def luruskan(img, quad):
    """Perspective transform 4 titik -> persegi panjang tegak."""
    (tl, tr, br, bl) = quad
    lebar = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    tinggi = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    if lebar < 40 or tinggi < 40:
        return None
    tujuan = np.array([[0, 0], [lebar - 1, 0], [lebar - 1, tinggi - 1], [0, tinggi - 1]],
                      dtype="float32")
    M = cv2.getPerspectiveTransform(quad, tujuan)
    return cv2.warpPerspective(img, M, (lebar, tinggi))


def kandidat_kontur(gray):
    """Gabungkan beberapa strategi ambang — sampul terang di latar gelap dan
    sebaliknya tidak tertangkap oleh satu metode saja."""
    kontur = []

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 1. Canny + closing: bagus untuk tepi buku yang kontras
    for lo, hi in ((30, 90), (50, 150), (75, 200)):
        tepi = cv2.Canny(blur, lo, hi)
        tepi = cv2.morphologyEx(tepi, cv2.MORPH_CLOSE,
                                cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))
        c, _ = cv2.findContours(tepi, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        kontur.extend(c)

    # 2. Otsu: bagus saat latar (karpet gelap) seragam
    for inv in (0, cv2.THRESH_BINARY_INV):
        _, th = cv2.threshold(blur, 0, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU + inv)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE,
                              cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11)))
        c, _ = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        kontur.extend(c)

    return kontur


def containment(inner, outer):
    """Berapa bagian kotak `inner` yang berada di dalam `outer` (0..1)."""
    ax, ay, aw, ah = inner
    bx, by, bw, bh = outer
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    return ((x2 - x1) * (y2 - y1)) / float(aw * ah)


def layak_sampul(img):
    """Buang potongan yang jelas bukan sampul: lantai, karpet, kulit tangan,
    atau bidang blur hasil zoom berlebihan.

    Sampul buku selalu punya teks + grafis -> detail tinggi dan warna kaya.
    """
    if img.shape[0] < 120 or img.shape[1] < 90:
        return False

    kecil = cv2.resize(img, (200, 280))
    gray = cv2.cvtColor(kecil, cv2.COLOR_BGR2GRAY)

    # Detail: sampul bertekstur teks punya varian Laplacian tinggi
    if cv2.Laplacian(gray, cv2.CV_64F).var() < 90:
        return False

    # Kekayaan warna: karpet/lantai/kulit cenderung satu rona saja
    hsv = cv2.cvtColor(kecil, cv2.COLOR_BGR2HSV)
    if hsv[:, :, 1].mean() < 40 and gray.std() < 45:
        return False

    # Dominasi warna kulit -> kemungkinan tangan/kaki yang ikut terfoto
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    kulit = ((h < 25) & (s > 40) & (s < 170) & (v > 60)).mean()
    if kulit > 0.55:
        return False

    return True


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    return inter / float(aw * ah + bw * bh - inter)


def deteksi(path):
    asli = cv2.imread(str(path))
    if asli is None:
        return []

    skala = WORK_W / asli.shape[1]
    kerja = cv2.resize(asli, (WORK_W, int(asli.shape[0] * skala)))
    gray = cv2.cvtColor(kerja, cv2.COLOR_BGR2GRAY)
    luas_frame = kerja.shape[0] * kerja.shape[1]

    temuan = []
    for c in kandidat_kontur(gray):
        luas = cv2.contourArea(c)
        if not (MIN_AREA_FRAC * luas_frame < luas < MAX_AREA_FRAC * luas_frame):
            continue

        peri = cv2.arcLength(c, True)
        quad = None
        for eps in (0.02, 0.03, 0.05):
            approx = cv2.approxPolyDP(c, eps * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                quad = approx
                break
        if quad is None:
            # Bentuk tidak rapi -> pakai kotak berputar minimum
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            # Hanya terima kalau kontur benar-benar mengisi kotaknya (bukan bentuk aneh)
            if rect[1][0] * rect[1][1] == 0 or luas / (rect[1][0] * rect[1][1]) < 0.80:
                continue
            quad = box.astype(np.int32).reshape(4, 1, 2)

        titik = urutkan_titik(quad.astype("float32"))
        warp = luruskan(kerja, titik)
        if warp is None:
            continue

        h, w = warp.shape[:2]
        if w > h:                      # buku terfoto miring/terbaring
            warp = cv2.rotate(warp, cv2.ROTATE_90_CLOCKWISE)
            h, w = warp.shape[:2]
        if not (AR_MIN <= h / w <= AR_MAX):
            continue

        x, y, bw, bh = cv2.boundingRect(quad)
        temuan.append({"bbox": (x, y, bw, bh), "quad": titik, "luas": luas})

    # Buang deteksi ganda dari strategi ambang yang berbeda
    temuan.sort(key=lambda t: -t["luas"])
    unik = []
    for t in temuan:
        if all(iou(t["bbox"], u["bbox"]) < 0.35 for u in unik):
            unik.append(t)

    # Foto grid: kotak besar yang memuat >=2 buku adalah gabungan beberapa
    # sampul, bukan satu sampul. Buang induknya, pertahankan anak-anaknya.
    induk = set()
    for i, a in enumerate(unik):
        anak = sum(
            1 for j, b in enumerate(unik)
            if i != j and b["luas"] < a["luas"] * 0.75
            and containment(b["bbox"], a["bbox"]) > 0.85
        )
        if anak >= 2:
            induk.add(i)
    unik = [t for i, t in enumerate(unik) if i not in induk]

    # Urutkan seperti membaca: atas->bawah, kiri->kanan
    unik.sort(key=lambda t: (round(t["bbox"][1] / 120), t["bbox"][0]))

    # Potong dari citra resolusi penuh, bukan dari citra kerja
    hasil = []
    for t in unik:
        titik_asli = (t["quad"] / skala).astype("float32")
        warp = luruskan(asli, titik_asli)
        if warp is None:
            continue
        h, w = warp.shape[:2]
        if w > h:
            warp = cv2.rotate(warp, cv2.ROTATE_90_CLOCKWISE)
        if not layak_sampul(warp):
            continue
        hasil.append(warp)
    return hasil


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for lama in OUT_DIR.glob("*.jpg"):
        lama.unlink()

    indeks = []
    foto = sorted(SRC_DIR.glob("*.jpeg")) + sorted(SRC_DIR.glob("*.jpg"))
    for p in foto:
        potongan = deteksi(p)
        for i, img in enumerate(potongan):
            nama = f"{p.stem.replace(' ', '_')}__{i}.jpg"
            cv2.imwrite(str(OUT_DIR / nama), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
            indeks.append({"file": nama, "sumber": p.name, "urutan": i,
                           "ukuran": [img.shape[1], img.shape[0]]})
        print(f"{p.name[:48]:50} -> {len(potongan)} potongan", flush=True)

    INDEX_PATH.write_text(json.dumps(indeks, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    print(f"\nTotal {len(indeks)} potongan dari {len(foto)} foto -> {OUT_DIR}")


if __name__ == "__main__":
    main()
