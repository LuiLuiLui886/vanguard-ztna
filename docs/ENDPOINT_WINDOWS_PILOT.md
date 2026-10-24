# Pilot endpoint Windows fisik — kandidat 0.1.12

**Pembaruan installer24 Oktober:** paket Windows baru menyertakan Python/WireGuard
dan dependensi dalam satu ZIP. Ikuti [panduan Windows terbaru](../deploy/endpoint/windows/SETUP_WINDOWS.md).
Bagian prasyarat manual/kandidat22Oktober di bawah tetap menjadi riwayat paket lama;
lihat checkpoint untuk hasil native aktual. Arsitektur, jaringan, CA dan admission
tidak berubah.

Status 22 Oktober 2026: **persiapan lokal; belum release/rollout**. Ikuti
[master prompt](../CODEX_VANGUARD_MASTER_PROMPT.md), fokus ENDPOINT_WINDOWS.
Source dasar `040dc21` dari perbaikan terbaru dipertahankan pada branch
`feature/2026-10-22-physical-endpoints`. Master prompt diambil dari main
`235df05`; main masih source 0.1.8 dan tidak digabung menimpa source 0.1.11.
Versi 0.1.12 di dokumen ini adalah kandidat lokal, bukan versi pada VM.

## Audit dan urutan pekerjaan

Inventaris GitHub akun lokal menemukan lima repo, tujuh branch: VanGuard
(main/fix/hardening), MRT, Pemograman-Web-Kelola-barang-beserta-Login-dan-regis,
Porto-Web, Testing. Seluruh tree terjangkau tanpa truncation. Hanya VanGuard
mempunyai master prompt/instruksi agent; dokumen proposal/README produk pada
repo lain tidak diperlakukan sebagai perintah menjalankan proyek. Bukti privat
`state/endpoint-20261022/repository-scan.json`. Tidak ada repo lain yang diubah.

| Temuan dan prioritas | Lokasi/bukti sebelum perubahan | Dampak dan kriteria selesai | Status |
|---|---|---|---|
| FITUR_BELUM_ADA/P1, profil endpoint | `client._connect` memakai endpoint lab meskipun API diberikan custom | Satu profil mengendalikan API, transport WG, root/key, route/resource; tolak konflik sebelum admission | Implementasi dan regresi lokal lulus; target fisik BELUM_DIJALANKAN |
| FITUR_BELUM_ADA/P1, import onboarding | `Dashboard.bundle` hanya profil lab; belum ada CLI import tervalidasi | Bundle cocok request/key lokal dan root independen; tidak overwrite key/trust atau menambah peer | Tes CA sementara/import tamper lulus |
| RISIKO_DESAIN/P1, jalur LAN ke libvirt NAT | Ethernet host NO-CARRIER; jaringan sekarang .66/24, VM .100/24; firewall source lab | Route endpoint saja tidak cukup: host forward/libvirt filter/return path dan firewall VM harus cocok | Rencana dan kandidat rule siap; penerapan BLOCKED tahap terpisah |
| FITUR_BELUM_ADA/P1, installer fisik | `deploy/windows/bootstrap.ps1` adalah provisioning VM/NIC/SSH | Installer offline terpisah, tanpa jaringan/key, runtime terisolasi dan preservasi identitas | Source/paket siap; IMPLEMENTASI_BELUM_UJI_TARGET |
| RISIKO_DESAIN/P1, konflik identitas/jaringan | Default init lab .2 berisiko dipakai endpoint baru; route VPN lain belum diperiksa launcher | Profil init wajib ID/IP eksplisit; snapshot Windows diperiksa sebelum admission | Regresi validator lokal; snapshot OS native BELUM_DIJALANKAN |
| BELUM_TERUJI/P1, UAC/ACL/service/repair | Tidak ada PowerShell native pada host, VM tidak dijalankan pada tahap ini | Native fresh/reinstall/repair/upgrade/uninstall, path khusus, gagal hash/UAC dan preservasi key | BLOCKED lingkungan/otorisasi target; jangan sebut paket siap distribusi |
| RISIKO_DESAIN/P1, ownership/ACL installer | `Common.Assert-SafePath` semula menerima semua SID service; installer memeriksa marker hanya berdasarkan keberadaan | Batasi ke TrustedInstaller hasil resolusi OS, cocokkan isi marker, tolak setup-state terputus | Source r3 diperketat; guard source PASS, ACL native BELUM_DIJALANKAN |
| BUG_TERBUKTI/P2, duplikasi anggota arsip selama perubahan | Allowlist JSON ditambah sementara dua JSON sudah eksplisit di `package_source.main` | Arsip akhir tanpa path duplikat dan tanpa private state | Diperbaiki dengan deduplikasi; periksa arsip akhir |

