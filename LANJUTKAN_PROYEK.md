# Lanjutkan proyek VanGuard

**12 Oktober 2026: 0.1.5 terpasang pada lima VM.** Perbaikan sesuai audit proposal
mencakup health dashboard, audit admin, alasan/waktu pencabutan, history/validity
sertifikat dan bundle publik. 132 tes lokal + 132 guest PASS; UI HTTPS live dan
pilot clear/VanGuard n=1 PASS. Finalisasi validasi sesudah resume dan push berlangsung.

Baca AGENTS.md, VANGUARD_CONTEXT.md, [checkpoint](docs/CHECKPOINT.md) dan
[jurnal 12 Oktober](docs/PROGRESS_2026-10-12.md) sebelum melanjutkan.

- [Catatan revisi proposal per bagian](docs/SARAN_REVISI_PROPOSAL_2026-10-12.md)
  memuat konflik arsitektur, contoh redaksi, metrik dan perbaikan daftar pustaka.
- [Tutorial dari awal sampai akhir](docs/TUTORIAL_PENGGUNAAN.md) dan
  [fitur dashboard 0.1.5](docs/DASHBOARD_0.1.5.md).
- [Hasil pilot dan batas kesimpulan](docs/BENCHMARK_PILOT_2026-10-12.md);
  seri formal tiga konfigurasi × 10 belum dijalankan.
- Kredensial hanya di komputer ini:
  `/home/lui/VanGuard-Privat/KREDENSIAL_VANGUARD.md`, di luar repository.
  Admin/VPN utama dan password console lima VM tersedia di sana; jangan unggah.
- Bukti privat: `state/deployment/audit-2026-10-12/`; backup sebelum 0.1.5:
  `state/backups/before-0.1.5-2026-10-12/`.

VM sempat ditemukan mati sesudah interupsi. Pemulihan counter CRL kosong dan
config client tertinggal dicatat pada jurnal serta `shutdown-recovery.json`.
Periksa status COMPLETE sebelum menganggap pemulihan berhasil; jangan mengembalikan
CA index/CRL lama. Sesi VPN delapan jam perlu login ulang saat expired.

Langkah yang sedang diselesaikan: identity ulang, firewall/health akhir, inventaris
kredensial lokal terbaru, commit/push private dan hasil CI aktual. Setelah itu
lanjutkan gap proposal: baseline WG membutuhkan pengecualian admission eksplisit,
renewal sertifikat, notifikasi, Windows, resource policy dan bukti TCP/aplikasi.
Jangan menjalankan eksperimen .3 bersamaan atau recreate topologi lima node.

GitHub: [repository private](https://github.com/LuiLuiLui886/vanguard-ztna),
branch main; CLI `state/tooling/github/cli/usr/bin/gh`.
[Laporan aktif](docs/IMPLEMENTATION_REPORT.md), [arsip resume](docs/LANJUTKAN_PROYEK_2026-10-10.md).
TOTP HP pribadi, console interaktif dan reboot workstation belum terverifikasi.
Seluruh TA belum selesai. Update checkpoint/resume sebelum berhenti.
