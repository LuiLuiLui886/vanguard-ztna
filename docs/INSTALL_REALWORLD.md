# Pemasangan VanGuard pada perangkat nyata

Panduan operator dan pengguna —22 Oktober2026. Topologi sudah dikonfirmasi:
router khusus, backend VM pada laptop Linux, PC Windows LAN dan laptop Windows
Wi-Fi. Tujuan tahap pertama adalah **pilot nyata terbatas**, bukan membuka layanan
ke internet atau menyatakan siap produksi. Installer Windows masih kandidat0.1.12
r3; native UAC/ACL/repair dan jaringan kedua endpoint harus dibuktikan pada target.

## 1. Siapkan perangkat dan pembagian tugas

| Komponen | Yang disiapkan | Alamat rencana |
|---|---|---|
| Router khusus | Admin router, DHCP reservation, LAN dan SSID uji saling terhubung; jangan memakai guest isolation | 192.168.50.1/24 |
| Laptop Linux host | Catu daya, kabel LAN, akses admin lokal/console, ruang backup dan RAM untuk tiga backend VM | 192.168.50.10/24 |
| PC Windows11 x64 | Kabel LAN, admin lokal, waktu benar, PowerShell5.1, Python3.13 x64 dan WireGuard resmi | 192.168.50.20/24 |
| Laptop Windows11 x64 | Wi-Fi ke SSID uji, admin lokal, prasyarat sama | 192.168.50.30/24 |
| Backend | VM-CA, VM-SERVER, VM-ADMIN yang sudah ada; VM client/attacker lama tetap disimpan | .100.10/.100.20/.100.40 |

Gunakan dua kabel Ethernet untuk router–host dan router–PC; laptop endpoint lewat
Wi-Fi. Jangan ubah subnet/backend VM atau mengganti lima Ubuntu dan satu Windows
lama. Host harus tetap mendapat pendinginan/daya dan tidak sleep saat layanan
berjalan. Kapasitas host diperiksa terhadap alokasi VM yang sudah ada; jangan
menyalakan seluruh guest sekaligus hanya untuk pilot. Simpan akses console untuk
pemulihan ketika rute/SSH salah.

Pembagian pekerjaan: operator host mengurus VM/routing/firewall/backup; admin
VanGuard mengurus akun, binding, sertifikat dan grant; karyawan hanya menjalankan
client/login. Password dan username operasional hanya dicatat pada inventaris
privat komputer ini, bukan kit, GitHub, screenshot atau laporan hasil.

**Kondisi saat kit disiapkan:** host masih Wi-Fi192.168.66.9/24, Ethernet belum
memiliki alamat pilot, keenam VM mati. Karena itu kit belum boleh dianggap sudah
memberikan akses. Pemeriksa host memang mengembalikan BLOCKED pada kondisi ini.

## 2. Isi kit dan cara memeriksa integritas

Ekstrak ZIP kit ke folder baru. Jangan mencampur dengan rilis/identitas lama.

| Isi | Kegunaan |
|---|---|
| START_HERE.html | Halaman mulai yang dibuka di browser |
| windows/ | Kandidat installer BAT/PowerShell r3 dan20wheel Windows offline |
| config/ | Profil publik, root publik, rencana jaringan, contoh env admin |
| backend/ | Wheel0.1.12 untuk upgrade aplikasi admin; firewall kandidat dan halaman demo publik |
| checks/ | Pemeriksa integritas, host Linux dan endpoint Windows read-only |
| docs/ | Panduan ini, modul lengkap CA–pengguna dan histori/batas bukti |
| ACCEPTANCE.csv | Template hasil PC, laptop dan penggunaan bersamaan; awalnya belum diuji |
| DEPLOYMENT_STATUS.json | Status kandidat/bagian yang belum tervalidasi |
| kit-manifest.json | SHA256 setiap file; hash manifest harus diperiksa dari kanal lain |

