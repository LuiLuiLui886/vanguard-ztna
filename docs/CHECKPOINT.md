# Checkpoint VanGuard — 19 Oktober 2026

## Terbaru: spesifikasi tugas Codex untuk endpoint fisik dan Windows

[Meta prompt utama](../CODEX_VANGUARD_MASTER_PROMPT.md) tersedia di root repository.
Dokumen menggabungkan perbaikan sistem, konfigurasi endpoint fisik dengan layanan
tetap di VM, installer Windows native, kriteria pengujian, dan prompt melanjutkan sesi.
Fokus awal `ENDPOINT_WINDOWS` menjaga pekerjaan ketahanan yang sedang berlangsung.

Ini penambahan spesifikasi, bukan implementasi fitur atau bukti tes endpoint.
Tidak ada perubahan aplikasi/VM/jaringan/CA atau pemeriksaan ulang kondisi live.
Temuan dan hasil operasional di bawah tetap merupakan bukti historis dengan tanggal
masing-masing. Codex harus memeriksa checkout dan progres terbaru sebelum mengerjakan
spesifikasi; jangan mengulang pekerjaan yang sudah selesai atau menimpa perubahan lokal.

Langkah berikutnya: buka repository di Codex dan gunakan bagian **Prompt mulai**
pada dokumen tersebut. Rincian lingkup serta validasi dokumentasi dicatat di
[jurnal 19 Oktober](PROGRESS_2026-10-19.md).

## Terbaru: satu modul lengkap termasuk CA/PKI

Sesuai permintaan pengguna, seluruh panduan CA telah digabung ke bab 5.3
[modul utama](MODUL_PENGGUNAAN_VANGUARD.md), tersedia sebagai
[satu HTML siap baca/cetak](MODUL_PENGGUNAAN_VANGUARD.html).
Ada 13 subbagian CA dengan daftar isi HTML yang dapat diklik. Alamat panduan
lama menjadi penunjuk ke modul; riwayat materi tetap ada dalam Git.

- Validasi PASS: 15 bab, 39 blok Bash, 55 tautan HTML, 15 tabel; seluruh 22 blok
  contoh dari panduan CA lama tetap ada. ID/tujuan fragment HTML valid, scan
  rahasia/permission privat, Ruff renderer dan git diff --check PASS.
- Bukti: state/documentation/2026-10-17/unified-module-validation.json.
  Ini penggabungan dokumentasi; tidak menjalankan contoh pada VM atau mengubah CA.
  Bukti kriptografi terisolasi sebelumnya tetap berlaku sebagai bukti historis.
- Siap commit/push; hasil publikasi dicatat di jurnal. Berikutnya gunakan modul
  tunggal untuk praktik; gap operasional Windows/durability CA tetap terbuka.

## Terbaru: penjelasan generate CA secara rinci

Bab 5.3 modul diperluas dan ditautkan ke [panduan CA/PKI](PANDUAN_CA_PKI.md)
serta [HTML siap cetak](PANDUAN_CA_PKI.html). Panduan 13 bagian menjelaskan
root/key, CSR, signing HTTPS, trust, issuance perangkat, CRL/revoke, backup,
masa berlaku dan troubleshooting dengan lokasi eksekusi/hasil setiap langkah.

- Uji CA sementara di host PASS: parameter root, penolakan init ulang, CSR/TLS,
  IP salah ditolak, profil perangkat/cache retry, CRL satu jam dan pencabutan
  menghasilkan error 23. Bukti privat: state/documentation/2026-10-17/ca-guide-validation.json.
- Struktur modul PASS: 15 bab, 25 blok Bash, 28 tautan, 11 tabel. Panduan CA:
  13 bagian, 21 blok Bash, 15 tautan, 5 tabel. Scan rahasia, Ruff renderer dan
  git diff --check PASS. Tidak ada pemeriksaan visual/PDF baru.
- Tidak mengubah aplikasi, CA produksi, trust, key, akun atau VM. Transfer SSH,
  restart layanan dan backup pada panduan tidak dijalankan di lab pada tugas ini.
- Panduan/modul sudah dipush pada commit 7e54bb5; SHA remote main cocok.
  Hasil publikasi dicatat di jurnal. CI commit dokumentasi belum dinyatakan lulus.
  Gap operasional sebelumnya tetap terbuka; langkah berikutnya sesi pengguna
  mengikuti modul, lalu pengujian Windows/durability CA sesuai daftar di bawah.

## Terbaru: modul penggunaan dan audit bukti

Tugas terbaru pengguna adalah modul lengkap dan akses password Windows.
[Modul Markdown](MODUL_PENGGUNAAN_VANGUARD.md) dan
[HTML siap baca/cetak](MODUL_PENGGUNAAN_VANGUARD.html) memuat15bab untuk teknisi,
admin dan karyawan, dari instalasi hingga penggunaan/arsip/shutdown.

- Pemeriksaan17 Oktober: keenam VM shut off. Tidak ada boot/deployment atau
  pengujian VPN live ulang pada tugas dokumentasi ini.
- Bukti15 Oktober: automatic-renewal.log PASS, dua admission berjarak61,83detik
  dengan cleanup. Ini satu siklus, bukan soak test. lease-expiry-after-renewal.json
  tetap IN_PROGRESS; penghapusan peer setelah expiry belum terbukti.
- CA pernah dipulihkan13457→13458, signature/revocation/index/key terjaga.
  Pemulihan tidak membuktikan masalah durability counter telah diperbaiki.
- CI78ff14e/run38692866340 SUCCESS: Linux3.10/3.12 masing-masing163 PASS+1 SKIP;
  Windows23 PASS. Bukti tersimpan di state/deployment/windows-2026-10-15/.
