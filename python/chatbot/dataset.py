"""
dataset.py — Training data dan reply templates untuk chatbot LIBRA.

TRAINING_DATA: 210 sampel, 7 intent × 30 variasi (seimbang).
REPLIES: dict 8 key — 7 intent + tidak_dimengerti (threshold fallback saja, bukan kelas training).

Desain dataset (v2 — diperluas dari 84 → 210 sampel):
- 30 sampel/intent supaya data uji hasil split 80/20 stratified cukup besar (42 sampel,
  6 per intent) → metrik per-kelas lebih stabil dan tidak bergoyang oleh 1 kesalahan.
- Batas cari_buku vs rekomendasi_buku dipertajam untuk menghindari kebingungan model:
    * cari_buku       = pengguna MENYEBUT topik/mapel/judul/penulis spesifik
                        ("ada buku tentang tata surya?", "cari buku IPA").
    * rekomendasi_buku = pengguna MINTA SARAN tanpa topik, memakai kata pembeda
                        bagus/menarik/seru/populer/saran/rekomendasi
                        ("buku apa yang bagus?", "rekomendasiin buku dong").
  Frasa ambigu lama seperti "cari buku cerita" vs "rekomendasi buku cerita" dihindari.
- Variasi natural: campuran formal + informal/slang siswa (dong, ga, kak, nih) + beberapa typo.

CRITICAL: tidak_dimengerti BUKAN kelas training — hanya muncul di REPLIES sebagai fallback
ketika confidence < 0.5. Jangan tambahkan ke TRAINING_DATA.
"""

