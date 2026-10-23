# VanGuard Windows: instalasi sampai terdaftar di admin

Paket offline untuk Windows 11 x64. Satu folder memuat BAT/PowerShell, installer
Python 3.13.17, WireGuard 1.1.1, wheel aplikasi/dependensi dan panduan ini.
Internet tidak diperlukan untuk pip/runtime; pemeriksaan kepercayaan tanda tangan
Windows tetap harus berhasil. Jangan mematikan pemeriksaan signature atau policy.

## 1. Persiapan dan memasang aplikasi

1. Ambil ZIP terbaru dari halaman downloads repo main. Bandingkan SHA256 dengan
   nilai yang diberikan admin/halaman GitHub tepercaya sebelum menjalankan file.
2. Ekstrak **seluruh isi** ke folder baru, misalnya
   `C:\Program Files\VanGuardInstaller`. File BAT, PS1, manifest, folder runtimes
   dan wheels harus tetap bersama. Windows meminta izin admin saat menyalin.
   Jangan menjalankan BAT dari dalam tampilan ZIP atau hanya menyalin BAT.
3. Buka `Install-VanGuard.bat`. Setujui UAC. Jika semua scope policy belum
   diatur (Undefined), BAT memilih RemoteSigned hanya untuk proses ini; tidak
   menyimpan policy ke registry. Policy eksplisit tetap dihormati. Jika policy organisasi menolak
   PowerShell, hubungi admin untuk distribusi/signing yang diizinkan; jangan
   mengubah execution policy global atau mematikan Defender/SmartScreen.
4. Installer memeriksa integritas seluruh paket serta Authenticode publisher
   Python Software Foundation/WireGuard LLC. Python3.13 x64 all-users yang valid
   dan WireGuard yang sudah terpasang dipakai kembali. Runtime belum ada dipasang
   dari runtimes. PATH global, DNS, IP LAN dan identitas lama tidak diubah.
5. Tunggu hingga **Exit code: 0**. Kode1/2 berarti gagal: baca fase dan alasannya;
   1223 berarti UAC batal;3010 meminta restart manual, lalu jalankan installer lagi.
   Tidak ada reboot otomatis. Runtime parsial tidak dihapus/ditimpa sembarangan.
6. Buka PowerShell Administrator dan periksa:

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg status
```

Pada instalasi baru, `Terpasang; profil tepercaya belum tersedia` normal.
Aplikasi di `C:\Program Files\VanGuardEndpoint`; konfigurasi/identitas di
`C:\Program Files\VanGuardEndpointData`. Installer tidak membuat key, mendaftar
perangkat, login, memasang peer, atau menyalakan tunnel.

## 2. Siapkan jaringan dan data dari administrator

Sebelum enrollment, admin menyiapkan backend yang sehat, sertifikat HTTPS sesuai
alamat API, profil publik `profile.json`, `root.crt`, fingerprint SHA256 root,
public key WireGuard server, device ID unik, IP tunnel kosong dan akun karyawan.
Konfirmasi fingerprint/key melalui komunikasi admin yang tepercaya, bukan hanya
karena ada di ZIP. Bundel installer tidak berisi kredensial atau alokasi identitas.

Untuk pilot PC LAN: alamat PC192.168.50.20/24, router192.168.50.1, host Linux
192.168.50.10. Backend API192.168.100.20:8081 HTTPS dan UDP51820. Operator memeriksa
routing/firewall sesuai runbook repo; installer tidak mengubahnya. IP tunnel
berbeda dari IP LAN.10.8.0.2/.3/.4 sudah dicadangkan; .5/.6 hanya boleh dipakai
setelah admin memeriksa registry. PC dan laptop wajib memiliki identitas berbeda.

Admin memerlukan kandidat0.1.12 dengan VANGUARD_CLIENT_PROFILE yang sesuai untuk
bundle berprofil. Paket backend/VM lama tidak otomatis di-upgrade oleh installer
Windows. Hentikan alur jika bundle tidak memiliki profil yang cocok.

Simpan profil/root di folder admin-only, misalnya `C:\Program Files\VanGuardTrust`.
Dari PowerShell Administrator:

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg configure
& $vg status
```

Masukkan lokasi profil/root, fingerprint dan public key saat diminta. Configure
menolak penimpaan konfigurasi lama. Data rahasia CA tidak pernah disalin ke PC.

## 3. Komputer baru membuat key dan CSR, bukan CA baru

**CA hanya satu, tetap di VM-CA.** Komputer baru membuat private key X.509 dan
WireGuard sendiri serta permintaan sertifikat (CSR). CA menandatangani CSR setelah
admin mendaftarkan perangkat. Jangan menjalankan init CA, membuat root pengganti,
menyalin private key CA atau menyalin identitas komputer lain.

```powershell
& $vg init
```

Isi device ID dan IP tunnel yang dialokasikan admin. Hasil request publik ada di:
`C:\Program Files\VanGuardEndpointData\identity\request.json`.
Kirim **hanya request.json** ke admin melalui jalur yang disepakati. Private key
`identity.key`, `wg.key`, sesi/token dan seluruh folder identity jangan dikirim.
Init hanya untuk perangkat baru; reinstall tidak memerlukan init ulang.

## 4. Administrator mendaftarkan perangkat

