# Modul lengkap penggunaan Sistem VanGuard

Edisi 17 Oktober 2026 · Panduan teknisi, administrator, dan karyawan

Modul ini menjelaskan persiapan, pemasangan, pendaftaran pengguna/perangkat,
pembuatan CA dan pengelolaan sertifikat secara rinci, pemakaian VPN Ubuntu dan
Windows, audit, pengujian, serta penghentian sistem dalam satu dokumen.
Contoh mengikuti lab VanGuard di komputer ini. Gunakan versi HTML dengan nama
yang sama untuk membaca di browser atau mencetak ke PDF ukuran A4.

## 1. Tujuan, hasil belajar, dan jalur membaca

Setelah mengikuti modul, peserta mampu:

1. Menjelaskan perbedaan akun sistem operasi, admin dashboard, dan karyawan VPN.
2. Memeriksa kesiapan VM, waktu, layanan HTTPS, dan sertifikat kepercayaan.
3. Membuat akun karyawan dan mendaftarkan identitas perangkat melalui dashboard.
4. Menggunakan VPN dari Ubuntu atau Windows serta membuktikan koneksinya.
5. Menelusuri waktu/tindakan admin, membuat arsip, dan memeriksa integritasnya.
6. Menutup sesi, menangani kendala, dan mencatat bukti tanpa membocorkan rahasia.

| Kondisi pembaca | Urutan yang dikerjakan | Hasil akhir |
|---|---|---|
| Karyawan pada lab terpasang | Bab 2–4, bab 7 atau8, bab 9 dan12 | Login, tunnel, ping, lalu disconnect |
| Admin dashboard | Bab 2–6, bab 9–13 | Akun dan perangkat dikelola, aktivitas diarsipkan |
| Teknisi instalasi baru | Seluruh bab; bab 5 hanya untuk lingkungan kosong | Infrastruktur dan aplikasi siap diserahterimakan |
| Pembimbing/penguji | Bab 2–3, bab 9–11 dan14 | Memahami bukti serta batas hasil yang dapat diklaim |

Perintah berlabel **HOST** dijalankan pada laptop Ubuntu, **VM-…** di guest yang
bersangkutan, dan **WINDOWS ADMIN** pada PowerShell yang dijalankan sebagai
Administrator. Ganti placeholder huruf kapital dengan nilai milik lab Anda.
Jangan mengetik placeholder sebagai kredensial sungguhan.

Lab ini sudah terpasang. Untuk pemakaian harian, **lewati bab 5 dan langkah init
perangkat utama**. Instalasi ulang CA atau penggantian key bukan cara login.

## 2. Mengenal sistem dan identitas

VanGuard mengizinkan perangkat menjadi peer WireGuard setelah akun karyawan
terautentikasi dan identitas perangkat lolos pemeriksaan. Sistem tidak mengubah
kernel atau protokol WireGuard.

Urutan kerja:

```text
Client membuat key sendiri → request publik → admin menerbitkan sertifikat/binding
Karyawan login → sesi akun → challenge → proof ditandatangani key perangkat
Server memeriksa sertifikat/CRL/proof/binding → ACCEPT → peer WireGuard aktif
Client membentuk tunnel → handshake → akses yang diizinkan → admission berkala
```

Enam pemeriksaan perangkat: signature X.509 terhadap Root CA, masa berlaku
sertifikat, CRL terkini, serial tidak dicabut, bukti kepemilikan private key
X.509, dan kecocokan sertifikat dengan public key WireGuard pada registry.
Password karyawan yang benar tidak menggantikan pemeriksaan tersebut.

| Jenis identitas | Dipakai untuk | Penyimpanan/penanggung jawab |
|---|---|---|
| Akun OS/console | Masuk Ubuntu atau Windows | Operator; inventaris privat host |
| Admin dashboard | Mengelola akun, sertifikat dan audit | Password + TOTP admin |
| Karyawan VPN | Meminta sesi akses VPN | Password karyawan dari admin |
| Identitas perangkat | Membuktikan perangkat memiliki key yang terdaftar | Private key tetap di client |
| Token antarlayanan | Otorisasi API administrasi CA/server | Berkas env privat layanan |

TOTP admin berasal dari aplikasi authenticator yang telah didaftarkan. Dashboard
memverifikasi kode enam digit; tidak menyediakan tombol untuk menampilkan kode
login berjalan. Karyawan VPN tidak memakai TOTP admin untuk login.

Sesi karyawan berlaku delapan jam pada implementasi ini. Admission berkala
memperbarui lease perangkat, tetapi tidak memperpanjang sesi karyawan. Ketika
sesi habis, karyawan harus login lagi. Private key, token sesi, seed TOTP, dan
password bukan lampiran laporan.

## 3. Topologi, perangkat lunak, dan batas lab

| VM | LAN | Tunnel | Fungsi |
|---|---|---|---|
| VM-CA | 192.168.100.10 | — | OpenSSL private CA; HTTPS 8080 |
| VM-SERVER | 192.168.100.20 | 10.8.0.1 | Validasi, daemon, registry; HTTPS 8081 dan UDP 51820 |
| VM-CLIENT | 192.168.100.30 | 10.8.0.2 | Client Ubuntu 22.04 |
| VM-ADMIN | 192.168.100.40 | — | Flask/Jinja2, SQLite, dashboard HTTPS 5000 |
| VM-ATTACKER | 192.168.100.50 | — | Simulasi negatif yang diotorisasi dalam lab |
| VM-CLIENT-WINDOWS | 192.168.100.60 | 10.8.0.4 | Client Windows tambahan |

Jaringan libvirt `vanguard` menggunakan gateway host `192.168.100.1`.
Alamat `10.8.0.3` dicadangkan untuk eksperimen terpisah. Kelima Ubuntu tetap ada;
Windows adalah node keenam. Client memakai pasangan key masing-masing.

Host memakai KVM/libvirt, `virsh`, Virtual Machine Manager, SSH dan browser.
Windows memakai UEFI Secure Boot, TPM2, 4 GiB RAM, 2 vCPU dan disk sparse80 GiB.
RAM host yang tercatat sekitar 7,5 GiB; menyalakan seluruh node menambah beban.
Periksa `free -h` sebelum sesi dan hindari menjalankan pekerjaan berat bersamaan.
Status `running` pada libvirt belum membuktikan OS selesai boot atau VPN aktif.

Versi yang terakhir dibuktikan pada15 Oktober: dashboard Ubuntu 0.1.6, komponen
Ubuntu lain0.1.5, client Windows 0.1.8; Windows build26300, Python 3.13.16,
WireGuard 1.1.1. Versi source terbaru tidak otomatis mengganti paket semua VM.

Layanan terlindungi yang telah dibuktikan adalah **ICMP/ping ke 10.8.0.1**.
Modul ini tidak menjanjikan internet lewat VPN, akses ERP/web/file server,
kebijakan per departemen, SSO, atau pembuktian TCP yang belum diimplementasikan.

