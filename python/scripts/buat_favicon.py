"""Membuat set favicon LIBRA dari logo SMP Negeri 1 Kemang.

Sumber: react/public/icon.png (logo asli, 577x433, banyak ruang transparan).

Berkas itu tidak bisa dipakai apa adanya sebagai favicon:
  * Bentuknya tidak persegi, sedangkan Google hanya mengambil favicon persegi
    dengan sisi kelipatan 48 px. Kalau ditolak, hasil pencarian memakai ikon
    globe bawaan.
  * Latarnya transparan, sedangkan tulisan "SMP NEGERI 1 KEMANG" berwarna
    hitam. Di tab bertema gelap dan di pintasan layar depan, tulisan itu hilang.

Jadi logo dipangkas ke kotak isinya, diberi margin, ditaruh di atas putih,
lalu diekspor ke ukuran-ukuran yang dibaca peramban dan mesin telusur.

Jalankan dari akar proyek:

    python/.venv/Scripts/python.exe python/scripts/buat_favicon.py
"""

from pathlib import Path

from PIL import Image

AKAR = Path(__file__).resolve().parents[2]
SUMBER = AKAR / "react" / "public" / "icon.png"
KELUARAN = AKAR / "react" / "public"

PUTIH = (255, 255, 255, 255)

# Margin di sekeliling logo, sebagai pecahan dari sisi kotak.
MARGIN_BIASA = 0.06
# Ikon maskable dipotong bulat oleh Android; isinya harus muat di lingkaran
# aman selebar 80% sisi, sehingga marginnya jauh lebih lebar.
MARGIN_MASKABLE = 0.22

# 16/32/48 adalah ukuran yang benar-benar dipakai peramban di dalam .ico.
UKURAN_ICO = [16, 32, 48]

# Kelipatan 48 supaya lolos syarat Google; 180 adalah ukuran wajib Apple.
UKURAN_PNG = {
    "favicon-96.png": 96,
    "apple-touch-icon.png": 180,
    "icon-192.png": 192,
    "icon-512.png": 512,
}


def logo_kotak(margin: float) -> Image.Image:
    """Logo yang sudah dipangkas, diberi margin, dan diratakan ke latar putih."""
    logo = Image.open(SUMBER).convert("RGBA")

    # getbbox() pada RGBA mengabaikan piksel yang alfanya 0, jadi ini membuang
    # seluruh ruang kosong di sekeliling logo.
    kotak_isi = logo.getbbox()
    if kotak_isi is None:
        raise SystemExit(f"GAGAL: {SUMBER} kosong / seluruhnya transparan.")
    logo = logo.crop(kotak_isi)

    sisi_isi = max(logo.size)
    sisi = round(sisi_isi / (1 - 2 * margin))
    kanvas = Image.new("RGBA", (sisi, sisi), PUTIH)
    kanvas.alpha_composite(
        logo,
        ((sisi - logo.width) // 2, (sisi - logo.height) // 2),
    )
    return kanvas


def main() -> None:
    dasar = logo_kotak(MARGIN_BIASA)

    for nama, ukuran in UKURAN_PNG.items():
        gambar = dasar.resize((ukuran, ukuran), Image.LANCZOS)
        # iOS tidak menangani kanal alfa pada apple-touch-icon; latarnya sudah
        # putih penuh, jadi kanal itu dibuang saja.
        if nama == "apple-touch-icon.png":
            gambar = gambar.convert("RGB")
        gambar.save(KELUARAN / nama)
        print(f"  {nama:<24} {ukuran}x{ukuran}")

    maskable = logo_kotak(MARGIN_MASKABLE).resize((512, 512), Image.LANCZOS)
    maskable.save(KELUARAN / "icon-512-maskable.png")
    print(f"  {'icon-512-maskable.png':<24} 512x512")

    # .ico ditulis dari salinan besar supaya Pillow yang menurunkan skalanya
    # untuk tiap ukuran di dalamnya.
    dasar.resize((256, 256), Image.LANCZOS).save(
        KELUARAN / "favicon.ico",
        sizes=[(u, u) for u in UKURAN_ICO],
    )
    print(f"  {'favicon.ico':<24} {'/'.join(str(u) for u in UKURAN_ICO)}")

    print(f"\nSelesai. Berkas ditulis ke {KELUARAN}")
    print("Jangan lupa `npm run build` lalu pasang dist/ ke server.")


if __name__ == "__main__":
    main()
