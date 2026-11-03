# Validasi rilis 0.1.15 — 2–3 November 2026

Status: **rilis0.1.15 terpasang dan pengujian di bawah selesai**. Penerimaan akhir
seluruh sistem belum selesai; batas yang belum diuji dijelaskan terpisah.
Perangkat fisik belum tersedia menurut pengguna; pengujian dilanjutkan di VM.

## Temuan dan kriteria selesai

Tabel ini mencatat kondisi saat audit awal; hasil penyelesaiannya ada di bawah.

| Klasifikasi | Lokasi/fungsi | Bukti dan dampak | Prioritas | Kriteria selesai |
|---|---|---|---|---|
| Bug yang berhasil dibuktikan | `scripts/build_endpoint_package.py:build` | README paket menunjuk bab manual yang sudah dihapus; tautan HTML menunjuk main yang belum memuat kandidat. Pengguna dapat mengikuti petunjuk versi berbeda. | P3 | README memakai bagian manual aktif; HTML mengarah branch kandidat; paket diverifikasi. |
| Risiko desain/operasional | `vanguard/health.py`, batas query database dan dependency CA | Sampel 1 November di bawah beban menangkap SQLite `interrupted` karena budget 0,2 detik serta CA ReadTimeout. 48/60 ready saat beban; 30/30 setelah I/O selesai. Ini tidak membuktikan penyebab insiden 31 Oktober. | P2 | Diagnostik terpasang; hasil probe pascarollout tercatat tanpa melonggarkan fail-closed. |
| Perilaku yang belum diuji pada kandidat | EXE, instalasi utama Windows 10/11 | Pada audit awal kandidat baru dibangun. Kini kedua OS lulus instalasi aktual; rincian hasil di bawah. | P1 sebelum publikasi | EXE final nyata terpasang, versi/hash/dependensi cocok, identitas dan firewall tetap. |
| Risiko operasional | Identitas Ubuntu utama `/var/lib/vanguard/client` | Sertifikat berakhir24Oktober, paket0.1.9; akses tidak bisa diaktifkan dengan renewal lease saja. | P1 | Replacement ID/key baru dari client melalui workflow resmi, histori lama tetap, handshake dan dua renewal nyata. |
| Fitur belum diaktifkan di deployment utama | Environment Internet policy dan profil admin | Kode tersedia; konfigurasi utama belum mengaktifkan gateway internet terkelola. | P1 untuk skenario internet | Rollout firewall/policy/profil dengan pemulihan, lalu bukti grant/revoke dan larangan bypass endpoint. |
| Perilaku belum diuji | Perangkat fisik, UAC interaktif, Windows kosong | Perangkat fisik belum tersedia; pengujian VM berprasyarat tidak menggantikannya. | P1 sebelum penerimaan fisik | Pengujian eksplisit pada setiap lingkungan dengan hasil tersendiri. |

## Batas metode

- Full baseline 1 November terhenti tanpa laporan akhir; tidak dihitung lulus.
- Baseline baru berjalan di Linux lokal; tes mock/fixture tidak menjadi bukti VM.
- Windows native memisahkan helpers Python, fakta platform sintetis, filesystem
  konfigurasi, wizard dengan installer stub, extractor C#, bootstrap EXE dan
  instalasi EXE nyata. Hasil setiap lapisan tercatat terpisah di bawah.
- Saat instalasi awal host7,5GiB RAM: Windows dijalankan bergiliran. Pada
  3November host terdeteksi15GiB; definisi VM tidak diubah oleh pekerjaan ini.
- Tidak membuat ulang CA, memulihkan index/CRL lama, mengubah WireGuard kernel,
  atau mengganti password. Backup dan inventaris tetap privat di komputer.

## Koreksi harness yang harus tetap terlihat

Persiapan awal Windows terhenti karena kebijakan eksekusi proses. RemoteSigned
hanya dipasang pada proses persiapan. Observer PowerShell lalu salah membaca
stderr kasus sertifikat invalid sebagai kegagalan seluruh suite. Pemanggilan
Start-Process dengan stdout/stderr terpisah membuktikan exit0; validasi produk
sama. Retry bootstrap menggunakan fixture lama dan gagal CreateNew pada berkas
modifikasi; direktori fixture unik dipakai pada percobaan berikutnya. Semua
kegagalan awal disimpan, bukan dihitung sebagai PASS.

