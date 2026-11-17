# Figure 2 — uji media VM, 17 November 2026

Status: **satu run representatif selesai**, bukan matriks evaluasi lengkap atau
uji endpoint fisik. Identitas run: `media-20261117-r01`, sertifikat serial `1029`.
Screenshot dan log adalah hasil observasi aktual, bukan gambar generatif.

## Hasil yang dibuktikan

| Pemeriksaan | Hasil aktual |
| --- | --- |
| Registrasi dan login, sebelum admission | Tidak ada peer uji |
| Admission perangkat dan sesi karyawan | Audit server: `all_six_checks_and_employee_passed` |
| Kontrol unduh berizin | 2.880.044 byte; SHA-256 sumber dan penerima cocok |
| Transfer yang sedang berlangsung | HTTP 200, counter 8.192 → 40.960 → 73.728 → 106.496 byte sebelum tindakan admin |
| Pencabutan melalui dashboard | Server menonaktifkan perangkat; CA mencabut serial 1029; workflow `revoked` |
| Akhir transfer | 122.880 byte, `TimeoutError`; tidak ada event `completed` |
| Koneksi ulang aplikasi | `URLError`, tidak memperoleh respons HTTP aplikasi |
| Admission ulang | Ditolak upstream HTTP 403; pembungkus client melaporkan status 502 |
| Peer setelah pencabutan | Tidak ada |
| Cleanup | Logout karyawan terkonfirmasi, akun uji nonaktif, tunnel dan listener media berhenti, policy pulih byte-identik |
| Identitas/histori | Hash identitas utama dan kunci/root CA tetap; semua entri index lama tetap; serial 1029 ada pada CRL |

Kontrol hash: `7bc918d719995617b6e282e3a189b34dc76fda0544eb30fcfb3c0d82752ffee1`.
Berkas sintetis WAV: mono, 8.000 Hz, PCM 16-bit, sinus 440 Hz, durasi 180 detik.
Transfer uji mengirim 8.192 byte tiap jeda nominal 0,25 detik; ini konfigurasi
pengirim, bukan hasil pengukuran throughput. Kontrol positif mengirim tanpa jeda.
Resource hanya `10.8.0.1/TCP8082`, melalui grant identitas/akun eksplisit.
Kunci identitas dan WireGuard dibuat di VM-CLIENT; tidak ada bypass admission.

## Waktu dan batas interpretasi

Penerima mencatat HTTP 200 pada 07:39:08 UTC; server mencatat disable pada
07:39:11 UTC; dashboard mencatat pencabutan selesai 14:39:12 WIB.
Penerima timeout pada 07:39:15 UTC dan koneksi ulang gagal pada 07:39:18 UTC.
Urutan diperkuat audit server: admission diterima lalu disable, tanpa event
`peer_removed/crl_unavailable` di antara kedua event tersebut pada run terpilih.

Jangan mengurangkan timestamp antar-VM untuk menghitung latensi presisi.
Durasi 7,5166 detik pada log adalah **durasi total percobaan transfer**,
bukan waktu pencabutan. Timer host 1,0620 detik hanya mencakup permintaan
pencabutan sampai respons navigasi browser; bukan waktu berhentinya data.
Timeout baca 4 detik dan koneksi ulang 3 detik membatasi resolusi deteksi.
122.880 byte termasuk byte yang mungkin sudah berada di buffer. Tidak ada
pengukuran packet-level atas saat terakhir paket berhasil lewat.

## Asal screenshot

[Figure 2 lengkap](../../../proposal/figures/figure-2-media-revocation-20261117.png)
terdiri dari tiga tangkapan Chromium headless:

1. Panel a: isi log JSONL yang dibaca langsung dari VM-CLIENT saat transfer aktif.
2. Panel b: bagian sertifikat pada halaman riwayat dashboard asli. Diambil setelah
   run, setelah memperbaiki proses capture yang gagal pada redirect; bukan
   tangkapan saat tombol ditekan.
3. Panel c: isi log penerima sesudah timeout dan upaya koneksi ulang.

