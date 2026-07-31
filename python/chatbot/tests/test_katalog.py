"""
Uji lapisan perakit jawaban katalog.

Seluruh berkas ini TIDAK menyentuh MySQL. Fungsi kueri diganti (monkeypatch)
dengan data buatan supaya cabang yang sulit dipicu oleh data nyata — misalnya
kategori yang seluruh bukunya sedang dipinjam — tetap teruji.
"""
import pytest

from chatbot import katalog


# ── ekstrak_kategori ────────────────────────────────────────────────────────
@pytest.mark.parametrize("pesan,harap", [
    ("ada buku fiksi ga", "Fiksi"),
    ("buku fiksi apa yang ada di perpustakaan ini?", "Fiksi"),
    ("nyari novel dong", "Fiksi"),
    ("ada komik gk", "Komik"),
    ("buku mtk ada?", "Matematika"),
    ("ada buku bahasa inggris", "Bahasa Inggris"),
    ("ada buku pkn ga", "PKN"),
    ("ada buku bahasa indonesia", "Bahasa Indonesia"),
])
def test_ekstrak_kategori(pesan, harap):
    assert katalog.ekstrak_kategori(pesan) == harap


def test_indonesia_sendirian_tidak_membajak_ke_kategori_kosong():
    """'sejarah Indonesia' harus jadi Sejarah, bukan kategori Bahasa Indonesia."""
    assert katalog.ekstrak_kategori("ada buku tentang sejarah indonesia") == "Sejarah"


# ── jawab_info_umum: pertanyaan waktu vs pertanyaan jumlah ──────────────────
@pytest.mark.parametrize("pesan", [
    "perpustakaan buka jam berapa",
    "perpus tutup jam berapa",
    "sampai jam berapa perpus buka",
    "jam operasional perpustakaan",
    "hari sabtu buka gak",
    "jam istirahat perpus buka gak",
])
def test_pertanyaan_waktu_tidak_dijawab_jumlah_koleksi(pesan, monkeypatch):
    """Kata 'berapa' pada 'jam berapa' tidak boleh memicu ringkasan koleksi."""
    monkeypatch.setattr(katalog, "ringkasan_koleksi",
                        lambda: (257, 14, [{"nama": "Matematika", "n": 50}]))
    assert katalog.jawab_info_umum(pesan) is None


@pytest.mark.parametrize("pesan", [
    "berapa jumlah buku di perpus",
    "koleksi bukunya ada berapa",
    "kategori buku apa aja yang ada",
    "ada berapa judul buku di libra",
])
def test_pertanyaan_jumlah_koleksi_tetap_dijawab(pesan, monkeypatch):
    monkeypatch.setattr(katalog, "ringkasan_koleksi",
                        lambda: (257, 14, [{"nama": "Matematika", "n": 50}]))
    jawab = katalog.jawab_info_umum(pesan)
    assert jawab is not None and "257" in jawab


# ── atribusi penulis ────────────────────────────────────────────────────────
def test_penulis_dicantumkan_kalau_seragam():
    rows = [{"judul": "A", "penulis": "Tere Liye"}, {"judul": "B", "penulis": "Tere Liye"}]
    assert katalog._keterangan_penulis(rows) == " karya Tere Liye"


def test_penulis_dihilangkan_kalau_campuran():
    """Jangan menempelkan penulis judul pertama ke seluruh daftar."""
    rows = [{"judul": "A", "penulis": "Bu Kasur"}, {"judul": "B", "penulis": "Arsyad Sidik"}]
    assert katalog._keterangan_penulis(rows) == ""


def test_penulis_kosong_tidak_menghasilkan_karya_gantung():
    rows = [{"judul": "A", "penulis": ""}, {"judul": "B", "penulis": ""}]
    assert katalog._keterangan_penulis(rows) == ""


# ── klaim ketersediaan dihitung atas seluruh kategori ───────────────────────
def _contoh(n=3):
    return [{"judul": f"Judul {i}", "penulis": f"Penulis {i}", "stok_tersedia": 1}
            for i in range(n)]


def test_semua_tersedia(monkeypatch):
    monkeypatch.setattr(katalog, "cari_per_kategori", lambda k: (18, 18, _contoh()))
    assert "Semuanya bisa langsung dipinjam." in katalog.jawab_cari_buku("ada buku fiksi")


def test_sebagian_tersedia_tidak_diklaim_semua(monkeypatch):
    """Contoh yang tampil semuanya ada stok, tetapi kategori tidak seluruhnya."""
    monkeypatch.setattr(katalog, "cari_per_kategori", lambda k: (18, 5, _contoh()))
    jawab = katalog.jawab_cari_buku("ada buku fiksi")
    assert "Semuanya bisa langsung dipinjam" not in jawab
    assert "5 di antaranya" in jawab


def test_tidak_ada_yang_tersedia(monkeypatch):
    monkeypatch.setattr(katalog, "cari_per_kategori", lambda k: (18, 0, _contoh()))
    jawab = katalog.jawab_cari_buku("ada buku fiksi")
    assert "semua sedang dipinjam" in jawab.lower()


def test_kategori_kosong(monkeypatch):
    monkeypatch.setattr(katalog, "cari_per_kategori", lambda k: (0, 0, []))
    assert "belum ada buku kategori" in katalog.jawab_cari_buku("ada buku pkn")


# ── prosedur_pinjam: satu intent, banyak topik ──────────────────────────────
@pytest.mark.parametrize("pesan,harus_memuat", [
    ("cara mengembalikan buku gimana", "mengembalikan"),
    ("gimana cara balikin bukunya", "mengembalikan"),
    ("denda telat berapa", "tidak menghitung denda"),
    ("kalau terlambat kena sanksi apa", "tidak menghitung denda"),
    ("bisa perpanjang pinjaman gak", "belum bisa diajukan"),
    ("berapa lama bisa minjam buku", "7 hari"),
    ("kalau bukunya hilang gimana", "lapor ke petugas"),
    ("buku aku rusak gimana", "lapor ke petugas"),
])
def test_prosedur_pinjam_menjawab_topik_yang_ditanya(pesan, harus_memuat):
    jawab = katalog.jawab_prosedur_pinjam(pesan)
    assert jawab is not None, f"{pesan!r} jatuh ke templat umum"
    assert harus_memuat in jawab, f"{pesan!r} -> {jawab!r}"


def test_pertanyaan_cara_meminjam_tetap_pakai_templat():
    """Templat lama sudah benar untuk 'cara meminjam' — jangan diganti."""
    assert katalog.jawab_prosedur_pinjam("gimana cara pinjam buku") is None


def test_denda_tidak_mengarang_angka():
    """Sistem tidak punya fitur denda; jawaban tidak boleh menyebut nominal."""
    import re as _re
    jawab = katalog.jawab_prosedur_pinjam("denda telat berapa")
    nominal = _re.findall(r'\b(?:rp|Rp)\s?\d|\d+\s*(?:rupiah|ribu|perak)', jawab)
    assert nominal == [], f"jawaban denda mengarang nominal: {jawab!r}"


def test_db_mati_mengembalikan_none(monkeypatch):
    """Fail-safe: DB tidak terjangkau -> None supaya app.py pakai templat."""
    monkeypatch.setattr(katalog, "cari_per_kategori", lambda k: None)
    assert katalog.jawab_cari_buku("ada buku fiksi") is None
