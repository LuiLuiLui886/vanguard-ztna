# Deployment Ubuntu Server 22.04 — lima VM

Panduan ini untuk pemasangan baru dan pemeliharaan oleh operator. Untuk memakai
lab yang sudah terpasang, ikuti [tutorial penggunaan](TUTORIAL_PENGGUNAAN.md);
jangan membuat ulang CA/identitas utama pada lab tersebut.

## 1. Prasyarat dan akses

Topologi: CA `.10`, SERVER `.20`, CLIENT `.30`, ADMIN `.40`, ATTACKER `.50` pada
`192.168.100.0/24`. Sinkronkan waktu semua VM (`timedatectl status`): waktu digunakan untuk
sertifikat, CRL, challenge, lease, dan TOTP. Jalur control-plane HTTPS harus dapat diakses
sebelum tunnel WireGuard terbentuk.

Siapkan SSH key/agent dan known_hosts dengan fingerprint yang diverifikasi. Installer
memerlukan root pada VM tujuan. `sudo -n true` digunakan preflight untuk deployment tanpa
interaksi; jika memakai sudo interaktif, jalankan installer langsung di console/SSH.
Jangan menyimpan password/private key di inventory atau repositori.

Salin inventory contoh ke lokasi privat, sesuaikan username/alias/port (jump host dapat
didefinisikan dengan ProxyJump di `~/.ssh/config`), lalu:

```bash
python3 scripts/ssh_preflight.py /path/to/inventory.json
```

Preflight hanya membaca hostname, user, versi OS, dan kemampuan sudo. Timeout menunjukkan
masalah reachability sebelum autentikasi. Host key yang belum dikenal perlu diverifikasi
operator; jangan menonaktifkan StrictHostKeyChecking.

## 2. Instal paket pada setiap VM

Salin source project ke masing-masing VM melalui SSH/SCP tanpa `.venv`, `state`, atau
secret. Jika memakai arsip hasil build, ekstrak ke direktori kerja, lalu:

```bash
sudo bash deploy/install.sh ca       # hanya VM-CA
sudo bash deploy/install.sh server   # hanya VM-SERVER
sudo bash deploy/install.sh client   # hanya VM-CLIENT
sudo bash deploy/install.sh admin    # hanya VM-ADMIN
sudo bash deploy/install.sh attacker # hanya VM-ATTACKER
```

Pilih satu role sesuai VM, bukan menjalankan lima perintah pada satu VM. Installer memeriksa
Ubuntu 22.04 dan IP lokal. Paket Python dipasang ke `/opt/vanguard/venv`; versi dependency
dikunci dalam `deploy/constraints.txt`. Installer **belum menyalakan service**.

Pada VM-SERVER, installer membuat `/etc/wireguard/wg0.conf` (0700 directory, 0600 file):
Address `10.8.0.1/24`, UDP `51820`, private key unik, **tanpa `[Peer]` dan SaveConfig**.
Public key tersedia di `/etc/vanguard/server-wg.pub`. Jika wg0.conf sudah ada, installer
mempertahankannya: periksa bahwa alamat/port benar dan hapus konfigurasi peer lama sebelum
memulai service. Tidak diperlukan IP forwarding/NAT untuk akses langsung client → server
tunnel. Jangan menambahkan peer statis sebagai langkah registrasi.

## 3. Buat CA dan sertifikat HTTPS

Di VM-CA:

```bash
sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca init
sudo install -m 0644 /var/lib/vanguard/ca/root.crt /etc/vanguard/root.crt
openssl x509 -in /etc/vanguard/root.crt -noout -fingerprint -sha256
```

Init menolak overwrite CA yang sudah ada. Simpan fingerprint Root CA melalui jalur tepercaya.
Salin **root.crt saja** ke `/etc/vanguard/root.crt` pada empat VM lainnya, mode 0644;
cocokkan fingerprint. Root private key tetap di VM-CA.

Pada masing-masing VM CA, SERVER, ADMIN, buat key dan CSR HTTPS lokal:

```bash
sudo openssl req -new -newkey rsa:3072 -nodes \
  -keyout /etc/vanguard/tls.key -out /etc/vanguard/tls.csr \
  -subj '/CN=VanGuard Service'
sudo chown root:vanguard /etc/vanguard/tls.key
sudo chmod 0640 /etc/vanguard/tls.key
```

Salin CSR (tidak mengandung private key) ke VM-CA. Letakkan salinannya pada direktori
yang dapat dibaca akun vanguard, misalnya `/var/lib/vanguard/ca/requests/` dengan
owner vanguard. Tandatangani setiap CSR dengan IP yang sesuai:

```bash
sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca sign-tls \
  --csr /var/lib/vanguard/ca/requests/ca.csr --ip 192.168.100.10 \
  --out /var/lib/vanguard/ca/requests/ca.crt
sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca sign-tls \
  --csr /var/lib/vanguard/ca/requests/server.csr --ip 192.168.100.20 \
  --out /var/lib/vanguard/ca/requests/server.crt
sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca sign-tls \
  --csr /var/lib/vanguard/ca/requests/admin.csr --ip 192.168.100.40 \
  --out /var/lib/vanguard/ca/requests/admin.crt
```

Kembalikan sertifikat ke `/etc/vanguard/tls.crt` pada VM yang bersangkutan, mode 0644.
Verifikasi dengan `openssl verify -CAfile /etc/vanguard/root.crt /etc/vanguard/tls.crt`.
Private key service tidak perlu dikirim ke CA. Import root.crt ke trust store browser
administrator untuk membuka dashboard tanpa mengabaikan verifikasi TLS.

## 4. Token dan akun administrator

Template `/etc/vanguard/{ca,server,admin}.env` sengaja memiliki secret kosong.
Buat dua token independen dan session secret menggunakan `openssl rand -hex 32`, lalu
isi melalui editor root (`sudoedit`). Hindari meletakkan secret literal pada history shell.

| Secret | Dipasang pada |
|---|---|
| `VANGUARD_CA_TOKEN` | ca.env pada CA; admin.env pada ADMIN |
| `VANGUARD_SERVER_TOKEN` | server.env pada SERVER; admin.env pada ADMIN |
| `VANGUARD_SESSION_SECRET` | admin.env pada ADMIN, nilai independen |

Gunakan transfer SSH tepercaya bila perlu dan pertahankan env file `root:root`, mode 0600.
systemd membaca EnvironmentFile sebelum menurunkan privilege service. Jangan menggunakan
token yang sama untuk CA/server atau menjadikan password login sebagai token.

Di VM-ADMIN, buat akun dengan prompt interaktif:

```bash
sudo -u vanguard /opt/vanguard/venv/bin/vanguard-admin --username admin
```

Password minimal 12 karakter, diketik dua kali. URI TOTP ditampilkan **hanya di terminal
operator** untuk dimasukkan ke aplikasi authenticator; konfirmasi dengan kode aktif.
Jangan menaruh URI tersebut pada laporan/log publik.

## 5. Jalur jaringan

Atur firewall hypervisor/VM sesuai matriks ini. Installer tidak mengubah firewall atau SSH.
Pertahankan akses SSH manajemen yang sudah ada sebelum mengaktifkan kebijakan default-deny.

| Tujuan | Sumber | Port/fungsi |
|---|---|---|
| CA `.10` | SERVER `.20`, ADMIN `.40` | TCP 8080 HTTPS |
| SERVER `.20` | CLIENT `.30`, ADMIN `.40`, ATTACKER `.50` | TCP 8081 HTTPS |
| SERVER `.20` | CLIENT `.30`, ATTACKER `.50` | UDP 51820 |
| ADMIN `.40` | Workstation administrator yang ditentukan operator | TCP 5000 HTTPS |
| Semua VM | Jalur administrasi operator | SSH sesuai konfigurasi |
| Server `10.8.0.1` via wg0 | Client `10.8.0.2` | ICMP atau layanan demo yang ditetapkan |

ATTACKER sengaja diizinkan menjangkau endpoint admission dan UDP WireGuard agar penolakan
identitas dapat diuji. CA management tetap membutuhkan bearer token meskipun akses jaringan
dibatasi. Protected service untuk demonstrasi harus bind ke `10.8.0.1` atau dibatasi firewall;
service yang juga terbuka pada LAN dapat diakses tanpa melewati tunnel.

## 6. Jalankan layanan

VM-CA:

```bash
sudo systemctl enable --now vanguard-ca
```

VM-SERVER:

```bash
sudo systemctl enable wg-quick@wg0 vanguard-daemon vanguard-server
sudo systemctl start vanguard-server
sudo wg show wg0 peers
```

Output peers harus kosong. Dependensi unit menyalakan wg0 dan daemon sebelum API.
CA harus terjangkau agar admission berhasil. VM-ADMIN:

```bash
sudo systemctl enable --now vanguard-admin
```

Periksa `systemctl status` dan `journalctl -u <service>`. Jangan memakai Flask development
server untuk deployment. Unit menggunakan Gunicorn satu worker/empat thread, HTTPS, dan
permission terbatas. Directory server dimiliki root; CA/admin dimiliki user vanguard.

