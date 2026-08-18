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

_PERAN = """Kamu asisten perpustakaan SMPN 1 Kemang bernama LIBRA, bicara dengan siswa SMP.

Ada dua jenis informasi, dan keduanya diperlakukan berbeda.

1. FAKTA PERPUSTAKAAN — apa yang ada di rak, jumlah eksemplar, ketersediaan,
   penulis dan kategori menurut catatan sekolah. Ini HANYA boleh dari DATA
   PERPUSTAKAAN di bawah. Jangan pernah menyebut judul yang tidak ada di
   sana seolah-olah tersedia, dan jangan pernah mengarang jumlah stok.

2. PENGETAHUAN UMUM — isi cerita, tokoh, latar, penulis, dan konteks sebuah
   buku. Ini boleh kamu jawab dari pengetahuanmu sendiri, terutama saat siswa
   ingin tahu lebih jauh daripada yang tercatat di basis data.

Cara memakainya:
- Kalau ditanya isi buku, mulai dari sinopsis di data. Kalau siswa bertanya
  lagi atau minta lebih detail, lanjutkan dengan pengetahuanmu.
- Saat menjelaskan dari pengetahuan sendiri tentang buku yang TIDAK ada di
  data perpustakaan, katakan apa adanya bahwa bukunya belum ada di
  perpustakaan sekolah, lalu tetap jelaskan isinya.
- Kalau kamu tidak benar-benar tahu buku itu, katakan tidak tahu. Jangan
  mengarang cerita, tokoh, atau penulis.

Gaya: Bahasa Indonesia yang ramah dan mudah untuk siswa SMP. Ringkas saja
secara bawaan, sekitar tiga kalimat; boleh lebih panjang bila siswa memang
meminta penjelasan detail. Jangan memakai format markdown."""


def tersedia() -> bool:
    """Gemini hanya dipakai bila kuncinya benar-benar ada."""
    return bool(_kunci())


def _uraikan(b: dict) -> str:
    """
    Satu buku sebagai kalimat data untuk Gemini.

    Sinopsis ikut dikirim — tanpa itu pertanyaan "buku ini tentang apa"
    tidak mungkin dijawab benar, karena modelnya tidak diberi bahannya
    dan hanya bisa menebak dari judul.
    """
    bagian = [
        f"{b['judul']} — penulis {b['penulis']}",
        f"kategori {b.get('kategori_nama')}",
        f"tersedia {b.get('stok_tersedia')} dari {b.get('stok_total')}",
    ]
    sinopsis = (b.get('sinopsis') or '').strip()
    if sinopsis:
        # Dipotong supaya beberapa buku sekaligus tetap muat dalam satu
        # permintaan tanpa menenggelamkan pertanyaan siswanya.
        bagian.append("sinopsis: " + sinopsis[:600])
    else:
        bagian.append("sinopsis belum tersedia di basis data")
    return ", ".join(bagian)


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
                daftar = "; ".join(_uraikan(b) for b in baris)
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


MAKS_RIWAYAT = 8   # 4 tanya-jawab terakhir; cukup untuk "jelaskan lebih detail"


def _percakapan(pesan: str, riwayat):
    """
    Susunan giliran percakapan untuk Gemini.

    Riwayat diperlukan supaya pertanyaan lanjutan seperti "jelaskan lebih
    detail" punya rujukan. Tanpa itu tiap pesan berdiri sendiri dan Gemini
    tidak tahu buku mana yang sedang dibicarakan.

    Data katalog ditempelkan pada giliran terakhir saja, tidak diulang di
    setiap giliran, supaya permintaannya tidak membengkak.
    """
    isi = []
    for giliran in (riwayat or [])[-MAKS_RIWAYAT:]:
        teks = (giliran.get("teks") or "").strip()
        if not teks:
            continue
        peran = "user" if giliran.get("peran") == "siswa" else "model"
        isi.append({"role": peran, "parts": [{"text": teks[:1500]}]})

    isi.append({
        "role": "user",
        "parts": [{
            "text": f"DATA PERPUSTAKAAN:\n{_konteks(pesan)}\n\n"
                    f"Pertanyaan siswa: {pesan}"
        }],
    })
    return isi


def teks_bebas(perintah: str, sistem: str = ""):
    """
    Panggilan Gemini polos: tanpa persona pustakawan, tanpa konteks katalog.

    Dipakai perkakas di luar chatbot, misalnya penyusun sinopsis. Memakai
    jawab() untuk keperluan itu keliru — persona pustakawan memerintahkan
    "jawab hanya dari data perpustakaan", sehingga model menolak menulis
    apa pun dan selalu menjawab tidak tahu.
    """
    kunci = _kunci()
    if not kunci:
        return None

    isi = {"contents": [{"role": "user", "parts": [{"text": perintah}]}],
           "generationConfig": {"temperature": 0.4, "maxOutputTokens": 512,
                                "thinkingConfig": {"thinkingBudget": 0}}}
    if sistem:
        isi["system_instruction"] = {"parts": [{"text": sistem}]}

    permintaan = urllib.request.Request(
        _URL.format(model=_model()),
        data=json.dumps(isi).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": kunci},
        method="POST",
    )
    try:
        with urllib.request.urlopen(permintaan, timeout=BATAS_DETIK) as balasan:
            data = json.loads(balasan.read().decode("utf-8"))
        potongan = data["candidates"][0]["content"]["parts"]
        return ("".join(p.get("text", "") for p in potongan).strip()) or None
    except (urllib.error.URLError, TimeoutError, ValueError, OSError,
            KeyError, IndexError, TypeError):
        return None


def jawab(pesan: str, riwayat=None):
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
        "contents": _percakapan(pesan, riwayat),
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
