"""
eval_rekomendasi.py — Hitung Precision@K dan Recall@K untuk rekomendasi CBF.

Mengisi Tabel 3.7 Penulisan Ilmiah. Definisi relevansi mengikuti yang tertulis
di subbab 3.8.3: sebuah buku rekomendasi dianggap relevan bila kategorinya sama
dengan buku acuan.

Metode: leave-one-out atas SELURUH katalog. Setiap buku dipakai sekali sebagai
acuan, sistem diminta K rekomendasi teratas, lalu dihitung
    Precision@K = (relevan di K teratas) / K
    Recall@K    = (relevan di K teratas) / (total buku relevan di katalog)

Recall@K pada katalog seperti ini akan bernilai kecil — itu wajar dan bukan
kesalahan: kategori Matematika berisi 52 buku, sehingga K=5 paling banyak
menjangkau 5/51 dari seluruh buku relevan. Precision@K adalah metrik yang
lebih bermakna untuk kasus ini.

Perhitungan memakai pipeline yang SAMA dengan layanan produksi (TF-IDF atas
judul + penulis + kategori, lalu cosine similarity), bukan implementasi terpisah.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pymysql
import pymysql.cursors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cbf'))
from preprocess import preprocess          # noqa: E402  — sama dengan produksi

NILAI_K = (3, 5)


def muat_katalog():
    conn = pymysql.connect(
        host=os.environ.get('LIBRA_DB_HOST', 'localhost'),
        user=os.environ.get('LIBRA_DB_USER', 'root'),
        password=os.environ.get('LIBRA_DB_PASS', ''),
        database=os.environ.get('LIBRA_DB_NAME', 'libra_db'),
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
    )
    with conn, conn.cursor() as cur:
        cur.execute(
            """SELECT b.id, b.judul, b.penulis, k.nama AS kategori_nama
               FROM buku b JOIN kategori k ON k.id = b.kategori_id
               ORDER BY b.id"""
        )
        return list(cur.fetchall())


def main():
    buku = muat_katalog()
    n = len(buku)
    print(f"Katalog: {n} buku\n")

    korpus = [preprocess(f"{b['judul']} {b['penulis']} {b['kategori_nama']}") for b in buku]
    matriks = TfidfVectorizer(min_df=1).fit_transform(korpus)
    sim = cosine_similarity(matriks)
    np.fill_diagonal(sim, -1.0)            # buku acuan tidak boleh merekomendasikan dirinya

    kategori = [b['kategori_nama'] for b in buku]
    jml_per_kategori = {k: kategori.count(k) for k in set(kategori)}

    hasil = {}
    for K in NILAI_K:
        presisi, recall = [], []
        for i in range(n):
            top = np.argsort(sim[i])[::-1][:K]
            relevan = sum(1 for j in top if kategori[j] == kategori[i])
            presisi.append(relevan / K)
            # -1 karena buku acuan tidak dihitung sebagai kandidat relevan
            total_relevan = jml_per_kategori[kategori[i]] - 1
            recall.append(relevan / total_relevan if total_relevan > 0 else 0.0)
        hasil[K] = (float(np.mean(presisi)), float(np.mean(recall)))
        print(f"K = {K}:  Precision@{K} = {hasil[K][0]:.4f}   Recall@{K} = {hasil[K][1]:.4f}")

    rata_p = np.mean([hasil[K][0] for K in NILAI_K])
    rata_r = np.mean([hasil[K][1] for K in NILAI_K])
    print(f"\nRata-rata: Precision = {rata_p:.4f}   Recall = {rata_r:.4f}")

    print("\n=== TABEL 3.7 (siap disalin ke PI) ===")
    print(f"{'Nilai K':<12}{'Precision@K':<15}{'Recall@K'}")
    for K in NILAI_K:
        print(f"K = {K:<8}{hasil[K][0]:<15.2f}{hasil[K][1]:.2f}")
    print(f"{'Rata-rata':<12}{rata_p:<15.2f}{rata_r:.2f}")


if __name__ == '__main__':
    main()
