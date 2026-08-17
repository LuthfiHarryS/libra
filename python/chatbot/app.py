"""
app.py — Flask chatbot service entry point.

Port: 5001 (terpisah dari CBF port 5000, per D-01)
Startup: load_or_train() di module-level — BUKAN before_first_request (dihapus Flask 3.0)

Endpoints:
  GET  /health  — health check (D-08)
  POST /chat    — intent classification + reply (D-02, CHAT-01)
  POST /train   — retrain + save models, returns accuracy (D-09, CHAT-05)
                  Requires X-Train-Key header matching CHATBOT_TRAIN_KEY env var.

CORS: whitelist React dev origin (bukan wildcard *)
Auth /chat: None — intranet sekolah (D-09)
Auth /train: shared secret via X-Train-Key header
"""
import os

# Dipanggil sebelum apa pun membaca os.environ di bawah — kalau tidak,
# TRAIN_KEY dan MODE sudah terlanjur dibaca saat .env belum termuat.
try:
    from chatbot.muat_env import muat_env
except ImportError:
    from muat_env import muat_env  # type: ignore[no-redef]
muat_env()

from flask import Flask, jsonify, request
from flask_cors import CORS
from pydantic import BaseModel, field_validator, ValidationError

from classifier import load_or_train, predict_intent, train_and_save
import gemini
import katalog
from dataset import get_training_data, REPLIES

app = Flask(__name__)
# Di produksi Nginx mem-proxy /chat pada origin yang sama, jadi request browser
# tidak lintas-origin dan CORS tidak terpakai. Daftar ini hanya untuk dev; origin
# produksi bisa ditambahkan lewat env var kalau suatu saat dipanggil lintas domain.
_extra_origins = [o for o in os.environ.get('CHATBOT_CORS_ORIGINS', '').split(',') if o.strip()]
CORS(app, origins=[
    'http://localhost:5173',
    'http://localhost:4173',
    'http://127.0.0.1:5173',
] + _extra_origins)

# Shared secret untuk endpoint /train. Set via env var sebelum start Flask.
# Kalau env var tidak di-set, /train auto-block (return 503) — fail-secure.
TRAIN_KEY = os.environ.get('CHATBOT_TRAIN_KEY', '')

# Cabang eksperimen. Bawaannya 'klasifikasi' — persis perilaku di main,
# sehingga menjalankan cabang ini tanpa menyetel apa pun tidak mengubah
# hasil pengukuran di naskah.
#   klasifikasi : hanya NB/SVM + katalog
#   hibrida     : Gemini hanya saat classifier menyerah (tidak_dimengerti)
#   gemini      : Gemini lebih dulu, classifier jadi cadangan
MODE = os.environ.get('CHATBOT_MODE', 'klasifikasi')

# Module-level initialization — Flask 3.x pattern (no before_first_request)
# Load joblib jika ada, else train dari dataset.py dan simpan
vectorizer, clf_lsvc, clf_nb, *_ = load_or_train(get_training_data())


class ChatRequest(BaseModel):
    message: str

    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('message cannot be empty')
        return v.strip()


@app.route('/health')
def health():
    """Health check — D-08: returns {"status": "ok"}."""
    # Mode dan kesiapan kunci ikut dilaporkan supaya saat demo kamu tahu
    # jalur mana yang sedang aktif tanpa membaca env var di server.
    return jsonify({
        "status": "ok",
        "mode": MODE,
        "gemini_siap": gemini.tersedia(),
    })


