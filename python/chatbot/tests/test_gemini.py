"""
Uji lapisan Gemini tanpa menyentuh jaringan.

Yang diuji bukan mutu jawaban modelnya — itu tidak bisa diuji otomatis —
melainkan janji yang dipegang lapisan ini: selalu mengembalikan None saat
gagal, tidak pernah melempar, dan selalu menyertakan data katalog di
dalam permintaan supaya jawabannya tertambat.
"""
import json
import urllib.error

import pytest

from chatbot import gemini


def _balasan(teks):
    """Bentuk balasan Gemini yang sudah dipersempit ke bagian yang dipakai."""
    return json.dumps({
        "candidates": [{"content": {"parts": [{"text": teks}]}}]
    }).encode()


class _Palsu:
    """Pengganti objek yang dikembalikan urllib.request.urlopen."""

    def __init__(self, isi):
        self._isi = isi

    def read(self):
        return self._isi

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


@pytest.fixture
def kunci_ada(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'kunci-uji')
    monkeypatch.setattr(gemini, '_konteks', lambda pesan: "Ringkasan koleksi: 34 buku")


def test_tanpa_kunci_langsung_none(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    assert gemini.jawab("jam buka perpustakaan?") is None
    assert gemini.tersedia() is False


def test_kunci_kosong_dianggap_tidak_ada(monkeypatch):
    """Baris 'GEMINI_API_KEY=' di .env menghasilkan string kosong."""
    monkeypatch.setenv('GEMINI_API_KEY', '   ')
    assert gemini.tersedia() is False
    assert gemini.jawab("halo") is None


def test_model_bisa_diganti_lewat_env(monkeypatch):
    monkeypatch.delenv('GEMINI_MODEL', raising=False)
    assert gemini._model() == gemini.MODEL_BAWAAN
    monkeypatch.setenv('GEMINI_MODEL', 'gemini-3-pro')
    assert gemini._model() == 'gemini-3-pro'


def test_jawaban_normal(monkeypatch, kunci_ada):
    monkeypatch.setattr(gemini.urllib.request, 'urlopen',
                        lambda *a, **k: _Palsu(_balasan("Perpustakaan buka jam 7 pagi.")))
    assert gemini.jawab("jam buka?") == "Perpustakaan buka jam 7 pagi."


def test_konteks_katalog_ikut_terkirim(monkeypatch, kunci_ada):
    terkirim = {}

    def tangkap(permintaan, timeout=None):
        terkirim['badan'] = json.loads(permintaan.data.decode())
        terkirim['header'] = permintaan.headers
        return _Palsu(_balasan("ok"))

    monkeypatch.setattr(gemini.urllib.request, 'urlopen', tangkap)
    gemini.jawab("ada buku apa saja?")

    teks = terkirim['badan']['contents'][0]['parts'][0]['text']
    assert "Ringkasan koleksi: 34 buku" in teks
    assert "ada buku apa saja?" in teks
    # Kunci lewat header, bukan URL.
    assert terkirim['header'].get('X-goog-api-key') == 'kunci-uji'


def test_berpikir_dimatikan_dan_jatah_cukup(monkeypatch, kunci_ada):
    """
    Gemini 2.5 memakai token berpikir dari jatah maxOutputTokens. Dibiarkan
    menyala dengan jatah kecil, jawabannya terpotong di tengah kalimat —
    kegagalan yang sudah pernah terjadi, jadi dikunci di sini.
    """
    terkirim = {}

    def tangkap(permintaan, timeout=None):
        terkirim['badan'] = json.loads(permintaan.data.decode())
        return _Palsu(_balasan("ok"))

    monkeypatch.setattr(gemini.urllib.request, 'urlopen', tangkap)
    gemini.jawab("halo")

    cfg = terkirim['badan']['generationConfig']
    assert cfg['thinkingConfig']['thinkingBudget'] == 0
    assert cfg['maxOutputTokens'] >= 512


def test_semua_kandidat_topik_dicoba(monkeypatch):
    """
    ekstrak_topik menyerah pada kalimat panjang informal — persis kalimat
    yang sampai ke Gemini. Kandidat lain harus tetap dicoba.
    """
    monkeypatch.setattr(gemini.katalog, 'ringkasan_koleksi', lambda: None)
    monkeypatch.setattr(gemini.katalog, 'buku_terpopuler', lambda: None)
    monkeypatch.setattr(gemini.katalog, 'ekstrak_topik', lambda p: None)
    monkeypatch.setattr(gemini.katalog, 'kandidat_topik', lambda p: ['kliping', 'cuaca'])

    def cari(topik):
        if topik != 'cuaca':
            return None
        return [{'judul': 'Air Udara Cuaca', 'penulis': 'Wawan',
                 'kategori_nama': 'Sains', 'stok_tersedia': 3, 'stok_total': 3}]

    monkeypatch.setattr(gemini.katalog, 'cari_judul', cari)
    monkeypatch.setattr(gemini.katalog, 'cari_per_topik', lambda t: (0, []))

    assert "Air Udara Cuaca" in gemini._konteks("bikin kliping tentang cuaca")


@pytest.mark.parametrize("kegagalan", [
    urllib.error.URLError("jaringan mati"),
    urllib.error.HTTPError("u", 429, "kuota habis", {}, None),
    TimeoutError(),
    OSError("soket tertutup"),
])
def test_kegagalan_jaringan_jadi_none(monkeypatch, kunci_ada, kegagalan):
    def meledak(*a, **k):
        raise kegagalan

    monkeypatch.setattr(gemini.urllib.request, 'urlopen', meledak)
    assert gemini.jawab("halo") is None


@pytest.mark.parametrize("isi", [
    b'{}',                                  # tanpa candidates
    b'{"candidates": []}',                  # candidates kosong
    b'bukan json',                          # balasan rusak
    b'{"candidates": [{"content": {}}]}',   # tanpa parts
])
def test_balasan_tak_terduga_jadi_none(monkeypatch, kunci_ada, isi):
    monkeypatch.setattr(gemini.urllib.request, 'urlopen',
                        lambda *a, **k: _Palsu(isi))
    assert gemini.jawab("halo") is None


def test_jawaban_kosong_jadi_none(monkeypatch, kunci_ada):
    monkeypatch.setattr(gemini.urllib.request, 'urlopen',
                        lambda *a, **k: _Palsu(_balasan("   ")))
    assert gemini.jawab("halo") is None


def test_konteks_tetap_jalan_saat_katalog_mati(monkeypatch):
    """Database mati tidak boleh membuat _konteks melempar."""
    monkeypatch.setattr(gemini.katalog, 'ringkasan_koleksi',
                        lambda: (_ for _ in ()).throw(RuntimeError("db mati")))
    monkeypatch.setattr(gemini.katalog, 'ekstrak_topik',
                        lambda p: (_ for _ in ()).throw(RuntimeError("db mati")))
    monkeypatch.setattr(gemini.katalog, 'buku_terpopuler',
                        lambda: (_ for _ in ()).throw(RuntimeError("db mati")))
    assert gemini._konteks("halo") == "(data katalog tidak terjangkau)"


def test_riwayat_kosong_hanya_satu_giliran(monkeypatch):
    monkeypatch.setattr(gemini, '_konteks', lambda p: "data")
    isi = gemini._percakapan("halo", None)
    assert len(isi) == 1
    assert isi[0]['role'] == 'user'
    assert "Pertanyaan siswa: halo" in isi[0]['parts'][0]['text']


def test_riwayat_dipetakan_ke_peran_gemini(monkeypatch):
    monkeypatch.setattr(gemini, '_konteks', lambda p: "data")
    isi = gemini._percakapan("lanjut", [
        {"peran": "siswa", "teks": "negeri 5 menara tentang apa"},
        {"peran": "libra", "teks": "Bercerita tentang Alif."},
    ])
    assert [g['role'] for g in isi] == ['user', 'model', 'user']


def test_riwayat_dipangkas(monkeypatch):
    """Percakapan panjang tidak boleh membuat permintaan membengkak."""
    monkeypatch.setattr(gemini, '_konteks', lambda p: "data")
    banyak = [{"peran": "siswa", "teks": f"pesan {i}"} for i in range(30)]
    isi = gemini._percakapan("terakhir", banyak)
    assert len(isi) == gemini.MAKS_RIWAYAT + 1


def test_giliran_kosong_dilewati(monkeypatch):
    monkeypatch.setattr(gemini, '_konteks', lambda p: "data")
    isi = gemini._percakapan("x", [
        {"peran": "siswa", "teks": "   "},
        {"peran": "libra", "teks": "ada isi"},
    ])
    assert len(isi) == 2


def test_konteks_hanya_di_giliran_terakhir(monkeypatch):
    """Data katalog tidak diulang tiap giliran — itu yang membuat boros."""
    monkeypatch.setattr(gemini, '_konteks', lambda p: "PENANDA_KATALOG")
    isi = gemini._percakapan("x", [{"peran": "siswa", "teks": "sebelumnya"}])
    assert "PENANDA_KATALOG" not in isi[0]['parts'][0]['text']
    assert "PENANDA_KATALOG" in isi[-1]['parts'][0]['text']