## 4. Memulai lab yang sudah terpasang

### 4.1 Nyalakan dan periksa VM — HOST

```bash
cd /home/lui/vanguard
virsh -c qemu:///system list --all
free -h
virsh -c qemu:///system net-info vanguard
```

Jika jaringan `vanguard` tidak aktif, jalankan `virsh -c qemu:///system net-start
vanguard`. Nyalakan VM berstatus **shut off** sesuai kebutuhan, berurutan:

```bash
virsh -c qemu:///system start VM-CA
virsh -c qemu:///system start VM-SERVER
virsh -c qemu:///system start VM-ADMIN
virsh -c qemu:///system start VM-CLIENT
virsh -c qemu:///system start VM-CLIENT-WINDOWS
virsh -c qemu:///system start VM-ATTACKER
```

Jangan ulangi `start` pada VM yang sudah running. Attacker diperlukan saat
latihan keamanan. `scripts/open_dashboard.sh` yang tersedia saat modul ditulis
menyalakan lima Ubuntu; Windows tetap perlu dinyalakan terpisah.

Untuk melihat console:

```bash
virt-manager --connect qemu:///system
virt-viewer --connect qemu:///system VM-CLIENT-WINDOWS
```

Password console Windows terakhir ada pada kartu lokal
`/home/lui/VanGuard-Privat/AKSES_WINDOWS_TERBARU.txt`. Inventaris lengkap berada
di folder privat yang sama. Password console berbeda dari password VPN Windows.

### 4.2 Verifikasi layanan — HOST, lalu guest yang dipilih

```bash
.venv/bin/python scripts/ssh_preflight.py state/lab/inventory.json
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.10
```

Preflight lama memeriksa lima Ubuntu, **tidak mencakup Windows**. Perintah SSH
menempatkan terminal pada VM-CA. Periksa, kemudian `exit` untuk kembali ke host:

```bash
sudo systemctl is-active vanguard-ca
timedatectl status
exit
```

Pada VM-SERVER melalui SSH `.20`, jalankan:

```bash
sudo systemctl is-active vanguard-server vanguard-daemon wg-quick@wg0
sudo wg show wg0
timedatectl status
```

Pada VM-ADMIN melalui SSH `.40`, jalankan:

```bash
sudo systemctl is-active vanguard-admin
timedatectl status
```

Target: semua unit di atas `active`, waktu benar, dashboard dapat dibuka melalui
**https://192.168.100.40:5000**. Di HOST, pemeriksaan TLS:

```bash
curl --fail --cacert state/deployment/root.crt \
  https://192.168.100.40:5000/healthz
```

Browser harus mempercayai root CA lab yang fingerprint-nya sudah diverifikasi.
Impor `state/deployment/root.crt` ke Authorities/CA browser bila diperlukan.
Jangan menyelesaikan masalah sertifikat dengan menonaktifkan pemeriksaan TLS.

## 5. Pemasangan awal — khusus lingkungan baru

Bab ini adalah pekerjaan teknisi. Jangan menjalankannya pada lab terpasang.
Panduan detail referensi: [deployment Ubuntu](DEPLOYMENT.md) dan
[penyiapan Windows](WINDOWS_CLIENT.md). Ikuti urutan berikut; tiap tahap memiliki
hasil yang harus dipenuhi sebelum lanjut.

### 5.1 Siapkan host, enam guest, source dan SSH

1. Siapkan host Linux dengan virtualisasi KVM, libvirt, virt-manager/virt-viewer,
   akses administrator dan penyimpanan untuk seluruh disk/backup.
2. Buat jaringan NAT libvirt `vanguard`, subnet192.168.100.0/24, gateway.1.
   Pastikan subnet tidak bertabrakan dengan jaringan host lain.
3. Pasang lima Ubuntu Server22.04 dengan nama/IP pada bab 3. Atur IPv4 statis,
   gateway/DNS.1, hostname, waktu, serta akun operator dan OpenSSH.
4. Siapkan satu Windows 11 tambahan dengan spesifikasi bab 3 dan IP.60. Pakai
   media resmi yang telah diverifikasi; selesaikan instalasi serta akun lokal.
   Jangan memakai ulang seed pemformatan pada disk berisi data.
5. Salin source yang telah diverifikasi ke direktori kerja pada setiap Ubuntu.
   Jangan ikut menyalin `state/`, `.venv/`, `.git/`, atau inventaris rahasia.
6. Siapkan key SSH host, cocokkan fingerprint guest melalui console, lalu catat
   host key. Salin `deploy/inventory.example.json` ke lokasi privat dan sesuaikan
   user/host/port/konfigurasi SSH lima Ubuntu. Password tidak dimasukkan inventory ini.
7. Jalankan `python3 scripts/ssh_preflight.py /path/to/inventory.json`. Target
   kelima role `ok: true`, Ubuntu 22.04 dan kemampuan sudo sesuai deployment.

Skrip `create_lab.py` serta `create_windows_client.py` adalah alat provisioning;
baca `--help` dan batasannya sebelum dipakai. Inventaris lima role yang digunakan
`deploy_lab.py` tidak boleh ditambah role Windows lalu dianggap otomatis didukung.

### 5.2 Pasang aplikasi Ubuntu pada role yang benar

Di root source **guest masing-masing**, jalankan hanya perintah yang cocok:

| Guest | Perintah |
|---|---|
| VM-CA | `sudo bash deploy/install.sh ca` |
| VM-SERVER | `sudo bash deploy/install.sh server` |
| VM-CLIENT | `sudo bash deploy/install.sh client` |
| VM-ADMIN | `sudo bash deploy/install.sh admin` |
| VM-ATTACKER | `sudo bash deploy/install.sh attacker` |

Installer memeriksa OS dan IP, memasang Python/aplikasi serta unit systemd.
Installer belum memulai layanan atau menerapkan firewall. Paket berada pada
`/opt/vanguard/venv`, state pada `/var/lib/vanguard`, konfigurasi pada
`/etc/vanguard`. Server mendapat key WireGuard dan config tanpa peer statis.

### 5.3 CA, sertifikat, trust dan CRL — panduan rinci

Seluruh materi CA/PKI berada di bagian ini, mulai dari generate root hingga
backup dan troubleshooting. Bagian 5.3.1–5.3.9 memandu pemasangan CA/HTTPS;
5.3.10–5.3.13 menjelaskan siklus sertifikat dan pemeliharaan setelah instalasi.
Lanjutkan bagian 5.4–5.6 untuk token, firewall, layanan dan client Windows,
lalu bab 6–10 untuk pendaftaran dan pemakaian sistem.

Contoh mengikuti source VanGuard 0.1.8, terutama `vanguard/ca.py`,
`vanguard/pki.py`, `vanguard/client.py` dan workflow dashboard. Setiap blok
menyebutkan tempat menjalankannya. **CA lab yang ada sudah terpasang**;
gunakan bagian pemeriksaan untuk pemeliharaan. Langkah init/generate/signing
hanya untuk pemasangan baru atau pekerjaan teknisi yang direncanakan.

