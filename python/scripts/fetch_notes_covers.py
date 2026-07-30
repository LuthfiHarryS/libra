"""
fetch_notes_covers.py — Ambil cover + metadata untuk katalog hasil parse_notes.py.

Sumber utama: Google Books GData feed (books.google.com/books/feeds/volumes).
Dipilih karena — beda dengan books.googleapis.com/books/v1 — endpoint ini tidak
kena kuota harian anonim (HTTP 429), dan mayoritas buku di daftar ini terbitan
Alprin/ARC Media yang memang terindeks di sana. Open Library dicoba 0/8 judul: nihil.

Untuk judul yang tetap tidak ketemu, cover placeholder tipografis di-render lokal
supaya katalog tidak bolong.

Semua cover disimpan sebagai WebP ke uploads/covers/.
Output metadata: python/scripts/books_with_covers.json
"""
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from io import BytesIO
from pathlib import Path

import defusedxml.ElementTree as ET   # stdlib ET rentan XXE/billion-laughs
from PIL import Image, ImageDraw, ImageFont

IN_PATH = Path(__file__).parent / "books_from_notes.json"
OUT_PATH = Path(__file__).parent / "books_with_covers.json"
COVERS_DIR = Path(r"D:\xampp\htdocs\libra\uploads\covers")
COVERS_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LIBRA-SchoolLibrary/1.0 (educational)"
FEED = "https://books.google.com/books/feeds/volumes"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/terms",
}
THUMB_REL = "http://schemas.google.com/books/2008/thumbnail"

# Ukuran akhir cover di katalog. 460px cukup tajam untuk grid 2x retina,
# tapi tetap ~25-40KB per file dalam WebP q=82.
TARGET_W = 460
WEBP_QUALITY = 82

# Ambang penerimaan diputuskan di pilih_kandidat() — kombinasi kemiripan judul,
# penulis, dan penerbit. Satu angka saja terbukti tidak cukup: ambang longgar
# meloloskan buku lain berjudul mirip, ambang ketat membuang edisi yang benar.


# ── Kategori ────────────────────────────────────────────────────────────────
# Urutan penting: aturan paling spesifik didahulukan (mis. "bangun ruang" harus
# kena Matematika sebelum "ruang" tersenggol aturan lain).
KATEGORI_RULES = [
    ("Olahraga", ["olahraga", "sepak bola", "futsal", "voli", "basket", "bulu tangkis",
                  "tenis", "senam", "karate", "gulat", "binaraga", "atletik", "renang",
                  "perenang", "catur", "boling", "sepak takraw", "kebugaran", "balap sepeda",
                  "sepatu roda", "pemain", "penjelajahan", "aerobik", "pola gerak"]),
    ("Agama", ["allah", "nabi", "islam", "salat", "neraka", "khulafaurrasyidin", "arab",
               "quran", "teladan nabi", "khabab", "raden fatah", "subhanallah", "ilyasa",
               "nuh a.s"]),
    ("Matematika", ["matematika", "matematikawan", "bilangan", "aljabar", "pecahan",
                    "persamaan", "pertidaksamaan", "himpunan", "diagram venn", "pythagoras",
                    "bangun datar", "bangun ruang", "kubus", "balok", "lingkaran", "segitiga",
                    "segi banyak", "kesebangunan", "simetri", "pencerminan", "statistika",
                    "kpk", "fpb", "pangkat", "akar", "perkalian", "penjumlahan", "pengurangan",
                    "jarimatika", "sempoa", "persen", "permil", "koordinat", "transformasi",
                    "berhitung", "sudut", "keliling dan luas", "luas permukaan", "jaring-jaring",
                    "tempat kedudukan", "kuadrat", "lambang matematika", "angka", "diagram",
                    "mengukur jarak", "pengolahan data", "fungsi"]),
    ("Fisika", ["gaya", "newton", "energi", "kalor", "listrik", "elektromagnet", "gerak",
                "laser", "hologram", "konduktor", "isolator", "pesawat sederhana",
                "tumbukan", "gesekan", "roket", "antariksa", "tata surya", "matahari bumi"]),
    ("Kimia", ["kimia", "unsur", "senyawa", "campuran", "asam", "basa", "garam", "molekul",
               "ikatan kimia", "pengawetan"]),
    ("Biologi", ["tumbuhan", "hewan", "organisme", "makhluk hidup", "lumut", "serangga",
                 "moluska", "coelenterata", "herbarium", "biota", "mikroorganisme",
                 "golongan darah", "pernapasan", "mencerna", "adaptasi", "sel", "flora",
                 "cacing", "kucing", "burung", "lebah", "lalat", "bakau", "uniseluler",
                 "ekologi", "kelangsungan hidup", "sayur", "buah", "manusia", "mata"]),
    ("Sains", ["sains", "ilmu", "alam semesta", "gunung", "laut", "hujan", "pelangi",
               "atmosfer", "cuaca", "pemanasan global", "rumah kaca", "biogas", "air",
               "hutan", "gurun", "bumi", "muka bumi", "peta", "bencana", "konservasi",
               "lingkungan", "berat, waktu"]),
    ("Teknologi", ["komputer", "coreldraw", "microsoft word", "adobe premiere", "teknologi",
                   "video", "vektor", "kompor", "sepeda", "listrik", "industri"]),
    ("Sejarah", ["peradaban", "sejarah", "amangkurat", "mataram", "nusantara", "firaun",
                 "hatta", "tokoh", "nobel", "perdamaian"]),
    ("IPS", ["pekerjaan", "kewirausahaan", "ketenagakerjaan", "industrialisasi", "ekonomi",
             "keuangan", "masyarakat", "kearifan lokal", "norma", "narkoba", "budaya",
             "pergaulan", "public speaking", "karakter", "potensi diri", "pramuka",
             "kesehatan jiwa", "hidup sehat", "iq", "eq", "sq", "masa depan"]),
    ("Bahasa Inggris", ["english", "the ", "story of", "other stories", "a shepherd"]),
    ("Komik", ["bleach"]),
]
FIKSI_HINTS = ["dongeng", "fabel", "cerita", "kisah", "novel", "puisi", "narasi",
               "pohon dalam perut", "sekolah pohon", "stella", "life is beautiful",
               "rindu tanah", "pudarnya pesona", "si paser", "patepung", "ngeng",
               "tinkerbell", "air mata sang pohon", "perjalanan sebatang kayu",
               "jika pertiwi", "angel", "prince", "lord of the shadows", "games board"]


