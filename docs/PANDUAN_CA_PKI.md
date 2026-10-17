# Panduan rinci CA, sertifikat dan CRL VanGuard

Edisi 17 Oktober 2026 · Pendamping bab 5.3 [modul lengkap](MODUL_PENGGUNAAN_VANGUARD.md)

Panduan ini mengikuti source VanGuard 0.1.8, terutama `vanguard/ca.py`,
`vanguard/pki.py`, `vanguard/client.py` dan workflow dashboard. Setiap blok
menyebutkan tempat menjalankannya. **CA lab yang ada sudah terpasang**;
gunakan bagian pemeriksaan untuk pemeliharaan. Langkah init/generate/signing
di bawah hanya untuk pemasangan baru atau pekerjaan teknisi yang direncanakan.

## 1. CA itu apa dan apa hubungannya dengan VPN?

Certificate Authority (CA) adalah penerbit sertifikat. Sertifikat menyatakan
identitas pemilik public key dan ditandatangani CA agar pihak lain dapat
memverifikasi asalnya. Private key tetap dikuasai pemiliknya.

Contoh: client Windows membuat key P-256 dan meminta sertifikat untuk
`vm-client-windows`. CA menandatangani sertifikat menggunakan root private key.
Saat admission, server memverifikasi sertifikat tersebut menggunakan root
certificate, kemudian meminta proof yang hanya dapat dibuat pemilik key client.
Memiliki salinan sertifikat publik saja tidak cukup untuk membuat proof itu.

| Istilah | Makna praktis | Apakah rahasia? |
|---|---|---|
| Private key | Kunci untuk menandatangani atau membuktikan kepemilikan | Ya |
| Public key | Pasangan publik yang dipakai untuk verifikasi | Tidak |
| CSR | Certificate Signing Request; permintaan berisi identitas/public key dan signature pemohon | Bukan key rahasia; tetap dikelola operator |
| Certificate | Identitas/public key/masa berlaku/signature penerbit | Publik, dapat berisi metadata perangkat |
| Root CA | Trust anchor yang ditetapkan operator | Sertifikat publik; key root rahasia |
| Fingerprint SHA256 | Ringkasan untuk membandingkan sertifikat yang sama | Publik |
| Serial sertifikat | Nomor unik sertifikat pada CA | Publik; berbeda dari fingerprint |
| CRL | Certificate Revocation List, daftar serial tercabut bertanda tangan | Publik; harus valid dan terkini |
| SAN | Subject Alternative Name, misalnya IP endpoint HTTPS | Bagian publik sertifikat |
| EKU | Extended Key Usage, membatasi tujuan sertifikat | serverAuth atau clientAuth |

VanGuard memiliki dua kelompok sertifikat: HTTPS untuk identitas API/dashboard,
dan sertifikat perangkat untuk admission. Proof perangkat dikirim pada API
aplikasi; jangan menganggap mekanisme ini otomatis berupa mutual TLS pada setiap
koneksi. WireGuard tetap memakai keypair terpisah yang diikat pada registry.

## 2. Struktur file dan parameter CA yang sebenarnya

Pada VM-CA, direktori default `/var/lib/vanguard/ca` berisi:

```text
ca/
├── openssl.cnf          konfigurasi CA OpenSSL
├── private/root.key    root private key; jangan disalin ke client
├── root.crt            root certificate publik
├── index.txt           database status sertifikat OpenSSL
├── index.txt.attr      pengaturan database
├── serial              counter nomor sertifikat berikutnya
├── crlnumber           counter nomor CRL berikutnya
├── crl.pem             CRL yang sudah ditandatangani
├── newcerts/           arsip sertifikat menurut serial
├── issued/             cache issuance perangkat menurut hash CSR; muncul saat issuance
├── requests/           staging CSR/sertifikat HTTPS yang disiapkan operator
└── ca.lock             lock operasi perubahan CA
```

OpenSSL dapat membuat berkas `.old` saat memperbarui database/counter.
Jangan menghapus atau mengganti file state secara acak untuk mengatasi error.