@app.route('/chat', methods=['POST'])
def chat():
    """
    Klasifikasi intent pesan Bahasa Indonesia.

    Request:  {"message": "..."}
    Response: {"intent": "prosedur_pinjam", "confidence": 0.92, "reply": "..."}

    Guardrails (per AI-SPEC Section 6):
    - clf_lsvc is None -> HTTP 503 (model not ready — should not happen dengan module-level init)
    - message kosong -> pydantic ValidationError -> HTTP 400
    - confidence < 0.5 -> intent='tidak_dimengerti' (ditangani di predict_intent, D-04)
    """
    global clf_lsvc, vectorizer

    if clf_lsvc is None:
        return jsonify({"error": "model not ready"}), 503

    try:
        req = ChatRequest.model_validate(request.get_json() or {})
    except ValidationError:
        return jsonify({"error": "message cannot be empty"}), 400

    intent, confidence, reply = predict_intent(req.message, vectorizer, clf_lsvc, REPLIES)

    # Mode 'gemini': model bahasa dicoba lebih dulu. Intent tetap dihitung
    # di atas supaya angkanya bisa dibandingkan berdampingan pada pesan
    # yang sama, bukan supaya dipakai menjawab.
    if MODE == 'gemini':
        teks = gemini.jawab(req.message)
        if teks:
            return jsonify({
                "intent": intent,
                "confidence": confidence,
                "reply": teks,
                "sumber": "gemini",
            })

    # Jawaban dinamis dari katalog. Classifier tetap yang menentukan intent;
    # tahap ini hanya mengganti template statis dengan kalimat yang menyebut
    # judul, jumlah, dan ketersediaan sebenarnya.
    #
    # Semua fungsi katalog mengembalikan None kalau database tidak terjangkau
    # atau entitasnya tidak dikenali — dalam kedua kasus itu template lama
    # tetap dipakai, sehingga chatbot tidak pernah gagal total.
    dinamis = None
    try:
        # Pertanyaan atribut sebuah judul ("X kategorinya apa", "siapa penulis
        # X") diperiksa lebih dulu, tanpa memandang intent. Classifier tidak
        # punya kelas untuk pertanyaan semacam ini dan kata penandanya condong
        # ke info_umum, sehingga tanpa langkah ini jawabannya jadi jam buka.
        # Fungsinya mengembalikan None kecuali pesan memuat kata tanya atribut
        # sekaligus judul yang benar-benar ada di katalog.
        dinamis = katalog.jawab_detail_buku(req.message)

        # Rantai berbasis intent hanya dijalankan bila langkah di atas tidak
        # menghasilkan apa-apa; kalau tidak, jawaban detail akan tertimpa.
        if dinamis is None:
            if intent == 'cari_buku':
                dinamis = katalog.jawab_cari_buku(req.message)
            elif intent == 'rekomendasi_buku':
                dinamis = katalog.jawab_rekomendasi(req.message)
            elif intent == 'prosedur_pinjam':
                dinamis = katalog.jawab_prosedur_pinjam(req.message)
            elif intent == 'info_umum':
                dinamis = katalog.jawab_info_umum(req.message)
    except Exception:
        dinamis = None

    # Mode 'hibrida': Gemini hanya dipanggil di titik yang selama ini buntu —
    # classifier tidak yakin dan katalog tidak punya jawaban. Tujuh intent
    # yang terukur di naskah tetap dilayani classifier apa adanya.
    if MODE == 'hibrida' and dinamis is None and intent == 'tidak_dimengerti':
        teks = gemini.jawab(req.message)
        if teks:
            return jsonify({
                "intent": intent,
                "confidence": confidence,
                "reply": teks,
                "sumber": "gemini",
            })

    return jsonify({
        "intent": intent,
        "confidence": confidence,
        "reply": dinamis or reply,
        "sumber": "katalog" if dinamis else "template",
    })


@app.route('/train', methods=['POST'])
def train():
    """
    Retrain kedua classifier dari dataset.py dan simpan joblib.
    Response: {"trained": true, "lsvc_accuracy": 0.95, "nb_accuracy": 0.87, "samples": 84}

    Auth: X-Train-Key header harus match env var CHATBOT_TRAIN_KEY.
          Kalau TRAIN_KEY tidak di-set di env, semua request ditolak (fail-secure).
    Akurasi: train_test_split 80/20 (bukan cross_val_score — nested CV bug, Pitfall 1)
    """
    if not TRAIN_KEY:
        return jsonify({"error": "training disabled — CHATBOT_TRAIN_KEY env var not set"}), 503

    provided = request.headers.get('X-Train-Key', '')
    # constant-time compare untuk hindari timing attack
    import hmac
    if not hmac.compare_digest(provided, TRAIN_KEY):
        return jsonify({"error": "unauthorized"}), 401

    global vectorizer, clf_lsvc, clf_nb

    dataset = get_training_data()
    vectorizer, clf_lsvc, clf_nb, lsvc_acc, nb_acc, n_samples = train_and_save(dataset)

    return jsonify({
        "trained": True,
        "lsvc_accuracy": lsvc_acc,
        "nb_accuracy": nb_acc,
        "samples": n_samples
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