#### 5.3.1 CA itu apa dan apa hubungannya dengan VPN?

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

#### 5.3.2 Struktur file dan parameter CA yang sebenarnya

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

#### 5.3.3 Persiapan sebelum generate CA

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
inventaris privat host yang disebut pada modul ini.

#### 5.3.4 Generate root CA pada VM baru

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

#### 5.3.5 Verifikasi root sebelum dipercaya

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

#### 5.3.6 Distribusikan root publik melalui HOST

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

Cocokkan fingerprint dengan hasil bagian 5.3.5 sebelum meneruskan. `$ca_stage` hanya
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

#### 5.3.7 Generate key dan CSR HTTPS pada setiap layanan

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

#### 5.3.8 Contoh lengkap: tanda tangani HTTPS SERVER lewat CA

Contoh berikut melanjutkan variabel `$ca_stage` dari bagian 5.3.6, dan mengikuti
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

#### 5.3.9 Verifikasi sertifikat HTTPS dan jalankan layanan

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

Isi token pada env sesuai bagian 5.4. `VANGUARD_CA_TOKEN` sama pada CA
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

#### 5.3.10 Bagaimana sertifikat perangkat diterbitkan?

1. Pada client baru, jalankan `vanguard-client init` sesuai bab 6–8.
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

#### 5.3.11 CRL, pencabutan dan pemeriksaannya

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

#### 5.3.12 Backup, kedaluwarsa dan pemulihan

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

#### 5.3.13 Kesalahan umum dan hasil yang harus dicatat

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

### 5.4 Konfigurasi token dan akun admin awal

Buat tiga nilai acak independen dengan `openssl rand -hex 32` dalam terminal
privat. Isi template env menggunakan `sudoedit`; jangan menaruh nilai literal
di command history atau dokumen. Catat lokasi dan nilai hanya pada inventaris
privat operator.

| Variabel | Lokasi yang menerima nilai sama |
|---|---|
| VANGUARD_CA_TOKEN | ca.env di CA dan admin.env di ADMIN |
| VANGUARD_SERVER_TOKEN | server.env di SERVER dan admin.env di ADMIN |
| VANGUARD_SESSION_SECRET | admin.env di ADMIN; nilai ketiga yang independen |

Semua file berada pada `/etc/vanguard/`, owner root:root, mode0600.
Pastikan URL CA/server dan path sertifikat pada template sesuai topologi.
Pada **VM-ADMIN baru**, buat satu admin melalui prompt:

```bash
sudo -u vanguard /opt/vanguard/venv/bin/vanguard-admin --username NAMA_ADMIN_BARU
```

Password minimal 12 karakter, diketik dua kali. Daftarkan URI TOTP yang ditampilkan
di terminal privat ke authenticator dan konfirmasi kode. Jangan membuat ulang
akun admin utama hanya karena sesi login habis.

### 5.5 Firewall dan layanan

Jalur yang perlu diizinkan: CA8080 dari SERVER/ADMIN; SERVER8081 dari kedua
client, ADMIN dan ATTACKER; UDP 51820 dari kedua client dan ATTACKER; ADMIN5000
dari host. SSH guest hanya dari manajemen. ICMP10.8.0.1 dari.2/.4 harus masuk
lewat `wg0`; trafik ke alamat tunnel yang datang langsung dari LAN ditolak.

Pasang `nftables` pada Ubuntu yang akan diberi aturan. Salin `deploy/firewall.py`
ke `/opt/vanguard/firewall.py` pada guest. Di guest masing-masing jalankan
`sudo python3 /opt/vanguard/firewall.py ROLE --management-ip 192.168.100.1`,
dengan ROLE `ca`, `server`, `client`, `admin`, atau `attacker`. Khusus SERVER:

```bash
sudo python3 /opt/vanguard/firewall.py server \
  --management-ip 192.168.100.1 --windows-client
```

Simpan ruleset sebelum perubahan. Skrip memasang timer rollback120 detik.
**Buka koneksi SSH baru** dan periksa `sudo systemctl is-active vanguard-firewall`;
baru hentikan `vanguard-firewall-rollback.timer` pada guest itu. Jika SSH gagal,
gunakan console dan periksa rollback; jangan menandai firewall siap.

Mulai layanan sesuai guest:

```bash
# VM-CA
sudo systemctl enable --now vanguard-ca
# VM-SERVER
sudo systemctl enable wg-quick@wg0 vanguard-daemon vanguard-server
sudo systemctl start vanguard-server
sudo wg show wg0 peers
# VM-ADMIN
sudo systemctl enable --now vanguard-admin
```

Pada instalasi baru, daftar peer harus kosong sebelum admission client. Setelah
HTTPS sehat, lanjutkan bab 6. Jangan menambahkan peer manual untuk mempercepat demo.

### 5.6 Pasang aplikasi Windows baru

1. Pasang Python 3.12 atau lebih baru dan WireGuard for Windows dari penerbit resmi;
   periksa signature installer. Jangan menonaktifkan Windows Firewall.
2. Atur NIC ke 192.168.100.60/24, gateway/DNS.1, waktu Jakarta. Pastikan koneksi
   HTTPS ke server tersedia dan sertifikat root cocok fingerprint operator.
3. Build wheel source di HOST dengan
   `.venv/bin/python -m pip wheel --no-deps --wheel-dir dist .`, lalu transfer
   wheel0.1.8 dan `deploy/constraints.txt` ke folder staging privat guest.
4. Pada PowerShell Administrator, buat virtualenv; sesuaikan path Python dan wheel:

```powershell
& 'C:\Program Files\Python313\python.exe' -m venv C:\ProgramData\VanGuard\venv
$py = 'C:\ProgramData\VanGuard\venv\Scripts\python.exe'
& $py -m pip install -c C:\VG-Staging\constraints.txt C:\VG-Staging\vanguard_ztna-0.1.8-py3-none-any.whl
& $py -m pip check
& $py -m vanguard.client --help
```

Python313 adalah lokasi instalasi yang dibuktikan pada guest ini; ganti bila
berbeda. Instalasi pip di atas membutuhkan akses dependensi, atau wheelhouse
terverifikasi yang disiapkan teknisi. Paket0.1.8 membutuhkan pywin32 di Windows.
Jika installer memakai autologon/unattend, teknisi harus membersihkan secret
setup dan mengeluarkan media seed sesudah selesai. Lanjut bab 6 untuk perangkat
yang belum diinisialisasi. SSH Windows opsional untuk pemeliharaan; pemakaian
normal bisa melalui console, dengan hak Administrator untuk mengelola tunnel.

## 6. Admin: menyiapkan akun dan perangkat

### 6.1 Login dashboard

