"""
preprocess.py — Indonesian text preprocessing untuk chatbot intent classification.

CRITICAL: Fungsi preprocess() ini IDENTIK digunakan untuk:
1. Build TF-IDF corpus saat training (di classifier.py train_and_save)
2. Inference/query preprocessing saat prediksi intent (di classifier.py predict_intent)
Jangan buat versi lain dari fungsi ini — satu fungsi, satu file.
"""
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Inisialisasi SEKALI di module-level — JANGAN di dalam fungsi preprocess().
# StemmerFactory() memuat dictionary besar; konstruksi di dalam fungsi
# menyebabkan latency 60+ detik per request. (Critical Pitfall 7)
_factory = StemmerFactory()
_stemmer = _factory.create_stemmer()

_sw_factory = StopWordRemoverFactory()
_stopword_remover = _sw_factory.create_stop_word_remover()


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
