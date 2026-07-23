from chatbot.preprocess import preprocess


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
