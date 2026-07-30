"""
retry_missing_covers.py — Retry cover untuk entri yang gagal di fetch_covers.py.

Perbaikan dari run pertama:
  - Cek SEMUA hasil pencarian (bukan cuma docs[0]) untuk cover_i pertama yang ada
  - Retry otomatis 1x kalau request gagal (timeout/network hiccup)
  - Query fallback tambahan: judul tanpa tanda baca (: * ' -)
"""
import json
import re
import subprocess
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

RESULT_PATH = Path(__file__).parent / "famous_books_with_covers.json"
COVERS_DIR = Path(r"D:\xampp\htdocs\libra\uploads\covers")

UA = "LIBRA-SchoolLibraryProject/1.0 (educational use; contact: libra-project@example.com)"


def http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_get_retry(url, timeout=15, tries=2):
    last_err = None
    for _ in range(tries):
        try:
            return http_get(url, timeout=timeout)
        except Exception as e:
            last_err = e
            time.sleep(1.5)
    raise last_err


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:60]


def openlibrary_search_best(query):
    url = "https://openlibrary.org/search.json?q=" + urllib.parse.quote(query) + \
          "&limit=5&fields=title,cover_i,isbn"
    try:
        body = http_get_retry(url)
        data = json.loads(body)
        for doc in data.get("docs") or []:
            if doc.get("cover_i"):
                return doc["cover_i"], (doc.get("isbn") or [None])[0]
    except Exception:
        pass
    return None, None


def wikipedia_thumbnail(title, lang):
    page = title.replace(" ", "_")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(page)
    try:
        body = http_get_retry(url)
        data = json.loads(body)
        return (data.get("originalimage") or {}).get("source") or (data.get("thumbnail") or {}).get("source")
    except Exception:
        return None


def download_image(url, dest_path):
    # upload.wikimedia.org memblokir fingerprint Python urllib (403) meski curl lolos —
    # pakai curl sebagai subprocess untuk unduh gambar aktual.
    try:
        proc = subprocess.run(
            ["curl", "-sL", "--max-time", "20", "-o", str(dest_path), url],
            capture_output=True, timeout=25,
        )
        if proc.returncode != 0:
            return False, f"curl exit {proc.returncode}: {proc.stderr.decode(errors='ignore')[:200]}"
    except Exception as e:
        return False, str(e)

    if not dest_path.exists():
        return False, "file tidak terbuat"
    body = dest_path.read_bytes()
    if len(body) < 2000:
        dest_path.unlink(missing_ok=True)
        return False, f"terlalu kecil ({len(body)} bytes)"
    if body[:4] == b"GIF8":
        dest_path.unlink(missing_ok=True)
        return False, "GIF placeholder"
    if not (body[:2] == b"\xff\xd8" or body[:8] == b"\x89PNG\r\n\x1a\n" or body[:4] == b"RIFF"):
        dest_path.unlink(missing_ok=True)
        return False, "bukan format gambar valid"
    return True, None


def clean_title(title):
    return re.sub(r"[:*'\u2019-]", " ", title)


def main():
    results = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    missing = [r for r in results if not r["cover_filename"]]
    print(f"Mencoba ulang {len(missing)} buku...\n")

    fixed = 0
    for r in missing:
        judul = r["judul"]
        penulis = r["penulis"]
        print(f"- {judul}", flush=True)

        cover_url = None
        source = None
        isbn = None

        for q in [r["query"], judul, clean_title(judul) + " " + penulis, clean_title(judul)]:
            cover_i, found_isbn = openlibrary_search_best(q)
            if cover_i:
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
                source = "openlibrary"
                isbn = found_isbn
                break
            time.sleep(0.4)

        if not cover_url:
            for lang in ("id", "en"):
                thumb = wikipedia_thumbnail(judul, lang)
                if not thumb:
                    thumb = wikipedia_thumbnail(clean_title(judul), lang)
                if thumb:
                    cover_url = thumb
                    source = f"wikipedia_{lang}"
                    break
                time.sleep(0.4)

        if cover_url:
            ext = ".png" if ".png" in cover_url.lower() else ".jpg"
            filename = f"{slugify(judul)}-{slugify(penulis)}{ext}"
            dest = COVERS_DIR / filename
            ok, err = download_image(cover_url, dest)
            if ok:
                r["cover_filename"] = filename
                r["cover_source"] = source
                r["cover_error"] = None
                r["isbn"] = r.get("isbn") or isbn
                fixed += 1
                print(f"    -> OK via {source}")
            else:
                r["cover_error"] = err
                print(f"    -> gagal download: {err}")
        else:
            print("    -> tetap tidak ditemukan")

        time.sleep(0.3)

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    still_missing = [r["judul"] for r in results if not r["cover_filename"]]
    print(f"\n=== Retry selesai: {fixed}/{len(missing)} berhasil diperbaiki ===")
    print(f"Total masih tanpa cover: {len(still_missing)}")
    for t in still_missing:
        print(f"  - {t}")


if __name__ == "__main__":
    main()
