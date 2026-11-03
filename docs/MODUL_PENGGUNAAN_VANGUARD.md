# Panduan penggunaan VanGuard

Edisi 2 November 2026 · panduan admin dan pengguna Windows.
Markdown dan HTML adalah dua format dari **manual yang sama**.
Ganti `/PATH/...`, `ID_PERANGKAT`, `IP_TUNNEL` dan placeholder kapital dengan
nilai yang sudah disiapkan admin; jangan menyalin placeholder apa adanya.

**Alur:** siapkan layanan → install endpoint → daftar perangkat → import sertifikat
→ login → connect → uji akses → logout atau revoke.

| Kebutuhan | Mulai dari |
|---|---|
| Sistem sudah terpasang, tambah PC Windows | Bagian 1–5 |
| Perangkat sudah terdaftar | Bagian 4 |
| Cabut akses atau lihat aktivitas | Bagian 6 |
| Membuat paket satu BAT/EXE per perangkat | Bagian 7 |
| Memblokir internet tanpa mengubah router | Bagian 8 |
| Memasang backend dan CA dari nol | Bagian 9, lalu kembali ke Bagian 1 |
| Ada kendala | Bagian 10 |

**Pilih paket:** gunakan versi dan checksum pada [halaman unduhan](../downloads/README.md).
Lihat [checkpoint](CHECKPOINT.md) untuk versi yang benar-benar terpasang dan hasil
uji. Instalasi aplikasi tidak otomatis mengaktifkan profil server atau gateway
internet; admin tetap perlu mengikuti konfigurasi pada Bagian 1 dan 8.

## 1. Persiapan admin

**Tempat kerja:** HOST = laptop Linux; VM = mesin layanan; WINDOWS = PowerShell
**Run as administrator**; DASHBOARD = browser admin pada jalur management.

| Layanan lab | Alamat |
|---|---|
| CA | 192.168.100.10:8080, HTTPS |
| Server admission / WireGuard | 192.168.100.20:8081 HTTPS / UDP51820 |
| Dashboard admin | https://192.168.100.40:5000 |
| Tunnel server | 10.8.0.1 |

1. Nyalakan VM-CA, VM-SERVER, lalu VM-ADMIN. Lab yang sudah terpasang memakai CA
   yang sama; **jangan generate CA baru untuk setiap komputer**.
2. Periksa jam, ruang disk, dan service pada masing-masing VM:

   ```bash
   timedatectl status
   df -h
   # Sesuaikan role: vanguard-ca, vanguard-server, atau vanguard-admin.
   sudo systemctl is-active vanguard-server
   ```

3. Di **VM-ADMIN**, pastikan kedua pemeriksaan menghasilkan HTTP200 dan `ready`:

   ```bash
   curl --fail --connect-timeout 3 --max-time 8 --cacert /etc/vanguard/root.crt \
     https://192.168.100.20:8081/readyz
   curl --fail --connect-timeout 3 --max-time 8 --cacert /etc/vanguard/root.crt \
     https://192.168.100.40:5000/readyz
   ```

4. Siapkan untuk setiap PC: `profile.json`, `root.crt`, fingerprint root, public
   key WireGuard server, device ID unik, IP tunnel kosong, dan akun karyawan.
   Verifikasi fingerprint/key melalui admin tepercaya. Password dibagikan privat.
5. Pastikan endpoint dapat mencapai server TCP8081 dan UDP51820. Installer
   Windows tidak menyiapkan jaringan host, backend Linux, atau izin aplikasi.

**IP tunnel bukan IP LAN.** Lab mencadangkan10.8.0.2/.3/.4; periksa registry sebelum
mengalokasikan IP lain. PC berbeda harus mempunyai ID dan kunci berbeda.

### 1.1 Menyiapkan profil jika belum tersedia

Di HOST, gunakan salinan **root publik** dan **public key server** yang diverifikasi:

```bash
.venv/bin/python scripts/prepare_endpoint_pilot.py \
  --root /PATH/root.crt --server-public-key-file /PATH/server-wg.pub \
  --output /PATH/PROFIL_BARU
```