Runtime installer Python/WireGuard **tidak disertakan**. Python wheel offline
sudah ada; instalasi prasyarat runtime tetap tahap terpisah. Jangan memakai
installer0.1.7 VM atau deploy/windows/bootstrap.ps1 pada perangkat fisik.

Operator memberi SHA256 ZIP dan manifest melalui kanal tepercaya terpisah.
Di Windows gunakan Get-FileHash; di Linux gunakan sha256sum. Membandingkan hash
hanya dengan file dari unduhan yang sama tidak membuktikan autentisitas.
Setelah hash ZIP cocok, ekstrak, lalu verifikasi seluruh anggota kit:

```powershell
# WINDOWS ADMIN: ubah path sesuai lokasi kit. Hash harus datang dari operator.
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\lokasi\vanguard-realworld-pilot-20261022.zip'
& 'C:\Program Files\Python313\python.exe' `
  'C:\Program Files\VanGuardPilotKit\checks\verify_kit.py' `
  'C:\Program Files\VanGuardPilotKit' --expected-manifest-sha256 'HASH_MANIFEST_DARI_OPERATOR'
```

Pemeriksa integritas menolak hash berubah, file tambahan/hilang, symlink dan path
keluar kit. Hasil PASS hanya integritas, bukan Windows/layanan sudah aman atau
siap. Simpan hasil acceptance di folder laporan **di luar kit**, supaya anggota
paket tetap sama dengan manifest. Jangan mengedit template ACCEPTANCE di dalam
kit; salin dahulu ke folder hasil.

## 3. Siapkan Python dan WireGuard pada Windows

