# Lanjutkan proyek VanGuard

**22 Oktober 2026 — tambahan pekerjaan pilot dua endpoint Windows 11.**
[Master prompt](CODEX_VANGUARD_MASTER_PROMPT.md) sudah memuat topologi dan IP
yang disetujui: router 192.168.50.1, Linux host .10, PC LAN .20, laptop Wi-Fi .30,
seluruhnya /24. Jaringan VM 192.168.100.0/24 dan tunnel 10.8.0.0/24 tetap terpisah.
Baca Bagian B0/B0.1 dan D1 untuk routing/firewall/TLS, paket manual, enrollment
terpisah, uji satu lalu dua endpoint bersamaan, serta pemulihan/cleanup.

Ini pembaruan spesifikasi; IP, router, VM, dan endpoint belum diubah pada tugas ini.
Source terbaru yang diamati ada di `fix/2026-10-20-readiness-lock` (`040dc21`) (0.1.11),
bukan main 0.1.8. Ambil instruksi terbaru sambil mempertahankan source serta progres
branch kerja; jangan menimpa perubahan lokal atau mengulang perbaikan ketahanan.
Ikuti [checkpoint](docs/CHECKPOINT.md) dan [jurnal](docs/PROGRESS_2026-10-22.md).

**19 Oktober 2026 — meta prompt Codex tersedia.**
Baca [CODEX_VANGUARD_MASTER_PROMPT.md](CODEX_VANGUARD_MASTER_PROMPT.md) di root.
Gunakan **Prompt mulai** dengan fokus `ENDPOINT_WINDOWS` untuk persiapan endpoint
fisik dan installer BAT/PowerShell; tersedia pula fokus perbaikan sistem serta
prompt melanjutkan sesi. Audit progres ketahanan dan perubahan lokal sebelum edit.

Tugas publikasi ini hanya menambahkan spesifikasi dan catatan proyek. Fitur yang
diminta dalam prompt belum diimplementasikan atau diuji melalui tugas ini; VM,
jaringan, CA, dan kredensial tidak diubah. Langkah berikutnya menjalankan spesifikasi
melalui Codex sesuai batas persiapan lokal. Lihat [checkpoint](docs/CHECKPOINT.md)
dan [jurnal 19 Oktober](docs/PROGRESS_2026-10-19.md).

**17 Oktober 2026 — seluruh materi sudah menjadi satu modul.**
Gunakan [modul utama](docs/MODUL_PENGGUNAAN_VANGUARD.md) atau
[satu HTML siap baca/cetak](docs/MODUL_PENGGUNAAN_VANGUARD.html).
Materi CA/PKI lengkap sekarang berada di bab 5.3 (13 subbagian), dilanjutkan
instalasi, administrasi dan pemakaian Ubuntu/Windows dalam dokumen yang sama.
Alamat panduan CA lama hanya menunjuk ke modul agar tautan historis tetap hidup.
Validasi kelengkapan, Bash, tautan/fragment, rahasia dan renderer PASS; bukti di
state/documentation/2026-10-17/unified-module-validation.json. Tidak ada perubahan
VM atau CA. Siap commit/push; hasil publikasi dicatat di jurnal.
Langkah berikutnya praktik memakai modul dan lanjutkan gap operasional checkpoint.

**17 Oktober 2026 — rincian CA/PKI selesai disusun dan divalidasi.**
Bab 5.3 modul sekarang menjelaskan generate CA dan tahapan terkait. Baca
[panduan CA/PKI lengkap](docs/PANDUAN_CA_PKI.md) atau
[HTML siap cetak](docs/PANDUAN_CA_PKI.html), mencakup 13 bagian dari konsep
hingga backup dan troubleshooting. Uji CA sementara di host PASS, termasuk
signing TLS/perangkat dan penolakan sertifikat setelah revoke. Struktur kedua
dokumen, sintaks contoh Bash, tautan dan scan rahasia PASS. Bukti di
state/documentation/2026-10-17/. Tidak mengubah CA/VM produksi.
Panduan/modul sudah dipush pada commit 7e54bb5; remote main terverifikasi cocok.
CI commit dokumentasi belum dinyatakan lulus; lihat jurnal untuk hasil publikasi.
Pekerjaan operasional berikutnya tetap mengikuti checkpoint di bawah.

**17 Oktober2026 — modul penggunaan lengkap.** Tugas terbaru: audit checkpoint,
modul teknisi/admin/karyawan, dan akses password console Windows. Baca
[modul lengkap](docs/MODUL_PENGGUNAAN_VANGUARD.md) atau
[HTML siap cetak](docs/MODUL_PENGGUNAAN_VANGUARD.html).