| Jenis | Parameter implementasi |
|---|---|
| Root | RSA 3072, signature SHA256, CN VanGuard Root CA,3650 hari |
| Root extensions | CA:true, pathlen:0; keyCertSign dan cRLSign |
| HTTPS layanan | serverAuth, CA:false, SAN IP .10/.20/.40;365 hari |
| Key HTTPS pada prosedur instalasi | RSA 3072 dibuat pada guest layanan itu sendiri |
| Perangkat | P-256, digitalSignature, clientAuth, CA:false;30 hari |
| CRL | Masa berlaku1 jam; dibuat baru pada setiap fetch API |
| Key WireGuard client | X25519 independen dari key P-256 perangkat |

Angka masa berlaku adalah konfigurasi penerbitan source ini, bukan masa berlaku
yang tersisa pada lab Anda. Periksa `notBefore/notAfter` sertifikat yang aktual.
Root pathlen:0 berarti tidak ada rantai intermediate CA dalam desain ini.
Counter diawali teks heksadesimal 1000 pada init; pembuatan CRL/issuance akan
mengubah counter. Jangan menuntut nilai awal tetap sama pada CA yang sudah berjalan.

## 3. Persiapan sebelum generate CA

**VM-CA (.10), melalui console atau SSH terverifikasi:**

```bash
hostname
ip -4 address
timedatectl status
openssl version
id vanguard
sudo ls -la /var/lib/vanguard/ca
```

Pastikan Ubuntu 22.04, IP 192.168.100.10, jam benar, OpenSSL dan paket VanGuard
terpasang melalui `sudo bash deploy/install.sh ca` dari root source.
Installer membuat akun service `vanguard`, virtualenv dan direktori state.

Jika CA sudah memiliki konfigurasi/key/index, berhenti dari alur generate dan
lanjut ke pemeriksaan. Init menolak overwrite jika openssl.cnf sudah ada;
operator tetap harus memeriksa sisa instalasi parsial jika init dahulu gagal.
Jangan menghapus openssl.cnf hanya supaya init dapat dijalankan ulang.

Sebelum setiap perubahan, catat intent, guest sasaran dan lokasi backup pada
jurnal pekerjaan tanpa nilai secret. Untuk lab saat ini, gunakan direktori
inventaris privat host yang disebut pada modul utama.

## 4. Generate root CA pada VM baru

**VM-CA baru saja:**

```bash
sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca init
```

Arti perintah: `sudo -u vanguard` menggunakan pemilik state CA, executable
berasal dari virtualenv aplikasi, dan `init` menyiapkan CA lengkap.
Target keluaran: `CA initialized: /var/lib/vanguard/ca/root.crt`.

Di dalam init, aplikasi menyiapkan konfigurasi/database/counter, membuat key
root RSA 3072 dan sertifikat root self-signed, mengatur key 0600, lalu menerbitkan
CRL awal. Pengaturan OpenSSL penting yang digunakan:

| Opsi internal | Arti |
|---|---|
| req -new -x509 | Membuat sertifikat root self-signed |
| -newkey rsa:3072 | Membuat pasangan key root RSA 3072 |
| -nodes | Key tidak dienkripsi dengan passphrase dalam implementasi ini |
| -days 3650 -sha256 | Validitas dan algoritma signature sertifikat root |
| CA:true,pathlen:0 | Root berwenang sebagai CA tanpa intermediate |
| keyCertSign,cRLSign | Root dapat menandatangani sertifikat dan CRL |

Tabel menjelaskan operasi aplikasi; **jangan menjalankan salinan perintah
generate root generik secara terpisah pada direktori produksi**. Itu dapat
membuat key/root berbeda tanpa memperbarui state CA secara konsisten.
Key tanpa passphrase memudahkan layanan noninteraktif, sehingga akses filesystem,
VM dan backup harus dibatasi. Modul ini tidak mengklaim root disimpan dalam HSM.

Tempatkan root publik pada path trust standar:

```bash
sudo install -m 0644 /var/lib/vanguard/ca/root.crt /etc/vanguard/root.crt
```

Perintah ini menyalin **sertifikat publik**, bukan root.key.

## 5. Verifikasi root sebelum dipercaya

**VM-CA:**

