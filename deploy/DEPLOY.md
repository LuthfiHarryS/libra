# Deploy LIBRA ke VPS

Target: `https://perpuslibra.web.id` — VPS Biznet NEO Lite, IP `<IP_VPS>`,
Ubuntu 24.04, 2 vCPU / 4 GB / 60 GB.

> `<IP_VPS>` dan `<USER_SSH>` sengaja ditulis sebagai placeholder karena
> repositori ini publik. Nilai sebenarnya ada di catatan pribadi, bukan di sini:
> IP memang bisa didapat dari DNS, tetapi nama pengguna SSH tidak perlu
> diumumkan. Ganti keduanya saat menyalin perintah di bawah.

Struktur akhir di server:

```
/var/www/libra/
├── public/          <- hasil build React (react/dist)
├── api/             <- PHP (dari D:\xampp\htdocs\libra\api)
├── vendor/          <- composer
├── uploads/covers/  <- 261 cover .webp
└── python/          <- cbf/, chatbot/, .venv/
/etc/libra/libra.env <- kredensial (chmod 640)
```

Satu origin melayani semuanya, jadi tidak ada mixed-content dan CORS tidak terpakai.

---

## 0. DNS (lakukan lebih dulu — propagasi butuh waktu)

Di panel pengelola `perpuslibra.web.id`, buat dua A record:

| Type | Name | Value |
|------|------|-------|
| A | `@` | `<IP_VPS>` |
| A | `www` | `<IP_VPS>` |

Cek dari laptop sampai IP-nya muncul benar:

```powershell
nslookup perpuslibra.web.id 8.8.8.8
```

Certbot akan **gagal** kalau DNS belum menunjuk ke VPS — jangan lanjut ke langkah 8
sebelum ini benar.

## 1. Firewall Biznet + UFW

Di panel Biznet buka port **22, 80, 443** saja. Port 3306, 5000, 5001 jangan dibuka.

```bash
ssh -i ~/.ssh/libra_vps <USER_SSH>@<IP_VPS>

sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

## 2. Paket dasar

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx mariadb-server \
    php8.3-fpm php8.3-mysql php8.3-mbstring php8.3-xml php8.3-curl php8.3-gd \
    python3-venv python3-dev build-essential \
    unzip curl git
```

Node untuk build React:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

## 3. Swap 2 GB

Jaring pengaman supaya proses tidak kena OOM-kill saat sistem ditinggal berbulan-bulan.

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

## 4. Database

```bash
sudo mysql_secure_installation      # set root password, jawab Y untuk sisanya
```

Buat database dan user khusus aplikasi — **jangan pakai root untuk aplikasi**:

```bash
sudo mysql
```

```sql
CREATE DATABASE libra_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'libra_app'@'localhost' IDENTIFIED BY 'GANTI_PASSWORD_KUAT_DISINI';
GRANT SELECT, INSERT, UPDATE, DELETE ON libra_db.* TO 'libra_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Catatan: `libra_app` sengaja tanpa DDL (CREATE/DROP/ALTER). Kalau ada SQL injection
yang lolos, kerusakannya terbatas pada data, bukan struktur tabel.

## 5. Kirim kode dari laptop

Dari PowerShell di laptop (bukan di server):

```powershell
cd "c:\Luthfi\Kuliah\Semester 6\pi"

# Build React dulu di laptop — lebih cepat dan tidak membebani VPS
cd react
npm ci
npm run build
cd ..

# Dump database lokal (261 buku + cover relatif + users)
& D:\xampp\mysql\bin\mysqldump.exe -u root --default-character-set=utf8mb4 libra_db > libra_dump.sql

