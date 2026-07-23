# LIBRA — Layanan Informasi Buku & Referensi Akademik

Sistem perpustakaan digital untuk SMPN 1 Kemang: katalog buku, peminjaman,
rekomendasi buku berbasis *content-based filtering*, dan chatbot layanan
perpustakaan berbahasa Indonesia.

Dikerjakan sebagai proyek **Penulisan Ilmiah** (Semester 6).

---

## Fitur

**Pengguna**
- Registrasi & login (autentikasi JWT)
- Katalog buku dengan pencarian, filter, dan paginasi
- Detail buku + rekomendasi "Buku Serupa", "Untukmu", dan "Populer"
- Peminjaman buku dengan *timeline* status dan hitung mundur jatuh tempo
- Daftar favorit, halaman profil, tema terang/gelap, dan notifikasi
- **Chatbot** layanan perpustakaan (klasifikasi intent LinearSVC)

**Admin**
- Dashboard statistik
- Manajemen buku (CRUD)
- Manajemen peminjaman

---

## Arsitektur

```
                ┌──────────────┐
                │    React     │  (Vite dev server :5173)
                └──────┬───────┘
                       │
        ┌──────────────┴───────────────┐
        │                              │
        ▼ /api (proxy → :8080)         ▼ langsung (:5001)
┌───────────────┐              ┌──────────────────┐
│  PHP 8.2 API  │              │  Flask Chatbot   │
│  CRUD + Auth  │              │  LinearSVC       │
└───────┬───────┘              └──────────────────┘
        │
        ├──────────► MySQL 8 (utf8mb4, FULLTEXT)
        │
        └── cURL ──► Flask CBF (:5000) — rekomendasi
```

Prinsip: **Python tidak pernah mengakses MySQL secara langsung** — seluruh akses
data melalui lapisan PHP.

---

## Tech Stack

| Lapisan     | Teknologi                                                            |
|-------------|----------------------------------------------------------------------|
| Frontend    | React 18, Vite 6, TypeScript, Tailwind CSS v4, React Router 7, Zustand, Axios |
| Backend API | PHP 8.2 native (tanpa framework) + PDO + firebase/php-jwt — port 8080 |
| Database    | MySQL 8 (utf8mb4, FULLTEXT index pada judul/penulis/sinopsis)         |
| ML Service  | Python 3.11, Flask 3.1, scikit-learn, PySastrawi — port 5000 & 5001   |

---

## Isi Repositori

```
.
├── react/                  # Frontend React + Vite + TypeScript
│   ├── src/pages/          # Halaman pengguna & admin
│   ├── src/components/     # ChatWidget, BookCard, Navbar, dll.
│   ├── src/services/api.ts # Axios instance (baseURL '/api')
│   └── src/store/          # State global (Zustand)
├── python/
│   ├── cbf/                # Layanan rekomendasi content-based filtering (:5000)
│   └── chatbot/            # Klasifikasi intent chatbot + tes (:5001)
└── database/
    ├── schema.sql          # Skema MySQL
    └── seed.php            # Pengisian data awal
```

> **Catatan:** lapisan **API PHP (port 8080)** yang menangani seluruh CRUD dan
> autentikasi **tidak termasuk dalam repositori ini**. Tanpa layanan tersebut,
> frontend hanya dapat dijalankan sampai tahap tampilan — permintaan ke `/api`
> tidak akan mendapat respons.

---

## Menjalankan Secara Lokal

### 1. Database

```bash
mysql -u root < database/schema.sql
php database/seed.php          # mengisi data contoh
```

### 2. Frontend

```bash
cd react
npm install
npm run dev                    # http://localhost:5173
```

Vite otomatis mem-proxy `/api` ke `http://localhost:8080` (lihat `react/vite.config.ts`).

### 3. Layanan rekomendasi (CBF)

```bash
cd python/cbf
pip install -r requirements.txt
python app.py                  # http://localhost:5000
```

### 4. Layanan chatbot

```bash
cd python/chatbot
pip install -r requirements.txt
python app.py                  # http://localhost:5001
```

Frontend membaca alamat chatbot dari variabel `VITE_CHATBOT_URL` bila disetel.

### 5. Menjalankan tes chatbot

```bash
cd python
pytest chatbot/tests -v
```

---

## Catatan Teknis

- Satu fungsi `preprocess()` dipakai untuk **training maupun inference** chatbot
  agar tidak terjadi ketidakcocokan fitur.
- `TfidfVectorizer(min_df=1)` digunakan karena korpus intent relatif kecil.
- TF-IDF di-*fit* sekali saat Flask *startup*, bukan setiap permintaan.
- PySastrawi dipakai untuk *stemming* Bahasa Indonesia.
- LinearSVC menjadi pengklasifikasi utama; MultinomialNB disertakan sebagai
  pembanding untuk keperluan analisis akademik.
- Seluruh lapisan memakai `utf8mb4`.

---

## Lisensi

Bebas digunakan untuk keperluan edukasi dan pembelajaran.