Audit Bagian A: source dasar sudah memuat manifest/roll-forward CA, logout scoped,
expiry/disabled/revocation, readiness terbatas, resource gate dan audit. Regresi
lokal tetap dijalankan. Bukti VM 20–21 Oktober tetap historis; keenam VM **shut off**
saat audit 22 Oktober. Tidak mengulangi CA enrollment, rollout atau mengklaim
readiness saat ini. WIN-CLEANUP-02, power-loss media CA dan soak panjang masih
BELUM_TERUJI. Lihat [checkpoint](CHECKPOINT.md) dan [kapasitas CA](CA_SERVICE_CAPACITY.md).

## Topologi rencana dan fakta host

| Perangkat | Rencana | Fakta saat audit |
|---|---|---|
| Router khusus | 192.168.50.1/24, LAN+SSID uji sama subnet | Model, akses admin, DHCP reservation, AP isolation belum diperiksa |
| Host Linux | Ethernet 192.168.50.10/24 | enp2s0 NO-CARRIER tanpa IPv4; Wi-Fi wlp0s20f3 192.168.66.9/24, gateway .66.1 |
| PC Windows 11 LAN | 192.168.50.20/24, gateway .50.1 | OS build/arsitektur/admin/runtime belum diverifikasi |
| Laptop Windows 11 Wi-Fi | 192.168.50.30/24, gateway .50.1 | SSID/OS build/arsitektur/admin/runtime belum diverifikasi |
| Backend enam VM | .100.10/.20/.30/.40/.50/.60 | NAT libvirt vanguard, bridge virbr-vg .100.1/24; semua mati |
| Tunnel | 10.8.0.1 server, .2 Ubuntu, .4 VM Windows | .3 dicadangkan eksperimen; .5/.6 hanya usulan PC/laptop |

Host `ip_forward=1` teramati; ruleset firewall berprivilege belum terbaca
(`sudo -n` membutuhkan autentikasi). Ini tidak membuktikan forwarding diizinkan.
Jangan mengubah bridge/NAT backend, default route atau Wi-Fi host pada persiapan.
Alokasi ID/IP wajib diperiksa di registry, termasuk revoked/history, sebelum init;
IP yang tidak merespons ping belum tentu kosong. Profil tetap mendukung tunnel
10.8.0.0/24 sesuai registry server saat ini, bukan migrasi subnet otomatis.

## Konfigurasi publik dan firewall yang dapat ditinjau

Generator berikut hanya menulis direktori keluaran baru. Gunakan salinan root
publik dan public key server yang diperoleh lewat kanal operator tepercaya.
Salinan lokal saat ini belum dibandingkan ulang dengan VM aktif.

```bash
.venv/bin/python scripts/prepare_endpoint_pilot.py \
  --root state/deployment/root.crt \
  --server-public-key-file state/deployment/server-wg.pub \
  --output state/endpoint-20261022/public-pilot
```

Keluaran lokal sudah tersedia: `profile.json`, `root.crt`, `admin-public.env`,
`network-plan.json`. Generator menolak output yang sudah ada. Profil memisahkan
API HTTPS `192.168.100.20:8081`, WG UDP `192.168.100.20:51820`, fingerprint root,
public key server, backend/tunnel network, allowed host route `10.8.0.1/32`,
resource `internal-demo` TCP8082. Tidak ada token/password/private key.
`resources` menjelaskan tujuan; **tidak memberikan grant**.