Bukti privat: `state/release-20261101/`. Jurnal:
[1 November](PROGRESS_2026-11-01.md), [2 November](PROGRESS_2026-11-02.md),
[3 November](PROGRESS_2026-11-03.md).

## Hasil aktual sebelum rollout backend

| Lingkungan | Pengujian | Hasil |
|---|---|---|
| Linux lokal | Full suite | 348 PASS, 1 SKIP; 958,53detik |
| Linux lokal | Packaging setelah manual final | 12 PASS; 0,26detik (overlap, tidak dijumlahkan) |
| Windows10 build19044 | Helpers Python native | 46 PASS, 2 SKIP |
| Windows11 build26300 | Helpers Python native | 46 PASS, 2 SKIP |
| Masing-masing Windows | Parsing PowerShell; platform dengan fakta sintetis | PASS; 9kasus platform |
| Masing-masing Windows | Konfigurasi filesystem/crypto nyata | 10 PASS |
| Masing-masing Windows | Wizard resume dengan installer stub | 6 PASS |
| Masing-masing Windows | Extractor C# dengan payload sintetis | 13 PASS |
| Masing-masing Windows | Bootstrap EXE asli | 6 PASS |
| Masing-masing Windows | Instalasi EXE asli pada runtime yang sudah tersedia | exit0, versi0.1.15, pip check PASS |
| Masing-masing Windows | Pascainstalasi | 27file source cocok; identitas/config/firewall tetap, tidak ada tunnel, release lama retained |
| Host | EXE final |39anggota ZIP tertanam; CRC/hash/manifest/payload cocok template final |

EXE final: `01bdfd418cf8ab97543b172d7abaedb1baba507ac215900f895eb18ced591031`.
ZIP final: `c4c8045d1f1d8bdc7535a58d2f28fff4871ecffb3a5cb112a76b709532a3c4e7`.
Tidak ada profil, root CA, alokasi, approval atau identitas khusus dalam template
publik. Password/private key tidak dimasukkan. Kedua Windows shutdown normal
setelah task installer selesai dan bukti disalin. Hasil installer ini terpisah
dari uji jaringan berikutnya; klik interaktif UAC tetap BELUM_TERUJI.

## Layanan utama dan identitas Ubuntu

CA/server/admin berhasil diperbarui dari0.1.14 ke0.1.15 setelah backup quiescent.
Client Ubuntu diperbarui dari0.1.9 ke0.1.15. Hash27file source per backend,
pip check dan invariantCA lulus. Pascapembaruan:30/30health/readiness, lima guard
otorisasi, integritas DB, histori7tabel server dan6tabel admin sesuai backup.
Tidak ada pemulihan state CA/DB atau penggantian Root CA. Hash root/key tetap.

Identitas lama `vm-client` yang habis24Oktober dicabut. Pengganti
`vm-client-20261102` memakai dua key baru yang dibuat di client; workflow resmi
mewarisi akun/IP10.8.0.2 tanpa mengganti binding lama. Berkas lama tetap di tempat.
Unit client memakai drop-in menuju `/var/lib/vanguard/client-20261102`. Registrasi
serta login tidak menambah peer. Handshake dan dua renewal aktual lulus; selisih
lease63,377/67,141detik. Password tidak berubah; inventaris lokal diperbarui.

Gateway utama kini memakai uplinketh0, forwarding IPv4, NAT dan policy default-deny.
Admin memuat profil publik schema2. Backup config dan tabel runtime dibuat;
nft--check lulus. Recovery terjadwal disiapkan untuk memulihkan tabel lama utuh.
Timer dibatalkan setelah SSH baru, readiness dan nolgrant terverifikasi; jalur
rollback gateway tersebut tidak dieksekusi dan bukan hasil drill pemulihan.
Tidak ada grant internet permanen yang diberikan melalui deployment ini.

## Integrasi HTTPS/WireGuard/nftables0.1.15 aktual

