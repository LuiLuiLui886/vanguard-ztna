# Pemasangan VanGuard pada perangkat nyata

Runbook penerapan lengkap, revisi dokumentasi2 —22 Oktober2026. Topologi sudah dikonfirmasi:
router khusus, backend VM pada laptop Linux, PC Windows LAN dan laptop Windows
Wi-Fi. Tujuan tahap pertama adalah **pilot nyata terbatas**, bukan membuka layanan
ke internet atau menyatakan siap produksi. Installer Windows masih kandidat0.1.12
r3; native UAC/ACL/repair dan jaringan kedua endpoint harus dibuktikan pada target.

## Cara membaca dan mengisi dokumen

Dokumen ini adalah panduan kerja, bukan laporan bahwa penerapan telah selesai.
Bab1–10 berisi langkah instalasi/pemakaian; Bab12–17 berisi lembar kendali,
pemeriksaan tiap tahap, troubleshooting, operasi dan serah terima. Hasil aktual
harus dicatat pada lembar pelaksanaan, bukan mengganti status hanya karena perintah
sudah tersedia. Versi HTML memiliki daftar isi dan dapat dicetak ke PDF: Ctrl+P →
Simpan sebagai PDF → A4. Buka seluruh folder docs agar tautan pendukung berfungsi.

| Pembaca | Jalur kerja |
|---|---|
| Operator host/backend | Bab1–6,9–10,12–17; siapkan pemulihan sebelum perubahan |
| Admin VanGuard | Bab6,8–10,13–17; kelola akun/binding/grant dan arsip aktivitas |
| Karyawan PC/laptop | Bab3,7–8,10 dan troubleshooting Bab14; jangan mengubah CA/firewall |
| Penguji/pembimbing | Bab9,11,13,15–17; bedakan bukti unit/native/fisik |

Label HOST berarti laptop Linux, VM-ADMIN/VM-SERVER/VM-CA berarti guest yang
bersangkutan, WINDOWS ADMIN berarti PowerShell elevated di endpoint yang sedang
diuji. Jangan menyalin semua blok sekaligus. Contoh `$ifIndex`, `HASH_...`, ID/IP
alokasi, nama akun dan path installer harus diisi dari pemeriksaan aktual. Jangan
mengetik placeholder secara literal lalu menganggap kegagalan sebagai bug sistem.

Sumber implementasi kandidat: aplikasi0.1.12 dan installer Windows r3. Revisi
panduan ini tidak mengubah versi aplikasi atau memberi hasil uji native baru.

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

## 12. Lembar rencana dan topologi yang harus disepakati

Isi sebelum window penerapan. Catat kontak penanggung jawab secara privat;
lembar publik cukup role atau kode petugas. Tidak ada password pada lembar ini.

| Field | Rencana | Aktual saat pelaksanaan |
|---|---|---|
| Waktu mulai/selesai dan zona waktu | Window yang disepakati | BELUM_DIISI |
| Operator host/backend, admin, penguji | Tiga peran; boleh satu orang dengan catatan | BELUM_DIISI |
| Hash kit/manifest dan versi aplikasi | Dari operator melalui kanal tepercaya | BELUM_DIISI |
| Model/router/firmware dan port LAN | Router khusus, bukan jaringan utama | BELUM_DIISI |
| SSID uji, guest isolation, client isolation | LAN dan Wi-Fi uji dapat berkomunikasi sesuai kebijakan | BELUM_DIISI |
| Interface Ethernet host | Nama nyata dari ip address, bukan tebakan | BELUM_DIISI |
| Alokasi DHCP/static dan konflik IP | .50.10/.20/.30 terpisah dan tidak duplikat | BELUM_DIISI |
| Akses console/backup dan verifikasi checksum | Lokasi privat, dapat dibaca operator | BELUM_DIISI |
| Firewall host/libvirt | Backend/chain/hook/handle sebelum perubahan | BELUM_DIISI |
| Windows build/arsitektur/Python/WireGuard/PowerShell | Dicatat masing-masing PC dan laptop | BELUM_DIISI |
| ID/IP tunnel PC dan laptop | .5/.6 usulan; registry diperiksa sebelum persetujuan | BELUM_DIISI |
| Root fingerprint, server WG public key | Dibandingkan dengan backend aktif | BELUM_DIISI |

Topologi aliran, bukan bukti koneksi yang telah berhasil:

