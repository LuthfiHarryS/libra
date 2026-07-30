"""
test_kesegaran.py — regresi layanan CBF: kesegaran korpus dan bobot profil.

Latar: korpus, matriks TF-IDF, dan matriks kemiripan dulu hanya dibangun sekali
saat proses Flask dijalankan. PHP menulis langsung ke MySQL tanpa memberi tahu
Flask, sehingga snapshot itu membeku dan menimbulkan tiga gejala di produksi:
buku yang dihapus tetap direkomendasikan, buku baru tidak pernah punya
rekomendasi, dan stok pada kartu rekomendasi tidak ikut berubah.

Menjalankan:
    python test_kesegaran.py          (butuh MySQL hidup dan libra_db terisi)

Catatan: kedua buku uji sengaja dibuat kembar — teks korpusnya identik sehingga
kemiripannya 1,0 dan yang satu dijamin menjadi peringkat teratas bagi yang lain.
Tanpa itu, buku uji berjudul unik tidak masuk daftar teratas sama sekali dan
pengujian lulus secara palsu.
"""
import sys
import time

from db import get_db_connection
from recommender import CBFRecommender

JUDUL = '__ZZTEST Matematika Aljabar Geometri__'
KEMBAR = '__ZZTEST Matematika Aljabar Geometri Kembar__'


def jalankan(sql, args=None, ambil=False):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute(sql, args or ())
            hasil = cur.fetchall() if ambil else None
        conn.commit()
    return hasil


def buat_buku(judul, stok=5):
    kid = jalankan("SELECT id FROM kategori LIMIT 1", ambil=True)[0]['id']
    jalankan("""INSERT INTO buku (kategori_id, judul, penulis, stok_total, stok_tersedia)
                VALUES (%s, %s, 'Penulis Uji Matematika', %s, %s)""", (kid, judul, stok, stok))
    return jalankan("SELECT id FROM buku WHERE judul = %s", (judul,), ambil=True)[0]['id']


def bersihkan():
    jalankan("DELETE FROM buku WHERE judul IN (%s, %s)", (JUDUL, KEMBAR))


def id_hasil(rekomendasi):
    return {b['id'] for b in rekomendasi}


hasil = []


def periksa(nama, lulus, detail):
    hasil.append(lulus)
    print(f"  [{'LULUS' if lulus else 'GAGAL'}] {nama}\n         {detail}")


def kasus_buku_dihapus():
    """Buku yang dihapus petugas tidak boleh muncul lagi di rekomendasi."""
    print('\nKasus 1 — buku dihapus setelah layanan berjalan')
    try:
        bid = buat_buku(JUDUL)
        kid = buat_buku(KEMBAR)
        r = CBFRecommender()
        assert bid in id_hasil(r.get_similar_books(kid, 5)), \
            'prasyarat gagal: buku kembar seharusnya saling menjadi peringkat teratas'
        jalankan("DELETE FROM buku WHERE id = %s", (bid,))
        muncul = bid in id_hasil(r.get_similar_books(kid, 5))
        periksa('buku terhapus tidak boleh direkomendasikan', not muncul,
                f'id {bid} {"MASIH muncul" if muncul else "tidak muncul"} di rekomendasi kembarnya')
    finally:
        bersihkan()


def kasus_buku_baru():
    """Buku yang ditambahkan setelah layanan berjalan harus dikenali."""
    print('\nKasus 2 — buku ditambah setelah layanan berjalan')
    try:
        r = CBFRecommender()
        bid = buat_buku(JUDUL)
        rekomendasi = r.get_similar_books(bid, 5)
        periksa('buku baru harus punya rekomendasi', len(rekomendasi) > 0,
                f'get_similar_books({bid}) mengembalikan {len(rekomendasi)} hasil')
    finally:
        bersihkan()


def kasus_stok_berubah():
    """Kartu rekomendasi menampilkan Tersedia/Habis dari stok_tersedia."""
    print('\nKasus 3 — stok berubah setelah layanan berjalan')
    try:
        bid = buat_buku(JUDUL, stok=5)
        kid = buat_buku(KEMBAR, stok=5)
        r = CBFRecommender()
        jalankan("UPDATE buku SET stok_tersedia = 0 WHERE id = %s", (bid,))
        kartu = [b for b in r.get_similar_books(kid, 5) if b['id'] == bid]
        stok = kartu[0]['stok_tersedia'] if kartu else None
        periksa('stok pada kartu rekomendasi harus mutakhir', stok == 0,
                f'stok_tersedia terbaca {stok}, seharusnya 0')
    finally:
        bersihkan()


def kasus_riwayat_ganda():
    """Buku yang dipinjam dua kali tetap satu buku bagi profil pengguna.

    Tabel peminjaman menyimpan satu baris per transaksi. Tanpa DISTINCT, buku
    yang dipinjam ulang ikut dirata-ratakan dua kali saat centroid dibentuk,
    sehingga kategorinya berbobot ganda tanpa dasar.
    """
    print('\nKasus 4 — buku yang sama dipinjam dua kali')
    nama = '__ZZTEST riwayat ganda'
    jalankan("DELETE p FROM peminjaman p JOIN users u ON u.id = p.user_id "
             "WHERE u.nama = %s", (nama,))
    jalankan("DELETE FROM users WHERE nama = %s", (nama,))
    try:
        jalankan("INSERT INTO users (nama, username, password, role) "
                 "VALUES (%s, %s, 'x', 'siswa')", (nama, nama))
        uid = jalankan("SELECT id FROM users WHERE nama = %s", (nama,), ambil=True)[0]['id']
        buku = [b['id'] for b in jalankan("SELECT id FROM buku LIMIT 3", ambil=True)]
        for bid in [buku[0], buku[0], buku[1], buku[2]]:      # buku pertama dua kali
            jalankan("INSERT INTO peminjaman (user_id, buku_id, status) "
                     "VALUES (%s, %s, 'Dikembalikan')", (uid, bid))

        riwayat = CBFRecommender()._get_borrowed_ids(uid)
        unik = len(riwayat) == len(set(riwayat))
        periksa('tiap buku hanya dihitung sekali pada profil', unik,
                f'4 baris peminjaman atas 3 buku -> _get_borrowed_ids memberi '
                f'{len(riwayat)} id: {riwayat}')
    finally:
        jalankan("DELETE p FROM peminjaman p JOIN users u ON u.id = p.user_id "
                 "WHERE u.nama = %s", (nama,))
        jalankan("DELETE FROM users WHERE nama = %s", (nama,))


if __name__ == '__main__':
    bersihkan()  # buang sisa percobaan yang gagal di tengah jalan
    kasus_buku_dihapus()
    kasus_buku_baru()
    kasus_stok_berubah()
    kasus_riwayat_ganda()

    mulai = time.perf_counter()
    r = CBFRecommender()
    print(f'\nMuat + fit TF-IDF atas {r.books_loaded} buku: '
          f'{(time.perf_counter() - mulai) * 1000:.0f} ms')

    lulus = sum(hasil)
    print(f'\n{lulus}/{len(hasil)} lulus')
    sys.exit(0 if lulus == len(hasil) else 1)
