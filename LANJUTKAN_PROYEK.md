# Lanjutkan proyek VanGuard

Status diperbarui **8 Oktober 2026, 22:58 WIB**. Proyek: `/home/lui/vanguard`.
Selalu baca `AGENTS.md`, `VANGUARD_CONTEXT.md`, [checkpoint](docs/CHECKPOINT.md),
dan [jurnal terbaru](docs/PROGRESS_2026-10-08.md) sebelum mengubah sesuatu.

## Keadaan terbaru

- Lima VM Ubuntu 22.04 aktif: CA `.10`, SERVER `.20`, CLIENT `.30`, ADMIN `.40`,
  ATTACKER `.50`, subnet `192.168.100.0/24`. Jangan membuat ulang lab.
- Versi **0.1.2 terpasang di seluruh VM**; hash berkas cocok dengan source.
- Layanan, firewall, NTP, peer `10.8.0.2/32`, handshake dan ping tunnel lulus.
- **54 tes lokal dan 54 tes Python 3.10 guest lulus**, termasuk admission, PKI,
  TOTP/CSRF, lease/revocation, HTTPS dan recovery evidence.
- Firewall 40 pemeriksaan, attacker, admission/replay/revocation identitas sementara,
  dan reboot lima role terverifikasi. Reboot CA/server/client berasal dari sesi
  sebelumnya hari ini; admin/attacker dilengkapi setelah upgrade.
- Observasi stabilitas COMPLETE: 51/51 sampel PASS selama 681,95 detik,
  12 deadline lease berbeda dan nol removal sejak observasi dimulai.
  Bukti: `state/deployment/resume-2026-10-08-2145/stability/health.json`.

## Perubahan penting

Audit baru membuktikan CRL kadang mendahului waktu validator sekitar 7–41 ms karena
perbedaan jam antarnode. Versi 0.1.2 menunggu sekali <=1 detik lalu memvalidasi CRL
kembali dengan waktu aktual. CRL future/stale tetap ditolak dan TTL challenge dicek
ulang sebelum menambah peer. Pada 120 probe nyata, 17 tunggu sekitar 9–100 ms terjadi
dan semua CRL diterima dalam periode sah. Audit lama ID 29 tidak cukup rinci untuk
memastikan penyebab yang sama.

Sesi sore mencatat boot systemd segfault dan mismatch checksum. Saat sesi malam,
guest sudah sehat dan checksum kembali cocok; penyebab perubahan keadaan belum
diketahui. Uji CPU tidak memperbaiki masalah; XML asli telah dipulihkan. Tidak ada
backing image, CA, private key, atau identitas utama yang dibuat ulang.

## Cara melanjutkan

1. Periksa domain: `virsh -c qemu:///system list --all`, lalu jalankan
   `.venv/bin/python scripts/ssh_preflight.py state/lab/inventory.json`.
2. Jalankan pemeriksaan baca-saja dengan direktori hasil baru:
   `.venv/bin/python scripts/health_lab.py state/lab/inventory.json --state state/deployment/health-run-baru`.
3. Jika observasi masih RUNNING setelah prosesnya terputus, periksa sampel terakhir;
   jalankan observasi baru dengan direktori baru. Jangan menyebutnya lulus.
4. Source dan dokumentasi telah dipush ke GitHub private (tautan di bawah).
   Tidak perlu mengulang deployment, enrollment, pencabutan, atau tes lease.
5. Catat rencana sebelum setiap kelompok perubahan dan hasil sesudahnya. Perbarui
   checkpoint sebelum berhenti. Git lokal memakai branch `main` dan melacak
   `origin/main`. CLI lokal: `state/tooling/github/cli/usr/bin/gh`.
   Simpan perubahan berikutnya dengan commit dan push setelah validasi.

## Bukti dan backup

- Artefak source/wheel/checksum: `dist/`; hasil verifikasi pada jurnal.
- Sesi terbaru: `state/deployment/resume-2026-10-08-2145/`.
- Lease nyata 300 detik: `state/deployment/operations-lease.json`.
- Reboot lengkap: `state/deployment/operations-reboot.json`.
- Backup privat sebelum rollout: `state/backups/2026-10-08-2154/`.
- Laporan: [IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md).
- Akses: [LAB_ACCESS.md](docs/LAB_ACCESS.md), [AKTIVASI_ADMIN.md](docs/AKTIVASI_ADMIN.md).

Backup state berisi rahasia: jangan unggah ke laporan/arsip source. Jangan rollback
index CA/CRL yang bisa menghidupkan sertifikat dicabut. Penyimpanan ini bukan snapshot
disk VM. Autostart guest pada boot host tetap nonaktif; jaringan libvirt autostart.

Langkah operator yang belum terkonfirmasi: TOTP di HP dan login dashboard. Reboot
workstation belum diuji dalam sesi ini. Gunakan [panduan demo](docs/DEMO_TA.md).

## Status penyimpanan Git

Repository **private**: [https://github.com/LuiLuiLui886/vanguard-ztna](https://github.com/LuiLuiLui886/vanguard-ztna), branch `main`, remote `origin`.
Push pertama terverifikasi: `19cf0cb`; HEAD lokal/remote sama dan GitHub
mengembalikan `isPrivate: true`. Catatan akhir dipush sebagai commit berikutnya.
Commit implementasi: `242dffd`; backup Git sebelum publikasi tersedia di
`state/backups/final-source-2026-10-08-225332/`. State, secret, database,
private key dan disk VM tetap lokal. Jangan mengulang enrollment/deployment.

## Progres CI (8 Oktober, 23:11 WIB)

Workflow dua versi Python dan build arsip sudah divalidasi lokal; run GitHub
akan diperiksa setelah push. Status saat ini BELUM TERVERIFIKASI di runner.
Panduan: [docs/CI.md](docs/CI.md). Bukti lokal: `state/deployment/ci-2026-10-08/`.