```bash
openssl x509 -in /etc/vanguard/root.crt -noout -subject -issuer -serial -dates
openssl x509 -in /etc/vanguard/root.crt -noout -fingerprint -sha256
openssl x509 -in /etc/vanguard/root.crt -noout -ext basicConstraints,keyUsage
openssl verify -check_ss_sig -CAfile /etc/vanguard/root.crt /etc/vanguard/root.crt
sudo stat -c '%a %U:%G %n' /var/lib/vanguard/ca /var/lib/vanguard/ca/private/root.key
```

Harapkan subject/issuer VanGuard Root CA, tanggal masuk akal, CA:TRUE/pathlen:0,
Certificate Sign dan CRL Sign, hasil `OK`, direktori 0700 serta key 0600.
Pada setup standar, keduanya dimiliki akun service `vanguard`.
Tanggal keluaran OpenSSL biasanya GMT/UTC; dashboard dapat menampilkan WIB.

Pemeriksaan key tanpa mencetak isi key, bila diperlukan oleh teknisi:

```bash
sudo -u vanguard openssl pkey \
  -in /var/lib/vanguard/ca/private/root.key -check -noout
```

Target `Key is valid`. Jangan menambahkan `-text` atau mengeluarkan key PEM ke
log. Self-signature OK hanya membuktikan konsistensi root yang diperiksa;
untuk mempercayai asalnya, cocokkan fingerprint terhadap console CA/jalur
operator yang sudah dipercaya, bukan dari berkas yang sama tanpa pembanding.

## 6. Distribusikan root publik melalui HOST

Contoh ini menggunakan konfigurasi SSH lab. Pada instalasi lain, siapkan
konfigurasi yang setara dengan fingerprint host key yang telah diverifikasi.

**HOST, satu sesi terminal:**

```bash
umask 077
ca_stage=$(mktemp -d /tmp/vanguard-ca-public.XXXXXX)
scp -F ~/.ssh/vanguard_lab_config \
  192.168.100.10:/etc/vanguard/root.crt "$ca_stage/root.crt"
openssl x509 -in "$ca_stage/root.crt" -noout -fingerprint -sha256
```

Cocokkan fingerprint dengan hasil bab 5 sebelum meneruskan. `$ca_stage` hanya
menyimpan sertifikat/CSR publik, dan nilainya berlaku pada terminal ini.

Contoh pemasangan trust untuk **VM-SERVER baru** dari HOST:

```bash
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.20 \
  'sudo test ! -e /etc/vanguard/root.crt && sudo tee /etc/vanguard/root.crt >/dev/null && sudo chmod 0644 /etc/vanguard/root.crt' \
  < "$ca_stage/root.crt"
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.20 \
  'openssl x509 -in /etc/vanguard/root.crt -noout -fingerprint -sha256'
```

Ulangi untuk .30, .40, .50 dengan IP sasaran yang benar. Jika root.crt tujuan sudah
ada, guard menolak overwrite; bandingkan fingerprint dan gunakan salinan yang
sama jika cocok. Ketidakcocokan trust adalah masalah yang perlu diperiksa,
bukan alasan mengganti root secara otomatis.

Windows menerima root.crt di `C:\ProgramData\VanGuard\client\root.crt` melalui
transfer tepercaya dan PowerShell Administrator. Browser admin mengimpor root
publik sebagai Authorities/CA untuk HTTPS. Semua salinan harus berasal dari
root yang sama. Jangan pernah mengirim private/root.key ke Windows atau browser.

## 7. Generate key dan CSR HTTPS pada setiap layanan

HTTPS membutuhkan key milik layanan, bukan root private key. Lakukan pada
**masing-masing VM-CA, VM-SERVER dan VM-ADMIN yang baru**:

```bash
sudo ls -l /etc/vanguard
```

Pastikan tls.key/tls.csr belum ada. Jika sudah ada, periksa atau rencanakan
penggantian dengan backup; jangan menimpanya dengan perintah berikut.

```bash
sudo openssl req -new -newkey rsa:3072 -nodes \
  -keyout /etc/vanguard/tls.key -out /etc/vanguard/tls.csr \
  -subj '/CN=VanGuard Service'
sudo chown root:vanguard /etc/vanguard/tls.key
sudo chmod 0640 /etc/vanguard/tls.key
sudo chmod 0644 /etc/vanguard/tls.csr
openssl req -in /etc/vanguard/tls.csr -noout -verify -subject
```