```text
PC Windows LAN .50.20 ----- kabel -----+
                                      |
Laptop Windows Wi-Fi .50.30 -- SSID -- Router khusus .50.1/24
                                      |
                                   kabel LAN
                                      |
                          Host Linux Ethernet .50.10
                          route/forward/libvirt filter
                                      |
                          virbr-vg 192.168.100.1/24
                          + VM-CA     .100.10 HTTPS8080
                          + VM-SERVER .100.20 HTTPS8081 / UDP51820
                          + VM-ADMIN  .100.40 HTTPS5000
                          + 3 guest client/attacker lama dipertahankan

Sebelum tunnel: endpoint -> .100.20:8081 (admission HTTPS)
Setelah admission: endpoint -> .100.20:51820 (WireGuard UDP)
Di dalam tunnel: identitas yang punya grant -> 10.8.0.1:8082
CA/admin bukan tujuan yang dibuka langsung kepada endpoint fisik.
```

Tiga ruang alamat berbeda: .50/24 untuk LAN fisik, .100/24 untuk backend guest,
10.8/24 untuk tunnel. Default gateway endpoint tetap router.50.1; host.50.10 hanya
next hop rute khusus server. Tidak ada rencana WAN/port forwarding internet.
Jangan membuka admin/CA pada router karena client tidak perlu memanggilnya langsung.

### 12.1 Urutan rollback yang harus dipahami sebelum mulai

Tetapkan siapa yang boleh menghentikan pilot dan di mana console tersedia.
Rollback dimulai ketika kehilangan jalur administrasi, trust/key tidak cocok,
default-deny gagal, identitas lain terputus oleh logout scoped, atau cleanup
kepemilikan tidak pasti. Hentikan tahap berikutnya; simpan bukti tersaring.

1. Cabut sesi/grant pilot melalui server/admin yang sah; verifikasi peer/aplikasi
   endpoint terkait terputus, pertahankan scope endpoint lain.
2. Hentikan proses connect milik pilot. Konfirmasi teardown; jika gagal, tangani
   WIN-CLEANUP-02 dengan ownership terverifikasi sebelum menyentuh config.
3. Hapus hanya route /32 dan rule bertanda pilot yang baru dibuat, memakai interface,
   next-hop atau handle yang dicatat. Jangan flush tabel global/libvirt.
4. Bila upgrade admin gagal, pulihkan runtime/env/unit/profil kompatibel yang
   di-backup; pertahankan database/CA terkini dan histori pencabutan.
5. Periksa lagi akses console/management, readiness, nol akses disposable dan
   identitas utama tetap. Catat hasil rollback, bukan hanya perintah yang dijalankan.

Jika tidak bisa memastikan restore runtime kompatibel, biarkan layanan terkait
berhenti/fail-closed dan eskalasi ke operator. Jangan mengembalikan CA/database
lama untuk mengejar hasil hijau.

## 13. Pelaksanaan per tahap dengan syarat lanjut

| Tahap / penanggung jawab | Tindakan dan rujukan | Hasil yang harus terlihat | Berhenti jika |
|---|---|---|---|
| T0 Operator | Inventaris, hash kit, backup, console; Bab1–4 | Paket cocok manifest; backup checksum benar; keenam VM tercatat | Hash berbeda/backup tidak terbaca/console tidak tersedia |
| T1 Operator jaringan | Router, IP, route host/endpoint; Bab5 | .50/24 sesuai rencana, tidak overlap, backend .100/24 tetap | IP duplikat, Wi-Fi terisolasi, interface salah |
| T2 Operator backend | CA → server → admin, clock/CRL/readiness | Service terkait active dan readiness200 melalui jalur sah |503, CRL invalid/stale, trust tidak cocok |
| T3 Operator firewall | Review forwarding/NAT/return path dan kandidat VM | Hanya TCP8081/UDP51820 dari dua endpoint; management tetap | API/CA/admin terbuka salah scope, bypass LAN atau akses admin hilang |
| T4 Operator admin | Backup konsisten dan upgrade admin0.1.12; Bab6 | pip check PASS, service/readiness sehat, profil terbaca | Env hilang, dependency gagal, root/key berbeda |
| T5 Operator PC | Runtime, preflight, UAC/install, status; Bab3,7 | Runtime terpasang, tanpa peer/identitas otomatis | Signature/path/hash/UAC/state gagal |
| T6 Admin+karyawan PC | Init/request/binding/import/login; Bab8 | Binding cocok original key/request, login belum menambah peer | Key hilang/ID reused/akun salah/bundle tidak cocok |
| T7 Penguji PC | Connect/admission/grant/demo, deny tests; Bab9 | Lease/peer/handshake benar, hanya resource berizin yang lolos | Bypass admission/grant, LAN langsung lolos, cleanup tidak pasti |
| T8 Laptop | Ulang T5–T7 via Wi-Fi dengan identitas berbeda | Bukti laptop sendiri; SSID/adapter benar | Menggunakan key/ID PC, guest isolation, runtime tidak cocok |
| T9 Bersama | Renewal, logout/revoke satu sisi, tukar peran | Akses satu sisi terputus sesuai scope; sisi lain tetap | Sesi/perangkat lain ikut terputus atau TCP dicabut tetap berjalan |
| T10 Operator+admin | Cleanup, arsip audit, serah terima; Bab10,15–17 | Disposable dicabut, demo berhenti bila selesai, bukti tersimpan | Peer/grant/tunnel/config ownership belum jelas |

