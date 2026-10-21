# Kapasitas HTTPS CA — 21 Oktober 2026

Status: kandidat konfigurasi di branch `fix/2026-10-20-readiness-lock`.
Paket aplikasi tetap0.1.11; perubahan unit systemd memerlukan pemasangan unit
serta restart CA, bukan sekadar upgrade wheel. Status terpasang ada pada
[checkpoint](CHECKPOINT.md).

HEALTH-CAPACITY-01 adalah **risiko desain/P2** pada
`deploy/systemd/vanguard-ca.service`. Empat thread melayani TLS handshake dan
request. Satu pemantauan CA/server/admin bersamaan menghasilkan sampai empat
request readiness CA, ditambah fetch CRL daemon. Saat keempat thread sibuk,
koneksi berikutnya dapat habis budget TLS0,5detik sebelum mencapai handler.

Diagnosis VM dengan tambahan probe server mengamati3/40unknown akibat Requests
ReadTimeout0,505–0,507detik, sementara database/daemon/interface ready. Tes
terisolasi memakai Gunicorn asli, sertifikat sementara tepercaya dan empat
request yang ditahan sampai probe kelima selesai. Konfigurasi4thread gagal di
`ssl.do_handshake`; konfigurasi8thread lulus. Tidak ada CA utama atau private
key operasional dalam fixture. Probe tetap menolak respons503 dependency.

Perubahan menyediakan **satu worker, delapan thread pada CA saja**. Server/admin
masih empat thread. Lock CA, manifest durable, pemeriksaan perangkat dan sesi
karyawan tetap berlaku. Timeout koneksi/read/child tidak dinaikkan. Lebih banyak
thread tidak menjamin kesiapan ketika beban berlebih; hasil gagal tetap unknown
atau not_ready503. Jangan menganggap patch ini menghilangkan seluruh overload.

Kriteria selesai: reproduksi sebelum patch, regresi HTTPS nyata, baseline
health/status, CI, backup unit/state konsisten sebelum rollout, layanan aktif,
identitas/invariant/enam VM terjaga, dan sampel HTTPS nyata dengan beban tercatat.
Baseline15PASS; kandidat16PASS34,71detik. CI/rollout masih IN_PROGRESS.

Pemulihan hanya mengembalikan unit sebelumnya yang hash-nya cocok, reload systemd,
dan restart berurutan dengan layanan terkait. Jangan mengembalikan index, serial,
CRL, root/key atau database lama. Backup hanya disimpan privat. Power-loss CA,
soak panjang dan WIN-CLEANUP-02 tetap membutuhkan bukti terpisah.
