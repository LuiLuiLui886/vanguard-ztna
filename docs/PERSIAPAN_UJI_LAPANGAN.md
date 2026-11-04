# Pelaksanaan uji lapangan VanGuard — lab kampus

Edisi 4 November 2026. **Satu dokumen kerja untuk dibawa ke lapangan.**
Target: komputer Windows kampus yang sudah digunakan, router khusus
`192.168.50.0/24`, dan backend VM yang sudah terpasang pada laptop Linux.
Dokumen ini menyiapkan pilot; **belum merupakan laporan keberhasilan di kampus**.

Source CA saat penyusunan: **0.1.17**; server/admin dan installer Windows:
**0.1.15**. Branch: `feature/2026-10-22-physical-endpoints`.
Uji VM Windows 10/11 dan backend terdahulu tidak menggantikan uji fisik berikut.

**Urutan:** persetujuan lab → inventaris/backup → router dan host → backend siap →
periksa Windows → install/configure → aktifkan lockdown bila dipilih → enrollment
→ login/connect → uji izin/pencabutan → pemulihan → serah terima hasil.

## 1. Tentukan ruang lingkup dan penanggung jawab

Isi sebelum berangkat; jangan menulis password atau token di dokumen ini.

| Data | Isian lapangan |
| --- | --- |
| Tanggal, ruang lab, jam mulai–selesai | … |
| Penanggung jawab lab / operator Linux / operator Windows | … |
| Komputer yang diizinkan untuk uji, memakai kode aset anonim | … |
| Mode yang akan diterima | Aplikasi internal / aplikasi + internet terkelola |
| Sumber internet router dan aturan penggunaan yang disetujui | … |
| Lokasi backup dan bukti privat, petugas pemulihan | … |
| Batas waktu pencabutan yang disepakati sebelum uji | … detik |
| Waktu penggunaan berkelanjutan yang disepakati | … menit; amati minimal dua renewal |

Mulai satu PC LAN, lanjut satu laptop Wi-Fi, kemudian keduanya bersamaan.
Jangan langsung memasang ke seluruh kelas. Uji pada OS yang memang digunakan lab;
Windows kosong bukan syarat awal pilot ini. Hasilnya nanti hanya berlaku untuk
build OS, kebijakan dan jaringan yang benar-benar diuji.

**Pemilihan mode:** mode aplikasi melindungi aplikasi internal tetapi tidak
memutus internet langsung. Jika tujuan penelitian mencakup blokir internet sebelum
admission dan setelah revoke, mode **internet terkelola wajib diuji**. Lulus mode
aplikasi saja tidak boleh dicatat sebagai lulus tujuan internet.

## 2. Perangkat, berkas dan akses yang harus dibawa

| Kebutuhan | Siapkan dan periksa |
| --- | --- |
| Laptop Linux backend | Charger, akses administrator host, libvirt/KVM, console VM dan ruang backup yang cukup |
| VM backend | CA, server dan admin beserta disk/konfigurasi existing; kelima Ubuntu dan VM Windows lama tetap disimpan |
| Router TP-Link khusus | Akses konfigurasi oleh petugas lab, adaptor daya, SSID uji dan akses WAN bila menguji internet |
| Koneksi fisik | Ethernet host→router, Ethernet PC→router, laptop→Wi-Fi router; kabel cadangan bila tersedia |
| Endpoint | Windows x64 yang memenuhi bagian 5; akun administrator lokal dan izin perubahan jaringan/firewall |
| Media transfer | USB atau media privat yang disetujui lab untuk request dan bundle saat internet diblok |
| Installer offline | `Setup-VanGuard-0.1.15.exe`, `SHA256SUMS`; ZIP template 0.1.15 bila perlu paket BAT |
| Bahan trust publik | `root.crt`, `profile.json`, fingerprint root dan public key WireGuard server terverifikasi |
| Akses aplikasi | Akun dashboard + authenticator TOTP; akun karyawan uji berbeda untuk tiap endpoint |
| Pemulihan | Backup konfigurasi host/router/endpoint dan backup backend konsisten, console lokal tetap tersedia |
| Bukti | Folder privat per sesi, jam tersinkron, formulir hasil pada bagian 11 |

Unduh dari [folder downloads](../downloads/README.md) pada branch di atas,
**Download raw file**. Simpan file dokumen ini juga untuk dibaca offline.

| Berkas terbaru | SHA-256 saat dokumen disusun |
| --- | --- |
| `Setup-VanGuard-0.1.15.exe` | `01bdfd418cf8ab97543b172d7abaedb1baba507ac215900f895eb18ced591031` |
| `vanguard-windows10-11-setup-template-0.1.15-20261102.zip` | `c4c8045d1f1d8bdc7535a58d2f28fff4871ecffb3a5cb112a76b709532a3c4e7` |

Pastikan hash cocok dengan sumber admin tepercaya, bukan hanya file checksum
yang diterima bersama unduhan. Paket sudah membawa Python/WireGuard/dependensi.
Jangan membawa root private key, token API, password atau TOTP seed di folder
instalasi pengguna. Inventaris kredensial tetap privat pada komputer pengelola;
repo GitHub hanya menerima dokumentasi yang sudah disanitasi.