1. Di browser HOST buka `https://192.168.100.40:5000` dengan trust CA yang benar.
2. Masukkan username/password **admin dashboard** dan kode TOTP dari authenticator.
3. Klik **Masuk**. Halaman **Perangkat & admission** harus terbuka.
4. Periksa **Kesehatan layanan**: CA dan Server tersedia.

Di lab terpasang, informasi aktivasi privat berada di
`state/deployment/aktivasi-admin.html`. QR/seed hanya untuk pemilik akun.
TOTP memakai waktu, SHA-1, enam digit,30 detik. Kode yang sudah dipakai tidak bisa
dipakai untuk login kedua; tunggu kode berikutnya. Setelah lima kegagalan,
tunggu lima menit. Sesi dashboard sekitar 30 menit.

### 6.2 Buat akun karyawan

Pada **Akun karyawan**, isi username unik dan password awal minimal 12 karakter,
lalu klik **Buat akun karyawan**. Serahkan kredensial melalui kanal privat dan
catat pada inventaris lokal operator. Akun Ubuntu dan Windows lab sudah ada;
gunakan akun yang terikat pada perangkat masing-masing. Belum ada fitur reset
password mandiri atau aktivasi ulang akun yang dinonaktifkan.

### 6.3 Buat request hanya pada client baru

**Ubuntu baru**, pada VM-CLIENT:

```bash
sudo /opt/vanguard/venv/bin/vanguard-client init --device-id vm-client
```

Hasilnya `/var/lib/vanguard/client/request.json`. Default alamat Ubuntu.2.
Pada **Windows baru**, PowerShell Administrator:

```powershell
$py = 'C:\ProgramData\VanGuard\venv\Scripts\python.exe'
& $py -m vanguard.client init --device-id vm-client-windows --tunnel-ip 10.8.0.4
```

Hasilnya `C:\ProgramData\VanGuard\client\request.json`. Direktori identitas
dilindungi ACL SYSTEM/Administrators. `identity.key` dan `wg.key` tetap di guest.
Salin **request.json saja** ke host operator melalui transfer tepercaya.
Pada guest yang sudah terdaftar jangan mengulang init atau mengganti request.

### 6.4 Daftar, unduh dan pasang sertifikat

1. Pada **Registrasi perangkat**, pilih request JSON yang sesuai.
2. Isi **Nama perangkat**, **Departemen**, **Pemilik**, dan **Platform**.
3. Pilih akun karyawan yang benar. Binding akun-perangkat tidak dapat diganti
   hanya dengan mengedit metadata; periksa pilihan sebelum mengirim.
4. Klik **Terbitkan sertifikat & daftarkan binding**.
5. Pastikan workflow `registered`. Peer perangkat baru harus belum aktif.
6. Klik **Unduh bundle onboarding** atau **Unduh sertifikat** pada baris tersebut.
   Bundle berisi device.crt, root.crt, manifest dan petunjuk; tidak berisi key.
7. Cocokkan device ID, public key/binding pada manifest dan fingerprint root
   dengan referensi operator sebelum mengimpor. Pasang hanya pada client pembuat CSR.

Pada Ubuntu, salin sertifikat ke staging guest, kemudian:

```bash
sudo install -m 0600 /PATH/STAGING/device.crt /var/lib/vanguard/client/device.crt
```

Trust Ubuntu di `/etc/vanguard/root.crt` sudah disiapkan pada instalasi layanan.
Pada PowerShell Administrator Windows, setelah bundle publik diekstrak ke staging:

```powershell
Copy-Item C:\VG-Staging\device.crt C:\ProgramData\VanGuard\client\device.crt
Copy-Item C:\VG-Staging\root.crt C:\ProgramData\VanGuard\client\root.crt
```

Jika file tujuan sudah ada, teknisi membandingkan identitasnya dahulu; jangan
menimpa sertifikat utama dengan hasil latihan. Client memeriksa kesesuaian
sertifikat dengan key lokal saat admission. Registrasi dan unduhan bundle
belum mengaktifkan tunnel. Workflow tertahan dilanjutkan dengan **Ulangi workflow**
setelah dependency pulih, bukan mengirim registrasi duplikat.

## 7. Karyawan Ubuntu: login dan memakai VPN

Prasyarat: perangkat sudah registered, sertifikat/root terpasang, akun terikat
dan aktif. Di HOST masuk ke VM-CLIENT:

```bash
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.30
```

Di VM-CLIENT masukkan username karyawan dari inventaris privat:

```bash
sudo /opt/vanguard/venv/bin/vanguard-client login --username USERNAME_KARYAWAN_UBUNTU
sudo systemctl restart vanguard-client
sudo systemctl status vanguard-client --no-pager
ping -c 3 -W 2 10.8.0.1
sudo wg show wg0
```

Password diminta tersembunyi. Login menghasilkan masa kedaluwarsa; client
menyimpan token privat, bukan password. Target: ping berhasil, handshake ada,
dan dashboard menunjukkan peer perangkat aktif. Jika delapan jam habis,
login kembali dan restart service. Logout dashboard tidak mengakhiri VPN ini.

Untuk instalasi Ubuntu baru, service membutuhkan `/etc/vanguard/client.env`
dengan `VANGUARD_SERVER_WG_PUBLIC_KEY` berisi public key dari
`/etc/vanguard/server-wg.pub` pada SERVER. Teknisi memasangnya root:root0600
melalui editor lalu `sudo systemctl enable vanguard-client`. Installer saja
belum mengisi nilai ini. Jangan memakai private key server.

Alternatif foreground untuk teknisi: stop service terlebih dahulu, kemudian
jalankan `sudo /opt/vanguard/venv/bin/vanguard-client connect --server-key
'PUBLIC_KEY_SERVER'`. Jangan menjalankan service dan foreground bersamaan.

## 8. Karyawan Windows: dari login desktop sampai disconnect

1. Buka console **VM-CLIENT-WINDOWS** melalui virt-viewer/virt-manager.
2. Masuk memakai **username/password console Windows** pada kartu lokal host.
3. Buka Start, cari PowerShell, pilih **Run as administrator**, setujui UAC.
4. Pastikan server, CA dan jaringan siap. Lab Windows sudah memiliki sertifikat
   dan key; tidak perlu init atau pendaftaran ulang.
5. Jalankan:

```powershell
$py = 'C:\ProgramData\VanGuard\venv\Scripts\python.exe'
& $py -m vanguard.client login --username USERNAME_KARYAWAN_WINDOWS
& $py -m vanguard.client connect --server-key 'PUBLIC_KEY_SERVER'
```

Username/password langkah5 adalah **akun VPN Windows**, berbeda dari akun
desktop langkah2. Public key server diperoleh operator melalui SSH terverifikasi
ke SERVER, dengan `sudo cat /etc/vanguard/server-wg.pub`. Ini nilai publik yang
boleh diberikan kepada karyawan; bukan isi `/etc/wireguard/wg0.conf`.

Target terminal: `Admitted; tunnel up. Renewing admission until stopped.`
Biarkan terminal ini berjalan. Pada PowerShell Administrator kedua:

```powershell
ping -n 3 10.8.0.1
& 'C:\Program Files\WireGuard\wg.exe' show vanguard-client
sc.exe qc 'WireGuardTunnel$vanguard-client'
```

Target: balasan ping, latest handshake, dan start type `DEMAND_START`.
Pada dashboard cari `vm-client-windows` dengan tunnel.4 dan peer aktif.
Jangan menambah tunnel manual lewat GUI WireGuard untuk melewati admission.

Untuk selesai, tekan **Ctrl+C di terminal connect**, lalu periksa:

```powershell
sc.exe query 'WireGuardTunnel$vanguard-client'
Test-Path C:\ProgramData\VanGuard\client\vanguard-client.conf
```

Setelah cleanup selesai, query service menghasilkan1060/tidak ditemukan dan
Test-Path `False`. Versi 0.1.8 menunggu penghapusan service hingga 15 detik; bila
tidak bisa memastikan cleanup, config dipertahankan agar bisa diperiksa.
Private key dan sertifikat tetap disimpan untuk koneksi berikutnya.

Windows tidak otomatis menyalakan tunnel ketika reboot. Buka PowerShell admin
dan jalankan connect lagi; login ulang jika sesi sudah expired. Satu siklus
renewal otomatis sudah dibuktikan, bukan uji kestabilan berjam-jam.

## 9. Memastikan sistem sudah dapat digunakan

Gunakan daftar penerimaan berikut. Isi hasil aktual dan tanggal, bukan menyalin
PASS dari hasil historis.

| Pemeriksaan | Bukti yang dicatat | Kriteria lulus |
|---|---|---|
| Mesin tersedia | Daftar VM dan tanggal | VM yang dipakai running dan selesai boot |
| Kepercayaan HTTPS | Fingerprint publik dan health | Root cocok; tidak menonaktifkan TLS |
| Admin | Login TOTP, halaman dashboard | Masuk dengan kode yang sah; CA/Server tersedia |
| Registry baru | Baris perangkat + peer server | Registered, key baru belum menjadi peer |
| Login karyawan | Hasil login tanpa token | Sesi sah; login saja belum membuka peer |
| Admission/tunnel | Output connect + wg show | ACCEPT, alamat benar, handshake ada |
| Akses user | Hasil ping10.8.0.1 | Balasan melalui tunnel |
| Dua client | Dua handshake dan allowed IP | Ubuntu.2 dan Windows.4 tidak bertabrakan |
| Selesai sesi | Service/interface/config client | Tunnel berhenti dan config sementara dibersihkan |
| Audit admin | Waktu WIB, pelaku, tindakan | Catatan sesuai tindakan yang dilakukan |
| Arsip | ZIP + checksum | Dapat dibuka dan cocok hash |

Di SERVER gunakan `sudo wg show wg0` atau `sudo wg show wg0 peers`.
**Jangan gunakan format dump untuk laporan**, karena dapat memuat private key.
Peer server bisa bertahan hingga lease habis sesudah client berhenti; ini
berbeda dari service tunnel lokal yang sudah dibersihkan. Pencabutan/disable
menjalankan penghapusan peer sesuai workflow server.

Runner `scripts/health_lab.py` bergantung pada client Ubuntu utama yang aktif;
bukan tes Windows. Bila diperlukan oleh teknisi di HOST:

```bash
module_run="state/deployment/module-$(date +%Y%m%d-%H%M%S)"
.venv/bin/python scripts/health_lab.py state/lab/inventory.json \
  --state "$module_run/health" --samples 3 --interval 10
```

Gunakan direktori baru per run. Jika hanya Windows yang aktif, periksa melalui
bab 8 dan SERVER; jangan mengartikan health runner Ubuntu gagal sebagai bukti
tunnel Windows gagal.

## 10. Admin: aktivitas, arsip, dan penghentian akses

### 10.1 Mencari tindakan berdasarkan waktu

1. Klik **Aktivitas admin**.
2. Pilih tanggal mulai/akhir dalam WIB, lalu filter pelaku, ID perangkat atau
   jenis tindakan. Tanggal akhir mencakup satu hari penuh.
3. Klik **Tampilkan**. Telusuri halaman berikutnya bila lebih dari50 baris.
4. Periksa jam-menit-detik, pelaku, tindakan dan keterangan Indonesia.

Satu tindakan dapat memiliki tahap diminta, gagal, retry dan selesai.
**Aktivitas keamanan server** berasal dari proses VPN otomatis; jangan menyamakan
aktor otomatis dengan admin yang sedang login. Waktu sumber disimpan Unix/UTC,
sedangkan tampilan dan CSV menggunakan WIB.

### 10.2 Menyimpan arsip yang dapat diverifikasi

1. Setelah filter sesuai, klik **Simpan arsip aktivitas**.
2. Snapshot memuat seluruh hasil filter, bukan hanya halaman yang sedang tampil.
   Batasnya10.000 catatan dan8 MiB sebelum ZIP; persempit filter jika melewati batas.
3. Buka **Arsip**, periksa pembuat, waktu, jumlah dan filter; unduh ZIP.
4. ZIP berisi `aktivitas.csv`, `aktivitas.json`, `manifest.json`, `PETUNJUK.txt`.
5. Di HOST jalankan `sha256sum /PATH/ARSIP.zip` dan cocokkan dengan checksum
   di dashboard. Manifest mencatat checksum CSV/JSON untuk verifikasi isi.
6. Simpan ZIP di folder privat operator dan catat path pada lembar praktikum.

Arsip tidak menghapus log asal. Arsip tersimpan dalam database VM-ADMIN, sehingga
backup database tetap diperlukan. Checksum bukan tanda tangan digital dan tidak
menjamin ketahanan terhadap root VM yang dapat mengubah database.

### 10.3 Mencabut akses

Pada perangkat yang memang hendak dihentikan, pilih alasan dan klik
**Cabut akses & sertifikat**. Tunggu status `revoked`, periksa peer hilang dan
admission ulang ditolak. Status `revoking` belum berarti proses selesai;
pulihkan dependency lalu pilih **Ulangi workflow**.

**Nonaktifkan akun karyawan** membatalkan sesi dan menghapus peer terkait,
tetapi tidak otomatis mencabut sertifikat. Identitas yang dicabut memerlukan
device ID dan key baru untuk pemakaian berikutnya; bukan edit metadata.
Gunakan identitas disposable untuk latihan, bukan `vm-client` atau
`vm-client-windows` yang sedang dipakai.

## 11. Praktikum dan penilaian

Praktikum dilakukan pada lab yang diotorisasi. Alokasi waktu berikut hanya
perkiraan untuk sesi pembelajaran, bukan hasil benchmark.

