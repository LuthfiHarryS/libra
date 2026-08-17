#!/usr/bin/env bash
#
# update-react.sh — Pasang build React baru ke /var/www/libra/public.
#
# Dijalankan DI SERVER, setelah hasil `npm run build` disalin ke suatu direktori
# sementara. Pemakaian:
#
#     scp -r dist <USER_SSH>@<ip>:/tmp/dist_baru
#     ssh <USER_SSH>@<ip> "bash /tmp/update-react.sh /tmp/dist_baru"
#
# Skrip ini ada karena menyalin dist secara manual pernah mematikan situs.
# Penyebabnya izin berkas: DEPLOY.md menyuruh menerapkan 750/640 ke seluruh
# /var/www/libra, dan izin itu membuat Nginx membalas 403 pada "/" serta 500
# pada semua rute SPA. Langkah izin di bawah tidak boleh dilewati, jadi
# ditanamkan di sini alih-alih ditulis sebagai catatan yang bisa terlupa.
set -euo pipefail

SUMBER="${1:-}"
TUJUAN=/var/www/libra/public
CADANGAN="/var/www/libra/public.bak-$(date +%Y%m%d-%H%M%S)"

if [[ -z "$SUMBER" ]]; then
    echo "Pemakaian: bash update-react.sh <direktori-dist>" >&2
    exit 1
fi
if [[ ! -f "$SUMBER/index.html" ]]; then
    echo "GAGAL: '$SUMBER/index.html' tidak ada — apakah itu benar folder dist?" >&2
    exit 1
fi

# Sitemap, robots.txt, dan favicon.ico harus ikut, kalau tidak Google menerima
# index.html untuk /robots.txt maupun /favicon.ico akibat fallback SPA di Nginx.
for wajib in robots.txt sitemap.xml favicon.ico; do
    if [[ ! -f "$SUMBER/$wajib" ]]; then
        echo "PERINGATAN: '$wajib' tidak ada di build. Pastikan berkas itu berada" >&2
        echo "            di react/public/ sebelum menjalankan npm run build." >&2
    fi
done

echo "==> Mencadangkan $TUJUAN ke $CADANGAN"
sudo cp -a "$TUJUAN" "$CADANGAN"

echo "==> Menyalin build baru"
sudo rm -rf "${TUJUAN:?}"/*
sudo cp -a "$SUMBER"/. "$TUJUAN"/

echo "==> Menerapkan kepemilikan dan izin"
sudo chown -R libra:www-data "$TUJUAN"
sudo find "$TUJUAN" -type d -exec chmod 750 {} \;
sudo find "$TUJUAN" -type f -exec chmod 640 {} \;
# Bagian yang wajib. Tanpa dua baris ini Nginx tidak bisa membaca index.html.
# Huruf X besar hanya menambahkan bit execute pada direktori, bukan pada berkas.
sudo chmod o+x /var/www/libra
sudo chmod -R o+rX "$TUJUAN"

echo "==> Memeriksa hasil"
gagal=0
for jalur in / /robots.txt /sitemap.xml /katalog; do
    kode=$(curl -s -o /dev/null -w '%{http_code}' -H 'Host: perpuslibra.web.id' \
           "http://127.0.0.1$jalur" || echo 000)
    # 301 wajar pada port 80 karena Nginx mengalihkan ke HTTPS.
    if [[ "$kode" == "200" || "$kode" == "301" ]]; then
        printf '    %-14s %s\n' "$jalur" "$kode"
    else
        printf '    %-14s %s  <== GAGAL\n' "$jalur" "$kode"
        gagal=1
    fi
done

if [[ "$gagal" -ne 0 ]]; then
    echo >&2
    echo "Pemeriksaan gagal. Kembalikan dengan:" >&2
    echo "    sudo rm -rf $TUJUAN && sudo mv $CADANGAN $TUJUAN" >&2
    exit 1
fi

echo "==> Selesai. Cadangan tersimpan di $CADANGAN"
echo "    Hapus bila sudah yakin:  sudo rm -rf $CADANGAN"