Sebelum perjalanan, periksa `df -h` dan `free -h`. Catatan terakhir host sekitar
5,4 GiB ruang bebas; ini **bukan jaminan cukup** untuk backup dan pertumbuhan disk.
Hitung kebutuhan nyata sebelum sesi. Gunakan PC fisik sebagai endpoint; tidak
perlu menjalankan VM Windows tambahan bersamaan jika sumber daya host terbatas.

## 3. Rencana jaringan yang harus dicocokkan di lokasi

```text
WAN yang disetujui kampus
          |
Router khusus 192.168.50.1/24
          |-- Ethernet: host Linux 192.168.50.10
          |                 |-- virbr-vg 192.168.100.1/24
          |                      |-- CA     192.168.100.10
          |                      |-- SERVER 192.168.100.20 (WG 10.8.0.1)
          |                      |-- ADMIN  192.168.100.40
          |-- Ethernet: PC Windows 192.168.50.20
          `-- Wi-Fi: laptop Windows 192.168.50.30
```

| Alokasi | Nilai rencana dan ketentuan |
| --- | --- |
| LAN router | `192.168.50.1`, mask `255.255.255.0` |
| Host / PC / laptop | `.50.10` / `.50.20` / `.50.30`; reservasi DHCP atau alamat statis di luar pool DHCP |
| Default gateway endpoint | `.50.1`; koneksi tunnel dibuat oleh VanGuard, jangan mengganti default gateway secara manual ke VM |
| Route khusus endpoint | `192.168.100.20/32` melalui `.50.10` |
| Route balik VM server | Tujuan `.50.20/.50.30` harus melalui host `.100.1` |
| Tunnel endpoint baru | Usulan `.5` dan `.6` pada `10.8.0.0/24`, **hanya setelah registry diperiksa** |

Alamat `10.8.0.2/.3/.4` sudah dialokasikan/dicadangkan; IP LAN berbeda dari IP
tunnel. Gunakan device ID unik dan kedua key baru untuk setiap PC.

**Petugas router:** backup konfigurasi, gunakan LAN `/24` di atas, pastikan
alamat reservasi tidak bentrok dengan pool DHCP. Hindari subnet WAN yang sama
dengan LAN. PC dan laptop harus berada pada SSID/LAN uji yang sama; guest/AP
isolation yang memutus laptop dari host akan menggagalkan jalur ini. Jangan
mengubah jaringan utama kampus, mengaktifkan DMZ atau membuka port dari WAN.
Nama menu tergantung model/firmware TP-Link; catat model yang benar di formulir.
Router tidak mengeluarkan sertifikat dan bukan pelaksana pencabutan VanGuard.

**Petugas endpoint:** simpan konfigurasi IP/DNS lama, lalu gunakan reservasi DHCP
atau isi IPv4 sesuai tabel melalui pengaturan adapter Windows. Cek IP aktual,
mask, gateway, DNS dan SSID. Matikan koneksi alternatif untuk pengujian terkontrol
(hotspot/tethering/VPN lain) sesuai izin; catat perubahan untuk dipulihkan.

### 3.1 Host Linux: pemeriksaan dan gerbang kesiapan jaringan

Jalankan di **host**, bukan di VM; simpan hasil secara privat:

```bash
ip -br -4 address
ip -4 route
sysctl net.ipv4.ip_forward
virsh -c qemu:///system net-list --all
virsh -c qemu:///system net-dumpxml vanguard
sudo nft list ruleset
sudo iptables-save
```

Host Ethernet harus `.50.10/24`, bridge `virbr-vg` harus `.100.1/24`.
Atur IP melalui pengelola jaringan host yang sudah digunakan; jangan mengganti
konfigurasi interface lain atau menambahkan alamat yang sudah dipakai.

**Firewall host/libvirt belum mempunyai installer universal pada proyek ini.**
Operator wajib mengidentifikasi interface Ethernet, backend nft/iptables, chain
libvirt, forwarding dan NAT aktual sebelum menerapkan aturan. Matriks minimum:

| Sumber → tujuan | Izin yang harus dibuktikan |
| --- | --- |
| `.50.20/.50.30` → `.100.20` | TCP 8081 untuk admission HTTPS dan UDP 51820 untuk WireGuard, termasuk balasannya |
| Endpoint → CA `.100.10`, admin `.100.40`, SSH backend | Ditolak melalui jalur endpoint; management tetap lewat host/operator |
| Endpoint LAN → demo TCP 8082 | Ditolak; aplikasi hanya melalui tunnel dengan grant |
| Server gateway → WAN melalui host/router | Bekerja untuk mode internet; jalur balik/NAT benar |

Siapkan backup aturan, akses console, cara membatalkan **perubahan pilot saja**,
dan jadwal pemulihan sebelum mengubah jaringan. `ip_forward=1` tidak membuktikan
forwarding berhasil; `accept` pada satu chain bisa tetap ditolak chain lain.
Jangan memakai `nft flush ruleset`, membuka semua forwarding, atau memasang NAT
masquerade umum endpoint→VM untuk menyembunyikan sumber. Jangan memulihkan seluruh
snapshot firewall lama jika aturan lain telah berubah sejak backup.

Pemeriksa tambahan dari root repo, setelah konfigurasi operator:

```bash
python3 scripts/pilot_preflight.py
```

Exit **2** memang normal untuk alat ini: masih memerlukan pemeriksaan manual
firewall/HTTPS/traffic. `MANUAL_REVIEW_REQUIRED` bukan kelulusan akhir. Jika belum
bisa membuktikan matriks di atas, **tunda instalasi/lockdown**, catat BLOCKED dan
selesaikan dengan petugas jaringan. Dokumen ini tidak menyatakan host sudah siap.

### 3.2 Tambahkan route pada Windows

PowerShell **Run as administrator** pada setiap endpoint:

```powershell
Get-NetIPConfiguration
Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '192.168.100.20/32' -ErrorAction SilentlyContinue
# Isi angka InterfaceIndex LAN/Wi-Fi yang sudah diperiksa di atas.
[int]$ifIndex = Read-Host 'InterfaceIndex adapter uji'
# Hanya bila route yang tepat belum ada:
New-NetRoute -DestinationPrefix '192.168.100.20/32' -InterfaceIndex $ifIndex `
  -NextHop '192.168.50.10' -PolicyStore ActiveStore
Test-NetConnection 192.168.100.20 -Port 8081
```

