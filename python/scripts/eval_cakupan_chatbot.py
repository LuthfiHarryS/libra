"""
eval_cakupan_chatbot.py — Mengukur cakupan chatbot atas pertanyaan siswa.

Berbeda dari eval_chatbot.py yang mengukur akurasi validasi silang ATAS data
latih, berkas ini memakai set uji HELD-OUT: pertanyaan yang sengaja ditulis
di luar dataset pelatihan, meniru cara siswa SMP bertanya di perpustakaan
(termasuk singkatan, slang, dan salah ketik).

Tujuannya menjawab pertanyaan yang berbeda:
    eval_chatbot.py       -> "seberapa akurat model pada distribusi datanya?"
    eval_cakupan_chatbot.py -> "apakah pertanyaan nyata siswa benar-benar terjawab?"

Dua kegagalan dibedakan:
  SALAH  = intent tertebak kelas lain           (jawaban keliru — paling berbahaya)
  RAGU   = confidence < ambang -> tidak_dimengerti (chatbot menyerah)

Jalankan:  python python/scripts/eval_cakupan_chatbot.py
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'chatbot'))

from classifier import load_or_train, predict_intent, THRESHOLD  # noqa: E402
from dataset import get_training_data, REPLIES                   # noqa: E402
from preprocess import preprocess                                # noqa: E402

# ── Set uji held-out ────────────────────────────────────────────────────────
# Tidak satu pun kalimat di bawah ini boleh ada di TRAINING_DATA. Pemeriksaan
# tumpang tindih dijalankan otomatis di bawah dan akan menggagalkan laporan.
UJI = [
    # ── salam ──
    ("selamat pagi bot", "salam"),
    ("assalamualaikum kak perpus", "salam"),
    ("halo, mau nanya boleh?", "salam"),
    ("hai kak apa kabarnya", "salam"),
    ("permisi numpang tanya ya", "salam"),
    ("sore kak libra", "salam"),
    ("hallo perpus", "salam"),
    ("hey kak", "salam"),

    # ── cari_buku ──
    ("kak ada buku tentang gunung meletus ga", "cari_buku"),
    ("buku fiksi apa yang ada di perpustakaan ini?", "cari_buku"),
    ("aku nyari buku tentang pecahan", "cari_buku"),
    ("ada buku tentang hewan laut nggak", "cari_buku"),
    ("punya buku resep masakan gak", "cari_buku"),
    ("ada buku tentang sholat gak kak", "cari_buku"),
    ("mau nyari buku tentang tumbuhan hijau", "cari_buku"),
    ("buku tentang basket ada ga", "cari_buku"),
    ("ada buku tentang kemerdekaan indonesia ga", "cari_buku"),
    ("carikan buku tentang listrik dong", "cari_buku"),
    ("ada novel remaja gak", "cari_buku"),
    ("buku tentang bangun datar ada?", "cari_buku"),
    ("ada buku tentang pahlawan nasional nggak", "cari_buku"),
    ("kak mau cari buku tentang virus", "cari_buku"),
    ("ada kamus inggris indonesia ga", "cari_buku"),
    ("buku tentang sampah plastik ada gak", "cari_buku"),

    # ── rekomendasi_buku ──
    ("buku apa yang enak dibaca pas santai", "rekomendasi_buku"),
    ("kasih rekomendasi dong kak", "rekomendasi_buku"),
    ("bingung mau baca apa nih", "rekomendasi_buku"),
    ("ada saran buku buat anak smp gak", "rekomendasi_buku"),
    ("buku apa yang paling banyak dibaca di sini", "rekomendasi_buku"),
    ("saranin dong buku yang gak bikin ngantuk", "rekomendasi_buku"),
    ("buku apa sih yang bagus banget", "rekomendasi_buku"),
    ("minta usul bacaan dong", "rekomendasi_buku"),
    ("buku paling favorit apa kak", "rekomendasi_buku"),
    ("mau baca yang seru, ada usul?", "rekomendasi_buku"),

    # ── prosedur_pinjam ──
    ("kak gimana sih caranya pinjem buku", "prosedur_pinjam"),
    ("mau minjem buku, mulai dari mana ya", "prosedur_pinjam"),
    ("kalau telat balikin didenda gak", "prosedur_pinjam"),
    ("bukunya boleh dibawa pulang berapa lama", "prosedur_pinjam"),
    ("aku boleh minjem berapa buku sekaligus", "prosedur_pinjam"),
    ("kalau bukunya kena air gimana", "prosedur_pinjam"),
    ("cara balikin bukunya gimana kak", "prosedur_pinjam"),
    ("bisa diperpanjang gak pinjamannya", "prosedur_pinjam"),
    ("syarat minjem buku apa aja sih", "prosedur_pinjam"),
    ("harus pakai kartu pelajar ya kalau pinjam", "prosedur_pinjam"),

    # ── cek_status_pinjam ──
    ("pinjeman aku udah disetujui belum", "cek_status_pinjam"),
    ("aku pinjem buku apa aja sekarang", "cek_status_pinjam"),
    ("kapan aku harus balikin bukunya", "cek_status_pinjam"),
    ("coba cek pinjaman punyaku dong", "cek_status_pinjam"),
    ("aku ada denda telat gak ya", "cek_status_pinjam"),
    ("masih ada buku yang belum aku kembaliin?", "cek_status_pinjam"),
    ("status pengajuan pinjem aku gimana", "cek_status_pinjam"),
    ("sisa berapa hari lagi pinjaman aku", "cek_status_pinjam"),
    ("riwayat pinjam aku bisa dilihat di mana", "cek_status_pinjam"),
    ("pengajuanku udah di acc kak?", "cek_status_pinjam"),

    # ── info_umum ──
    ("perpus buka jam berapa sih", "info_umum"),
    ("kak perpusnya tutup jam berapa", "info_umum"),
    ("hari sabtu perpus buka gak", "info_umum"),
    ("perpusnya di lantai berapa", "info_umum"),
    ("ada berapa buku di perpus ini", "info_umum"),
    ("boleh bawa makanan masuk gak", "info_umum"),
    ("perpus ada di sebelah mana ya", "info_umum"),
    ("kategori bukunya apa aja sih", "info_umum"),
    ("libra itu aplikasi apa", "info_umum"),
    ("siapa yang jaga perpus", "info_umum"),
    ("boleh belajar kelompok di perpus gak", "info_umum"),
    ("koleksi buku di sini ada berapa judul", "info_umum"),

    # ── bantuan_sistem ──
    ("kok aku gak bisa login ya", "bantuan_sistem"),
    ("cara ganti password gimana kak", "bantuan_sistem"),
    ("aplikasinya nge-bug terus", "bantuan_sistem"),
    ("tombol pinjemnya di mana sih", "bantuan_sistem"),
    ("gimana cara nyari buku di aplikasi ini", "bantuan_sistem"),
    ("cara keluar dari akun gimana", "bantuan_sistem"),
    ("aku lupa sandi akunku", "bantuan_sistem"),
    ("kok halamannya kosong ya", "bantuan_sistem"),
    ("cara daftar akunnya gimana", "bantuan_sistem"),
    ("gimana cara liat profil aku", "bantuan_sistem"),
]

# ── Set uji tersegel ────────────────────────────────────────────────────────
# UJI di atas dipakai untuk MEMANDU perbaikan dataset, sehingga angkanya lambat
# laun menjadi optimistis — kelemahan yang ditemukan di sana langsung ditambal.
# Set di bawah ini ditulis sekali sebelum putaran penyetelan terakhir dan TIDAK
# BOLEH dipakai untuk memilih sampel latih. Fungsinya satu: memberi angka
# cakupan yang tidak bias pada akhir pekerjaan. Kalau suatu saat set ini ikut
# dipakai menyetel, ia kehilangan gunanya dan harus diganti seluruhnya.
UJI_TERSEGEL = [
    ("selamat malam kak", "salam"),
    ("hai bot perpus", "salam"),
    ("halo, ada orang?", "salam"),
    ("kak, mau tanya sebentar", "salam"),

    ("ada buku tentang planet mars gak", "cari_buku"),
    ("buku tentang cara berkebun ada?", "cari_buku"),
    ("punya buku tentang dinosaurus nggak", "cari_buku"),
    ("aku butuh buku tentang pantun", "cari_buku"),
    ("ada buku tentang tarian daerah gak", "cari_buku"),
    ("buku tentang perkalian ada tidak", "cari_buku"),
    ("ada buku cerita rakyat nusantara ga", "cari_buku"),
    ("nyari buku tentang tubuh manusia", "cari_buku"),

    ("kasih tau buku yang bagus dong kak", "rekomendasi_buku"),
    ("ada bacaan seru buat liburan gak", "rekomendasi_buku"),
    ("buku apa ya yang pantas dibaca duluan", "rekomendasi_buku"),
    ("rekomendasi buku buat yang malas baca dong", "rekomendasi_buku"),
    ("buku terpopuler di sini apa", "rekomendasi_buku"),

    ("gimana tata cara meminjam di sini", "prosedur_pinjam"),
    ("berapa lama buku boleh ditahan", "prosedur_pinjam"),
    ("kalau hilang bukunya harus ganti gak", "prosedur_pinjam"),
    ("sanksi telat mengembalikan apa", "prosedur_pinjam"),
    ("maksimal berapa judul boleh dipinjam", "prosedur_pinjam"),
    ("perlu bawa apa saja kalau mau meminjam", "prosedur_pinjam"),

    ("pinjaman punyaku sudah disetujui belum", "cek_status_pinjam"),
    ("kapan batas balikin punyaku", "cek_status_pinjam"),
    ("aku lagi minjem berapa judul", "cek_status_pinjam"),
    ("tunggakan aku ada gak", "cek_status_pinjam"),
    ("pengajuan aku ditolak ya kak", "cek_status_pinjam"),
    ("daftar buku yang aku pinjam mana", "cek_status_pinjam"),

    ("perpus mulai buka pukul berapa", "info_umum"),
    ("perpus letaknya di gedung mana", "info_umum"),
    ("hari libur perpus tutup ya", "info_umum"),
    ("ada aturan apa aja di dalam perpus", "info_umum"),
    ("total koleksi perpus berapa judul", "info_umum"),
    ("aplikasi libra ini fungsinya apa", "info_umum"),

    ("kenapa aku gak bisa masuk akun", "bantuan_sistem"),
    ("cara reset sandi gimana", "bantuan_sistem"),
    ("menu favorit letaknya di mana", "bantuan_sistem"),
    ("web nya lemot banget kak", "bantuan_sistem"),
    ("cara pakai filter kategori gimana", "bantuan_sistem"),
    ("gimana cara keluar akun di hp", "bantuan_sistem"),
]


def _lapor(nama: str, kasus, vect, clf_lsvc, rinci: bool):
    benar = 0
    salah, ragu = [], []
    per_intent = defaultdict(lambda: {"n": 0, "benar": 0})

    for teks, harap in kasus:
        intent, conf, _ = predict_intent(teks, vect, clf_lsvc, REPLIES)
        per_intent[harap]["n"] += 1
        if intent == harap:
            benar += 1
            per_intent[harap]["benar"] += 1
        elif intent == 'tidak_dimengerti':
            ragu.append((teks, harap, conf))
        else:
            salah.append((teks, harap, intent, conf))

    n = len(kasus)
    print(f"=== {nama} — {n} pertanyaan ===")
    print(f"  Terjawab benar   : {benar}/{n}  ({benar/n:.1%})")
    print(f"  Salah intent     : {len(salah)}/{n}  ({len(salah)/n:.1%})")
    print(f"  Tidak dimengerti : {len(ragu)}/{n}  ({len(ragu)/n:.1%})")
    print("  " + "-" * 46)
    for intent in sorted(per_intent):
        d = per_intent[intent]
        print(f"  {intent:20} {d['benar']:2}/{d['n']:<3} {d['benar']/d['n']:>7.0%}")
    print("  " + "-" * 46)

    if rinci and salah:
        print("\n  SALAH INTENT (jawaban keliru diberikan ke siswa)")
        for teks, harap, dapat, conf in salah:
            print(f"     {teks!r}\n        harap={harap}  dapat={dapat}  conf={conf:.3f}")

    if rinci and ragu:
        print("\n  TIDAK DIMENGERTI (chatbot menyerah)")
        for teks, harap, conf in ragu:
            print(f"     {teks!r}\n        harap={harap}  conf={conf:.3f}")

    print()
    return len(salah), len(ragu)


def main() -> int:
    dataset = get_training_data()
    vect, clf_lsvc, _, *_ = load_or_train(dataset)

    # Kedua set harus benar-benar held-out.
    latih = {preprocess(d['text']) for d in dataset}
    bocor = [t for t, _ in (UJI + UJI_TERSEGEL) if preprocess(t) in latih]
    if bocor:
        print("GAGAL — kalimat uji berikut identik dengan data latih setelah preprocessing:")
        for t in bocor:
            print(f"   {t!r}")
        return 1

    print(f"Ambang batas : {THRESHOLD}    Dataset latih : {len(dataset)} sampel")
    print()
    s1, r1 = _lapor("SET PENYETELAN (dipakai memandu perbaikan — optimistis)",
                    UJI, vect, clf_lsvc, rinci=True)
    s2, r2 = _lapor("SET TERSEGEL (tidak pernah dipakai menyetel — angka jujur)",
                    UJI_TERSEGEL, vect, clf_lsvc, rinci=True)

    return 0 if not (s1 + r1 + s2 + r2) else 1


if __name__ == '__main__':
    raise SystemExit(main())
