#!/bin/bash
# backup-libra.sh — Cadangkan database dan berkas unggahan LIBRA.
#
# Dua hal yang tidak dapat dibuat ulang bila VPS hilang:
#   1. basis data libra_db  — 261 buku, sinopsis, akun, riwayat peminjaman
#   2. uploads/             — 90 sampul hasil foto rak yang tidak ada sumbernya
#                             di internet, ditambah 50 sampul Google Books dan
#                             146 sampul placeholder hasil render
#
# Dijalankan sebagai root lewat cron. mysqldump memakai autentikasi unix_socket
# sehingga tidak perlu menyimpan kata sandi di dalam berkas ini.
#
# Pemasangan:
#   sudo install -m 750 -o root -g root backup-libra.sh /usr/local/bin/backup-libra
#   sudo crontab -e
#     15 2 * * * /usr/local/bin/backup-libra >> /var/log/libra-backup.log 2>&1
#
# PENTING: salinan di server ini hanya melindungi dari kesalahan operasional
# (tabel terhapus, berkas tertimpa). Ia TIDAK melindungi dari kehilangan VPS.
# Unduh berkas hasil cadangan ke luar server secara berkala — lihat DEPLOY.md.

set -euo pipefail

TUJUAN=/var/backups/libra
SUMBER_UPLOAD=/var/www/libra/uploads
BASIS_DATA=libra_db
SIMPAN_HARI=14

tanggal=$(date +%Y%m%d-%H%M)
mkdir -p "$TUJUAN"

echo "[$(date '+%F %T')] mulai pencadangan"

# ── Basis data ───────────────────────────────────────────────────────────
db_file="$TUJUAN/libra_db-$tanggal.sql.gz"
# --single-transaction: konsisten tanpa mengunci tabel, aman untuk InnoDB
# --default-character-set=utf8mb4: jangan sampai judul berbahasa Indonesia rusak
mysqldump --single-transaction --default-character-set=utf8mb4 \
          --routines --triggers "$BASIS_DATA" | gzip -9 > "$db_file"

# Dump yang gagal di tengah tetap menghasilkan berkas; periksa isinya.
if ! gzip -t "$db_file" 2>/dev/null; then
    echo "GAGAL: berkas dump rusak, dihapus"
    rm -f "$db_file"
    exit 1
fi
jumlah_buku=$(zcat "$db_file" | grep -c "INSERT INTO \`buku\`" || true)
if [ "$jumlah_buku" -eq 0 ]; then
    echo "GAGAL: dump tidak memuat data tabel buku, dihapus"
    rm -f "$db_file"
    exit 1
fi
echo "  database : $(du -h "$db_file" | cut -f1)"

# ── Berkas unggahan ──────────────────────────────────────────────────────
up_file="$TUJUAN/uploads-$tanggal.tar.gz"
tar -czf "$up_file" -C "$(dirname "$SUMBER_UPLOAD")" "$(basename "$SUMBER_UPLOAD")"
jumlah_webp=$(tar -tzf "$up_file" | grep -c '\.webp$' || true)
if [ "$jumlah_webp" -lt 200 ]; then
    echo "PERINGATAN: hanya $jumlah_webp sampul .webp dalam arsip (biasanya 261)"
fi
echo "  uploads  : $(du -h "$up_file" | cut -f1)  ($jumlah_webp sampul)"

# ── Buang cadangan lama ──────────────────────────────────────────────────
hapus=$(find "$TUJUAN" -type f -name '*.gz' -mtime +$SIMPAN_HARI -print -delete | wc -l)
echo "  dihapus  : $hapus berkas lebih tua dari $SIMPAN_HARI hari"

echo "[$(date '+%F %T')] selesai — total $(du -sh "$TUJUAN" | cut -f1) di $TUJUAN"
