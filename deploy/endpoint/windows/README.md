# Installer Windows VanGuard dengan prasyarat offline

Baca **SETUP_WINDOWS.html** atau SETUP_WINDOWS.md untuk instalasi, konfigurasi,
CSR pada komputer baru, pendaftaran admin, import sertifikat, login dan pemakaian.

Ekstrak seluruh ZIP terverifikasi ke folder baru di bawah Program Files, lalu
buka Install-VanGuard.bat. Python3.13.17/WireGuard1.1.1 dan wheel sudah disertakan;
runtime valid yang sudah ada dipertahankan. Tidak perlu Git, WSL, unduhan pip,
path Python manual atau thumbprint yang diketik pengguna. Hash dan publisher
runtime diperiksa sebelum eksekusi. Tetap verifikasi checksum ZIP melalui sumber
proyek yang dipercaya; hash manifest dari paket itu sendiri bukan autentikasi.

Tidak mengubah PATH global/jaringan, membuat key atau menyalakan tunnel saat
install. UAC/signing/policy organisasi tetap dihormati; paket aplikasi unsigned.
Exit0 berhasil,1/2 gagal,1223 UAC batal,3010 restart manual diperlukan. Jalankan
ulang setelah restart; tidak reboot paksa. BAT /nopause untuk runner pengujian.
Preview PowerShell -Preview tidak membuat state/runtime/key. Opsi
-ExpectedManifestSha256 menerima hash yang sudah dikonfirmasi untuk otomasi.

Runtime/config aplikasi terpisah di Program Files; identitas VM lama di
ProgramData tidak dipakai/diubah. Reinstall mempertahankan identitas endpoint.
Uninstall mempertahankan data identitas dan runtime bersama; bukan revocation.
Baca checkpoint repo untuk hasil native yang benar-benar selesai. Pengujian
fisik, ARM64 dan signing distribusi organisasi belum dinyatakan didukung.
