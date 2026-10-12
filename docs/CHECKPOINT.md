# Checkpoint VanGuard — 12 Oktober 2026

**0.1.5 terpasang pada lima VM; finalisasi validasi/push berlangsung.**
132 tes lokal dan 132 guest PASS. Dashboard HTTPS live dan pilot clear/VanGuard
n=1 per kondisi PASS. Jangan menyamakan status ini dengan seri benchmark lengkap
atau seluruh proposal selesai. [Jurnal](PROGRESS_2026-10-12.md).

## Keadaan dan bukti

- CA .10, SERVER .20, CLIENT .30, ADMIN .40, ATTACKER .50 pada 192.168.100.0/24.
  Tunnel server 10.8.0.1/client 10.8.0.2; identitas uji sementara .3.
- Rollout/integritas COMPLETE: 14 berkas aplikasi per VM cocok source saat rollout,
  config/CA/key/identitas utama cocok backup. Tidak reenrollment utama.
- Dashboard baru: health, audit admin, alasan/waktu revoke, validity/history,
  bundle publik. [Panduan](DASHBOARD_0.1.5.md).
- [Pilot benchmark](BENCHMARK_PILOT_2026-10-12.md) selesai n=1; iperf3 3.9 tersedia
  pada client/server, tanpa daemon permanen. Pilot gagal 10 Oktober dipertahankan.
- Bukti aktif: `state/deployment/audit-2026-10-12/`.
  Backup: `state/backups/before-0.1.5-2026-10-12/`.
- Sesi utama terakhir di `resume.json`; berlaku delapan jam sejak login,
  tidak diperpanjang oleh renewal atau boot. Periksa expiry aktual sebelum demo.
- Kredensial lokal: `/home/lui/VanGuard-Privat/KREDENSIAL_VANGUARD.md` di luar repo,
  mode 0600; folder 0700. Password console lima VM disiapkan, SSH tetap memakai key.
  Password admin/VPN utama cocok hash aktual. Akun uji lama dicatat tanpa mengarang
  password yang hanya tersimpan sebagai hash.

## Pemulihan dan pekerjaan yang sedang berlangsung

VM ditemukan mati lagi sesudah interupsi. Sesudah boot, identity gagal akibat
counter CRL kosong dan client tertahan config tunnel sisa. Backup CA dibuat
sebelum pemulihan counter secara monoton; jangan mengembalikan index/CRL lama.
Lihat `shutdown-recovery.json` dan laporan identity gagal sebelum melanjutkan.
Hasil yang RUNNING/FAIL belum boleh dianggap sukses.

Berikutnya: selesaikan recovery, identity ulang, firewall dan health, refresh
inventaris akun lokal, verifikasi tidak ada secret masuk index, commit/push
source dan pantau CI, lalu simpan hasil aktual pada handoff ini.
Tidak menjalankan eksperimen .3 atau benchmark bersamaan.

## Sesi berikutnya

1. Baca AGENTS.md, VANGUARD_CONTEXT.md, checkpoint dan jurnal terbaru.
2. Periksa lima domain lama; jangan recreate lab/CA. Autostart VM masih nonaktif.
3. Preflight lalu health dengan direktori bukti baru. Login ulang karyawan secara
   privat jika expired, sesuai [panduan](EMPLOYEE_ACCESS.md).
4. Lanjutkan gap [matriks proposal](PROPOSAL_ALIGNMENT.md) dan
   [saran revisi](SARAN_REVISI_PROPOSAL_2026-10-12.md). Baseline WG tanpa admission
   belum diotorisasi; [rencana isolasi/cleanup](BENCHMARK_PLAN.md) sudah tersedia.
5. Catat intent sebelum perubahan dan hasil sesudahnya. Credential/state/key/disk
   tetap lokal. GitHub private; CLI `state/tooling/github/cli/usr/bin/gh`.

S-01 kuantitatif tetap bukti 0.1.4; S-03/S-04 ICMP tetap bukti 0.1.3, tidak diulang
penuh. [Laporan aktif](IMPLEMENTATION_REPORT.md), [tutorial](TUTORIAL_PENGGUNAAN.md),
[checkpoint lama](CHECKPOINT_2026-10-10.md). Login HP pribadi dan console interaktif,
reboot workstation, serta penyebab shutdown belum terverifikasi.
