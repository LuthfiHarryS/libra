"""
Lapisan Gemini — hanya untuk cabang eksperimen.

Cabang ini ada untuk membandingkan dua pendekatan menjawab pertanyaan
siswa: classifier intent (Naive Bayes/SVM) yang diukur di naskah, dan
model bahasa. Kode di main tidak berubah.

Jawaban selalu ditambatkan ke isi basis data: judul yang relevan dicari
lebih dulu lewat katalog.py, lalu Gemini hanya boleh menjawab dari
potongan itu. Tanpa penambatan, chatbot perpustakaan akan mengarang
judul yang tidak ada di rak — kegagalan yang jauh lebih buruk daripada
menjawab "tidak tahu".

Kunci API dibaca dari env var GEMINI_API_KEY dan tidak pernah ditulis
ke berkas mana pun.
"""
import json
import os
import urllib.error
import urllib.request

# Mendukung mode paket (pytest / import chatbot.gemini) dan mode skrip
# (python app.py dari folder python/chatbot/), sama seperti classifier.py.
try:
    from chatbot import katalog
except ImportError:
    import katalog  # type: ignore[no-redef]

MODEL_BAWAAN = 'gemini-2.5-flash'
BATAS_DETIK = 8


def _kunci() -> str:
    """
    Dibaca saat dipakai, bukan saat modul diimpor.

    Kalau dibaca saat impor, .env yang dimuat belakangan tidak akan
    pernah terlihat dan kuncinya seolah-olah kosong padahal ada.
    """
    return os.environ.get('GEMINI_API_KEY', '').strip()


def _model() -> str:
    return os.environ.get('GEMINI_MODEL', '').strip() or MODEL_BAWAAN

_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
        "{model}:generateContent")

_PERAN = """Kamu asisten perpustakaan SMPN 1 Kemang bernama LIBRA.

Aturan yang tidak boleh dilanggar:
- Jawab hanya dari DATA PERPUSTAKAAN di bawah. Jangan pernah menyebut
  judul, penulis, atau jumlah yang tidak ada di sana.
- Kalau datanya tidak memuat jawabannya, katakan terus terang belum
  ketemu, lalu sarankan bertanya ke petugas perpustakaan.
- Tolak dengan sopan pertanyaan di luar urusan perpustakaan sekolah.
- Bahasa Indonesia, ramah, untuk siswa SMP. Maksimal tiga kalimat.
- Jangan memakai format markdown."""


def tersedia() -> bool:
    """Gemini hanya dipakai bila kuncinya benar-benar ada."""
    return bool(_kunci())


def _konteks(pesan: str) -> str:
    """
    Potongan data perpustakaan yang relevan dengan pesan.

    Setiap bagian dibungkus try sendiri supaya satu query yang gagal
    tidak menghapus konteks yang lain.
    """
    bagian = []

    try:
        ringkas = katalog.ringkasan_koleksi()
        if ringkas:
            bagian.append(f"Ringkasan koleksi: {ringkas}")
    except Exception:
        pass

    # ekstrak_topik menyerah pada kalimat panjang dan informal — persis
    # jenis kalimat yang sampai ke Gemini, karena classifier pun menyerah
    # di situ. Maka setiap kata kandidat dicoba, bukan cuma satu topik.
    kandidat = []
    try:
        satu = katalog.ekstrak_topik(pesan)
        if satu:
            kandidat.append(satu)
        for k in katalog.kandidat_topik(pesan):
            if k not in kandidat:
                kandidat.append(k)
    except Exception:
        pass

    terpakai = 0
    for topik in kandidat:
        if terpakai >= 3:  # cukup untuk menambatkan; lebih dari itu jadi bising
            break
        try:
            baris = katalog.cari_judul(topik)
            if baris:
                daftar = "; ".join(
                    f"{b['judul']} — penulis {b['penulis']}, "
                    f"kategori {b['kategori_nama']}, "
                    f"tersedia {b['stok_tersedia']} dari {b['stok_total']}"
                    for b in baris
                )
                bagian.append(f"Judul yang cocok dengan '{topik}': {daftar}")
                terpakai += 1
                continue
        except Exception:
            pass

        try:
            jumlah, judul = katalog.cari_per_topik(topik)
            if judul:
                bagian.append(
                    f"Pencarian '{topik}' menemukan {jumlah} buku: "
                    + ", ".join(judul)
                )
                terpakai += 1
        except Exception:
            pass

    try:
        populer = katalog.buku_terpopuler()
        if populer:
            bagian.append(f"Buku terpopuler: {populer}")
    except Exception:
        pass

    return "\n".join(bagian) if bagian else "(data katalog tidak terjangkau)"


def jawab(pesan: str):
    """
    Jawaban Gemini yang sudah ditambatkan, atau None.

    None berarti pemanggil harus memakai jalur lama. Semua kegagalan —
    kunci kosong, jaringan mati, kuota habis, balasan tak terduga —
    menghasilkan None, tidak pernah melempar. Chatbot tidak boleh mati
    hanya karena layanan luar sedang bermasalah.
    """
    kunci = _kunci()
    if not kunci:
        return None

    badan = json.dumps({
        "system_instruction": {"parts": [{"text": _PERAN}]},
        "contents": [{
            "parts": [{
                "text": f"DATA PERPUSTAKAAN:\n{_konteks(pesan)}\n\n"
                        f"Pertanyaan siswa: {pesan}"
            }]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 512,
            # Gemini 2.5 berpikir dulu sebelum menjawab, dan token berpikir
            # ikut memakan maxOutputTokens. Dibiarkan menyala, jatahnya habis
            # untuk berpikir dan jawabannya terpotong di tengah kalimat.
            # Pertanyaan di sini sederhana dan datanya sudah disediakan, jadi
            # tidak ada yang perlu dipikir panjang.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }).encode('utf-8')

    permintaan = urllib.request.Request(
        _URL.format(model=_model()),
        data=badan,
        headers={
            'Content-Type': 'application/json',
            # Kunci lewat header, bukan query string, supaya tidak ikut
            # tercatat di log akses maupun riwayat proxy.
            'x-goog-api-key': kunci,
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(permintaan, timeout=BATAS_DETIK) as balasan:
            data = json.loads(balasan.read().decode('utf-8'))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None

    try:
        potongan = data['candidates'][0]['content']['parts']
        teks = "".join(p.get('text', '') for p in potongan).strip()
    except (KeyError, IndexError, TypeError):
        return None

    return teks or None