`-keyout` adalah file rahasia; `-out` adalah CSR yang boleh dikirim ke CA.
`-nodes` membuat key layanan tanpa passphrase untuk service noninteraktif.
Root:vanguard 0640 memungkinkan service membaca key. CSR harus menunjukkan
self-signature verify OK. Nama CN contoh boleh sama, tetapi setiap guest
membuat key sendiri dan memperoleh SAN IP berbeda saat signing.

## 8. Contoh lengkap: tanda tangani HTTPS SERVER lewat CA

Contoh berikut melanjutkan variabel `$ca_stage` dari bab 6, dan mengikuti
jalur HOST → guest; tidak mengharuskan SSH guest ke guest.

**HOST:**

```bash
scp -F ~/.ssh/vanguard_lab_config \
  192.168.100.20:/etc/vanguard/tls.csr "$ca_stage/server.csr"
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.10 \
  'sudo install -d -m 0700 -o vanguard -g vanguard /var/lib/vanguard/ca/requests'
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.10 \
  'sudo test ! -e /var/lib/vanguard/ca/requests/server.csr && sudo tee /var/lib/vanguard/ca/requests/server.csr >/dev/null && sudo chown vanguard:vanguard /var/lib/vanguard/ca/requests/server.csr && sudo chmod 0600 /var/lib/vanguard/ca/requests/server.csr' \
  < "$ca_stage/server.csr"
```

Jika CSR staging sudah ada, periksa permintaan sebelumnya; jangan menganggap
gagal transfer berarti belum pernah ditandatangani.

**VM-CA:**

```bash
sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca sign-tls \
  --csr /var/lib/vanguard/ca/requests/server.csr \
  --ip 192.168.100.20 \
  --out /var/lib/vanguard/ca/requests/server.crt
```

`--csr` adalah permintaan publik milik SERVER, `--ip` menjadi SAN IP sertifikat,
dan `--out` adalah hasil publik. Source menolak output yang sudah ada dan
hanya menerima IP layanan .10, .20, .40. Target keluaran `TLS certificate signed`.
Sertifikat diberi CA:false, serverAuth, digitalSignature/keyEncipherment dan365 hari.

**HOST**, ambil hasil dan pasang pada SERVER baru:

```bash
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.10 \
  'sudo cat /var/lib/vanguard/ca/requests/server.crt' > "$ca_stage/server.crt"
openssl verify -purpose sslserver -verify_ip 192.168.100.20 \
  -CAfile "$ca_stage/root.crt" "$ca_stage/server.crt"
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.20 \
  'sudo test ! -e /etc/vanguard/tls.crt && sudo tee /etc/vanguard/tls.crt >/dev/null && sudo chmod 0644 /etc/vanguard/tls.crt' \
  < "$ca_stage/server.crt"
```

Ulangi alur tersebut untuk layanan lain dengan pemetaan berikut:

| Guest pemilik CSR | Nama staging CA | IP pada sign-tls | Tujuan sertifikat |
|---|---|---|---|
| VM-CA | ca.csr → ca.crt | 192.168.100.10 | /etc/vanguard/tls.crt di CA |
| VM-SERVER | server.csr → server.crt | 192.168.100.20 | /etc/vanguard/tls.crt di SERVER |
| VM-ADMIN | admin.csr → admin.crt | 192.168.100.40 | /etc/vanguard/tls.crt di ADMIN |

Root CA dan HTTPS CA berbeda: `root.crt` adalah trust anchor, sedangkan
`/etc/vanguard/tls.crt` pada VM-CA membuktikan endpoint HTTPS .10. Private key
HTTPS tetap di guest yang membuat CSR; root key tetap dalam direktori CA.

## 9. Verifikasi sertifikat HTTPS dan jalankan layanan

**VM-SERVER**, setelah hasil signing dipasang:

```bash
openssl x509 -in /etc/vanguard/tls.crt -noout -subject -issuer -dates
openssl x509 -in /etc/vanguard/tls.crt -noout -ext subjectAltName,extendedKeyUsage
openssl verify -purpose sslserver -verify_ip 192.168.100.20 \
  -CAfile /etc/vanguard/root.crt /etc/vanguard/tls.crt
```

