# Keputusan implementasi dan batas operasional

Dokumen ini memperinci aturan dalam VANGUARD_CONTEXT.md dan AGENTS.md. Tidak mengganti
topologi atau mengubah implementasi kernel WireGuard.

Versi0.1.9 menambahkan perilaku pada [catatan hardening](HARDENING_0.1.9.md).
Status pengujian/deployment ada di checkpoint; source tidak otomatis berarti VM
sudah memakai versi tersebut.

## Admission

1. Root CA dipasang out-of-band dan dipakai untuk memverifikasi signature issuer langsung.
2. Waktu sertifikat perangkat dan Root CA diperiksa menggunakan waktu UTC.
3. CRL diambil melalui HTTPS setiap challenge, verify, dan siklus daemon. Signature,
   issuer, lastUpdate, nextUpdate, dan key usage Root CA diperiksa; tidak ada fallback CRL kedaluwarsa.
   Jika CRL dengan issuer/signature sah hanya mendahului waktu lokal <=1 detik,
   server menunggu sekali hingga batas lastUpdate, kemudian mengulang semua
   pemeriksaan menggunakan waktu aktual. CRL belum berlaku tidak pernah diterima;
   selisih lebih besar, jam mundur, expiry, atau kegagalan validasi tetap ditolak.
4. Serial perangkat dicocokkan dengan daftar pencabutan.
5. Challenge acak 256 bit, TTL 60 detik, hanya bisa dikonsumsi sekali. SQLite dan flock
   menserialkan penggunaan lintas thread/proses; kegagalan proof menghabiskan challenge tersebut.
   Expiry challenge diperiksa lagi sesudah fetch CRL/proof, sebelum penambahan peer.
6. SHA-256 fingerprint sertifikat, device ID/CN, public key WireGuard, dan tunnel IP
   dicocokkan dengan registry. Pesan signature mengikat semua identitas dan nonce.

Setelah langkah tersebut, satu-satunya jalur untuk menambahkan peer di server adalah
`Admission.verify()`. Registrasi hanya memvalidasi dan menyimpan binding. Server mengalokasikan
allowed-ips `/32` dari registry, bukan dari nilai yang dikirim saat verify.

## Lifecycle akses

Mulai 0.1.3 sesi akun karyawan wajib dan terikat ke device melalui registry akun.
Password disimpan sebagai hash scrypt dan token sesi hanya sebagai SHA-256 pada
server. Sesi delapan jam dikirim pada challenge/verify lewat HTTPS; kedua request
harus memakai sesi yang sama. Password/sesi karyawan tidak memberi akses management.
Penonaktifan akun menghapus sesi dan peer; daemon juga memeriksa validitas sesi.
Perangkat lama tanpa binding akun gagal admission. Metadata pemilik/departemen
hanya deskriptif, bukan kebijakan akses atau attestation hardware.

Lease maksimal 300 detik. Daemon memeriksa ulang setiap 5 detik **setelah** siklus sebelumnya
selesai. Peer expired/revoked/disabled/unknown dihapus. Kegagalan fetch/validasi CRL membatalkan
lease dan menghapus semua peer. Restart API/daemon mengosongkan peer dan lease agar memerlukan
admission baru. Reconciler tidak menghidupkan kembali peer yang hilang tanpa admission.

Pencabutan tidak instan jika hanya dilakukan pada CA: ada waktu polling ditambah latency
request dan operasi WireGuard. Client HTTP timeout connect 3 detik/read 10 detik; perintah
lokal timeout 30 detik. Dashboard mencoba disable peer dahulu, lalu tetap mencoba revoke CA
jika server gagal dihubungi. Kegagalan parsial ditampilkan sebagai `revoking` dan bisa di-retry.
Penanganan batas detik CRL dapat menambah waktu tunggu maksimal satu detik per fetch.