| Praktikum | Waktu | Tugas dan keluaran |
|---|---|---|
| A: orientasi | 20 menit | Gambar enam node dan jelaskan tiga jenis akun |
| B: kesiapan | 20 menit | Periksa VM, waktu, trust dan health; catat kendala |
| C: pemakaian | 30 menit | Login client yang dipilih, handshake/ping, disconnect |
| D: administrator | 25 menit | Login TOTP, cari aktivitas WIB, buat/cek arsip |
| E: enrollment latihan | 45 menit | Identitas disposable → registered → admission → revoke → cleanup |

Praktikum E memakai prosedur terpisah pada
[tutorial bab 7](TUTORIAL_PENGGUNAAN.md). Prosedur tersebut mengikuti client
Ubuntu 0.1.5 yang terpasang dan memakai alamat eksperimen.3. Pastikan tidak ada
eksperimen lain aktif. Latihan `admit` tidak membuktikan trafik; pengujian ping
tetap dilakukan pada client utama. Jangan menyalin key ke attacker.

Contoh penilaian: kesiapan20 poin, penjelasan akun/admission20, koneksi dan
disconnect30, audit/arsip20, pencatatan aman10. Lulus minimal 80/100 dan tidak
memasukkan kredensial/private key pada bukti. Rubrik ini usulan pembelajaran.

Pertanyaan evaluasi:

1. Mengapa password karyawan yang benar belum cukup untuk mendapatkan tunnel?
2. Apa perbedaan `registered`, peer aktif, handshake dan ping berhasil?
3. Mengapa login karyawan harus diulang meskipun renewal perangkat berjalan?
4. Apa perbedaan disable akun, revoke sertifikat dan logout dashboard?
5. Mengapa checksum arsip belum membuktikan bahwa root VM tidak mengubah isinya?

Jawaban inti: akun dan perangkat diperiksa terpisah; registry bukan akses;
lease dibatasi sesi login; tindakan penghentian memiliki sasaran berbeda;
checksum tidak memiliki penandatangan independen.

## 12. Mengakhiri sesi dan mematikan lab

1. Karyawan Windows: Ctrl+C pada connect dan periksa cleanup sesuai bab 8.
2. Karyawan Ubuntu: `sudo systemctl stop vanguard-client`; pastikan `wg0`
   tidak aktif pada client. Perintah ini tidak mematikan interface server.
3. Admin: simpan arsip bila perlu, kemudian klik **Keluar**.
4. Jika seluruh lab hendak dimatikan, dari HOST kirim shutdown normal:

```bash
virsh -c qemu:///system shutdown VM-CLIENT-WINDOWS
virsh -c qemu:///system shutdown VM-CLIENT
virsh -c qemu:///system shutdown VM-ATTACKER
virsh -c qemu:///system shutdown VM-ADMIN
virsh -c qemu:///system shutdown VM-SERVER
virsh -c qemu:///system shutdown VM-CA
virsh -c qemu:///system list --all
```

Kirim hanya pada VM running. Tunggu seluruh target `shut off` sebelum mematikan
host. Respons shutdown sukses berarti permintaan terkirim, bukan guest pasti
sudah mati. Jika Windows tidak merespons ACPI, gunakan Start → Power → Shut down
di console. Hindari force-off saat CA menulis state.

Backup oleh teknisi: hentikan layanan penulis terkait atau gunakan backup SQLite
konsisten, lalu simpan konfigurasi `/etc/vanguard`, state `/var/lib/vanguard`,
WireGuard `/etc/wireguard` dan versi paket sebelumnya di lokasi privat. Backup
CA berisi key sensitif; batasi akses. Pemulihan tidak boleh mengembalikan index/CRL
lama sehingga sertifikat tercabut menjadi berlaku kembali. Catat tanggal,
hash backup, layanan yang dihentikan/dimulai, dan pemeriksaan setelah pemulihan.

## 13. Pemecahan masalah

| Gejala | Pemeriksaan dan langkah berikutnya |
|---|---|
| VM running tetapi SSH gagal | Tunggu boot; periksa NIC/IP dan console; jangan hapus known_hosts sembarangan |
| Windows meminta password | Gunakan akun console pada kartu lokal; autologon sengaja dinonaktifkan |
| Dashboard tidak terbuka | Periksa VM-ADMIN, service, port 5000 dari host dan root CA; gunakan HTTPS |
| TOTP ditolak | Periksa waktu HP/VM, gunakan kode baru, tunggu lockout bila tercapai |
| CA/Server tidak tersedia | Periksa service, waktu, HTTPS antarlayanan dan log unit; jangan menganggap peer pasti mati/aktif |
| Login karyawan gagal | Pastikan memakai akun VPN yang tepat, akun aktif, password benar; bukan akun console/admin |
| Session expired | Login karyawan ulang kemudian restart/connect; renewal tidak memperpanjang delapan jam |
| Certificate/key mismatch | Cocokkan device ID dan sertifikat dengan CSR asli; jangan menyalin key client lain |
| Tunnel config exists | Pastikan proses lama berhenti, inspect interface/service; simpan config sebelum pemulihan oleh teknisi |
| Windows meminta elevation | Buka PowerShell Run as administrator; hak akun saja belum selalu membuat terminal elevated |
| Windows cleanup timeout | Inspect service WireGuard khusus; config sengaja dipertahankan; jangan hapus semua direktori client |
| Handshake/ping gagal | Periksa peer, UDP 51820, endpoint, alamat.2/.4, firewall wg0 dan trust; jangan tambah peer manual |
| registered tetapi peer tidak aktif | Login dan jalankan connect; registrasi saja memang belum membuka akses |
| revoking belum selesai | Periksa CA/server kemudian retry workflow pada identitas yang sama |
| Arsip melebihi batas | Perkecil tanggal/filter, lalu buat beberapa snapshot |
| Host reboot mendadak | Periksa state/log aktual sebelum resume; log IN_PROGRESS bukan PASS |
| CRL counter kosong setelah shutdown | Hentikan perubahan CA, backup, eskalasi ke teknisi; jangan init CA atau rollback index |

Untuk diagnosis layanan Ubuntu, gunakan `sudo journalctl -u NAMA_UNIT -n 50
--no-pager`. Tinjau hasil secara privat sebelum menyalin ke laporan. Pemulihan
counter CA15 Oktober menjaga signature, monotonic counter dan seluruh revocation;
ini tindakan teknisi berdasarkan bukti, bukan perintah rutin pengguna.

## 14. Bukti yang tersedia dan pekerjaan berikutnya