def norm(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def tebak_kategori(judul, penulis, subject=None):
    hay = norm(f"{judul} {penulis} {subject or ''}")
    for kategori, keywords in KATEGORI_RULES:
        for kw in keywords:
            if norm(kw) in hay:
                return kategori
    if any(norm(h) in hay for h in FIKSI_HINTS):
        return "Fiksi"
    return "Non-Fiksi"


# ── HTTP ────────────────────────────────────────────────────────────────────
def http_get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def gdata_search(query, max_results=5):
    """Cari di GData feed. Kembalikan list dict metadata volume."""
    url = f"{FEED}?q={urllib.parse.quote(query)}&max-results={max_results}"
    try:
        body = http_get(url)
        root = ET.fromstring(body)
    except Exception:
        return []

    out = []
    for entry in root.findall("atom:entry", NS):
        title_el = entry.find("dc:title", NS)
        if title_el is None or not title_el.text:
            continue

        thumb = None
        for link in entry.findall("atom:link", NS):
            if link.get("rel") == THUMB_REL:
                thumb = link.get("href")
                break

        ids = [e.text for e in entry.findall("dc:identifier", NS) if e.text]
        vol_id = next((i for i in ids if not i.startswith("ISBN:")), None)
        isbn = next((i[5:] for i in ids if i.startswith("ISBN:") and len(i) == 18), None)
        if isbn is None:
            isbn = next((i[5:] for i in ids if i.startswith("ISBN:")), None)

        def txt(tag):
            el = entry.find(tag, NS)
            return el.text if el is not None and el.text else None

        out.append({
            "vol_id": vol_id,
            "title": title_el.text,
            "creator": txt("dc:creator"),
            "publisher": txt("dc:publisher"),
            "subject": txt("dc:subject"),
            "description": txt("dc:description"),
            "isbn": isbn,
            "thumb": thumb,
        })
    return out


def skor_penulis(penulis, creator):
    """Kemiripan penulis lewat irisan token — format nama sering beda
    ('D. Astuti' vs 'Astuti, D., A.Md.'). None kalau tidak bisa dinilai."""
    if not creator or penulis == "Tidak Tertera":
        return None
    t1 = {t for t in norm(penulis).split() if len(t) > 2}
    t2 = {t for t in norm(creator).split() if len(t) > 2}
    if not t1 or not t2:
        return None
    return len(t1 & t2) / min(len(t1), len(t2))


def pilih_kandidat(judul, penulis, kandidat):
    """Terima kandidat hanya kalau judulnya benar-benar buku yang sama.

    Aturan longgar berbasis substring TIDAK dipakai: judul pendek seperti
    'Energi', 'Hutan', 'Karate' akan cocok dengan 'Energi Terbarukan',
    'Pengelolaan Hutan Indonesia', 'Pembelajaran Beladiri Karate' — semuanya
    buku lain. Lebih baik placeholder daripada memasang sampul buku yang salah.
    """
    target = norm(judul)
    best, best_score = None, 0.0

    for c in kandidat:
        t_sim = SequenceMatcher(None, target, norm(c["title"])).ratio()
        a_sim = skor_penulis(penulis, c.get("creator"))
        penerbit = norm(c.get("publisher") or "")

        # Mayoritas koleksi ini terbitan Alprin/ARC Media — kecocokan penerbit
        # adalah sinyal kuat bahwa ini memang edisi yang sama.
        penerbit_cocok = any(p in penerbit for p in ("alprin", "arc media", "gading"))

        diterima = (
            t_sim >= 0.93 and (a_sim is None or a_sim >= 0.34)
        ) or (
            t_sim >= 0.85 and a_sim is not None and a_sim >= 0.5
        ) or (
            t_sim >= 0.88 and penerbit_cocok
        )

        if diterima and t_sim > best_score:
            best, best_score = c, t_sim
        elif not diterima:
            best_score = max(best_score, 0.0)

    if best:
        return best, round(best_score, 3)
    # Skor tertinggi yang ditolak — untuk pelaporan saja
    tertinggi = max(
        (SequenceMatcher(None, target, norm(c["title"])).ratio() for c in kandidat),
        default=0.0,
    )
    return None, round(tertinggi, 3)


def cari_volume(judul, penulis):
    """Coba semua strategi query lalu ambil kecocokan terbaik secara global.

    Berhenti di query pertama yang lolos akan melewatkan kandidat yang lebih
    tepat dari query berikutnya, jadi semuanya dijalankan.
    """
    judul_bersih = re.sub(r"[:\(\)\[\]\-—,\.]+", " ", judul).strip()
    ada_penulis = penulis != "Tidak Tertera"
    queries = [
        f'"{judul}" {penulis}' if ada_penulis else f'"{judul}"',
        f'"{judul}"',
        f'"{judul}" Alprin',          # mayoritas koleksi ini terbitan Alprin
        f'{judul_bersih} {penulis}' if ada_penulis else judul_bersih,
        judul_bersih,
    ]

    terbaik, skor_terbaik, query_terbaik = None, 0.0, None
    skor_ditolak = 0.0
    seen = set()

    for q in queries:
        if q in seen:
            continue
        seen.add(q)
        hasil = gdata_search(q)
        if hasil:
            pilihan, skor = pilih_kandidat(judul, penulis, hasil)
            if pilihan and skor > skor_terbaik:
                terbaik, skor_terbaik, query_terbaik = pilihan, skor, q
            elif not pilihan:
                skor_ditolak = max(skor_ditolak, skor)
        if skor_terbaik >= 0.99:      # judul identik, tidak perlu query lain
            break
        time.sleep(0.3)

    if terbaik:
        return terbaik, skor_terbaik, query_terbaik
    return None, skor_ditolak, None


# ── Gambar ──────────────────────────────────────────────────────────────────
def unduh_cover(vol_id):
    """Ambil cover resolusi terbaik yang tersedia. edge=curl sengaja TIDAK dipakai
    supaya sampul rata, bukan efek lengkung halaman."""
    terbaik = None
    for zoom in (4, 3, 2, 1):
        url = (f"https://books.google.com/books/content?id={vol_id}"
               f"&printsec=frontcover&img=1&zoom={zoom}")
        try:
            body = http_get(url, timeout=30)
        except Exception:
            continue
        if len(body) < 3000:          # placeholder "no cover" Google berukuran mungil
            continue
        try:
            im = Image.open(BytesIO(body))
            im.load()
        except Exception:
            continue
        if terbaik is None or im.width > terbaik.width:
            terbaik = im
        if im.width >= TARGET_W:      # sudah cukup tajam, tidak perlu zoom lain
            break

    # Sumber di bawah 220px akan pecah saat ditampilkan di grid katalog —
    # lebih baik pakai placeholder yang tajam daripada cover asli yang buram.
    if terbaik is not None and terbaik.width < 220:
        return None
    return terbaik


def simpan_webp(im, dest):
    im = im.convert("RGB")
    if im.width > TARGET_W:
        h = round(im.height * TARGET_W / im.width)
        im = im.resize((TARGET_W, h), Image.LANCZOS)
    im.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)
    return dest.stat().st_size


