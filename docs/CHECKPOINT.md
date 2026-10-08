# Checkpoint VanGuard — 8 Oktober 2026

Pembaruan **22:58 WIB**. Versi 0.1.2 terpasang dan teruji; observasi selesai PASS.
Arsip source/wheel/checksum selesai dan terverifikasi. Source serta dokumentasi
sudah dipush ke GitHub **private**, branch `main`; detail di bawah.

## Keadaan terverifikasi

| Bagian | Hasil |
|---|---|
| Lima VM | CA `.10`, SERVER `.20`, CLIENT `.30`, ADMIN `.40`, ATTACKER `.50` aktif |
| Paket | 0.1.2 seluruh VM, hash berkas sesuai source |
| Akses | SSH pinned host key dan sudo guest lulus |
| Layanan | CA, server API, daemon, client, admin, firewall aktif |
| Tunnel | Peer utama `10.8.0.2/32`, handshake kernel dan ping lulus |
| Tes | 54 lokal + 54 Python 3.10 guest; Ruff/pip check/shell lulus |
| Firewall | 40 TCP allow/deny, attacker API dan pencegahan bypass LAN lulus |
| Identity | Registrasi tanpa peer; proof/binding/replay/revocation/cleanup lulus |
| Waktu CRL | 120 probe nyata lulus, 17 penantian batas detik 9–100 ms |
| Stabilitas | 51/51 sampel PASS selama 681,95 detik, nol removal, 12 deadline lease |
| Reboot | Lima role PASS; dua role terakhir dilanjutkan dengan --resume |
| Lease | Bukti 300 detik + recovery lulus pada sesi sebelumnya hari ini |

## Perbaikan dan batasnya

Audit 72/77/84 mengungkap CRL beberapa milidetik di masa depan. Penanganan baru
menunggu sekali <=1 detik sebelum mengulang validasi ketat, tanpa menerima CRL
sebelum berlaku atau sesudah expired. TTL challenge dicek lagi setelah fetch/proof.
Semua peer nyata tetap hanya ditambah sesudah admission enam pemeriksaan.

Audit lama ID 29 tidak cukup rinci untuk diagnosis pasti. Masalah boot/checksum
sore tidak terulang pada sesi malam; keadaan kini sehat tetapi penyebab perubahan
tersebut tidak diketahui. CPU CA memakai konfigurasi asli, tidak ada disk/CA/key
yang diganti. Kernel/source WireGuard tidak diubah.

## Titik lanjut yang konkret

1. Observasi `state/deployment/resume-2026-10-08-2145/stability/health.json` COMPLETE.
2. Publikasi GitHub selesai; lanjutkan kebutuhan TA/demonstrasi melalui
   [panduan demo](DEMO_TA.md). Jangan unggah state atau backup rahasia.
3. TOTP di HP/login pribadi masih menunggu konfirmasi operator. Panduan:
   [AKTIVASI_ADMIN.md](AKTIVASI_ADMIN.md). Reboot workstation belum diuji.

Untuk pemeriksaan ulang tanpa mengganggu client:

```bash
.venv/bin/python scripts/ssh_preflight.py state/lab/inventory.json
.venv/bin/python scripts/health_lab.py state/lab/inventory.json \
  --state state/deployment/health-run-baru
```

Gunakan direktori baru. Jangan jalankan ulang `create_lab.py` atau `verify_lab.py`
(yang memerlukan client idle), dan jangan cabut identitas utama. Autostart VM tetap
nonaktif; `bash scripts/open_dashboard.sh` menyalakan VM yang ada dan membuka
dashboard. Jaringan libvirt autostart.

## Lokasi penyimpanan

- Artefak source/wheel: `dist/`, checksum `dist/SHA256SUMS` (lokal, diabaikan Git).
- Bukti terbaru: `state/deployment/resume-2026-10-08-2145/`.
- Backup sebelum rollout: `state/backups/2026-10-08-2154/`, mode privat.
- Lease/reboot: `state/deployment/operations-{lease,reboot}.json`.
- Kredensial/QR lokal: `state/deployment/`, lihat panduan aktivasi; jangan cetak isinya.
- [Checkpoint September](CHECKPOINT_2026-09-24.md) dan
  [laporan September](IMPLEMENTATION_REPORT_2026-09-24.md) menjadi arsip historis.

Backup mencakup source dan state aplikasi, bukan snapshot disk VM atau backup
di perangkat lain. Jangan memulihkan CA index/CRL lama untuk rollback paket.

## Status penyimpanan Git

Repository **private**: [https://github.com/LuiLuiLui886/vanguard-ztna](https://github.com/LuiLuiLui886/vanguard-ztna), branch `main`, remote `origin`.
Push pertama terverifikasi: `19cf0cb`; HEAD lokal/remote sama dan GitHub
mengembalikan `isPrivate: true`. Catatan akhir dipush sebagai commit berikutnya.
Commit implementasi: `242dffd`; backup Git sebelum publikasi tersedia di
`state/backups/final-source-2026-10-08-225332/`. State, secret, database,
private key dan disk VM tetap lokal. Jangan mengulang enrollment/deployment.
