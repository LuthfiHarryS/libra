"""
eval_chatbot.py — Evaluasi model klasifikasi intent dengan 5-fold stratified
cross-validation. Menghasilkan ulang angka pada Tabel 3.6 dan Tabel 3.7
Penulisan Ilmiah.

Jalankan dari direktori python/:
    .venv/Scripts/python.exe scripts/eval_chatbot.py

Skrip ini TIDAK menyentuh model produksi di chatbot/models/. Model dilatih ulang
di memori khusus untuk pengukuran, lalu dibuang.

Konfigurasi (terverifikasi menghasilkan angka yang sama persis dengan naskah):
  - Preprocessing  : fungsi preprocess() yang sama dengan pelatihan dan inferensi
  - Vektorisasi    : TfidfVectorizer(min_df=1, ngram_range=(1,2), sublinear_tf=True)
                     di-fit sekali pada seluruh data, mengikuti pola classifier.py
  - Pembagian data : StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
  - Model          : LinearSVC dan MultinomialNB

Mengapa LinearSVC dievaluasi tanpa CalibratedClassifierCV:
  Pembungkus kalibrasi dipakai di produksi semata untuk menghasilkan nilai
  keyakinan yang dibutuhkan mekanisme ambang batas (lihat chatbot/classifier.py).
  Kalibrasi tidak mengubah kemampuan klasifikasi yang sedang diukur, sedangkan
  validasi silang internalnya menambah keragaman yang tidak berkaitan dengan
  kinerja model. Karena itu pengukuran dilakukan pada LinearSVC apa adanya.

Varian tanpa kebocoran juga dilaporkan sebagai pembanding: TfidfVectorizer di-fit
hanya pada data latih tiap lipatan, sehingga kosakata data uji tidak pernah
dilihat saat pelatihan. Angkanya sedikit berbeda dan wajar dicantumkan bila
diminta penguji.
"""
import os
import sys

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.dataset import TRAINING_DATA          # noqa: E402
from chatbot.preprocess import preprocess          # noqa: E402

N_SPLITS = 5
SEED = 42
URUTAN_INTENT = ['salam', 'cari_buku', 'rekomendasi_buku', 'prosedur_pinjam',
                 'cek_status_pinjam', 'info_umum', 'bantuan_sistem']


def _vectorizer():
    return TfidfVectorizer(min_df=1, ngram_range=(1, 2), sublinear_tf=True)


def _models():
    return {'LinearSVC': lambda: LinearSVC(max_iter=1000),
            'MultinomialNB': lambda: MultinomialNB()}


def evaluate(texts, y, vectorizer_per_fold=False):
    """Kembalikan (skor per lipatan, prediksi out-of-fold) untuk tiap model."""
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    if not vectorizer_per_fold:
        X_full = _vectorizer().fit_transform(texts)

    skor = {n: [] for n in _models()}
    oof = {n: np.empty(len(y), dtype=object) for n in _models()}

    for i_tr, i_te in skf.split(np.zeros(len(y)), y):
        if vectorizer_per_fold:
            vect = _vectorizer()
            X_tr = vect.fit_transform([texts[i] for i in i_tr])
            X_te = vect.transform([texts[i] for i in i_te])
        else:
            X_tr, X_te = X_full[i_tr], X_full[i_te]

        for nama, buat in _models().items():
            clf = buat()
            clf.fit(X_tr, y[i_tr])
            pred = clf.predict(X_te)
            skor[nama].append(accuracy_score(y[i_te], pred))
            oof[nama][i_te] = pred

    return skor, oof


def cetak_tabel_36(skor):
    print('\nTabel 3.6  Perbandingan Akurasi Model Klasifikasi Intent (5-fold CV)')
    print('  ' + '-' * 66)
    print(f'  {"Model":34}{"Akurasi":20}Keterangan')
    print('  ' + '-' * 66)
    ket = {'LinearSVC': 'Model utama (produksi)', 'MultinomialNB': 'Model pembanding'}
    nama_panjang = {'LinearSVC': 'Linear Support Vector Classifier',
                    'MultinomialNB': 'Multinomial Naive Bayes'}
    for nama, s in skor.items():
        s = np.asarray(s)
        akurasi = f'{s.mean() * 100:.2f}% (±{s.std() * 100:.2f}%)'
        print(f'  {nama_panjang[nama]:34}{akurasi:20}{ket[nama]}')
    print('  ' + '-' * 66)
    for nama, s in skor.items():
        per_lipatan = '  '.join(f'{v * 100:.2f}' for v in s)
        print(f'  akurasi tiap lipatan {nama:16}: {per_lipatan}')


def cetak_tabel_37(y, pred):
    p, r, f, _ = precision_recall_fscore_support(
        y, list(pred), labels=URUTAN_INTENT, zero_division=0)
    print('\nTabel 3.7  Presisi, Recall, dan F1-Score per Intent')
    print('           (LinearSVC, Out-of-Fold 5-fold CV, %d Sampel)' % len(y))
    print('  ' + '-' * 56)
    print(f'  {"Intent":22}{"Presisi":>10}{"Recall":>10}{"F1-Score":>12}')
    print('  ' + '-' * 56)
    for i, k in enumerate(URUTAN_INTENT):
        print(f'  {k:22}{p[i]:>10.2f}{r[i]:>10.2f}{f[i]:>12.2f}')
    print('  ' + '-' * 56)
    print(f'  {"Rata-rata (macro)":22}{p.mean():>10.2f}{r.mean():>10.2f}{f.mean():>12.2f}')


def main():
    texts = [preprocess(d['text']) for d in TRAINING_DATA]
    y = np.asarray([d['intent'] for d in TRAINING_DATA])

    print(f'Dataset : {len(texts)} sampel, {len(set(y))} kelas intent '
          f'({len(texts) // len(set(y))} sampel per kelas)')
    print(f'Skema   : StratifiedKFold(n_splits={N_SPLITS}, shuffle=True, '
          f'random_state={SEED}), vectorizer di-fit pada seluruh data')

    skor, oof = evaluate(texts, y)
    cetak_tabel_36(skor)
    cetak_tabel_37(y, oof['LinearSVC'])

    skor_b, _ = evaluate(texts, y, vectorizer_per_fold=True)
    print('\nPembanding — vectorizer di-fit per lipatan (tanpa kebocoran kosakata):')
    for nama, s in skor_b.items():
        s = np.asarray(s)
        print(f'  {nama:16}: {s.mean() * 100:.2f}% (±{s.std() * 100:.2f}%)')


if __name__ == '__main__':
    main()
