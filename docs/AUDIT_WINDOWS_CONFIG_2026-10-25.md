# Audit pemulihan konfigurasi Windows — 25 Oktober 2026

Audit ini melanjutkan pemeriksaan bug setelah baseline `eb54320`. Fokusnya adalah
pemulihan konfigurasi endpoint ketika proses terputus, bukan klaim seluruh sistem
bebas bug. Manual operasional tetap satu: [Manual admin](MODUL_PENGGUNAAN_VANGUARD.md),
Bab 10–12. Laporan ini menyimpan bukti teknis, bukan tutorial tambahan.

## Temuan dan keputusan

| ID / klasifikasi | File atau fungsi | Bukti dan dampak | Prioritas / kriteria selesai |
| --- | --- | --- | --- |
| WIN-CONFIG-01 — **BUG_TERBUKTI**, diperbaiki | `deploy/endpoint/windows/VanGuard.ps1`, aksi `configure`; fungsi baru `Install-TrustedProfile` di `Common.ps1` | Windows 10 LTSC build 19044: injeksi kegagalan copy profil setelah root tersalin menghasilkan exit 1, root ada/profil tidak ada. Retry tanpa fault tetap exit 1; onboarding macet. | P2: retry pasangan yang identik menyelesaikan state parsial; input berbeda tidak menimpa trust; validasi mendahului publikasi. Uji native memenuhi kriteria. |
| WIN-CONFIG-STATUS — **BUG_TERBUKTI**, diperbaiki bersama WIN-CONFIG-01 | `VanGuard.ps1`, aksi `status` | State root saja sebelumnya diperlakukan seperti instalasi baru. Setelah perbaikan, pemeriksaan fixture parsial exit 1 dengan penjelasan dan instruksi retry. | P2: keadaan parsial tidak dilaporkan sebagai instalasi kosong yang normal. |
| Dua file konfigurasi tidak membentuk satu transaksi — **RISIKO_DESAIN** | `Common.ps1::Install-TrustedProfile` | Rename root dan profil tetap dua operasi. Uji pemulihan kedua bentuk parsial lulus; ini tidak membuktikan ketahanan terhadap kehilangan daya/storage. Snapshot publik yang gagal dipertahankan untuk inspeksi. | P2: fail-closed dan retry aman dipenuhi; power-loss serta configure serentak tetap BELUM_TERUJI. Jangan menganggap atomic rename sebagai transaksi seluruh state. |
| UAC interaktif, MOTW/GPO, Windows 10 Home/Pro build 19045 dan koneksi VPN Windows 10 — **PERILAKU_BELUM_DIUJI** | Installer/launcher dan client Windows | Uji di bawah menggunakan SSH administratif dan Windows PowerShell native. Tidak mewakili klik pengguna biasa, kebijakan organisasi, ataupun semua edisi Windows 10. | P2: uji native terpisah dengan bukti hasil dan cleanup sebelum menyatakan didukung penuh. |

Tidak ada fitur tambahan yang dinyatakan selesai di luar perubahan konfigurasi
ini. Temuan terbuka CA power-loss/soak dan WIN-CLEANUP-02 pada checkpoint tetap
berlaku. CA utama, sertifikat, registry binding, autentikasi karyawan, enam
pemeriksaan admission dan kernel WireGuard tidak diubah.

## Perbaikan

Input publik disalin ke staging dengan ACL administrator/SYSTEM. Fingerprint
admin, key WireGuard server dan validasi profil/sertifikat Python diperiksa pada
salinan tersebut. Kedua target diperiksa sebelum publikasi: file berbeda ditolak,
file identik dipertahankan, dan file yang belum ada dipindahkan tanpa overwrite.
Retry dengan pasangan yang sama menyelesaikan state parsial. Staging gagal tidak
dihapus otomatis; staging sukses dibersihkan hanya untuk file milik operasi itu.

Status root tanpa profil sekarang menjelaskan konfigurasi tidak lengkap dan
mengembalikan exit 1. Manual Bab 11.1 menjelaskan retry serta larangan mengganti
root untuk mengatasi konflik. Tidak ada private key yang dibuat oleh konfigurasi.

## Bukti aktual

| Lingkungan | Hasil | Batas bukti |
| --- | --- | --- |
| Linux lokal, sebelum patch | 41 PASS / 1 SKIP, 0,263 detik | Helper Python/builder; bukan PowerShell atau VM |
| Linux lokal, setelah patch | 41 PASS / 1 SKIP, 0,453 detik; resume 0,29 detik | `test_client_platform`, `test_endpoint_package`, `test_realworld_kit` |
| VM Windows 10 LTSC Evaluation x64 build 19044, fixture source | 10 PASS; status parsial exit 1; dua retry launcher exit 0 | Filesystem dan validasi crypto nyata; input prompt/runtime lookup dan kegagalan copy diinjeksi untuk isolasi |
| VM Windows 10, ZIP fix1 melalui BAT | Reinstall exit 0, status exit 0; 10 PASS menggunakan Common.ps1 terpasang | Konfigurasi lama hash-identik, release baru, launcher identik ZIP, tidak membuat identitas atau tunnel |
| Paket fix1 | Manifest, runtime pins, 20 wheel, 25 file aplikasi, scan credential nested PASS | Integritas paket, bukan keberhasilan VPN |
| VM Windows 11 build 26300, fix1 | SEDANG_DIUJI | Hasil r3 sebelumnya tidak dianggap bukti fix1 |
| CI source fix1 | BELUM_SELESAI | Akan diperbarui setelah run aktual |

Sepuluh regresi native: pasangan baru valid; retry tanpa overwrite; pemulihan
root saja; pemulihan profil saja; penolakan root berbeda; penolakan profil berbeda;
fingerprint admin salah; public key server salah; sertifikat rusak; fingerprint
hex huruf besar. Kasus konflik memastikan file pasangan belum dipublikasikan dan
file lama tidak diubah. Sertifikat disposable dibuat di memory; private key tidak
ditulis. Runner `tests/windows/installer_configure.ps1` juga ditambahkan ke CI
Windows; CI Windows Server harus dibedakan dari Windows 10/11 desktop native.

ZIP yang diuji dan akan diterbitkan memakai nama tunggal di `downloads/`:
`vanguard-windows10-11-offline-0.1.12-20261025.zip`, **44.675.510 byte**, SHA256
`26ba30082b2c21da3a0d81d9670f5ae7e2eb5157cca566b662fbafb2d1790515`.
Paket lama r3 dipertahankan dalam histori Git serta state lokal. Versi aplikasi
Python tetap 0.1.12; perbaikan ini berada pada launcher PowerShell dan manual.

Bukti mentah hanya lokal di `state/bug-review-20261025/`, termasuk
`configure-before-fix-confirmed.json`, `configure-after-fix.json`,
`configure-regression-native10.json`, `package-native10.json`,
`package-configure-native10.json`, dan JUnit regresi. Backup sebelum reinstall
Windows 10 berada pada direktori guest terlindungi
`C:\Program Files\VanGuard Configure Package Fix1\before.zip`.
Tidak ada password di laporan, paket, atau Git. Invokasi tes dengan nama file
salah sempat menghasilkan no-tests/exit 4; invokasi dikoreksi dan hasil aktual di
atas digunakan. Bukti percobaan awal yang tidak selesai tetap dipertahankan.
