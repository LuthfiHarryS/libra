"""
ambil_tangkapan_layar.py — Ambil ulang Gambar 3.11-3.15 dari sistem produksi.

Tangkapan diambil dengan Playwright sehingga hanya memuat isi halaman, tanpa
bilah alamat maupun bingkai peramban — sesuai kebutuhan gambar pada Penulisan
Ilmiah.

Sumber: https://perpuslibra.web.id (lingkungan produksi, bukan localhost),
supaya isi katalog dan tampilan sesuai keadaan sistem yang sebenarnya.

Hasil: figma/tangkapan/gambar_3_xx.png
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASIS = 'https://perpuslibra.web.id'
SISWA = ('luthfi1', 'Luthfi123')
ADMIN = ('admin', 'admin123')

KELUARAN = Path(__file__).resolve().parents[2] / 'figma' / 'tangkapan'
KELUARAN.mkdir(parents=True, exist_ok=True)

# Lebar 1366 mewakili laptop sekolah pada umumnya dan menghasilkan tata letak
# yang masih terbaca saat gambar diperkecil ke lebar kolom dokumen.
VIEWPORT = {'width': 1366, 'height': 850}


def simpan(page, nama, full=False):
    berkas = KELUARAN / f'{nama}.png'
    page.screenshot(path=str(berkas), full_page=full)
    print(f'  tersimpan: {berkas.name}  ({berkas.stat().st_size // 1024} KB)')


def login(page, username, password):
    page.goto(f'{BASIS}/login', wait_until='networkidle')
    page.fill('input[type="text"], input[name="username"]', username)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1500)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        page = ctx.new_page()

        # ── Gambar 3.11 — Halaman Login ───────────────────────────────────
        print('Gambar 3.11 Halaman Login Pengguna')
        page.goto(f'{BASIS}/login', wait_until='networkidle')
        page.wait_for_timeout(1200)
        simpan(page, 'gambar_3_11_login')

        # ── Login sebagai siswa ───────────────────────────────────────────
        login(page, *SISWA)
        print('  login siswa ->', page.url)

        # ── Gambar 3.12 — Katalog Buku ────────────────────────────────────
        print('Gambar 3.12 Halaman Katalog Buku')
        page.goto(f'{BASIS}/katalog', wait_until='networkidle')
        page.wait_for_timeout(2500)          # tunggu cover selesai dimuat
        simpan(page, 'gambar_3_12_katalog')

        # ── Gambar 3.14 — Rekomendasi Buku Serupa ─────────────────────────
        print('Gambar 3.14 Hasil Rekomendasi Buku Serupa')
        kartu = page.locator('a[href^="/buku/"]').first
        if kartu.count() == 0:
            kartu = page.locator('[class*="card"] a').first
        kartu.click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2500)
        # Gulirkan ke panel rekomendasi bila ada
        for teks in ['Buku Serupa', 'Rekomendasi', 'Serupa']:
            panel = page.get_by_text(teks, exact=False).first
            if panel.count() > 0:
                panel.scroll_into_view_if_needed()
                page.wait_for_timeout(1200)
                break
        simpan(page, 'gambar_3_14_rekomendasi')

        # ── Gambar 3.15 — Antarmuka Chatbot ───────────────────────────────
        print('Gambar 3.15 Antarmuka Chatbot LIBRA')
        page.goto(f'{BASIS}/', wait_until='networkidle')
        page.wait_for_timeout(2000)
        fab = page.locator('button[aria-label="Buka chat"]')
        if fab.count() == 0:
            fab = page.locator('button').filter(has=page.locator('svg')).last
        fab.click()
        page.wait_for_timeout(1200)
        # Kirim satu pertanyaan agar tampak jawaban dari katalog
        kotak = page.locator('input[placeholder*="Tanya"]')
        if kotak.count() > 0:
            kotak.fill('ada buku komik tidak')
            kotak.press('Enter')
            page.wait_for_timeout(3500)
        simpan(page, 'gambar_3_15_chatbot')

        # ── Gambar 3.13 — Dasbor Petugas ──────────────────────────────────
        print('Gambar 3.13 Dashboard Petugas Perpustakaan')
        ctx.clear_cookies()
        page2 = ctx.new_page()
        page2.goto(f'{BASIS}/login', wait_until='networkidle')
        page2.evaluate("localStorage.clear()")
        login(page2, *ADMIN)
        print('  login admin ->', page2.url)
        page2.wait_for_timeout(2500)
        simpan(page2, 'gambar_3_13_dasbor_admin')

        browser.close()

    print(f'\nSemua tangkapan tersimpan di: {KELUARAN}')


if __name__ == '__main__':
    sys.exit(main())