Unit systemd daemon menurunkan wg0 saat daemon berhenti; admission API bergantung pada
daemon dan wg0. Sejak0.1.9 daemon memakai watchdog 90 detik dengan notifikasi hanya
setelah reconcile selesai, sehingga hang tanpa heartbeat ditangani supervisor.
Matriks VM20 Oktober membuktikan watchdog/stop hook unit produksi serta
penghentian akses pada Linux/Windows; batas buktinya ada di checkpoint.
API mati saja tetap dibatasi daemon dan lease. Tidak ada jaminan real-time ketika
supervisor/host gagal atau perlindungan dari administrator root yang menguasai server.

WireGuard `SaveConfig` tidak digunakan: peer runtime tidak dipersistenkan ke wg0.conf.
Server memiliki interface tanpa blok `[Peer]` saat boot. Perubahan manual oleh root berada
di luar trust model; daemon menghapus public key asing tetapi tidak mendeteksi perubahan
allowed-ips manual pada peer yang masih memiliki lease.

## Identitas dan transport

Private key X.509 dan WireGuard dihasilkan independen pada client. Hanya CSR dan public key
yang masuk request.json. HTTPS service certificates memiliki serverAuth dan SAN IP service;
admission menolaknya sebagai identitas perangkat. CA root key hanya berada di VM-CA.

CA menggunakan OpenSSL `ca`, index.txt, serial, crlnumber, serta lock bersama untuk issue,
revoke, dan CRL. CA API memerlukan token berbeda dari token registry server. Token acak
minimal 32 karakter, environment file mode 0600, tanpa default fallback.
CSR sama menggunakan cache hasil. Versi0.1.9 mengatasi interupsi antara signing
dan cache dengan staging, manifest commit durable, dan roll-forward seluruh state.
Operasi berikutnya menyelesaikan commit sebelum mutasi baru. Staging tanpa commit
dipertahankan sebagai bukti; state rusak tanpa manifest ditolak. Tidak ada restore
index/CRL lama atau tebakan counter. SIGKILL sudah diuji pada CA sementara;
rollout CA utama20 Oktober sudah lolos invariant/salinan terisolasi dan backup;
power-loss disk tetap memerlukan bukti terpisah. Lihat
[matriks live](VALIDASI_ROLLOUT_2026-10-20.md).

TLS client memverifikasi chain dan IP terhadap Root CA. Implementasi Requests tidak menerapkan
CRL untuk **sertifikat HTTPS service**; revoke admission berlaku pada sertifikat perangkat.
Jika TLS service key bocor, hentikan service, ganti key/cert, dan lakukan rotasi trust bila
diperlukan. Renewal sertifikat service (365 hari) dilakukan melalui CLI CA, bukan otomatis.

Kunci CA disimpan tanpa passphrase agar service bisa menerbitkan CRL tanpa operator,
dilindungi permission OS dan pemisahan VM. Backup CA harus mencakup private key, index,
serial, crlnumber, issued, dan newcerts secara konsisten saat service dihentikan.

## Dashboard

Password di-hash oleh Werkzeug (scrypt), TOTP 30 detik tanpa menerima ulang timestep,
lockout setelah 5 kegagalan per username/IP selama 5 menit. Sesi 30 menit dicatat server-side,
logout menghapus token sesi. Cookie Secure, HttpOnly, SameSite=Strict, semua POST dilindungi
CSRF. Secret TOTP harus tersedia untuk verifikasi, sehingga disimpan di SQLite yang hanya
dapat dibaca akun service. Tidak ada password atau TOTP seed bawaan.

Workflow CA → registry bukan transaksi terdistribusi. Dashboard menyimpan status
pending_issue/pending_registry dan menyediakan retry. Sertifikat yang baru terbit tetapi
belum terdaftar tidak memberikan akses. Audit lokal belum memiliki pengiriman eksternal,
rotasi, atau perlindungan terhadap modifikasi oleh root.

## Referensi implementasi