Target SAN .20, serverAuth dan OK. Gunakan IP yang sesuai saat menguji CA/ADMIN.
Untuk membuktikan key dan sertifikat berpasangan tanpa menampilkan key, di guest
yang sama jalankan dua pipeline berikut dengan `pipefail`; hash harus sama:

```bash
set -o pipefail
sudo openssl pkey -in /etc/vanguard/tls.key -pubout -outform DER | openssl dgst -sha256
openssl x509 -in /etc/vanguard/tls.crt -pubkey -noout | \
  openssl pkey -pubin -outform DER | openssl dgst -sha256
```

Isi token pada env sesuai bab 5.4 modul utama. `VANGUARD_CA_TOKEN` sama pada CA
dan ADMIN; token server independen. Token ini melindungi endpoint issuance/revoke,
bukan password karyawan. Simpan env root:root 0600 dan jangan tampilkan isinya.

Setelah CA TLS/env/firewall siap, **VM-CA**:

```bash
sudo systemctl enable --now vanguard-ca
sudo systemctl is-active vanguard-ca
```

**VM-SERVER atau VM-ADMIN**, yang diizinkan firewall CA:

```bash
curl --fail --cacert /etc/vanguard/root.crt https://192.168.100.10:8080/healthz
```

Target health `status: ok`. Host laptop tidak otomatis boleh mengakses port 8080
karena firewall CA membatasi sumber ke SERVER/ADMIN. Jangan membuka firewall
semua sumber hanya agar contoh curl dapat dijalankan dari host.
Health membuktikan endpoint hidup, bukan seluruh state CA/CRL sehat.

## 10. Bagaimana sertifikat perangkat diterbitkan?

1. Pada client baru, jalankan `vanguard-client init` sesuai modul Ubuntu/Windows.
   Client membuat P-256 identity.key, CSR dengan CN device ID, serta key WireGuard
   X25519 independen. request.json memuat CSR, public key WireGuard dan tunnel IP.
2. Admin membuat akun karyawan lalu mengunggah request.json pada dashboard.
3. Dashboard mengirim device ID dan CSR ke `/api/ca/issue` memakai token CA.
4. CA memeriksa signature CSR, satu CN yang cocok device ID dan key P-256.
   Extensions klien tidak disalin sembarang; profil perangkat berasal dari CA.
5. CA menandatangani sertifikat clientAuth 30 hari, mencatat serial/index dan
   menyimpan salinan berdasarkan hash CSR. Retry CSR yang sama dapat mendapat
   sertifikat yang sama; ini bukan renewal otomatis.
6. Dashboard mengirim sertifikat/public key WireGuard/tunnel IP ke registry SERVER
   dan menautkan akun karyawan. Status menjadi registered.
7. Sertifikat dipasang ke client asal. Karyawan login dan connect; server baru
   menambahkan peer setelah keenam pemeriksaan admission berhasil.

Jangan memakai `sign-tls` untuk perangkat. CLI CA hanya menyediakan `init` dan
`sign-tls`; tidak ada subcommand CLI `issue`/`revoke` dalam versi ini. Pengelolaan
perangkat rutin dilakukan melalui dashboard yang mencatat actor dan waktu.

Di client Ubuntu, inspeksi publik dapat dilakukan dengan:

```bash
sudo openssl x509 -in /var/lib/vanguard/client/device.crt \
  -noout -subject -issuer -serial -dates -ext extendedKeyUsage
```

Target CN device ID, issuer root lab, clientAuth dan tanggal valid. Pengecekan
OpenSSL ini belum membuktikan binding WireGuard, sesi karyawan, atau proof.
Sertifikat publik tidak memberikan akses tanpa private key yang cocok.

## 11. CRL, pencabutan dan pemeriksaannya

CRL memuat issuer, lastUpdate, nextUpdate, CRL number, serial tercabut dan
signature root. Source membuat CRL baru pada setiap fetch `/api/ca/crl` di
bawah lock CA. Artinya fetch CRL memperbarui crl.pem/crlnumber, bukan sekadar
membaca file. Tidak ada fallback menerima cache CRL expired ketika CA gagal.

