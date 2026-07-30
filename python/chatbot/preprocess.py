"""
preprocess.py — Indonesian text preprocessing untuk chatbot intent classification.

CRITICAL: Fungsi preprocess() ini IDENTIK digunakan untuk:
1. Build TF-IDF corpus saat training (di classifier.py train_and_save)
2. Inference/query preprocessing saat prediksi intent (di classifier.py predict_intent)
Jangan buat versi lain dari fungsi ini — satu fungsi, satu file.
"""
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import (
    StopWordRemoverFactory, StopWordRemover, ArrayDictionary
)

# Inisialisasi SEKALI di module-level — JANGAN di dalam fungsi preprocess().
# StemmerFactory() memuat dictionary besar; konstruksi di dalam fungsi
# menyebabkan latency 60+ detik per request. (Critical Pitfall 7)
_factory = StemmerFactory()
_stemmer = _factory.create_stemmer()

# Kata yang DIPERTAHANKAN meski ada di daftar stopword Sastrawi (809 kata).
#
# Sastrawi dirancang untuk information retrieval, di mana kata tanya dan sapaan
# memang tidak informatif. Untuk klasifikasi intent justru sebaliknya: kata-kata
# inilah yang membedakan satu intent dari yang lain.
#
# Ditemukan saat pengujian: preprocess("halo") menghasilkan string kosong,
# sehingga vektor TF-IDF-nya nol dan model hanya bisa menebak acak — intent
# 'salam' mustahil dikenali dari sapaan satu kata.
#
#   sapaan          -> sinyal tunggal intent 'salam'
#   kata tanya      -> "kapan" (info_umum), "berapa" (prosedur_pinjam),
#                      "bagaimana" (prosedur_pinjam), "siapa" (info_umum)
#   penanda status  -> "sudah"/"belum" membedakan cek_status_pinjam
#   negasi          -> "tidak"/"bukan" pada pertanyaan ketersediaan koleksi
_KATA_DIPERTAHANKAN = {
    'halo', 'hai', 'hello',
    'ada', 'apa', 'siapa', 'kapan', 'mana', 'bagaimana', 'berapa', 'kenapa',
    'tidak', 'bukan', 'belum', 'sudah',
    'boleh', 'bisa', 'mau', 'lama', 'banyak', 'baru',
}

_sw_factory = StopWordRemoverFactory()
_stopwords = [w for w in _sw_factory.get_stop_words()
              if w not in _KATA_DIPERTAHANKAN]
_stopword_remover = StopWordRemover(ArrayDictionary(_stopwords))


def preprocess(text: str) -> str:
    """
    Preprocess teks Bahasa Indonesia untuk TF-IDF intent classification.

    Urutan: lowercase -> hapus punctuation -> stemming (PySastrawi) -> hapus stopwords -> normalize whitespace.

    CRITICAL: fungsi ini dipakai identik saat training DAN inference chatbot — jangan buat versi lain.
    Import path: `from Sastrawi.Stemmer.StemmerFactory import StemmerFactory` (capital P dan S di PySastrawi).
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)   # hapus punctuation, pertahankan alphanumeric + spasi
    text = _stemmer.stem(text)
    text = _stopword_remover.remove(text)
    text = re.sub(r'\s+', ' ', text).strip()  # normalisasi whitespace berlebih
    return text