Pada tahap rollout kelak, `VANGUARD_CLIENT_PROFILE=/etc/vanguard/endpoint-profile.json`
adalah environment **VM-ADMIN** untuk bundle dashboard, bukan environment
VM-SERVER. Salin profil publik yang sama ke admin dan endpoint melalui kanal
tepercaya. Pertahankan seluruh environment rahasia yang sudah ada. Restart
terencana hanya setelah backup/validasi; belum dilakukan dalam tugas ini.
Bundle tanpa profile lama tetap kompatibel alur lab manual; importer baru
memerlukan profil tepercaya yang sama dan tidak mengambil trust dari ZIP.

Kandidat firewall server sudah dibuat lokal dengan perintah generate-only:

```bash
.venv/bin/python deploy/firewall.py server --management-ip 192.168.100.1 \
  --windows-client --application-policy \
  --physical-client 192.168.50.20 --physical-client 192.168.50.30 --print-only \
  > state/endpoint-20261022/server-firewall.candidate.nft
```

Nilai management harus diverifikasi terhadap akses operasional sebelum penerapan.
Flag physical menolak mode apply. Rule mempertahankan klien lama dan gate aplikasi,
hanya menambah sumber dua endpoint untuk TCP8081/UDP51820. Jangan menambahkan
peer statis, membuka CA8080/admin5000 atau menghapus tabel firewall global.
ICMP tunnel untuk .5/.6 belum diizinkan; ping bukan kriteria pilot.

### Rencana routing dan host filtering

Urutan setelah otorisasi penerapan: sambungkan host LAN ke router khusus,
konfirmasi IP/mask/reservasi/DHCP dan jangan mengganggu Wi-Fi administrasi;
periksa konflik .50/.100/10.8; verifikasi interface yang sebenarnya. Tambahkan
route endpoint **192.168.100.20/32 via 192.168.50.10**, bukan seluruh subnet VM.
Router tidak membutuhkan static route jika memakai route /32 pada dua endpoint.
Jika router/AP mengisolasi Wi-Fi dari LAN, pilot laptop terblokir sampai kebijakan
SSID uji disetujui; jangan memperlonggar jaringan utama.

Contoh **belum dijalankan**, PowerShell Administrator pada endpoint yang benar;
`$ifIndex` harus diisi dari hasil Get-NetIPConfiguration, bukan contoh angka:

```powershell
Get-NetIPConfiguration
Get-NetRoute -AddressFamily IPv4
# Isi $ifIndex hanya setelah interface LAN/Wi-Fi endpoint dikonfirmasi.
New-NetRoute -DestinationPrefix '192.168.100.20/32' -InterfaceIndex $ifIndex `
  -NextHop '192.168.50.10' -PolicyStore ActiveStore