### 13.1 Perintah observasi yang tidak menampilkan private key

Di VM-SERVER, gunakan output terarah; **jangan** memakai `wg showconf` atau dump
konfigurasi/environment ke laporan karena dapat membawa rahasia.

```bash
# VM-SERVER: public key dan bukti tunnel, bukan private key.
sudo wg show wg0 peers
sudo wg show wg0 latest-handshakes
sudo wg show wg0 transfer
sudo wg show wg0 allowed-ips
systemctl is-active vanguard-server vanguard-daemon wg-quick@wg0
```

Public key tetap metadata identitas; batasi penyebaran laporan sesuai kebutuhan.
Handshake0 berarti belum pernah terlihat; waktu lama bukan bukti aktif sekarang.
Byte kumulatif harus dibandingkan sebelum/sesudah request demo, bukan dipakai
sendiri sebagai bukti akses aplikasi. Server/API/dashboard menyediakan lease dan
status registered terpisah; nilai unknown harus tetap dicatat unknown.

Jika perlu log untuk kegagalan, operator membacanya pada node privat dalam rentang
waktu kejadian. Jangan menyalin request lengkap, header Authorization, OTP, password,
token, key atau environment. Arsip administrator dilakukan melalui dashboard
agar field kejadian/alasan yang aman tetap konsisten dengan sistem.

### 13.2 Langkah native installer yang wajib dibuktikan

Lakukan pada identitas disposable, setelah baseline/backup. Rekam hash identitas
sebelum/sesudah secara privat, bukan isi key.

1. Fresh install di path terlindungi: exit0, runtime lengkap, belum ada peer/key
   yang dibuat installer. Configure/init adalah tahap terpisah.
2. UAC dibatalkan: exit1223, tidak melanjutkan instalasi. Salah hash manifest:
   proses gagal, existing identity tidak berubah.
3. Reinstall/repair: runtime baru lolos check sebelum pointer berganti; key/config
   tetap. Interupsi: status tidak boleh terlihat INSTALLED jika belum selesai.
4. Upgrade ketika tunnel aktif: ditolak sampai pemilik menyelesaikan cleanup.
   Jangan menutup paksa aplikasi lain atau menghapus config.
5. Path berspasi dan ACL: package/runtime terlindungi; reparse/junction ditolak;
   pengguna biasa tidak dapat membaca key atau menulis kode elevated.
6. Uninstall setelah service absent: binary milik aplikasi hilang, data/key/config
   serta Python/WireGuard shared tetap. Decommission server diuji terpisah.

Checklist ini belum merupakan bukti bahwa hasil di atas sudah tercapai. Linux
unit tests dan parse PowerShell tidak menggantikan eksekusi Windows native.

## 14. Troubleshooting berdasarkan gejala

