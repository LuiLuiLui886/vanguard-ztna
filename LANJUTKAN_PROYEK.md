# Lanjutkan proyek VanGuard

Status **10 Oktober 2026: tahap 0.1.4 selesai**, terpasang pada lima VM.
Sepuluh percobaan S-01 dengan akun karyawan valid dan proof perangkat salah
ditolak tanpa peer VPN. Mean **MTTD aplikasi 69,649 ms**, **MTTR Respond aplikasi
19,383 ms**; definisi tidak mencakup waktu sejak password bocor atau recovery.
[Hasil per sampel](docs/RESPONSE_METRICS_2026-10-10.md).

Baca `AGENTS.md`, `VANGUARD_CONTEXT.md`, [checkpoint](docs/CHECKPOINT.md) dan
[jurnal terbaru](docs/PROGRESS_2026-10-10.md) sebelum perubahan.

Panduan operator tersedia di [tutorial penggunaan lengkap](docs/TUTORIAL_PENGGUNAAN.md):
boot/login/VPN, dashboard, latihan registrasi terpisah, pengujian, shutdown dan
troubleshooting. Penambahan tutorial tidak mengubah aplikasi atau keadaan VM.

## Hasil terakhir

- 100 tes lokal, 100 guest, serta 100 pada masing-masing CI Python 3.10/3.12 PASS.
- Paket/config/CA/key/sertifikat utama cocok source dan backup; tidak enrollment ulang.
- S-01 10/10, kontrol positif, identity/revocation dan cleanup PASS.
- Firewall 40 pemeriksaan dan penolakan bypass LAN PASS.
- Health 7/7 selama 84,18 detik: tiga deadline lease, nol removal; tunnel sehat.
- Tidak ada rollout/eksperimen aktif. S-03 3/3 dan S-04 ICMP 10/10 tetap bukti
  0.1.3; angka revoke SSH/polling bukan MTTD/MTTR dan tidak diulang penuh hari ini.
- Source `c5b94af` dipush ke [GitHub private](https://github.com/LuiLuiLui886/vanguard-ztna);
  [CI 37897878616](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37897878616)
  success. Catatan akhir disimpan pada commit dokumentasi setelahnya.

## Langkah berikutnya

Periksa lima domain lama, jalankan preflight/health dengan direktori baru sesuai
checkpoint. CA .10, SERVER .20, CLIENT .30, ADMIN .40, ATTACKER .50 tetap pada
192.168.100.0/24; tunnel server 10.8.0.1 dan client 10.8.0.2. Jangan recreate lab.

Sesi `employee-lab` untuk `vm-client` berakhir **10 Oktober 2026 08:52:10 WIB**.
Jika expired, login ulang privat lalu restart client sesuai
[panduan akun](docs/EMPLOYEE_ACCESS.md). Bootstrap kredensial ada di
`state/deployment/proposal-2026-10-09/employee-onboarding.json`; jangan cetak/unggah.
Sesi tidak diperpanjang oleh renewal atau boot. TOTP admin terpisah.

Pekerjaan berikutnya: implementasi runner/cleanup dan pilot benchmark clear serta
VanGuard sesuai [rencana tiga konfigurasi × 10](docs/BENCHMARK_PLAN.md).
Benchmark belum dijalankan, iperf3 belum dipasang. Baseline WG tanpa admission
memerlukan pengecualian eksplisit setelah runner siap ditinjau; jangan jalankan
bypass. Gap TCP/aplikasi, Windows, lifecycle/notifikasi/provisioning/resource ada
di [matriks proposal](docs/PROPOSAL_ALIGNMENT.md). Seluruh TA belum selesai.

## Penyimpanan

- Bukti aktif: `state/deployment/metrics-2026-10-10/`; suite asli 9 Oktober pada
  `state/deployment/metrics-2026-10-09/`. Bukti security/proposal lama dipertahankan.
- Backup privat: `state/backups/before-0.1.4-2026-10-10/`, lima role.
- Wheel/source/checksum: `dist/`; Git menyimpan catatan terbaru sesudah arsip dibuat.
- [Laporan aktif](docs/IMPLEMENTATION_REPORT.md), [demo](docs/DEMO_TA.md),
  [aktivasi admin](docs/AKTIVASI_ADMIN.md), [resume lama](docs/LANJUTKAN_PROYEK_2026-10-09.md).
- Branch main, remote origin, CLI `state/tooling/github/cli/usr/bin/gh`.

Catat rencana sebelum setiap kelompok perubahan, hasil validasi serta sisa langkah
sesudahnya; perbarui checkpoint dan file ini sebelum berhenti, lalu commit/push.
State/database/key/disk tetap lokal. Jangan memulihkan index CA/CRL lama atau
downgrade otomatis. TOTP HP/login pribadi dan reboot workstation belum terverifikasi.
Autostart VM nonaktif; penyebab VM mati saat resume belum diketahui.
