# VanGuard 0.1.9 — ketahanan dan pengelolaan akses

Source berada pada branch `hardening/2026-10-18-resilience`. Pada20 Oktober,
paket0.1.9 sudah dipasang pada lima Ubuntu dan satu Windows dengan backup serta
pemeriksaan identitas. Matriks VM Linux dan Windows selesai, termasuk reboot,
revoke TCP aktif dan replacement. Identitas uji sudah dicabut dan cleanup
terkonfirmasi. Power-loss media CA, risiko cleanup interupsi segera di Windows,
serta readiness503 akibat konflik lock CA tetap pekerjaan lanjutan; jangan
menyamakan matriks lulus dengan seluruh risiko sudah tertutup.
Lihat [hasil rollout](VALIDASI_ROLLOUT_2026-10-20.md),
[audit](AUDIT_HARDENING_2026-10-18.md) dan [jurnal](PROGRESS_2026-10-20.md).

## Perubahan perilaku

- CA menjalankan OpenSSL di staging privat. Manifest commit tersinkronkan memuat
  index, serial, crlnumber, signed CRL, arsip sertifikat dan cache issuance.
  Operasi berikutnya menyelesaikan publikasi manifest yang terputus sebelum
  mutasi baru. Setiap file memakai fsync/rename; konsistensi seluruh state berasal
  dari manifest dan lock, bukan rename satu file. Counter rusak tanpa manifest
  lengkap ditolak, tidak ditebak. Root CA tidak dibuat ulang pada upgrade.
- Staging yang terinterupsi sebelum commit dipertahankan dalam
  `interrupted-transactions/`; operator perlu mengawasi ukurannya. Snapshot
  transaksi selesai boleh dibersihkan. State `.old` tidak menjadi sumber rollback.
  Menyalin/verifikasi seluruh state pada tiap operasi cocok untuk lab kecil;
  biaya I/O meningkat dengan arsip. Power-loss disk tetap berbeda dari SIGKILL.
- Logout karyawan mencabut satu token beserta challenge dan lease yang dimiliki
  token itu. Token lain tetap berlaku. Lock serialisasi sama dengan verify,
  sehingga renewal yang selesai lebih dahulu dihapus oleh logout berikutnya.
  Invalidasi disimpan sebelum kernel dipanggil; kegagalan penghapusan peer
  memerlukan retry. Server menyimpan hash tombstone untuk idempotensi.
- Client menggunakan lock proses, menolak tunnel lama, dan mempertahankan config
  jika ownership atau cleanup tidak pasti. Linux menandai alias interface milik
  proses; Windows hanya melepas service setelah instalasinya terkonfirmasi.
  Guard bukan pertahanan terhadap administrator root yang sengaja mengubah sistem.
- Daemon mengirim heartbeat watchdog setelah reconcile selesai. Unit systemd
  memakai `WatchdogSec=90`, timeout abort 5 detik, kemudian hook menghentikan wg0.
  Nilai tersebut bukan jaminan batas real-time pada host gagal/overload.
- Dashboard membedakan registry, lease, peer, handshake terakhir dan byte RX/TX
  kumulatif. Kegagalan observasi menjadi “Tidak diketahui”. Peer terpasang belum
  membuktikan koneksi atau aplikasi aktif. Warning sertifikat muncul tujuh hari
  sebelum expiry; lease renewal tetap tidak memperpanjang sertifikat.

## Pemakaian tambahan

Pada client dengan paket 0.1.9, jalankan `vanguard-client logout` (Ubuntu) atau
`python -m vanguard.client logout` (Windows), memakai directory/trust yang sama
dengan login. Bila server tidak terjangkau, token lokal dipertahankan untuk retry
dan pesan menyatakan pencabutan belum terkonfirmasi. Setelah konfirmasi, token
lokal dihapus. Ctrl+C pada proses connect mempercepat cleanup tunnel lokal;
logout sendiri tidak mengambil alih tunnel milik proses lain. Tanpa token lokal,
CLI tidak mengklaim pencabutan server sudah terjadi.

Untuk mengganti identitas, buka riwayat perangkat: hentikan tunnel, cabut akses
lama dan tunggu `revoked`. Buat ID dan kedua key baru di direktori baru pada
client, dengan IP tunnel lama. Unggah request baru melalui form penggantian.
Sistem mempertahankan binding/history lama, mencatat hubungan old/new, serta
mewariskan akun dan IP. Jika proses parsial, retry identitas baru yang tercatat;
jangan membuat CSR/key lain untuk retry yang sama. Bundle dan admission mengikuti
alur biasa. Penggantian ini memerlukan jeda akses; tidak ada rotasi tanpa jeda.

Halaman `/operations` memerlukan sesi admin dan menampilkan ukuran DB/journal,
jumlah audit, disk bebas dan pertumbuhan sejak sampel sebelumnya. Sampel dibuat
paling sering sekali per jam saat halaman diperiksa, bukan background monitoring.
Ambang warning: DB 100 MiB atau disk bebas kurang dari 100 MiB. Tidak ada purge
otomatis. Ukuran journal systemd diperiksa operator dengan `journalctl --disk-usage`.

