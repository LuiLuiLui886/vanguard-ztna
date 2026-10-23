# Download kit VanGuard untuk uji Windows

Paket ZIP berikut ikut Git sejak23 Oktober2026, sesuai permintaan pengguna.
Gunakan branch **feature/2026-10-22-physical-endpoints**. Semua isi adalah kandidat
pilot0.1.12, belum klaim pemasangan Windows native/fisik berhasil.

| Paket | Isi | Ukuran |
|---|---|---|
| [Kit instalasi lengkap](vanguard-installation-20261022-docs-r2.zip) | BAT/PowerShell,20wheel Windows offline, profil/root publik, wheel admin, pemeriksa dan panduan17bab |12.421.751byte |
| [Dokumentasi saja](vanguard-dokumentasi-penerapan-20261022-r2.zip) | PanduanHTML/Markdown, modul utama dan dokumen pendukung |338.739byte |
| [SHA256SUMS](SHA256SUMS) | SHA256 kedua ZIP | — |

Di halaman file GitHub, pilih **Download raw file** untuk mengambil ZIP. Clone/
pull Git biasa juga membawa file ZIP ini; tidak memerlukan Git LFS. Installer
runtime Python/WireGuard tidak disertakan: Python3.13x64 dengan pip/venv dan
WireGuard resmi terverifikasi harus tersedia dahulu. Kit tidak berisi username/
password operasional, token, private key atau state VM. Root CA dalam kit adalah
sertifikat publik; tetap cocokkan fingerprint dan server public key melalui admin.

## Mengambil melalui PowerShell

Jika repo sudah di-clone, jalankan dari folder repo dan pastikan perubahan lokal
sudah diamankan. Jangan reset/force untuk melewati perubahan yang belum disimpan.

```powershell
git switch feature/2026-10-22-physical-endpoints
git pull --ff-only
Get-ChildItem .\downloads
```

Jika belum punya repo:

```powershell
gh repo clone LuiLuiLui886/vanguard-ztna -- --branch feature/2026-10-22-physical-endpoints
cd vanguard-ztna
```

## Verifikasi dan buka kit

Jalankan PowerShell **Administrator** dari folder repo. Tujuan ekstraksi harus
folder baru; jangan mencampur kit dengan identitas/runtime yang sudah terpasang.
Hash berikut sesuai ZIP yang telah dipindai dan diverifikasi pada komputer proyek:

```powershell
$kitZip = '.\downloads\vanguard-installation-20261022-docs-r2.zip'
$expectedZip = '19ede36ca3967f4717e012e3d027e341331bc837fda57cbc8255eefceb078f30'
if ((Get-FileHash -LiteralPath $kitZip -Algorithm SHA256).Hash -ne $expectedZip) {
    throw 'Hash ZIP berbeda; jangan lanjut.'
}
$kitPath = Join-Path $env:ProgramFiles 'VanGuardPilotKit'
if (Test-Path -LiteralPath $kitPath) {
    throw 'Folder tujuan sudah ada; inspeksi instalasi/kit lama sebelum melanjutkan.'
}
Expand-Archive -LiteralPath $kitZip -DestinationPath $kitPath -ErrorAction Stop
Start-Process (Join-Path $kitPath 'START_HERE.html')
```

Baca panduan dahulu. Sesudah hash dan asal kit diverifikasi, identitas operator/
runtime tepercaya tersedia, gunakan pemeriksa dan installer dari lokasi terlindungi:

```powershell
& "$env:ProgramFiles\VanGuardPilotKit\checks\Check-Endpoint.ps1" -Role PC
& "$env:ProgramFiles\VanGuardPilotKit\windows\Install-VanGuard.bat"
```

`Check-Endpoint` read-only dan exit2 berarti review/tes target masih diperlukan;
periksa setiap FAIL/UNKNOWN. Jangan bypass execution policy/signing organisasi.
Installer menanyakan hash **windows/manifest.json** (berbeda dari hash ZIP/kit):

```text
47b50e47e156e1b41ff11ffba01e0e76433eb5f96cfde81b4b6df8361f530cb1
```

Hash **kit-manifest.json** untuk checks/verify_kit.py:

```text
4649b11f89a18ba08da9df32fe4e30aa0b940796f86eedcb06dd045df1ce701e
```

Manifest/hash membuktikan integritas terhadap nilai tepercaya, bukan jaringan
siap atau identitas sudah disahkan. Backend, alokasi ID/IP, trust, firewall dan
enrollment tetap harus selesai sebelum connect. Jangan menjalankan init pada
identitas yang sudah ada atau menambahkan peer WireGuard statis.

Dokumen di ZIP adalah snapshot22Oktober sehingga beberapa catatan menyebut belum
push atau artefak hanya lokal. Publikasi ZIP disetujui23Oktober; gunakan README
ini dan [checkpoint terbaru](../docs/CHECKPOINT.md) untuk status publikasi.
Isi arsip tidak diubah agar checksum dan bukti pengujian sebelumnya tetap berlaku.