Hasilnya profil **aplikasi internal/schema1**, bukan internet terkelola. Generator
menggunakan alamat lab pada tabel di atas. Pada jaringan lain, alamat, SAN HTTPS,
routing dan firewall harus disesuaikan oleh operator.

Pada VM-ADMIN, setelah backup konfigurasi/database yang konsisten:

1. Salin profil ke `/etc/vanguard/endpoint-profile.json`, owner root:vanguard,
   mode0640. Profil tidak memuat password atau private key.
2. Tambahkan `VANGUARD_CLIENT_PROFILE=/etc/vanguard/endpoint-profile.json` melalui
   `sudoedit /etc/vanguard/admin.env`; pertahankan nilai env lainnya.
3. Restart `vanguard-admin` dan ulangi readiness. Bundle harus berisi profil yang
   sama dengan profil endpoint. Berhenti jika tidak cocok.

**PC fisik pada pilot .50/24:** host Linux192.168.50.10 meneruskan koneksi ke
backend .100/24. Operator menyiapkan forwarding dan jalur balik, membatasi endpoint
ke TCP8081/UDP51820. CA, dashboard dan aplikasi internal tidak dibuka langsung
ke LAN. Bila route belum ada, di Windows gunakan adapter yang sudah diperiksa:

```powershell
Get-NetIPConfiguration
# Ganti INDEX_ADAPTER dengan angka adapter LAN/Wi-Fi yang benar.
New-NetRoute -DestinationPrefix '192.168.100.20/32' -InterfaceIndex INDEX_ADAPTER `
  -NextHop '192.168.50.10' -PolicyStore ActiveStore
```

Route ini hilang setelah reboot. Jangan menambahkan route kedua jika sudah ada;
periksa kembali jaringan sebelum connect.

## 2. Install Windows dan buat permintaan perangkat

Target paket: Windows10 x64 build19044/19045 atau Windows11 x64. Instalasi perlu
hak administrator lokal. Akun VPN tetap terpisah dari akun admin Windows.

### 2.1 Install EXE umum

1. Unduh EXE terbaru dari [halaman unduhan](../downloads/README.md)
   dari branch `feature/2026-10-22-physical-endpoints`, folder `downloads`, tombol
   **Download raw file**. Tidak perlu GitHub CLI.
2. Cocokkan hash dengan [SHA256SUMS](../downloads/SHA256SUMS) dan nilai tepercaya
   dari admin:

   ```powershell
   Get-FileHash '.\NAMA_FILE_INSTALLER.exe' -Algorithm SHA256
   ```

3. Klik kanan EXE → **Run as administrator**, setujui UAC, tunggu selesai.
   Python, WireGuard dan dependensi disertakan. Jika kebijakan Windows memblokir
   EXE yang belum ditandatangani ini, minta admin meninjau; jangan matikan proteksi.

| Kode hasil | Tindakan |
|---|---|
| 0 | Tahap selesai; EXE umum baru memasang aplikasi |
| 20 | Wizard per-device menunggu bundle persetujuan admin |
| 3010 | Restart Windows, lalu jalankan installer yang sama |
| 1 | Catat error dan periksa; jangan hapus key/config |

**EXE umum belum membuat sertifikat, tunnel atau blokir internet.** Jika admin
memberikan paket per-device, ikuti Bagian7; jangan ulang init pada identitas wizard.

### 2.2 Configure dan buat request

Letakkan profil/root publik dari admin di `C:\Program Files\VanGuardTrust`.
Buka PowerShell Administrator:

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg configure
& $vg status
& $vg diagnose
```

Isi path profil/root, fingerprint dan public key server saat diminta.
**Hasil wajib:** konfigurasi lengkap dan server dapat diperiksa. Jangan mengganti
root lama atau mengabaikan TLS agar lolos.

Untuk **perangkat baru**, jalankan:

```powershell
& $vg init
```

Masukkan device ID dan IP tunnel dari admin. Kirim **hanya** berkas berikut:

`C:\Program Files\VanGuardEndpointData\identity\request.json`

Kunci X.509 dan WireGuard dibuat di PC. Jangan kirim `identity.key`, `wg.key`,
token, atau seluruh folder identity. Jika memakai schema2, aktifkan policy
Bagian8 **sebelum** init/enrollment. Perangkat yang sudah punya identitas melewati init.

## 3. Daftarkan perangkat di dashboard

**DASHBOARD ADMIN:**

1. Buka `https://192.168.100.40:5000` melalui jalur management yang diizinkan.
   Pastikan sertifikat HTTPS dipercaya dari root yang sudah diverifikasi.
2. Login admin menggunakan password dan TOTP authenticator.
3. Buat atau pilih **akun karyawan**. Bagikan kredensial melalui jalur privat.
4. Unggah request dari PC; pilih akun karyawan dan metadata perangkat. Cocokkan
   device ID, IP tunnel dan permintaan dari PC asal.
5. Tunggu status **registered**. Jika pending, perbaiki penyebab lalu retry.
6. Unduh **bundle perangkat**, kirim ke PC asal melalui jalur tepercaya.

CA menerbitkan sertifikat dari CSR; root CA tidak dibuat ulang. Registrasi dan
login karyawan saja **belum** menambahkan peer atau memberikan akses VPN.

## 4. Import, login, connect dan logout

**WINDOWS:** buka PowerShell Administrator. Untuk endpoint dari EXE umum:

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg import-bundle
& $vg status
& $vg diagnose
& $vg login
& $vg connect
```

- Saat import, masukkan path bundle dari admin. Bundle harus cocok dengan profil,
  root dan kunci PC yang membuat request.
- Saat login, masukkan akun karyawan dan password secara interaktif.
- Biarkan terminal **connect** terbuka untuk renewal lease.
- Server menambah peer hanya setelah sesi dan enam pemeriksaan perangkat lolos.
  Jangan menambahkan peer statis melalui GUI WireGuard.

**Mengakhiri pemakaian:** Ctrl+C pada terminal connect. Atau di terminal admin kedua:

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg disconnect
& $vg logout
```

Disconnect menutup tunnel; logout mencabut sesi server. Jika server tidak
terjangkau, pencabutan **belum terkonfirmasi**: retry setelah layanan pulih.
Jika cleanup gagal, pertahankan config sampai tunnel berhenti dan kepemilikannya
jelas. Setelah reboot, periksa route, login bila sesi habis, lalu connect kembali.

**Repair/reinstall:** disconnect dahulu, lalu jalankan installer tepercaya yang
sama; pertahankan key/config. Jika lockdown aktif, ikuti recovery Bagian8 dahulu.
Uninstall melalui `C:\Program Files\VanGuardEndpointData\tools\Uninstall-VanGuard.bat`
mempertahankan identitas serta Python/WireGuard bersama; tetap lakukan revoke
oleh admin bila perangkat tidak akan digunakan lagi.

**Client Ubuntu yang sudah terdaftar:**

```bash
sudo /opt/vanguard/venv/bin/vanguard-client login --username AKUN_KARYAWAN
sudo systemctl restart vanguard-client
```

Jangan jalankan connect foreground bersamaan dengan service. Sertifikat yang
kedaluwarsa perlu penggantian identitas oleh admin; login tidak memperpanjangnya.

## 5. Beri izin aplikasi dan uji koneksi

**VM-SERVER:** sediakan aplikasi uji dan aktifkan firewall application-policy
serta `VANGUARD_RESOURCE_POLICY`. Profil client saja tidak memberi izin aplikasi.

Untuk demo, siapkan folder publik `/srv/vanguard-pilot-demo` beserta `index.html`,
lalu jalankan jika port/unit belum digunakan:

```bash
sudo systemd-run --unit=vanguard-pilot-demo --uid=vanguard \
  --property=NoNewPrivileges=yes --property=ProtectSystem=strict \
  --property=ProtectHome=yes /usr/bin/python3 -m http.server 8082 \
  --bind 10.8.0.1 --directory /srv/vanguard-pilot-demo
```

