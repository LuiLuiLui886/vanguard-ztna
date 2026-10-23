# Client Windows tambahan — VanGuard0.1.9

**Pembaruan installer24 Oktober:** paket Windows baru menyertakan Python/WireGuard
dan dependensi dalam satu ZIP. Ikuti [panduan Windows terbaru](../deploy/endpoint/windows/SETUP_WINDOWS.md).
Bagian prasyarat manual/kandidat22Oktober di bawah tetap menjadi riwayat paket lama;
lihat checkpoint untuk hasil native aktual. Arsitektur, jaringan, CA dan admission
tidak berubah.

Pada 20 Oktober, client utama sudah di-upgrade ke0.1.9 dengan backup ZIP privat,
verifikasi dependensi dan hash identitas utama tetap sama. WireGuard/HTTP asli,
default-deny, LAN/portdeny, dua renewal67,18/71,73detik dan cleanup normal PASS.
Logout race/idempotensi/scope, unreachable, natural expiry, CA outage/recovery,
daemon stop/watchdog, reboot aktif dan admission baru PASS. TCP aktif terputus
setelah grant dihapus atau sertifikat dicabut. Penggantian dengan ID dan kedua
key baru dari Windows serta akun disabled PASS. Semua identitas disposable
dicabut dan akun uji disabled; task/service/config uji sudah tidak ada. Identitas
utama, Secure Boot/TPM dan definisi VM tetap sama. Ini tidak mencakup seluruh
kegagalan OS atau soak test panjang; cleanup interupsi di bawah masih risiko.
Readiness CA dapat sementara503 karena contention lock; liveness bukan readiness.
Untuk rincian dan batas bukti,
lihat [matriks aktual](VALIDASI_ROLLOUT_2026-10-20.md) dan [checkpoint](CHECKPOINT.md).

Jika cleanup menampilkan timeout, **jangan hapus config**. Pada uji interupsi
segera setelah install, service masih running meskipun uninstall telah diminta;
akses server dicabut dahulu. Operator mencocokkan path service dengan config
identitas uji, memastikan proses pemilik tidak lagi berjalan dan mengambil lock,
lalu menghentikan service yang tepat. Setelah uninstall terkonfirmasi1060,
config diarsipkan sebelum dihapus. Pemulihan ini tidak membenarkan penghapusan
service/config yang kepemilikannya belum dipastikan. Detail bukti tetap privat.

## Riwayat validasi0.1.8 dan kandidat0.1.9
Kandidat 0.1.9: [hardening dan rollout](HARDENING_0.1.9.md) menambahkan logout,
lock proses dan guard ownership saat cleanup. Gunakan `python -m vanguard.client
logout` setelah paket yang mendukungnya dipasang. Kegagalan kontak server
mempertahankan token untuk retry; config dipertahankan bila service belum pasti
berhenti atau ownership tidak diketahui. Bukti native terbaru dicatat pada
[checkpoint](CHECKPOINT.md); bagian berikut adalah riwayat 0.1.8.

Modul terpadu teknisi/admin/karyawan tersedia pada
[modul lengkap](MODUL_PENGGUNAAN_VANGUARD.md) dan
[HTML siap cetak](MODUL_PENGGUNAAN_VANGUARD.html). Audit bukti17 Oktober menemukan
satu siklus renewal otomatis PASS (sekitar61,83detik) dan cleanup PASS.
Pengamatan lease expiry terakhir masih IN_PROGRESS, belum dapat dinyatakan lulus.

Permintaan 13 Oktober 2026 menambahkan client Windows di samping lima VM Ubuntu.
VM-CLIENT lama tidak diganti. Status instalasi terbaru ada di
[checkpoint](CHECKPOINT.md) dan [jurnal](PROGRESS_2026-10-15.md).
Kode client lintas platform belum berarti tunnel Windows sudah terbukti hidup.

| Node | LAN | Tunnel | Peran |
|---|---|---|---|
| VM-CLIENT | 192.168.100.30 | 10.8.0.2 | Client Ubuntu yang lama |
| VM-CLIENT-WINDOWS | 192.168.100.60 | 10.8.0.4 | Client Windows tambahan |

CA, server, dashboard dan attacker tetap pada alamat/peran semula. Alamat tunnel
10.8.0.3 tetap untuk eksperimen, bukan Windows. Kedua client membuat key X.509
dan WireGuard masing-masing; key/certificate Ubuntu tidak disalin ke Windows.

## Hasil aktual 15 Oktober 2026