## 7. Enrollment dan koneksi client

Di VM-CLIENT:

```bash
sudo /opt/vanguard/venv/bin/vanguard-client init --device-id vm-client
```

Output menunjukkan `/var/lib/vanguard/client/request.json`. Salin file tersebut ke operator
admin (CSR dan public key saja), lalu login ke `https://192.168.100.40:5000`.
Pada **Akun karyawan**, buat akun VPN dengan password awal minimal 12 karakter.
Unggah request pada **Registrasi perangkat**, isi metadata dan pilih akun karyawan
tersebut sebelum menerbitkan sertifikat/binding. Unduh sertifikat dan pasang pada client:

```bash
sudo install -m 0600 /path/to/vm-client.crt /var/lib/vanguard/client/device.crt
```

Pada instalasi baru tanpa client lain, pastikan `wg show wg0 peers` pada SERVER
masih kosong setelah registrasi. Pada lab aktif, yang harus belum ada adalah
peer perangkat yang baru didaftarkan; peer client lain boleh tetap ada.
Login karyawan di CLIENT memakai username yang baru dibuat (ganti `USERNAME_KARYAWAN`):

```bash
sudo /opt/vanguard/venv/bin/vanguard-client login --username USERNAME_KARYAWAN
```

Password diminta secara interaktif. Sesi berlaku delapan jam; boot/renewal tidak
memperpanjangnya. Detail ada di [panduan akun](EMPLOYEE_ACCESS.md).
Ambil public key server dari `/etc/vanguard/server-wg.pub` di SERVER melalui jalur SSH tepercaya.
Di CLIENT (gantikan placeholder dengan public key, bukan private key):

```bash
sudo /opt/vanguard/venv/bin/vanguard-client connect --server-key 'PUBLIC_KEY_SERVER'
```

Jangan jalankan koneksi foreground bersamaan dengan service `vanguard-client`.
Proses berjalan foreground, admission lebih dahulu lalu `wg-quick up`, dan memperbarui
admission otomatis. Pada terminal lain, `ping -c 3 10.8.0.1` dan `sudo wg show wg0`
untuk membuktikan handshake. Ctrl-C/SIGTERM menurunkan interface client. File wg0.conf
sementara dilindungi mode 0600 dan dihapus saat shutdown normal.

Jika proses terbunuh paksa, periksa/down interface sebelum menghapus wg0.conf yang tersisa;
CLI sengaja menolak overwrite. CLI `admit` tersedia untuk uji admission tanpa menaikkan
tunnel, dan hanya memberi lease sementara yang tetap akan diperiksa daemon.

## 8. Pencabutan, recovery, dan node attacker

Klik **Cabut akses & sertifikat** di dashboard. Pastikan peer hilang di SERVER, ping berhenti,
dan admission baru ditolak. Jika status `revoking`, selesaikan dependency yang offline dan
gunakan **Ulangi workflow**. Identity yang dicabut tidak dapat diaktifkan kembali: buat
device ID dan keypair baru; tunnel IP dapat digunakan ulang setelah identitas lama disabled.

Pada VM-ATTACKER:

```bash
/opt/vanguard/venv/bin/python /opt/vanguard/attacker_checks.py
```

Script hanya mengirim tiga request negatif; hasil jaringan gagal diberi label UNVERIFIED,
bukan dianggap sebagai keberhasilan keamanan.

Jika daemon berhenti, unit menurunkan wg0 dan API ikut berhenti. Setelah penyebabnya diperbaiki:

```bash
sudo systemctl reset-failed vanguard-daemon vanguard-server wg-quick@wg0
sudo systemctl start vanguard-server
```

Client perlu admission baru. Restart daemon sengaja memutus akses; lakukan di waktu uji
yang sesuai. Jangan menambahkan peer manual untuk memulihkan akses.

## 9. Backup, update, dan rollback

Sebelum update, hentikan service terkait; simpan salinan source versi sebelumnya dan backup
state secara privat. CA: seluruh `/var/lib/vanguard/ca`; server: SQLite registry; admin:
SQLite users/sessions/workflows; client: identitas dan sertifikat; semua VM: config yang relevan
di `/etc/vanguard`, serta `/etc/wireguard` pada server. Pertahankan owner dan permission.