| Gejala | Pemeriksaan pertama | Tindakan aman / kriteria selesai |
|---|---|---|
| Preflight host BLOCKED | Alamat Ethernet .50.10/24 dan status CA/server/admin | Selesaikan jaringan/startup sesuai window; exit2 tetap perlu review manual |
| PC dapat menghubungi API, laptop tidak | SSID/guest isolation/IP/route /32/adapter Wi-Fi | Betulkan SSID/rute yang disetujui; jangan membuka CA/admin |
| Timeout HTTPS sebelum tunnel | Route .100.20/32, host forwarding efektif, libvirt filter, firewall VM, listener | Telusuri jalur satu per satu; TCP8081 harus berhasil dengan TLS valid |
| TLS certificate verify failed | Waktu, URL/SAN, root fingerprint independen | Cocokkan ke layanan aktif; jangan verify=False atau mengganti trust dari ZIP semata |
| Readiness503 | Detail dependency unknown/not_ready, waktu/CRL/daemon/disk | Atasi dependency; liveness200 tidak cukup, jangan memperpanjang timeout tanpa bukti |
| Installer gagal sebelum UAC | Hash paket, sumber admin-only, ACL/reparse, execution policy organisasi | Tempatkan lewat operator pada path terlindungi; signing bila wajib, bukan bypass policy |
| Python tidak ditemukan/tidak cocok | Path absolut, 3.13,64bit,pip/venv, lokasi terlindungi | Pasang runtime resmi yang sesuai; jangan menimpa runtime aplikasi lain |
| WireGuard signature/thumbprint ditolak | Signature valid, publisher dan thumbprint signer yang dikonfirmasi admin | Periksa asal dan waktu/trust store; jangan menerima thumbprint tak dikenal |
| Config sudah ada | Ownership instalasi, file profil/root lama, setup-state | Bandingkan konfigurasi; jangan hapus config/key agar configure dapat berjalan |
| Init menolak direktori tidak kosong | Apakah identitas sudah pernah dibuat | Lanjutkan identitas yang sah; init bukan reset atau repair key |
| Import bundle ditolak | Original request/ID/IP/WGkey, root/profil, cert/key, validity | Minta bundle yang benar; tidak menyalin private key dari perangkat lain |
| Login gagal | Akun karyawan aktif dan binding perangkat yang benar | Admin memeriksa akun; username/password tidak diunggah ke laporan |
| Login berhasil tetapi connect ditolak | Enam cek perangkat, sesi, CRL, revocation, clock | Perbaiki sebab terkonfirmasi; kredensial valid bukan izin melewati admission |
| Peer ada tetapi handshake belum terlihat | Endpoint UDP51820, server public key, route/NAT/filter balasan | Buktikan lalu lintas UDP; ping/TCP/API saja belum cukup |
| Handshake ada tetapi HTTP demo gagal | Demo aktif/bind10.8.0.1, grant identity+akun, lease valid, gate aktif | Benahi grant/listener yang benar; jangan membuka LAN atau menambah peer statis |
| HTTP LAN langsung justru berhasil | Ingress interface, gate sebelum established, target/port pengujian | Hentikan pilot; enforcement gagal sampai bypass ditutup dan diuji ulang |
| Renewal terhenti/lease habis | Terminal connect, sesi8jam, clock/CA/daemon/koneksi | Fresh login bila sesi expired; lease renewal tidak memperpanjang sertifikat |
| Disconnect timeout / service hang | Pemilik proses/service, marker, config, status server | Cabut akses server; pastikan teardown sebelum mengarsipkan config; WIN-CLEANUP-02 |
| Logout server tidak terjangkau | Jalur API/layanan | Pencabutan belum terkonfirmasi; retry/admin revoke, bukan tampilkan sukses |
| Setelah reboot tidak terhubung | Route ActiveStore hilang, terminal renewal tidak hidup | Periksa route/preflight lalu login/admission baru; jangan autostart peer statis |
| Kit integrity gagal setelah mengisi checklist | File acceptance diedit di dalam kit atau ada file tambahan | Gunakan salinan checklist di luar kit; kembalikan kit dari ZIP terverifikasi |

Jangan mengubah banyak lapisan sekaligus. Catat gejala, waktu, dugaan, satu perubahan,
hasil pengukuran ulang dan keputusan lanjut/rollback. Jika belum diuji, gunakan
BELUM_DIJALANKAN; jika pemeriksaan tidak bisa dilakukan, gunakan UNKNOWN beserta
alasan. Catat kegagalan sekalipun percobaan berikutnya berhasil.

## 15. Bukti penerimaan dan laporan pengujian

Salin ACCEPTANCE.csv dari kit ke folder bukti privat. Matriks template mencakup PC,
laptop dan bersama; skenario yang tidak berlaku (misalnya putus Wi-Fi pada PC LAN)
ditandai TIDAK_BERLAKU dengan alasan, bukan PASS. Setiap hasil memerlukan bukti
waktu dan versi yang sama dengan eksekusi. Jangan menjumlahkan suite overlap atau
menyalin hasil VM lama menjadi hasil perangkat fisik.