Panel client adalah tampilan instrumentasi eksperimen melalui browser,
bukan terminal native atau GUI aplikasi VanGuard. Transport capture dashboard
menggunakan `requests.Session` dengan verifikasi TLS terhadap root CA existing;
Playwright menerima byte respons nyata. Tidak memakai `ignore_https_errors`,
tidak mengubah HTML dashboard, dan tidak merekonstruksi status produk.
Panel client membungkus baris JSON asli agar terbaca. Komposisi menambahkan
label dan memotong ruang kosong/teks penjelasan di bawah bukti. Nilai tidak diubah.
[Manifest](../../../proposal/figures/figure-2-manifest.json) mencatat hash dan crop;
ketiga PNG sumber juga tersedia di folder gambar. Tidak ada username, password,
OTP, token atau private key pada gambar/log publik. Log audit lengkap dan arsip
identitas berada di inventaris bukti privat lokal, tidak di Git.

## Lingkungan dan percobaan gagal

Empat VM Ubuntu aktif: CA, SERVER, ADMIN, CLIENT; ATTACKER tetap mati. Lima node
Ubuntu dipertahankan, Windows VM tetap dipensiunkan. Versi terpasang: CA 0.1.17;
server/admin/client 0.1.15. Alokasi masing-masing 524/768/524/524 MiB dan satu vCPU.
Host mempunyai RAM 7,5 GiB, menggunakan swap, dan mengalami tekanan I/O saat
percobaan. Hash modul terpasang dan hasil readiness disimpan pada `postflight.json`.

Kegagalan sebelum run terpilih dipertahankan:

- Pembuatan akun uji timeout tetapi commit berhasil; diperiksa, tidak diduplikasi.
- Harness media awal salah memanggil atribut `st_size` sebagai fungsi. Diperbaiki
  sebelum kontrol hash lulus; ini bug harness, bukan bukti bug admission.
- Fetch CRL beberapa kali gagal; daemon mencabut peer secara fail-closed. Satu
  percobaan receiver awal menerima nol byte. Client akhirnya berhenti karena
  kegagalan upstream dan dimulai ulang dengan identitas yang sama.
- Capture pertama tidak menemukan peer. Capture berikutnya membaca log terlalu
  dini saat host/SSH tersendat. Capture run terpilih berhasil mengambil panel a,
  tetapi redirect browser setelah pencabutan gagal; status revoked diperiksa
  dari dashboard dan panel b/c diambil setelahnya.
- Stop unit receiver saat cleanup melaporkan unit sudah tidak dimuat; status
  inactive dan ketiadaan tunnel diverifikasi, lalu cleanup dilanjutkan.

Ini satu identitas dengan retry, **bukan beberapa run independen**. Penyebab
fetch CRL/renewal gagal belum diisolasi; tekanan host merupakan observasi, bukan
kesimpulan sebab. CA readiness dari host tidak dapat dinilai karena firewall CA
hanya mengizinkan TCP8080 dari server/admin. Probe melalui VM-SERVER menghasilkan
HTTP 200/ready. Server dan admin juga HTTP 200/ready pada postflight. Keberhasilan
postflight tidak menghapus kegagalan selama eksperimen.

## Artefak dan pengulangan

`media_server.py` dan `receiver.py` adalah source workload yang benar-benar
berjalan. Receiver memakai path run asli. Untuk uji baru, alokasikan identitas
baru dan direktori baru; jangan menimpa log atau menggunakan kembali sertifikat
yang telah dicabut. Enrollment, autentikasi, grant dan tunnel harus melalui
alur resmi. Script workload ini bukan installer dan tidak mengatur admission.

Log penerima, kontrol hash, hasil readmission, cleanup, dan integritas CA berada
pada folder ini. Bukti mentah/backup quiescent tetap di
`/home/lui/VanGuard-Privat/conference-evidence/media-20261117-r01/` (lokal privat).
Tidak pernah memulihkan index/CRL/counter CA dari backup.

BELUM_TERUJI pada tugas ini: matriks Tabel I lengkap, sepuluh run independen,
Windows native/endpoint fisik, direct-LAN bypass media, distribusi waktu,
beban produksi, dan perbandingan dengan kontrol tanpa VanGuard. Tidak mengulang
suite unit aplikasi karena tidak ada perubahan source layanan.

Google Docs belum diperbarui: sesi ini tidak memiliki konektor Google Drive/Docs
atau document session tersambung. Figure dan revisi draft disiapkan lokal/Git;
jangan menyatakan tab Google Docs telah sinkron. Layout enam halaman harus
kembali diperiksa setelah gambar dimasukkan.
