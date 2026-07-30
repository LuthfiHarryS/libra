"""
recommender.py — CBFRecommender class untuk Content-Based Filtering.

Cara kerja:
1. __init__ memanggil _load_and_fit() — query MySQL, preprocess corpus, fit TF-IDF, precompute sim_matrix
2. Semua ini terjadi saat module di-import (di app.py: recommender = CBFRecommender())
3. Tidak ada before_first_request — Flask 3.x menghapus decorator itu (RESEARCH.md Pitfall 1)
4. Korpus dimuat ulang otomatis ketika katalog di MySQL berubah — lihat _pastikan_segar()

Kesegaran korpus:
    PHP menulis langsung ke MySQL dan tidak pernah memberi tahu Flask. Tanpa
    pemeriksaan, snapshot yang dibuat saat startup akan membeku selamanya:
    buku yang dihapus petugas tetap direkomendasikan, buku baru tidak pernah
    punya rekomendasi, dan stok pada kartu rekomendasi tidak ikut berubah.
    Karena itu setiap permintaan membandingkan sidik jari katalog yang murah
    (satu agregat) dengan sidik jari snapshot, dan memuat ulang hanya bila
    berbeda. Muat ulang penuh atas 257 buku memakan sekitar 10 ms, sehingga
    tetap jauh lebih murah daripada fit TF-IDF per permintaan.
"""
import threading

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from preprocess import preprocess
from db import get_db_connection


# SQL untuk load corpus buku saat startup (D-01, D-03)
# Hanya kolom yang relevan: id, judul, penulis, isbn, cover_url, stok_tersedia, kategori_nama
# Sinopsis TIDAK digunakan (banyak data dummy kosong, nullable — D-03)
_CORPUS_SQL = """
    SELECT b.id, b.judul, b.penulis, b.isbn, b.cover_url, b.stok_tersedia,
           k.nama AS kategori_nama
    FROM buku b
    JOIN kategori k ON b.kategori_id = k.id
"""

# Sidik jari katalog — dipakai untuk mendeteksi perubahan tanpa menarik seluruh baris.
# WAJIB memuat setiap kolom yang dikembalikan _CORPUS_SQL. Kolom yang tertinggal di
# sini berarti perubahan pada kolom itu tidak akan pernah memicu muat ulang.
# SUM bersifat bebas urutan, dan COUNT menangkap penghapusan yang kebetulan
# menghasilkan jumlah CRC sama.
_SIDIK_SQL = """
    SELECT COUNT(*) AS jumlah,
           COALESCE(SUM(CRC32(CONCAT_WS('\\t',
               b.id, b.judul, b.penulis, k.nama, b.stok_tersedia,
               COALESCE(b.isbn, ''), COALESCE(b.cover_url, '')))), 0) AS crc
    FROM buku b
    JOIN kategori k ON b.kategori_id = k.id
"""

# SQL untuk riwayat peminjaman user — personal recommendations (D-07)
# DISTINCT wajib: tabel peminjaman menyimpan satu baris per transaksi, sehingga
# buku yang dipinjam dua kali akan ikut dirata-ratakan dua kali saat centroid
# dibentuk dan bobotnya berlipat tanpa alasan. Profil pengguna didefinisikan
# sebagai rata-rata atas BUKU yang pernah dipinjam, bukan atas transaksinya.
_BORROW_HISTORY_SQL = """
    SELECT DISTINCT buku_id FROM peminjaman
    WHERE user_id = %s AND status IN ('Dipinjam', 'Dikembalikan')
"""

# SQL untuk buku populer berdasarkan COUNT peminjaman (D-14)
_POPULAR_SQL = """
    SELECT b.id, b.judul, b.penulis, b.isbn, b.cover_url, b.stok_tersedia,
           k.nama AS kategori_nama,
           COUNT(p.id) AS borrow_count
    FROM buku b
    JOIN kategori k ON b.kategori_id = k.id
    LEFT JOIN peminjaman p ON b.id = p.buku_id
    GROUP BY b.id
    ORDER BY borrow_count DESC
    LIMIT %s
"""