| Bukti historis | Status yang dapat diklaim |
|---|---|
| Source0.1.8 commit 78ff14e, CI 38692866340 | Linux3.10/3.12 masing-masing163 PASS +1 SKIP; Windows 23 PASS |
| Guest Windows 15 Oktober | Login console/SSH, enrollment tanpa peer, sesi/proof invalid ditolak, admission, handshake, ping dan cleanup PASS |
| Dua client 15 Oktober | Ubuntu.2 dan Windows.4 aktif bersamaan, dua handshake dan ping PASS |
| Renewal otomatis Windows | Satu siklus normal sekitar 61,83 detik dan cleanup PASS; bukan soak test |
| Boot sesudah host restart | SSH pulih; tunnel idle tidak otomatis aktif; bukan uji reboot saat tunnel aktif |
| Penghapusan peer setelah lease habis | Bukti terakhir IN_PROGRESS; belum dinyatakan PASS |
| Revocation Windows, reboot saat tunnel aktif | Belum diverifikasi |
| Benchmark formal tiga konfigurasi ×10 | Belum selesai; jangan memakai pilot n=1 sebagai hasil statistik |
| Pemeriksaan17 Oktober | Enam VM shut off; dokumen disusun dari source/bukti, bukan uji live ulang |

Untuk proposal, uraikan enam node dan dua platform client secara eksplisit.
Pisahkan hasil admission, handshake dan trafik. S-01 menggunakan kredensial
**karyawan** yang dicuri pada perangkat tidak dipercaya. MTTD/MTTR aplikasi
mengikuti definisi yang terdokumentasi; MTTR berarti **Mean Time to Respond**.
Pemakaian sistem oleh user berarti akses lab yang diizinkan, bukan otomatis
memenuhi semua target penelitian. Lihat [matriks proposal](PROPOSAL_ALIGNMENT.md)
dan [catatan revisi proposal](SARAN_REVISI_PROPOSAL_2026-10-12.md).

## 15. Lembar kerja dan serah terima

Salin tabel ini ke catatan praktikum. Jangan mengisi password/token/private key.

| Isian | Hasil peserta |
|---|---|
| Tanggal/jam WIB dan operator | … |
| Versi/modul/commit yang digunakan | … |
| VM/client dan device ID | … |
| Status layanan dan waktu | … |
| Login admin/karyawan berhasil atau kendala | … |
| Status registry sebelum admission | … |
| Handshake, alamat tunnel dan hasil ping | … |
| Penghentian tunnel dan hasil cleanup | … |
| Filter audit, nama arsip dan checksum | … |
| Lokasi bukti privat | … |
| Masalah tersisa, status terakhir, langkah berikutnya | … |

Serah terima selesai bila pengguna dapat login, memakai tunnel sesuai haknya,
memverifikasi akses, dan menutup koneksi; admin dapat menelusuri/menyimpan audit;
teknisi memiliki backup serta catatan kendala. Kredensial diserahkan terpisah
melalui inventaris lokal, dengan folder0700 dan file0600.

Dokumen pendukung: [checkpoint](CHECKPOINT.md), [panduan Windows](WINDOWS_CLIENT.md),
[aktivitas admin](DASHBOARD_0.1.6.md), [akses karyawan](EMPLOYEE_ACCESS.md),
[deployment](DEPLOYMENT.md), [definisi metrik](RESPONSE_METRICS.md).

Untuk menghasilkan ulang HTML di HOST, renderer memakai paket `markdown-it-py`
yang sudah tersedia pada Python sistem di komputer ini:

```bash
python3 scripts/render_module.py docs/MODUL_PENGGUNAAN_VANGUARD.md \
  docs/MODUL_PENGGUNAAN_VANGUARD.html
```

HTML tidak memuat script, font eksternal atau kredensial. Buka di browser dan
pilih Ctrl+P → Simpan sebagai PDF → A4 untuk salinan cetak.

### 15.1 VanGuard0.1.9: logout, status dan penggantian identitas

Paket **0.1.9** dari branch `hardening/2026-10-18-resilience` sudah dipasang pada
lima Ubuntu dan satu Windows20 Oktober, dengan backup serta verifikasi identitas.
Bukti tiap skenario dibedakan dalam [matriks validasi](VALIDASI_ROLLOUT_2026-10-20.md).
Periksa [checkpoint](CHECKPOINT.md) untuk status VM dan pekerjaan lanjutan.

Pembaruan21 Oktober: CA/server/admin sudah memakai0.1.11, dengan pemeriksaan
readiness berbatas waktu dan pengurangan penulisan ulang file CA yang identik.
Client Ubuntu/attacker/Windows tetap0.1.9. Setelah patch kapasitas unit CA,
93pemeriksaan HTTPS penutup berhasil; pemantauan dengan tambahan beban juga
lulus. Sampel bukan jaminan semua beban: periksa dependensi jika503 menetap dan
jangan menganggap liveness sebagai bukti seluruh layanan siap.
Unit layanan CA juga memakai satu worker dan delapan thread sejak21 Oktober.
Perubahan ini memberi kapasitas untuk pemeriksaan dependensi paralel dan fetch
CRL daemon; batas waktu dan penolakan ketika pemeriksaan gagal tetap berlaku.
Kapasitas ini tidak menjamin layanan siap pada semua beban. Perubahan unit perlu
restart layanan terencana setelah backup dan pemeriksaan peer, bukan enrollment
ulang atau penggantian CA. Rinciannya ada pada [catatan kapasitas HTTPS CA](CA_SERVICE_CAPACITY.md).

Penggantian paket layanan tidak memperbarui sertifikat dan tidak membutuhkan
ulang enrollment. Status rollout, hasil HTTPS dan batas bukti tersedia pada
[catatan readiness dan penyimpanan CA](READINESS_0.1.10.md).

Matriks VM Ubuntu dan Windows sudah menguji renewal, expiry, logout bersamaan
renewal, reboot aktif, pencabutan yang memutus TCP aktif dan penggantian identitas.
Semua akun/identitas disposable dinonaktifkan/dicabut setelah tes; demo HTTP
sementara sudah dihentikan, sehingga hasil uji bukan aplikasi bisnis yang selalu
tersedia. Readiness CA dapat sementara503 ketika lock sedang dipakai transaksi:
tunggu lalu periksa kembali, dan jangan mengabaikan503 yang terus berulang.
Healthz200 hanya membuktikan proses hidup. Jika cleanup Windows timeout, jangan
hapus config sampai ownership dan penghentian service benar-benar terkonfirmasi.
Power-loss media CA dan seluruh jenis kegagalan OS belum dibuktikan oleh matriks.

Karyawan dapat menjalankan `vanguard-client logout` pada Ubuntu, atau
`python -m vanguard.client logout` pada Windows dengan virtualenv dan direktori
identitas yang sama seperti login. Keberhasilan berarti server mengonfirmasi
pencabutan token yang dipakai beserta challenge dan akses terkait. Sesi lain
tetap berlaku. Hentikan proses connect dengan Ctrl+C untuk cleanup lokal segera.
Jika server tidak terjangkau, pesan menyatakan pencabutan **belum terkonfirmasi**;
token lokal dipertahankan agar bisa retry. Jangan mengartikan penutupan terminal
atau hilangnya file lokal sebagai konfirmasi logout server.