Catat apakah route dibuat oleh sesi ini. Jangan menimpa route yang berbeda tanpa
review. Route ActiveStore hilang setelah reboot; periksa/tambahkan kembali hanya
jika hilang. TCP sukses belum membuktikan TLS, UDP atau admission. Jangan memberi
endpoint route ke seluruh `.100/24`. Uji UDP dibuktikan lewat handshake setelah
admission, bukan lewat `Test-NetConnection` TCP.

## 4. Menyalakan dan menggunakan VM lewat terminal

Perintah **HOST** dijalankan di terminal laptop Linux yang menyimpan VM, bukan
PowerShell Windows. VM berjalan di belakang layar; terminal SSH dipakai untuk
mengoperasikan Ubuntu di dalamnya. Menutup SSH tidak mematikan VM atau layanan.

### 4.0.1 Nyalakan ketiga VM

**HOST:** periksa dahulu:

```bash
virsh -c qemu:///system list --all
virsh -c qemu:///system net-list --all
```

Jika jaringan `vanguard` sudah terdaftar tetapi inactive, jalankan
`virsh -c qemu:///system net-start vanguard`. Jangan membuat jaringan atau VM
pengganti jika nama tidak ditemukan; periksa host/repository yang benar.

Untuk VM yang statusnya **shut off**, jalankan sesuai urutan:

```bash
virsh -c qemu:///system start VM-CA
virsh -c qemu:///system start VM-SERVER
virsh -c qemu:///system start VM-ADMIN
virsh -c qemu:///system list --all
```

Lewati `start` untuk VM yang sudah running. Jika muncul izin ditolak, gunakan
akun pengelola libvirt yang disetujui, atau `sudo virsh` sesuai akses host.
Tunggu boot; running belum berarti SSH/aplikasi siap. Jangan mengulang provisioning,
mengubah disk, atau membuat CA baru. Node lama lainnya tetap dipertahankan.

### 4.0.2 Buka tiga terminal SSH

Pada host proyek ini, inventory privat ada di `state/lab/inventory.json`. Dari
root repository, jalankan blok berikut di **masing-masing dari tiga tab terminal**.
Pilih `ca` pada tab pertama, `server` pada tab kedua, dan `admin` pada tab ketiga.
Blok ini mengambil user, port dan konfigurasi SSH existing tanpa mencetak password:

```bash
python3 - <<'PYSSH'
import json, subprocess
from pathlib import Path
# Input melalui /dev/tty karena stdin blok ini berisi kode Python.
with open('/dev/tty', 'r+') as terminal:
    terminal.write('Peran (ca/server/admin): ')
    terminal.flush()
    role = terminal.readline().strip()
if role not in ('ca', 'server', 'admin'):
    raise SystemExit('Peran tidak valid')
node = json.loads(Path('state/lab/inventory.json').read_text())[role]
args = ['ssh', '-tt', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10']
if node.get('ssh_config'):
    args += ['-F', node['ssh_config']]
args += ['-p', str(node.get('port', 22)), node['user'] + '@' + node['host']]
with open('/dev/tty', 'rb') as terminal:
    raise SystemExit(subprocess.call(args, stdin=terminal))
PYSSH
```

Inventory tidak disertakan di GitHub. Pada host lain, operator menyiapkan akses
SSH lebih dahulu. Alternatif: `ssh USER_VM@IP_VM`, atau tambahkan
`-F /PATH/konfigurasi-ssh` sesuai inventory. Jangan menulis password di command
line. Jika host key tidak dikenal/berubah, cocokkan fingerprint melalui console;
jangan memakai `StrictHostKeyChecking=no` atau menghapus known_hosts sembarangan.

Sesudah login, jalankan `hostname`. Pastikan tab menampilkan `vm-ca`, `vm-server`
atau `vm-admin` yang sesuai sebelum mengetik perintah administrasi. Ketik `exit`
untuk menutup koneksi SSH saja. Jika koneksi ditolak saat boot, tunggu dan periksa
console; jangan langsung menganggap aplikasi gagal atau mengubah password.