Tambahkan grant ke **kandidat** kebijakan server, pertahankan grant sah lainnya:

```json
{"grants":[{"device_id":"ID_PERANGKAT","username":"AKUN_KARYAWAN","resource":"internal-demo","address":"10.8.0.1","protocol":"tcp","port":8082}]}
```

Validasi kandidat sebelum dipasang pada path `VANGUARD_RESOURCE_POLICY`:

```bash
sudo /opt/vanguard/venv/bin/python -c \
  "from vanguard.resource_policy import load_policy; print('valid; grants:',len(load_policy('/etc/vanguard/resource-policy.candidate.json')))"
```

Operator mempublikasikan file tervalidasi dengan penggantian atomic, owner root
mode0600. Jangan mengganti policy aktif dengan contoh kosong atau menambah elemen
nft manual. Gate harus sudah aktif sebelum uji.

**WINDOWS setelah connect:**

```powershell
curl.exe --connect-timeout 3 --max-time 8 http://10.8.0.1:8082/
```

| Uji | Hasil yang diharapkan |
|---|---|
| Akun + perangkat sah + grant sesuai | Aplikasi dapat diakses lewat tunnel |
| Tanpa grant, port lain, atau akses LAN langsung | Ditolak |
| Logout/revoke saat koneksi aktif | Akses terkait berhenti; perangkat lain tetap bekerja |
| Sertifikat expired/revoked atau akun nonaktif | Admission ditolak |

Periksa lease, peer, handshake, dan hasil HTTP **secara terpisah**. Peer terpasang
belum membuktikan akses aplikasi. Hentikan demo setelah pengujian:
`sudo systemctl stop vanguard-pilot-demo`.

## 6. Cabut akses, ganti identitas dan simpan audit

| Tindakan admin | Langkah |
|---|---|
| Cabut satu perangkat | Pilih perangkat → alasan → **Cabut akses & sertifikat**. Tunggu `revoked`; pastikan peer hilang dan akses ditolak |
| Status `revoking` | Perbaiki dependency → **Ulangi workflow**. Belum dianggap selesai |
| Nonaktifkan karyawan | Nonaktifkan akun. Sesi/akses akun dibatalkan; sertifikat tidak otomatis dicabut |
| Ganti identitas expired/hilang | Cabut identitas lama; buat ID dan kedua key baru di endpoint; gunakan form penggantian pada riwayat perangkat. Akun/IP diwariskan |
| Lihat aktivitas | **Aktivitas admin** → filter waktu WIB, pelaku atau perangkat → **Tampilkan** |
| Arsipkan aktivitas | **Simpan arsip aktivitas** → **Arsip** → unduh ZIP dan cocokkan SHA256 |

Simpan bukti/backup secara privat. Arsip tidak menghapus log asli. Jangan reset
CA, mengembalikan index/CRL lama, atau menimpa kunci lama untuk memaksa recovery.
Sebelum upgrade, backup konsisten saat service terkait berhenti; verifikasi arsip
sebelum mengubah runtime. Pemulihan kode tidak berarti rollback histori CA/database.

## 7. Opsional: satu BAT atau EXE per perangkat

Jalur ini menggantikan konfigurasi manual Bagian2.2. Admin menyiapkan profil,
root dan alokasi; pengguna menjalankan wizard yang sama sampai connect.

**HOST:** ambil folder `wheels` dan `runtimes` dari
[template offline](../downloads/README.md), verifikasi checksum, lalu:

```bash
.venv/bin/python scripts/build_endpoint_package.py \
  --wheelhouse /PATH/windows-wheels --runtime-directory /PATH/runtime-installers \
  --output /PATH/paket-perangkat-baru \
  --profile /PATH/profile.json --root /PATH/root.crt \
  --device-id ID_PERANGKAT --tunnel-ip IP_TUNNEL \
  --expected-root-sha256 FINGERPRINT_ROOT_64_HEX \
  --expected-server-key PUBLIC_KEY_WIREGUARD_SERVER
```

