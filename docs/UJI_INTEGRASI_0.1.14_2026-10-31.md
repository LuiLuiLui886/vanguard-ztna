# Uji integrasi layanan VanGuard 0.1.14 — 31 Oktober 2026

**Hasil: alur akses yang diuji berhasil; satu readiness 503 sementara tetap menjadi
temuan. Belum merupakan penerimaan produksi atau pengujian ulang Windows/EXE.**

## Versi dan lingkungan

- Source `40ebf81`, branch `feature/2026-10-22-physical-endpoints`, versi paket
  `0.1.14`. Fetch origin pada sesi ini mengonfirmasi HEAD tersebut.
- CA, server, admin: paket **0.1.14 terpasang**, HTTPS dengan validasi Root CA.
- VM-CLIENT Ubuntu: source 0.1.14 di direktori uji terpisah; 19 modul Python
  cocok hash source. Instalasi utama client **tetap 0.1.9**.
- IP tunnel uji `10.8.0.3`; identitas dan akun disposable baru. Private key
  dibuat di client. Sertifikat, akun dan konfigurasi utama tidak diganti.
- Backup state/config ketiga layanan dibuat saat layanan dihentikan terurut;
  seluruh isi arsip dapat dibaca. Backup disimpan privat, tidak dipulihkan ke CA.
- Windows 10/11 dan attacker tidak dinyalakan pada sesi ini. Lima VM Ubuntu
  serta dua VM Windows tetap dipertahankan.

## Hasil VM langsung

| Skenario | Bukti aktual |
|---|---|
| Registrasi dari workflow admin ke CA/server | Sertifikat terbit; tidak ada peer setelah registrasi |
| Bundle publik | Manifest sesuai identitas; tidak mengandung private key; tidak menambah peer |
| Login karyawan | HTTPS berhasil; login saja tidak menambah peer |
| Admission negatif | Tanpa sertifikat, sesi invalid, binding WG salah dan proof salah ditolak HTTP400/403; tetap tidak ada peer |
| Admission valid | Peer terpasang dan handshake WireGuard aktual teramati |
| Aplikasi tanpa grant | HTTP tunnel TCP8082 ditolak |
| Grant eksplisit | Identitas/akun, resource internal-demo, alamat10.8.0.1, protokolTCP, port8082 mengizinkan HTTP |
| Pembatasan alamat/port | Akses langsung LAN192.168.100.20:8082 dan tunnel port8083 ditolak |
| Pencabutan grant | Socket TCP yang sudah berhasil berkomunikasi tidak dapat melanjutkan komunikasi |
| Renewal otomatis | Dua renewal melalui HTTPS, interval67,33 dan63,38detik; lease300detik |
| Logout sesi lama | Lease sesi baru pada identitas yang sama tetap memiliki peer |
| Logout sesi aktif | Peer dihapus; pengulangan logout berhasil idempotent; token lokal dibuang setelah konfirmasi |
| Revoke langsung di CA | Peer dihapus dalam8,238detik, TCP aktif berhenti, admission berikutnya403 |
| Cleanup | Identitas revoked, akun disabled, tidak ada peer/tunnel client/listener demo |

Waktu8,238detik adalah **satu pengamatan** yang mencakup pemanggilan API,
polling dan SSH. Bukan SLA, distribusi latency atau pengukuran MTTD proposal.
Penolakan HTTP membuktikan lalu lintas aplikasi terhenti; tidak mengklaim selalu
menghasilkan TCP RST dibanding timeout. Renewal lease tidak memperpanjang sertifikat.

Registrasi memakai objek dashboard terpasang yang menghubungi API nyata, bukan
klik form browser. Pengujian admin terpisah memakai HTTPS dan cookie/CSRF nyata:
login password+TOTP, label Registry/Lease/Peer/Handshake/Transfer, halaman riwayat
masa berlaku, operations/storage, waktu WIB, pembuatan serta unduh arsip audit.
SHA-256 unduhan dan setiap anggota ZIP sesuai manifest; password/TOTP pengujian
tidak ditemukan pada isi arsip yang diekspansi. Ini bukan audit semua kemungkinan
rahasia atau uji visual browser.

## Regresi terisolasi Linux

**89 lulus, 1 dilewati, 267,83detik; 90 kasus dikumpulkan.**

```bash
.venv/bin/python -m pytest -q \
  tests/test_ca_durability.py tests/test_ca_publication_io.py \
  tests/test_logout.py tests/test_health_status.py \
  tests/test_resource_policy.py tests/test_client_platform.py \
  tests/test_managed_internet.py
```

CA sementara menggunakan OpenSSL nyata dan interupsi SIGKILL pada penerbitan,
pencabutan serta publikasi CRL. Regresi juga meliputi counter rusak, kegagalan
fsync, logout bersamaan renewal, status tidak diketahui, cleanup gagal dan
fail-closed policy. Sebagian adapter/kernel/subprocess memakai mock. Kasus
Windows dalam suite Linux **bukan Windows native**; ACL native Windows dilewati.
Ini subset baru, bukan pengulangan seluruh baseline307PASS/1SKIP30Oktober.

## Kesehatan dan pelestarian data