TRAINING_DATA = [
    # ── cari_buku ── 30 sampel — SELALU menyebut topik/mapel/judul/penulis spesifik
    {"text": "cari buku IPA", "intent": "cari_buku"},
    {"text": "ada buku matematika ga", "intent": "cari_buku"},
    {"text": "mau cari buku tentang sejarah", "intent": "cari_buku"},
    {"text": "ada buku pelajaran fisika?", "intent": "cari_buku"},
    {"text": "cariin buku biologi dong", "intent": "cari_buku"},
    {"text": "ada buku tentang tata surya nggak", "intent": "cari_buku"},
    {"text": "nyari buku bahasa inggris", "intent": "cari_buku"},
    {"text": "mau cari buku geografi", "intent": "cari_buku"},
    {"text": "ada buku tentang Indonesia ga?", "intent": "cari_buku"},
    {"text": "cari buku kimia kelas 9", "intent": "cari_buku"},
    {"text": "punya buku tentang hewan langka nggak", "intent": "cari_buku"},
    {"text": "mau cari novel Laskar Pelangi", "intent": "cari_buku"},
    {"text": "ada buku karya Tere Liye ga", "intent": "cari_buku"},
    {"text": "cari buku tentang tumbuhan", "intent": "cari_buku"},
    {"text": "ada kamus bahasa inggris nggak", "intent": "cari_buku"},
    {"text": "nyari buku tentang komputer", "intent": "cari_buku"},
    {"text": "mau cari buku ensiklopedia sains", "intent": "cari_buku"},
    {"text": "ada buku tentang perang dunia ga", "intent": "cari_buku"},
    {"text": "cari buku PKN", "intent": "cari_buku"},
    {"text": "ada buku tentang planet nggak kak", "intent": "cari_buku"},
    {"text": "mau cari buku olahraga", "intent": "cari_buku"},
    {"text": "cari buku tentang budaya Indonesia", "intent": "cari_buku"},
    {"text": "ada buku agama Islam ga", "intent": "cari_buku"},
    {"text": "nyari buku tentang lingkungan hidup", "intent": "cari_buku"},
    {"text": "cari buku ekonomi", "intent": "cari_buku"},
    {"text": "ada buku tentang teknologi nggak", "intent": "cari_buku"},
    {"text": "mau cari buku kumpulan puisi", "intent": "cari_buku"},
    {"text": "ada buku tentang kesehatan ga", "intent": "cari_buku"},
    {"text": "cari buku seni musik", "intent": "cari_buku"},
    {"text": "ada buku tentang luar angkasa nggak", "intent": "cari_buku"},

    # ── rekomendasi_buku ── 30 sampel — MINTA SARAN tanpa topik spesifik
    {"text": "rekomendasiin buku dong", "intent": "rekomendasi_buku"},
    {"text": "minta rekomendasi buku", "intent": "rekomendasi_buku"},
    {"text": "buku apa yang bagus", "intent": "rekomendasi_buku"},
    {"text": "ada rekomendasi buku ga", "intent": "rekomendasi_buku"},
    {"text": "buku apa yang recommended", "intent": "rekomendasi_buku"},
    {"text": "buku yang menarik apa ya", "intent": "rekomendasi_buku"},
    {"text": "rekomendasikan buku yang bagus", "intent": "rekomendasi_buku"},
    {"text": "buku apa yang cocok buat aku", "intent": "rekomendasi_buku"},
    {"text": "suggest buku dong", "intent": "rekomendasi_buku"},
    {"text": "ada saran buku ga", "intent": "rekomendasi_buku"},
    {"text": "buku populer apa aja", "intent": "rekomendasi_buku"},
    {"text": "buku apa yang seru buat dibaca", "intent": "rekomendasi_buku"},
    {"text": "kasih saran buku dong kak", "intent": "rekomendasi_buku"},
    {"text": "buku terbaik di sini apa", "intent": "rekomendasi_buku"},
    {"text": "buku apa nih yang lagi hits", "intent": "rekomendasi_buku"},
    {"text": "mau baca buku tapi bingung pilih apa", "intent": "rekomendasi_buku"},
    {"text": "buku bagus buat pemula apa ya", "intent": "rekomendasi_buku"},
    {"text": "ada buku yang wajib dibaca ga", "intent": "rekomendasi_buku"},
    {"text": "buku favorit di perpus apa", "intent": "rekomendasi_buku"},
    {"text": "rekomendasi buku yang seru dong", "intent": "rekomendasi_buku"},
    {"text": "buku yang paling laris di sini apa", "intent": "rekomendasi_buku"},
    {"text": "saranin buku yang enak dibaca dong", "intent": "rekomendasi_buku"},
    {"text": "buku apa ya yang bikin ketagihan baca", "intent": "rekomendasi_buku"},
    {"text": "ada usul buku bagus ga", "intent": "rekomendasi_buku"},
    {"text": "buku yang lagi trending apa", "intent": "rekomendasi_buku"},
    {"text": "kasih rekomendasi buku menarik dong", "intent": "rekomendasi_buku"},
    {"text": "buku apa yang worth it dibaca", "intent": "rekomendasi_buku"},
    {"text": "mau buku bagus tapi bebas apa aja temanya", "intent": "rekomendasi_buku"},
    {"text": "buku hits apa yang kamu saranin", "intent": "rekomendasi_buku"},
    {"text": "rekomendasi bacaan yang asik dong", "intent": "rekomendasi_buku"},

    # ── prosedur_pinjam ── 30 sampel
    {"text": "gimana cara pinjam buku", "intent": "prosedur_pinjam"},
    {"text": "cara minjem buku gimana", "intent": "prosedur_pinjam"},
    {"text": "mau pinjam buku caranya gimana", "intent": "prosedur_pinjam"},
    {"text": "bisa pinjem buku di sini?", "intent": "prosedur_pinjam"},
    {"text": "gimana caranya minjem buku di libra", "intent": "prosedur_pinjam"},
    {"text": "cara pinjam buku di perpustakaan", "intent": "prosedur_pinjam"},
    {"text": "mau pinjem buku dong", "intent": "prosedur_pinjam"},
    {"text": "bagaimana prosedur peminjaman buku", "intent": "prosedur_pinjam"},
    {"text": "cara pinjam buku sekolah gimana ya", "intent": "prosedur_pinjam"},
    {"text": "minjam buku caranya apa", "intent": "prosedur_pinjam"},
    {"text": "proses pinjam buku gimana", "intent": "prosedur_pinjam"},
    {"text": "cara borrow buku di sini", "intent": "prosedur_pinjam"},
    {"text": "langkah-langkah pinjam buku apa aja", "intent": "prosedur_pinjam"},
    {"text": "gimana sih biar bisa minjem buku", "intent": "prosedur_pinjam"},
    {"text": "mau minjam buku harus ngapain", "intent": "prosedur_pinjam"},
    {"text": "syarat pinjam buku apa aja", "intent": "prosedur_pinjam"},
    {"text": "berapa lama bisa minjam buku", "intent": "prosedur_pinjam"},
    {"text": "maksimal pinjam berapa buku", "intent": "prosedur_pinjam"},
    {"text": "cara ngajuin peminjaman buku", "intent": "prosedur_pinjam"},
    {"text": "gimana biar bukunya bisa aku bawa pulang", "intent": "prosedur_pinjam"},
    {"text": "aku mau pinjam buku ini caranya gimana", "intent": "prosedur_pinjam"},
    {"text": "prosedur minjam buku di libra gimana", "intent": "prosedur_pinjam"},
    {"text": "cara reservasi buku gimana", "intent": "prosedur_pinjam"},
    {"text": "boleh pinjam buku berapa hari", "intent": "prosedur_pinjam"},
    {"text": "gimana cara ngebooking buku", "intent": "prosedur_pinjam"},
    {"text": "mau pinjam buku tapi belum tau caranya", "intent": "prosedur_pinjam"},
    {"text": "tata cara peminjaman buku dong", "intent": "prosedur_pinjam"},
    {"text": "cara minjem buku lewat aplikasi ini", "intent": "prosedur_pinjam"},
    {"text": "kalau mau pinjam buku klik apa", "intent": "prosedur_pinjam"},
    {"text": "pinjam buku di sini gimana prosesnya", "intent": "prosedur_pinjam"},

    # ── info_umum ── 30 sampel
    {"text": "perpustakaan buka jam berapa", "intent": "info_umum"},
    {"text": "jam buka perpustakaan", "intent": "info_umum"},
    {"text": "perpustakaan tutup jam berapa", "intent": "info_umum"},
    {"text": "lokasinya di mana", "intent": "info_umum"},
    {"text": "perpustakaan ada di mana", "intent": "info_umum"},
    {"text": "info perpustakaan", "intent": "info_umum"},
    {"text": "kapan perpustakaan buka", "intent": "info_umum"},
    {"text": "perpustakaan sekolah jam berapa bukanya", "intent": "info_umum"},
    {"text": "jam operasional perpustakaan", "intent": "info_umum"},
    {"text": "sekolah perpustakaannya di gedung mana", "intent": "info_umum"},
    {"text": "kontak perpustakaan ada ga", "intent": "info_umum"},
    {"text": "ada info tentang perpustakaan ini ga", "intent": "info_umum"},
    {"text": "perpustakaan buka hari apa aja", "intent": "info_umum"},
    {"text": "perpustakaan buka sabtu ga", "intent": "info_umum"},
    {"text": "hari minggu perpustakaan buka nggak", "intent": "info_umum"},
    {"text": "perpustakaan libur kapan aja", "intent": "info_umum"},
    {"text": "nomor telepon perpustakaan berapa", "intent": "info_umum"},
    {"text": "perpustakaan di lantai berapa", "intent": "info_umum"},
    {"text": "alamat perpustakaan di mana", "intent": "info_umum"},
    {"text": "sampai jam berapa perpustakaan buka", "intent": "info_umum"},
    {"text": "perpustakaan buka dari jam berapa sampai jam berapa", "intent": "info_umum"},
    {"text": "jam istirahat perpustakaan buka ga", "intent": "info_umum"},
    {"text": "perpustakaannya deket mana sih", "intent": "info_umum"},
    {"text": "perpustakaan buka pas jam istirahat ga", "intent": "info_umum"},
    {"text": "gimana cara ke perpustakaan", "intent": "info_umum"},
    {"text": "perpustakaan sekolah ada di sebelah mana", "intent": "info_umum"},
    {"text": "jadwal buka perpustakaan", "intent": "info_umum"},
    {"text": "perpustakaan masih buka sekarang ga", "intent": "info_umum"},
    {"text": "email perpustakaan apa", "intent": "info_umum"},
    {"text": "hari senin perpustakaan buka jam berapa", "intent": "info_umum"},

    # ── salam ── 30 sampel
    {"text": "halo", "intent": "salam"},
    {"text": "hai", "intent": "salam"},
    {"text": "hello", "intent": "salam"},
    {"text": "selamat pagi", "intent": "salam"},
    {"text": "selamat siang", "intent": "salam"},
    {"text": "hei libra", "intent": "salam"},
    {"text": "apa kabar", "intent": "salam"},
    {"text": "hey", "intent": "salam"},
    {"text": "halo libra", "intent": "salam"},
    {"text": "hi", "intent": "salam"},
    {"text": "permisi", "intent": "salam"},
    {"text": "selamat datang", "intent": "salam"},
    {"text": "selamat sore", "intent": "salam"},
    {"text": "selamat malam", "intent": "salam"},
    {"text": "assalamualaikum", "intent": "salam"},
    {"text": "pagi kak", "intent": "salam"},
    {"text": "hai kak", "intent": "salam"},
    {"text": "halo min", "intent": "salam"},
    {"text": "hallo", "intent": "salam"},
    {"text": "halo kak libra", "intent": "salam"},
    {"text": "hai bot", "intent": "salam"},
    {"text": "selamat pagi kak", "intent": "salam"},
    {"text": "halo semuanya", "intent": "salam"},
    {"text": "hai libra apa kabar", "intent": "salam"},
    {"text": "haloo", "intent": "salam"},
    {"text": "hi libra", "intent": "salam"},
    {"text": "salam kenal", "intent": "salam"},
    {"text": "permisi kak", "intent": "salam"},
    {"text": "selamat pagi libra", "intent": "salam"},
    {"text": "hola", "intent": "salam"},

    # ── cek_status_pinjam ── 30 sampel
    {"text": "cek status pinjaman aku", "intent": "cek_status_pinjam"},
    {"text": "status buku yang aku pinjam", "intent": "cek_status_pinjam"},
    {"text": "buku yang aku pinjam gimana statusnya", "intent": "cek_status_pinjam"},
    {"text": "pinjaman aku udah diapprove belum", "intent": "cek_status_pinjam"},
    {"text": "mau lihat status peminjaman", "intent": "cek_status_pinjam"},
    {"text": "cek pinjaman aku dong", "intent": "cek_status_pinjam"},
    {"text": "buku ku udah bisa diambil belum", "intent": "cek_status_pinjam"},
    {"text": "status request pinjem buku aku", "intent": "cek_status_pinjam"},
    {"text": "pinjaman ku statusnya apa", "intent": "cek_status_pinjam"},
    {"text": "lihat daftar buku yang aku pinjam", "intent": "cek_status_pinjam"},
    {"text": "request pinjem aku gimana", "intent": "cek_status_pinjam"},
    {"text": "buku pinjaman ku udah approved ga", "intent": "cek_status_pinjam"},
    {"text": "pinjaman aku udah disetujui belum", "intent": "cek_status_pinjam"},
    {"text": "peminjaman aku ditolak atau enggak", "intent": "cek_status_pinjam"},
    {"text": "cek dong pinjaman aku diterima ga", "intent": "cek_status_pinjam"},
    {"text": "buku yang aku ajukan gimana kabarnya", "intent": "cek_status_pinjam"},
    {"text": "status peminjaman buku aku apa", "intent": "cek_status_pinjam"},
    {"text": "udah di acc belum pinjaman aku", "intent": "cek_status_pinjam"},
    {"text": "mau tau pinjaman aku sampai mana", "intent": "cek_status_pinjam"},
    {"text": "cek buku yang lagi aku pinjam", "intent": "cek_status_pinjam"},
    {"text": "daftar peminjaman aku dong", "intent": "cek_status_pinjam"},
    {"text": "pinjaman aku masih pending ga", "intent": "cek_status_pinjam"},
    {"text": "buku yang aku pinjam kapan harus dikembalikan", "intent": "cek_status_pinjam"},
    {"text": "kapan aku harus balikin buku pinjaman", "intent": "cek_status_pinjam"},
    {"text": "buku pinjaman aku jatuh tempo kapan", "intent": "cek_status_pinjam"},
    {"text": "status peminjaman ku sekarang gimana", "intent": "cek_status_pinjam"},
    {"text": "pinjaman aku udah diproses belum", "intent": "cek_status_pinjam"},
    {"text": "lihat riwayat peminjaman aku", "intent": "cek_status_pinjam"},
    {"text": "cek apakah pinjaman aku disetujui", "intent": "cek_status_pinjam"},
    {"text": "buku aku udah boleh diambil belum", "intent": "cek_status_pinjam"},

    # ── bantuan_sistem ── 30 sampel
    {"text": "cara pakai libra", "intent": "bantuan_sistem"},
    {"text": "gimana cara make aplikasi ini", "intent": "bantuan_sistem"},
    {"text": "bantuan penggunaan libra", "intent": "bantuan_sistem"},
    {"text": "cara daftar di libra", "intent": "bantuan_sistem"},
    {"text": "cara login libra", "intent": "bantuan_sistem"},
    {"text": "libra itu apa", "intent": "bantuan_sistem"},
    {"text": "gimana cara pakai sistem ini", "intent": "bantuan_sistem"},
    {"text": "aplikasi ini buat apa", "intent": "bantuan_sistem"},
    {"text": "help cara pakai libra", "intent": "bantuan_sistem"},
    {"text": "cara register di libra", "intent": "bantuan_sistem"},
    {"text": "tutorial pakai libra dong", "intent": "bantuan_sistem"},
    {"text": "panduan penggunaan libra", "intent": "bantuan_sistem"},
    {"text": "libra ini fungsinya apa", "intent": "bantuan_sistem"},
    {"text": "cara bikin akun di libra", "intent": "bantuan_sistem"},
    {"text": "gimana cara daftar akun", "intent": "bantuan_sistem"},
    {"text": "aku baru di sini gimana caranya", "intent": "bantuan_sistem"},
    {"text": "cara ganti password libra", "intent": "bantuan_sistem"},
    {"text": "lupa password gimana", "intent": "bantuan_sistem"},
    {"text": "cara logout dari libra", "intent": "bantuan_sistem"},
    {"text": "fitur libra apa aja", "intent": "bantuan_sistem"},
    {"text": "libra bisa ngapain aja", "intent": "bantuan_sistem"},
    {"text": "cara edit profil di libra", "intent": "bantuan_sistem"},
    {"text": "gimana cara menggunakan aplikasi perpustakaan ini", "intent": "bantuan_sistem"},
    {"text": "aku bingung pakai libra", "intent": "bantuan_sistem"},
    {"text": "jelasin dong cara kerja libra", "intent": "bantuan_sistem"},
    {"text": "cara masuk ke akun libra", "intent": "bantuan_sistem"},
    {"text": "sistem ini cara pakainya gimana", "intent": "bantuan_sistem"},
    {"text": "apa itu libra", "intent": "bantuan_sistem"},
    {"text": "cara pakai aplikasi perpustakaan digital ini", "intent": "bantuan_sistem"},
    {"text": "gimana cara operasiin libra", "intent": "bantuan_sistem"},
]

