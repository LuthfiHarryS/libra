import pytest

from chatbot.preprocess import preprocess
from chatbot.dataset import get_training_data


def test_meminjam_stems_to_pinjam():
    assert "pinjam" in preprocess("meminjam")


def test_perpustakaan_stems_to_pustaka():
    assert "pustaka" in preprocess("perpustakaan")


def test_lowercase_and_no_punctuation():
    result = preprocess("GIMANA caranya???")
    assert result == result.lower()
    assert "?" not in result


def test_deterministic():
    assert preprocess("cara pinjam buku") == preprocess("cara pinjam buku")


def test_tidak_ada_sampel_latih_yang_jadi_kosong():
    """
    Sampel yang menjadi string kosong menghasilkan vektor TF-IDF nol, sehingga
    tidak mengajarkan apa pun dan mencemari kelasnya. Ini menangkap seluruh
    kelas kesalahan tersebut, bukan hanya kata yang kebetulan sudah diketahui.
    """
    kosong = [d['text'] for d in get_training_data() if not preprocess(d['text'])]
    assert kosong == [], f"sampel latih menjadi kosong setelah preprocess: {kosong}"


@pytest.mark.parametrize("sapaan", [
    "halo", "hallo", "helo", "hello", "hai", "hi", "haii",
    "hei", "hey", "woi", "yo", "pagi", "siang", "sore", "malam",
    "assalamualaikum", "spada", "permisi",
])
def test_sapaan_satu_kata_tidak_hilang(sapaan):
    """Sapaan satu kata harus menyisakan token; kalau kosong, intent salam mustahil dikenali."""
    assert preprocess(sapaan) != "", f"{sapaan!r} hilang total setelah preprocess"