Keenam VM ditemukan shut off; tugas ini tidak menjalankan deployment atau tes
live ulang. Bukti15 Oktober menunjukkan satu renewal otomatis Windows PASS
(61,83detik), cleanup PASS dan CI78ff14e SUCCESS. Bukti lease expiry terakhir
tetap IN_PROGRESS. Counter CA pernah dipulihkan, durability belum diperbaiki.

Password Windows tersedia pada kartu lokal
`/home/lui/VanGuard-Privat/AKSES_WINDOWS_TERBARU.txt`; akun/password tidak diubah.
Kredensial tetap di luar Git. Kartu/inventaris0600 dan folder0700.
Modul/HTML tervalidasi sudah dipush ke main: commit modul d162980 tercakup pada
remote e9104a4 yang telah dicocokkan. Pengguna meminta push setelah informasi
visibility public disampaikan; visibility tidak diubah. Referensi repository
private di catatan historis tidak menggambarkan status sekarang.
Berikutnya jalankan sesi pengguna mengikuti modul serta periksa health saat boot.
Lihat [checkpoint](docs/CHECKPOINT.md) dan [jurnal17 Oktober](docs/PROGRESS_2026-10-17.md).

## Riwayat handoff15 Oktober

**Status operasional terbaru 15 Oktober 13:38 WIB:** host sempat reboot;
enam VM ditemukan mati. CA, SERVER dan Windows sedang dinyalakan bertahap.
Hasil integrasi di bawah adalah bukti sebelum reboot. Uji lease-expiry/renewal
otomatis terinterupsi, belum dinyatakan lulus. CI78ff14e sudah SUCCESS.

**15 Oktober 2026 — client Windows tambahan berhasil diuji langsung.**

- Enam domain tetap ada; lima definisi Ubuntu sama dengan backup awal.
- Windows 11 Enterprise Evaluation build 26300, Secure Boot/TPM aktif,
  LAN `192.168.100.60`, tunnel `10.8.0.4`. Login console dan SSH key-only PASS;
  SSH hanya dari host `.1`. Kedua CD sudah dikeluarkan; seed/backup privat tetap.
- Windows memakai client **0.1.8**, Python 3.13.16 dan WireGuard 1.1.1.
  23 tes native Windows PASS. Cleanup menunggu service benar-benar terhapus;
  timeout/error mempertahankan config untuk inspeksi. Ubuntu tidak di-upgrade.
- Akun karyawan Windows terpisah, enrollment lewat admin HTTPS/TOTP dan root CA
  bundle terverifikasi. Registrasi/login tidak menambah peer. Sesi invalid serta
  proof invalid ditolak. Admission sah, handshake, ping dan admission ulang PASS.
- Dua client Ubuntu `.2` dan Windows `.4` aktif bersamaan: dua handshake/ping PASS.
  Cleanup Windows PASS; Ubuntu tetap bisa ping. Ini bukti integrasi awal, bukan
  seluruh skenario keamanan atau benchmark formal Windows.
- OpenSSH bawaan terinterupsi; fallback resmi Microsoft Win32-OpenSSH MSI
  `10.0.0.0p2-Preview` berhasil, hash/tanda tangan terverifikasi. Paket GitHub ini
  perlu pemeliharaan manual; rincian pada panduan Windows.
- Windows, CA, SERVER, ADMIN dan CLIENT running saat pemeriksaan; ATTACKER mati.
  Tunnel Windows sudah ditutup setelah tes; jalankan `connect` untuk pemakaian.
  Autologon dinonaktifkan. Password/username hanya inventaris privat host.
- Bukti privat: `state/deployment/windows-2026-10-15/`; backup pra-enrollment:
  `state/backups/before-windows-enrollment-20261015/`. Jangan rollback CA index/CRL.

Berikutnya: uji pencabutan menggunakan identitas disposable, renewal otomatis
jangka panjang dan reboot Windows, lalu gap proposal/benchmark yang masih terbuka.
Baca [jurnal 15 Oktober](docs/PROGRESS_2026-10-15.md) dan
[panduan Windows](docs/WINDOWS_CLIENT.md). Status push/CI dicatat setelah selesai.

## Catatan historis

**14 Oktober 2026 — IN PROGRESS: pemulihan instalasi client Windows tambahan.**
Lima Ubuntu tetap utuh dan shut off selama instalasi (RAM host terbatas).
ISO resmi selesai, SHA256 cocok hash penerbit. Instalasi kemarin terputus saat
image apply 90%; disk tidak bootable, bukan OS siap pakai. Backup disk sudah dibuat
sebelum recovery. Setup berjalan kembali memakai partisi yang ada, dengan seed
pemulihan tanpa wipe/format. Jangan jalankan ulang script first-install atau seed awal.