# Palet placeholder per kategori — cukup kontras untuk teks putih.
PALET = {
    "Matematika": (37, 99, 235), "IPA": (5, 150, 105), "IPS": (217, 119, 6),
    "Bahasa Indonesia": (190, 24, 93), "Bahasa Inggris": (124, 58, 237),
    "PKN": (185, 28, 28), "Sejarah": (146, 64, 14), "Biologi": (22, 163, 74),
    "Fisika": (2, 132, 199), "Kimia": (168, 85, 247), "Fiksi": (219, 39, 119),
    "Non-Fiksi": (71, 85, 105), "Sains": (13, 148, 136), "Teknologi": (79, 70, 229),
    "Komik": (234, 88, 12), "Olahraga": (202, 138, 4), "Agama": (15, 118, 110),
}


def muat_font(ukuran, tebal=False):
    for nama in (["segoeuib.ttf", "arialbd.ttf"] if tebal else ["segoeui.ttf", "arial.ttf"]):
        p = Path(r"C:\Windows\Fonts") / nama
        if p.exists():
            return ImageFont.truetype(str(p), ukuran)
    return ImageFont.load_default()


def bungkus(draw, teks, font, lebar_maks):
    kata, baris, kini = teks.split(), [], ""
    for k in kata:
        coba = f"{kini} {k}".strip()
        if draw.textlength(coba, font=font) <= lebar_maks:
            kini = coba
        else:
            if kini:
                baris.append(kini)
            kini = k
    if kini:
        baris.append(kini)
    return baris


