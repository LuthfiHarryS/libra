"""
Pemuat .env sederhana, tanpa dependensi.

python-dotenv sengaja tidak dipakai supaya requirements.txt cabang ini
tetap sama dengan main — kalau eksperimen ini nanti dibuang, tidak ada
sisa apa pun yang tertinggal.

Nilai yang sudah ada di environment TIDAK ditimpa, sehingga menyetel
env var lewat terminal tetap menang atas isi berkas.
"""
import os

# python/chatbot/muat_env.py → naik dua tingkat ke akar repo.
AKAR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BAWAAN = os.path.join(AKAR, '.env')


def muat_env(path: str = BAWAAN) -> int:
    """
    Membaca pasangan KUNCI=nilai dari `path` ke os.environ.

    Mengembalikan jumlah kunci yang benar-benar disetel. Berkas yang
    tidak ada bukan kesalahan — layanan ini harus tetap bisa dijalankan
    hanya dengan env var dari terminal.
    """
    try:
        with open(path, encoding='utf-8') as f:
            baris_semua = f.readlines()
    except OSError:
        return 0

    terpasang = 0
    for baris in baris_semua:
        baris = baris.strip()
        if not baris or baris.startswith('#') or '=' not in baris:
            continue

        kunci, _, nilai = baris.partition('=')
        kunci = kunci.strip()
        nilai = nilai.strip()

        # Tanda kutip pembungkus dibuang, tetapi hanya bila berpasangan —
        # kunci API bisa saja memuat kutip di tengah.
        if len(nilai) >= 2 and nilai[0] == nilai[-1] and nilai[0] in ('"', "'"):
            nilai = nilai[1:-1]

        if kunci and kunci not in os.environ:
            os.environ[kunci] = nilai
            terpasang += 1

    return terpasang
