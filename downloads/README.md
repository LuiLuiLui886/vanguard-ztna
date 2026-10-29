# Installer VanGuard Windows10/11 x64

Lihat **flowchart seluruh sistem** pada [manual Bab1.1](../docs/MODUL_PENGGUNAAN_VANGUARD.md#11-flowchart-sistem-lengkap-dari-ca-sampai-exe-dan-penggunaan): CA/backend → installer → enrollment → akses → pencabutan dan audit.

## EXE offline0.1.14-fix1 — kandidat pada branch feature

[Unduh Setup-VanGuard-0.1.14-fix1.exe](Setup-VanGuard-0.1.14-fix1.exe)
melalui **Download raw file**, lalu cocokkan [SHA256](SHA256SUMS).
Python, WireGuard, dependensi dan aplikasi sudah dibundel. EXE umum ini memasang
prasyarat/aplikasi; **profil server, CA publik dan alokasi perangkat tetap perlu
disiapkan admin**. Untuk satu EXE yang juga menjalankan wizard pendaftaran,
admin membangun EXE per-device sesuai [manual tunggal Bab14.0.1](../docs/MODUL_PENGGUNAAN_VANGUARD.md).
Kunci dibuat di endpoint; approval admin dan login karyawan tetap wajib.

EXE belum ditandatangani Authenticode. Jangan menonaktifkan proteksi Windows jika
policy menolak; konfirmasikan origin/checksum dan minta pemeriksaan admin.
[Hasil uji dan keterbatasan](../docs/VALIDASI_EXE_2026-10-29.md) membedakan Windows10
native dari UAC/browser, Windows11 wrapper, OS fresh dan PC fisik yang belum diuji.
Branch: **feature/2026-10-22-physical-endpoints**; paket stabil/main tidak diganti.

## Kandidat setup terpadu0.1.14-fix1 — untuk persiapan admin

[Template offline satu folder](vanguard-windows10-11-setup-template-0.1.14-fix1-20261029.zip)
menyertakan Python/WireGuard, wheel aplikasi dan `Setup-VanGuard.bat`.
**Template ini belum berisi profil CA/server atau alokasi perangkat.** Admin
menyiapkan paket per-device dengan builder dan input publik tepercaya menurut
[manual Bab14.0](../docs/MODUL_PENGGUNAAN_VANGUARD.md); wheel/runtime dapat diambil
dari folder template yang diekstrak. User akhir menerima paket hasil persiapan
admin, lalu menjalankan satu BAT untuk install/config/request/import/login/connect.
Pendaftaran tetap menunggu persetujuan admin dan password dimasukkan saat login.
Tidak membagikan paket fixture lab. Kandidat berada pada branch feature; lihat
[hasil native dan batas bukti](../docs/VALIDASI_SETUP_TERPADU_2026-10-29.md).
Cocokkan [checksum](SHA256SUMS) sebelum ekstraksi/eksekusi.

Fix1 memperbaiki resume setelah pemasangan ulang terputus.
[Laporan bug dan uji repair](../docs/AUDIT_WIZARD_2026-10-29.md):6kasus kontrol
alur native dan7kasus installer/runtime nyata terisolasi lulus di Windows10.
Wheel tetap0.1.14; ini revisi script installer. EXE alternatif tersedia di atas;
ZIP tetap berguna sebagai input admin untuk membangun paket per-device.

## Paket sebelumnya0.1.12

[Satu ZIP lengkap25Oktober](vanguard-windows10-11-offline-0.1.12-20261025.zip)
(44.675.510byte) berisi BAT, Python3.13.17, WireGuard1.1.1,20wheel offline,
dan manual admin. [Checksum SHA256](SHA256SUMS) harus dicocokkan sebelum eksekusi.
Unduh melalui **Download raw file**, atau clone/pull branch **main**.

**Satu manual resmi:** [baca manual admin18bab](../docs/MODUL_PENGGUNAAN_VANGUARD.md).
Salinan HTML di dalam ZIP bernama `MODUL_PENGGUNAAN_VANGUARD.html`; Bab10
menjelaskan ekstraksi dan instalasi, Bab11–12 konfigurasi endpoint, CSR,
registrasi admin, import sertifikat, login dan koneksi. Bab5–9 mencakup backend,
CA, jaringan dan profil. Komputer baru memakai CA yang sama, dengan key baru
buatan client. Seluruh file ZIP harus diekstrak bersama; jangan mengambil BAT saja.

Target: Windows10 x64 build19044/19045 dan Windows11 x64 build22000 ke atas.
[Lihat checkpoint untuk hasil native per OS/build](../docs/CHECKPOINT.md).
Kompatibilitas installer tidak menjamin status dukungan keamanan OS, akses VPN,
UAC interaktif atau distribusi browser/MOTW/GPO; ikuti batas bukti pada laporan.
[Perbaikan konfigurasi terputus](../docs/AUDIT_WINDOWS_CONFIG_2026-10-25.md) masuk dalam ZIP ini;
retry pasangan root/profil identik kini dapat menyelesaikan konfigurasi parsial.
Paket aplikasi masih unsigned dan menghormati policy organisasi.

Tutorial dan ZIP lama telah dikeluarkan dari tree aktif agar tidak membingungkan.
Histori tetap tersedia pada [snapshot sebelum konsolidasi](https://github.com/LuiLuiLui886/vanguard-ztna/tree/31c69816f4860869f3483dab86d3452bdb54333c/downloads).
Password, token, private key dan identitas komputer tidak disertakan.
