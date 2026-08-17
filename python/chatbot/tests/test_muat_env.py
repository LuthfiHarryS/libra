"""
Uji pemuat .env.

Yang dijaga di sini: berkas yang tidak ada tidak boleh menggagalkan
start, dan nilai dari terminal tidak boleh tertimpa isi berkas — kalau
tertimpa, menyetel kunci sementara lewat terminal jadi mustahil.
"""
from chatbot.muat_env import muat_env


def _tulis(tmp_path, isi):
    berkas = tmp_path / ".env"
    berkas.write_text(isi, encoding="utf-8")
    return str(berkas)


def test_berkas_tidak_ada_bukan_kesalahan(tmp_path):
    assert muat_env(str(tmp_path / "tidak-ada.env")) == 0


def test_memuat_pasangan_biasa(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("CHATBOT_MODE", raising=False)
    jalur = _tulis(tmp_path, "GEMINI_API_KEY=abc123\nCHATBOT_MODE=hibrida\n")

    assert muat_env(jalur) == 2

    import os
    assert os.environ["GEMINI_API_KEY"] == "abc123"
    assert os.environ["CHATBOT_MODE"] == "hibrida"


def test_env_terminal_menang(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dari-terminal")
    jalur = _tulis(tmp_path, "GEMINI_API_KEY=dari-berkas\n")

    assert muat_env(jalur) == 0

    import os
    assert os.environ["GEMINI_API_KEY"] == "dari-terminal"


def test_komentar_baris_kosong_dan_baris_rusak_dilewati(tmp_path, monkeypatch):
    monkeypatch.delenv("SATU", raising=False)
    jalur = _tulis(tmp_path, "# komentar\n\nbaris tanpa sama dengan\nSATU=1\n")

    assert muat_env(jalur) == 1

    import os
    assert os.environ["SATU"] == "1"


def test_kutip_pembungkus_dibuang(tmp_path, monkeypatch):
    monkeypatch.delenv("A", raising=False)
    monkeypatch.delenv("B", raising=False)
    monkeypatch.delenv("C", raising=False)
    jalur = _tulis(tmp_path, "A=\"berkutip\"\nB='tunggal'\nC=ada\"di\"tengah\n")

    muat_env(jalur)

    import os
    assert os.environ["A"] == "berkutip"
    assert os.environ["B"] == "tunggal"
    # Kutip di tengah nilai bukan pembungkus — harus dibiarkan utuh.
    assert os.environ["C"] == 'ada"di"tengah'


def test_nilai_kosong_tetap_disetel(tmp_path, monkeypatch):
    """GEMINI_API_KEY= yang belum diisi harus jadi string kosong, bukan galat."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    jalur = _tulis(tmp_path, "GEMINI_API_KEY=\n")

    assert muat_env(jalur) == 1

    import os
    assert os.environ["GEMINI_API_KEY"] == ""