```

Sebelum menambahkan, pastikan route identik belum ada dan simpan snapshot. Route
ActiveStore bersifat sementara; jangan membuat default route baru. Return path
VM-SERVER memakai gateway .100.1, kemudian host langsung ke .50/24. Jika host
melakukan SNAT tak terencana, source .50.20/.30 hilang dan rule server menolak;
perbaiki rencana routing, bukan membuka source apa pun.

Matriks rule host yang harus ditempatkan **pada chain forwarding efektif** setelah
backend nft/iptables libvirt teridentifikasi:

| Arah | Sumber → tujuan | Kriteria |
|---|---|---|
| enp2s0 → virbr-vg | {.50.20,.50.30} → .100.20 | TCP dport8081, UDP dport51820; new/established |
| virbr-vg → enp2s0 | .100.20 → {.50.20,.50.30} | Hanya established/related balasan koneksi yang diizinkan |
| LAN → subnet backend/tunnel lain | Selain dua transport di atas | Deny; jangan memberi jalur LAN ke TCP8082/CA/admin |

Template ekspresi nft untuk **review**, bukan perintah siap apply:
`iifname "enp2s0" oifname "virbr-vg" ip saddr { 192.168.50.20, 192.168.50.30 } ip daddr 192.168.100.20 tcp dport 8081 ct state new,established counter accept`;
ganti protokol/port untuk UDP51820. Rule balasan juga harus membatasi interface,
alamat dan conntrack. Tambahkan komentar ownership pilot dan rekam handle/rule ID.
Accept pada base chain terpisah tidak otomatis mengalahkan drop libvirt pada
chain lain; karena backend/chain belum terverifikasi, tidak dibuat script apply
host yang menebak urutan hook. Periksa nft/iptables, chain libvirt, NAT dan packet
counter sebelum koneksi uji. Ini blocker konkret penerapan, bukan proof jaringan.

### TLS

Dengan route di atas, URL tetap .100.20; SAN layanan yang ada tidak perlu diubah.
Jika operator memilih DNS/IP tambahan, helper `vanguard.ca.Authority.sign_tls` dan CLI
`sign-tls --ip HOST --approved-host HOST` menerima hanya allowlist eksplisit,
memilih SAN DNS/IP dan menolak newline/injeksi konfigurasi OpenSSL. Domain/IP
harus dialokasikan serta resolusi diverifikasi terlebih dahulu. Tes hanya pada
CA sementara, termasuk `openssl verify -verify_hostname` cocok dan salah.
Tidak membuat ulang CA, mengganti root atau menerbitkan sertifikat aktif.

## Paket offline dan jalur manual

Kandidat lokal: `dist/endpoint-windows-0.1.12-candidate-r3/`, tersedia juga ZIP
`dist/endpoint-windows-0.1.12-candidate-r3.zip` (SHA256 pada file `.zip.sha256`).
Kandidat pertama dipertahankan sebagai bukti; gunakan revisi r3. Ada 20 wheel dipin, 27 file
tercakup manifest (ditambah manifest itu sendiri), sekitar12,1MB. Target build
**CPython3.13 win_amd64**; bukan bukti perangkat sebenarnya x64. SHA256 manifest:

```text
47b50e47e156e1b41ff11ffba01e0e76433eb5f96cfde81b4b6df8361f530cb1
```

Build lokal memakai wheelhouse Windows yang sudah tersedia ditambah wheel source
baru; memeriksa tag, metadata, dependensi transitif Windows, hash dan anggota.
Tidak mengunduh runtime. Wheel aplikasi final SHA256:
`e116ec9a0c9f1b48bf059ffbba6f731032aa10dcfe79448c303fafed6234d066`.
Hash integritas bukan autentikasi publisher; sampaikan fingerprint melalui kanal
admin terpisah. Verifikasi asal/signature runtime dan signing sesuai kebijakan
organisasi. Kandidat **unsigned**; jangan bypass execution policy/SmartScreen.

Rebuild memakai folder baru; wheel source harus dibangun dari checkout final:

```bash
.venv/bin/python -m pip wheel --no-deps --no-build-isolation \
  --wheel-dir state/endpoint-20261022/wheel-final .
.venv/bin/python scripts/build_endpoint_package.py \
  --wheelhouse state/endpoint-20261022/wheelhouse-final \
  --output dist/endpoint-windows-0.1.12-candidate-r3
