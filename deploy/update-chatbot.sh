#!/usr/bin/env bash
#
# update-chatbot.sh — Pasang kode layanan chatbot baru ke /var/www/libra/python/chatbot.
#
# Dijalankan DI SERVER, setelah folder chatbot disalin ke direktori sementara:
#
#     scp -r python/chatbot <USER_SSH>@<ip>:/tmp/chatbot_baru
#     scp deploy/update-chatbot.sh <USER_SSH>@<ip>:/tmp/
#     ssh <USER_SSH>@<ip> "bash /tmp/update-chatbot.sh /tmp/chatbot_baru"
#
# Yang dijaga skrip ini:
#   - model .joblib yang sudah terlatih TIDAK ikut tertimpa; melatih ulang di
#     server memakan memori dan tidak perlu selama dataset tidak berubah
#   - pemilik dan izin berkas dikembalikan ke libra:libra, karena salah izin
#     pernah mematikan layanan (lihat catatan pada update-react.sh)
#   - layanan diuji lewat /health dan satu permintaan /chat sungguhan sebelum
#     skrip dinyatakan berhasil; kalau gagal, versi lama dikembalikan
set -euo pipefail

SUMBER="${1:-}"
TUJUAN=/var/www/libra/python/chatbot
CADANGAN="/var/www/libra/python/chatbot.bak-$(date +%Y%m%d-%H%M%S)"

if [[ -z "$SUMBER" ]]; then
    echo "Pemakaian: bash update-chatbot.sh <direktori-chatbot>" >&2
    exit 1
fi
if [[ ! -f "$SUMBER/app.py" || ! -f "$SUMBER/katalog.py" ]]; then
    echo "GAGAL: '$SUMBER' tidak berisi app.py dan katalog.py." >&2
    exit 1
fi

echo "== mencadangkan versi lama ke $CADANGAN"
sudo cp -a "$TUJUAN" "$CADANGAN"

echo "== menyalin berkas Python (model .joblib dipertahankan)"
# Hanya berkas .py yang diperbarui. Folder models/ sengaja tidak disentuh
# supaya model hasil pelatihan tetap utuh.
sudo find "$SUMBER" -maxdepth 1 -name '*.py' -exec cp {} "$TUJUAN"/ \;
if [[ -d "$SUMBER/tests" ]]; then
    sudo rm -rf "$TUJUAN/tests"
    sudo cp -a "$SUMBER/tests" "$TUJUAN/tests"
fi
sudo rm -rf "$TUJUAN/__pycache__" "$TUJUAN/tests/__pycache__" 2>/dev/null || true

echo "== mengembalikan pemilik dan izin"
sudo chown -R libra:libra "$TUJUAN"
sudo find "$TUJUAN" -type d -exec chmod 750 {} \;
sudo find "$TUJUAN" -type f -exec chmod 640 {} \;

echo "== memuat ulang layanan"
sudo systemctl restart libra-chatbot
sleep 4

echo "== memeriksa kesehatan layanan"
gagal=0
if ! curl -sf --max-time 10 localhost:5001/health >/dev/null; then
    echo "GAGAL: /health tidak menjawab" >&2
    gagal=1
else
    jawab=$(curl -s --max-time 15 -X POST localhost:5001/chat \
        -H 'Content-Type: application/json' \
        -d '{"message":"The Peach Boy kategorinya apa"}' || true)
    echo "   uji /chat: ${jawab:0:160}"
    # Perbaikan ini dianggap berhasil bila jawabannya menyebut judul bukunya,
    # bukan mengembalikan templat jam buka.
    if ! grep -q 'Peach' <<<"$jawab"; then
        echo "GAGAL: jawaban tidak menyebut judul yang ditanyakan" >&2
        gagal=1
    fi
fi

if [[ $gagal -eq 1 ]]; then
    echo "== MENGEMBALIKAN versi lama"
    sudo rm -rf "$TUJUAN"
    sudo mv "$CADANGAN" "$TUJUAN"
    sudo systemctl restart libra-chatbot
    echo "Versi lama sudah dipulihkan. Layanan tidak jadi diperbarui." >&2
    exit 1
fi

echo "== selesai. Cadangan versi lama ada di $CADANGAN"
sudo systemctl status libra-chatbot --no-pager | head -5
