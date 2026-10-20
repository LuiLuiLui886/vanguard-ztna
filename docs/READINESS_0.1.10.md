# Readiness VanGuard 0.1.10

Status: kandidat pada branch `fix/2026-10-20-readiness-lock`; rollout belum
dinyatakan selesai. Lihat [checkpoint](CHECKPOINT.md) untuk status terpasang.

## Masalah dan perbaikan

HEALTH-LOCK-01 adalah risiko desain yang terbukti pada0.1.9:
`vanguard.health.probe/ca_state` langsung mengembalikan unknown ketika writer
memegang lock. Pengukuran read-only VM-CA20 Oktober mencatat transaksi memegang
lock sekitar2,8–3,2detik; snapshot sebelumnya18ready/12konflik lock. Dependency
readiness memiliki read timeout1detik, sehingga menambah retry CA saja akan
tetap dipotong caller.

0.1.10 menunggu shared lock maksimal3,5detik, polling50ms. Hanya setelah lock
didapat probe memeriksa manifest, konsistensi state dan validitas CRL. Ia tidak
memanggil constructor Authority, menerbitkan CRL, memulihkan transaksi, atau
menambahkan peer. Pending manifest, corruption, CRL tidak valid dan long
contention tetap tidak siap; hasil lama tidak dipakai sebagai cache sehat.

Caller memakai connect timeout0,5detik dan read timeout4,25detik untuk CA atau
5detik untuk server. Dua dependency admin diperiksa bersamaan oleh maksimal
dua worker, agar waktu nested request tidak dijumlahkan. Subprocess keseluruhan
tetap dihentikan setelah6detik; bila timeout/error hasilnya unknown503.
Timeout socket bukan deadline keseluruhan, sehingga penjagaan subprocess tetap
diperlukan. Waktu nyata dapat bertambah karena penjadwalan OS/host overload.

`/healthz` tetap sederhana. `/readyz` tidak memberikan akses dan bukan bukti
aplikasi bisnis dapat dijangkau. Jangan mengganti503 dengan200 ketika pemeriksaan
tidak berhasil. Kegagalan yang terus berulang membutuhkan inspeksi CA/dependensi.

## Bukti dan kriteria selesai

- Baseline health/status pada snapshot52e31db:7PASS14,18detik. Full baseline
  awal di checkout bergerak dihentikan dan tidak digunakan sebagai bukti lulus.
- Reproduksi sebelum patch:6gagal/1lulus pada tes perilaku baru. Kandidat:
 15PASS43,77detik pada suite health/status+contention; Ruff/pip check PASS.
- Tes menggunakan CA sementara serta flock/thread asli untuk contention,
  membandingkan hash/permission seluruh file, dan menghentikan child macet
  yang nyata setelah6detik. Tes parameter transport memakai stub HTTP dan tes
  paralel dependency memakai barrier; bukan pengujian HTTPS/VM.
- Staging VM-CA melalui wheel pada PYTHONPATH (belum mengganti service):
 20/20ready, waktu maksimum3,344detik. Ini sampel dengan writer normal aktif,
  bukan jaminan semua beban atau simulasi power-loss.
- Suite lengkap, CI dan rollout HTTPS masih menunggu hasil. Kriteria selesai:
  pemeriksaan terarah/full suite PASS, backup paket/config terverifikasi, versi
  layanan tepat, hash identitas/state aman dan sampel HTTPS pascarollout dicatat.

## Rollout dan pemulihan

Perubahan hanya pada health probe layanan Linux. Siapkan backup CA/server/admin
dengan layanan terkait dihentikan dan periksa integritas arsip. Pastikan tidak
ada peer aktif sebelum maintenance. Install wheel0.1.10 yang hash-nya cocok,
lalu hidupkan CA, tunnel/daemon/server, dan admin. Client Ubuntu/Windows tetap
kompatibel pada0.1.9; jangan mengklaim keenam paket sudah0.1.10.

Bila startup gagal, hentikan admission/tunnel; kembalikan **paket**0.1.9 yang
terverifikasi, dengan state terbaru tetap dipertahankan. Jangan restore database
akses, index, serial, crlnumber, CRL, atau root/key lama. Tidak ada migrasi state
pada patch ini. Semua backup/key tetap di lokasi privat di luar Git.

WIN-CLEANUP-02 dan power-loss media CA tetap terbuka. Patch readiness tidak
mengatasi kedua masalah tersebut, tidak mengganti framework, dan tidak mengubah
enam pemeriksaan perangkat, sesi karyawan, binding, atau WireGuard.
