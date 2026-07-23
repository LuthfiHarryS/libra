from chatbot.dataset import TRAINING_DATA, REPLIES, get_training_data


def test_no_tidak_dimengerti_in_training_data():
    intents = [d['intent'] for d in TRAINING_DATA]
    assert 'tidak_dimengerti' not in intents


def test_all_replies_keys_present():
    required = {'cari_buku', 'prosedur_pinjam', 'info_umum', 'salam',
                'rekomendasi_buku', 'cek_status_pinjam', 'bantuan_sistem', 'tidak_dimengerti'}
    assert required.issubset(set(REPLIES.keys()))


def test_minimum_samples():
    assert len(TRAINING_DATA) >= 200


def test_intents_are_balanced():
    """Setiap intent harus punya jumlah sampel yang sama (dataset seimbang)."""
    from collections import Counter
    counts = Counter(d['intent'] for d in TRAINING_DATA)
    assert len(set(counts.values())) == 1, f"Dataset tidak seimbang: {dict(counts)}"
    assert min(counts.values()) >= 25


def test_get_training_data_returns_list():
    data = get_training_data()
    assert isinstance(data, list)
    assert len(data) == len(TRAINING_DATA)


def test_training_data_schema():
    for item in TRAINING_DATA:
        assert 'text' in item
        assert 'intent' in item