### 4.0.3 Alternatif console serial tanpa SSH

**HOST:** jika jaringan SSH belum siap:

```bash
virsh -c qemu:///system console VM-CA
```

Tekan Enter untuk prompt, lalu login dengan credential lokal yang sudah tercatat
privat. Ganti nama VM untuk server/admin. Tekan **Ctrl+]** untuk keluar dari
console; VM tetap menyala. Console dapat sedang dipakai virt-manager; tutup sesi
console milik sendiri terlebih dahulu, jangan memaksa mengambil sesi orang lain.

### 4.0.4 Periksa dan mulai layanan Ubuntu

**Di dalam VM-CA:**

```bash
sudo systemctl is-active vanguard-ca
# Jalankan start hanya jika belum active:
sudo systemctl start vanguard-ca
sudo systemctl status vanguard-ca --no-pager
```

**Di dalam VM-SERVER**, setelah CA siap:

```bash
sudo systemctl is-active wg-quick@wg0 vanguard-server vanguard-daemon
# Untuk unit yang belum active, start sesuai urutan:
sudo systemctl start wg-quick@wg0
sudo systemctl start vanguard-server
sudo systemctl start vanguard-daemon
```

**Di dalam VM-ADMIN:**

```bash
sudo systemctl is-active vanguard-admin
# Jalankan start hanya jika belum active:
sudo systemctl start vanguard-admin
```

`start` bukan install ulang dan tidak perlu `vanguard-ca init`. Jika service
failed, baca status/log lebih dahulu, jangan terus melakukan restart:

```bash
# Ganti nama unit sesuai tab/layanan yang diperiksa.
sudo journalctl -u vanguard-server -n 50 --no-pager
```

Jangan memublikasikan log mentah sebelum diperiksa dari rahasia. Dashboard admin
adalah aplikasi web, sehingga setelah layanan siap buka browser pengelola ke
`https://192.168.100.40:5000`. Terminal tidak menggantikan halaman dashboard.

Setelah sesi lapangan selesai, disconnect/logout endpoint dan simpan bukti,
lalu gunakan shutdown normal dari HOST: `virsh -c qemu:///system shutdown VM-ADMIN`,
kemudian `VM-SERVER`, lalu `VM-CA`. Tunggu dan cek `list --all`; jangan mematikan
host sebelum VM benar-benar shut off. Hindari `destroy` atau kill proses QEMU.

### 4.0.5 Pastikan layanan siap menerima pengujian

**Masing-masing VM:** periksa jam, disk, versi dan service sesuai perannya:

```bash
timedatectl status
df -h
/opt/vanguard/venv/bin/python -c "from importlib.metadata import version; print(version('vanguard-ztna'))"
# CA: vanguard-ca; admin: vanguard-admin; baris berikut khusus server:
sudo systemctl is-active vanguard-server vanguard-daemon wg-quick@wg0
```

**VM-ADMIN:** jalankan ketiganya; harus HTTP 200 dan status ready, tanpa `-k`:

```bash
curl --fail --connect-timeout 3 --max-time 8 --cacert /etc/vanguard/root.crt https://192.168.100.10:8080/readyz
curl --fail --connect-timeout 3 --max-time 8 --cacert /etc/vanguard/root.crt https://192.168.100.20:8081/readyz
curl --fail --connect-timeout 3 --max-time 8 --cacert /etc/vanguard/root.crt https://192.168.100.40:5000/readyz
```

CA hanya menerima jalur API dari server/admin; timeout dari host ke CA tidak
boleh dipakai sebagai satu-satunya kesimpulan CA gagal. Dari browser pengelola,
buka `https://192.168.100.40:5000`, verifikasi trust dan login password + TOTP.

Sebelum perubahan, buat backup backend konsisten pada periode maintenance dan
verifikasi dapat dibaca. Jangan mengembalikan index, serial, crlnumber, CRL atau
DB lama sebagai cara membatalkan uji. Revoke adalah bagian histori yang tetap disimpan.

### 4.1 Siapkan kebijakan aplikasi dan internet

Ini prasyarat operator sebelum hari uji, bukan otomatis dikerjakan EXE:

- Sediakan demo publik tanpa data sensitif pada `10.8.0.1:8082` di VM server.
- Pastikan `VANGUARD_RESOURCE_POLICY` menunjuk kebijakan sah. Grant mencakup
  device ID, username, resource `internal-demo`, alamat `10.8.0.1`, protokol `tcp`,
  port `8082`; jangan mengganti grant perangkat lain dengan contoh baru.
- Untuk internet, aktifkan forwarding IPv4/NAT pada gateway Linux dan pastikan
  `VANGUARD_INTERNET_POLICY` dipakai server **dan daemon**. Policy awal untuk
  perangkat uji tidak diberi izin; default-deny dipertahankan.
- Verifikasi internet/DNS dari host dan VM server **sebelum** lockdown Windows.
  Gangguan upstream dicatat terpisah dari penolakan VanGuard.

Bila firewall guest harus disesuaikan, contoh **kandidat saja** pada source repo:

