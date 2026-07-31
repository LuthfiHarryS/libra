# tarik-backup.ps1 — Unduh cadangan LIBRA dari VPS ke laptop.
#
# Cadangan yang hanya tersimpan di server tidak menolong bila servernya sendiri
# yang hilang. Skrip ini menarik berkas cadangan terbaru ke laptop sehingga ada
# salinan di luar VPS.
#
# Pemakaian:
#   .\deploy\tarik-backup.ps1
#
# Jalankan sepekan sekali, atau sebelum melakukan perubahan besar pada sistem.

$ErrorActionPreference = 'Stop'

$KEY    = "$env:USERPROFILE\.ssh\libra_vps"
$SRV    = '<USER_SSH>@<IP_VPS>'
$TUJUAN = "$env:USERPROFILE\Documents\LIBRA-Backup"

New-Item -ItemType Directory -Force -Path $TUJUAN | Out-Null

Write-Host "Mencari cadangan terbaru di server..." -ForegroundColor Cyan
$db = ssh -i $KEY $SRV "ls -t /var/backups/libra/libra_db-*.sql.gz 2>/dev/null | head -1"
$up = ssh -i $KEY $SRV "ls -t /var/backups/libra/uploads-*.tar.gz 2>/dev/null | head -1"

if (-not $db -or -not $up) {
    Write-Host "Tidak ada cadangan di server. Jalankan dulu: sudo /usr/local/bin/backup-libra" -ForegroundColor Red
    exit 1
}

Write-Host "  database : $db"
Write-Host "  uploads  : $up"
Write-Host "Mengunduh ke $TUJUAN ..." -ForegroundColor Cyan

scp -i $KEY "${SRV}:$db" $TUJUAN
scp -i $KEY "${SRV}:$up" $TUJUAN

Write-Host "`nSelesai. Isi folder cadangan:" -ForegroundColor Green
Get-ChildItem $TUJUAN | Sort-Object LastWriteTime -Descending |
    Select-Object -First 6 Name, @{n='Ukuran';e={'{0:N0} KB' -f ($_.Length/1KB)}}, LastWriteTime |
    Format-Table -AutoSize
