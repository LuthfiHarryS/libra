"""
photo_cover_map2.py — Pemetaan manual tahap 2: sel hasil split_grid_crops.py -> judul.

Sama seperti photo_cover_map.py, tapi sumbernya crops2_index.json (sel-sel hasil
pemecahan foto grid).

Sel yang dilewati: hasil potong yang mengenai badan buku (bukan sela), sel berisi
lantai/tangan, dan sampul yang terpotong sampai berbentuk lanskap — di grid katalog
yang potret, sampul lanskap terlihat lebih buruk daripada placeholder.
Contoh yang sengaja dibuang karena alasan itu: Peradaban Turki, Peradaban Thailand.

rot = derajat putaran searah jarum jam agar sampul tegak.
"""

# indeks sel (crops2_index.json) -> (judul, rot)
PETA2 = {
    2:   ("Belajar Mudah Jarimatika", 180),
    8:   ("Sudut dan Luas Segi Banyak", 0),
    9:   ("Sistem Pernapasan Makhluk Hidup", 180),
    10:  ("Hewan Berbahaya di Sekitar Kita", 180),
    11:  ("Memahami Unsur, Senyawa, dan Campuran", 0),
    15:  ("Mengenal Herbarium Flora", 0),
    17:  ("Sains untuk Pemula 9: Mari Bermain Elektromagnet", 180),
    26:  ("Senam Aerobik", 0),
    30:  ("Permainan Bulu Tangkis", 0),
    40:  ("Langkah Menjadi Pemain Basket Hebat", 0),
    41:  ("Pola Gerak dalam Senam 2", 0),
    51:  ("Industrialisasi", 0),
    58:  ("Operasi Bentuk Aljabar", 0),
    63:  ("Patepung di Bandung", 0),
    64:  ("Si Paser", 0),
    65:  ("Nu Ngageugeuh Legok Kiara", 180),
    66:  ("Ask Tinkerbell", 180),
    68:  ("Bahtera Penyelamat Nabi Nuh a.s", 0),
    69:  ("Pandangan Hidup Manusia", 0),
    70:  ("Mahir Bahasa Arab", 0),
    71:  ("Subhanallah Allah Menciptakan Lalat", 0),
    76:  ("Narasi-Narasi Memecah Sunyi", 0),
    77:  ("Sejarah Khulafaurrasyidin", 0),
    79:  ("Subhanallah Allah Menciptakan Lebah", 180),
    81:  ("Tokoh Perdamaian Dunia", 0),
    85:  ("Belajar Memahami Keuangan Pribadi Sejak Dini", 0),
    87:  ("Ayo Siaga Bencana!", 0),
    90:  ("Mengenal Istilah Komputer A-Z", 0),
    91:  ("The Snake and the Man and Other Stories", 0),
    92:  ("The Mouse Deer Cheats the Farmer and Other Stories", 0),
    94:  ("Baby Squirrel Learnt A Lesson and Other Stories", 0),
    102: ("A Shepherd's Dream", 0),
}