Gunakan wheel/runtime yang sesuai versi paket. Satu alokasi hanya untuk satu PC;
paket tidak memuat password, token management atau private key.

**WINDOWS:** ekstrak seluruh paket → jalankan `Setup-VanGuard.bat` → setujui UAC.
Kirim `C:\Program Files\VanGuardEndpointData\enrollment-request.json` ke admin.
Admin melakukan Bagian3. Masukkan path bundle ke wizard, atau simpan sebagai
`C:\Program Files\VanGuardEndpointData\approval.zip` lalu jalankan BAT yang sama.
Lanjutkan login dan connect. Exit20 berarti menunggu approval, bukan gagal.

**Membungkus menjadi EXE:** salin paket dan folder `deploy/endpoint/exe` ke komputer
build Windows admin. Jalankan:

```powershell
& 'C:\Program Files\VanGuardBuild\source\Build-Exe.ps1' `
  -Package 'C:\Program Files\VanGuardBuild\paket-perangkat-baru' `
  -Output 'C:\Program Files\VanGuardBuild\Setup-Perangkat-Baru.exe'
Get-FileHash 'C:\Program Files\VanGuardBuild\Setup-Perangkat-Baru.exe' -Algorithm SHA256
```

Folder `source` berisi `Build-Exe.ps1`, `VanGuardSetup.cs` dan `app.manifest`.
Bagikan EXE dan checksum tepercaya; simpan metadata build. EXE per-device memakai
alur wizard di atas, sedangkan EXE umum unduhan tetap perlu configure manual.

## 8. Opsional: internet terkelola tanpa konfigurasi router

**Mode ini memerlukan gateway Linux dan policy Windows.** Linux saja tidak dapat
memblokir koneksi PC yang langsung menuju router. Gunakan endpoint terkelola;
admin lokal penuh tetap dapat mengubah firewall. Mode ini IPv4, IPv6 diblok.

1. **Operator Linux:** siapkan uplink WAN, IPv4 forwarding, NAT gateway, jalur
   admission yang dapat dijangkau dan jalur management/pemulihan. Backup dahulu.
   Generate kandidat firewall lab, ganti `eth0` dengan uplink yang benar:

   ```bash
   python3 deploy/firewall.py server --management-ip 192.168.100.1 \
     --windows-client --application-policy --internet-uplink eth0 --print-only \
     > gateway-internet.candidate.nft
   sudo nft --check --file gateway-internet.candidate.nft
   ```

   Review subnet/aturan, lalu terapkan dalam maintenance dengan console dan
   rollback tersedia. Perintah di atas **hanya validasi**, belum mengaktifkan gateway.
2. Buat `/var/lib/vanguard/server/internet-policy.json` berisi `{"grants":[]}`
   **hanya bila belum ada**, owner root mode0600. Pasang `VANGUARD_INTERNET_POLICY`
   ke path itu pada env server **dan daemon**. Pastikan path boleh ditulis unit;
   validasi dengan `vanguard.internet.load_internet_policy`, restart terencana,
   lalu periksa readiness dan nft. Jangan menimpa policy/grant lama.
3. Buat profil **schema2** dari profil sah: `allowed_ips` berisi
   `["0.0.0.0/1","128.0.0.0/1"]`, tambahkan
   `"internet":{"mode":"managed-ipv4","dns":["1.1.1.1"]}`. Validasi profil,
   pertahankan root/key/resource, pasang profil sama di admin dan endpoint.
4. **WINDOWS setelah configure, sebelum enrollment:** sediakan console dan media
   transfer request/bundle. Jalankan:

   ```powershell
   & $vg internet-preview
   & $vg internet-enable
   & $vg internet-status
   ```

   Internet langsung diblok **setelah enable berhasil**, bukan saat klik EXE umum.
   Wizard per-device schema2 menjalankan tahap ini. Endpoint domain atau GPO yang
   bertentangan ditolak; jangan memaksa atau menghapus policy organisasi.