Admin membaca status registry, lease, peer, handshake dan byte RX/TX secara
terpisah. “Peer terpasang” belum membuktikan handshake atau akses aplikasi.
“Tidak diketahui” berarti pemeriksaan gagal. Timestamp handshake memakai WIB;
byte transfer adalah total, bukan kecepatan saat ini. `/healthz` menunjukkan
proses hidup, sedangkan `/readyz` memeriksa dependensi tanpa menerbitkan
sertifikat/CRL atau menambah peer.

Peringatan sertifikat muncul tujuh hari sebelum habis. Renewal koneksi hanya
memperbarui lease, bukan sertifikat. Untuk penggantian, admin mencabut identitas
lama sampai status `revoked`. Karyawan membuat ID dan kedua key baru di folder
baru, tetap memakai IP tunnel miliknya. Admin mengunggah request baru melalui
form penggantian di riwayat perangkat. Akun/IP diwariskan; binding dan bukti
identitas lama tetap tersimpan. Unduh bundle baru dan lakukan admission seperti
biasa. Jangan menimpa direktori/key lama sebelum prosedur pemulihan selesai.

Halaman **Penyimpanan operasional** (`/operations`) memperlihatkan ukuran database,
jumlah audit, pertumbuhan dan ruang disk. Tidak ada penghapusan histori otomatis.
Gate aplikasi uji internal TCP8082 sudah dipasang dengan default-deny. Server
demo pada pengujian memakai service sementara; keberhasilan tes tidak berarti
ada aplikasi bisnis permanen yang otomatis tersedia. Akses memerlukan kebijakan
eksplisit pasangan identitas/akun, resource, alamat, protokol dan port;
pendaftaran perangkat saja tidak memberi grant. Rincian backup, rollout, recovery
CA tanpa rollback index/CRL dan matriks pengujian ada pada
[panduan hardening 0.1.9](HARDENING_0.1.9.md).

### 15.2 Windows lambat terbuka

Konfigurasi VM Windows diperbaiki19 Oktober dengan clock/timer Hyper-V.
Secure Boot,TPM dan file identitas tetap terverifikasi. Pada pengukuran tunggal
sesudah perubahan, SSH siap27,49detik; ini bukan jaminan waktu desktop/VPN.
Tunggu tampilan login merespons sebelum memasukkan password. Jangan mengulang
instalasi atau reset password hanya karena layar belum merespons.

Pengujian clock native menunjukkan perbaikan, tetapi waktu tunggu login,
aktivitas startup dan beban disk/RAM host juga berpengaruh. Lima Ubuntu tetap
ada; nyalakan hanya layanan yang diperlukan secara bertahap. Rincian bukti,
keterbatasan dan pemulihan XML ada di [panduan Windows](WINDOWS_CLIENT.md).

### 15.3 Pilot PC Windows LAN dan laptop Windows Wi-Fi

**Tambahan22 Oktober2026: kandidat lokal0.1.12, belum dipasang atau dipublikasikan.**
Enam VM lab tetap ada; PC dan laptop fisik menggunakan identitas tambahan. Jangan
memakai bootstrap VM pada perangkat fisik atau membuat ulang CA. Panduan langkah
terperinci, rencana rule/route, paket dan matriks hasil tersedia pada
[pilot endpoint Windows](ENDPOINT_WINDOWS_PILOT.md). Tahap ini hanya persiapan;
master prompt terbaru melarang perubahan jaringan/VM/perangkat dan push.

Rencana router192.168.50.1/24 menghubungkan host Linux .50.10 melalui Ethernet,
PC .50.20 melalui LAN, laptop .50.30 melalui Wi-Fi. Backend tetap .100/24, tunnel
10.8/24. Endpoint memakai route /32 menuju server .100.20 melalui host .50.10;
host/libvirt/VM firewall harus ditinjau bersama. Hanya HTTPS8081 dan WG UDP51820,
bukan akses langsung aplikasi8082/CA/admin. IP tunnel .5/.6 baru usulan; admin
harus memastikan registry sebelum alokasi, jangan menyimpulkan kosong dari ping.

Urutan pilot setelah izin penerapan dan verifikasi native:

1. Operator menyiapkan jaringan, prasyarat Windows11x64/Python3.13x64/WireGuard,
   backup dan paket offline pada path admin-only. Cocokkan hash manifest dan
   publisher runtime lewat kanal tepercaya. Paket unsigned belum siap distribusi.
2. Install-VanGuard.bat menjalankan installer PowerShell/UAC. Aplikasi terpasang
   belum berarti enrolled/login/VPN. Installer tidak mengubah NIC, membuat key,
   menambah peer atau mengunduh runtime otomatis.
3. Launcher `VanGuard.ps1 -Action configure` meminta profil/root tepercaya beserta
   fingerprint root dan public key server. Config tidak ditimpa. `-Action init`
   meminta ID/IP yang dialokasikan admin; kedua private key dibuat pada endpoint.
4. Kirim request.json ke admin, daftar dan bind akun. Bundle publik hasil admin
   diimpor dengan `-Action import-bundle`, cocok dengan root/profil/key/request
   asli. Tidak ada private key dikirim balik atau akses otomatis saat import.
5. `-Action diagnose` memeriksa readiness HTTPS; UDP/aplikasi masih unknown.
   `-Action login` meminta password tersembunyi, lalu `-Action connect` menjalankan
   preflight, admission dan renewal. Terminal pemilik harus tetap terbuka.
6. Admin memeriksa lease/peer/handshake/transfer dan memberi grant explicit
   internal-demo TCP8082. Buktikan HTTP lewat10.8.0.1:8082 berhasil dengan grant
   serta ditolak tanpa grant/LAN langsung. Ping bukan syarat pilot fisik.
7. Ulangi pada laptop Wi-Fi, kemudian kedua endpoint bersamaan. Logout/revoke
   satu endpoint harus memutus aksesnya tanpa memutus yang lain. Catat renewal,
   Wi-Fi putus/sambung, active TCP revocation, expiry/reboot dan cleanup sebenarnya.
8. Ctrl+C atau `-Action disconnect` meminta cleanup lokal; `-Action logout`
   mencabut sesi server. Jika server tidak terjangkau, revocation belum
   terkonfirmasi. Jangan menghapus config jika ownership/tunnel down belum pasti.
9. Setelah pilot, cabut identitas/sesi/grant disposable, hentikan demo sementara
   dan pulihkan hanya route/rule pilot. Preserve identitas utama dan histori CA.

Runtime berada di Program Files/VanGuardEndpoint, sedangkan identity/config/log
terpisah di Program Files/VanGuardEndpointData dengan akses SYSTEM/Administrators.
Reinstall/repair membangun runtime baru tanpa rotasi key; uninstall mempertahankan
data serta Python/WireGuard bersama. Pemulihan parsial otomatis, shortcut GUI,
ARM64 dan signing organisasi belum tersedia. Seluruh pengujian installer native
serta pilot PC/laptop **BELUM_DIJALANKAN**. Tes Linux/mocks bukan bukti ACL Windows,
handshake fisik atau rollout. WIN-CLEANUP-02 tetap perlu uji target terpisah.
