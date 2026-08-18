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
    # Kategori berikut ada di tabel kategori tetapi belum berisi buku. Tetap
    # dipetakan supaya jawabannya "belum ada buku kategori X" yang akurat,
    # bukan templat umum cara memakai fitur pencarian.
    'pkn': 'PKN', 'ppkn': 'PKN', 'kewarganegaraan': 'PKN',
    # HANYA frasa dua kata. Memetakan 'indonesia' sendirian akan membajak
    # pertanyaan seperti "buku tentang sejarah Indonesia" ke kategori kosong.
    'bahasa indonesia': 'Bahasa Indonesia',
}

# Kata yang tidak boleh dianggap topik pencarian meski lolos filter panjang.
BUKAN_TOPIK = {
    'buku', 'bukunya', 'perpus', 'perpustakaan', 'libra', 'ada', 'apa', 'aja',
    'saja', 'kak', 'dong', 'nggak', 'gak', 'ga', 'gk', 'tidak', 'punya', 'mau',
    'cari', 'cariin', 'nyari', 'pinjam', 'minjam', 'yang', 'tentang', 'sini',
    'ini', 'itu', 'kah', 'ya', 'yaa', 'nih', 'sih', 'min', 'bot', 'engga',
    'kagak', 'gada', 'adakah', 'berapa', 'banyak', 'jumlah', 'koleksi',
}

# Dipakai jawab_info_umum untuk memisahkan pertanyaan jumlah koleksi dari
# pertanyaan jam operasional, yang sama-sama memuat kata "berapa".
_KATA_UKURAN  = {'berapa', 'jumlah', 'banyak', 'kategori', 'koleksi', 'total'}
_KATA_KOLEKSI = {'buku', 'bukunya', 'koleksi', 'judul', 'kategori', 'bacaan'}
_KATA_WAKTU   = {'jam', 'pukul', 'buka', 'bukanya', 'tutup', 'tutupnya', 'hari',
                 'jadwal', 'libur', 'sabtu', 'minggu', 'istirahat', 'operasional'}


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
    """
    (jumlah, tersedia, [judul...]) untuk satu kategori.

    `tersedia` dihitung atas SELURUH kategori, bukan hanya judul contoh.
    Sebelumnya ketersediaan disimpulkan dari tiga judul contoh saja, sehingga
    kalimat "semuanya bisa langsung dipinjam" bisa keliru untuk kategori yang
    sebagian bukunya sedang dipinjam habis.

    None kalau DB tidak terjangkau.
    """
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
                """SELECT COUNT(*) AS n,
                          COALESCE(SUM(b.stok_tersedia > 0), 0) AS tersedia
                   FROM buku b
                   JOIN kategori k ON k.id = b.kategori_id WHERE k.nama = %s""",
                (kategori,),
            )
            row = cur.fetchone()
            return row['n'], int(row['tersedia']), contoh
    except Exception:
        return None