```

Output yang sudah ada sengaja ditolak. Wheelhouse Windows memerlukan dependensi
pinned `deploy/constraints.txt` tanpa gunicorn, plus pywin32==312/colorama==0.4.6
serta aplikasi0.1.12. Tidak menggunakan wheel Linux untuk runtime Windows.

### Langkah operator dan pengguna, setelah uji native diotorisasi

1. Periksa Windows11 build≥22000, x64, PowerShell5.1, hak admin dan waktu benar.
   Ambil ZIP lengkap24Oktober melalui downloads dan verifikasi hash sebelum BAT.
   Ekstrak ke path admin-only tanpa reparse point. Python/WireGuard sudah dibundel;
   runtime sesuai yang sudah ada dipakai kembali. Tidak perlu Git/WSL.
2. Jalankan Install-VanGuard.bat. Runtime belum ada dipasang setelah hash/signature
   publisher valid, lalu venv offline/pip hash-required/pip check/CLI check.
   Tidak mengubah PATH global/NIC/firewall/SSH atau membuat identitas/peer.
   Exit0 berhasil;1/2 gagal;1223 UAC batal;3010 restart manual kemudian retry.
   Policy eksplisit/GPO tetap dihormati; tidak meminta path/thumbprint manual.
3. Buka PowerShell Administrator. Launcher:
   `& "$env:ProgramFiles\VanGuardEndpoint\VanGuard.bat" configure`.
   Pilih profil/root publik; cocokkan fingerprint root dan public key server
   dari kanal admin terpisah. Config lama tidak ditimpa. Binary di
   `%ProgramFiles%\VanGuardEndpoint`; identity/config/log terpisah di
   `%ProgramFiles%\VanGuardEndpointData`, akses SYSTEM/Administrators.
4. Jalankan `status`, lalu `init`. Masukkan ID dan IP tunnel
   yang sudah dialokasikan admin (usulan .5/.6 belum merupakan izin alokasi).
   Private key X.509 dan WG dibuat pada endpoint, tidak pernah dikirim ke admin.
   Kirim hanya `identity\request.json` lewat kanal operator terautentikasi.
5. Admin mendaftarkan request, mengikat akun karyawan sesuai kewenangan dan
   mengunduh bundle dashboard berprofil. Registrasi dan login tidak menambah peer.
   Admin mengirim ZIP publik; `import-bundle` memeriksa root independen,
   profil, device ID, WG key, IP, fingerprint, tanda tangan, validity, CN/clientAuth
   dan private key lokal. Bundle berbeda ditolak; identik boleh diulang.
   Import offline belum memeriksa CRL aktual; server admission tetap wajib.
6. Jalankan `diagnose`: TLS/readyz harus berhasil sebelum tunnel.
   Status UDP/aplikasi tetap unknown; tidak dianggap siap hanya karena TCP terbuka.
   Login dengan `login`, password diketik tersembunyi. Token hanya file
   privat. Login bukan admission; akun valid saja belum memberikan akses.
7. `connect` menjalankan preflight konflik jaringan lalu enam pemeriksaan
   perangkat dan sesi server, memasang tunnel hanya setelah admission, serta
   mempertahankan renewal di terminal foreground. Jangan menutup terminal selama
   penggunaan. Jika renewal gagal, cleanup wajib; kegagalan teardown mempertahankan
   config/ownership agar tidak menimpa service VPN lain.
8. Admin memeriksa lease, peer, waktu handshake dan byte transfer masing-masing.
   Tambahkan grant disposable untuk identitas/akun yang benar pada kebijakan server:
   resource `internal-demo`, address `10.8.0.1`, protocol `tcp`, port8082. File
   kebijakan berformat `{"grants":[{"device_id":"ID_UJI","username":"AKUN_UJI",
   "resource":"internal-demo","address":"10.8.0.1","protocol":"tcp","port":8082}]}`.
   Nilai ID/akun contoh adalah placeholder; jangan membuat akun otomatis atau
   membuka seluruh LAN. Demo HTTP sementara harus dijalankan terencana pada server;
   tidak ada aplikasi bisnis permanen yang dinyalakan oleh paket.
9. Uji akses HTTP `http://10.8.0.1:8082/` dengan grant dan penolakan tanpa grant.
   Route bukan grant; port/resource lain tetap deny. Uji akses langsung .100.20:8082
   dari LAN harus gagal, termasuk percobaan routed ke IP tunnel dari NIC non-WG.