Windows terpasang dan console/password serta SSH key-only terverifikasi.
Build OS 26300, Secure Boot/TPM aktif; Python3.13.16, WireGuard1.1.1 dan client0.1.8.
23 tes native Windows lulus. Enrollment lewat dashboard HTTPS/TOTP menghasilkan
sertifikat dan binding akun karyawan terpisah, tanpa live peer. Login saja juga
belum menambah peer; sesi invalid dan proof invalid ditolak.

Admission, handshake WireGuard, ping server, admission ulang dan cleanup lulus.
Ubuntu `.2` serta Windows `.4` diuji bersamaan dengan dua handshake dan ping.
Sesudah cleanup Windows, Ubuntu tetap berfungsi. Pada 0.1.7 ditemukan race saat
service Windows dihapus asinkron; 0.1.8 menunggu konfirmasi service1060 sebelum
menghapus config. Jika gagal/timeout15detik, config dipertahankan untuk inspeksi.

Pengujian ini belum membuktikan revocation Windows, renewal otomatis jangka
panjang atau pemulihan reboot ketika tunnel aktif. Cleanup diuji menggunakan
interupsi terkontrol dalam runner integrasi; jangan mengklaim semua input console
Ctrl+C atau kegagalan jaringan sudah diuji. Tunnel Windows ditutup setelah tes.