def cari_judul(topik: str):
    """
    Baris buku yang JUDULNYA memuat `topik`, lengkap dengan kategori dan stok.

    Sengaja mencocokkan kolom judul saja, bukan indeks FULLTEXT gabungan
    (judul, penulis, sinopsis) seperti cari_per_topik. Pencocokan yang sempit
    itulah pengamannya: kata umum seperti "kategori" atau "perpustakaan" tidak
    akan pernah cocok dengan satu judul pun, sehingga pertanyaan koleksi dan
    pertanyaan bantuan tidak ikut terbajak menjadi pertanyaan atribut judul.

    None kalau DB tidak terjangkau.
    """
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT b.judul, b.penulis, k.nama AS kategori_nama,
                          b.stok_tersedia, b.stok_total, b.sinopsis
                   FROM buku b LEFT JOIN kategori k ON k.id = b.kategori_id
                   WHERE b.judul LIKE %s
                   ORDER BY CHAR_LENGTH(b.judul), b.judul
                   LIMIT %s""",
                (f'%{topik}%', MAKS_SEBUT),
            )
            return cur.fetchall()
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


def _keterangan_penulis(rows) -> str:
    """
    " karya X" hanya kalau X benar-benar menulis SEMUA judul yang disebut.

    Sebelumnya penulis judul pertama ditempelkan ke seluruh daftar, sehingga
    jawaban menyatakan tiga buku karya satu orang padahal penulisnya berbeda.
    Untuk daftar dengan penulis campuran, atribusi dihilangkan sepenuhnya.
    """
    penulis = {(r.get('penulis') or '').strip() for r in rows}
    if len(penulis) == 1:
        satu = penulis.pop()
        if satu:
            return f" karya {satu}"
    return ""


# Kata yang menandai pertanyaan tentang atribut sebuah judul. "tersedia" dan
# "ada" sengaja tidak dimasukkan: keduanya sudah tertangani dengan benar oleh
# intent cari_buku dan memasukkannya justru akan membajak perilaku yang sehat.
_KATA_ATRIBUT = {
    'kategori': 'kategori', 'kategorinya': 'kategori', 'genre': 'kategori',
    'genrenya': 'kategori', 'termasuk': 'kategori',
    'penulis': 'penulis', 'penulisnya': 'penulis', 'pengarang': 'penulis',
    'pengarangnya': 'penulis', 'karya': 'penulis', 'nulis': 'penulis',
    'menulis': 'penulis',
    'sinopsis': 'sinopsis', 'sinopsisnya': 'sinopsis', 'ringkasan': 'sinopsis',
    'ringkasannya': 'sinopsis', 'isinya': 'sinopsis',
    'eksemplar': 'stok', 'stok': 'stok', 'stoknya': 'stok',
}

# Kata tanya dan kata pengisi yang tidak boleh dikira bagian judul. Disimpan
# terpisah dari BUKAN_TOPIK supaya perilaku cari_buku yang sudah diukur pada
# subbab 3.8.2 tidak ikut berubah.
_KATA_TANYA = {
    'siapa', 'siapakah', 'kapan', 'bagaimana', 'gimana', 'kenapa', 'mengapa',
    'dimana', 'mana', 'apakah', 'kalau', 'judul', 'judulnya', 'tolong',
    'menulis', 'nulis', 'bikin', 'buat',
    # "cara" ikut dibuang karena kata tanya prosedural, meskipun katalog
    # memuat judul yang diawali kata itu. Buku semacam "Cara Menentukan
    # Golongan Darah" tetap terjangkau lewat kata lain pada judulnya.
    'cara', 'caranya',
}


def jawab_detail_buku(pesan: str) -> Optional[str]:
    """
    Jawaban untuk pertanyaan atribut sebuah judul. None -> bukan urusan fungsi ini.

    Classifier tidak punya kelas untuk pertanyaan semacam ini, dan kata
    penandanya justru condong ke intent lain: pada data latih, "penulis" tidak
    pernah muncul sedangkan "kategori" hanya ada di info_umum dan
    bantuan_sistem. Akibatnya "Negeri 5 Menara kategorinya apa" diklasifikasi
    sebagai info_umum lalu dijawab jam buka. Fungsi ini memotong keadaan itu
    di tahap penyusunan jawaban, tanpa mengubah dataset maupun model.

    Dua syarat harus terpenuhi bersamaan supaya tidak membajak pertanyaan lain:
    pesan memuat kata tanya atribut, DAN memuat kata yang benar-benar cocok
    dengan judul di katalog.
    """
    kata = set(re.sub(r'[^\w\s]', ' ', pesan.lower()).split())
    diminta = {_KATA_ATRIBUT[k] for k in kata if k in _KATA_ATRIBUT}
    if not diminta:
        return None

    # Kandidat judul: kata di luar daftar kata umum, kata atribut, dan kata
    # tanya. Kata tanya harus ikut dibuang karena katalog memuat judul yang
    # diawali kata tanya — tanpa penyaringan ini "siapa penulis Negeri 5
    # Menara" menunjuk buku "Siapa Bilang Matematika Sulit 3".
    kandidat = [k for k in kandidat_topik(pesan)
                if k not in _KATA_ATRIBUT and k not in _KATA_TANYA]
    if not kandidat:
        return None

    # Judul dipilih berdasarkan BERAPA BANYAK kandidat yang menunjuk judul
    # yang sama. Satu kata pendek saja tidak cukup: katalog memuat judul yang
    # diawali kata lazim seperti "Cara ...", sehingga pertanyaan bantuan
    # "cara filter buku per kategori gimana" akan terbaca sebagai pertanyaan
    # atribut judul kalau satu kecocokan sudah dianggap sah.
    hasil = [(k, cari_judul(k)) for k in kandidat]
    hasil = [(k, rows) for k, rows in hasil if rows]
    if not hasil:
        return None

    # Berapa kandidat yang menunjuk judul yang sama.
    cocok = {}
    for k, rows in hasil:
        for r in rows:
            n, baris = cocok.get(r['judul'], (0, r))
            cocok[r['judul']] = (n + 1, baris)

    judul_pilihan = max(cocok, key=lambda j: cocok[j][0])
    n_kandidat, b = cocok[judul_pilihan]

    if n_kandidat < 2:
        # Hanya satu kata yang menunjuk judul ini, jadi kata itu harus benar-
        # benar menciri: cocok dengan tepat satu judul di katalog. Kata lazim
        # seperti "cara" mengenai beberapa judul sekaligus ("Cara Menentukan
        # Golongan Darah" dan lainnya) sehingga pertanyaan bantuan tidak ikut
        # terbaca sebagai pertanyaan atribut judul.
        menciri = [rows for k, rows in hasil if len(rows) == 1]
        if not menciri:
            return None
        b = menciri[0][0]
        judul_pilihan = b['judul']

    judul = b['judul']
    bagian = []
    if 'kategori' in diminta:
        kat = (b.get('kategori_nama') or '').strip()
        bagian.append(f'termasuk kategori {kat}' if kat
                      else 'belum diberi kategori')
    if 'penulis' in diminta:
        pen = (b.get('penulis') or '').strip()
        bagian.append(f'ditulis oleh {pen}' if pen else 'penulisnya belum dicatat')
    if 'stok' in diminta:
        total = b.get('stok_total')
        bagian.append(f'tercatat {total} eksemplar' if total is not None
                      else 'jumlah eksemplarnya belum dicatat')
    if 'sinopsis' in diminta and not bagian:
        bagian.append('sinopsis lengkapnya bisa dibaca di halaman Detail Buku')

    kalimat = f'"{judul}" ' + ', '.join(bagian) + '.'

    tersedia = b.get('stok_tersedia')
    if tersedia is not None:
        kalimat += (' Saat ini bisa langsung dipinjam.' if tersedia > 0
                    else ' Saat ini sedang dipinjam semua.')
    if len(cocok) > 1:
        kalimat += ' Kalau bukan buku ini, coba telusuri lewat halaman Katalog ya.'
    return kalimat


def jawab_cari_buku(pesan: str) -> Optional[str]:
    """Jawaban dinamis untuk intent cari_buku. None -> pakai template lama."""
    kategori = ekstrak_kategori(pesan)
    if kategori:
        hasil = cari_per_kategori(kategori)
        if hasil is None:
            return None
        jumlah, tersedia, contoh = hasil
        if jumlah == 0:
            return (f"Maaf, belum ada buku kategori {kategori} di koleksi LIBRA saat ini. "
                    f"Coba cari kategori lain lewat halaman Katalog ya!")
        kalimat = (f"Ada {jumlah} buku kategori {kategori} di LIBRA. "
                   f"Contohnya {_daftar_judul(contoh)}{_keterangan_penulis(contoh)}. ")
        if tersedia == jumlah:
            kalimat += "Semuanya bisa langsung dipinjam."
        elif tersedia == 0:
            kalimat += "Sayangnya semua sedang dipinjam. Cek halaman Katalog secara berkala ya!"
        else:
            kalimat += f"Saat ini {tersedia} di antaranya bisa langsung dipinjam."
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
            contoh = hasil[2]
            return (f"Untuk kategori {kategori}, kamu bisa mulai dari "
                    f"{_daftar_judul(contoh)}{_keterangan_penulis(contoh)}. "
                    f"Rekomendasi yang lebih sesuai denganmu ada di bagian "
                    f"'Rekomendasi untuk Kamu' di halaman utama.")

    rows = buku_terpopuler()
    if not rows:
        return None
    return (f"Buku yang paling sering dipinjam di LIBRA: {_daftar_judul(rows)}. "
            f"Kalau mau saran yang cocok dengan seleramu, lihat panel "
            f"'Rekomendasi untuk Kamu' di halaman utama — disusun dari buku yang "
            f"pernah kamu pinjam.")


# Aturan peminjaman. Nilai di bawah HARUS sama dengan sumber kebenarannya:
#   DURASI_PINJAM_HARI -> react/src/components/DueCountdown.tsx BORROW_DURATION_DAYS
#                         dan INTERVAL 7 DAY di api/controllers/AdminController.php
#   BATAS_PINJAM_AKTIF -> BATAS_PINJAM di api/config.php
# Kalau salah satu diubah, ubah juga di sini — chatbot tidak membacanya dari API.
DURASI_PINJAM_HARI = 7
BATAS_PINJAM_AKTIF = 3


def jawab_prosedur_pinjam(pesan: str) -> Optional[str]:
    """
    Jawaban bertopik untuk intent prosedur_pinjam.

    Satu intent ini menampung seluruh daur hidup peminjaman: cara meminjam,
    durasi, batas jumlah, pengembalian, perpanjangan, denda, serta buku hilang
    atau rusak. Templat tetapnya hanya menjelaskan cara MEMINJAM, sehingga
    pertanyaan "cara mengembalikan buku" dijawab langkah peminjaman. Fungsi ini
    memilih paragraf yang sesuai; None berarti pakai templat lama.

    Denda dan perpanjangan sengaja dijawab apa adanya: kedua fitur itu TIDAK ada
    di sistem, jadi siswa diarahkan ke petugas alih-alih diberi aturan karangan.
    """
    kata = set(re.sub(r'[^\w\s]', ' ', pesan.lower()).split())

    if kata & {'hilang', 'rusak', 'sobek', 'basah', 'ilang'}:
        return ("Kalau buku yang kamu pinjam hilang atau rusak, segera lapor ke petugas "
                "perpustakaan ya. Penggantiannya diatur langsung oleh petugas, bukan "
                "lewat aplikasi LIBRA.")

    if kata & {'denda', 'didenda', 'sanksi', 'telat', 'terlambat'}:
        return (f"LIBRA mencatat tanggal jatuh tempo dan menandai peminjaman yang lewat "
                f"{DURASI_PINJAM_HARI} hari sebagai terlambat, tetapi aplikasi ini tidak "
                f"menghitung denda. Ketentuan denda diatur petugas perpustakaan, jadi "
                f"tanyakan langsung ke petugas ya.")

    if kata & {'perpanjang', 'diperpanjang', 'perpanjangan', 'tambah', 'ditambah'}:
        return ("Perpanjangan masa pinjam belum bisa diajukan lewat aplikasi LIBRA. "
                "Kembalikan dulu bukunya ke petugas, lalu ajukan peminjaman baru dari "
                "halaman Katalog kalau masih mau membacanya.")

    if kata & {'kembalikan', 'mengembalikan', 'pengembalian', 'balikin', 'balik', 'kembali'}:
        return (f"Cara mengembalikan buku: bawa bukunya ke petugas perpustakaan sebelum "
                f"batas {DURASI_PINJAM_HARI} hari. Petugas yang akan menandai peminjamanmu "
                f"sebagai 'Dikembalikan' di LIBRA, dan stok buku otomatis bertambah lagi. "
                f"Status terbarunya bisa kamu lihat di halaman 'Status Peminjaman'.")

    if kata & {'lama', 'durasi', 'hari', 'berapa'} and kata & {'pinjam', 'minjam', 'pinjem', 'minjem'}:
        return (f"Buku boleh dipinjam selama {DURASI_PINJAM_HARI} hari sejak disetujui "
                f"petugas. Kamu bisa meminjam paling banyak {BATAS_PINJAM_AKTIF} buku "
                f"sekaligus. Sisa waktunya tampil di halaman 'Status Peminjaman'.")

    return None


def jawab_info_umum(pesan: str) -> Optional[str]:
    """
    Tambahkan angka koleksi nyata kalau pertanyaannya memang soal jumlah koleksi.

    Pemeriksaan kata "berapa" saja tidak cukup. "perpustakaan buka jam berapa"
    memuat kata itu tetapi menanyakan jam operasional, dan sebelumnya dijawab
    dengan jumlah judul buku. Karena itu jawaban koleksi hanya disusun ketika
    pesan memuat kata ukuran DAN kata benda koleksi, serta tidak memuat penanda
    waktu. Di luar itu kembalikan None supaya templat jam buka yang dipakai.
    """
    kata = set(re.sub(r'[^\w\s]', ' ', pesan.lower()).split())
    if not (kata & _KATA_UKURAN):
        return None
    if not (kata & _KATA_KOLEKSI):
        return None
    if kata & _KATA_WAKTU:
        return None
    hasil = ringkasan_koleksi()
    if not hasil:
        return None
    total, n_kat, tiga = hasil
    daftar = ', '.join(f"{r['nama']} ({r['n']})" for r in tiga)
    return (f"Koleksi LIBRA saat ini berjumlah {total} judul buku yang terbagi "
            f"dalam {n_kat} kategori. Terbanyak: {daftar}. "
            f"Semua bisa ditelusuri lewat halaman Katalog.")