VM-CLIENT-WINDOWS: 4 GiB, 2 vCPU, 80 GiB, UEFI Secure Boot/TPM, VNC localhost.
LAN .60/tunnel .4 masih rencana sampai dibuktikan guest. Source 0.1.7 `3467802`
sudah di GitHub private, CI Linux masing-masing 160 PASS + 1 SKIP dan Windows
20 PASS; VPN guest/enrollment/firewall live belum dilakukan. Baca
[jurnal 14 Oktober](docs/PROGRESS_2026-10-14.md),
[checkpoint](docs/CHECKPOINT.md) dan [panduan Windows](docs/WINDOWS_CLIENT.md).
Bukti privat: `state/deployment/windows-2026-10-14/`.

**12 Oktober 2026: 0.1.6 live, push, dan CI selesai.** Dashboard terbaru
terpasang pada VM-ADMIN; empat VM lain tetap 0.1.5. Tes admin terakhir 26 PASS;
verifikasi HTTPS/TOTP final 4/4 PASS dan arsip 17 aktivitas terverifikasi.
CI final: 137/137 PASS pada Python 3.10 dan 3.12, tanpa error/failure/skip.
Perbaikan sesuai audit proposal
mencakup health dashboard, audit admin, alasan/waktu pencabutan, history/validity
sertifikat dan bundle publik. 132 tes lokal + 132 guest PASS; UI HTTPS live dan
pilot clear/VanGuard n=1 PASS. Identity, firewall dan health akhir PASS.
Source 0.1.5 `8eeffaa` sudah dipush private; CI sebelumnya masing-masing 132 tes
Python 3.10/3.12 lulus. Source awal 0.1.6 `a478111` dan revisi final `49dd332`
sudah dipush private; CI final lulus pada kedua versi Python.

Baca AGENTS.md, VANGUARD_CONTEXT.md, [checkpoint](docs/CHECKPOINT.md) dan
[jurnal 12 Oktober](docs/PROGRESS_2026-10-12.md) sebelum melanjutkan.

- [Catatan revisi proposal per bagian](docs/SARAN_REVISI_PROPOSAL_2026-10-12.md)
  memuat konflik arsitektur, contoh redaksi, metrik dan perbaikan daftar pustaka.
- [Tutorial dari awal sampai akhir](docs/TUTORIAL_PENGGUNAAN.md),
  [aktivitas dan arsip 0.1.6](docs/DASHBOARD_0.1.6.md), serta
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
Pemulihan COMPLETE; data revocation lama dipertahankan. Jangan mengembalikan
CA index/CRL lama. Sesi VPN utama berakhir **12 Oktober 2026 21:39:08 WIB**;
perlu login ulang saat expired.

Identity ulang/cleanup PASS, firewall 40 pemeriksaan PASS, health 7/7 selama
82,75 detik dengan nol removal. Inventaris kredensial lokal sudah diperbarui.
Tahap dashboard 0.1.6 selesai dan terdokumentasi. Berikutnya lanjutkan gap proposal
serta isu operasional yang masih tercatat pada checkpoint.
Setelah itu lanjutkan gap proposal: baseline WG membutuhkan pengecualian admission eksplisit,
renewal sertifikat, notifikasi, Windows, resource policy dan bukti TCP/aplikasi.
Jangan menjalankan eksperimen .3 bersamaan atau recreate topologi lima node.

GitHub: [repository private](https://github.com/LuiLuiLui886/vanguard-ztna),
branch main; CLI `state/tooling/github/cli/usr/bin/gh`.
[Laporan aktif](docs/IMPLEMENTATION_REPORT.md), [arsip resume](docs/LANJUTKAN_PROYEK_2026-10-10.md).
TOTP HP pribadi dan reboot workstation belum terverifikasi.
Seluruh TA belum selesai. Update checkpoint/resume sebelum berhenti.
Tindak lanjut operasional: ketahanan counter CA terhadap shutdown mendadak dan
warning control socket Gunicorn; lihat checkpoint untuk bukti pemulihan.

12 Oktober 2026 16:11 WIB: kelima VM running; login password console pada ttyS0
terverifikasi dan lima jendela terminal sudah dibuka untuk pengguna. Password tidak
diubah. Sesi console sengaja dibiarkan aktif; Ctrl+] melepaskan console tanpa
mematikan VM. Bukti ada pada `state/deployment/console-login-2026-10-12/`.

Dashboard 0.1.6 menyimpan snapshot arsip admin pada VM-ADMIN dan salinan final lokal
privat `state/deployment/activity-0.1.6/final-check/admin-activity.zip` mode 0600.
Backup pra-upgrade dan backup final tersedia pada `state/backups/`.