```bash
python3 deploy/firewall.py server --management-ip 192.168.100.1 \
  --windows-client --application-policy \
  --physical-client 192.168.50.20 --physical-client 192.168.50.30 \
  --print-only > server-pilot.candidate.nft
```

Untuk mode internet, tambahkan `--internet-uplink NAMA_INTERFACE_GUEST` sebelum
`--print-only`; nama diambil dari route VM server, bukan nama Ethernet host.
Periksa kandidat dengan `sudo nft --check --file server-pilot.candidate.nft` pada
VM server. Ini **belum memasang aturan dan belum membuat timer rollback**.
Generator mengganti tabel `inet vanguard`; review aturan/set/grant existing dan
siapkan pemulihan konfigurasi yang tepat sebelum operator menerapkannya.

### 4.2 Siapkan trust dan profil publik

Pada backend existing, gunakan salinan `root.crt` dan profil admin yang sudah
valid; jangan membuat CA untuk setiap PC. Cocokkan root fingerprint melalui
console CA dan public key server dari `sudo wg show wg0 public-key` di VM server.
Untuk input launcher, fingerprint adalah 64 karakter hex tanpa awalan/colon.

Profil endpoint dan profil bundle admin harus sama dan lolos validasi:

```bash
# Pada VM admin; sesuaikan path apabila env memakai lokasi lain.
sudo /opt/vanguard/venv/bin/python -c "from vanguard.profile import load_profile; p=load_profile('/etc/vanguard/endpoint-profile.json','/etc/vanguard/root.crt'); print('schema',p['schema'],'api',p['api_url'])"
```

| Mode | Isi profil yang diperlukan |
| --- | --- |
| Aplikasi internal | schema1, API `https://192.168.100.20:8081`, WG host `.100.20`, port 51820, allowed IP `10.8.0.1/32` |
| Internet terkelola | schema2, API/WG IPv4 literal yang sama, allowed IP tepat `0.0.0.0/1` dan `128.0.0.0/1`, `internet.mode=managed-ipv4`, 1–2 DNS IPv4 publik yang diizinkan jaringan |

Keduanya membawa root fingerprint, public key server, jaringan backend `.100/24`,
tunnel `10.8.0.0/24`, serta resource demo TCP8082. DNS router `.50.1` bukan DNS
schema2 yang valid. Generator `prepare_endpoint_pilot.py` membuat **schema1**;
jangan menganggap outputnya otomatis menyiapkan internet. Bila profil existing
belum cocok, operator membuat kandidat dan memvalidasinya sebelum distribusi;
jangan mengganti profil endpoint yang sudah memiliki identitas secara paksa.

## 5. Periksa Windows yang sudah digunakan

Lama pemakaian bukan penentu kompatibilitas. Periksa **build, arsitektur dan
kebijakan**. Jalankan baca saja dalam PowerShell Administrator:

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture
$env:PROCESSOR_ARCHITECTURE
(Get-CimInstance Win32_ComputerSystem).PartOfDomain
Get-NetFirewallRule -PolicyStore ActiveStore | Where-Object PolicyStoreSourceType -eq GroupPolicy | Select-Object Name,Direction,Action
Get-NetFirewallRule -PolicyStore localhost
Get-NetIPAddress -AddressFamily IPv4
Get-NetRoute -AddressFamily IPv4
Get-Service 'WireGuardTunnel*' -ErrorAction SilentlyContinue
Get-Date
```

**Target installer:** Windows 10 x64 build 19044/19045 atau Windows 11 x64 build
22000 ke atas. ARM64, x86 dan Windows Server ditolak. Gate tersebut tidak
membuktikan semua build telah diuji; bukti VM yang tersedia: build19044 dan26300.
Jangan upgrade OS kampus semata-mata untuk pilot tanpa rencana dari petugas lab.

**Mode internet BLOCKED** jika domain=true, ada rule GroupPolicy, atau Local GPO
firewall sudah berisi rule. Installer policy sekarang belum mengintegrasikan
kondisi itu. Jangan keluar dari domain, menghapus GPO, atau mematikan antivirus.
Pilih perangkat uji yang diizinkan atau catat kebutuhan integrasi administrator.
Pemeriksaan yang error berarti UNKNOWN, bukan berarti tidak ada policy.

Interface Windows tidak boleh overlap `192.168.100.0/24` atau `10.8.0.0/24`.
Periksa VPN/adapter virtual lama dan route tunnel yang tersisa; jangan memintas
pemeriksaan konflik launcher atau menghapus config milik aplikasi lain.

Simpan kondisi awal IP/DNS/firewall secara privat, pastikan aplikasi lab dapat
kembali berfungsi, dan sediakan admin lokal/console serta media transfer offline.
Sinkronkan jam sebelum lockdown. Setelah lockdown, DNS/NTP internet langsung
memang dapat ditolak.

## 6. Install dan configure satu PC terlebih dahulu

1. Salin EXE dan berkas trust publik yang disetujui admin. Buka PowerShell admin:

   ```powershell
   Get-FileHash '.\Setup-VanGuard-0.1.15.exe' -Algorithm SHA256
   ```

2. Cocokkan hash bagian 2. Klik kanan EXE → **Run as administrator**. Catat prompt
   UAC dan hasilnya. Paket belum ditandatangani Authenticode; jika diblok kebijakan
   lab, berhenti dan minta peninjauan petugas, jangan menonaktifkan proteksi.
3. Exit0 = instalasi selesai; exit3010 = reboot lalu ulang installer yang sama;
   exit1 = gagal, simpan pesan aman. Exit20 pada paket per-device berarti menunggu
   persetujuan admin. **EXE umum tidak otomatis memblokir internet.**
4. Simpan profil/root publik di lokasi terlindungi, misalnya
   `C:\Program Files\VanGuardTrust`. Lalu:

   ```powershell
   $vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
   & $vg configure
   & $vg status
   & $vg diagnose
   ```

   Masukkan path profil/root, fingerprint dan public key yang dikonfirmasi admin.
   Jika configure gagal, jangan menghapus trust lama atau mengabaikan TLS.
5. **Khusus internet:** sebelum init/enrollment, jalankan:

   ```powershell
   & $vg internet-preview
   & $vg internet-enable
   & $vg internet-status
   ```

   Preview belum mengubah firewall. Setelah enable berhasil, internet langsung
   dan IPv6 diblok, jalur admission/WireGuard tetap tersedia. Buktikan website/DNS
   yang sebelumnya bisa diakses kini tertolak. Siapkan media USB untuk approval.
   Jika gagal/UNKNOWN, hentikan alur dan periksa pemulihan; jangan mencatat PASS.

Paket ZIP/BAT alternatif: ekstrak **seluruh folder** terverifikasi. Paket per-device
buatan admin dapat memakai `Setup-VanGuard.bat` dan melanjutkan wizard dengan
request/approval yang sama. Runbook ini memakai EXE umum dan langkah manual di
bawah; jangan mencampur dua alur dengan menjalankan init dua kali.

## 7. Daftar perangkat, import, lalu connect

**WINDOWS baru:** setiap terminal PowerShell baru (termasuk sesudah reboot)
harus mengisi kembali variabel `$vg`; variabel tidak diwariskan antarterminal.

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg init
```