Contoh catatan satu kasus (template, **bukan hasil uji**):

```text
ID kasus       : PC-ADMISSION-01
Perangkat      : PC-LAN
Waktu UTC/WIB  : BELUM_DIISI
Versi/hash kit : BELUM_DIISI
Prasyarat      : root/key cocok, akun aktif/binding sah, tanpa peer statis
Tindakan       : login, buktikan belum ada peer; connect, lakukan request demo
Hasil harapan  : admission wajib; peer/lease sesuai; HTTP hanya dengan grant
Hasil aktual   : BELUM_DIJALANKAN
Bukti aman     : lokasi laporan tersaring; jangan lampirkan token/private key
Cleanup        : BELUM_DIJALANKAN
Keputusan      : BELUM_DINILAI
```

Untuk revoke TCP aktif, koneksi harus benar-benar terbuka sebelum revocation;
catat waktu revocation, penghentian transfer, status peer/grant dan kondisi endpoint
lain. Satu request HTTP baru setelah revoke tidak membuktikan sesi TCP lama terputus.
Untuk renewal, rekam beberapa pembaruan lease beserta sertifikat yang tidak berubah.
Untuk pengujian expired, gunakan identitas/sesi disposable dan skenario terkontrol;
jangan mengubah jam CA utama untuk memaksa hasil.

Hasil minimal yang diserahkan:

- Inventaris versi, topologi aktual, root/public key yang diverifikasi, tanpa key privat.
- Hash kit dan baseline backup yang tersimpan privat, catatan perubahan per tahap.
- Hasil PC, laptop dan bersama, termasuk denial/bypass/renewal/cleanup/isolasi logout.
- Arsip aktivitas admin beserta filter waktu dan checksum; simpan bukti kegagalan.
- Daftar disposable yang dicabut, grant/service/route pilot yang dibersihkan.
- Keterbatasan yang belum diuji, pemilik tindak lanjut dan keputusan pilot diterima/ditunda.

Arsip dashboard adalah snapshot yang dapat diverifikasi, bukan ledger yang tahan
perubahan oleh root VM. Jika perlu retensi/off-site, salin arsip ke penyimpanan
terkontrol sesuai kebijakan, tanpa menghapus bukti lama otomatis.

## 16. Operasi harian, shutdown dan pemeliharaan

### 16.1 Sebelum dipakai

Operator memastikan host mendapat daya dan tidak sleep, tiga backend tersedia,
waktu sinkron, disk/log cukup, readiness dependency sehat serta CRL aktual.
Admin meninjau sertifikat mendekati expiry dan akun/perangkat nonaktif. Karyawan
memeriksa profil yang disetujui, login dan connect melalui launcher. Tidak perlu
init, enrollment ulang atau generate CA setiap hari.

Jika certificate hampir kedaluwarsa, rencanakan penggantian immutable: siapkan key/
request baru pada client, ikuti alur replace admin setelah pencabutan lama sesuai
prosedur, preserve histori/binding. Lease renewal tidak memperpanjang sertifikat.
Jangan menimpa direktori identitas lama sebelum tunnel down terkonfirmasi.

### 16.2 Selama layanan dipakai

Bedakan domain running, service active, liveness, readiness, lease, peer, handshake
serta transfer. Masing-masing menjawab pertanyaan berbeda. Pantau halaman
penyimpanan operasional, pertumbuhan database/audit dan ruang disk; jangan menghapus
log/database untuk membuat grafik terlihat baik. Rekam alasan gagal yang aman.

Untuk perubahan profil/port/trust atau upgrade runtime, buat window, backup dan
uji kompatibilitas baru. Signing/hash paket harus diperbarui ketika isi berubah;
jangan mengedit ZIP terverifikasi lalu memakai checksum sebelumnya. Hindari
mengubah interface/IP aktif di tengah sesi tanpa rencana kehilangan koneksi.

### 16.3 Mengakhiri hari atau pilot

1. Karyawan menutup akses aplikasi, disconnect lalu logout ketika server masih
   terjangkau. Admin memastikan lease/peer/grant terkait sudah dibersihkan.
2. Selesaikan akun/identitas disposable dan hentikan demo sementara jika pilot
   selesai. Jangan mencabut identitas utama hanya untuk mematikan mesin.
