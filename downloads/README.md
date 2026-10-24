# Download installer VanGuard Windows

Gunakan **main** untuk paket terbaru. Paket Windows24Oktober menyatukan installer
Python3.13.17, WireGuard1.1.1,20wheel offline aplikasi/dependensi, BAT dan panduan
setup dalam satu ZIP. Tidak perlu memasang Python/WireGuard secara manual jika
belum ada. Runtime bersama yang sudah sesuai dipertahankan.

| Paket | Penggunaan | Ukuran |
|---|---|---|
| [Installer Windows lengkap24Oktober](vanguard-windows-offline-0.1.12-20261024.zip) | **Pilihan untuk PC baru:** ekstrak seluruh isi, buka SETUP_WINDOWS.html lalu Install-VanGuard.bat |44.649.724byte |
| [SHA256SUMS](SHA256SUMS) | Checksum ZIP dari sumber proyek tepercaya | — |
| [Kit sistem22Oktober — arsip](vanguard-installation-20261022-docs-r2.zip) | Profil/root publik, wheel admin, pemeriksa dan panduan backend; **installer Windows di dalamnya sudah digantikan paket24Oktober** |12.421.751byte |
| [Dokumentasi22Oktober — arsip](vanguard-dokumentasi-penerapan-20261022-r2.zip) | Modul utama dan panduan backend historis; gunakan docs di main untuk pembaruan |338.739byte |

Pilih **Download raw file** pada halaman ZIP GitHub, atau clone/pull biasa. Tidak
memerlukan Git LFS, GitHub CLI maupun Git bila mengunduh lewat browser. ZIP tidak
berisi password, token, private key, state VM atau identitas komputer siap pakai.

## Mulai di PC Windows LAN

1. Unduh ZIP Windows24Oktober, cocokkan checksum di bawah dari halaman proyek
   tepercaya. Jangan hanya memindahkan BAT; seluruh folder harus tetap bersama.
2. Buka **Windows PowerShell → Run as administrator**, ekstrak ke folder baru di
   Program Files. Jangan menjalankan file dari tampilan ZIP.
3. Baca **SETUP_WINDOWS.html**, jalankan **Install-VanGuard.bat**, tunggu exit0.
   Installer memverifikasi hash dan Authenticode Python/WireGuard. Tidak meminta
   password VM, path Python atau thumbprint signer. UAC dapat muncul bila belum
   elevated; dialog UAC interaktif belum diuji pada sesi native ini.
4. Periksa `VanGuard.bat status`. Pesan profil belum tersedia adalah normal pada
   pemasangan baru; aplikasi belum memiliki identitas atau tunnel.
5. Admin menyiapkan backend/jaringan, profil/root tepercaya, akun dan alokasi ID/IP.
   Lanjut configure → init (key/CSR di PC) → kirim request.json ke admin → registrasi
   dan download bundle → import-bundle → login → connect. Panduan dalam ZIP
   menjelaskan tiap langkah. **Komputer baru tidak membuat Root CA baru.**

```powershell
$kitZip = Join-Path $env:USERPROFILE 'Downloads\vanguard-windows-offline-0.1.12-20261024.zip'
$expected = '91b551183f1f197d7390e32b31ff4de3da33ef62261e73fba572784b05b396dd'
if ((Get-FileHash -LiteralPath $kitZip -Algorithm SHA256).Hash -ne $expected) {
    throw 'Checksum tidak cocok; jangan lanjut.'
}
$kitPath = Join-Path $env:ProgramFiles 'VanGuardInstaller20261024'
if (Test-Path -LiteralPath $kitPath) { throw 'Gunakan folder baru; jangan timpa instalasi/identitas lama.' }
Expand-Archive -LiteralPath $kitZip -DestinationPath $kitPath -ErrorAction Stop
Start-Process (Join-Path $kitPath 'SETUP_WINDOWS.html')
& (Join-Path $kitPath 'Install-VanGuard.bat')
& "$env:ProgramFiles\VanGuardEndpoint\VanGuard.bat" status
```

Exit1/2 berarti gagal: catat fase/alasan aman.1223 berarti UAC batal/tidak tersedia;
3010 berarti simpan pekerjaan, restart manual lalu jalankan lagi. Jangan mengirim
password, OTP, token atau isi private key ketika melaporkan error.

BAT memilih RemoteSigned untuk proses saat semua scope policy Undefined. Policy
organisasi/eksplisit tetap dihormati, tidak ada perubahan policy permanen. Skrip
aplikasi masih unsigned; tanda internet/MOTW dapat menyebabkan penolakan. Jika
terjadi, admin perlu distribusi/signing sesuai kebijakan. Installer tidak menghapus
MOTW atau mematikan proteksi otomatis. Pemeriksaan kepercayaan Authenticode tetap
harus berhasil; seluruh payload runtime/pip sudah tersedia lokal.

## Ambil melalui Git

Dari clone yang bersih, gunakan `git switch main` kemudian `git pull --ff-only`.
Jika belum ada clone:

```powershell
gh repo clone LuiLuiLui886/vanguard-ztna
cd vanguard-ztna
```

Jangan reset/force perubahan lokal untuk melewati konflik. Jika branch lama berisi
pekerjaan sendiri, simpan pekerjaan tersebut sebelum berpindah. Main menyatukan
histori hardening, readiness dan endpoint; branch feature tetap untuk pengembangan.

## Batas penggunaan dan bukti

[Hasil uji aktual](../docs/VALIDASI_INSTALLER_2026-10-24.md) membedakan Linux/CI,
Windows VM native dan PC fisik. Label CANDIDATE_NATIVE_TESTS_REQUIRED pada manifest
adalah metadata saat build; laporan menyimpan hasil uji paket dengan checksum di
atas. Keberhasilan instalasi tidak membuktikan VPN, firewall atau backend sehat.

Ikuti [panduan lengkap Windows](../docs/MODUL_PENGGUNAAN_VANGUARD.md),
[runbook sistem](../docs/MODUL_PENGGUNAAN_VANGUARD.md), dan
[checkpoint](../docs/CHECKPOINT.md). Paket0.1.12 admin diperlukan untuk bundle
berprofil; installer Windows tidak memperbarui backend. Root/public key/alokasi
IP harus dikonfirmasi admin. IP LAN192.168.50.20 berbeda dari IP tunnel. Tidak ada
peer statis atau bypass enam pemeriksaan perangkat dan sesi karyawan.