5. Daftarkan perangkat dan import bundle (Bagian3–4). Di dashboard pilih
   **Izin internet melalui gateway → Izinkan setelah admission**. Login dan connect.
6. Uji internet/DNS, penolakan jalur langsung, logout/revoke saat TCP aktif,
   reboot dan isolasi perangkat lain. Jangan menganggap PASS hanya karena install sukses.

**Recovery:** disconnect, pastikan tunnel/service berhenti, lalu admin lokal
menjalankan `& $vg internet-recover` dan mengonfirmasi `PULIHKAN`. Ini memulihkan
policy sebelum lockdown dan dapat membuka internet langsung; **bukan revoke server**.
Jangan hapus state/backup firewall. Maintenance runtime saat lockdown aktif harus
melalui recovery terencana. Tidak ada fallback otomatis yang membuka internet.

## 9. Khusus instalasi backend dan CA baru

**Lewati bagian ini pada lab yang sudah terpasang.** Contoh otomatis berikut
khusus topologi lab lima Ubuntu22.04: CA.10, SERVER.20, CLIENT.30, ADMIN.40,
ATTACKER.50 pada192.168.100.0/24; gateway host.1. Windows adalah client tambahan,
bukan pengganti Ubuntu. Installer tidak memasang OS Windows.

### 9.1 Siapkan host dan inventory

Siapkan KVM/libvirt, media OS resmi terverifikasi, SSH operator dan storage yang
cukup. Pada HOST kosong, provisioning lima Ubuntu tersedia melalui:

```bash
sudo python3 scripts/create_lab.py --image /PATH/UBUNTU22_IMAGE.img \
  --public-key /PATH/OPERATOR_KEY.pub --operator NAMA_USER_HOST \
  --output /PATH/INVENTORY_PRIVAT_BARU
```

Jangan jalankan bila VM/jaringan tersebut sudah ada. Konfirmasi host key SSH lewat
console. Isi inventory lima role mengikuti `deploy/inventory.example.json`, lalu
jalankan `python3 scripts/ssh_preflight.py /PATH/inventory.json`; semua harus `ok`.

Di root repo commit yang disetujui, siapkan runtime dan arsip source:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -c deploy/constraints.txt .
git archive --format=tar.gz HEAD -o /PATH/vanguard-source.tar.gz
```

### 9.2 Install, generate CA dan siapkan admin

**HOST, hanya lingkungan baru:** gunakan direktori state privat yang sama untuk
semua fase. Jangan gunakan `--phase all` untuk setup ini.

```bash
.venv/bin/python scripts/deploy_lab.py /PATH/inventory.json \
  --state /PATH/STATE_PRIVAT --archive /PATH/vanguard-source.tar.gz --phase install
.venv/bin/python scripts/deploy_lab.py /PATH/inventory.json \
  --state /PATH/STATE_PRIVAT --phase configure
.venv/bin/python scripts/deploy_lab.py /PATH/inventory.json \
  --state /PATH/STATE_PRIVAT --phase admin
