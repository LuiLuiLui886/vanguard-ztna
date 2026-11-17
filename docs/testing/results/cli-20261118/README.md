# Uji baru dengan screenshot CLI native — 18 November 2026 WIB

Pengguna memilih menjalankan uji baru, bukan menampilkan ulang log 17 November.
Run `cli-20261118-r01` memakai identitas baru dan sertifikat `102A`.
**Ketiga screenshot diambil langsung dari GNOME Terminal di desktop host.**
Terminal client menjalankan proses penerima secara langsung melalui SSH ber-PTY
pada VM-CLIENT; terminal operator mengirim permintaan HTTPS terautentikasi ke
VM-ADMIN. Tidak menggunakan halaman browser untuk merender output terminal.

[Figure 2 versi CLI](../../../proposal/figures/cli-20261118/figure-2-native-cli-20261118.png)
memuat transfer aktif, pencabutan, dan penolakan koneksi berikutnya.
[Manifest dan hash](../../../proposal/figures/cli-20261118/manifest.json)
merujuk pada tiga PNG asli di folder gambar yang sama. Hasil 17 November
[disimpan terpisah](../media-20261117/README.md); tidak ditimpa.

## Hasil aktual

| Pemeriksaan | Hasil |
| --- | --- |
| Registrasi + login sebelum admission | Tidak ada peer baru |
| Admission + renewal | Audit mencatat `all_six_checks_and_employee_passed` dua kali |
| Kontrol unduh berizin | 2.880.044 byte, SHA-256 cocok dengan sumber |
| Transfer aktif | HTTP 200; counter 8.192 → 40.960 → 73.728 byte sebelum trigger revoke |
| Pencabutan | Login admin dengan password/TOTP; HTTPS POST revoke; workflow `revoked`, serial `102A` |
| Transfer sesudah pencabutan | Timeout setelah 98.304 byte; tidak selesai mengunduh |
| Koneksi ulang aplikasi | `URLError`; tidak mendapatkan respons HTTP aplikasi |
| Admission ulang | Ditolak upstream HTTP 403; pembungkus client menampilkan status 502 |
| Peer server | Tidak ada setelah pencabutan |
| Cleanup | Akun uji nonaktif, logout karyawan terkonfirmasi, tunnel/listener berhenti, policy pulih byte-identik |
| Pelestarian CA/identitas | Root/private key CA dan identitas utama tidak berubah; index lama tetap; serial1029 dan102A ada di CRL |

Source workload tersedia di `media_server.py` dan `receiver_cli.py`. Berkas audio
sama dengan pilot sebelumnya: WAV mono PCM16, 8 kHz, sinus440Hz, 180detik.
SHA-256: `7bc918d719995617b6e282e3a189b34dc76fda0544eb30fcfb3c0d82752ffee1`.
Pengirim memakai potongan8.192byte dan jeda nominal0,25detik; kontrol unduh
mengirim tanpa jeda. Laju konfigurasi ini bukan hasil pengukuran throughput.
Grant eksplisit mengikat akun/identitas ke `10.8.0.1/TCP8082`. Semua pemeriksaan
perangkat dan sesi tetap aktif; private key dibuat di VM-CLIENT.

## Waktu dan metode screenshot

Run berlangsung **18 November 2026, 01:01:32–01:01:41 WIB**. Terminal menampilkan
UTC: **17 November 2026, 18:01:32–18:01:41 UTC**. Perbedaan tanggal berasal dari
zona waktu, bukan pemakaian ulang screenshot lama.

- Panel a ditangkap saat penerima masih berjalan, sebelum trigger pencabutan.
- Panel b adalah terminal operator pada host. Script melakukan login password +
  TOTP dan POST ke dashboard HTTPS dengan verifikasi root CA. HTTP302 diverifikasi
  lagi terhadap workflow admin dan ketiadaan peer; redirect sendiri bukan bukti
  pencabutan. Ini CLI instrumentasi uji, bukan fitur CLI admin baru pada produk.
- Panel c ditangkap dari jendela client yang sama setelah proses penerima selesai
  dan koneksi ulang gagal. `tty` menunjukkan PTY guest `/dev/pts/0`.