## Readiness dan resource aplikasi

`/healthz` tetap liveness. `/readyz` memberi HTTP 200 `ready` atau 503 `not_ready`
dengan status aman per dependency; subprocess keseluruhan dibatasi 6 detik.
CA memeriksa state/CRL yang ada tanpa menerbitkan CRL. Server memeriksa SQLite,
CA readiness, heartbeat daemon dari boot yang sama dan observasi interface.
Admin memeriksa SQLite serta CA/server. Ini snapshot, bukan otorisasi admission.
Readiness dapat menjadi unknown ketika CA sedang memegang lock; retry sesuai
interval monitor. Readiness tidak memperbaiki transaksi atau mengubah peer.

Resource opt-in `internal-demo` adalah **10.8.0.1, TCP, port 8082**. Grant harus
menentukan `device_id` dan `username` yang sama dengan binding, serta seluruh
field resource/address/protocol/port tersebut. File awal
`deploy/resource-policy.example.json` berisi daftar kosong, sehingga default deny.
Nilai akun operasional hanya ditulis pada file lokal privat di guest.

Firewall dipasang dengan flag `--application-policy` bersama `--windows-client`.
Set `VANGUARD_RESOURCE_POLICY=/etc/vanguard/resource-policy.json` hanya sesudah
aturan firewall tersedia. Grant dinamis berasal dari peer, lease dan sesi aktif,
dengan timeout lebih pendek dari lease. Gate input diperiksa sebelum established;
output aplikasi juga dibatasi. Penghapusan/expiry grant menghentikan paket TCP
yang sudah terhubung. Kegagalan policy menghasilkan deny; nftables gagal harus
ditangani sebagai kegagalan layanan, bukan diterima dengan policy lama.

Tes namespace menggunakan echo TCP sebagai aplikasi uji. Tidak ada aplikasi
produksi baru yang otomatis dijalankan. Uji aturan veth bukan bukti WireGuard
handshake, Windows VPN, atau pencabutan sertifikat melalui seluruh layanan.

## Rollout dan pemulihan yang disiapkan

1. Catat kondisi enam VM, versi paket, SHA source, status tunnel dan sesi aktif.
   Siapkan maintenance window. Backup XML serta paket/unit/env sebelum perubahan.
2. Pada CA, hentikan service dan pastikan tidak ada CLI CA berjalan. Simpan
   **seluruh** state termasuk `.transaction` dan `interrupted-transactions` ke
   arsip privat mode 0600; verifikasi arsip/hash. Jangan menyalin state aktif
   tanpa lock/quiescence. Simpan SQLite melalui backup API atau saat service
   berhenti; catat backup server/admin secara terpisah.
3. Uji paket pada salinan CA dengan penyesuaian path konfigurasi di salinan saja.
   Jalankan pemeriksaan consistency tanpa memperbaiki counter produksi. Jika
   state lama tidak konsisten, hentikan rollout dan simpan bukti; upgrade tidak
   memberi izin menebak counter, menulis ulang index atau membuat CA baru.
4. Pasang CA dahulu, lalu server/daemon/admin, kemudian client. Pertahankan env,
   identity dan registry. Jalankan daemon sebelum API dan periksa readiness.
   Startup server/daemon membatalkan lease sehingga client memerlukan admission
   baru. Perbarui unit systemd dari kandidat dan lakukan daemon-reload.
5. Resource policy adalah langkah opt-in terpisah. Simpan ruleset firewall lama,
   gunakan rollback timer, cek SSH baru sebelum membatalkan timer. Salinan env
   yang baru tidak boleh membocorkan bearer token. Mulai dengan grants kosong;
   tambahkan identitas disposable hanya setelah deny LAN/port lain dibuktikan.
6. Uji login saja tanpa peer, proof invalid, admission sah, beberapa renewal,
   expiry/disable/revoke/logout, kegagalan CA, daemon stop/hang dan reboot client.
   Gunakan identitas disposable; pertahankan Ubuntu dan Windows utama.
7. Bila kandidat gagal, hentikan API dan tunnel dahulu. Restore paket/config
   yang kompatibel sambil mempertahankan **state CA terbaru**. Selesaikan commit
   manifest memakai kode baru sebelum downgrade CA; jangan menjalankan 0.1.8
   terhadap manifest yang belum selesai. Jangan restore DB/index/CRL lama yang
   dapat menghidupkan kembali sesi atau sertifikat tercabut.

Rollout utama dan seluruh matriks VPN langsung masih harus dicatat per skenario.
Hasil unit/mock, HTTPS lokal, Windows native, namespace kernel dan VM produksi
tidak boleh dijumlahkan menjadi satu klaim dukungan penuh.

Referensi semantik supervisor: [systemd watchdog/notify](https://www.freedesktop.org/software/systemd/man/257/sd_notify.html).
Timeout set dan gate paket mengikuti [nftables](https://www.netfilter.org/projects/nftables/manpage.html).
