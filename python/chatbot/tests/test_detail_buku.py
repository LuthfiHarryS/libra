"""
Uji jawaban atribut sebuah judul: kategori, penulis, sinopsis, dan stok.

Latar belakang: classifier hanya mengenal tujuh intent dan tidak satu pun
mencakup pertanyaan atribut sebuah judul. Kata penandanya pun menyesatkan —
pada 525 sampel latih, "penulis" tidak pernah muncul sama sekali, sedangkan
"kategori" hanya muncul dua kali dan keduanya di intent lain. Akibatnya
"Negeri 5 Menara kategorinya apa" diklasifikasikan sebagai info_umum dan
dijawab jam buka perpustakaan.

Perbaikannya berada di tahap penyusunan jawaban berbasis katalog (subbab
3.7.3), bukan di dataset: bila pesan memuat kata tanya atribut sekaligus
judul yang benar-benar ada di katalog, jawaban disusun dari basis data apa
pun intent tebakan classifier.

Seperti test_katalog.py, berkas ini tidak menyentuh MySQL.
"""
import pytest

from chatbot import katalog


BUKU_PEACH = {
    "judul": "The Peach Boy",
    "penulis": "Didik Djunaedi",
    "kategori_nama": "Bahasa Inggris",
    "stok_tersedia": 1,
    "stok_total": 1,
}
BUKU_NEGERI = {
    "judul": "Negeri 5 Menara",
    "penulis": "Ahmad Fuadi",
    "kategori_nama": "Fiksi",
    "stok_tersedia": 0,
    "stok_total": 1,
}
# Judulnya diawali kata tanya. Katalog nyata memang memuat buku semacam ini,
# dan itu membuat "siapa penulis Negeri 5 Menara" salah menunjuk buku ini
# karena kata tanya "siapa" ikut dianggap kandidat judul.
BUKU_SIAPA = {
    "judul": "Siapa Bilang Matematika Sulit 3",
    "penulis": "Dra. Siswanto",
    "kategori_nama": "Matematika",
    "stok_tersedia": 2,
    "stok_total": 2,
}


# Judulnya diawali kata yang lazim dipakai bertanya. Katalog nyata memuat
# "Cara Menentukan Golongan Darah", dan itu membuat pertanyaan bantuan
# "cara filter buku per kategori gimana" salah terbaca sebagai pertanyaan
# atribut judul.
BUKU_CARA = {
    "judul": "Cara Menentukan Golongan Darah",
    "penulis": "Tim Penulis",
    "kategori_nama": "Biologi",
    "stok_tersedia": 1,
    "stok_total": 1,
}


@pytest.fixture
def katalog_palsu(monkeypatch):
    """Ganti kueri judul dengan katalog buatan."""
    isi = [BUKU_PEACH, BUKU_NEGERI, BUKU_SIAPA, BUKU_CARA]

    def cari_judul(topik):
        t = topik.lower()
        return [b for b in isi if t in b["judul"].lower()]

    monkeypatch.setattr(katalog, "cari_judul", cari_judul)


# ── pertanyaan atribut harus dijawab dari katalog ───────────────────────────
@pytest.mark.parametrize("pesan,harus_memuat", [
    ("The Peach Boy kategorinya apa", ["The Peach Boy", "Bahasa Inggris"]),
    ("buku a peach boy kategorinya apa", ["The Peach Boy", "Bahasa Inggris"]),
    ("kategori buku peach boy", ["The Peach Boy", "Bahasa Inggris"]),
    ("siapa penulis Negeri 5 Menara", ["Negeri 5 Menara", "Ahmad Fuadi"]),
    ("Negeri 5 Menara pengarangnya siapa", ["Negeri 5 Menara", "Ahmad Fuadi"]),
    ("Negeri 5 Menara ada berapa eksemplar", ["Negeri 5 Menara"]),
])
def test_menjawab_atribut_judul(katalog_palsu, pesan, harus_memuat):
    jawaban = katalog.jawab_detail_buku(pesan)
    assert jawaban is not None, "pertanyaan atribut judul tidak terjawab"
    for potongan in harus_memuat:
        assert potongan in jawaban, f"{potongan!r} tidak disebut pada: {jawaban}"


def test_menyebut_ketersediaan(katalog_palsu):
    """Judul yang stoknya habis harus dinyatakan sedang dipinjam."""
    jawaban = katalog.jawab_detail_buku("Negeri 5 Menara kategorinya apa")
    assert "dipinjam" in jawaban.lower()


# ── yang TIDAK boleh dibajak ────────────────────────────────────────────────
@pytest.mark.parametrize("pesan", [
    "kategori buku apa aja yang ada",     # pertanyaan koleksi, milik info_umum
    "cara filter buku per kategori gimana",  # milik bantuan_sistem
    "ada buku fiksi ga",                  # pencarian kategori, milik cari_buku
    "jam buka perpustakaan kapan",        # milik info_umum
])
def test_tidak_membajak_pertanyaan_lain(katalog_palsu, pesan):
    assert katalog.jawab_detail_buku(pesan) is None, (
        "pertanyaan non-atribut ikut terbajak")


@pytest.mark.parametrize("pesan,judul_benar", [
    ("siapa penulis Negeri 5 Menara", "Negeri 5 Menara"),
    ("Negeri 5 Menara pengarangnya siapa", "Negeri 5 Menara"),
    ("siapa yang menulis The Peach Boy", "The Peach Boy"),
])
def test_kata_tanya_tidak_dianggap_judul(katalog_palsu, pesan, judul_benar):
    """Kata tanya seperti "siapa" tidak boleh mencocoki judul buku."""
    jawaban = katalog.jawab_detail_buku(pesan)
    assert jawaban is not None
    assert judul_benar in jawaban, f"judul salah pada: {jawaban}"
    assert "Siapa Bilang" not in jawaban, f"kata tanya terbaca sebagai judul: {jawaban}"


def test_judul_tidak_dikenal_dikembalikan_none(katalog_palsu):
    """Judul di luar katalog harus jatuh ke perilaku lama, bukan mengarang."""
    assert katalog.jawab_detail_buku("Harry Potter kategorinya apa") is None


def test_gagal_database_tidak_melempar(monkeypatch):
    """Kalau kueri gagal, fungsi mengembalikan None supaya template dipakai."""
    monkeypatch.setattr(katalog, "cari_judul", lambda t: None)
    assert katalog.jawab_detail_buku("The Peach Boy kategorinya apa") is None