| Pemeriksaan | Hasil |
|---|---|
| Sampel awal healthz/readyz ketiga layanan | **29/30HTTP200**; server/readyz503 satu kali,0,614detik |
| Detail respons503 | CA `unknown`; daemon, database dan interface `ready` |
| Diagnostik server→CA readiness | 20/20HTTP200 |
| Sampel lanjutan healthz/readyz | 30/30HTTP200 |
| CA invariant dan validasi CRL | Lulus;35baris index lama tetap;75berkas root/key/config/sertifikat lama sama |
| SQLite dan histori | Integrity OK;1120baris7tabel server serta157baris6tabel admin tetap |
| Konfigurasi/identitas | 8berkas config server,6admin dan seluruh berkas identitas client utama sama |

Penyebab dependency CA menjadi `unknown` **BELUM_TERKONFIRMASI**. Journal CA/server
pada jendela diagnostik tidak memuat entry; CA aktif tanpa restart. Hasil lanjutan
tidak menghapus503 awal dan tidak membuktikan masalah sudah diperbaiki.

Pembandingan histori mengecualikan state operasional lease/session/rate-limit
serta kolom `users.last_step` admin: counter anti-replay TOTP memang maju setelah
login sah. Kemajuan counter diverifikasi, kolom identitas/kredensial lainnya sama.
Tidak ada restore database, index, CRL atau counter lama. Penerbitan/pencabutan
identitas uji menambah histori CA secara sah.

## Temuan dan kriteria selesai

| Klasifikasi | Lokasi/bukti | Dampak dan prioritas | Kriteria selesai |
|---|---|---|---|
| Risiko desain/operasional | `vanguard/health.py:dependency_ready`, `probe`; satu503 dengan CA unknown | P2: readiness sesaat gagal; asal exception belum diketahui | Reproduksi dengan instrumentasi aman, tentukan penyebab dan uji perbaikan jika terbukti; batas waktu/fail-closed tetap |
| Risiko desain/operasional | Filesystem host sekitar1,3GiB kosong | P1 sebelum build/VM tambahan: risiko kehabisan ruang | Tambah kapasitas atau arsipkan bukti dengan verifikasi integritas; jangan hapus bukti/backup otomatis |
| Perilaku yang belum diuji | Client utama masih cert/sesi expired, unit auto-restart; uji memakai identitas baru | P1 sebelum penggunaan utama: endpoint utama belum siap koneksi | Penggantian identitas terencana dengan binding immutable, login baru dan uji native |
| Perilaku yang belum diuji | Profil/gatewayinternet belum dikonfigurasi pada layanan utama | P1 sebelum rollout internet: hasil aplikasi internal tidak membuktikan blokir internet penuh | Deploy profil/policy terencana, uji Windows dan LAN/Wi-Fi fisik termasuk revoke serta reboot |
| Perilaku yang belum diuji | Windows native, EXE/UAC, reboot/outage layanan pada sesi ini | P2: bukti sebelumnya tidak otomatis berlaku sebagai pengujian ulang | Jalankan matriks native yang sesuai setelah kapasitas cukup |

Tidak ada bug produk baru dengan penyebab terkonfirmasi pada alur akses yang
diuji. Pernyataan ini tidak berarti sistem bebas bug. Temuan kelayakan sebelumnya
di [laporan30Oktober](UJI_KELAYAKAN_2026-10-30.md) tetap berlaku sesuai scope-nya.

## Koreksi harness dan bukti yang dipertahankan

1. Assertion admin awal mengharapkan warning hampir expired pada fixture baru.
   Diganti pemeriksaan penjelasan masa berlaku pada riwayat. Warning hampir
   expired tidak diklaim diuji dengan fixture ini.
2. Worker memanggil `connect` langsung tanpa handler SIGTERM milik CLI. Sebelum
   dihentikan, unit disposable diberi runtime SIGINT agar `finally` cleanup
   berjalan. Drop-in dihapus setelah tunnel dipastikan berhenti.
3. Driver exercise exit1 setelah semua skenario akses karena alasan revoke
   buatan harness tidak termasuk enum admin. Cleanup dilanjutkan dengan
   `operator_request`, lalu diverifikasi terpisah. Bukan satu run exit0.
4. Cleanup pertama menganggap transient unit yang sudah tidak loaded masih ada.
   Retry memeriksa state dan tetap memastikan tunnel/config hilang.
5. Verifier histori pertama memasukkan counter TOTP sebagai immutable. Koreksi
   membandingkan kolom tetap serta membuktikan counter anti-replay maju.

Log kegagalan, retry, XML dan hasil perkasus berada di
`state/live014-20261031/` yang diabaikan Git. Backup dan inventaris kredensial
tetap lokal; akun uji ditandai DISABLED_REVOKED. Tidak ada perubahan source produk,
installer, key utama atau unit layanan utama. GitHub hanya menerima dokumentasi.

Kondisi akhir: CA/server/admin/clientUbuntu running; attacker/Win10/Win11 off.
Client utama tetap fail-closed karena identitas/sesi expired, tanpa tunnel aktif.
Kebijakan aplikasi dikembalikan byte-identik; listener demo serta peer uji hilang.
