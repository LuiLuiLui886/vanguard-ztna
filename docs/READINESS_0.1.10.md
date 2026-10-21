# Readiness0.1.10 dan publikasi CA0.1.11

Status21 Oktober: **0.1.11 terpasang pada CA/server/admin**. Client Ubuntu,
attacker dan Windows tetap0.1.9. Source e0e58dd pada branch
`fix/2026-10-20-readiness-lock`. Lihat [checkpoint](CHECKPOINT.md).

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
-0.1.10: full lokal213PASS/1SKIP676,76detik; CI39437511242 SUCCESS, Linux3.10/3.12
  masing-masing213PASS/1SKIP, Windows helper28PASS/2SKIP. Rollout terverifikasi
  dengan backup,15hash identitas/state dan enam definisi VM tetap. Postflight
  HTTPS dari VM-ADMIN31HTTP200/2HTTP503; kedua503 admin dependency server.
  Sampel dari host ke CA/server ditolak firewall dan bukan bukti bug aplikasi.

## Riwayat rollout0.1.10 dan pemulihan

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


## Versi0.1.11 — publikasi CA

Readiness tetap mempunyai batas dan makna yang sama. Perubahan kecil di
`Publication.publish_file/recover` menghindari penulisan ulang anggota identik.
Setiap file tetap fsync; setiap direktori parent fsync sekali sebelum manifest
commit dihapus. Manifest penuh, staging durable, lock dan validasi seluruh
generasi tetap wajib. Atomic rename satu file bukan transaksi seluruh CA.
Jika barrier gagal, manifest tetap ada untuk roll-forward pada recovery berikutnya.

34 tes terarah PASS86,54detik, termasuk SIGKILL serta fsync inode/direktori gagal.
Benchmark bergantian pada CA sementara77anggota/74identik:0.1.10 membutuhkan
2,458–2,606detik; kandidat1,165–1,201detik (tiga sampel masing-masing).
Ini hasil terisolasi tanpa writer operasional, bukan SLA atau bukti power-loss.
CI39572681808 pada source e0e58dd SUCCESS:218PASS/1SKIP pada masing-masing
Linux3.10/3.12,28PASS/2SKIP pada helper Windows. Full lokal218PASS/1SKIP488,85detik. Rollout0.1.11 selesai pada ketiga layanan:
backup konsisten terverifikasi, pip check,23anggota aplikasi per VM dan15hash
identitas/state cocok, invariant CA/enam XML/nol peer/grant kosong PASS.
Wheel SHA256 `546b1ea8616f1d83f3731ef1e674933d9aa325c6fa91f49f54c728a347f98aa0`.
Pemulihan untuk versi ini menggunakan paket0.1.10 yang terverifikasi, dengan
state terbaru tetap dipertahankan; jangan restore index/CRL/database.

Postflight HTTPS awal31HTTP200/2HTTP503, maksimum1,731detik. Keduanya admin
server not_ready. Diagnosis60sampel berikutnya ready, tetapi admin dijalankan
sebagai child terinstrumentasi sehingga tidak membuktikan jalur HTTPS dashboard
selalu siap. Biaya publikasi CA teratasi pada sampel; contention/transport503
belum mempunyai akar masalah terkonfirmasi. Jangan menaikkan timeout atau
mengubah unknown menjadi ready tanpa bukti. Power-loss dan cleanup interupsi
Windows tetap terbuka. Hasil penutup berikutnya dicatat dalam jurnal/checkpoint.

Pengukuran HTTPS penutup21 Oktober: berurutan30/30HTTP200 (maks1,074detik),
paralel29HTTP200/1HTTP503 (maks2,314detik), liveness3/3HTTP200. Satu503 pada
admin dependency server; CA/database ready. Ini membatasi klaim: optimasi CA
terukur, tetapi readiness paralel belum stabil. Bukti final-https-samples.json
tersimpan privat; seluruh hasil gagal sebelumnya dipertahankan.
