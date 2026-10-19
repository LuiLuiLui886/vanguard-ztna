# Lanjutkan proyek VanGuard

**19 Oktober2026 — hardening kandidat teruji; Windows timer diperbaiki.**
Source0.1.9 dan modul sudah dipush ke branch `hardening/2026-10-18-resilience`
(publikasi aplikasi84f4a81, timer Windows42028cf); main tetap c454c0c. CA/lifecycle/logout/readiness/
resource/audit belum di-rollout ke layanan utama. Linux lengkap199 PASS/1 SKIP,
client final29 PASS/1 SKIP, Windows native28 PASS/2 SKIP. Jangan jumlahkan suite
yang overlap; perintah tunnel pada native memakai stub.

VM Windows yang sama sudah memakai clock/timer Hyper-V. Microbenchmark waktu
turun2,63–3,18detik ke0,045–0,051detik per sejuta panggilan; boot penuh hingga
SSH27,49detik pada satu sampel. Secure Boot,TPM,hash identitas dan kelima XML
Ubuntu terjaga. Windows running/viewer tersedia; lima Ubuntu shut off. Paket
utama Windows masih0.1.8;0.1.9 hanya staging. Password tidak diubah.

CI39283176466 untuk42028cf terakhir queued, bukan PASS. Langkah berikutnya periksa hasil CI,
lalu rollout dengan backup dan matriks VPN guest termasuk expiry/revoke/reboot.
Baca [checkpoint](docs/CHECKPOINT.md), [audit](docs/AUDIT_HARDENING_2026-10-18.md),
[rollout](docs/HARDENING_0.1.9.md), [Windows](docs/WINDOWS_CLIENT.md) dan
[jurnal aktif](docs/PROGRESS_2026-10-19.md). Bukti privat:state/hardening/2026-10-19/.

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