3. Simpan arsip audit dan laporan hasil. Backup terbaru mengikuti konsistensi
   aplikasi dan lokasi privat; tidak menggantikan histori backup sebelumnya.
4. Operator menghentikan backend secara normal setelah memastikan tidak ada user
   aktif. Shutdown admin, server, lalu CA; konfirmasi keadaan guest sebelum host
   dimatikan. Hindari forced power-off sebagai rutinitas.
5. Pada pemakaian berikutnya, urutan startup CA → server → admin dan verifikasi
   readiness diulang. Reboot bukan bukti revocation; fresh admission tetap wajib.

## 17. Serah terima, CA dan batas penerapan

### 17.1 Formulir serah terima

| Item serah terima | Isi/keputusan |
|---|---|
| Tanggal, operator, admin penerima | BELUM_DIISI; identitas personal rinci disimpan privat |
| Versi/hash kit dan aplikasi terpasang per node | BELUM_DIISI; jangan menganggap versi kandidat sudah terpasang |
| Diagram jaringan dan rule/route aktual | BELUM_DIISI; rencana tidak sama dengan hasil diterapkan |
| Hasil PC LAN/laptop Wi-Fi/bersama | BELUM_DIJALANKAN |
| Bukti default-deny dan scoped logout/revoke | BELUM_DIJALANKAN |
| Backup, checksum, lokasi dan akses pemulihan | BELUM_DIISI; lokasi privat, bukan password |
| Sertifikat expiry, prosedur replace dan CRL | BELUM_DIISI |
| Penanggung jawab operasi/audit/insiden | BELUM_DIISI |
| Daftar masalah terbuka dan rencana penyelesaian | WIN-CLEANUP-02/native/fisik/soak/power-loss sesuai bukti aktual |
| Keputusan penerimaan | DITUNDA sampai kriteria target terpenuhi; jangan tanda tangan hasil fiktif |

### 17.2 Penjelasan CA untuk penerapan ini

CA mengesahkan sertifikat perangkat/HTTPS; WireGuard memakai keypair terpisah.
Private key X.509 dan WireGuard perangkat dibuat di perangkat. Admin mendaftarkan
request/binding dan mengirim sertifikat publik, bukan membuat key milik karyawan.
Sertifikat saja belum memberi peer: sesi karyawan dan enam pemeriksaan admission
termasuk CRL/revocation/proof/binding tetap wajib.

Pada backend yang sudah ada **gunakan CA yang sudah ada**. Jangan menjalankan init
untuk mengganti CA, memperbaiki CRL secara manual, menebak counter atau mengembalikan
index lama. Domain/IP tambahan pada HTTPS memerlukan SAN dan allowlist operator;
rencana saat ini tetap mengakses.100.20 sehingga tidak memerlukan CA baru.

Untuk lingkungan yang benar-benar kosong, prosedur lengkap generate CA, key/CSR
HTTPS, signing, trust, CRL dan pemeriksaan sudah tersedia pada
[modul utama Bab5.3](MODUL_PENGGUNAAN_VANGUARD.html#bagian-5-3).
Baca prasyarat lingkungan kosong dahulu. Untuk sistem ini jalur yang digunakan
adalah verifikasi/pemeliharaan CA yang ada, bukan menyalin tahap init lab baru.

### 17.3 Batas klaim dan dokumen acuan

Paket ini mendukung persiapan pilot LAN/Wi-Fi terkontrol. Ia belum membuktikan
kapasitas produksi, HA, akses internet publik, pengelolaan fleet besar atau semua
jenis aplikasi/protokol. Resource gate yang dicontohkan khusus internal-demo
TCP8082; menambah route/resource pada profil saja tidak membuat kebijakan baru.
Prasyarat runtime, signing organisasi, native Windows dan topologi aktual wajib
ditutup melalui pengujian target.

Gunakan [checkpoint](CHECKPOINT.md) untuk status terbaru,
[panduan teknis pilot](ENDPOINT_WINDOWS_PILOT.md) untuk matriks routing/firewall,
[API](API.md) untuk kontrak layanan, [keamanan](SECURITY.md) untuk trust/lifecycle,
dan [Windows client](WINDOWS_CLIENT.md) untuk histori serta batas bukti guest.
Jika revisi kit dan checkout berbeda, cocokkan hash serta tanggal; dokumen dalam
ZIP adalah snapshot saat build, bukan status VM real-time.
