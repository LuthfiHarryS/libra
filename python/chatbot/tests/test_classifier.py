import pytest
from chatbot.dataset import get_training_data, REPLIES
from chatbot.classifier import train_and_save, predict_intent


@pytest.fixture(scope="module")
def trained_models():
    dataset = get_training_data()
    vect, clf_lsvc, clf_nb, lsvc_acc, nb_acc, n = train_and_save(dataset)
    return vect, clf_lsvc, clf_nb, lsvc_acc, nb_acc, n


def test_train_and_save_returns_six_tuple(trained_models):
    assert len(trained_models) == 6


def test_accuracy_is_float(trained_models):
    _, _, _, lsvc_acc, nb_acc, _ = trained_models
    assert isinstance(lsvc_acc, float)
    assert isinstance(nb_acc, float)
    assert 0.0 <= lsvc_acc <= 1.0
    assert 0.0 <= nb_acc <= 1.0


def test_predict_prosedur_pinjam(trained_models):
    vect, clf_lsvc, _, _, _, _ = trained_models
    intent, conf, reply = predict_intent("cara pinjam buku", vect, clf_lsvc, REPLIES)
    assert intent == "prosedur_pinjam"
    assert conf >= 0.5


def test_predict_cari_buku(trained_models):
    vect, clf_lsvc, _, _, _, _ = trained_models
    intent, conf, reply = predict_intent("cari buku IPA", vect, clf_lsvc, REPLIES)
    assert intent == "cari_buku"


@pytest.mark.parametrize("pesan", [
    # Pola "…apa yang ada di perpustakaan" — kata "perpustakaan" sebelumnya
    # hanya muncul di info_umum, sehingga pertanyaan pencarian yang menyebut
    # kata itu tertarik ke jawaban jam buka.
    "buku fiksi apa yang ada di perpustakaan ini?",
    "buku komik apa yang ada di perpustakaan ini?",
    "buku sejarah apa yang ada di perpustakaan",
    "di perpustakaan ini ada buku fiksi apa aja",
    # Nama kategori katalog harus masuk kosakata; "fiksi" sempat tidak ada
    # satu pun di data latih sehingga hilang saat vektorisasi.
    "ada buku fiksi ga",
    "buku fiksi apa aja",
    "punya novel fiksi nggak",
])
def test_pertanyaan_kategori_di_perpustakaan_masuk_cari_buku(trained_models, pesan):
    """Menyebut kategori + kata 'perpustakaan' tetap harus jadi cari_buku."""
    vect, clf_lsvc, _, _, _, _ = trained_models
    intent, conf, _ = predict_intent(pesan, vect, clf_lsvc, REPLIES)
    assert intent == "cari_buku", f"{pesan!r} -> {intent} ({conf:.3f})"


@pytest.mark.parametrize("pesan", [
    # Pertanyaan di luar cakupan perpustakaan. Ambang keyakinan saja tidak
    # cukup menolaknya — beberapa memperoleh keyakinan di atas 0,8 karena
    # bentuk kalimatnya mirip pertanyaan perpustakaan — sehingga penjaga
    # kosakata domain yang harus menangkapnya.
    "siapa presiden Indonesia",
    "bel pulang jam berapa",
    "film bagus apa",
    "aku lapar",
    "nilai ulangan aku berapa",
    "tolong kerjain pr aku",
    "jadwal pelajaran besok apa",
    "besok libur gak",
    "kamu siapa sih",
])
def test_pertanyaan_luar_topik_ditolak(trained_models, pesan):
    vect, clf_lsvc, _, _, _, _ = trained_models
    intent, conf, reply = predict_intent(pesan, vect, clf_lsvc, REPLIES)
    assert intent == "tidak_dimengerti", f"{pesan!r} dijawab sebagai {intent} ({conf:.3f})"
    assert reply == REPLIES["tidak_dimengerti"]


@pytest.mark.parametrize("pesan", [
    # Penjaga domain tidak boleh menolak pertanyaan perpustakaan yang sah,
    # termasuk ragam slang yang tidak terdaftar eksplisit di kosakata.
    "pinjeman aku udah disetujui belum",
    "tombol pinjemnya di mana sih",
    "bukunya ada di rak mana",
    "cara balikin buku gimana",
])
def test_penjaga_domain_tidak_menolak_pertanyaan_sah(trained_models, pesan):
    vect, clf_lsvc, _, _, _, _ = trained_models
    from chatbot.classifier import _menyinggung_domain
    from chatbot.preprocess import preprocess
    assert _menyinggung_domain(preprocess(pesan)), f"{pesan!r} dianggap di luar domain"


def test_salam_dikecualikan_dari_penjaga_domain(trained_models):
    """Sapaan tidak memuat kata benda domain, jadi harus dikecualikan."""
    vect, clf_lsvc, _, _, _, _ = trained_models
    for sapaan in ["halo kak", "selamat pagi", "assalamualaikum"]:
        intent, conf, _ = predict_intent(sapaan, vect, clf_lsvc, REPLIES)
        assert intent == "salam", f"{sapaan!r} -> {intent} ({conf:.3f})"


def test_models_dir_created():
    import os
    # __file__ = .../python/chatbot/tests/test_classifier.py
    # Go up two levels: tests -> chatbot, then append models
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    chatbot_dir = os.path.dirname(tests_dir)
    models_dir = os.path.join(chatbot_dir, "models")
    assert os.path.isdir(models_dir)