Identitas disposable10.8.0.3 menggunakan **paket terpasang**, tanpa source overlay.

- Bundle publik dan login tanpa peer; empat admission negatif lulus.
- Admission dan handshake nyata; default-deny, grant identitas/resource/TCP8082,
  penolakan akses LAN dan port lain lulus.
- TCP aktif tidak dapat bertukar data setelah grant aplikasi dihapus.
- Dua renewal otomatis HTTPS lulus; nilai aktual ada pada bukti privat.
- Gateway internet: satu route /32 sementara menuju1.1.1.1:443 melalui tunnel
  ditolak tanpa grant, berhasil dengan grant identitas eksplisit, lalu ditolak
  setelah grant dihapus. Target publik diperiksa terpisah dari server.
- Logout token lama tidak memutus lease token baru; logout aktif dan retry
  idempotent lulus.
- Revoke langsung CA membuat peer hilang6,828detik pada satu sampel, TCP aktif
  terblokir, dan admission ulang ditolak403.

Ini pengujian forwarding gateway dengan fixture Linux, **bukan bukti lockdown
Windows terbaru**. Route /32, demoHTTP dan grant uji sudah dibersihkan; byte policy
awal dipulihkan. Akun uji disabled, sertifikat revoked, bukti tetap disimpan.
Client utama kembali aktif dengan identitas baru. Pemeriksaan akhir empat peran
Linux active0.1.15 dan30/30HTTPhealth/readiness lulus; root/key CA tetap. Seluruh30serial revokasi awal tetap ada dalam CRL terbaru
yang memuat32serial setelah pencabutan primary lama dan identitas uji.

Dua koreksi harness integrasi: systemd sudah meng-GC unit transient setelah
cleanup sukses (dikonfirmasi tidak ada interface/marker/config); serta enum
alasan cleanup yang salah ditolak dashboard. Bagian tersisa dilanjutkan setelah
verifikasi, tidak mengulang enrollment atau menghapus bukti. Tidak ada patch
produk untuk menutupi kedua kesalahan pengamat ini.

## Windows native dengan gateway utama

Windows10 build19044 R2 selesai: **122 probe, tiga observasi lease (dua renewal),
PASS**. CA-only revoke menghapus peer dalam **10,056detik**, satu sampel. Sebelum
lockdown kedua target publik dapat dihubungi. Sesudah lockdown, sebelum import
sertifikat dan setelah login sebelum admission, Internet terblokir sementara
API bootstrap tetap terjangkau. Grant membuka Internet melalui tunnel; removal
menutupnya; regrant membuka kembali. Route /32 eksplisit ke target publik lain
melalui LAN tetap diblokir selama kebijakan aktif. Setelah revoke, admission
ulang ditolak403; disconnect tidak membuka lockdown. Recovery eksplisit membuka
kebijakan lama. Hash konfigurasi/identitas dan profil firewall awal pulih; route
uji, grant dan task dibersihkan, akun disabled dan sertifikat revoked. Pemeriksaan
ulang setelah reboot host3November juga lulus. Bukti: windows-managed-r2/10/.

Windows11 build26300 selesai pada3November: **98 probe, tiga observasi lease
(dua renewal), PASS** untuk fase yang sama. CA-only revoke menghapus peer dalam
**4,359detik**, satu sampel; admission ulang403. Recovery, hash konfigurasi dan
identitas legacy, profil firewall, serta ketidakhadiran direktori identitas
Program Files seperti sebelum uji terverifikasi. Akun disabled, sertifikat revoked,
grant dan task fixture dibersihkan. Bukti: windows-managed-r2/11/.

Pengujian ini memanggil API client terpasang0.1.15 secara langsung. Guard overlap
subnet launcher produksi tetap ada; fixture API tidak menguji launcher perangkat
fisik. Probe Internet adalah percobaan koneksi TCP baru. Pemutusan TCP aplikasi
internal yang sudah aktif dibuktikan pada integrasi Linux; koneksi TCP Internet
Windows yang tetap terbuka sepanjang revocation belum diuji pada tahap ini.