Unduh Python Windows installer64-bit seri3.13 dari
[halaman resmi Python](https://www.python.org/downloads/windows/); pilih installer
penuh, bukan embeddable ZIP. Pada pemeriksaan22 Oktober, seri3.13 terbaru di
halaman resmi adalah3.13.17; wheel kandidat dibangun untuk CPython3.13/win_amd64.
Versi patch pada perangkat tetap wajib dicatat dan diuji, tidak otomatis dianggap
lulus karena sama seri. Gunakan Custom installation, sertakan pip/venv, Install
for all users ke `C:\Program Files\Python313`. Hindari mengubah PATH global jika
aplikasi lain memakai Python; launcher menggunakan path absolut.

Unduh WireGuard dari [halaman instalasi resmi](https://www.wireguard.com/install/).
Operator memeriksa Authenticode valid dan publisher Python Software Foundation/
WireGuard sesuai artefak. Jangan mengambil installer dari tautan pihak ketiga atau
menonaktifkan Defender/SmartScreen/execution policy. Jika kebijakan organisasi
mengharuskan signing script, tanda tangani kandidat melalui proses organisasi
sebelum uji; paket sekarang belum signed.

Contoh pemeriksaan **sebelum** menjalankan installer yang diunduh:

```powershell
Get-AuthenticodeSignature -LiteralPath 'C:\lokasi\installer-yang-diunduh.exe' |
  Select-Object Status,@{Name='Publisher';Expression={$_.SignerCertificate.Subject}}
```

Nama/path di atas placeholder, bukan file yang disertakan. Hash resmi/publisher
harus ditinjau operator; status valid tidak menggantikan pemeriksaan publisher.
Jika runtime sudah ada, jangan downgrade atau menimpa runtime aplikasi lain.
Gunakan path yang cocok prasyarat; versi/arsitektur lain adalah blocker kandidat.

Setelah pemasangan, operator mengonfirmasi sertifikat signer **wireguard.exe yang
terpasang** lewat kanal tepercaya, termasuk thumbprint. Jangan menyalin thumbprint
dari executable yang belum dipercaya lalu menyebutnya verifikasi independen.

```powershell
& 'C:\Program Files\Python313\python.exe' -c "import sys,struct,venv,ensurepip; print(sys.version); print(struct.calcsize('P')*8)"
Get-AuthenticodeSignature -LiteralPath 'C:\Program Files\WireGuard\wireguard.exe' |
  Select-Object Status,@{Name='Publisher';Expression={$_.SignerCertificate.Subject}},@{Name='Thumbprint';Expression={$_.SignerCertificate.Thumbprint}}
```

Jangan mengimpor konfigurasi WireGuard manual/static peer. VanGuard mengelola
service tunnel setelah admission, dan private key dibuat kemudian oleh client.

## 4. Backup sebelum perubahan aktif

Catat waktu dan baseline, ruang disk serta lokasi backup di inventaris privat.
Saat guest mati, backup disk guest/UEFI/TPM serta XML melalui prosedur hypervisor;
jangan menyalin disk yang aktif tanpa mekanisme konsistensi. Preserve seluruh enam
VM, terutama CA dan identitas utama. Untuk upgrade aplikasi admin, gunakan backup
service yang dihentikan seperti Bagian6. Backup bukan izin memulihkan CA lama.

Pada host, simpan XML/daftar disk, route, konfigurasi jaringan, ruleset host/libvirt,
konfigurasi router dan akses pemulihan. Contoh keluaran hanya ke folder privat:

```bash
# HOST: baru snapshot read-only; tidak menyalakan atau mengubah jaringan.
umask 077
backup_dir="$HOME/VanGuard-Privat/pilot-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 "$backup_dir"
virsh -c qemu:///system dumpxml VM-CA > "$backup_dir/VM-CA.xml"
virsh -c qemu:///system domblklist VM-CA --details > "$backup_dir/VM-CA-disks.txt"
ip -j -4 address show > "$backup_dir/addresses.json"
ip -j -4 route show > "$backup_dir/routes.json"
# Ulangi XML/daftar disk untuk lima guest lain; simpan firewall via admin host.
```

Jangan mengunggah backup atau environment/database. Pastikan backup dapat dibaca,
checksum cocok dan lokasi disk benar sebelum mengubah apa pun. Jangan restore
index, serial, crlnumber, CRL atau database keamanan lama saat rollback aplikasi.

## 5. Siapkan jaringan khusus dan backend yang ada

1. Hubungkan host dan PC ke LAN router, laptop ke SSID uji. Operator router
   menetapkan .50.1/24 dan reservation .50.10/.20/.30; hindari konflik DHCP/static.
   Default gateway endpoint .50.1. Jangan mengubah jaringan rumah/kantor utama.
2. Host mendapat .50.10/24 pada Ethernet; backend libvirt tetap .100/24. Pertahankan
   Wi-Fi administrasi sampai jalur LAN/console teruji. Jangan bridge NIC backend,
   menghapus NAT libvirt, mengubah kernel atau memasang custom WireGuard.
3. Setelah backup terverifikasi, nyalakan backend bertahap: CA, server, admin.
   Windows VM/client/attacker lama tidak wajib hidup untuk pilot ini. Periksa
   waktu/NTP, service readiness, freshness CRL dan disk/log. CRL kedaluwarsa harus
   diperbaiki lewat mekanisme CA yang sah; jangan melewati pemeriksaannya.
4. Pada setiap endpoint, inspeksi adapter; tambahkan host route .100.20/32 melalui
   .50.10 pada adapter yang benar. Jangan membuat route default ke laptop host.
5. Tinjau forwarding host/libvirt dan return path, kemudian firewall VM-SERVER.
   Dua sumber .50.20/.30 hanya boleh ke .100.20 TCP8081 dan UDP51820. Jangan buka
   CA8080/admin5000 atau aplikasi8082 langsung dari LAN. Admin tetap melalui
   jalur management host yang sudah ada.

Perintah tahap penerapan backend (jalankan satu per satu setelah backup):

```bash
# HOST: perintah ini menyalakan VM; hanya ketika tahap penerapan sudah dimulai.
virsh -c qemu:///system start VM-CA
virsh -c qemu:///system start VM-SERVER
virsh -c qemu:///system start VM-ADMIN
```

Jangan menjalankan `start` pada guest yang sudah hidup; cek `virsh list --all`.
Di setiap guest, periksa service terkait; server juga vanguard-daemon/wg-quick@wg0.
Tidak ada peer statis pada wg0. TLS/readiness harus diperiksa dari jalur yang
memang diizinkan, misalnya server menuju CA dan admin menuju server.

```bash
# VM-ADMIN dengan trust anchor yang sudah dipasang melalui kanal tepercaya.
curl --fail --show-error --silent --connect-timeout 3 --max-time 8 \
  --cacert /etc/vanguard/root.crt https://192.168.100.20:8081/readyz
```

TCP berhasil/ping bukan bukti UDP siap. Rule `backend/server-firewall.candidate.nft`
adalah bahan review, **jangan langsung apply**. Pastikan management IP .100.1 dan
aturan layanan lama cocok, buat backup ruleset, jalankan nft syntax check di
VM-SERVER, dan gunakan rollback terjadwal yang mempertahankan akses console.
Host firewall belum diketahui backend/chain efektifnya; accept pada chain nft
baru dapat tetap kalah oleh drop chain libvirt lain. Operator harus memeriksa
ruleset aktual sebelum menentukan lokasi rule. Rincian matriks ada pada
[panduan pilot](ENDPOINT_WINDOWS_PILOT.md); tidak ada script host yang menebak
aturan atau flush firewall global.

Contoh route sementara setelah interface dikonfirmasi, Windows Administrator:

```powershell
Get-NetIPConfiguration
Get-NetRoute -AddressFamily IPv4
# Isi $ifIndex dari adapter LAN/Wi-Fi yang mempunyai IP endpoint yang disetujui.
New-NetRoute -DestinationPrefix '192.168.100.20/32' -InterfaceIndex $ifIndex `
  -NextHop '192.168.50.10' -PolicyStore ActiveStore
```

Jangan menambah jika sudah ada route identik. ActiveStore hilang saat reboot;
uji ulang preflight setelah boot. Persistensi baru diputuskan setelah pilot lolos.
Router tidak memerlukan static route backend jika kedua endpoint memakai /32 ini.

Jalankan pemeriksa host dari kit:

```bash
python3 checks/pilot_preflight.py
```

Script hanya membaca alamat, forwarding flag dan status6VM dengan batas waktu;
tidak sudo, menyalakan guest, membuka port atau mengubah route. Exit2 berarti
FAIL/UNKNOWN atau review manual masih diperlukan. Bahkan semua cek otomatis PASS
belum membuktikan firewall/TLS/UDP/aplikasi. Gunakan report untuk memperbaiki
prasyarat, bukan menganggap script gagal karena tidak mengembalikan ready.

## 6. Siapkan profil dan upgrade aplikasi admin

Profil kit menggunakan salinan root/public key lokal. **Bandingkan lagi dengan
layanan aktif**: fingerprint root DER dan server WireGuard public key. Jangan
membaca/mengirim server private key. Contoh read-only di node yang benar:

```bash
# VM-ADMIN atau VM-CA: fingerprint trust anchor publik.
openssl x509 -in /etc/vanguard/root.crt -outform DER | sha256sum
# VM-SERVER: hanya public key interface, bukan konfigurasi/private key.
sudo wg show wg0 public-key
```

Jika berbeda, berhenti dan telusuri asal/root/rotasi. Jangan menimpa trust agar
cocok kit. Operator membangun ulang profil/kit dari root/key publik yang sah.
Dengan routing .100.20, SAN HTTPS lama tetap sesuai; tidak perlu membuat CA
baru atau mengganti sertifikat layanan hanya untuk pilot ini.

Kontrak server0.1.11 sudah mendukung admission/logout/resource gate yang diperlukan.
Untuk bundle berprofil, **VM-ADMIN perlu aplikasi0.1.12** dan environment baru.
CA/server tidak perlu di-upgrade untuk sekadar menambah field profil pada bundle.
Jangan menjalankan deploy/install.sh sebagai upgrade buta terhadap seluruh lab.
Wheel backend di kit sama hash dengan wheel aplikasi pada paket Windows; dependensi
aplikasi0.1.11 dan0.1.12 sama. Jika pip check gagal, hentikan upgrade dan tinjau
runtime, jangan mengunduh/mengganti dependency diam-diam.

Operator menyalin wheel dan config publik ke `/srv/vanguard-pilot/` pada VM-ADMIN,
direktori milik root yang tidak writable akun biasa. Hash dicek terhadap manifest.
Contoh urutan pada **VM-ADMIN saja**, setelah jalur pemulihan tersedia:

```bash
sudo systemctl stop vanguard-admin
# Pastikan inactive sebelum backup konsisten; jika stop gagal, jangan lanjut.
sudo systemctl is-active vanguard-admin
```

`is-active` harus menampilkan inactive (exit nonzero memang diharapkan). Backup
root-only yang baru harus mencakup `/opt/vanguard/venv`, `/var/lib/vanguard/admin`,
`/etc/vanguard/admin.env`, profil lama jika ada, dan unit. Hindari memasukkan
isi environment ke terminal/log. Contoh backup konsisten, setelah admin inactive:

```bash
# VM-ADMIN: arsip memuat rahasia; hanya root, jangan dikirim bersama kit.
pilot_backup="/var/backups/vanguard-pilot/$(date +%Y%m%d-%H%M%S)"
sudo install -d -m 0700 "$pilot_backup"
sudo tar --acls --xattrs -cpf "$pilot_backup/admin-before.tar" -C / \
  opt/vanguard/venv var/lib/vanguard/admin etc/vanguard \
  etc/systemd/system/vanguard-admin.service
sudo chmod 0600 "$pilot_backup/admin-before.tar"
sudo tar -tf "$pilot_backup/admin-before.tar" > /dev/null
sudo sha256sum "$pilot_backup/admin-before.tar"
```

Jika arsip/checksum gagal, jangan upgrade. Arsip DB menjadi bukti pemulihan yang
harus direview, bukan bahan rollback rutin. Setelah backup terverifikasi:

```bash
sudo /opt/vanguard/venv/bin/python -m pip install --no-index --no-deps \
  /srv/vanguard-pilot/backend/vanguard_ztna-0.1.12-py3-none-any.whl
sudo /opt/vanguard/venv/bin/python -m pip check
sudo install -o root -g vanguard -m 0640 \
  /srv/vanguard-pilot/config/profile.json /etc/vanguard/endpoint-profile.json
sudoedit /etc/vanguard/admin.env
```

Tambahkan tepat satu baris `VANGUARD_CLIENT_PROFILE=/etc/vanguard/endpoint-profile.json`;
pertahankan semua nilai env lain, terutama secret/token. Jangan mengganti env dengan
file contoh kit. Lalu mulai admin dan periksa readiness/bundle tanpa menerbitkan
sertifikat uji pada health check:

```bash
sudo systemctl start vanguard-admin
sudo systemctl is-active vanguard-admin
curl --fail --show-error --silent --connect-timeout 3 --max-time 8 \
  --cacert /etc/vanguard/root.crt https://192.168.100.40:5000/readyz
```

Jika gagal, pertahankan log yang disaring, hentikan admin dan pulihkan runtime/env/
profil/unit dari backup kompatibel. Jangan rollback database/CA untuk membatalkan
upgrade paket. Paket/backup/izin aktual harus diverifikasi operator; contoh di
atas belum dieksekusi oleh kit.

## 7. Install pada PC Windows LAN dahulu

1. Pastikan admin lokal, runtime, IP/route dan backend siap. Salin kit yang sudah
   dicek hash ke `C:\Program Files\VanGuardPilotKit` menggunakan Explorer/terminal
   Administrator. Periksa ACL: SYSTEM/Administrators boleh tulis; Users hanya
   baca. Sumber root/profil juga harus terlindungi. Jangan memakai Downloads
   writable pengguna sebagai sumber script elevated. Hindari junction/reparse.
2. Buka PowerShell Administrator, jalankan pemeriksaan. Script tidak mengubah
   jaringan/key/service; hasil FAIL/UNKNOWN harus ditindaklanjuti.

```powershell
& 'C:\Program Files\VanGuardPilotKit\checks\Check-Endpoint.ps1' -Role PC
```

Untuk path Python berbeda, tambahkan `-PythonPath 'PATH_PYTHON_TERVERIFIKASI'`.
Exit2 selalu meminta pemeriksaan manual/native lanjutan; tidak menandai siap
produksi. Script PowerShell pemeriksa ini belum diuji native pada target.

3. Jalankan `windows\Install-VanGuard.bat`. UAC bila belum elevated; masukkan
   hash **windows/manifest.json**, bukan kit-manifest, path Python yang diverifikasi,
   dan thumbprint signer WireGuard terpasang yang dikonfirmasi operator. Hash
   endpoint r3: `47b50e47e156e1b41ff11ffba01e0e76433eb5f96cfde81b4b6df8361f530cb1`.
4. Exit0 berarti runtime aplikasi terpasang; belum ada key, login, peer atau VPN.
   Exit1 berarti gagal;1223 UAC batal. Jangan menghapus state/key untuk mengulang.
5. Launcher terpasang di Program Files, konfigurasi/identitas terpisah. Jalankan:

```powershell
$launcher = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.ps1'
& $launcher -Action configure
& $launcher -Action status
& $launcher -Action init
```

Configure: pilih `config\profile.json` dan `config\root.crt` dari kit terlindungi,
konfirmasi fingerprint root dan public key server lewat admin. Init: masukkan
**ID perangkat/IP tunnel yang dialokasikan admin**. Usulan PC10.8.0.5/laptop.6
harus dicek registry terlebih dahulu; .2/.3/.4 jangan dipakai. Jangan memakai
identitas VM-client untuk perangkat fisik baru. Private key dibuat pada PC.

## 8. Enrollment, login dan penggunaan oleh karyawan

1. Kirim hanya `request.json` dari identity PC ke admin melalui kanal tepercaya.
   Lokasi identity: `%ProgramFiles%\VanGuardEndpointData\identity`. Jangan
   mengirim identity.key, wg.key atau employee-session.json.
2. Admin membuka dashboard dari jalur management yang sudah ada, login+TOTP,
   membuat/memilih akun karyawan, mengunggah request, memeriksa ID/WG public key/IP,
   lalu mengikat akun. Registrasi tidak boleh menambah peer.
3. Admin mengunduh bundle publik hasil registrasi dan mengirimkannya ke PC.
   Import harus memakai identity asli yang membuat request. Bundle/profil/root
   berbeda ditolak; jangan memaksa overwrite. Jalankan:

```powershell
& $launcher -Action import-bundle
& $launcher -Action diagnose
& $launcher -Action login
& $launcher -Action connect
```

Import menanyakan ZIP; login menanyakan username, password diketik tersembunyi.
Tidak ada password pada command-line atau kit. Diagnose memeriksa HTTPS readiness;
UDP/aplikasi tetap unknown. Connect melakukan enam pemeriksaan perangkat+sesi,
lalu tunnel dibuat jika admission diterima. Terminal harus tetap terbuka untuk
renewal. Status file lokal atau service installed bukan bukti handshake/aplikasi.

4. Admin memeriksa registered/lease valid/peer/handshake/transfer secara terpisah.
   Karyawan baru dapat mengakses demo setelah ada grant eksplisit yang sesuai.
   Ulangi untuk laptop Wi-Fi menggunakan `-Role Laptop`, identitas dan IP berbeda;
   PC harus lulus dulu sebelum keduanya dipakai bersama.

## 9. Siapkan resource demo dan buktikan akses

Pilot hanya mencakup HTTP uji10.8.0.1 TCP8082. Tidak menyediakan internet penuh
atau aplikasi bisnis otomatis. Operator menjalankan demo sementara pada server
melalui service yang dikelola; jangan menaruh data sensitif atau bind demo sebagai
jalan pintas LAN. Admin/server menetapkan kebijakan tuple:
`device_id + username + internal-demo + 10.8.0.1 + tcp + 8082`.
Contoh demo sementara pada VM-SERVER setelah firewall gate terverifikasi. Salin
hanya `backend/demo/index.html` publik dari kit ke staging operator. Gunakan
folder baru milik pilot; jangan menimpa service/folder aplikasi yang sudah ada.

```bash
# VM-SERVER: mulai service demo hanya saat pilot; bukan bagian otomatis installer.
sudo install -d -o root -g root -m 0755 /srv/vanguard-pilot-demo
sudo install -o root -g root -m 0644 \
  /srv/vanguard-pilot/backend/demo/index.html /srv/vanguard-pilot-demo/index.html
sudo systemd-run --unit=vanguard-pilot-demo --uid=vanguard \
  --property=NoNewPrivileges=yes --property=ProtectSystem=strict \
  --property=ProtectHome=yes /usr/bin/python3 -m http.server 8082 \
  --bind 10.8.0.1 --directory /srv/vanguard-pilot-demo
```

Service berjalan sebagai user non-root dan hanya bind alamat tunnel. Jangan
menyimpulkan aman dari bind saja; gate aplikasi juga wajib menolak ingress LAN.
Jika nama unit/folder sudah dipakai, inspeksi ownership sebelum menggunakan nama
lain. Hentikan dengan `sudo systemctl stop vanguard-pilot-demo` setelah pengujian.

File kebijakan server mengikuti path `VANGUARD_RESOURCE_POLICY` yang dikonfigurasi
pada server (umumnya `/etc/vanguard/resource-policy.json`), bukan profil client. Pertahankan grant lain yang masih sah; lakukan perubahan dengan validator
kebijakan/prosedur server. Nilai karyawan aktual hanya inventaris privat.

Format satu grant (placeholder, bukan akun yang otomatis dibuat):

```json
{"grants":[{"device_id":"ID_PERANGKAT","username":"AKUN_KARYAWAN","resource":"internal-demo","address":"10.8.0.1","protocol":"tcp","port":8082}]}
```

Siapkan kandidat file kebijakan privat yang mempertahankan grant sah lainnya.
Validasi dengan loader aplikasi sebelum operator menerapkannya; output cukup
jumlah grant, jangan cetak isi akun:

```bash
# VM-SERVER: validasi kandidat lokal, tidak memasang grant/peer.
sudo /opt/vanguard/venv/bin/python -c \
  "from vanguard.resource_policy import load_policy; print('policy valid; grants:',len(load_policy('/etc/vanguard/resource-policy.candidate.json')))"
```

Operator mempublikasikan file tervalidasi secara atomic pada path kebijakan yang
sudah dikonfirmasi, mode0600/root. Daemon/renewal menyinkronkan set akses dari
kebijakan+sesi/lease; jangan menambahkan elemen nft manual untuk melewati admission.
Jika gate/env belum aktif, berhenti dan selesaikan rollout gate dengan backup;
keberadaan file JSON saja tidak mengaktifkan enforcement.

Uji HTTP dari endpoint setelah admission dan grant:

```powershell
curl.exe --connect-timeout 3 --max-time 8 http://10.8.0.1:8082/
```

Syarat minimum penerimaan pilot:

| Pengujian | Hasil wajib |
|---|---|
| Install/enrollment/login saja | Belum ada peer otomatis |
| Perangkat sah+akun sah+enam cek lolos | Lease dan peer sesuai, handshake teramati |
| HTTP dengan grant tepat | Berhasil lewat tunnel |
| Tanpa grant/port lain/LAN langsung .100.20:8082 | Ditolak |
| Identitas tidak terdaftar/expired/revoked/akun nonaktif | Ditolak, akses terkait dibersihkan |
| Renewal berulang | Lease diperbarui; validity sertifikat tidak berubah |
| Logout/revoke PC saat TCP aktif | Akses PC terputus; laptop tetap bekerja |
| Tukar peran PC/laptop | Isolasi sama, tanpa menghidupkan identitas revoked |
| Wi-Fi putus/sambung/reboot | Tidak reconnect dengan akses statis; fresh admission wajib |
| Cleanup gagal | Config dipertahankan sampai ownership/tunnel down pasti |
| Repair/upgrade/uninstall | Key/config dipertahankan; komponen shared tidak dihapus |

Salin ACCEPTANCE.csv keluar kit. Catat PASS/FAIL/BELUM_DIJALANKAN, waktu UTC/WIB,
versi, ID uji, lease/handshake/transfer, hasil HTTP dan lokasi bukti tersaring.
Jangan mengisi PASS hanya karena checklist tersedia. Tes Linux sebelumnya260/1
bukan bukti kedua endpoint fisik.

## 10. Disconnect, logout dan pemulihan

Pada terminal pemilik, Ctrl+C meminta cleanup. Dari terminal administrator lain:

```powershell
$launcher = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.ps1'
& $launcher -Action disconnect
& $launcher -Action logout
```

Disconnect menghentikan tunnel lokal, tidak mencabut token server. Logout mencabut
sesi/challenge/lease terkait saja. Jika server tak terjangkau, pencabutan server
belum terkonfirmasi; hubungi admin dan retry setelah konektivitas pulih. Jangan
menghapus config ketika service/tunnel down belum pasti. Jangan taskkill massal.

Jika service hang (WIN-CLEANUP-02): cabut akses di server, verifikasi peer/grant
hilang, identifikasi service/proses pemilik, pastikan teardown sebelum config
diarsipkan. Jangan menimpa key atau menghapus VPN lain agar bisa connect lagi.

Setelah uji: cabut identitas/sesi/grant disposable, disable akun uji sesuai scope,
hentikan demo sementara, hapus hanya route/rule pilot yang baru dibuat. Kembalikan
config/runtime dari backup bila perlu, **tanpa restore CA/database keamanan lama**.
Uninstall mempertahankan identity/config dan Python/WireGuard shared; decommission
server harus dikonfirmasi dahulu. Lease/cert expiry, soak panjang dan media
power-loss CA masih perlu pengujian terpisah sebelum klaim produksi.

## 11. Apa yang sudah siap dan yang belum

Source aplikasi0.1.12, paket offline Windows r3, public profile, wheel admin,
generator firewall, pemeriksa read-only, template acceptance dan panduan tersedia.
Kit dibangun/diverifikasi lokal; hasil terbaru dicatat pada CHECKPOINT/jurnal.
Tidak ada credential/private key atau runtime installer dalam kit.

Belum selesai di target: native PowerShell/UAC/ACL/fresh/repair/upgrade/uninstall,
runtime/signing sesuai kebijakan, kabel/router/IP pilot, host forwarding efektif,
readiness live, registry alokasi .5/.6 dan pengujian dua endpoint. Langkah berikutnya
adalah menyambungkan router/topologi, menyelesaikan baseline/backup, kemudian uji
native Windows dan pemasangan PC dahulu. Jangan membuka layanan ke internet atau
menganggap paket unsigned sebagai release produksi.