10. Ctrl+C pemilik atau `disconnect` di terminal admin lain meminta stop
    proses connect dengan nonce ownership. Hasil sukses hanya setelah tunnel down
    dan marker dibersihkan. Disconnect tidak mencabut sesi server. `logout`
    mencabut token/challenge/lease terkait; jika server tak terjangkau, pencabutan
    belum terkonfirmasi. Jangan mematikan seluruh proses Python/WireGuard.

Untuk menjalankan CLI manual tanpa launcher setelah runtime terpasang, ambil path
venv dari `current.json` di AppRoot (release yang aktif), lalu gunakan
`python.exe -m vanguard.client --directory IDENTITY --profile PROFILE --trust ROOT`
diikuti perintah yang sama: init dengan `--device-id/--tunnel-ip`, import-bundle ZIP,
login `--username`, connect, status, diagnose, disconnect, logout. Jangan memakai
default identitas VM atau meletakkan password pada argumen. Jalur Python/profile
sudah diuji lokal Linux; eksekusi manual Windows end-to-end **BELUM_DIJALANKAN**.

### Repair, upgrade, uninstall dan pemulihan

Installer/launcher memakai mutex bersama; install ditolak ketika connect/service
masih aktif. Reinstall/repair membuat runtime staging baru, memeriksa pip/CLI,
baru mengganti current.json; key/config tidak dibuat ulang. State instalasi publik
ada pada DataRoot/setup-state.json; jangan transcript password/token. Runtime
lama/parsial disimpan sebagai bukti. Jika marker/config parsial tidak konsisten,
inspeksi operator; pemulihan otomatis belum disediakan.

Uninstall-VanGuard.ps1 hanya menghapus AppRoot miliknya setelah mutex bebas,
marker cocok, tidak ada reparse point dan service dipastikan tidak ada (1060).
Identity/config/log serta Python/WireGuard bersama dipertahankan. Untuk decommission,
admin mencabut identitas/sesi/grant dahulu dan mengonfirmasi akses terputus;
penghapusan file lokal bukan revocation.

WIN-CLEANUP-02 masih berlaku: interupsi segera setelah pemasangan tunnel pernah
membuat service hang. Cabut akses server dan pastikan peer/grant terhapus, periksa
PID/service/config serta ownership, konfirmasi tunnel down sebelum mengarsipkan
config. Jangan menggunakan taskkill massal, menghapus config lebih dahulu atau
mengganti key agar percobaan berikutnya lolos.

Backup rollout kelak: simpan konfigurasi jaringan/router, route kedua endpoint,
ruleset host/libvirt+VM beserta handle, environment/unit dan wheel sebelumnya,
backup konsisten database aplikasi serta manifest/hash identitas di direktori
privat. Catat akses SSH/console pemulihan yang teruji. Terapkan PC dahulu setelah
validasi nft syntax pada target; baru laptop. Tidak mengganti state CA.

Rollback: hentikan admission pilot/cabut sesi/grant, konfirmasi tunnel down;
hapus hanya route /32 yang baru dibuat pilot dengan interface/next-hop sama;
hapus hanya rule host dengan handle/comment pilot; pulihkan konfigurasi firewall
VM dari backup terverifikasi setelah sesi pilot dihentikan. Jangan memulihkan
set grant/peer stale, database lama, index/serial/crlnumber/CRL lama. Runtime dapat
kembali ke release sebelumnya hanya jika kompatibilitas profil/schema sudah
teruji; versi0.1.11 belum mendukung import profil baru. Pisahkan rollback paket
dari rollback state keamanan. Jangan flush ruleset/libvirt atau menghapus identitas.

## Checklist dan batas bukti

Untuk setiap pengujian target rekam waktu UTC/WIB, versi+manifest hash, profil
publik, ID perangkat, lease sampai kapan, peer/handshake/byte, resource/kebijakan,
hasil dan lokasi bukti yang sudah disaring. Jangan merekam key/token/OTP/password.