- [OpenSSL CA](https://docs.openssl.org/3.0/man1/openssl-ca/): signing, index, revoke, CRL.
- [RFC 5280 §5.1.2.4–5](https://www.rfc-editor.org/rfc/rfc5280.html#section-5.1.2.4):
  arti thisUpdate dan nextUpdate; timestamp issuer tidak diubah oleh validator.
- [cryptography X.509](https://cryptography.io/en/latest/x509/reference/): verifikasi signature, waktu UTC, dan CRL.
- [Flask security](https://flask.palletsprojects.com/en/stable/web-security/): CSRF, cookie dan header keamanan.

Ini merupakan implementasi lab untuk dievaluasi, bukan sistem yang sudah mendapatkan audit
keamanan independen atau pembuktian deployment produksi.


## Publikasi CA0.1.11 — terpasang21 Oktober

Optimasi mempertahankan file identik dan menyinkronkan setiap inode. File berubah
memakai fsync lalu rename. Seluruh direktori parent disinkronkan sebelum manifest
commit dihapus; manifest penuh dan work durable tetap tersedia selama publikasi.
Kegagalan barrier mempertahankan keputusan commit untuk roll-forward. Ini bukan
jaminan transaksi banyak file hanya dari atomic rename. Tes SIGKILL/fsync failure
menggunakan CA sementara; power-loss disk/host tetap BELUM_TERUJI. Paket0.1.11 terpasang pada CA/server/admin dengan backup dan invariant
terverifikasi; client/attacker/Windows tetap0.1.9. Lihat checkpoint.


## Kapasitas layanan CA

Unit CA memakai satu worker dan delapan thread setelah perbaikan21 Oktober.
Empat thread sebelumnya dapat penuh oleh fan-out readiness dan fetch CRL daemon,
sehingga TLS handshake request berikutnya habis budget koneksi0,5detik. Tes
Gunicorn/TLS nyata mereproduksinya sebelum patch. Penambahan kapasitas tidak
mengubah lock mutasi CA, verifikasi TLS, deadline6detik atau penolakan ketika
pemeriksaan gagal. Layanan tetap dapat not_ready saat overload; jangan mengubahnya
menjadi200 atau menggunakan CRL lama. Bukti dan pemulihan unit tersedia pada
[catatan kapasitas](CA_SERVICE_CAPACITY.md).

## Persiapan endpoint0.1.12, belum rollout

Profil publik harus diterima melalui kanal operator tepercaya dengan fingerprint
Root CA dan public key WireGuard server yang diperiksa terpisah. Root dalam ZIP
bukan trust anchor baru. Importer memeriksa signature/validity/EKU/key/request,
menolak anggota ZIP/path tambahan dan binding berbeda; hanya device.crt baru yang
dipublikasikan, tidak mengganti key/root/profile/sesi. Idempotent untuk PEM identik.
CRL/akun/lease aktual tetap diperiksa admission server; import tidak memberi peer.

Installer native kandidat tidak mengunduh, membuat key, membuka jaringan atau
mengubah trust Windows/global PATH. Paket, runtime dan sumber profil harus pada
path admin-only tanpa reparse point; data identitas dipisahkan. Hash manifest
harus berasal dari kanal tepercaya, bukan dihitung sendiri dari unduhan lalu
dianggap autentik. Kandidat unsigned dan native ACL/UAC belum diuji; jangan bypass
kebijakan eksekusi. Runtime Python3.13x64/WireGuard resmi terverifikasi harus sudah
tersedia. Launcher memeriksa konflik subnet/route sebelum admission; snapshot
bukan proof firewall/UDP. Pemulihan service yang belum terkonfirmasi tetap manual.

`CA.sign_tls` tambahan DNS/IP memerlukan allowlist operator eksplisit. Sanitasi
host mencegah injeksi ekstensi; default tetap alamat layanan lab. Perubahan ini
diuji pada CA sementara, bukan penerbitan/rotasi sertifikat utama. Riwayat CA dan
revocation tidak dipulihkan saat rollback paket. Baca [rencana pilot](ENDPOINT_WINDOWS_PILOT.md).