REPLIES = {
    "cari_buku": (
        "Untuk mencari buku, kamu bisa gunakan fitur Pencarian di halaman Katalog. "
        "Ketik judul, nama penulis, atau topik yang kamu cari di kolom search. "
        "Kamu juga bisa filter berdasarkan kategori buku."
    ),
    "prosedur_pinjam": (
        "Cara meminjam buku di LIBRA: (1) Cari buku yang ingin dipinjam di Katalog, "
        "(2) Buka halaman detail buku, (3) Klik tombol 'Pinjam', "
        "(4) Tunggu persetujuan dari petugas perpustakaan. "
        "Kamu bisa meminjam maksimal 3 buku sekaligus."
    ),
    "info_umum": (
        "Perpustakaan SMPN 1 Kemang buka Senin-Jumat pukul 07.00-15.00 WIB. "
        "Perpustakaan berada di lantai 1 gedung sekolah. "
        "Untuk informasi lebih lanjut, hubungi petugas perpustakaan."
    ),
    "salam": (
        "Halo! Saya LIBRA, asisten perpustakaan digital SMPN 1 Kemang. "
        "Saya bisa membantu kamu mencari buku, menjelaskan cara meminjam, "
        "cek status pinjaman, atau menjawab pertanyaan seputar perpustakaan. "
        "Ada yang bisa saya bantu?"
    ),
    "rekomendasi_buku": (
        "Untuk rekomendasi buku, kamu bisa lihat panel 'Buku Serupa' di halaman detail buku, "
        "atau lihat bagian 'Rekomendasi untuk Kamu' dan 'Buku Populer' di halaman utama. "
        "Rekomendasi didasarkan pada buku yang pernah kamu pinjam."
    ),
    "cek_status_pinjam": (
        "Kamu bisa cek status peminjaman di halaman 'Status Peminjaman' setelah login. "
        "Status bisa berupa: Pending (menunggu persetujuan), Dipinjam (sudah disetujui), "
        "Dikembalikan, atau Ditolak."
    ),
    "bantuan_sistem": (
        "LIBRA adalah sistem perpustakaan digital SMPN 1 Kemang. "
        "Cara pakainya: (1) Daftar atau login dengan akun sekolah, "
        "(2) Jelajahi Katalog buku, (3) Klik buku untuk lihat detail, "
        "(4) Klik 'Pinjam' untuk mengajukan peminjaman. Ada pertanyaan lain?"
    ),
    "tidak_dimengerti": (
        "Maaf, saya belum paham pertanyaanmu. "
        "Saya hanya bisa membantu seputar perpustakaan — seperti cara mencari buku, "
        "prosedur peminjaman, jam buka, atau cara pakai aplikasi LIBRA. "
        "Coba tanya tentang salah satu topik itu ya!"
    ),
}


def get_training_data():
    """Kembalikan TRAINING_DATA — dipakai oleh classifier.py dan app.py."""
    return TRAINING_DATA