def buat_placeholder(judul, penulis, kategori, dest):
    """Cover tipografis: blok warna kategori + judul & penulis. Jelas bukan sampul
    asli, tapi konsisten dan tidak menyesatkan seperti memakai cover buku lain."""
    W, H = TARGET_W, round(TARGET_W * 1.45)
    dasar = PALET.get(kategori, (71, 85, 105))
    im = Image.new("RGB", (W, H), dasar)
    d = ImageDraw.Draw(im)

    # Gradasi vertikal halus supaya tidak terlihat seperti kotak polos
    for y in range(H):
        f = y / H * 0.35
        d.line([(0, y), (W, y)], fill=tuple(max(0, round(c * (1 - f))) for c in dasar))

    marjin = round(W * 0.09)
    d.rectangle([marjin, marjin, W - marjin, H - marjin], outline=(255, 255, 255, 60), width=2)

    f_judul = muat_font(round(W * 0.085), tebal=True)
    f_penulis = muat_font(round(W * 0.052))
    f_label = muat_font(round(W * 0.042), tebal=True)

    isi_lebar = W - 2 * marjin - round(W * 0.06)
    x = marjin + round(W * 0.03)

    baris = bungkus(d, judul, f_judul, isi_lebar)[:6]
    tinggi_baris = round(W * 0.105)
    y = round(H * 0.30)
    for b in baris:
        d.text((x, y), b, font=f_judul, fill=(255, 255, 255))
        y += tinggi_baris

    if penulis and penulis != "Tidak Tertera":
        y += round(H * 0.02)
        for b in bungkus(d, penulis, f_penulis, isi_lebar)[:2]:
            d.text((x, y), b, font=f_penulis, fill=(255, 255, 255, 200))
            y += round(W * 0.065)

    d.text((x, H - marjin - round(W * 0.08)), kategori.upper(), font=f_label,
           fill=(255, 255, 255))

    im.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)
    return dest.stat().st_size