Pada komputer admin/jalur management yang diizinkan:

1. Buka dashboard HTTPS VanGuard dengan trust root yang telah diverifikasi.
   Untuk lab, endpoint dashboard192.168.100.40:5000. Jangan membuka CA/dashboard
   ke seluruh jaringan PC fisik hanya untuk mempermudah enrollment.
2. Login menggunakan akun administrator dan TOTP dari authenticator admin.
   Akun administrator berbeda dari akun karyawan untuk VPN.
3. Pada formulir akun karyawan, buat akun yang disetujui (atau gunakan akun sah
   yang tersedia), dengan password melalui form. Username/password dibagikan
   secara privat; jangan memasukkannya ke Git atau dokumentasi publik.
4. Pada formulir registrasi perangkat, masukkan request.json publik, metadata
   pemilik/departemen/platform (Windows11) dan pilih akun karyawan. Cocokkan device ID, IP tunnel,
   public key/CSR dengan permintaan dari PC yang benar.
5. Proses registrasi meminta sertifikat ke CA dan menyimpan binding sertifikat,
   public key WireGuard, device ID, IP tunnel serta akun karyawan. Registrasi
   **tidak menambahkan live peer**. Status harus registered; jika pending_issue/
   pending_registry, perbaiki dependensi dan gunakan retry, jangan membuat CA baru.
6. Unduh bundle perangkat dari dashboard. Bundle berisi sertifikat publik,
   root publik, manifest/profil dan README; tidak berisi private key client.
   Kirim bundle kembali ke PC asal. Catat waktu/aktor dan lihat audit/history.

Menghasilkan Root CA pertama kali hanya untuk instalasi sistem benar-benar baru,
bukan langkah onboarding PC. Prosedur inisialisasi lengkap ada pada modul utama
repo `docs/MODUL_PENGGUNAAN_VANGUARD.html`, Bab5.3. Sistem yang sedang digunakan
harus mempertahankan root, index, serial, CRL serta histori pencabutannya.

## 5. Import sertifikat, login dan koneksi

Letakkan bundle publik dari admin di folder terlindungi, lalu:

```powershell
& $vg import-bundle
& $vg status
& $vg diagnose
& $vg login
& $vg connect
```

Import meminta path bundle dan memeriksa binding dengan kedua key asli, profil,
root dan sertifikat. Login meminta username karyawan serta password interaktif
tersembunyi. Jangan menaruh password pada argumen terminal. Diagnose memeriksa
HTTPS/readiness; bukan bukti UDP/tunnel. Enam pemeriksaan perangkat dan sesi
karyawan tetap wajib sebelum server menambahkan peer.

Biarkan terminal connect terbuka agar lease diperbarui. Dari terminal lain uji
aplikasi yang diizinkan, misalnya `http://10.8.0.1:8082` jika admin telah menjalankan
demo dan memberi grant eksplisit identitas/resource/TCP/port8082. Tanpa grant,
akses seharusnya ditolak. Jangan menambahkan peer statis lewat GUI WireGuard.

## 6. Disconnect, logout, repair dan pencabutan

Ctrl+C pada terminal connect meminta cleanup. Alternatif terminal admin kedua:

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg disconnect
& $vg logout
```

Disconnect menutup tunnel milik sesi. Logout meminta pencabutan sesi server;
server tidak terjangkau berarti pencabutan **belum terkonfirmasi**. Jangan menghapus
config jika penghentian tunnel/kepemilikannya belum pasti. Admin dapat mencabut
identitas atau menonaktifkan akun melalui dashboard ketika perangkat hilang.

Repair/reinstall: disconnect dahulu, jalankan BAT lagi. Key/config dipertahankan;
runtime aplikasi baru diuji sebelum dipakai. Uninstall aplikasi:

```powershell
& "$env:ProgramFiles\VanGuardEndpointData\tools\Uninstall-VanGuard.bat"
```

Uninstall mempertahankan data identitas, tools maintenance dan Python/WireGuard bersama. Menghapus
aplikasi bukan revocation server; decommission harus diselesaikan admin.

## 7. Sumber paket dan batas pengujian

Installer runtime disalin tanpa modifikasi dari:

- Python: https://www.python.org/downloads/windows/ dan
  https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.exe
- WireGuard: https://www.wireguard.com/install/ dan
  https://download.wireguard.com/windows-client/wireguard-amd64-1.1.1.msi
- Opsi Python: https://docs.python.org/3.13/using/windows.html
- Source WireGuard Windows: https://git.zx2c4.com/wireguard-windows/

Versi/hash/URL tercatat di runtime-lock.json. Signature diverifikasi di Windows
sebelum runtime dijalankan. Paket aplikasi sendiri belum Authenticode-signed.
Hasil uji aktual tercatat di checkpoint repo; keberhasilan VM tidak otomatis
membuktikan PC LAN/laptop Wi-Fi, policy organisasi, UAC interaktif atau semua
skenario OS. Uji aplikasi dengan satu perangkat dahulu, kemudian perangkat kedua.

Execution policy proses dijelaskan Microsoft di
https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1 .
RemoteSigned tetap menolak skrip unduhan internet yang unsigned bila ditandai
MOTW. Jika ditolak, admin perlu distribusi/signing sesuai kebijakan; installer
tidak menghapus tanda internet secara otomatis.