# Kirim
scp -i $env:USERPROFILE\.ssh\libra_vps -r react\dist <USER_SSH>@<IP_VPS>:/tmp/public
scp -i $env:USERPROFILE\.ssh\libra_vps -r D:\xampp\htdocs\libra\api <USER_SSH>@<IP_VPS>:/tmp/api
scp -i $env:USERPROFILE\.ssh\libra_vps -r D:\xampp\htdocs\libra\vendor <USER_SSH>@<IP_VPS>:/tmp/vendor
scp -i $env:USERPROFILE\.ssh\libra_vps -r D:\xampp\htdocs\libra\uploads <USER_SSH>@<IP_VPS>:/tmp/uploads
scp -i $env:USERPROFILE\.ssh\libra_vps -r python\cbf python\chatbot <USER_SSH>@<IP_VPS>:/tmp/
scp -i $env:USERPROFILE\.ssh\libra_vps libra_dump.sql <USER_SSH>@<IP_VPS>:/tmp/
scp -i $env:USERPROFILE\.ssh\libra_vps deploy\* <USER_SSH>@<IP_VPS>:/tmp/
```

## 6. Susun di server

```bash
sudo mkdir -p /var/www/libra/python
sudo mv /tmp/public /tmp/api /tmp/vendor /tmp/uploads /var/www/libra/
sudo mv /tmp/cbf /tmp/chatbot /var/www/libra/python/

sudo useradd -r -s /usr/sbin/nologin libra || true
sudo chown -R libra:www-data /var/www/libra
sudo find /var/www/libra -type d -exec chmod 750 {} \;
sudo find /var/www/libra -type f -exec chmod 640 {} \;
sudo chmod -R 750 /var/www/libra/uploads      # PHP perlu tulis saat upload cover
sudo chown -R www-data:www-data /var/www/libra/uploads

# WAJIB — jangan dilewati. Izin 750/640 di atas TIDAK cukup untuk public/.
# Menerapkannya ke public/ membuat Nginx membalas 403 pada "/" dan 500 pada
# seluruh rute SPA, karena fallback try_files juga mengarah ke index.html yang
# sama. Isi public/ memang seluruhnya aset publik (HTML, JS, CSS, gambar) yang
# dikirim ke setiap pengunjung, jadi boleh dibaca siapa saja. api/ yang memuat
# config.local.php tetap 640 dan tidak terpengaruh.
sudo chmod o+x /var/www/libra                 # boleh ditembus, tidak boleh dilihat isinya
sudo chmod -R o+rX /var/www/libra/public      # X besar: execute hanya untuk direktori
```

Impor database:

```bash
sudo mysql libra_db < /tmp/libra_dump.sql
sudo mysql libra_db -e "SELECT COUNT(*) AS buku, SUM(cover_url LIKE '/uploads/%') AS cover_relatif FROM buku;"
```

Harus keluar `261` dan `261`. Kalau `cover_relatif` bukan 261, jalankan
`database/migrate_relative_urls.sql` dulu di laptop lalu dump ulang.

## 7. Konfigurasi

**Environment untuk layanan Python:**

```bash
sudo mkdir -p /etc/libra
sudo tee /etc/libra/libra.env >/dev/null <<'EOF'
LIBRA_DB_HOST=localhost
LIBRA_DB_USER=libra_app
LIBRA_DB_PASS=GANTI_PASSWORD_KUAT_DISINI
LIBRA_DB_NAME=libra_db
CHATBOT_TRAIN_KEY=GANTI_DENGAN_SECRET_PANJANG
EOF
sudo chown root:libra /etc/libra/libra.env
sudo chmod 640 /etc/libra/libra.env
```

**Config PHP** — edit `/var/www/libra/api/config.local.php`:

```php
'JWT_SECRET' => '<hasil: php -r "echo bin2hex(random_bytes(32));">',
'CBF_URL'    => 'http://127.0.0.1:5000',
'DB_HOST'    => 'localhost',
'DB_NAME'    => 'libra_db',
'DB_USER'    => 'libra_app',
'DB_PASS'    => 'GANTI_PASSWORD_KUAT_DISINI',
```

JWT_SECRET **wajib** diganti. Yang dipakai di laptop sudah pernah ada di repo/riwayat,
jadi tidak boleh dipakai untuk sistem yang terbuka di internet.

```bash
sudo chmod 640 /var/www/libra/api/config.local.php
sudo chown libra:www-data /var/www/libra/api/config.local.php
```

## 8. Python venv + systemd

```bash
cd /var/www/libra/python
sudo -u libra python3 -m venv .venv
sudo -u libra .venv/bin/pip install --upgrade pip
sudo -u libra .venv/bin/pip install -r cbf/requirements.txt
sudo -u libra .venv/bin/pip install -r chatbot/requirements.txt