- Kartu console Windows: /home/lui/VanGuard-Privat/AKSES_WINDOWS_TERBARU.txt,
  dibuat dari inventaris lokal tanpa reset. Login terakhir terverifikasi15 Oktober.
  Folder0700, inventaris/kartu0600; nilai rahasia tidak masuk modul atau Git.
- Modul tervalidasi:15bab,22blok Bash,26tautan HTML,10tabel; scan rahasia/ruff PASS.
  Modul commit d162980 sudah dipush; remote main e9104a4 terverifikasi.
  Pengguna meminta push setelah informasi repository public disampaikan.
  Visibility tetap public; catatan private pada riwayat bukan status saat ini.
- Langkah berikutnya: gunakan modul untuk sesi pengguna, periksa health dan sesi
  akun saat boot; lanjutkan durability CA, lease expiry, revocation Windows dan
  reboot tunnel aktif dengan bukti baru. Jangan ulangi init/enrollment utama.

Catatan15 Oktober di bawah adalah riwayat. Hasil yang lebih baru pada paragraf
di atas menggantikan status renewal yang sebelumnya masih terinterupsi.
Lihat [jurnal17 Oktober](PROGRESS_2026-10-17.md) untuk validasi/push dokumentasi.

## Riwayat checkpoint15 Oktober

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
Baca [jurnal 15 Oktober](PROGRESS_2026-10-15.md) dan
[panduan Windows](WINDOWS_CLIENT.md). Status push/CI dicatat setelah selesai.

## Catatan historis 14 Oktober

**IN PROGRESS: pemulihan instalasi Windows tambahan.** Seluruh lima Ubuntu
utuh dan shut off selama setup. VM keenam running: 4 GiB, 2 vCPU, 80 GiB,
UEFI Secure Boot/TPM2, VNC localhost. Rencana LAN .60/tunnel .4 tetap.

- ISO selesai dan SHA256 cocok hash Microsoft EN-US. Instalasi 13 Oktober
  terputus pada image apply 90%; EFI kosong, C:\Windows belum ada.
- Backup disk sebelum recovery: volume libvirt
  `vanguard-windows-before-recovery-20261014.qcow2`. Jangan hapus bukti/backup.
- Setup diulang pada partisi disk0/3 yang ada, menggunakan seed privat
  `vanguard-windows-recovery-auto-20261014.iso` **tanpa DiskConfiguration**.
  Seed awal yang memformat disk telah dikeluarkan. Jangan memakai ulang seed
  awal, recreate disk/domain, atau mengulang first-install script.
- Setup masih berlangsung; OS/login/SSH/VPN **belum dinyatakan berhasil**.
  Periksa console, lalu laporan guest `C:\ProgramData\VanGuard\windows-setup.json`.
  Setelah bootstrap, keluarkan media seed; kredensial hanya inventaris lokal.
- Source 0.1.7 `3467802` dipush private. CI `38366413893` sukses: Linux3.10/3.12
  masing-masing160 PASS +1 SKIP; Windows20 PASS. Belum bukti tunnel guest nyata.
- Bukti privat `state/deployment/windows-2026-10-14/`, log guest lama disalin ke
  `C:\VG-Recovery-20261014`. [Jurnal](PROGRESS_2026-10-14.md),
  [panduan Windows](WINDOWS_CLIENT.md). Autostart tetap mati.

Tahap 0.1.6 sebelumnya selesai dan dipush (`49dd332`, dokumentasi `aa291f1`), CI
137 PASS Python 3.10/3.12. VM-ADMIN terakhir 0.1.6; empat Ubuntu lain 0.1.5.
Catatan running 12 Oktober di bawah merupakan bukti historis, bukan status hari ini.

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
3.10/3.12. Source awal 0.1.6 `a478111` sudah dipush dan CI lulus. Revisi pencatatan
akses dashboard/filter/arsip dipush sebagai `49dd332`; CI `38232712179` lulus
137/137 pada Python 3.10 dan 3.12, nol failure/error/skip. Artefak terverifikasi
tersimpan lokal pada `state/deployment/ci-49dd332/`. Jangan jalankan eksperimen
.3/benchmark bersamaan. Backup CA sebelum repair ada pada direktori bukti audit.

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
Status 0.1.6 diperbarui 12 Oktober: deployment dashboard VM-ADMIN final telah lulus.
Tes admin setelah perubahan terakhir 26 PASS; verifikasi HTTPS/TOTP final 4/4 PASS.
Wheel final terpasang dengan force-reinstall setelah ditemukan pip mempertahankan
wheel versi sama. Backup kedua menjaga database yang sudah berisi arsip uji.
Arsip final 17 baris, ZIP dan hash isi cocok, tanpa password/seed TOTP. Rincian
dan bukti privat ada pada `docs/PROGRESS_2026-10-12.md`. Source/dokumen final sudah
dipush private; CI Python 3.10/3.12 masing-masing 137 PASS. Empat VM lain tetap
0.1.5 dan tidak perlu di-rollout.

## Console operator — 12 Oktober 2026 16:11 WIB

Lima VM running dan login password console sudah terverifikasi pada `/dev/ttyS0`.
Lima jendela GNOME Terminal terbuka, masing-masing tersambung ke VM-CA, VM-SERVER,
VM-CLIENT, VM-ADMIN dan VM-ATTACKER; sesi shell sengaja dibiarkan untuk pengguna.
Bukti privat `state/deployment/console-login-2026-10-12/`; password tetap hanya di
inventaris lokal. Ctrl+] melepaskan console tanpa shutdown. Tidak ada reboot atau
perubahan konfigurasi aplikasi pada langkah ini.
