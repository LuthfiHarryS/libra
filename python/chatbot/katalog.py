"""
katalog.py — Akses katalog untuk menyusun jawaban chatbot dari data nyata.

Sebelumnya chatbot hanya mengembalikan template statis dari REPLIES: pertanyaan
"ada buku komik tidak" dijawab dengan penjelasan umum cara memakai fitur
pencarian, bukan dengan isi koleksi yang sebenarnya.

Modul ini menambahkan tahap setelah klasifikasi intent:

    pesan -> LinearSVC (intent) -> ekstraksi entitas -> query katalog -> jawaban

Classifier tidak diubah. Yang bertambah hanya slot filling dan pengambilan data,
sehingga jawaban menyebut judul, jumlah, dan ketersediaan yang benar.

Semua fungsi di sini FAIL-SAFE: kalau database tidak bisa dihubungi, kembalikan
None supaya app.py jatuh ke template lama. Chatbot tidak boleh mati hanya karena
katalog sedang tidak tersedia.
"""
import os
import re
from typing import Optional

import pymysql
import pymysql.cursors

DB_HOST = os.environ.get('LIBRA_DB_HOST', 'localhost')
DB_USER = os.environ.get('LIBRA_DB_USER', 'root')
DB_PASS = os.environ.get('LIBRA_DB_PASS', '')
DB_NAME = os.environ.get('LIBRA_DB_NAME', 'libra_db')

# Berapa judul yang disebutkan dalam satu jawaban. Lebih dari 3 membuat balasan
# terlalu panjang untuk gelembung chat di layar ponsel.
MAKS_SEBUT = 3


def _conn():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME,
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=3, read_timeout=5,
    )


# ── Sinonim kategori ────────────────────────────────────────────────────────
# Kunci = kata yang mungkin diketik siswa, nilai = nama kategori di tabel.
# Dibutuhkan karena siswa menulis "mtk"/"matek", bukan "Matematika".
SINONIM_KATEGORI = {
    'matematika': 'Matematika', 'mtk': 'Matematika', 'matek': 'Matematika',
    'math': 'Matematika', 'aljabar': 'Matematika', 'geometri': 'Matematika',
    'ipa': 'Sains', 'sains': 'Sains', 'science': 'Sains',
    'biologi': 'Biologi', 'bio': 'Biologi',
    'fisika': 'Fisika', 'kimia': 'Kimia',
    'ips': 'IPS', 'sosial': 'IPS', 'ekonomi': 'IPS',
    'sejarah': 'Sejarah', 'history': 'Sejarah',
    'olahraga': 'Olahraga', 'olga': 'Olahraga', 'penjas': 'Olahraga',
    'pjok': 'Olahraga', 'sport': 'Olahraga',
    'agama': 'Agama', 'islam': 'Agama', 'religi': 'Agama',
    'komik': 'Komik', 'manga': 'Komik',
    'fiksi': 'Fiksi', 'novel': 'Fiksi', 'cerita': 'Fiksi', 'cerpen': 'Fiksi',
    'nonfiksi': 'Non-Fiksi', 'non fiksi': 'Non-Fiksi',
    'teknologi': 'Teknologi', 'komputer': 'Teknologi', 'tik': 'Teknologi',
    'inggris': 'Bahasa Inggris', 'english': 'Bahasa Inggris',
    'bahasa inggris': 'Bahasa Inggris',
}

# Kata yang tidak boleh dianggap topik pencarian meski lolos filter panjang.
BUKAN_TOPIK = {
    'buku', 'bukunya', 'perpus', 'perpustakaan', 'libra', 'ada', 'apa', 'aja',
    'saja', 'kak', 'dong', 'nggak', 'gak', 'ga', 'gk', 'tidak', 'punya', 'mau',
    'cari', 'cariin', 'nyari', 'pinjam', 'minjam', 'yang', 'tentang', 'sini',
    'ini', 'itu', 'kah', 'ya', 'yaa', 'nih', 'sih', 'min', 'bot', 'engga',
    'kagak', 'gada', 'adakah', 'berapa', 'banyak', 'jumlah', 'koleksi',
}


