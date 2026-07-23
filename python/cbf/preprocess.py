"""
preprocess.py — Indonesian text preprocessing untuk TF-IDF corpus.

CRITICAL: Fungsi preprocess() ini IDENTIK digunakan untuk:
1. Fit TF-IDF corpus saat startup (di recommender.py _load_and_fit)
2. Inference/query preprocessing jika ada (future use)
Jangan buat versi lain dari fungsi ini. (CLAUDE.md pitfall #2)
"""
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Inisialisasi SEKALI di module-level — JANGAN di dalam fungsi preprocess().
# StemmerFactory() memuat dictionary besar; konstruksi di dalam fungsi
# menyebabkan startup 60+ detik. (RESEARCH.md Pitfall 4)
_factory = StemmerFactory()
_stemmer = _factory.create_stemmer()

_sw_factory = StopWordRemoverFactory()
_stopword_remover = _sw_factory.create_stop_word_remover()


def preprocess(text: str) -> str:
    """
    Preprocess teks Bahasa Indonesia untuk TF-IDF.
    Urutan per D-04: lowercase -> hapus punctuation -> stemming -> hapus stopwords.
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)   # hapus punctuation, pertahankan alphanumeric + spasi
    text = _stemmer.stem(text)
    text = _stopword_remover.remove(text)
    text = re.sub(r'\s+', ' ', text).strip()  # normalisasi whitespace berlebih
    return text
