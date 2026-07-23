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


def test_fallback_tidak_dimengerti(trained_models):
    vect, clf_lsvc, _, _, _, _ = trained_models
    intent, conf, reply = predict_intent("siapa presiden Indonesia", vect, clf_lsvc, REPLIES)
    assert intent == "tidak_dimengerti"
    assert reply == REPLIES["tidak_dimengerti"]


def test_models_dir_created():
    import os
    # __file__ = .../python/chatbot/tests/test_classifier.py
    # Go up two levels: tests -> chatbot, then append models
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    chatbot_dir = os.path.dirname(tests_dir)
    models_dir = os.path.join(chatbot_dir, "models")
    assert os.path.isdir(models_dir)