GNOME Terminal memakai XWayland pada desktop Wayland; `capture_window.py` membaca
pixel jendela native dengan GDK. Gambar komposit hanya menambahkan label serta
memotong batas/ruang kosong; perintah, output, timestamp, dan judul tetap asli.
Tidak mengetik ulang log ke terminal, tidak menggambar prompt, tidak memakai
HTML terminal atau image generation. Bash `--noprofile --norc` menghindari prompt
berisi username pada artefak publik. Credential tidak dicetak. Interpreter Python
operator memakai virtualenv yang dibuat17November untuk dependensi requests/
pyotp; nama folder `browser-venv` pada baris perintah tidak berarti browser
menjalankan capture ini.

Nilai `elapsed_seconds=6.762` merupakan **seluruh durasi transfer**, bukan waktu
pencabutan. Timer HTTP host2,055detik hanya mencakup permintaan–respons revoke.
Tidak mengurangkan timestamp antar-VM untuk mengklaim latensi penegakan. Timeout
baca4detik dan reconnect3detik membatasi deteksi; byte yang terhitung dapat
mencakup data yang sudah dibuffer. Tidak ada pengukuran paket terakhir di jaringan.

## Lingkungan, kegagalan, dan pemulihan

CA/server/admin/client Ubuntu dinyalakan dari keadaan mati. Attacker tetap mati;
Windows yang telah dipensiunkan tidak dibuat ulang. Hash modul terpasang sesuai
observasi sebelumnya: CA0.1.17, server/admin/client0.1.15; lihat `postflight.json`.
Host mempunyai RAM7,5GiB, sekitar6GiB tersedia sebelum boot dan disk39GiB bebas.
Tidak ada perubahan source layanan, aturan admission atau konfigurasi keamanan.

Pemeriksaan startup pertama: CA200, server200, admin503 dengan database `unknown`.
Backup quiescent CA/server/admin kemudian diverifikasi dan layanan dimulai kembali.
Pemeriksaan admin sebelum transfer menghasilkan200/ready. Kondisi503 awal tetap
disimpan; penyebabnya belum diisolasi. Audit identitas baru tidak mencatat
`peer_removed/crl_unavailable` sepanjang run ini. Ini tidak membuktikan gangguan
CRL pilot sebelumnya telah diperbaiki. Tidak ada retry transfer/revoke pada run
baru; persiapan capture terminal sempat menemui konflik nama bus pada wrapper
GNOME. Pemakaian binary client `.real` menyelesaikan peluncuran jendela uji tanpa
mengubah konfigurasi terminal pengguna.

Postflight: CA200/ready melalui VM-SERVER, server/admin200/ready, peer0. Probe
host langsung ke CA timeout karena firewall membatasi TCP8080 pada server/admin;
jangan melabelinya sebagai kegagalan readiness CA. Cleanup terkonfirmasi pada
`cleanup.json`; bukti integritas CA ada di `ca-integrity.json`. Akun uji dicatat
nonaktif pada inventaris kredensial lokal. Client utama tetap berhenti karena
sesi lamanya sudah kedaluwarsa sebelum eksperimen; tidak mereset kredensialnya.

Bukti mentah, backup, sesi sementara, dan arsip identitas tetap privat pada
`/home/lui/VanGuard-Privat/conference-evidence/cli-20261118-r01/`.
Backup tidak dipakai untuk memulihkan index, serial, CRL atau counter lama.

## Batas hasil dan pekerjaan tersisa

Ini tambahan satu run representatif dengan identitas baru. Dua pilot memakai
instrumentasi capture berbeda; belum seri terkontrol sepuluh run independen,
bukan rata-rata latensi dan bukan pembandingan OS. Matriks TabelI lengkap,
Windows native/fisik, LAN bypass, dan distribusi waktu **BELUM_TERUJI** pada tugas
ini. Tidak mengulang suite aplikasi karena source layanan tidak berubah.

Draft lokal Inggris/Indonesia menggunakan gambar baru; hasil lama dipertahankan
sebagai pengamatan terpisah. Google Docs belum sinkron karena konektor tidak
tersedia. Pagination enam halaman setelah gambar native belum dirender.
