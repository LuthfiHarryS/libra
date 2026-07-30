"""
fetch_covers.py — Unduh cover buku untuk seed 150 buku terkenal (LIBRA).

Sumber cover (urutan fallback):
  1. Open Library Search API (title+author) -> cover_i -> covers.openlibrary.org/b/id/{id}-L.jpg
  2. Open Library Search API (title saja)
  3. Wikipedia ID REST summary API (thumbnail/originalimage)
  4. Wikipedia EN REST summary API (thumbnail/originalimage)

Hasil disimpan ke: python/scripts/famous_books_with_covers.json
Gambar diunduh ke: D:\\xampp\\htdocs\\libra\\uploads\\covers\\
"""
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

DATA_PATH = Path(__file__).parent / "famous_books_seed_data.json"
OUT_PATH = Path(__file__).parent / "famous_books_with_covers.json"
COVERS_DIR = Path(r"D:\xampp\htdocs\libra\uploads\covers")
COVERS_DIR.mkdir(parents=True, exist_ok=True)

UA = "LIBRA-SchoolLibraryProject/1.0 (educational use; contact: libra-project@example.com)"


def http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:60]


def openlibrary_search(query):
    url = "https://openlibrary.org/search.json?q=" + urllib.parse.quote(query) + \
          "&limit=1&fields=title,cover_i,isbn"
    try:
        body, _ = http_get(url)
        data = json.loads(body)
        docs = data.get("docs") or []
        if docs and docs[0].get("cover_i"):
            return docs[0]["cover_i"], (docs[0].get("isbn") or [None])[0]
    except Exception:
        pass
    return None, None


def wikipedia_thumbnail(title, lang):
    page = title.replace(" ", "_")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(page)
    try:
        body, _ = http_get(url)
        data = json.loads(body)
        thumb = (data.get("originalimage") or {}).get("source") or (data.get("thumbnail") or {}).get("source")
        return thumb
    except Exception:
        return None


def download_image(url, dest_path):
    try:
        body, ctype = http_get(url, timeout=20)
    except Exception as e:
        return False, str(e)

    if len(body) < 2000:
        return False, f"terlalu kecil ({len(body)} bytes) — kemungkinan placeholder"
    if body[:4] == b"GIF8":
        return False, "GIF placeholder (no cover)"
    if not (body[:2] == b"\xff\xd8" or body[:8] == b"\x89PNG\r\n\x1a\n" or body[:4] == b"RIFF"):
        return False, "bukan format gambar valid (jpg/png/webp)"

    dest_path.write_bytes(body)
    return True, None


def main():
    books = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    results = []
    stats = {"openlibrary": 0, "wikipedia_id": 0, "wikipedia_en": 0, "missing": 0}

    for i, book in enumerate(books, 1):
        judul = book["judul"]
        penulis = book["penulis"]
        query = book["query"]
        print(f"[{i}/{len(books)}] {judul} — {penulis}", flush=True)

        cover_url = None
        source = None
        isbn = None

        cover_i, found_isbn = openlibrary_search(query)
        if not cover_i:
            cover_i, found_isbn = openlibrary_search(judul)
        if cover_i:
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
            source = "openlibrary"
            isbn = found_isbn

        if not cover_url:
            thumb = wikipedia_thumbnail(judul, "id")
            if thumb:
                cover_url = thumb
                source = "wikipedia_id"

        if not cover_url:
            thumb = wikipedia_thumbnail(judul, "en")
            if thumb:
                cover_url = thumb
                source = "wikipedia_en"

        filename = None
        error = None
        if cover_url:
            ext = ".png" if ".png" in cover_url.lower() else ".jpg"
            filename = f"{slugify(judul)}-{slugify(penulis)}{ext}"
            dest = COVERS_DIR / filename
            ok, err = download_image(cover_url, dest)
            if ok:
                stats[source] += 1
            else:
                error = err
                filename = None
                source = None
                stats["missing"] += 1
        else:
            stats["missing"] += 1

        results.append({**book, "isbn": isbn, "cover_filename": filename,
                         "cover_source": source, "cover_error": error})
        time.sleep(0.3)

    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== RINGKASAN ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"Total: {len(books)}")
    missing_titles = [r["judul"] for r in results if not r["cover_filename"]]
    if missing_titles:
        print(f"\nBuku TANPA cover ({len(missing_titles)}):")
        for t in missing_titles:
            print(f"  - {t}")


if __name__ == "__main__":
    main()
