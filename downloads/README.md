# Installer VanGuard Windows10/11 x64

Lihat **flowchart seluruh sistem** pada [referensi flowchart pada manual](../docs/MODUL_PENGGUNAAN_VANGUARD.md#10-masalah-umum-dan-pemeriksaan-akhir): CA/backend → installer → enrollment → akses → pencabutan dan audit.

## EXE dan template0.1.15 — branch feature

[EXE offline0.1.15](Setup-VanGuard-0.1.15.exe) dan
[template satu folder0.1.15](vanguard-windows10-11-setup-template-0.1.15-20261102.zip)
memuat perbaikan respons login/logout, diagnostik readiness dan manual ringkas.
Cocokkan [checksum](SHA256SUMS). Profil, CA publik, approval admin dan login
karyawan tetap diperlukan; kunci privat dibuat di endpoint.

Windows10 build19044 dan Windows11 build26300: EXE identik terpasang dengan
exit0, versi0.1.15; hash identitas, konfigurasi dan profil firewall tetap.
Rincian hasil dan batas pengujian tersedia dalam
[laporan rilis](../docs/reports/VALIDASI_0.1.15_2026-11-02.md). Paket belum ditandatangani
Authenticode. UAC interaktif, Windows kosong dan perangkat fisik BELUM_TERUJI.
Branch: **feature/2026-10-22-physical-endpoints**.

## Arsip versi sebelumnya

EXE/ZIP versi 0.1.14-fix1 dan 0.1.12 dipindahkan ke [folder archive](archive/).
File tetap tersedia; isi dan hash tidak berubah. Gunakan versi terbaru di atas
untuk mengikuti panduan saat ini. [Manual utama](../docs/MODUL_PENGGUNAAN_VANGUARD.md)
tetap menjadi satu panduan penggunaan.

Untuk memeriksa semua unduhan setelah clone, dari folder ini jalankan
`sha256sum -c SHA256SUMS` pada Linux, atau cocokkan file yang dipilih menggunakan
`Get-FileHash -Algorithm SHA256` pada PowerShell.
