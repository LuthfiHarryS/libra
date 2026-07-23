"""
app.py — Flask CBF microservice entry point.

Port: 5000 (hardcoded, sesuai CLAUDE.md stack)
Startup: CBFRecommender() di module-level — BUKAN di before_first_request
         (decorator itu dihapus di Flask 3.0, RESEARCH.md Pitfall 1)

Endpoint:
  GET /health                              — status + jumlah buku di corpus
  GET /recommend?book_id=N&limit=N         — item-based recommendations (REC-01)
  GET /recommend/personal?user_id=N&limit=N — personal recommendations (REC-02)
  GET /popular?limit=N                     — buku populer by borrow count (REC-03)

Response format: simple JSON array (D-12), full book object + score (D-11)
Input validation: int() cast + range check untuk semua parameter (T-3-01)
"""
from flask import Flask, jsonify, request
from flask_cors import CORS

from recommender import CBFRecommender

app = Flask(__name__)
CORS(app)

# Module-level initialization — runs ONCE saat Python mengimport app.py
# Jika MySQL down, CBFRecommender() raise exception -> Flask crash -> fail-fast (D-02)
recommender = CBFRecommender()


@app.route('/health')
def health():
    """Health check — returns status dan jumlah buku yang berhasil di-load (D-13)."""
    return jsonify({
        "status": "ok",
        "books_loaded": recommender.books_loaded
    })


@app.route('/recommend')
def recommend():
    """
    Item-based recommendations menggunakan precomputed cosine similarity matrix.

    Query params:
      book_id (int, required): ID buku yang dicari rekomendasinya
      limit   (int, optional): Jumlah rekomendasi, default 5, max 20

    Returns: JSON array of book objects with score field, excludes book_id itself.
    Mitigation T-3-01: int() cast + range validation sebelum diproses.
    """
    try:
        book_id = int(request.args.get('book_id', 0))
        limit = min(int(request.args.get('limit', 5)), 20)
    except (ValueError, TypeError):
        return jsonify({"error": "invalid parameters — book_id and limit must be integers"}), 400

    if book_id <= 0:
        return jsonify({"error": "book_id required and must be positive integer"}), 400

    results = recommender.get_similar_books(book_id, limit)
    return jsonify(results)


@app.route('/recommend/personal')
def recommend_personal():
    """
    Personal recommendations berdasarkan riwayat peminjaman user.
    Fallback ke buku populer jika user tidak punya riwayat (D-09).

    Query params:
      user_id (int, required): ID user
      limit   (int, optional): Jumlah rekomendasi, default 5, max 20

    Returns: JSON array of book objects with score field (or borrow_count for fallback).
    Mitigation T-3-01: int() cast + range validation.
    """
    try:
        user_id = int(request.args.get('user_id', 0))
        limit = min(int(request.args.get('limit', 5)), 20)
    except (ValueError, TypeError):
        return jsonify({"error": "invalid parameters — user_id and limit must be integers"}), 400

    if user_id <= 0:
        return jsonify({"error": "user_id required and must be positive integer"}), 400

    results = recommender.get_personal_recs(user_id, limit)
    return jsonify(results)


@app.route('/popular')
def popular():
    """
    Daftar buku paling populer berdasarkan frekuensi peminjaman.

    Query params:
      limit (int, optional): Jumlah buku, default 10, max 50

    Returns: JSON array of book objects with borrow_count field.
    Mitigation T-3-01: int() cast dengan fallback ke default jika invalid.
    """
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
    except (ValueError, TypeError):
        limit = 10  # fallback ke default — /popular tidak butuh param wajib

    results = recommender.get_popular(limit)
    return jsonify(results)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