def slug(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()[:55]


def bersihkan_sinopsis(desc, judul, penulis):
    """dc:description Google Books sering cuma hasil OCR sampul ('SUPARTI Peradaban
    JEPANG 0000 ALPRIN...'). Tolak yang seperti itu, pakai hanya deskripsi asli."""
    if not desc:
        return None
    desc = re.sub(r"\s+", " ", desc).strip()
    if len(desc) < 60:
        return None
    # Kalau sebagian besar isinya pengulangan judul/penulis -> OCR sampul
    tokens = norm(desc).split()
    noise = set(norm(judul).split()) | set(norm(penulis).split())
    if tokens and sum(1 for t in tokens if t in noise) / len(tokens) > 0.45:
        return None
    if not re.search(r"[a-z]{3,}\s+[a-z]{3,}\s+[a-z]{3,}", desc.lower()):
        return None
    return desc[:900]


def sinopsis_cadangan(judul, kategori, penulis):
    subjek = {
        "Matematika": "konsep matematika", "Fisika": "konsep fisika",
        "Kimia": "konsep kimia", "Biologi": "materi biologi",
        "Sains": "pengetahuan sains", "Sejarah": "materi sejarah",
        "IPS": "materi ilmu pengetahuan sosial", "Olahraga": "materi olahraga dan kesehatan",
        "Agama": "materi pendidikan agama", "Teknologi": "materi teknologi",
        "Bahasa Inggris": "bacaan berbahasa Inggris", "Komik": "cerita bergambar",
        "Fiksi": "karya fiksi",
    }.get(kategori, "pengetahuan umum")
    pengarang = f" karya {penulis}" if penulis != "Tidak Tertera" else ""
    return (f"\"{judul}\"{pengarang} membahas {subjek} untuk jenjang SMP. "
            f"Buku ini merupakan koleksi Perpustakaan SMPN 1 Kemang pada kategori {kategori}.")


def main():
    buku = json.loads(IN_PATH.read_text(encoding="utf-8"))
    total = len(buku)
    hasil = []
    stat = {"gbooks": 0, "placeholder": 0}

    for i, b in enumerate(buku, 1):
        judul, penulis = b["judul"], b["penulis"]
        print(f"[{i}/{total}] {judul[:58]}", flush=True)

        vol, skor, query = cari_volume(judul, penulis)
        nama_file = f"{slug(judul)}-{slug(penulis)}.webp"
        dest = COVERS_DIR / nama_file

        isbn = sinopsis = penerbit = None
        sumber = None
        kategori = tebak_kategori(judul, penulis, vol["subject"] if vol else None)

        if vol:
            im = unduh_cover(vol["vol_id"])
            if im is not None:
                asal = im.size
                ukuran = simpan_webp(im, dest)
                sumber = "google_books"
                isbn = vol["isbn"]
                penerbit = vol["publisher"]
                sinopsis = bersihkan_sinopsis(vol["description"], judul, penulis)
                stat["gbooks"] += 1
                print(f"      cover asli  {ukuran//1024} KB  src={asal[0]}x{asal[1]}"
                      f"  (match {skor})", flush=True)

        if sumber is None:
            ukuran = buat_placeholder(judul, penulis, kategori, dest)
            sumber = "placeholder"
            stat["placeholder"] += 1
            print(f"      placeholder {ukuran//1024} KB  (skor tertinggi {skor})", flush=True)

        if not sinopsis:
            sinopsis = sinopsis_cadangan(judul, kategori, penulis)

        hasil.append({
            "judul": judul,
            "penulis": penulis,
            "kategori": kategori,
            "stok": b["stok"],
            "isbn": isbn,
            "penerbit": penerbit,
            "sinopsis": sinopsis,
            "cover_filename": nama_file,
            "cover_source": sumber,
            "match_score": skor,
            "gbooks_query": query,
        })

        # Tulis berkala supaya proses panjang bisa dilanjut kalau terputus
        if i % 25 == 0 or i == total:
            OUT_PATH.write_text(json.dumps(hasil, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        time.sleep(0.25)

    OUT_PATH.write_text(json.dumps(hasil, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== RINGKASAN ===")
    print(f"  Cover asli (Google Books) : {stat['gbooks']}")
    print(f"  Cover placeholder         : {stat['placeholder']}")
    print(f"  Total                     : {total}")
    dgn_isbn = sum(1 for r in hasil if r["isbn"])
    dgn_sin = sum(1 for r in hasil if r["cover_source"] == "google_books" and
                  r["sinopsis"] and not r["sinopsis"].startswith('"'))
    print(f"  Dapat ISBN asli           : {dgn_isbn}")
    print(f"  Dapat sinopsis asli       : {dgn_sin}")
    print("\nSebaran kategori:")
    from collections import Counter
    for k, v in Counter(r["kategori"] for r in hasil).most_common():
        print(f"  {k:<18} {v}")


if __name__ == "__main__":
    sys.exit(main())
