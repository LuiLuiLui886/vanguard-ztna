# Kandidat offline VanGuard Windows endpoint

**Belum release. Belum diuji pada Windows native/PC/laptop fisik.** Tidak signed.
Paket ini tidak memasang Python/WireGuard secara otomatis. Target build hanya
Windows 11 x64, Windows PowerShell 5.1, CPython 3.13 x64 dengan pip/venv, dan
WireGuard resmi yang sudah dipasang administrator. Validasi ACL/UAC/GUI pada
Windows asli masih diperlukan. Tidak memerlukan Git/WSL/Git Bash di endpoint.

1. Operator memeriksa manifest/hash dari jalur tepercaya dan asal wheelhouse.
   Hash paket melindungi integritas, bukan bukti autentisitas publisher. Gunakan
   signing organisasi bila kebijakan eksekusi memerlukannya; jangan bypass policy,
   SmartScreen atau Defender. Paket/runtime unsigned tidak dinyatakan siap sebar.
2. Salin paket ke direktori admin-only (contoh di bawah Program Files). Skrip
   menolak path yang writable akun biasa atau melewati junction/reparse point.
   Jangan langsung mengeksekusi paket dari Downloads secara elevated.
3. Buka Install-VanGuard.bat, setujui UAC; masukkan SHA256 manifest dari operator
   dan path python.exe 3.13 x64 yang terpercaya. WireGuard harus mempunyai
   signature valid serta thumbprint signer yang dikonfirmasi admin melalui jalur
   tepercaya. UAC batal menghasilkan1223; kesalahan1; berhasil0. Tidak ada
   reboot paksa/download/network provisioning. Preview tersedia lewat
   `powershell.exe -NoProfile -File Install-VanGuard.ps1 -Preview`.
4. Runtime berada di `%ProgramFiles%\VanGuardEndpoint\releases`, sedangkan
   config/identity/log berada di `%ProgramFiles%\VanGuardEndpointData`, ACL hanya
   SYSTEM/Administrators. Tidak memakai folder identitas VM yang sudah ada.
5. Buka PowerShell Administrator. Jalankan launcher dari Program Files dengan
   `-Action configure`, lalu `status`, `init`, `import-bundle`, `login`, `connect`.
   Configure meminta profil/root dari administrator dan konfirmasi fingerprint
   root serta public key WG melalui jalur terpisah. Sumber profil/root juga harus
   disiapkan di direktori admin-only; config lama tidak ditimpa.
   Init meminta ID/IP yang dialokasikan admin dan membuat key di endpoint.
   Kirim hanya request.json; binding/enrollment diselesaikan admin melalui HTTPS.
6. Connect menolak overlap interface LAN dengan subnet backend/tunnel serta route
   tunnel milik VPN lain sebelum admission. Pemeriksaan snapshot ini tidak
   membuktikan router/firewall sudah benar. Connect harus tetap hidup untuk
   renewal. Ctrl+C pada terminal pemilik atau
   `-Action disconnect` dari terminal lain meminta cleanup secara terkontrol.
   Disconnect tidak mencabut sesi server. `-Action logout` mencabut token/challenge/
   lease terkait pada server; kegagalan kontak server tidak boleh dianggap sukses.
   Tidak ada password/token di command-line/log; password melalui prompt tersembunyi.
7. `status` hanya menyatakan file lokal yang tersedia; bukan lease/handshake.
   `diagnose` memeriksa readiness API dengan TLS, tidak membuktikan UDP/akses aplikasi.
8. Install ulang/repair membangun runtime baru, pip offline hash-required/pip check
   dan CLI check sebelum current.json diganti. Runtime lama/interrupted disimpan
   untuk inspeksi, tanpa membuat ulang key. Upgrade ditolak ketika connect/service
   masih ada; mutex dipakai bersama launcher. Config parsial atau marker ownership
   yang tidak cocok memerlukan inspeksi operator, bukan dihapus otomatis.
9. Uninstall-VanGuard.ps1 memerlukan admin, lock bebas dan service benar-benar
   tidak ada(1060). Hanya binary milik instalasi dihapus; data/config/key, Python
   dan WireGuard bersama dipertahankan. Tidak ada pilihan purge otomatis.
   Decommission harus mencabut identitas/grant di server terlebih dahulu.

Paket hanya menggunakan wheel yang disertakan dan dipin. Tidak diam-diam mengakses
internet. Prasyarat tidak tersedia/versi tidak cocok merupakan blocker; dapatkan
installer resmi melalui operator dan verifikasi publisher/hash sebelum tahap ini.
Fitur bootstrap runtime otomatis, shortcut GUI, signing organisasi, repair state
parsial otomatis dan dukungan ARM64 BELUM_TERSEDIA. Semua skenario fresh/reinstall/
upgrade/repair/uninstall/UAC/path khusus/ACL/reboot Windows BELUM_DIJALANKAN.

Panduan pilot lengkap ada di docs/ENDPOINT_WINDOWS_PILOT.md pada source. Jangan
menjalankan deploy/windows/bootstrap.ps1: script itu mengubah jaringan/SSH VM.
