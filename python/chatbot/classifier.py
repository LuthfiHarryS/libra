"""
classifier.py — Train, load, dan predict untuk chatbot intent classification.

Menggunakan:
- CalibratedClassifierCV(LinearSVC(max_iter=1000), cv=3) sebagai classifier utama
- MultinomialNB() sebagai classifier pembanding akademik
- TfidfVectorizer(min_df=1, ngram_range=(1,2), sublinear_tf=True)

CRITICAL — Training pattern:
  1. Fit vectorizer pada SEMUA data
  2. Split 80/20 (stratified) untuk accuracy reporting
  3. Fit eval models pada train -> evaluate pada test
  4. Refit production models pada FULL data -> simpan joblib

DILARANG: cross_val_score(CalibratedClassifierCV(..., cv=3), X_vec, y, cv=3)
  -> nested CV gagal pada corpus kecil (Pitfall 1, verified live)
"""
import os
import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Support both package-mode (pytest / import chatbot.classifier) and
# script-mode (python app.py from python/chatbot/ directory).
try:
    from chatbot.preprocess import preprocess
except ImportError:
    from preprocess import preprocess  # type: ignore[no-redef]

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR      = os.path.join(BASE_DIR, 'models')
VECTORIZER_PATH = os.path.join(MODELS_DIR, 'vectorizer.joblib')
LSVC_PATH       = os.path.join(MODELS_DIR, 'model_lsvc.joblib')
NB_PATH         = os.path.join(MODELS_DIR, 'model_nb.joblib')

THRESHOLD = 0.5

# Kosakata domain perpustakaan, dalam bentuk SUDAH DI-STEM oleh preprocess().
#
# Ambang keyakinan saja tidak cukup menolak pertanyaan di luar topik. Classifier
# ini tertutup pada 7 kelas: apa pun yang masuk dipaksa menjadi salah satunya,
# dan pertanyaan seperti "bel pulang jam berapa" atau "film bagus apa" tetap
# memperoleh keyakinan tinggi karena bentuk kalimatnya mirip pertanyaan
# perpustakaan. Pengukuran menunjukkan hanya 40% pertanyaan di luar topik yang
# tertolak oleh ambang.
#
# Penjaga ini menambahkan syarat kedua: pesan harus menyinggung setidaknya satu
# kata dari domain perpustakaan. Intent 'salam' dikecualikan karena sapaan
# memang tidak memuat kata benda domain.
_KOSAKATA_DOMAIN = {
    # koleksi dan katalog
    'buku', 'baca', 'katalog', 'judul', 'tulis', 'kategori', 'koleksi',
    'novel', 'komik', 'fiksi', 'cerpen', 'kamus', 'ensiklopedia', 'majalah',
    # perpustakaan
    'pustaka', 'pus', 'perpus', 'libra', 'rak',
    # peminjaman
    'kembali', 'balik', 'balikin', 'masuk',
    'denda', 'telat', 'tempo', 'anggota', 'kartu', 'stok', 'sedia',
    'tunggak', 'aju', 'acc',
    # saran
    'rekomendasi', 'saran', 'usul',
    # sistem
    'aplikasi', 'akun', 'sandi', 'password', 'login', 'logout', 'favorit',
    'profil', 'halaman', 'menu', 'tombol', 'fitur', 'cari', 'web', 'situs',
    # nama kategori koleksi
    'matematika', 'sains', 'biologi', 'fisika', 'kimia', 'ips', 'ipa',
    'sejarah', 'olahraga', 'agama', 'teknologi', 'inggris', 'pkn',
}


# Ragam bahasa siswa menghasilkan terlalu banyak turunan untuk didaftar satu per
# satu: pinjeman, pinjemnya, pinjamanku, minjemin, bukunya, bacaannya. Awalan
# berikut dicocokkan sebagai prefiks sehingga seluruh keluarga kata ikut
# terjaring tanpa perlu diperbarui setiap kali ada bentuk baru.
_AWALAN_DOMAIN = ('pinjam', 'pinjem', 'minjam', 'minjem',
                  'buku', 'baca', 'pustaka', 'perpus', 'katalog')