sudo cp /tmp/libra-cbf.service /tmp/libra-chatbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now libra-cbf libra-chatbot
sudo systemctl status libra-cbf libra-chatbot --no-pager
```

Uji dari server sendiri:

```bash
curl -s localhost:5000/popular?limit=3
curl -s -X POST localhost:5001/chat -H 'Content-Type: application/json' -d '{"message":"cari buku matematika"}'
```

## 9. Nginx + SSL

```bash
sudo cp /tmp/nginx-perpuslibra.conf /etc/nginx/sites-available/perpuslibra
sudo ln -sf /etc/nginx/sites-available/perpuslibra /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Buka `http://perpuslibra.web.id` — katalog harus muncul. Baru lalu pasang SSL:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d perpuslibra.web.id -d www.perpuslibra.web.id
sudo systemctl status certbot.timer      # perpanjangan otomatis
```

## 10. Verifikasi akhir

```bash
curl -s https://perpuslibra.web.id/api/books?limit=2 | head -c 300
curl -s -o /dev/null -w '%{http_code}\n' https://perpuslibra.web.id/uploads/covers/peradaban-jepang-suparti.webp
curl -s -X POST https://perpuslibra.web.id/chat -H 'Content-Type: application/json' -d '{"message":"halo"}'
```

Lalu di browser: buka `https://perpuslibra.web.id`, login sebagai siswa, cek
katalog (cover muncul), detail buku (rekomendasi CBF muncul), dan widget chat.

---

## Yang perlu diingat

- **Backup**: `mysqldump libra_db` + folder `uploads/` adalah dua hal yang tidak bisa
  dibuat ulang. Jadwalkan cron harian ke luar VPS.
- **Kredensial produksi berbeda dari lokal.** JWT_SECRET, DB password, dan
  CHATBOT_TRAIN_KEY harus baru — jangan menyalin dari `config.local.php` laptop.
- **Update React**: jangan salin manual. Pakai `deploy/update-react.sh`, yang
  sudah memuat langkah izin berkas. Menyalin `dist` tanpa memperbaiki izinnya
  pernah membuat situs 403/500 — lihat catatan pada blok izin di atas.

  ```powershell
  cd react; npm run build
  scp -i $env:USERPROFILE\.ssh\libra_vps -r dist <USER_SSH>@<IP_VPS>:/tmp/dist_baru
  scp -i $env:USERPROFILE\.ssh\libra_vps ..\deploy\update-react.sh <USER_SSH>@<IP_VPS>:/tmp/
  ssh -i $env:USERPROFILE\.ssh\libra_vps <USER_SSH>@<IP_VPS> "bash /tmp/update-react.sh /tmp/dist_baru"
  ```

- **Update kode Python**: `scp` berkas `.py` ke `/var/www/libra/python/chatbot/`,
  lalu **hapus `models/*.joblib`** sebelum `sudo systemctl restart libra-chatbot`.
  Berkas joblib tidak masuk version control dan `load_or_train()` memuatnya dari
  disk bila ada, sehingga tanpa dihapus layanan tetap memakai model lama dan
  perubahan `dataset.py` maupun `preprocess.py` tidak berpengaruh sama sekali.
  Melatih ulang saat startup hanya memakan sekitar 1,5 detik.

- **Sitemap**: setelah katalog berubah, jalankan
  `python python/scripts/buat_sitemap.py` lalu build dan deploy ulang React.
  Sitemap usang membuat Google meminta URL buku yang sudah dihapus, menerima 200
  berisi index.html karena fallback SPA, lalu menandainya sebagai soft 404.

- Nginx tidak perlu di-reload untuk perubahan file statis.