Pada VM-CA, inspeksi file yang telah ada tanpa meminta CRL baru:

```bash
sudo -u vanguard openssl crl -in /var/lib/vanguard/ca/crl.pem \
  -noout -issuer -lastupdate -nextupdate -crlnumber
sudo -u vanguard openssl crl -in /var/lib/vanguard/ca/crl.pem \
  -noout -verify -CAfile /etc/vanguard/root.crt
```

Signature valid belum berarti CRL masih berlaku; periksa waktu secara terpisah.
Validator mewajibkan `lastUpdate <= waktu aktual < nextUpdate`. CRL bertanda
tangan yang maju maksimal1 detik hanya ditunggu hingga batas waktu lalu diperiksa
ulang; tidak diterima sebelum berlaku. Selisih lebih besar ditolak.

Contoh pengambilan CRL baru di **VM-SERVER**, menghasilkan state baru di CA:

```bash
crl_sample=$(mktemp /tmp/vanguard-crl.XXXXXX.pem)
curl --fail --cacert /etc/vanguard/root.crt \
  https://192.168.100.10:8080/api/ca/crl -o "$crl_sample"
openssl crl -in "$crl_sample" -noout -verify -CAfile /etc/vanguard/root.crt
openssl crl -in "$crl_sample" -noout -issuer -lastupdate -nextupdate -crlnumber
```

Untuk memeriksa **salinan sertifikat publik perangkat** yang ditempatkan teknisi
di `/PATH/device.crt` pada SERVER:

```bash
openssl verify -purpose sslclient -crl_check \
  -CAfile /etc/vanguard/root.crt -CRLfile "$crl_sample" /PATH/device.crt
```

Sertifikat sah mengembalikan OK. Setelah serialnya dicabut dan CRL baru diambil,
verifikasi harus gagal dengan `certificate revoked` (error 23). Error jaringan,
file salah atau CRL expired bukan bukti revocation berhasil.

Pencabutan operasional dilakukan admin melalui **Cabut akses & sertifikat**,
dengan alasan dan pemeriksaan target. Workflow menonaktifkan perangkat/server,
meminta CA mencabut serial, lalu mencatat penyelesaian. OpenSSL menandai index
`R`, mempertahankan sertifikat historis, dan menandatangani CRL baru.
Status `revoking` memerlukan retry setelah dependency pulih; status itu belum
menyatakan seluruh workflow berhasil. Gunakan perangkat disposable untuk latihan.

Pencabutan langsung CA dan pencabutan dashboard mempunyai batas pengamatan
berbeda: dashboard juga menonaktifkan perangkat segera melalui API server,
sedangkan deteksi CA-only bergantung pemeriksaan server/daemon. Jangan menyamakan
dua waktu tersebut dalam laporan penelitian. Revocation Windows belum diuji
penuh pada bukti yang dirangkum modul ini.

## 12. Backup, kedaluwarsa dan pemulihan

Backup harus menyimpan seluruh state CA, bukan root.crt saja: key root,
openssl.cnf, index, serial, crlnumber, CRL, arsip sertifikat, konfigurasi layanan,
serta versi paket. Arsip mengandung rahasia dan harus tetap privat.

Contoh **HOST**, pada jendela pemeliharaan yang sudah disepakati. Admission/
renewal yang memerlukan CA dapat gagal selama layanan dihentikan. Jalankan di
subshell berikut; jika CA tadinya aktif, trap mencoba menyalakannya kembali
meski backup gagal. Selalu periksa hasil restart:

```bash
(
  set -euo pipefail
  umask 077
  ca_backup=$(mktemp -d /home/lui/VanGuard-Privat/ca-backup.XXXXXX)
  ssh -F ~/.ssh/vanguard_lab_config 192.168.100.10 \
    'sudo systemctl is-active --quiet vanguard-ca'
  trap 'ssh -F ~/.ssh/vanguard_lab_config 192.168.100.10 "sudo systemctl start vanguard-ca"' EXIT
  ssh -F ~/.ssh/vanguard_lab_config 192.168.100.10 \
    'sudo systemctl stop vanguard-ca'
  ssh -F ~/.ssh/vanguard_lab_config 192.168.100.10 \
    'sudo tar czf - -C / var/lib/vanguard/ca etc/vanguard' \
    > "$ca_backup/ca.tar.gz.partial"
  tar tzf "$ca_backup/ca.tar.gz.partial" >/dev/null
  mv "$ca_backup/ca.tar.gz.partial" "$ca_backup/ca.tar.gz"
  sha256sum "$ca_backup/ca.tar.gz" > "$ca_backup/SHA256SUMS"
)
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.10 \
  'sudo systemctl is-active vanguard-ca'
```

