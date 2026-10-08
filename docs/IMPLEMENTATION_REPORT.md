# Hasil implementasi VanGuard — 8 Oktober 2026

## Status versi 0.1.2

**Versi 0.1.2 sudah berjalan pada lima VM Ubuntu Server 22.04.** Source aplikasi,
installer, layanan systemd, firewall, dashboard, pengujian dan panduan tersedia.
Pada pemeriksaan sesudah rollout, client utama memiliki peer `10.8.0.2/32`,
handshake WireGuard kernel dan ping tunnel berhasil. Hash semua berkas paket
terpasang pada lima VM sesuai source lokal.

Observasi stabilitas COMPLETE: 51/51 sampel PASS selama 681,95 detik. Seluruh
layanan/firewall, peer dan ping sehat, nol removal sejak awal observasi, serta
12 deadline lease berbeda membuktikan pembaruan admission berjalan.
Bukti: `stability/health.json` dalam direktori sesi.

## Perbaikan sesi ini

Audit removal sekarang mengandung alasan khusus serta waktu CRL/validator.
Audit 72, 77 dan 84 pada 8 Oktober menunjukkan `crl_future`: CRL bertanda tangan
sah mendahului waktu lokal sekitar 7–41 ms pada batas pergantian detik. CA dan
server memakai NTP, tetapi tetap memiliki selisih/jitter puluhan milidetik.

Versi 0.1.2 menunggu sekali jika lastUpdate mendahului waktu lokal <=1 detik,
lalu memeriksa ulang signature, issuer, periode CRL dan trust anchor pada waktu
aktual. Tidak ada penerimaan CRL sebelum berlaku, penggunaan CRL expired, perubahan
jam, atau perubahan timestamp issuer. Selisih lebih besar dan revalidasi gagal
tetap menolak admission serta memutus peer melalui daemon. Challenge yang habis
saat fetch/proof juga ditolak sebelum penambahan peer.

Pada 120 probe CRL nyata sesudah pemasangan, semua validasi lulus. Sebanyak 17
penantian 8,7–99,7 ms terjadi; seluruh waktu penerimaan berada di antara lastUpdate
dan nextUpdate. Audit historis ID 29 memiliki pesan umum sehingga penyebabnya
secara individual tetap tidak bisa dibuktikan.

Penyimpanan evidence dibuat atomik dengan fsync, status per tahap, dan larangan
menimpa hasil lama pada run baru. Reboot mendukung `--resume`; identity mencatat
nama/direktori/tahap/cleanup untuk recovery. Pengujian peer asing pada kernel tanpa
admission dihapus dari skrip operasional; unit test adapter memori tetap tersedia.

## Hasil yang sudah terverifikasi

| Pemeriksaan | Hasil dan bukti |
|---|---|
| Suite lokal Python 3.12 | 54 PASS, `docs/test-results.xml` |
| GitHub CI Ubuntu 22.04 | 54 PASS Python 3.10 + 54 PASS Python 3.12; build/checksum PASS, [bukti CI](CI.md) |
| Suite guest Ubuntu 22.04/Python 3.10 | 54 PASS, `docs/guest-test-results.xml` |
| Kualitas source | Ruff, pip check dan sintaks shell PASS |
| Paket terpasang | Lima VM versi 0.1.2, SHA-256 source cocok, `installed-manifest.json` |
| Setelah rollout | Layanan, lease, allowed IP, peer dan ping PASS, `post-upgrade/health.json` |
| Matriks firewall | 40 TCP allow/deny PASS, `operations-matrix.json` dan `firewall-matrix.json` |
| Attacker | 401 tanpa token, 403 verify palsu, 400 challenge palsu; semuanya PASS |
| Bypass LAN | Attacker dengan route langsung ke IP tunnel tetap tidak bisa ping |
| Registrasi | Identitas sementara `10.8.0.3` terdaftar tanpa peer live |
| Admission | Binding salah/proof salah/replay ditolak; proof sah menambah peer kernel |
| Revocation | CA-only revoke menghapus peer, audit `certificate_revoked`, readmission ditolak |
| Cleanup | Identitas sementara dicabut/disabled; client utama tetap terhubung |
| Probe CRL | 120 PASS, 17 penantian sah, `crl-boundary-probes.json` |
| Reboot lima guest | CA/server/client lulus sebelum upgrade; admin/attacker lulus setelah upgrade |
| Lease nyata 300 detik | Sebelum upgrade, removal sekitar 3,75 detik setelah deadline dan recovery PASS |
| Dashboard HTTPS | GET health/login PASS dengan verifikasi Root CA; form CSRF tersedia |

