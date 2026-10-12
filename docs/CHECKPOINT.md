# Checkpoint VanGuard — 12 Oktober 2026

**Tahap 0.1.6 sedang difinalkan.** Dashboard terbaru sudah terpasang pada VM-ADMIN;
empat VM lain tetap 0.1.5. Admin 0.1.6 live archive lulus. Perubahan source belum
dipush. Tahap 0.1.5: 132 tes lokal/guest PASS; [jurnal](PROGRESS_2026-10-12.md).

## Keadaan dan bukti

- CA .10, SERVER .20, CLIENT .30, ADMIN .40, ATTACKER .50 pada 192.168.100.0/24.
  Tunnel server 10.8.0.1/client 10.8.0.2; identitas uji sementara .3.
- Rollout/integritas COMPLETE: 14 berkas aplikasi per VM cocok source saat rollout,
  config/CA/key/identitas utama cocok backup. Tidak reenrollment utama.
- Dashboard baru: health, audit admin, alasan/waktu revoke, validity/history,
  bundle publik. [Panduan](DASHBOARD_0.1.5.md).
- VM-ADMIN: 0.1.6 mencatat tindakan dengan waktu WIB, uraian Indonesia, filter
  50/halaman dan arsip CSV/JSON/manifest. [Panduan](DASHBOARD_0.1.6.md).
- 137 tes lokal PASS; HTTPS/TOTP archive workflow live PASS. Bukti dan ZIP 0600:
  `state/deployment/activity-0.1.6/live/`.
- Backup konsisten admin sebelum migrasi:
  `state/backups/before-0.1.6-2026-10-12/`.
- [Pilot benchmark](BENCHMARK_PILOT_2026-10-12.md) selesai n=1; iperf3 3.9 tersedia
  pada client/server, tanpa daemon permanen. Pilot gagal 10 Oktober dipertahankan.
- Bukti aktif: `state/deployment/audit-2026-10-12/`.
  Backup: `state/backups/before-0.1.5-2026-10-12/`.
- Sesi utama terakhir di `resume.json` berakhir **12 Oktober 2026 21:39:08 WIB**;
  tidak diperpanjang oleh renewal atau boot. Periksa expiry aktual sebelum demo.
- Kredensial lokal: `/home/lui/VanGuard-Privat/KREDENSIAL_VANGUARD.md` di luar repo,
  mode 0600; folder 0700. Password console lima VM disiapkan, SSH tetap memakai key.
  Password admin/VPN utama cocok hash aktual. Akun uji lama dicatat tanpa mengarang
  password yang hanya tersimpan sebagai hash.

## Pemulihan dan hasil akhir lab

VM ditemukan mati lagi sesudah interupsi. Sesudah boot, identity gagal akibat
counter CRL kosong dan client tertahan config tunnel sisa. Backup CA dibuat
sebelum pemulihan counter secara monoton; jangan mengembalikan index/CRL lama.
`shutdown-recovery.json` **COMPLETE**: signature CRL valid, nomor 11641 ke 11642,
index/key/root/serial tetap dan seluruh revocation lama dipertahankan. Config
client lama dibackup setelah interface dipastikan mati; tunnel utama pulih.

Identity ulang **COMPLETE/PASS**, termasuk proof/binding/replay, CA-only revoke
dan cleanup. Firewall **40 pemeriksaan PASS**, API tanpa otorisasi dan bypass LAN
ditolak. Health **7/7 PASS selama 82,75 detik**, dua deadline lease, nol removal.
Tidak ada eksperimen aktif. Inventaris privat terbaru memuat satu admin, 22 akun
karyawan (satu aktif) dan lima akun console; nilai rahasia tidak masuk Git.

Source 0.1.5 `8eeffaa` dipush private dan CI-nya masing-masing 132 PASS Python
3.10/3.12. Perubahan 0.1.6 belum dipush; build/checksum sudah lulus dan CI 0.1.6
menunggu commit source. Jangan jalankan eksperimen .3/benchmark bersamaan. Backup
CA sebelum repair ada pada direktori bukti audit.

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
[checkpoint lama](CHECKPOINT_2026-10-10.md). Login HP pribadi,
reboot workstation, serta penyebab shutdown belum terverifikasi.
Tindak lanjut operasional: ketahanan counter CA saat shutdown mendadak dan warning
control socket Gunicorn pada sandbox service; API dan admission sudah lulus uji akhir.
Sisa pekerjaan 0.1.6: finalisasi dokumen/scan rahasia, push private dan validasi CI
137 tes pada Python 3.10/3.12. Deployment admin live telah lulus; tidak perlu rerollout.

## Console operator — 12 Oktober 2026 16:11 WIB

Lima VM running dan login password console sudah terverifikasi pada `/dev/ttyS0`.
Lima jendela GNOME Terminal terbuka, masing-masing tersambung ke VM-CA, VM-SERVER,
VM-CLIENT, VM-ADMIN dan VM-ATTACKER; sesi shell sengaja dibiarkan untuk pengguna.
Bukti privat `state/deployment/console-login-2026-10-12/`; password tetap hanya di
inventaris lokal. Ctrl+] melepaskan console tanpa shutdown. Tidak ada reboot atau
perubahan konfigurasi aplikasi pada langkah ini.