class CBFRecommender:
    """
    Content-Based Filtering recommender menggunakan TF-IDF + Cosine Similarity.

    TF-IDF di-fit sekali per versi katalog, bukan per permintaan. Similarity
    matrix (NxN) di-precompute agar setiap permintaan hanya membaca satu baris.
    """

    def __init__(self) -> None:
        # Seluruh state turunan korpus disimpan dalam SATU tuple dan ditukar
        # sekaligus. gunicorn menjalankan 4 thread pada satu worker; kalau tiap
        # atribut ditugaskan terpisah, thread pembaca bisa menangkap campuran
        # peta indeks lama dengan sim_matrix baru dan salah menunjuk buku.
        self._data: tuple = ()
        self._sidik: tuple | None = None      # (jumlah, crc) katalog saat snapshot dibuat
        self._kunci = threading.Lock()        # hanya melindungi proses muat ulang
        self._load_and_fit()

    # ── kompatibilitas: pemanggil lama membaca atribut ini secara langsung ──
    @property
    def books(self) -> list[dict]:
        return self._data[0]

    @property
    def book_id_to_idx(self) -> dict[int, int]:
        return self._data[1]

    @property
    def tfidf_matrix(self):
        return self._data[2]

    @property
    def sim_matrix(self) -> np.ndarray:
        return self._data[3]

    @property
    def books_loaded(self) -> int:
        return len(self._data[0])

    def _sidik_katalog(self) -> tuple:
        """Baca sidik jari katalog terkini. Satu agregat, tanpa menarik baris."""
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(_SIDIK_SQL)
                row = cursor.fetchone()
        return (row['jumlah'], int(row['crc']))

    def _pastikan_segar(self) -> None:
        """
        Muat ulang korpus bila katalog di MySQL sudah berubah sejak snapshot dibuat.

        Dipanggil di awal setiap permintaan rekomendasi. Bila MySQL sedang tidak
        terjangkau, snapshot lama tetap dipakai — rekomendasi usang jauh lebih
        baik daripada galat 500, sejalan dengan sikap fail-safe layanan ini.
        Sikap fail-fast tetap berlaku di startup: constructor tetap melempar
        exception bila database tidak bisa dibaca (D-02).
        """
        try:
            sidik = self._sidik_katalog()
        except Exception:
            return
        if sidik == self._sidik:
            return
        with self._kunci:
            # Thread lain mungkin sudah memuat ulang selagi menunggu kunci.
            if sidik == self._sidik:
                return
            try:
                self._load_and_fit(sidik)
            except Exception:
                pass  # pertahankan snapshot lama; percobaan berikutnya akan mencoba lagi

    def _load_and_fit(self, sidik: tuple | None = None) -> None:
        """
        Query MySQL -> preprocess corpus -> fit TF-IDF -> precompute sim_matrix.

        Dipanggil saat startup dan setiap kali katalog terdeteksi berubah. Jika
        MySQL down saat startup, constructor raise exception dan Flask crash —
        ini DISENGAJA (fail-fast; corpus kosong lebih buruk). (D-02)
        """
        # 1. Query MySQL untuk data buku
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(_CORPUS_SQL)
                books = list(cursor.fetchall())

        if not books:
            raise RuntimeError(
                "Corpus kosong — tidak ada buku di database libra_db. "
                "Pastikan seed.php sudah dijalankan."
            )

        # 2. Build corpus string: judul + penulis + kategori_nama (D-03)
        corpus = [
            preprocess(f"{b['judul']} {b['penulis']} {b['kategori_nama']}")
            for b in books
        ]

        # 3. Fit TF-IDF
        # min_df=1 WAJIB untuk corpus 34-35 buku — mencegah term unik dibuang (D-06, CLAUDE.md)
        vectorizer = TfidfVectorizer(min_df=1)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        # tfidf_matrix: scipy sparse CSR (N, n_features)

        # 4. Precompute full similarity matrix (NxN)
        sim_matrix = cosine_similarity(tfidf_matrix)
        # sim_matrix[i][j] = cosine similarity antara buku i dan buku j

        # 5. Build lookup dict untuk O(1) book_id -> matrix index
        book_id_to_idx = {b['id']: i for i, b in enumerate(books)}

        # 6. Tukar seluruh state sekaligus — lihat catatan di __init__
        self._data = (books, book_id_to_idx, tfidf_matrix, sim_matrix)
        # Sidik jari ditetapkan setelah data siap; kalau langkah di atas gagal,
        # sidik lama bertahan sehingga percobaan berikutnya tetap memuat ulang.
        self._sidik = sidik if sidik is not None else self._sidik_katalog()

    def get_similar_books(self, book_id: int, limit: int) -> list[dict]:
        """
        Item-based recommendation: return top-N buku paling mirip dengan book_id.
        Buku input (book_id) TIDAK masuk hasil.
        Jika book_id tidak ada di katalog, return [].
        """
        self._pastikan_segar()
        # Satu kali baca; muat ulang oleh thread lain tidak boleh mengubah
        # pasangan peta indeks dan matriks di tengah perhitungan.
        books, book_id_to_idx, _, sim_matrix = self._data

        if book_id not in book_id_to_idx:
            return []

        idx = book_id_to_idx[book_id]
        scores = sim_matrix[idx]  # shape (N,)

        # Urutkan descending, skip self, ambil top limit
        sorted_indices = np.argsort(scores)[::-1]
        results: list[dict] = []
        for i in sorted_indices:
            if i == idx:
                continue  # skip buku input itu sendiri
            if len(results) >= limit:
                break
            # WAJIB .copy() — mencegah mutasi books[i] dengan field score (Pitfall 7)
            book = books[i].copy()
            book['score'] = round(float(scores[i]), 4)
            results.append(book)
        return results

    def _get_borrowed_ids(self, user_id: int) -> list[int]:
        """Query MySQL untuk riwayat peminjaman user (D-07)."""
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(_BORROW_HISTORY_SQL, (user_id,))
                rows = cursor.fetchall()
        return [row['buku_id'] for row in rows]

    def get_personal_recs(self, user_id: int, limit: int) -> list[dict]:
        """
        Personal recommendations berdasarkan riwayat peminjaman user.

        Algoritma (D-08):
        1. Ambil buku yang pernah dipinjam user dari MySQL
        2. Hitung average TF-IDF vector (centroid user profile)
        3. Cosine similarity antara centroid dan semua buku di corpus
        4. Return top-N yang belum pernah dipinjam user (D-10)

        Fallback (D-09): jika user tidak punya riwayat, return get_popular(limit).
        """
        self._pastikan_segar()
        books, book_id_to_idx, tfidf_matrix, _ = self._data  # lihat get_similar_books

        borrowed_ids = self._get_borrowed_ids(user_id)

        # Fallback: tidak ada riwayat -> return popular (D-09)
        if not borrowed_ids:
            return self.get_popular(limit)

        # Filter ke buku yang masih ada di katalog — riwayat bisa memuat buku
        # yang sudah dihapus petugas.
        borrowed_indices = [
            book_id_to_idx[bid]
            for bid in borrowed_ids
            if bid in book_id_to_idx
        ]
        if not borrowed_indices:
            return self.get_popular(limit)

        # Hitung centroid: average TF-IDF vector dari semua buku yang dipinjam
        # tfidf_matrix sparse -> .toarray() untuk operasi mean
        borrowed_vectors = tfidf_matrix[borrowed_indices].toarray()
        user_profile = borrowed_vectors.mean(axis=0)  # shape (n_features,)

        # Cosine similarity: user_profile vs semua buku
        # reshape(1, -1) WAJIB — cosine_similarity butuh 2D array (Pitfall 5)
        scores = cosine_similarity(user_profile.reshape(1, -1), tfidf_matrix)[0]
        # scores: shape (N,)

        # Urutkan descending, eksklusi buku yang sudah dipinjam (D-10)
        sorted_indices = np.argsort(scores)[::-1]
        borrowed_set = set(borrowed_ids)
        results: list[dict] = []
        for i in sorted_indices:
            if books[i]['id'] in borrowed_set:
                continue  # sudah pernah dipinjam — skip
            if len(results) >= limit:
                break
            book = books[i].copy()
            book['score'] = round(float(scores[i]), 4)
            results.append(book)
        return results

    def get_popular(self, limit: int) -> list[dict]:
        """
        Daftar buku paling sering dipinjam berdasarkan COUNT peminjaman (D-14).

        Re-query MySQL setiap request — borrow count berubah seiring peminjaman baru.
        Response menyertakan field borrow_count tambahan (D-14).
        Buku yang tidak ada di TF-IDF corpus tetap bisa muncul di sini (D-15).
        """
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(_POPULAR_SQL, (limit,))
                return list(cursor.fetchall())