Pastikan tidak ada operator lain menjalankan CLI CA saat backup; menghentikan
API tidak otomatis menghentikan operasi manual lain. Jika koneksi terputus,
periksa status service dan arsip `.partial`; jangan menyatakan backup lengkap.
Folder privat pada contoh harus sudah ada dengan mode 0700. Inventaris/token/key
dan arsip tidak diunggah ke GitHub, termasuk repository private.

Jika sertifikat perangkat30 hari expired, renewal admission tidak memperpanjangnya.
Workflow renewal sertifikat otomatis belum tersedia. Rencanakan pergantian
identitas dengan akun/binding yang benar; jangan menghapus CA untuk mengatasi
satu client expired. Perpanjangan TLS/root juga memerlukan prosedur teknisi
terencana dan verifikasi trust, bukan mengulang installer pada data lama.

CA lab pernah mengalami counter CRL kosong setelah host restart. Pemulihan 15
Oktober menggunakan signed CRL dan counter lama untuk memilih nomor lebih besar,
dengan backup dan verifikasi bahwa index/key/serial/revocation tetap utuh.
Jangan memakai perintah reset counter ke 1000 atau mengembalikan index/CRL lama.
Pemulihan operasional tersebut belum memperbaiki durability penyimpanan source.

## 13. Kesalahan umum dan hasil yang harus dicatat

| Gejala | Penjelasan dan tindakan |
|---|---|
| CA already initialized | CA telah memiliki konfigurasi; periksa dan gunakan identitas yang ada |
| Output already exists pada sign-tls | Sertifikat output sudah ada; periksa hasil/serial sebelum retry |
| Permission denied | Periksa pemilik state vanguard, direktori 0700 dan key 0600; jangan chmod 777 |
| CSR must be signed by a P-256 key… | Device CSR salah key/CN/signature; buat request melalui client pada perangkat asal |
| TLS certificate must belong… | sign-tls dibatasi layanan .10/.20/.40, bukan endpoint client .60 |
| IP address mismatch | SAN sertifikat tidak sesuai IP akses; periksa sertifikat yang dipasang |
| Unable to get local issuer | Root trust salah/hilang; cocokkan fingerprint lalu perbaiki trust |
| Certificate expired/not yet valid | Periksa jam serta tanggal sertifikat; jangan menonaktifkan pemeriksaan |
| CRL signature/validity error | Periksa issuer/signature/waktu/CA; kegagalan harus menolak admission |
| Health OK tetapi issuance gagal | Health hanya liveness; periksa permission, counter/index dan log CA |
| Registry sudah ada | Lanjut workflow pada dashboard; jangan mengubah key/CSR identitas utama |

Catatan bukti minimal: waktu WIB, guest, operasi, fingerprint **publik**, serial
sertifikat, tanggal berlaku, CRL number, hasil verify, status workflow, lokasi
backup dan langkah berikutnya. Tidak perlu mencatat key, token atau password.

Urutan kelulusan instalasi: root valid dan dipercaya → TLS masing-masing layanan
valid/IP cocok → health/CRL berfungsi → perangkat registered tanpa peer → akun
login → admission → handshake → ping → penghentian akses/arsip sesuai skenario.

Pembuatan root, signing TLS/perangkat, CRL dan pencabutan pada panduan ini diuji
secara terisolasi di host. Transfer SSH, backup dan restart layanan adalah
prosedur operasional yang tidak dijalankan ulang pada tugas dokumentasi ini.
Tidak ada generate CA baru, penggantian trust, atau pencabutan pada VM
produksi ketika panduan ini ditulis. Bukti uji prosedur dicatat di
[jurnal 17 Oktober](PROGRESS_2026-10-17.md).
