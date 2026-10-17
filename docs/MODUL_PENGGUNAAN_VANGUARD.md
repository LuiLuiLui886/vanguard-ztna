# Modul lengkap penggunaan Sistem VanGuard

Edisi 17 Oktober 2026 · Panduan teknisi, administrator, dan karyawan

Modul ini menjelaskan persiapan, pemasangan, pendaftaran pengguna/perangkat,
pemakaian VPN Ubuntu dan Windows, audit, pengujian, serta penghentian sistem.
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

### 5.3 Buat CA, trust dan sertifikat HTTPS

**VM-CA baru**:

```bash
sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca init
sudo install -m 0644 /var/lib/vanguard/ca/root.crt /etc/vanguard/root.crt
openssl x509 -in /etc/vanguard/root.crt -noout -fingerprint -sha256
```

Catat fingerprint. Salin hanya root.crt ke `/etc/vanguard/root.crt` pada Ubuntu
lain dan cocokkan fingerprint. Root private key tetap di CA.

Pada **masing-masing VM-CA, VM-SERVER, VM-ADMIN**, buat key HTTPS lokal:

```bash
sudo openssl req -new -newkey rsa:3072 -nodes \
  -keyout /etc/vanguard/tls.key -out /etc/vanguard/tls.csr \
  -subj '/CN=VanGuard Service'
sudo chown root:vanguard /etc/vanguard/tls.key
sudo chmod 0640 /etc/vanguard/tls.key
```

Transfer CSR ke CA melalui SSH, dengan nama `ca.csr`, `server.csr`, `admin.csr`
di `/var/lib/vanguard/ca/requests/`; direktori/CSR harus dapat dibaca akun
service `vanguard`. Pada **VM-CA**, tandatangani sesuai IP:

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

Kembalikan sertifikat yang sesuai ke `/etc/vanguard/tls.crt` pada masing-masing
guest dengan mode0644. Pada setiap guest layanan, jalankan:

```bash
openssl verify -CAfile /etc/vanguard/root.crt /etc/vanguard/tls.crt
```

Target `OK`. Key HTTPS service tidak ditransfer ke CA. Simpan salinan root publik
di host untuk trust browser dan pemeriksaan HTTPS.

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
