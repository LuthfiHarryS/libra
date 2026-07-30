"""
photo_cover_map.py — Pemetaan manual: potongan hasil crop_book_photos.py -> judul buku.

Dibuat dengan membaca contact sheet potongan satu per satu. Hanya potongan yang
berisi SATU buku dan judulnya terbaca jelas yang dipetakan; potongan berisi grid
beberapa buku, hasil zoom yang blur, atau foto lantai/tangan sengaja dilewati.

rot = derajat putaran SEARAH JARUM JAM agar sampul tegak
      (0, 90, 180, 270). Banyak foto diambil terbalik atau menyamping.

Dipakai oleh apply_photo_covers.py.
"""

# indeks potongan -> (judul persis seperti di books_from_notes.json, rot)
PETA = {
    0:   ("Persamaan dan Pertidaksamaan Linear Satu Variabel", 180),
    1:   ("Mengenal Persen dan Permil", 0),
    3:   ("Mengenal Garis-Garis pada Segitiga", 0),
    5:   ("Ayo Mengenal Diagram", 180),
    6:   ("Menggambar dengan Jangka", 0),
    8:   ("Mengenal Bangun dan Belajar Pecahan", 0),
    10:  ("Mengenal Himpunan dan Diagram Venn", 0),
    13:  ("Membuat Jaring-Jaring Bangun Ruang", 0),
    16:  ("Mengenal Gerak", 180),
    20:  ("Bahan Kimia Di Sekitar Kita", 0),
    21:  ("Berhitung Cepat dengan Metode Horisontal (Metris)", 0),
    24:  ("Energi Kalor", 270),
    25:  ("Mengenal Mata dan Cara Merawatnya", 0),
    26:  ("Peranan Mikroorganisme dalam Kehidupan Manusia", 0),
    27:  ("Dampak Rumah Kaca", 180),
    28:  ("Atmosfer dan Pengaruhnya terhadap Kehidupan", 0),
    29:  ("Memahami Sains di Sekitar Rumah", 0),
    30:  ("Ikatan Kimia", 0),
    32:  ("Berpetualang di Dasar Laut", 270),
    36:  ("Mengenal Moluska", 0),
    39:  ("Mengenal Olahraga Sepatu Roda", 270),
    40:  ("Futsal: Sepak Bola dalam Ruangan", 180),
    41:  ("Tanaman Penghasil Bahan Bakar", 180),
    43:  ("Mengenal Manfaat Hutan Bakau", 270),
    44:  ("Permainan Tenis Lapangan", 0),
    46:  ("Budaya Hidup Sehat untuk Anak", 0),
    47:  ("Mengenal Olahraga Balap Sepeda", 180),
    48:  ("Bermain Tenis Meja", 180),
    50:  ("Kebugaran dan Kesehatan", 0),
    51:  ("Dasar-Dasar Senam", 180),
    57:  ("Pola Gerak dalam Senam 3", 270),
    58:  ("Atletik Cabang Lempar", 270),
    60:  ("Jenis-Jenis Pekerjaan", 180),
    61:  ("Industri Kecil dan Menengah", 180),
    62:  ("Mari Mengenal Lambang Matematika", 0),
    63:  ("Asyiknya Bermain Bangun Segitiga", 0),
    65:  ("Mengenal Laut Indonesia", 0),
    66:  ("Narkoba: Bahaya dan Upaya Pencegahannya", 0),
    67:  ("Indahnya Hujan dan Pelangi", 180),
    68:  ("Tanaman: Proyek Sains yang Menarik", 180),
    69:  ("Seri Jelajah Sains: Antariksa", 180),
    70:  ("Cakrawala Sains: Serba Serbi Energi", 180),
    71:  ("Struktur Luar Tumbuhan", 180),
    72:  ("Gaya dan Hukum Newton", 180),
    73:  ("Keliling dan Luas Bangun Datar", 0),
    75:  ("Ayo Mempelajari Lumut", 0),
    76:  ("Asyiknya Bermain Kubus dan Balok", 0),
    77:  ("Persamaan Kuadrat", 0),
    79:  ("Mengenal Bilangan", 0),
    80:  ("Mengenal Hewan Australia 2", 0),
    81:  ("Belajar Matematika dari Lingkungan Sekitar", 0),
    92:  ("Kutukan Firaun", 0),
    94:  ("Berpikir dengan IQ, EQ, dan SQ", 0),
    96:  ("Subhanallah Allah Menciptakan Burung", 0),
    102: ("Raden Fatah", 0),
    104: ("Lord of the Shadows: Penguasa Kegelapan", 0),
    106: ("Kreasiku Seri Tata Surya", 0),
    108: ("The Mouse Deer and His Magic Flute and Other Stories", 0),
}

# Potongan yang isinya buku yang sama dengan entri di atas — tidak dipakai,
# dicatat supaya jelas bahwa itu memang duplikat, bukan terlewat.
DUPLIKAT = {22: 20, 23: 21, 42: 32, 52: 44, 54: 46, 100: 96}
