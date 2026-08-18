"""
app.py — layanan chatbot LIBRA, cabang gemini-saja.

Berbeda dari main dan dari cabang eksperimen-gemini: classifier intent
(Naive Bayes/SVM) tidak ikut menentukan jawaban sama sekali. Seluruh
pesan dijawab Gemini, dengan data katalog sebagai penambat.

Alasannya satu kasus nyata: "Negeri 5 Menara buku tentang apa" tertangkap
sebagai intent rekomendasi_buku, katalog menjawabnya dengan daftar buku
terpopuler, dan karena katalog dianggap berhasil, jalur cadangan tidak
pernah dipakai. Selama classifier ikut memutuskan, jawaban yakin tetapi
salah seperti itu akan selalu bisa terjadi.

Angka akurasi di naskah Penulisan Ilmiah mengukur classifier, jadi naskah
itu merujuk pada branch main — bukan pada cabang ini.

Port: 5001
Endpoint:
  GET  /health  — status layanan
  POST /chat    — jawaban Gemini yang ditambatkan ke katalog
"""
import os

# Dipanggil sebelum apa pun membaca os.environ di bawah.
try:
    from chatbot.muat_env import muat_env
except ImportError:
    from muat_env import muat_env  # type: ignore[no-redef]
muat_env()

from flask import Flask, jsonify, request
from flask_cors import CORS
from pydantic import BaseModel, field_validator, ValidationError

try:
    from chatbot import gemini
except ImportError:
    import gemini  # type: ignore[no-redef]

app = Flask(__name__)
_extra_origins = [o for o in os.environ.get('CHATBOT_CORS_ORIGINS', '').split(',') if o.strip()]
CORS(app, origins=[
    'http://localhost:5173',
    'http://localhost:4173',
    'http://127.0.0.1:5173',
] + _extra_origins)

# Dipakai saat Gemini tidak bisa dihubungi. Cabang ini tidak punya jalur
# cadangan lain, jadi yang bisa dilakukan hanyalah mengaku terus terang —
# bukan menebak jawaban.
PESAN_GAGAL = ("Maaf, asisten LIBRA sedang tidak bisa dihubungi. "
               "Coba lagi sebentar lagi, atau tanyakan langsung ke petugas "
               "perpustakaan ya.")


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
    return jsonify({
        "status": "ok",
        "mode": "gemini-saja",
        "gemini_siap": gemini.tersedia(),
    })


@app.route('/chat', methods=['POST'])
def chat():
    """
    Request:  {"message": "..."}
    Response: {"reply": "...", "sumber": "gemini" | "gagal"}

    Bentuk balasan mempertahankan kunci intent dan confidence supaya
    ChatWidget yang sudah ada tidak perlu diubah. Keduanya tidak lagi
    berasal dari classifier: cabang ini tidak menjalankannya.
    """
    try:
        req = ChatRequest.model_validate(request.get_json() or {})
    except ValidationError:
        return jsonify({"error": "message cannot be empty"}), 400

    teks = gemini.jawab(req.message)

    return jsonify({
        "intent": "gemini",
        "confidence": 1.0 if teks else 0.0,
        "reply": teks or PESAN_GAGAL,
        "sumber": "gemini" if teks else "gagal",
    })


@app.route('/train', methods=['POST'])
def train():
    """Tidak ada model yang dilatih di cabang ini — lihat branch main."""
    return jsonify({
        "error": "tidak tersedia di cabang gemini-saja; classifier hanya ada di main"
    }), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