```

- `install`: memasang aplikasi/unit sesuai role, belum menjalankan service/firewall.
- `configure`: membuat CA pada VM-CA bila belum ada, membuat key/CSR HTTPS di tiap
  layanan, menandatanganinya, memasang root publik, token env dan identitas client Ubuntu.
- `admin`: membuat akun dashboard dan onboarding TOTP di state privat. Daftarkan
  TOTP ke authenticator; catat username/password hanya di inventaris privat.

Perintah CA yang dipakai fase configure adalah:
`sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca init`.
**Jangan menjalankannya lagi sesudah configure.** Root/private key tetap di CA;
setiap endpoint baru hanya membuat CSR dan kunci sendiri.

Di VM-CA, periksa root dan CRL yang sudah dihasilkan:

```bash
openssl x509 -in /etc/vanguard/root.crt -noout -subject -issuer -dates -fingerprint -sha256
openssl verify -check_ss_sig -CAfile /etc/vanguard/root.crt /etc/vanguard/root.crt
sudo openssl crl -in /var/lib/vanguard/ca/crl.pem -noout -lastupdate -nextupdate
```

Cocokkan fingerprint melalui console CA sebelum mempercayai salinan root. Fase
configure menyiapkan HTTPS SAN.10/.20/.40; private key HTTPS tetap pada VM asal.
Jangan memakai contoh lab untuk alamat lain tanpa mengubah SAN/routing yang sesuai.

### 9.3 Firewall dan mulai layanan

Di setiap guest, pasang nftables dan salin `deploy/firewall.py` ke
`/opt/vanguard/firewall.py`. Jalankan sesuai role:

```bash
sudo python3 /opt/vanguard/firewall.py ROLE --management-ip 192.168.100.1
# Khusus SERVER, gunakan ini sebagai pengganti baris ROLE di atas:
sudo python3 /opt/vanguard/firewall.py server --management-ip 192.168.100.1 \
  --windows-client --application-policy
```

Skrip memasang timer rollback120detik. Buka **SSH baru**, pastikan firewall aktif,
baru hentikan `vanguard-firewall-rollback.timer` pada guest tersebut. Bila gagal,
gunakan console/rollback. Siapkan policy aplikasi kosong dan env
`VANGUARD_RESOURCE_POLICY` sebelum memberi grant di Bagian5.

**HOST:**

```bash
.venv/bin/python scripts/deploy_lab.py /PATH/inventory.json \
  --state /PATH/STATE_PRIVAT --phase start
```

Layanan dimulai CA → server → admin. Sebelum admission, server harus tanpa peer:
`sudo wg show wg0 peers`. Lanjutkan pemeriksaan Bagian1, profil, lalu endpoint.
Backup CA lengkap harus menjaga root/key/index/serial/crlnumber/CRL/sertifikat
sebagai satu state konsisten; jangan memulihkan sebagian file lama.

## 10. Masalah umum dan pemeriksaan akhir

| Gejala | Tindakan |
|---|---|
| Readiness503/unknown | Periksa service, jam, disk dan dependency. Catat kegagalan; HTTP200 sesudah retry tidak menghapus kejadian awal |
| Configure ditolak | Cocokkan profil/root/fingerprint/key; jangan hapus trust lama untuk memaksa lolos |
| Login gagal | Periksa akun karyawan, password, status aktif dan koneksi HTTPS |
| Pending registration / exit20 | Tunggu admin; perbaiki dependency, gunakan request/key yang sama |
| Connect gagal | Periksa sertifikat, sesi, binding, route dan UDP51820; jangan pasang peer manual |
| Tunnel ada tetapi aplikasi gagal | Periksa grant resource/protokol/port dan service aplikasi |
| Sesi habis | Login kembali; renewal lease tidak memperpanjang sertifikat |
| Cleanup belum pasti | Pertahankan config; pastikan pemilik dan tunnel/service berhenti |
| Sertifikat dicabut/expired | Admin menjalankan alur penggantian identitas Bagian6 |

Sebelum serah terima, buktikan: akses sah berhasil, tanpa izin ditolak, revoke
memutus akses terkait, perangkat lain tetap bekerja, logout dan cleanup selesai.
Catat waktu, versi/OS, PASS/FAIL/BELUM_TERUJI dan lokasi bukti; jangan merekam password,
OTP, token atau private key. Simpan backup sebelum upgrade; uninstall bukan revoke.

**Referensi:** [checkpoint](CHECKPOINT.md), [API](API.md),
[keamanan](SECURITY.md), [hasil uji terbaru](UJI_INTEGRASI_0.1.14_2026-10-31.md).
Flowchart tersimpan terpisah agar manual tetap singkat:
[backend](assets/flows/01-backend.svg) · [installer](assets/flows/02-installer.svg) ·
[pendaftaran](assets/flows/03-enrollment.svg) · [akses](assets/flows/04-access.svg) ·
[lifecycle](assets/flows/05-lifecycle.svg).
