"""
recommender.py — CBFRecommender class untuk Content-Based Filtering.

Cara kerja:
1. __init__ memanggil _load_and_fit() — query MySQL, preprocess corpus, fit TF-IDF, precompute sim_matrix
2. Semua ini terjadi saat module di-import (di app.py: recommender = CBFRecommender())
3. Tidak ada before_first_request — Flask 3.x menghapus decorator itu (RESEARCH.md Pitfall 1)
"""
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

# SQL untuk riwayat peminjaman user — personal recommendations (D-07)
_BORROW_HISTORY_SQL = """
    SELECT buku_id FROM peminjaman
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

    TF-IDF di-fit SEKALI saat __init__ dipanggil (module-level di app.py).
    Similarity matrix (NxN) di-precompute untuk efisiensi request.
    """

    def __init__(self) -> None:
        self.books: list[dict] = []           # list dicts dari MySQL (ordered by query result)
        self.book_id_to_idx: dict[int, int] = {}  # {book_id: matrix_row_index}
        self.tfidf_matrix = None              # scipy sparse CSR matrix (N, n_features)
        self.sim_matrix: np.ndarray | None = None  # ndarray (N, N), precomputed
        self.books_loaded: int = 0
        self._load_and_fit()

    def _load_and_fit(self) -> None:
        """
        Query MySQL -> preprocess corpus -> fit TF-IDF -> precompute sim_matrix.

        Dipanggil sekali saat startup. Jika MySQL down, constructor raise exception
        dan Flask crash — ini DISENGAJA (fail-fast; corpus kosong lebih buruk). (D-02)
        """
        # 1. Query MySQL untuk data buku
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(_CORPUS_SQL)
                self.books = list(cursor.fetchall())

        if not self.books:
            raise RuntimeError(
                "Corpus kosong — tidak ada buku di database libra_db. "
                "Pastikan seed.php sudah dijalankan."
            )

        # 2. Build corpus string: judul + penulis + kategori_nama (D-03)
        corpus = [
            preprocess(f"{b['judul']} {b['penulis']} {b['kategori_nama']}")
            for b in self.books
        ]

        # 3. Fit TF-IDF
        # min_df=1 WAJIB untuk corpus 34-35 buku — mencegah term unik dibuang (D-06, CLAUDE.md)
        vectorizer = TfidfVectorizer(min_df=1)
        self.tfidf_matrix = vectorizer.fit_transform(corpus)
        # tfidf_matrix: scipy sparse CSR (N, n_features)

        # 4. Precompute full similarity matrix (NxN)
        self.sim_matrix = cosine_similarity(self.tfidf_matrix)
        # sim_matrix[i][j] = cosine similarity antara buku i dan buku j

        # 5. Build lookup dict untuk O(1) book_id -> matrix index
        self.book_id_to_idx = {b['id']: i for i, b in enumerate(self.books)}
        self.books_loaded = len(self.books)

    def get_similar_books(self, book_id: int, limit: int) -> list[dict]:
        """
        Item-based recommendation: return top-N buku paling mirip dengan book_id.
        Buku input (book_id) TIDAK masuk hasil.
        Jika book_id tidak ada di corpus (buku ditambah setelah startup), return [].
        """
        if book_id not in self.book_id_to_idx:
            return []

        idx = self.book_id_to_idx[book_id]
        scores = self.sim_matrix[idx]  # shape (N,)

        # Urutkan descending, skip self, ambil top limit
        sorted_indices = np.argsort(scores)[::-1]
        results: list[dict] = []
        for i in sorted_indices:
            if i == idx:
                continue  # skip buku input itu sendiri
            if len(results) >= limit:
                break
            # WAJIB .copy() — mencegah mutasi self.books[i] dengan field score (Pitfall 7)
            book = self.books[i].copy()
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
        borrowed_ids = self._get_borrowed_ids(user_id)

        # Fallback: tidak ada riwayat -> return popular (D-09)
        if not borrowed_ids:
            return self.get_popular(limit)

        # Filter ke buku yang ada di corpus (buku mungkin ditambah setelah startup)
        borrowed_indices = [
            self.book_id_to_idx[bid]
            for bid in borrowed_ids
            if bid in self.book_id_to_idx
        ]
        if not borrowed_indices:
            return self.get_popular(limit)

        # Hitung centroid: average TF-IDF vector dari semua buku yang dipinjam
        # tfidf_matrix sparse -> .toarray() untuk operasi mean
        borrowed_vectors = self.tfidf_matrix[borrowed_indices].toarray()
        user_profile = borrowed_vectors.mean(axis=0)  # shape (n_features,)

        # Cosine similarity: user_profile vs semua buku
        # reshape(1, -1) WAJIB — cosine_similarity butuh 2D array (Pitfall 5)
        scores = cosine_similarity(user_profile.reshape(1, -1), self.tfidf_matrix)[0]
        # scores: shape (N,)

        # Urutkan descending, eksklusi buku yang sudah dipinjam (D-10)
        sorted_indices = np.argsort(scores)[::-1]
        borrowed_set = set(borrowed_ids)
        results: list[dict] = []
        for i in sorted_indices:
            if self.books[i]['id'] in borrowed_set:
                continue  # sudah pernah dipinjam — skip
            if len(results) >= limit:
                break
            book = self.books[i].copy()
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