Versi 0.1.3 menambahkan tabel akun/sesi/binding karyawan melalui inisialisasi schema;
data registry/CA lama dipertahankan. Perangkat lama tanpa binding akun gagal admission.
Sebelum menyalakan client, buat akun karyawan eksplisit, tautkan perangkat dan login
sesuai [EMPLOYEE_ACCESS.md](EMPLOYEE_ACCESS.md). Jangan menjalankan versi berbeda
terhadap database yang tidak kompatibel. Rollback 0.1.2 juga menghilangkan kewajiban
login karyawan: bukan recovery transparan; pertahankan layanan berhenti jika
semantik otorisasi versi lama tidak boleh kembali berlaku.
Rollback paket/config tidak boleh mengembalikan index CA/CRL lama yang menghidupkan kembali
sertifikat dicabut. Hentikan admission dan pulihkan state yang konsisten sebelum membuka akses.

## Status lingkungan saat pengembangan

Pembaruan 8 Oktober 2026: firewall guest tersedia melalui `deploy/firewall.py`
dan sudah diterapkan pada lab ini. Skrip `scripts/harden_lab.py` mendeteksi IP
manajemen dari koneksi SSH, memasang hanya tabel nftables `inet vanguard`, dan
mengonfirmasi koneksi SSH baru sebelum membatalkan timer rollback. Instalasi paket
aplikasi tetap tidak otomatis memasang firewall. Status/bukti terbaru harus dibaca
di [CHECKPOINT.md](CHECKPOINT.md).

Pemeriksaan baca-saja saat client utama aktif:

```bash
.venv/bin/python scripts/health_lab.py state/lab/inventory.json \
  --state state/deployment/health-run-baru --samples 1
```

Gunakan direktori bukti baru untuk setiap run. Untuk observasi berulang, tambahkan
`--samples 51 --interval 10`; skrip memeriksa layanan, lease, binding allowed IP,
ping, dan removal selama observasi. Kegagalan atau interupsi tercatat pada JSON.
Skrip tidak menambah peer dan tidak mengubah konfigurasi VM.

Pada 24 September 2026, kelima VM Ubuntu 22.04 sudah berjalan di KVM/libvirt melalui
bridge `virbr-vg`. Layanan VanGuard sudah terpasang dan client utama berhasil admission,
handshake, serta ping tunnel. Lihat [LAB_ACCESS.md](LAB_ACCESS.md) untuk akses VM/dashboard
dan [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) untuk bukti serta batas pengujian.

## Upgrade instrumentasi 0.1.4

Versi 0.1.4 menambah audit timing penolakan dan header korelasi challenge/verify;
tidak mengubah schema database, CA/key, binding akun atau kontrak body API.
Hentikan layanan terkait untuk backup konsisten sebelum mengganti wheel, lalu
nyalakan CA/server/admin dan client yang sudah memiliki sesi valid. Tidak perlu
reenrollment atau membuat akun baru. Jika sesi delapan jam expired, lakukan login
ulang sesuai panduan karyawan sebelum menganggap kegagalan sebagai regresi upgrade.

Simpan paket 0.1.3 dan backup state privat. Pemulihan paket tidak boleh mengembalikan
index CA/CRL lama. Pemeriksaan setelah pemasangan mencakup hash source/config/key,
health/renewal, dan korelasi audit hasil penolakan pada server yang sebenarnya.

## Upgrade dashboard 0.1.5

Backup konsisten lima role sebelum mengganti wheel. Migrasi admin menambah tabel
audit dan kolom alasan/waktu pencabutan, tanpa mengganti identitas atau mengarang
histori sebelum upgrade. Tidak perlu reenrollment. Sesudah startup, periksa health
dan bundle/history/revoke beralasan melalui identitas sementara seperti
[panduan dashboard](DASHBOARD_0.1.5.md). Pertahankan CA index/CRL terbaru saat recovery.

## Upgrade aktivitas administrator 0.1.6

Versi ini memperluas skema audit dan menambah tabel snapshot arsip pada `admin.db`;
schema baru dibuat aditif, log lama dipertahankan. Sebelum update, hentikan service
dashboard lalu buat backup database admin dengan [prosedur backup dashboard](#upgrade-dashboard-015)
atau backup konsisten lima role. Pasang wheel 0.1.6 dan mulai kembali dashboard;
tidak perlu mengubah CA, client, key, atau binding.

Sesudah startup, login admin dan periksa **Aktivitas admin**, filter WIB, pagination,
pembuatan arsip, daftar arsip dan unduhan. Cocokkan checksum SHA-256. File download
ZIP harus disimpan privat di workstation; jangan di GitHub. Arsip sumber tidak
dihapus saat export. Backup rutin tetap diperlukan karena arsip disimpan dalam
database admin VM. Upgrade tidak membuat catatan tindakan yang terjadi sebelum
audit 0.1.5 diaktifkan dan tidak memberi perlindungan terhadap administrator root
yang memodifikasi database secara langsung.