| Skenario target | PC LAN | Laptop Wi-Fi | Bersamaan |
|---|---|---|---|
| Build/arsitektur/admin/runtime, LAN/SSID/IP/route, TLS readiness | BELUM_DIJALANKAN | BELUM_DIJALANKAN | BELUM_DIJALANKAN |
| Fresh install, offline/hash salah/UAC batal/path khusus/ACL/reparse | BELUM_DIJALANKAN | BELUM_DIJALANKAN | BELUM_DIJALANKAN |
| Generate endpoint key/CSR, import, binding, login tanpa peer | BELUM_DIJALANKAN | BELUM_DIJALANKAN | BELUM_DIJALANKAN |
| Admission, handshake, HTTP dengan grant; deny tanpa grant/LAN bypass | BELUM_DIJALANKAN | BELUM_DIJALANKAN | BELUM_DIJALANKAN |
| Renewal berulang, expiry/disabled/revoked, TCP aktif diputus | BELUM_DIJALANKAN | BELUM_DIJALANKAN | BELUM_DIJALANKAN |
| Logout/revoke satu endpoint tidak memutus endpoint lain; tukar peran | BELUM_DIJALANKAN | BELUM_DIJALANKAN | BELUM_DIJALANKAN |
| Disconnect/cleanup gagal, WIN-CLEANUP-02, reboot | BELUM_DIJALANKAN | BELUM_DIJALANKAN | BELUM_DIJALANKAN |
| Wi-Fi putus/sambung, konfirmasi SSID/lease baru | Tidak berlaku | BELUM_DIJALANKAN | BELUM_DIJALANKAN |
| Reinstall/repair/upgrade/uninstall menjaga key/config | BELUM_DIJALANKAN | BELUM_DIJALANKAN | BELUM_DIJALANKAN |
| Cabut disposable/grant, demo berhenti, rollback route/rule pilot | BELUM_DIJALANKAN | BELUM_DIJALANKAN | BELUM_DIJALANKAN |

Prasyarat otomatis, shortcut GUI, signing organisasi, ARM64, repair state parsial
otomatis BELUM_TERSEDIA. Installer kandidat menyediakan launcher CLI, runtime
terisolasi dan lifecycle source, bukan klaim Windows-native berhasil. Pemeriksaan
syntax PS ditambahkan pada workflow Windows untuk run mendatang; belum dijalankan
karena host tidak memiliki PowerShell dan tugas ini melarang push/VM changes.
Status lokal `status` hanya filepresence, bukan lease valid/peer/handshake aktif.
`diagnose` readiness tidak membuktikan jalur UDP maupun akses aplikasi.

Hasil aktual tes/build dicatat di [jurnal22 Oktober](PROGRESS_2026-10-22.md) dan
[checkpoint](CHECKPOINT.md). Keterbatasan di atas harus ditutup sebelum menyebut
pilot siap; histori pengujian Windows VM lama tidak membuktikan endpoint fisik.

### Hasil lokal final22 Oktober

- Baseline relevan81PASS/1SKIP153,71detik; terarah109PASS/1SKIP212,34detik.
- Full regression r2: **260PASS/1SKIP501,29detik**, Python3.12.3/Linux. Run pertama
  terputus tanpa JUnit dan tidak dihitung sukses. Skip hanya ACL Windows native.
- Guard packaging r3:4PASS0,35detik. Jangan menjumlahkan suite yang overlap.
- CA/OpenSSL/TLS sementara nyata; WireGuard pada regresi menggunakan backend
  test/mock. Tidak ada bukti handshake/native Windows/endpoint fisik baru.
- Ruff, pip check, bash syntax, modul/tautan, credential scan PASS. Wheel final
  25anggota aplikasi cocok source;20wheel Windows dipin/hash, dependency closure,
  rebuild manifest identik dan pip offline cross-platform dry-run PASS.
- PowerShell/native installer/signing/rollout/CI baru BELUM_DIJALANKAN. Tugas ini
  tidak mem-push GitHub. Paket/prasyarat tidak boleh dianggap release tervalidasi.