def ekstrak_kategori(pesan: str) -> Optional[str]:
    """Cari nama kategori (atau sinonimnya) di dalam pesan."""
    p = ' ' + re.sub(r'[^\w\s]', ' ', pesan.lower()) + ' '
    # Frasa dua kata diperiksa lebih dulu agar "bahasa inggris" tidak
    # tertangkap sebagai "inggris" saja — hasilnya sama, tapi urutan ini
    # mencegah salah cocok bila kelak ada sinonim yang saling tumpang tindih.
    for kata in sorted(SINONIM_KATEGORI, key=len, reverse=True):
        if f' {kata} ' in p:
            return SINONIM_KATEGORI[kata]
    return None


def kandidat_topik(pesan: str) -> list:
    """Semua kata yang mungkin menjadi topik pencarian, urut kemunculan."""
    kata = re.sub(r'[^\w\s]', ' ', pesan.lower()).split()
    return [k for k in kata if len(k) > 3 and k not in BUKAN_TOPIK]


def ekstrak_topik(pesan: str) -> Optional[str]:
    """Kandidat topik pertama. Dipertahankan untuk pemakaian sederhana/pengujian."""
    k = kandidat_topik(pesan)
    return k[0] if k else None


# ── Query ───────────────────────────────────────────────────────────────────
def cari_per_kategori(kategori: str):
    """(jumlah, [judul...]) untuk satu kategori. None kalau DB tidak terjangkau."""
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT b.judul, b.penulis, b.stok_tersedia
                   FROM buku b JOIN kategori k ON k.id = b.kategori_id
                   WHERE k.nama = %s
                   ORDER BY b.stok_tersedia DESC, b.judul
                   LIMIT %s""",
                (kategori, MAKS_SEBUT),
            )
            contoh = cur.fetchall()
            cur.execute(
                """SELECT COUNT(*) AS n FROM buku b
                   JOIN kategori k ON k.id = b.kategori_id WHERE k.nama = %s""",
                (kategori,),
            )
            return cur.fetchone()['n'], contoh
    except Exception:
        return None


def cari_per_topik(topik: str):
    """(jumlah, [judul...]) hasil pencarian FULLTEXT pada judul/penulis/sinopsis."""
    try:
        with _conn() as c, c.cursor() as cur:
            # Boolean mode + wildcard supaya "senam" ikut menangkap "senamnya".
            ekspresi = f'{topik}*'
            cur.execute(
                """SELECT judul, penulis, stok_tersedia FROM buku
                   WHERE MATCH(judul, penulis, sinopsis) AGAINST (%s IN BOOLEAN MODE)
                   ORDER BY stok_tersedia DESC LIMIT %s""",
                (ekspresi, MAKS_SEBUT),
            )
            contoh = cur.fetchall()
            cur.execute(
                """SELECT COUNT(*) AS n FROM buku
                   WHERE MATCH(judul, penulis, sinopsis) AGAINST (%s IN BOOLEAN MODE)""",
                (ekspresi,),
            )
            return cur.fetchone()['n'], contoh
    except Exception:
        return None


def buku_terpopuler():
    """Judul yang paling sering dipinjam — dasar jawaban rekomendasi."""
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT b.judul, b.penulis, COUNT(p.id) AS n
                   FROM buku b LEFT JOIN peminjaman p
                     ON p.buku_id = b.id AND p.status IN ('Dipinjam','Dikembalikan')
                   GROUP BY b.id, b.judul, b.penulis
                   ORDER BY n DESC, b.stok_tersedia DESC
                   LIMIT %s""",
                (MAKS_SEBUT,),
            )
            return cur.fetchall()
    except Exception:
        return None


def ringkasan_koleksi():
    """(total_buku, total_kategori, [(kategori, jumlah) x3]) untuk info_umum."""
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM buku")
            total = cur.fetchone()['n']
            cur.execute(
                """SELECT k.nama, COUNT(b.id) AS n FROM kategori k
                   JOIN buku b ON b.kategori_id = k.id
                   GROUP BY k.nama ORDER BY n DESC"""
            )
            per_kat = cur.fetchall()
            return total, len(per_kat), per_kat[:3]
    except Exception:
        return None