Instalasi OpenSSH bawaan terhenti setelah interupsi. Guest menggunakan MSI resmi
Win32-OpenSSH10.0.0.0p2-Preview; SHA256 dan Authenticode Microsoft diverifikasi.
Fingerprint ED25519 dibandingkan dengan console sebelum koneksi SSH pertama.
Firewall hanya menerima host192.168.100.1, password SSH dimatikan. Panduan resmi:
[Microsoft MSI/ZIP OpenSSH](https://learn.microsoft.com/en-us/troubleshoot/windows-server/system-management-components/upgrade-in-box-openssh-to-latest-openssh-release).
Paket GitHub dipelihara manual; jangan menyebutnya capability bawaan Windows.
Script fallback dan manifest tetap pada direktori bukti privat. Kedua media CD
sudah dikeluarkan; jangan menjalankan ulang seed instalasi OS.

## Memakai Windows yang sudah terpasang

1. Nyalakan CA, SERVER, ADMIN dan VM-CLIENT-WINDOWS yang ada. Buka VM melalui
   `virt-viewer --connect qemu:///system VM-CLIENT-WINDOWS`.
2. Login menggunakan bagian VM-CLIENT-WINDOWS pada inventaris privat komputer
   host. Akun console berbeda dari akun karyawan VPN Windows.
3. Buka PowerShell **Run as administrator**. Gunakan virtualenv yang terpasang:

```powershell
$py = 'C:\ProgramData\VanGuard\venv\Scripts\python.exe'
& $py -m vanguard.client login --username USERNAME_KARYAWAN_WINDOWS
& $py -m vanguard.client connect --server-key PUBLIC_KEY_SERVER
```

Username karyawan tersedia di inventaris privat; password dimasukkan pada prompt
tersembunyi. Public key server diambil dari `/etc/vanguard/server-wg.pub` pada
VM-SERVER melalui koneksi yang terverifikasi. Sertifikat/root/key Windows sudah
ada pada `C:\ProgramData\VanGuard\client`; **jangan ulangi init atau enrollment**.
Biarkan terminal connect aktif. Dari terminal lain jalankan `ping 10.8.0.1`.
Hentikan connect dengan Ctrl+C, lalu pastikan service khusus dan config hilang.
Jika config tertinggal, inspeksi service terlebih dahulu; jangan hapus key.

## VM dan kebutuhan host

Rencana Windows 11: 2 vCPU, 4096 MiB RAM, disk sparse 80 GiB, UEFI Secure Boot
dengan enrolled Microsoft keys dan TPM virtual 2.0. Disk SATA dan NIC e1000e
dipilih agar installer awal tidak memerlukan driver VirtIO terpisah. VNC hanya
listen localhost dan bisa dibuka dengan:

```bash
virt-viewer --connect qemu:///system VM-CLIENT-WINDOWS
```

Host saat pemeriksaan memiliki RAM 7,5 GiB. Instalasi Windows dilakukan saat
kelima Ubuntu mati. Pengujian awal cukup CA/server/Windows; hidupkan dashboard
saat enrollment, dan client Ubuntu bila menguji dua client. Jangan menganggap
VM-ATTACKER atau client lain hidup jika tidak diperiksa. Autostart Windows mati.

Paket host: `ovmf swtpm swtpm-tools`. Skrip
`scripts/create_windows_client.py --output DIREKTORI_BUKTI` menghasilkan rencana;
`--define` membuat satu disk dan domain **tanpa menginstal OS atau menyalakannya**.
Skrip menolak domain/disk yang sudah ada. `--resume` terbatas pada kegagalan define
yang sudah tercatat setelah disk dibuat; jangan gunakan pada guest terpasang.
Lima XML domain Ubuntu dibandingkan sebelum/sesudah dan backup tetap privat.

Sumber media: [Microsoft Evaluation Center](https://www.microsoft.com/en-us/evalcenter/download-windows-11-enterprise).
Windows 11 Enterprise Evaluation berlaku 90 hari, bukan lisensi permanen.
Catat edisi/build, sumber, ukuran dan checksum ISO. File `.part` belum dapat dipakai.
Persyaratan resmi: [Windows 11 VM](https://learn.microsoft.com/en-us/windows/whats-new/windows-11-requirements).
Setup awal Windows dan penerimaan lisensi harus diselesaikan sebelum klaim live.

Seed privat dapat disiapkan dengan `scripts/prepare_windows_seed.py --output
state/deployment/windows-2026-10-13/private-seed`. Seed ini berisi jawaban setup
untuk memformat **disk Windows baru saja**, akun console dan password acak, serta
bootstrap LAN/SSH. Username/password dicatat pada kedua inventaris privat dengan
status PREPARED_NOT_INSTALLED. Jangan memakai seed untuk disk yang sudah berisi
data atau mengunggahnya. Autologon hanya untuk bootstrap; sesudahnya dinonaktifkan.
SSH guest memakai public key host dan dibatasi sumber 192.168.100.1; password SSH
dinonaktifkan. Akun console berbeda dari akun VPN yang akan dibuat saat enrollment.

`scripts/start_windows_install.py --evidence state/deployment/windows-2026-10-13
--media state/media/windows` memeriksa ukuran/hash lokal media lengkap, kelima
Ubuntu shut off, definisi kelima domain tidak berubah, disk baru masih kosong,
dan RAM/swap host cukup. Setelah itu media diunggah ke volume libvirt privat,
dipasang pada VM baru dan installer dimulai. Marker mencegah pengulangan format
otomatis. Status INSTALLING_GUEST_VALIDATION_PENDING belum berarti setup selesai.
Sesudah setup, keluarkan kedua CDROM, verifikasi login dan hapus salinan unattended
di guest yang masih menyimpan password; simpan seed/backup host secara privat.

## Melanjutkan setelah instalasi terputus

Jangan menyamakan laporan `INSTALLER_STARTED` dengan OS siap pakai. Periksa
console dan disk lebih dahulu. Pada 14 Oktober ditemukan partisi EFI kosong dan
penyalinan image kemarin terhenti 90%; mengulang seed awal akan memformat disk.

1. Pastikan hanya disk Windows tambahan yang ditangani. Kelima definisi Ubuntu
   harus tetap cocok backup awal. Simpan backup disk Windows saat guest mati.
2. Keluarkan seed awal sebelum boot ISO resmi ke WinPE. Periksa partisi dengan
   DiskPart dan log `C:\$WINDOWS.~BT\Sources\Panther`; huruf drive harus diverifikasi.
   Salin log sebelum mencoba pemulihan. Jangan menganggap bootloader saja rusak.
3. Untuk kasus ini, recovery seed dibuat privat dari jawaban awal dengan seluruh
   `DiskConfiguration` dihapus. Target tetap disk0/partisi3 yang telah diverifikasi.
   Seed asli, backup disk dan kredensial dipertahankan. Recovery tidak generik:
   jangan menjalankannya pada disk lain atau instalasi Windows yang telah selesai.
4. Pantau sampai Windows boot dan laporan bootstrap sukses, kemudian uji akses
   SSH, Secure Boot, TPM, alamat, aplikasi, admission dan cleanup secara terpisah.
   Catat tahap yang benar-benar terbukti; jangan mengulang setup saat masih berjalan.

Bukti pemulihan hari ini: [jurnal](PROGRESS_2026-10-14.md). Petunjuk diagnosis:
[log Windows Setup](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/deployment-troubleshooting-and-log-files?view=windows-11).

## Instalasi aplikasi di Windows

1. Pasang Python 3.12 atau lebih baru dari [python.org](https://www.python.org/downloads/windows/)
   dan [WireGuard for Windows resmi](https://www.wireguard.com/install/).
   Periksa tanda tangan installer. Jalankan PowerShell sebagai Administrator.
2. Atur LAN `192.168.100.60/24`, gateway/DNS `192.168.100.1`, dan sinkronkan jam.
   Jangan mematikan firewall Windows. Akses administrasi guest dibatasi host.
3. Pasang wheel VanGuard 0.1.8 yang sudah lulus CI pada virtualenv Python lokal.
   Dependensi Windows memakai pywin32; Gunicorn hanya untuk Linux.
4. Jalankan client sebagai Administrator. Default direktori adalah
   `C:\ProgramData\VanGuard\client`, dengan ACL SYSTEM/Administrators.
   Mode POSIX 0600 bukan pengganti ACL Windows. Path reparse point ditolak.

```powershell
python -m vanguard.client init --device-id vm-client-windows --tunnel-ip 10.8.0.4
```

`request.json` memuat CSR, public key WireGuard, device ID dan tunnel address.
Daftarkan request publik melalui dashboard, buat akun karyawan terpisah, dan
ikat akun itu ke `vm-client-windows`. Dokumentasikan nilai akun/password hanya
di inventaris privat komputer host. Registrasi ini belum menambahkan peer hidup.

Salin sertifikat hasil CA sebagai `device.crt` dan root CA yang telah diverifikasi
sebagai `root.crt` ke direktori client; keduanya publik. Simpan key privat hasil
init di guest. Root ini menjadi trust HTTPS sekaligus identitas CA lab.

```powershell
python -m vanguard.client login --username USERNAME_LOKAL
python -m vanguard.client admit
python -m vanguard.client connect --server-key PUBLIC_KEY_SERVER
```

Ganti placeholder dengan inventaris lokal/public key server terverifikasi.
Login meminta password tersembunyi dan menyimpan token sesi, bukan password.
Biarkan proses `connect` berjalan selama akses dibutuhkan. Ctrl+C membersihkan
tunnel. Setelah restart, login ulang jika sesi expired lalu jalankan `connect`.

Backend menggunakan [WireGuard tunnel service resmi](https://git.zx2c4.com/wireguard-windows/about/docs/enterprise.md),
`WireGuardTunnel$vanguard-client`. Service diubah ke demand start agar boot tidak
otomatis memulai konfigurasi lama. Lease server tetap membatasi akses jika proses
client mati mendadak. Kegagalan renewal memicu pelepasan tunnel. Bila pelepasan
gagal, konfigurasi dipertahankan agar retry menolak mengambil alih tanpa inspeksi.
Untuk pemulihan setelah crash, pastikan proses lama sudah berhenti, lalu uninstall
service khusus ini sebelum menghapus `vanguard-client.conf`; jangan hapus key.

## Server dan validasi wajib

Firewall server memerlukan perluasan eksplisit:

```bash
sudo python3 deploy/firewall.py server --management-ip 192.168.100.1 --windows-client
```

Gunakan source yang disalin ke VM-SERVER dan prosedur rollback timer yang sama
seperti [deployment](DEPLOYMENT.md). Konfirmasi akses lewat SSH baru sebelum
mematikan timer rollback. Flag ini membuka API 8081/UDP 51820 dari .60 dan ICMP
dari .4 **hanya pada wg0**. Drop bypass LAN dan forward default drop tetap berlaku.
Default tanpa flag mempertahankan firewall lima VM lama. Deployment firewall ini
harus dibuktikan, bukan dianggap terjadi karena source sudah berubah.

Urutan bukti guest Windows yang harus disimpan sebelum menyatakan dukungan penuh:

1. OS/build, TPM/Secure Boot, LAN, sinkronisasi jam dan ACL identitas.
2. Enrollment tanpa peer; login saja juga tidak menambahkan peer.
3. Admission enam pemeriksaan, handshake WireGuard dan ping 10.8.0.1.
4. Client Ubuntu dan Windows hidup bersamaan tanpa konflik alamat/key.
5. Sertifikat/sesi tidak sah ditolak; revocation Windows menghentikan Windows,
   sementara client Ubuntu tetap berfungsi. Gunakan identitas uji untuk pencabutan.
6. Ctrl+C, kegagalan renewal dan reboot: cleanup, demand start dan lease expiry.

CI Windows hanya menguji helper client, file/sesi dan ACL native; backend command
diuji dengan stub. CI itu tidak membuktikan handshake atau admission di VM lab.
Runner benchmark/security/health lama masih menargetkan lima Ubuntu; jangan
menghitungnya sebagai bukti Windows atau menjalankannya lewat SSH Linux pada .60.

## Validasi kandidat19 Oktober2026

Source0.1.9 diuji pada folder staging terpisah di VM Windows:28 PASS/2 SKIP
(khusus POSIX),0,84detik. ACL dan competing lock native lulus; command service
WireGuard memakai stub. Satu failure awal PermissionError pada lock telah
diperbaiki. Ini tidak memasang paket baru pada identitas utama atau membuktikan
revocation/reboot tunnel Windows. Pengguna melaporkan boot/desktop lambat;
diagnosis terukur berjalan sesuai checkpoint. Tidak ada reset credential.

## Perbaikan respons Windows — 19 Oktober2026

VM yang sama sekarang memakai `hypervclock`, `vpindex`, `synic` dan `stimer`.
Sebelumnya hanya relaxed/vapic/spinlocks dengan HPET off. Clock Hyper-V
mengurangi overhead pembacaan waktu; synthetic timer menghindari fallback timer
emulasi yang mahal. Dependensinya mengikuti [dokumentasi resmi QEMU](https://www.qemu.org/docs/master/system/i386/hyperv.html).
Ini perubahan XML virtualisasi, bukan perubahan kernel/WireGuard atau instalasi
ulang Windows. UUID,disk,MAC,TPM/UEFI,4GiB RAM dan2vCPU tetap sama.

| Pengukuran aktual | Sebelum | Sesudah |
|---|---|---|
| Satu juta time.perf_counter(), tiga pengulangan | 2,6316–3,1764 detik | 0,04508–0,05138 detik |
| Start domain hingga perintah SSH berhasil, satu sampel | 50,12 detik (Hiberboot) | 27,49 detik (boot penuh) |
| Native helper/ACL setelah perubahan | — | 28 PASS/2 SKIP khusus POSIX |

Microbenchmark membuktikan overhead timestamp turun. Sampel startup memakai
jenis boot berbeda dan belum diulang, sehingga bukan bukti persentase percepatan
boot yang umum. Respons desktop setelah login masih perlu observasi pengguna.
Event boot sebelumnya juga mencatat aktivitas Defender dan waktu tunggu login;
Defender,Secure Boot,TPM dan kebijakan password tidak dinonaktifkan.

Backup XML asal dan candidate, hash lima node Ubuntu serta hash identitas
Windows berada privat di state/hardening/2026-10-19/windows-boot-2255/.
Hash identitas sebelum/sesudah cocok; Secure Boot/TPM tetap aktif. VM Windows
dibiarkan running dengan viewer tersedia; lima Ubuntu tetap shut off pada akhir
pengujian. Paket utama Windows masih0.1.8; helper0.1.9 diuji dari staging.

Jika konfigurasi timer perlu dibatalkan: simpan pekerjaan guest, pastikan tunnel
sudah berhenti, lakukan shutdown normal dan verifikasi domain shut off. Gunakan
`virsh -c qemu:///system define PATH_BACKUP_DOMAIN_BEFORE_XML --validate`, lalu
start domain yang sama. Gunakan backup milik VM ini; jangan restore disk,
TPM/NVRAM,identity,CA atau menjalankan ulang script first-install.
Template scripts/create_windows_client.py sekarang mencakup timer yang sama
untuk provisioning baru. Script tersebut tetap menolak VM existing.

Saat membuka Windows, beri waktu OS/service siap dan tunggu layar login
merespons sebelum mengetik. Readiness SSH tidak otomatis berarti desktop atau
VPN siap. Host hanya7,5GiB RAM dan backing disk guest berada pada perangkatUSB;
jalankan VM yang diperlukan secara bertahap, hindari pengujian I/O berat
bersamaan. Pengukuran ini tidak mengubah atau menghapus lima Ubuntu.

## Kandidat endpoint fisik0.1.12 —22 Oktober2026

Client Windows VM lama tetap dipertahankan. Pilot PC LAN dan laptop Wi-Fi adalah
endpoint tambahan, bukan penggantian VM dan bukan hasil yang sudah diuji. Gunakan
[panduan pilot lengkap](ENDPOINT_WINDOWS_PILOT.md) dan Bab15.3 pada modul tunggal.
Source installer ada di `deploy/endpoint/windows`; jangan menggunakan
`deploy/windows/bootstrap.ps1` provisioning VM pada perangkat fisik.

Paket offline lokal memerlukan Python3.13x64/WireGuard resmi yang sudah tersedia,
profil/root tepercaya, admin/UAC dan Windows11x64. Belum signed; fresh install,
repair, upgrade, uninstall, ACL, reboot, Wi-Fi dan pilot bersama BELUM_DIJALANKAN.
Tidak ada VM/router/NIC yang diubah pada tahap persiapan ini. Konfigurasi native
hanya dianggap siap setelah matriks uji target terpenuhi, bukan karena unit tests
Linux atau helper CI lama lulus. WIN-CLEANUP-02 belum ditutup oleh installer ini.
