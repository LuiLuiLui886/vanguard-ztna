# Validasi installer EXE offline — 29 Oktober 2026

Branch kerja `feature/2026-10-22-physical-endpoints`, basis `1983cd4`.
Wrapper baru membungkus paket0.1.14-fix1; wheel aplikasi tetap0.1.14.
Manual tunggal: [Bab14.0.1](MODUL_PENGGUNAAN_VANGUARD.md).

## Cakupan dan implementasi

- `deploy/endpoint/exe/VanGuardSetup.cs`: resource ZIP embedded, manifest UAC,
  batas ukuran/path, SHA256, ACL/owner, cache privat, mutex, launcher BAT dan
  penerusan exit code. Payload diverifikasi sebelum ekstraksi; isi cache
  diverifikasi sebelum setiap eksekusi. Bukti rusak/parsial tidak dihapus.
- `deploy/endpoint/exe/Build-Exe.ps1` dan `app.manifest`: build native dengan
  compiler .NET Framework Windows x64, input manifest lengkap, allowlist file,
  public provisioning all-or-none, metadata build dan output tanpa overwrite.
- Paket umum memanggil Install-VanGuard.bat. Paket per-device memanggil
  Setup-VanGuard.bat; key tetap dibuat di client dan approval/login wajib.
  Instalasi/ekstraksi bukan admission, tidak menambahkan peer.
- Tidak mengubah CA, kernel/protokol WireGuard, firewall atau backend. Tidak
  menyertakan kredensial, fixture profile atau private key dalam artefak publik.

## Temuan dan batas penyelesaian

| Kelas | File/fungsi dan bukti | Dampak/prioritas | Kriteria selesai/status |
|---|---|---|---|
| Fitur sebelumnya belum tersedia | Downloads1983cd4 hanya ZIP/BAT; wrapper dan builder ditambahkan | P2 kemudahan distribusi | Binary native, ekstraksi terverifikasi dan installer nyata diuji; hasil di bawah |
| Risiko desain | EXE unsigned; Get-AuthenticodeSignature bukan bukti penerbit tepercaya | P2 asal paket/SmartScreen | Konfirmasi origin+SHA256 wajib; signing produksi belum tersedia |
| Risiko desain | OfflinePackage.Extract mempublikasikan folder lewat rename | P2 interupsi/power-loss | Resume memeriksa ulang seluruh cache, reject/preserve jika rusak; durability listrik mati belum dibuktikan |
| Perilaku belum diuji | Main→UAC browser/klik langsung, OS fresh, reboot3010, Windows11/PC fisik | P2 batas dukungan wrapper | Uji native terpisah; BELUM_TERUJI, jangan memakai bukti BAT sebagai bukti EXE |

Tidak ditemukan bug produk terkonfirmasi pada kasus EXE yang lulus. Ini bukan
jaminan tidak ada bug atau bukti semua jalur Windows telah diuji.

## Pengujian

Lingkungan Windows10 Enterprise LTSC build19044, x64, .NET Framework4.8;
Python3.13.17/WireGuard1.1.1 sudah tersedia. Proses elevated lewat SSH/SYSTEM,
bukan interaksi UAC desktop. VM lain tidak diubah/dinyalakan untuk pengujian ini.

| Pengujian | Bukti aktual |
|---|---|
| `OfflinePackageTests.cs` | 13PASS native: payload sintetis pada ACL/filesystem Windows nyata, valid/resume, hash salah, traversal/absolute/backslash, case collision, reserved name, anggota asing, symlink, manifest salah, hash file salah, cache tamper retained, ACL Users-writable ditolak |
| `exe_bootstrap.ps1`, build r1 | 6PASS native EXE: PE manifest requireAdministrator, ekstraksi embedded, resume tanpa rewrite, byte payload dimodifikasi ditolak, opsi asing ditolak, tidak membuat tunnel |
| `exe_install.ps1` | Installer EXE asli selesai exit0, venv offline0.1.14 terpasang; observer terinterupsi shutdown guest sebelum laporan akhir, tetap dicatat INTERRUPTED |
| `exe_postflight.ps1` | 6PASS native setelah boot: metadata/script cocok, pip check/clienthelp, primary config/key cocok backup, release lama retained, device EXE exit20 dan resume menjaga hash, tidak ada tunnel/policy |
| EXE final dengan manual terbaru | Build native exit0,6PASS bootstrap berurutan; Authenticode NotSigned. Percobaan awal saat installer lain aktif ditolak oleh mutex, log FAIL dipertahankan |
| `tests/test_endpoint_package.py` | Linux lokal6PASS0,08detik; bukan pengujian Windows |

Bukti lokal `state/exe-20261029/`, staging Windows privat
`C:\Program Files\VanGuardExeBuild`. Build device menggunakan fixture schema1
`C:\Program Files\VGRT-00ad1962`; EXE fixture tidak didistribusikan.
Backup sebelum pemasangan nyata menyimpan config/identity/tools/metadata/script;
release lama dipertahankan. Pengambilan status PowerShell sempat timeout, sementara
SSH cmd responsif. Timeout observasi tidak dihitung sebagai PASS/FAIL installer. Event1074 mencatat
shutdown oleh wlms.exe dan restart oleh TrustedInstaller.exe; ini bukan kode3010
installer dan bukan klaim pengujian reboot3010. Aktivasi/update tidak diubah.
Postflight diulang setelah boot, hasil diambil dari JSON aktual. Task uji sudah
dihapus, tidak ada proses EXE build aktif, service tunnel1060, marker lockdown
tidak ada. ACL Users-writable fixture dikembalikan; isi/bukti dipertahankan.

## Artefak kandidat

`downloads/Setup-VanGuard-0.1.14-fix1.exe`, SHA256:
`f74a3b7b72373dbe55c1cc5b771938108cc683e930949c861cea7422415c7f69`.
Ukuran44.718.592byte; hash unduhan cocok dengan binary native. ZIP embedded:
CRC,39anggota, seluruh hash manifest dan byte payload lokal PASS.
Mode template, tanpa profil/alokasi perangkat. Manual terbaru disertakan; seluruh
script, wheel dan runtime identik r1. Template ZIP fix1 sebelumnya dan stable0.1.12
retained. Main tidak diubah. Hasil publikasi dicatat di jurnal/checkpoint setelah push.

## Pemulihan dan sisa

Jika instalasi gagal, pertahankan config/key dan log; jangan memulihkan CA atau
menghapus konfigurasi tunnel. Periksa service/ownership/policy dahulu, lalu
jalankan repair terverifikasi sesuai manual. Cache EXE yang ditolak perlu
inspeksi/archive admin; tidak ada penghapusan bukti otomatis. Output build lama
serta folder pending disimpan. Uji EXE bukan pengulangan matriks admission,
revocation, Internet terkelola atau readiness layanan.

Host sempat tersisa414MiB disk; VM di-pause sementara. Empat fragmen unduhan ISO
publik dipindah ke partisi lokal lain dengan SHA256 terverifikasi, fsync dan
symlink path lama; tidak ada backup/ISO lengkap/disk VM yang dibuang. Ruang host
pulih4,3GiB, kemudian VM di-resume. Manifest relokasi hanya lokal. Windows10
running, enam VM lain shut off pada akhir pemeriksaan.

BELUM_TERUJI: interaksi UAC/SmartScreen, Windows11 wrapper, mesin fresh tanpa
runtime, kode3010 nyata lewat EXE, login interaktif penuh, perangkat fisik,
concurrent termination/power-loss, dan signing organisasi. Bukti BAT/native
sebelumnya tetap historis dan terpisah. Tidak mengklaim CI baru.