Masukkan ID dan IP tunnel yang sudah dialokasikan. Kirim hanya
`C:\Program Files\VanGuardEndpointData\identity\request.json` ke pengelola.
Kunci X.509 dan WireGuard dibuat pada PC. Jangan mengirim key, token atau seluruh
folder identity. Perangkat existing tidak di-init ulang.

**DASHBOARD ADMIN:** login password/TOTP, buat/pilih akun karyawan uji, unggah
request PC yang benar, cocokkan ID/IP dan tautkan ke karyawan. Tunggu registered;
jika pending perbaiki sebab dan retry request yang sama. Unduh bundle perangkat
lalu kirim ke PC asal. CA menandatangani CSR; registrasi belum menambah peer.

**WINDOWS:**

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg import-bundle
& $vg status
& $vg diagnose
& $vg login
& $vg connect
```

Masukkan path ZIP bundle saat diminta; gunakan login karyawan, bukan akun admin
website. Terminal connect tetap terbuka untuk renewal. Jangan membuat peer
statis atau mengimpor konfigurasi WireGuard alternatif untuk melewati admission.

**ADMIN:** setelah uji tanpa izin, berikan grant aplikasi yang eksplisit di
server. Untuk internet, pilih **Izin internet melalui gateway → Izinkan setelah
admission** pada perangkat yang benar. Izin ini tetap membutuhkan sesi karyawan,
sertifikat valid dan keenam pemeriksaan perangkat.

**WINDOWS setelah grant aplikasi:**

```powershell
curl.exe --connect-timeout 3 --max-time 8 http://10.8.0.1:8082/
```

Gunakan HTTP demo sebagai bukti akses. Ping bukan kriteria wajib: firewall lab
untuk ICMP masih membatasi IP tertentu dan dapat menolak IP endpoint fisik baru.
Pada VM server, amati terpisah:

```bash
sudo wg show wg0 peers
sudo wg show wg0 latest-handshakes
sudo wg show wg0 transfer
```

Cocokkan public key dengan perangkat di registry. Terdaftar ≠ lease valid ≠ peer
terpasang ≠ handshake terbaru ≠ transfer aplikasi berhasil. Catat unknown bila
pemeriksaan gagal. Setelah PC LAN lulus, ulangi dengan ID/key/IP berbeda untuk
laptop Wi-Fi, kemudian uji keduanya bersamaan.

## 8. Matriks pengujian dan syarat penerimaan pilot

Awali setiap uji dengan kondisi yang dicatat. Jangan menebak PASS dari tampilan
installer sukses. Sinkronkan jam dan catat waktu permintaan, konfirmasi admin,
serta waktu akses benar-benar berhenti.

| ID | Langkah | Hasil yang diwajibkan |
| --- | --- | --- |
| F01 | Sebelum instalasi, cek internet dan aplikasi lab biasa | Baseline diketahui; gangguan upstream dicatat |
| F02 | Install EXE pada PC existing, periksa status/diagnose | Runtime terpasang, trust valid, error/UAC dicatat |
| F03 | Internet-enable sebelum sertifikat/admission | Internet langsung tertolak; admission masih dapat dijangkau |
| F04 | Login dengan akun sah pada endpoint belum terdaftar | Tidak memperoleh akses; kredensial saja tidak cukup |
| F05 | Daftar/import lalu admission dengan akun yang terikat | Lease/peer/handshake dapat dibuktikan, belum dianggap izin semua resource |
| F06 | Tanpa grant, lalu grant demo TCP8082 yang tepat | Ditolak sebelum grant; HTTP sukses setelah grant |
| F07 | Endpoint menuju demo lewat LAN, port lain, CA/admin/SSH backend | Akses yang tidak diizinkan tetap ditolak; uji pada alamat/port pilot saja |
| F08 | Mode internet: tanpa grant → beri grant → hapus grant | Internet/DNS tertolak → berfungsi lewat gateway → tertolak lagi |
| F09 | Kedua endpoint aktif selama waktu yang disepakati | Minimal dua renewal sukses, tidak ada putus yang tak dijelaskan |
| F10 | Logout PC, sementara laptop tetap aktif | Akses/sesi PC berhenti; laptop tetap bekerja sesuai grant |
| F11 | Reboot endpoint lalu periksa route, policy dan login/connect | Lockdown tetap berlaku; pemulihan koneksi sesuai sesi tanpa bypass |
| F12 | Revoke sertifikat PC saat ada koneksi aplikasi dan internet aktif | Data baru berhenti, peer/grant terkait hilang, readmission ditolak; laptop tetap bekerja |
| F13 | Setelah revoke, coba internet langsung, IPv6 dan route LAN | Tidak memperoleh jalur bypass selama policy terkelola aktif |
| F14 | Nonaktifkan akun fixture terpisah | Akses akun tersebut berhenti; akun lain tidak ikut dicabut |
| F15 | Putuskan koneksi, logout, lalu recovery lokal | Selesai atau kegagalan terdokumentasi; kondisi jaringan awal pulih sesuai izin |

**Batas F04:** kegagalan connect lokal karena belum ada sertifikat hanya membuktikan
endpoint belum mendapatkan akses. Untuk mengklaim skenario kredensial curian S-01
pada sisi server, bukti harus menunjukkan permintaan diterima dan ditolak oleh
API/audit server. Jika aspek itu belum diuji, catat BELUM_TERUJI secara terpisah.

F03/F08/bagian internet F12/F13 wajib untuk tujuan internet; jika belum dilakukan,
tulis BELUM_TERUJI, bukan PASS. Revoke tidak dibatalkan: pengujian berikutnya
memerlukan penggantian identitas resmi dengan histori lama dipertahankan.

**Cara membuktikan TCP aktif pada F12:** gunakan server uji yang diizinkan dengan
stream/unduhan cukup panjang. Pastikan satu koneksi TCP yang sama masih menerima
data sebelum revoke. Catat waktu revoke dan waktu byte baru terakhir diterima;
periksa trafik gateway/peer bersama hasil client. Refresh browser atau loop curl
membuat koneksi baru dan tidak membuktikan koneksi lama diputus. Data yang sudah
tersimpan di buffer dapat tampil setelah revoke; bedakan dari data jaringan baru.
Bila tidak tersedia stream dan alat observasinya, tandai bagian ini BELUM_TERUJI.
Jangan melakukan load test ke layanan publik tanpa izin pemiliknya.

**Keputusan:** pilot diterima untuk mode/build/topologi yang diuji jika semua
kasus wajib lulus, hasil negatif benar-benar menolak, perangkat lain tetap bekerja,
pemulihan selesai, dan penanggung jawab lab menandatangani catatan. Jika masih ada
FAIL/UNKNOWN/BELUM_TERUJI pada syarat wajib, tulis diterima sebagian atau ditunda
beserta tindakan berikutnya. Jangan memakai angka waktu VM sebelumnya sebagai
jaminan pencabutan di kampus; nilai ambang disepakati sebelum uji.

Windows kosong, uji banyak komputer, penggunaan jangka panjang dan power loss CA
merupakan lingkup tambahan. Itu tidak harus menghalangi pilot dua PC existing,
tetapi hasil pilot tidak boleh diklaim mencakup lingkup tersebut.

## 9. Penanganan kegagalan dan pemulihan

| Gejala | Tindakan aman |
| --- | --- |
| TCP8081 tidak tembus | Cek IP/route/interface, guest firewall dan chain host/libvirt; jangan mematikan semua firewall |
| TLS/readiness gagal | Periksa jam, root, SAN, service, disk dan dependensi; jangan pakai skip TLS atau CRL lama |
| Domain/GPO atau konflik subnet | Stop mode yang terhalang; tinjau bersama admin organisasi, jangan memaksa launcher |
| Internet gagal sebelum lockdown | Perbaiki upstream/route/NAT dahulu; hasil revoke belum dapat dinilai |
| Pending/exit20 | Admin menyelesaikan workflow; gunakan request dan kunci yang sama |
| Tunnel ada tetapi aplikasi gagal | Periksa grant tepat, service aplikasi, lease dan transfer |
| Cleanup gagal | Pertahankan config; pastikan pemilik serta berhentinya tunnel/service sebelum menghapus apa pun |

Normal: Ctrl+C di terminal connect. Di terminal administrator kedua:

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg disconnect
& $vg logout
```