# ── Perakit kalimat ─────────────────────────────────────────────────────────
def _daftar_judul(rows) -> str:
    judul = [f'"{r["judul"]}"' for r in rows]
    if len(judul) == 1:
        return judul[0]
    return ', '.join(judul[:-1]) + ' dan ' + judul[-1]


def jawab_cari_buku(pesan: str) -> Optional[str]:
    """Jawaban dinamis untuk intent cari_buku. None -> pakai template lama."""
    kategori = ekstrak_kategori(pesan)
    if kategori:
        hasil = cari_per_kategori(kategori)
        if hasil is None:
            return None
        jumlah, contoh = hasil
        if jumlah == 0:
            return (f"Maaf, belum ada buku kategori {kategori} di koleksi LIBRA saat ini. "
                    f"Coba cari kategori lain lewat halaman Katalog ya!")
        tersedia = sum(1 for r in contoh if r['stok_tersedia'] > 0)
        kalimat = (f"Ada {jumlah} buku kategori {kategori} di LIBRA. "
                   f"Contohnya {_daftar_judul(contoh)}")
        if contoh:
            kalimat += f" karya {contoh[0]['penulis']}"
        kalimat += ". "
        kalimat += ("Semuanya bisa langsung dipinjam." if tersedia == len(contoh)
                    else "Cek halaman Katalog untuk melihat ketersediaannya.")
        return kalimat

    kandidat = kandidat_topik(pesan)
    if not kandidat:
        return None

    # Coba setiap kandidat, lalu pilih yang PALING SPESIFIK: jumlah hasil
    # terkecil yang masih lebih dari nol. Tanpa ini, "ada buku bahasa arab"
    # akan memakai "bahasa" (10 hasil, melebar ke mana-mana) padahal "arab"
    # jauh lebih tepat.
    terbaik = None
    for k in kandidat[:4]:
        hasil = cari_per_topik(k)
        if hasil is None:
            return None                     # DB tidak terjangkau
        jumlah, contoh = hasil
        if jumlah > 0 and (terbaik is None or jumlah < terbaik[1]):
            terbaik = (k, jumlah, contoh)

    if terbaik is None:
        return (f"Aku belum menemukan buku tentang \"{kandidat[0]}\" di koleksi LIBRA. "
                f"Coba kata kunci lain, atau telusuri lewat kategori di halaman Katalog.")

    topik, jumlah, contoh = terbaik
    return (f"Aku menemukan {jumlah} buku tentang \"{topik}\": "
            f"{_daftar_judul(contoh)}. Buka halaman Katalog untuk detail lengkapnya.")


def jawab_rekomendasi(pesan: str) -> Optional[str]:
    """Jawaban dinamis untuk intent rekomendasi_buku."""
    kategori = ekstrak_kategori(pesan)
    if kategori:
        hasil = cari_per_kategori(kategori)
        if hasil and hasil[0] > 0:
            return (f"Untuk kategori {kategori}, kamu bisa mulai dari "
                    f"{_daftar_judul(hasil[1])}. Rekomendasi yang lebih sesuai "
                    f"denganmu ada di bagian 'Rekomendasi untuk Kamu' di halaman utama.")

    rows = buku_terpopuler()
    if not rows:
        return None
    return (f"Buku yang paling sering dipinjam di LIBRA: {_daftar_judul(rows)}. "
            f"Kalau mau saran yang cocok dengan seleramu, lihat panel "
            f"'Rekomendasi untuk Kamu' di halaman utama — disusun dari buku yang "
            f"pernah kamu pinjam.")


def jawab_info_umum(pesan: str) -> Optional[str]:
    """Tambahkan angka koleksi nyata kalau pertanyaannya soal jumlah/kategori."""
    p = pesan.lower()
    if not any(k in p for k in ('berapa', 'jumlah', 'banyak', 'kategori', 'koleksi')):
        return None
    hasil = ringkasan_koleksi()
    if not hasil:
        return None
    total, n_kat, tiga = hasil
    daftar = ', '.join(f"{r['nama']} ({r['n']})" for r in tiga)
    return (f"Koleksi LIBRA saat ini berjumlah {total} judul buku yang terbagi "
            f"dalam {n_kat} kategori. Terbanyak: {daftar}. "
            f"Semua bisa ditelusuri lewat halaman Katalog.")