Percobaan Windows10 pertama gagal pada baseline publik sebelum lockdown;
server/host dapat terhubung, tetapi guest tidak. Percobaan berikutnya lulus
baseline. Timeout upstream dashboard juga sempat terjadi. Penyebab kedua insiden
belum terkonfirmasi; tidak ada perubahan firewall host/router dan tidak diklaim
sebagai bug yang sudah diperbaiki. Bukti gagal tetap disimpan.

Controller R2 Windows10 sempat terhenti karena PowerShell File.Replace memakai
backup null yang berubah menjadi path tidak valid. Harness memakai berkas backup
.previous, lalu melanjutkan fase tersisa tanpa enrollment ulang. Persiapan
Windows11 sempat mengasumsikan direktori identitas generik sudah ada; arsip awal
membuktikan folder itu memang tidak ada. Continuation mempertahankan kondisi awal
tersebut dan identitas legacy ProgramData. Keduanya koreksi harness, bukan patch
produk atau alasan menghapus bukti gagal.

## Pemulihan Ubuntu setelah reboot3November

Sesi karyawan kedaluwarsa tetap fail-closed. Service pemilik dihentikan, lock
client diambil, tidak ada tunnel/interface diverifikasi. Config/marker lama
hanya diarsipkan setelah timestamp sebelumboot dan key/address/endpoint cocok.
Login ulang memakai akun existing tanpa reset password, tidak langsung membuat
peer. Service kemudian berhasil handshake dan renewal otomatis; dua observasi
lease berselisih63,235detik. Hash identitas tidak berubah. Bukti privat:
client-reboot-20261103/done.json dan leases.json.

## Postflight akhir 3 November

Empat peran Linux aktif pada0.1.15, daemon/WireGuard aktif, integritas kedua DB
ok. Primary baru memiliki lease/peer/handshake tanpa izin Internet. Empat identitas
disposable telah revoked, akun disabled, tanpa lease/peer; grant dan route/demo uji
hilang. Policy resource identik byte dan policy Internet identik secara semantik
(format JSON berubah saat cleanup). HTTPS health/readiness **30/30 HTTP200**.
Hash root/key CA tetap dan seluruh **30 revokasi lama** ada dalam **35 revokasi**
CRL sekarang. Tidak memulihkan state CA atau menyimpulkan insiden historis fixed.
Bukti: final-postflight-20261103/; bukti2November tetap terpisah. Pemeriksaan ulang
kedua Windows memastikan file/firewall asli, ketiadaan task/tunnel/route uji dan
credential staging. Enam VM running; attacker off, tujuh VM tetap dipertahankan.

## Keterbatasan dan pekerjaan tersisa

1. **BELUM_TERUJI** koneksi TCP Internet persisten sepanjang revocation kedua
   Windows; hasil TCP aplikasi internal dan probe Internet baru dipisahkan.
2. **BELUM_TERUJI** PC fisik LAN/laptop Wi-Fi, sesuai pengguna belum tersedia;
   UAC/browser/MOTW/GPO interaktif, Windows kosong, dan fresh install prasyarat.
3. Launcher produksi menolak overlap subnet backend. VM Windows berada pada LAN
   backend; fixture API langsung berbeda dari alur launcher pada perangkat
   fisik192.168.50.0/24. EXE per-device schema2 end-to-end belum dibuktikan di sini.
4. Sampel kesehatan saat ini lulus; beban panjang/power loss fisik CA belum
   dibuktikan. Insiden503 historis tidak dinyatakan selesai hanya karena probe
   terbaru berhasil. Disk host sekitar1,5GiB bebas pada3November; perlu kapasitas
   tambahan sebelum uji panjang. Backup dan bukti lama tidak dihapus.
5. Gateway aktif tidak dengan sendirinya memblokir internet perangkat unmanaged.
   Profil tepercaya, enrollment, login, lockdown endpoint dan grant eksplisit
   tetap diperlukan. EXE umum hanya memasang prasyarat dan aplikasi.

Dokumen operasional utama tetap [manual tunggal](MODUL_PENGGUNAAN_VANGUARD.md).
Laporan ini menyimpan bukti, bukan tutorial kedua. Status publikasi ada di checkpoint.