Jika server tidak terjangkau, logout server **belum terkonfirmasi**. Jangan
menganggap hapus token lokal sebagai pencabutan server; retry ketika pulih.

Untuk mengakhiri mode internet pada maintenance yang disetujui, setelah tunnel
berhenti dan kepemilikannya jelas:

```powershell
& $vg internet-recover
# Ketik PULIHKAN hanya setelah membaca konfirmasi administrator.
```

Recovery dapat membuka internet langsung seperti sebelum pilot; ini tindakan
pemulihan lokal, **bukan bukti fail-closed atau revoke server**. Jangan menghapus
backup/state firewall atau mengimpor backup firewall lama secara sembarang.

Jika route pilot dibuat pada sesi ini dan tidak lagi dibutuhkan, hapus hanya
route tersebut setelah memeriksa interface/tujuan/next-hop:

```powershell
# Terminal baru: isi kembali indeks dari catatan sesi, jangan menebaknya.
Get-NetIPConfiguration
[int]$ifIndex = Read-Host 'InterfaceIndex route pilot yang dicatat'
Get-NetRoute -DestinationPrefix '192.168.100.20/32' | Where-Object { $_.InterfaceIndex -eq $ifIndex -and $_.NextHop -eq '192.168.50.10' }
# Gunakan InterfaceIndex yang dicatat; konfirmasi hanya route milik pilot:
Remove-NetRoute -DestinationPrefix '192.168.100.20/32' -InterfaceIndex $ifIndex `
  -NextHop '192.168.50.10' -PolicyStore ActiveStore