Bukti sesi terbaru berada di `state/deployment/resume-2026-10-08-2145/` kecuali
lease/reboot pada `state/deployment/operations-{lease,reboot}.json`. Laporan identity
memiliki nama `final-check-*.json` yang unik. Evidence mentah adalah data lokal privat;
salin ringkasan nonrahasia yang diperlukan ke lampiran TA.

## Cakupan dan batas pengujian

Suite lokal/guest memakai OpenSSL nyata untuk CA dan fixture sertifikat/CRL.
Kasus negatif mencakup issuer/signature/periode/serial revoked, CA certificate,
serverAuth certificate, extension kritis asing, binding, proof, replay concurrent,
challenge expired, TOTP/replay/CSRF, workflow parsial dan HTTPS socket nyata.
Adapter WireGuard pada suite tersebut berada dalam memori. Bukti kernel berasal
dari pengujian lima VM yang dicatat terpisah; 54 tes guest tidak berarti 54 tes
kernel WireGuard.

Enam tes baru mencakup batas detik CRL, future jauh, jam tidak maju, CRL expired
selama menunggu, signature salah, dan challenge habis selama fetch. Tidak ada
pelonggaran validitas waktu sertifikat atau CRL.

Uji CA offline/pulih, stop daemon, API restart, serta shutdown client pernah lulus
pada 24 September. Riwayat terperinci dipertahankan dalam
[laporan September](IMPLEMENTATION_REPORT_2026-09-24.md). Skenario gangguan tersebut
tidak seluruhnya diulang pada kernel setelah upgrade 0.1.2; regresi logika tetap
tercakup suite terbaru. Reboot workstation belum diuji pada sesi ini.

## Penyimpanan dan pemulihan pekerjaan

- [Jurnal perubahan](PROGRESS_2026-10-08.md) mencatat rencana, hasil, temuan dan titik lanjut.
- [Checkpoint](CHECKPOINT.md) dan [ringkasan lanjut](../LANJUTKAN_PROYEK.md) memuat status aktif.
- Backup source/config/state sebelum rollout: `state/backups/2026-10-08-2154/`.
- Rekaman rollout: `state/deployment/resume-2026-10-08-2145/rollout.json`.
- Artefak lokal: `dist/vanguard-0.1.2.tar.gz`, wheel 0.1.2 dan `dist/SHA256SUMS`.
  Hasil pembuatan/verifikasi dicatat pada jurnal. Catatan publikasi GitHub dapat
  lebih baru daripada arsip source yang dipertahankan tanpa overwrite.

Backup state berisi kredensial/key dan dilindungi permission privat. Arsip source
harus mengecualikan state, database, env aktif, key dan halaman aktivasi. Backup
aplikasi bukan snapshot disk VM atau salinan di perangkat lain. Rollback paket
tidak boleh mengembalikan index CA/CRL lama yang membatalkan pencabutan.

## Temuan yang belum ditutup

- Sesi sore menemukan systemd segfault saat boot dan checksum image/tool berbeda.
  Saat sesi malam, lima guest sudah sehat; checksum image cocok dengan build Ubuntu
  asli dan `dpkg -V` untuk paket yang diperiksa bersih. Penyebab perubahan keadaan
  belum diketahui. Uji model CPU tidak menyelesaikan masalah dan XML asli dipulihkan.
- Audit ID 29 belum bisa dikaitkan secara pasti dengan penyebab CRL future terbaru.
- Konfirmasi pemasangan TOTP di HP dan login pribadi operator masih ditunggu.
- Stabilitas jangka panjang di luar jendela observasi tidak diklaim.

Topologi lima node, alamat tunnel, UDP 51820, CA dan identitas utama dipertahankan.
Source/kernel WireGuard tidak dimodifikasi. Panduan operasional ada di
[DEPLOYMENT.md](DEPLOYMENT.md), [SECURITY.md](SECURITY.md) dan [DEMO_TA.md](DEMO_TA.md).
