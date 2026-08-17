"""
uji_blackbox_chatbot.py — Pengujian black-box chatbot LIBRA dengan metode
Equivalence Partitioning (EP) dan Boundary Value Analysis (BVA).

Kedudukannya di antara berkas evaluasi yang sudah ada:

    eval_chatbot.py          -> akurasi model (5-fold CV) pada distribusi data latih
    eval_cakupan_chatbot.py  -> cakupan model atas pertanyaan held-out
    uji_blackbox_chatbot.py  -> PENGUJIAN PERANGKAT LUNAK atas layanan chatbot utuh

Dua berkas pertama menguji MODEL: masukannya kalimat, keluarannya label intent,
dan yang diukur akurasi statistik. Berkas ini menguji LAYANAN: masukannya
permintaan HTTP POST /chat, keluarannya badan JSON lengkap (intent, confidence,
reply, sumber) beserta kode status. Jalur yang diuji karena itu mencakup bagian
yang tidak pernah tersentuh oleh evaluasi akurasi:

  - validasi masukan pydantic (pesan kosong -> HTTP 400)
  - ambang keyakinan 0,5 -> intent 'tidak_dimengerti'
  - penjaga kosakata domain (menolak pertanyaan di luar cakupan perpustakaan)
  - penyusunan jawaban dari katalog (sumber='katalog') dan kemundurannya ke
    template statis (sumber='template')

Metodenya black-box: kasus uji disusun hanya dari spesifikasi antarmuka, tanpa
melihat isi model. Ruang masukan dipartisi menjadi kelas-kelas ekuivalen (satu
kelas per intent, satu kelas di luar domain, satu kelas masukan tidak sah), lalu
setiap kelas diwakili beberapa kasus. Nilai batas diuji terpisah: panjang pesan
minimum dan maksimum, kategori berisi 0 dan 1 buku, serta kedua sisi ambang
keyakinan.

Prasyarat: MySQL hidup dan layanan chatbot berjalan (python/chatbot/app.py, :5001).

Jalankan:  python python/scripts/uji_blackbox_chatbot.py
           python python/scripts/uji_blackbox_chatbot.py --url http://127.0.0.1:5001
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections import OrderedDict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'chatbot'))

URL_BAKU = 'http://127.0.0.1:5001'

# Ambang keyakinan menurut spesifikasi layanan. Ditulis ulang di sini, bukan
# diimpor dari classifier.py, supaya pengujian tetap black-box: nilainya berasal
# dari dokumen rancangan, bukan dari kode yang sedang diuji.
AMBANG = 0.5

# ── Definisi partisi ────────────────────────────────────────────────────────
PARTISI = OrderedDict([
    ('EP-01', 'Sapaan'),
    ('EP-02', 'Pencarian buku'),
    ('EP-03', 'Permintaan rekomendasi'),
    ('EP-04', 'Prosedur peminjaman'),
    ('EP-05', 'Status pinjaman pribadi'),
    ('EP-06', 'Informasi umum perpustakaan'),
    ('EP-07', 'Bantuan pemakaian sistem'),
    ('EP-08', 'Pertanyaan di luar domain'),
    ('EP-09', 'Masukan tidak sah'),
    ('EP-10', 'Pertanyaan atribut judul'),
    ('BVA-1', 'Batas panjang pesan'),
    ('BVA-2', 'Batas isi kategori'),
    ('BVA-3', 'Batas ambang keyakinan'),
])


# ── Pemeriksa tambahan ──────────────────────────────────────────────────────
# Selain intent, sebagian kasus menuntut sifat lain pada badan jawaban. Tiap
# pemeriksa menerima badan JSON dan mengembalikan None kalau lolos, atau alasan
# kegagalan berupa string.
def dari_katalog(b):
    return None if b.get('sumber') == 'katalog' else "sumber='%s', bukan katalog" % b.get('sumber')


def dari_template(b):
    return None if b.get('sumber') == 'template' else "sumber='%s', bukan template" % b.get('sumber')


def memuat(*potongan):
    def cek(b):
        reply = (b.get('reply') or '').lower()
        kurang = [p for p in potongan if p.lower() not in reply]
        return None if not kurang else 'jawaban tidak memuat %s' % kurang
    return cek


def gabung(*pemeriksa):
    def cek(b):
        for p in pemeriksa:
            alasan = p(b)
            if alasan:
                return alasan
        return None
    return cek


# ── Kasus uji ───────────────────────────────────────────────────────────────
# (id, partisi, pesan, status HTTP diharapkan, intent diharapkan, pemeriksa)
# intent None berarti tidak diperiksa (dipakai pada kasus HTTP 400).
KASUS = [
    # EP-01 Sapaan — dikecualikan dari penjaga domain karena sapaan tidak
    # memuat kata benda perpustakaan.
    ('U-01', 'EP-01', 'selamat siang kak libra', 200, 'salam', None),
    ('U-02', 'EP-01', 'hai, permisi mau tanya', 200, 'salam', None),

    # EP-02 Pencarian buku — jawaban wajib berasal dari katalog, bukan template.
    ('U-03', 'EP-02', 'ada buku tentang gunung berapi ga', 200, 'cari_buku', dari_katalog),
    ('U-04', 'EP-02', 'kak punya buku olahraga nggak', 200, 'cari_buku', dari_katalog),
    ('U-05', 'EP-02', 'mau nyari buku tentang tata surya', 200, 'cari_buku', dari_katalog),

    # EP-03 Rekomendasi
    ('U-06', 'EP-03', 'kasih saran bacaan yang seru dong', 200, 'rekomendasi_buku', dari_katalog),
    ('U-07', 'EP-03', 'buku apa yang paling sering dipinjam di sini', 200, 'rekomendasi_buku', dari_katalog),

    # EP-04 Prosedur peminjaman
    ('U-08', 'EP-04', 'gimana aturan meminjam buku di sini', 200, 'prosedur_pinjam', None),
    ('U-09', 'EP-04', 'berapa lama buku boleh dipinjam', 200, 'prosedur_pinjam', None),

    # EP-05 Status pinjaman pribadi — dibedakan dari EP-04 hanya oleh penanda
    # kepemilikan (aku, punyaku) yang sengaja dipertahankan dari stopword.
    ('U-10', 'EP-05', 'pinjaman aku sudah di acc belum', 200, 'cek_status_pinjam', None),
    ('U-11', 'EP-05', 'kapan aku harus balikin buku punyaku', 200, 'cek_status_pinjam', None),

    # EP-06 Informasi umum
    ('U-12', 'EP-06', 'perpusnya tutup jam berapa ya kak', 200, 'info_umum', None),
    ('U-13', 'EP-06', 'ada berapa judul buku di perpus ini', 200, 'info_umum', dari_katalog),

    # EP-07 Bantuan sistem
    ('U-14', 'EP-07', 'cara ganti sandi akun gimana', 200, 'bantuan_sistem', None),
    ('U-15', 'EP-07', 'kenapa aku tidak bisa masuk aplikasi', 200, 'bantuan_sistem', None),

    # EP-08 Di luar domain — classifier tertutup pada 7 kelas, sehingga kelas
    # ini hanya bisa ditolak oleh ambang keyakinan atau penjaga kosakata.
    ('U-16', 'EP-08', 'siapa presiden indonesia sekarang', 200, 'tidak_dimengerti', dari_template),
    ('U-17', 'EP-08', 'besok ada ulangan tidak', 200, 'tidak_dimengerti', dari_template),
    ('U-18', 'EP-08', 'film bioskop apa yang bagus', 200, 'tidak_dimengerti', dari_template),
    ('U-19', 'EP-08', 'bel pulang sekolah jam berapa', 200, 'tidak_dimengerti', dari_template),

    # EP-09 Masukan tidak sah — ditangani validator pydantic sebelum model.
    ('U-20', 'EP-09', '', 400, None, None),
    ('U-21', 'EP-09', '    ', 400, None, None),
    ('U-22', 'EP-09', None, 400, None, None),          # badan JSON tanpa kunci 'message'

    # EP-10 Pertanyaan atribut judul — jalur jawab_detail_buku() yang berjalan
    # mendahului rantai berbasis intent.
    ('U-23', 'EP-10', 'siapa penulis buku Alam Semesta', 200, None,
     gabung(dari_katalog, memuat('Rositawaty'))),
    ('U-24', 'EP-10', 'buku Adaptasi Makhluk Hidup kategorinya apa', 200, None,
     gabung(dari_katalog, memuat('Biologi'))),

    # BVA-1 Batas panjang pesan
    # Satu karakter dan satu kata domain sama-sama menghasilkan vektor TF-IDF
    # yang terlalu miskin untuk melewati ambang, sehingga keduanya ditolak.
    ('U-25', 'BVA-1', 'a', 200, 'tidak_dimengerti', dari_template),
    ('U-26', 'BVA-1', 'buku', 200, 'tidak_dimengerti', dari_template),
    ('U-27', 'BVA-1', ('ada buku tentang olahraga tidak ' * 30).strip(), 200, 'cari_buku', None),

    # BVA-2 Batas isi kategori — PKN terdaftar tetapi berisi 0 buku, Komik
    # berisi tepat 1. Keduanya harus dijawab dari katalog secara akurat.
    ('U-28', 'BVA-2', 'ada buku pkn tidak', 200, 'cari_buku', dari_katalog),
    ('U-29', 'BVA-2', 'punya buku komik nggak kak', 200, 'cari_buku', dari_katalog),
    ('U-30', 'BVA-2', 'ada buku tentang astronomi kuantum tidak', 200, 'cari_buku', None),

    # BVA-3 Batas ambang keyakinan 0,5 — kedua sisi keputusan.
    ('U-31', 'BVA-3', 'qwerty asdf zxcv', 200, 'tidak_dimengerti', dari_template),
    ('U-32', 'BVA-3', 'gmn cara pinjem bku', 200, 'prosedur_pinjam', None),
]


def kirim(url: str, pesan):
    """POST /chat. pesan None berarti badan JSON tanpa kunci 'message'."""
    badan = {} if pesan is None else {'message': pesan}
    req = urllib.request.Request(
        url + '/chat',
        data=json.dumps(badan).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))


def periksa_kebocoran():
    """Kasus uji tidak boleh identik dengan data latih setelah preprocessing."""
    from dataset import get_training_data
    from preprocess import preprocess
    latih = {preprocess(d['text']) for d in get_training_data()}
    bocor = []
    for kode, _, pesan, _, _, _ in KASUS:
        if isinstance(pesan, str) and pesan.strip() and preprocess(pesan) in latih:
            bocor.append((kode, pesan))
    return bocor


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default=URL_BAKU)
    arg = ap.parse_args()

    try:
        with urllib.request.urlopen(arg.url + '/health', timeout=5) as r:
            json.loads(r.read().decode('utf-8'))
    except Exception as e:
        print('Layanan chatbot tidak terjangkau di %s (%s).' % (arg.url, e))
        print('Jalankan lebih dulu: python/chatbot/app.py')
        return 2

    bocor = periksa_kebocoran()
    if bocor:
        print('GAGAL — kasus uji berikut identik dengan data latih setelah preprocessing:')
        for kode, pesan in bocor:
            print('   %s  %r' % (kode, pesan))
        return 1

    print('PENGUJIAN BLACK-BOX CHATBOT LIBRA — Equivalence Partitioning + Boundary Value Analysis')
    print('Layanan  : %s' % arg.url)
    print('Kasus uji: %d dalam %d partisi' % (len(KASUS), len(PARTISI)))
    print()

    lebar = (6, 7, 42, 20, 20, 9)
    judul = ('Kode', 'Partisi', 'Masukan', 'Diharapkan', 'Diperoleh', 'Status')
    print('  '.join(j.ljust(w) for j, w in zip(judul, lebar)))
    print('-' * (sum(lebar) + 2 * (len(lebar) - 1)))

    gagal = []
    hasil = []
    per_partisi = OrderedDict((k, [0, 0]) for k in PARTISI)

    for kode, partisi, pesan, status_harap, intent_harap, pemeriksa in KASUS:
        status, badan = kirim(arg.url, pesan)

        alasan = None
        if status != status_harap:
            alasan = 'HTTP %d, diharapkan %d' % (status, status_harap)
        elif status == 200:
            if intent_harap is not None and badan.get('intent') != intent_harap:
                alasan = "intent '%s'" % badan.get('intent')
            elif pemeriksa is not None:
                alasan = pemeriksa(badan)

        lolos = alasan is None
        hasil.append((kode, partisi, badan))
        per_partisi[partisi][1] += 1
        if lolos:
            per_partisi[partisi][0] += 1
        else:
            gagal.append((kode, partisi, pesan, alasan, badan))

        if status_harap == 400:
            harap_txt = 'HTTP 400'
            dapat_txt = 'HTTP %d' % status
        elif intent_harap is None:
            # Kasus yang dinilai dari isi jawaban, bukan dari label intent.
            harap_txt = 'jawaban katalog'
            dapat_txt = 'sumber=%s' % badan.get('sumber', '-')
        else:
            harap_txt = intent_harap
            dapat_txt = '%s %.2f' % (badan.get('intent', '-'), badan.get('confidence', 0.0))

        tampil = pesan if pesan is not None else '(tanpa kunci message)'
        if len(tampil) > lebar[2]:
            tampil = tampil[:lebar[2] - 1] + '…'
        baris = (kode, partisi, tampil, harap_txt, dapat_txt, 'SESUAI' if lolos else 'GAGAL')
        print('  '.join(str(s).ljust(w) for s, w in zip(baris, lebar)))

    lolos_total = sum(v[0] for v in per_partisi.values())
    print()
    print('RINGKASAN PER PARTISI')
    print('-' * 62)
    for kode, nama in PARTISI.items():
        b, n = per_partisi[kode]
        print('  %-6s %-32s %d/%d' % (kode, nama, b, n))
    print('-' * 62)
    print('  TOTAL %-32s %d/%d  (%.1f%%)'
          % ('', lolos_total, len(KASUS), 100.0 * lolos_total / len(KASUS)))

    # Analisis EP-08: memisahkan penolakan oleh ambang keyakinan dari penolakan
    # oleh penjaga kosakata domain. Angka ini yang membenarkan keberadaan
    # penjaga tersebut — tanpa dia, ambang saja meloloskan pertanyaan di luar
    # cakupan yang kebetulan berbentuk mirip pertanyaan perpustakaan.
    luar = [b for _, p, b in hasil if p == 'EP-08']
    if luar:
        oleh_penjaga = [b for b in luar if b.get('confidence', 0.0) >= AMBANG]
        print()
        print('ANALISIS PARTISI EP-08 (di luar domain)')
        print('-' * 62)
        print('  Pertanyaan di luar domain            : %d' % len(luar))
        print('  Ditolak ambang keyakinan (<%.1f)      : %d' % (AMBANG, len(luar) - len(oleh_penjaga)))
        print('  Ditolak penjaga kosakata domain      : %d' % len(oleh_penjaga))
        if oleh_penjaga:
            k = [b.get('confidence', 0.0) for b in oleh_penjaga]
            print('  Keyakinan kasus yang lolos ambang    : %s'
                  % ', '.join('%.2f' % x for x in sorted(k, reverse=True)))

    if gagal:
        print()
        print('RINCIAN KASUS GAGAL')
        for kode, partisi, pesan, alasan, badan in gagal:
            print('  %s [%s] %r' % (kode, partisi, pesan))
            print('       sebab  : %s' % alasan)
            print('       jawaban: %s' % (badan.get('reply') or badan.get('error'))[:160])

    return 0 if not gagal else 1


if __name__ == '__main__':
    raise SystemExit(main())