```

Kembalikan IP/DNS/adapter yang memang diubah. Cabut grant dan identitas uji melalui
admin, nonaktifkan akun fixture yang tidak dipakai, hentikan demo milik pilot,
dan verifikasi aplikasi lab kembali normal. Jangan menghapus akun/perangkat utama.
Uninstall bila diminta petugas melalui uninstaller resmi; uninstall bukan revoke.

## 10. Checklist keputusan hari pelaksanaan

- [ ] Izin, dua endpoint sasaran dan penanggung jawab pemulihan jelas.
- [ ] Backup dan bukti privat tersedia; data pengguna sudah disimpan.
- [ ] IP tidak bentrok; Ethernet host/PC dan Wi-Fi laptop sesuai topologi.
- [ ] Forwarding host/libvirt, jalur balik, NAT dan pembatasan endpoint terbukti.
- [ ] Tiga VM siap; root existing, jam, CRL dan versi terverifikasi.
- [ ] Kompatibilitas Windows, domain/GPO, subnet dan tunnel existing diperiksa.
- [ ] Hash installer dan trust benar; semua media tersedia sebelum lockdown.
- [ ] Profil, grant, ID/IP tunnel dan akun karyawan sudah disiapkan admin.
- [ ] Uji satu endpoint selesai sebelum menambah endpoint kedua.
- [ ] Dua renewal, logout, reboot, revoke dan isolasi endpoint lain dicatat.
- [ ] Tujuan internet diuji lengkap atau diberi status belum diterima.
- [ ] Recovery dilakukan; penanggung jawab lab memeriksa kondisi akhir.

## 11. Formulir hasil — isi saat uji, jangan isi PASS sebelumnya

| Kasus | Endpoint/build | Kondisi awal | Mulai/konfirmasi/akhir (WIB) | Hasil aktual | PASS/FAIL/UNKNOWN/BELUM_TERUJI | Bukti privat | Petugas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| … | … | … | … | … | … | … | … |

| Ringkasan sesi | Isi |
| --- | --- |
| Commit source / versi EXE / hash EXE | … |
| Model router / firmware / uplink / interface host | … |
| ID anonim PC dan laptop / build Windows / domain-GPO | … |
| Lama uji / jumlah renewal / gangguan yang teramati | … |
| Waktu revoke diminta, dikonfirmasi, peer hilang, data berhenti | … |
| Kegagalan dan percobaan ulang, semuanya dipertahankan | … |
| Status recovery dan kondisi akhir perangkat | … |
| Keputusan beserta lingkup yang diterima | … |
| Sisa pekerjaan / penanggung jawab / jadwal | … |
| Persetujuan petugas lab | … |

Simpan screenshot tanpa password/OTP/token, hasil status, audit admin WIB, dan
log yang telah ditinjau. Jangan merekam request lengkap, private key, env rahasia
atau isi profil pengguna. Bukti mentah berada di penyimpanan privat; ringkasan
tersanitasi boleh masuk GitHub. Kesalahan awal tetap dicatat meski retry berhasil.

Dokumen ini memakai backend existing. Bila harus membangun ulang lingkungan baru,
selesaikan instalasi CA/backend pada [manual resmi](MODUL_PENGGUNAAN_VANGUARD.md)
sebelum berangkat, tanpa membuat ulang CA operasional. Referensi internal proyek:
[checkpoint](CHECKPOINT.md), [hasil VM](reports/VALIDASI_0.1.15_2026-11-02.md),
[aturan firewall](../deploy/firewall.py), [gate Windows](../deploy/endpoint/windows/Platform.ps1),
[policy internet](../deploy/endpoint/windows/Internet-Lockdown.ps1).