def _menyinggung_domain(preprocessed: str) -> bool:
    """True kalau pesan memuat minimal satu kata kosakata domain perpustakaan."""
    token = preprocessed.split()
    if set(token) & _KOSAKATA_DOMAIN:
        return True
    return any(t.startswith(_AWALAN_DOMAIN) for t in token)


def train_and_save(dataset):
    """
    Train CalibratedClassifierCV(LinearSVC) + MultinomialNB dari dataset.
    Returns: (vectorizer, clf_lsvc, clf_nb, lsvc_acc, nb_acc, n_samples)
    """
    texts  = [preprocess(d['text']) for d in dataset]
    labels = [d['intent'] for d in dataset]

    # Step 1: Fit vectorizer pada SEMUA data
    vect  = TfidfVectorizer(min_df=1, ngram_range=(1, 2), sublinear_tf=True)
    X_all = vect.fit_transform(texts)

    # Step 2: 80/20 split (stratified) untuk accuracy reporting
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_all, labels, test_size=0.2, random_state=42, stratify=labels
    )

    # Step 3: Eval models (hanya untuk reporting akurasi — tidak disimpan)
    clf_lsvc_eval = CalibratedClassifierCV(LinearSVC(max_iter=1000), cv=3)
    clf_lsvc_eval.fit(X_tr, y_tr)
    lsvc_acc = accuracy_score(y_te, clf_lsvc_eval.predict(X_te))

    clf_nb_eval = MultinomialNB()
    clf_nb_eval.fit(X_tr, y_tr)
    nb_acc = accuracy_score(y_te, clf_nb_eval.predict(X_te))

    # Step 4: Production models — fit pada FULL data
    clf_lsvc = CalibratedClassifierCV(LinearSVC(max_iter=1000), cv=3)
    clf_lsvc.fit(X_all, labels)
    clf_nb = MultinomialNB()
    clf_nb.fit(X_all, labels)

    # Simpan ke disk — os.makedirs wajib sebelum joblib.dump (models/ mungkin belum ada)
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(vect,     VECTORIZER_PATH)
    joblib.dump(clf_lsvc, LSVC_PATH)
    joblib.dump(clf_nb,   NB_PATH)

    return vect, clf_lsvc, clf_nb, round(lsvc_acc, 4), round(nb_acc, 4), len(texts)


def load_or_train(dataset):
    """
    Load joblib dari disk jika ada, otherwise train dari dataset.
    Returns: (vectorizer, clf_lsvc, clf_nb, lsvc_acc_or_None, nb_acc_or_None, n_samples_or_None)
    """
    if os.path.exists(VECTORIZER_PATH):
        vect     = joblib.load(VECTORIZER_PATH)
        clf_lsvc = joblib.load(LSVC_PATH)
        clf_nb   = joblib.load(NB_PATH)
        return vect, clf_lsvc, clf_nb, None, None, None
    else:
        return train_and_save(dataset)


def predict_intent(message, vectorizer, clf_lsvc, REPLIES):
    """
    Klasifikasi intent dari pesan teks.

    Dua syarat harus dipenuhi sebelum sebuah intent diterima:
    1. max(predict_proba) >= THRESHOLD (0.5) — keyakinan cukup (D-04)
    2. pesan menyinggung kosakata domain perpustakaan — kecuali untuk 'salam',
       karena sapaan memang tidak memuat kata benda domain

    Keduanya gagal -> intent='tidak_dimengerti'. Kelas ini BUKAN kelas training,
    melainkan mekanisme cadangan agar chatbot tidak menjawab dengan yakin
    pertanyaan yang berada di luar cakupannya.

    Returns: (intent: str, confidence: float, reply: str)
    """
    preprocessed = preprocess(message)
    X_vec        = vectorizer.transform([preprocessed])
    proba        = clf_lsvc.predict_proba(X_vec)[0]
    confidence   = float(np.max(proba))
    intent       = clf_lsvc.classes_[np.argmax(proba)]

    if confidence < THRESHOLD:
        intent = 'tidak_dimengerti'
    elif intent != 'salam' and not _menyinggung_domain(preprocessed):
        intent = 'tidak_dimengerti'

    reply = REPLIES.get(intent, REPLIES['tidak_dimengerti'])
    return intent, confidence, reply
