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

## Kelanjutan investigasi — mode diagnostik lokal

Sesudah publikasi awal, gap observabilitas pada `vanguard/health.py:probe` telah
diverifikasi: exception dependency yang berbeda sama-sama diringkas `unknown`.
Klasifikasi **fitur belum tersedia, P2**; bukan bukti penyebab503 lama. Kriteria
selesai untuk fitur ini ialah alasan aman yang dapat dibedakan, batas waktu tetap,
output HTTP tetap dan pemeriksaan tidak mengubah state.

Source kini menyediakan `python -m vanguard.health <role> --diagnose` dengan
kode alasan dari allowlist dan waktu tiap pemeriksaan. Tidak ada pesan exception,
URL, credential atau body mentah. CLI tetap membatasi subprocess6detik. Endpoint
HTTP dan keputusan admission tidak berubah; versi paket VM/installer belum
memuat tambahan ini. Petunjuk ada di Bab7.3 manual admin tunggal dan `docs/API.md`.

Validasi tambahan:

- Baseline health/status/contention/capacity: **16PASS,47,57detik**.
- Setelah perubahan, suite yang sama ditambah diagnostik: **26PASS,61,39detik**.
  Termasuk koneksi lokal yang benar-benar ditolak, lock CA sementara, subprocess
  hang yang dihentikan, dan tidak adanya secret sentinel pada keluaran.
  Klasifikasi exception TLS/connect/read juga diuji menggunakan injeksi exception;
  tidak diklaim sebagai insiden TLS nyata di VM.
- Pemeriksaan server terpasang→CA: **20/20ready**. Harness juga mencoba jalur
  server→dashboard yang bukan jalur diizinkan firewall admin;20request itu gagal,
  dipertahankan sebagai kesalahan pemilihan jalur uji, bukan kegagalan backend.
  Ruleset admin hanya mengizinkan akses dashboard dari host lab.
- Kandidat dijalankan dari staging terpisah di CA/server/admin, memakai
  environment dan user masing-masing service: **36/36ready** dalam12putaran.
  Durasi maksimum termasuk SSH4,884detik; durasi check maksimum3128,6ms.
- Hash config ketiga VM serta root/key/index/serial CA tetap; tidak ada penerbitan,
  pencabutan atau penggantian identitas dalam investigasi ini.
- Postflight layanan terpasang: **30/30HTTP200**, nolpeer; hash module health
  terpasang masih sama dengan sebelum perubahan kandidat, versi paket0.1.14.

Kejadian503 sebelumnya **belum direproduksi dengan penyebab terkonfirmasi**.
Tambahan diagnostik menutup gap penelusuran lokal, bukan memperbaiki akar masalah
yang belum diketahui. Pemeriksaan terpisah dapat melewatkan insiden sementara;
tidak membuktikan sebab request lama. Tidak ada kenaikan timeout, restart layanan,
perubahan firewall, atau rollback CA. Bukti tambahan privat berada di
`state/readiness-20261031/`; kandidat staging terpisah dari paket terpasang.

## Audit bug lanjutan — validasi respons readiness dan sesi

Audit dimulai dari source `ccdaafd`, tree bersih. Mockup dibatalkan; tidak ada
pekerjaan antarmuka. Tiga bug berikut dibuktikan dengan regresi gagal sebelum
implementasi diperbaiki. Semua memerlukan respons malformed; tidak ditemukan
bukti bahwa respons seperti itu terjadi pada VM lab.

| Klasifikasi / prioritas | File dan fungsi | Bukti sebelum perbaikan / dampak | Kriteria selesai dan hasil source |
|---|---|---|---|
| Bug terbukti, P2 | `vanguard/health.py`: `bounded_readiness`, `dependency_ready` | JSON non-object memicu AttributeError; status ready tanpa checks atau berlawanan dengan checks tetap dipercaya. Status dapat salah sehat atau route gagal | Validasi struktur, check sesuai role dan konsistensi status; malformed menjadi unknown. Regresi lulus |
| Bug terbukti, P2 | `vanguard/client.py`: `_login_employee` | Respons login ditulis sebelum validasi, sehingga sesi lama terganti oleh respons rusak; field password/metadata tambahan ikut tersimpan | Validasi username, token dan expiry sebelum menulis; sesi lama byte-identik saat ditolak, simpan hanya tiga field sesi. Regresi lulus |
| Bug terbukti, P3 | `vanguard/client.py`: `logout_employee` | JSON non-object memicu AttributeError; token tetap ada tetapi pesan pencabutan belum terkonfirmasi tidak muncul | Respons malformed masuk jalur error aman, token dipertahankan, retry valid dapat selesai. Regresi lulus |

Validasi expiry menolak string, bool, waktu lewat, NaN dan infinity; token harus
bertipe string dengan panjang sesuai kontrak server, username sesuai permintaan.
Field tambahan respons login tidak disimpan. Login saja tetap tidak memberi akses;
enam pemeriksaan admission tidak berubah.

Hasil aktual:

- Baseline health/client/logout/transport: **61PASS/1SKIP,107,37detik**.
- Reproduksi sebelum perbaikan readiness/login: **27FAIL,1,53detik**; bukti gagal
  dipertahankan. Kasus logout tambahan: **3FAIL/1PASS** sebelum guard tipe.
- Sesudah perbaikan readiness/login, suite terpilih termasuk kapasitas CA:
  **89PASS/1SKIP,106,02detik**.
- Setelah guard logout, regresi sesi/login/logout: **23PASS,31,36detik**.
  Suite terakhir tumpang tindih; angka tidak dijumlahkan sebagai112tes unik.
- Source final readiness di staging CA/server/admin: **12/12ready**,4putaran;
  memakai environment dan user service. Config/root/key/index/serial tetap.

Tes malformed child menjalankan subprocess nyata dan route Flask; tes sesi
menggunakan respons sintetis serta file nyata. Alur normal HTTPS CA/server/client
juga diuji dengan CA sementara dan adapter WireGuard fake. Suite Linux bukan
Windows native; Windows ACL dilewati. Testdouble lama yang hanya berisi status
ready atau token pendek disesuaikan ke format respons server nyata.

Regresi baru: `tests/test_health_result_validation.py` dan
`tests/test_client_session_response.py`. Bukti privat `state/bugcheck-20261031/`.
Perubahan masih **source/staging**, belum wheel/EXE atau paket layanan/client
terpasang. Tidak ada perubahan akun, sertifikat, firewall, unit, kernel atau
paket VM. **503 historis belum diketahui penyebabnya** dan tidak diklaim
teratasi oleh tiga bug yang ditemukan melalui injeksi respons ini.

Postflight layanan terpasang pada audit ini: **29/30HTTP200**, satu
admin/readyz503 dalam1,324detik dengan `database=unknown`, CA/server ready.
Pengamatan ini berbeda dari kejadian server/CA sebelumnya. Pemeriksaan langsung
DB admin memakai user service kemudian **30/30berhasil, integrity_check=ok**.
Klasifikasi: risiko operasional P2 dengan sebab **BELUM_TERKONFIRMASI**, bukan
bukti database korup. Kriteria selesai: rekam penyebab aman saat kejadian dapat
direproduksi, lalu perbaiki sebab yang terbukti tanpa melonggarkan timeout.
Hash kode health paket terpasang tetap0.1.14 lama dan nolpeer; perbaikan source
belum aktif pada service. Hasil30/30 DB tidak menghapus503 yang sudah tercatat.
