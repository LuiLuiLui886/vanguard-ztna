# Installer VanGuard Windows10/11 x64

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
