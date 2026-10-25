# Validasi installer Windows10/11 dan manual tunggal — 25 Oktober 2026

Status: **SELESAI untuk pengujian installer dalam lingkup di bawah**.
Laporan ini mencatat bukti; langkah penggunaan hanya ada
pada [manual admin tunggal](MODUL_PENGGUNAAN_VANGUARD.md).

## Audit singkat dan ruang lingkup

| Klasifikasi/prioritas | File/fungsi dan bukti | Dampak dan kriteria selesai |
|---|---|---|
| Fitur belum tersedia/P1 | Gate `Install-VanGuard.ps1` sebelumnya hanya menerima Windows11; kini memakai `Platform.Assert-SupportedWindows` | Windows10 x64 build19044/19045 diterima; server/x86/ARM64/build lama ditolak; bukti native per build wajib |
| Bug terbukti/P2 | `build_endpoint_package.build`: README source memakai tautan relatif repository yang tidak tersedia dalam hasil ekstraksi | README paket harus menunjuk HTML lokal; paket lengkap diverifikasi dengan manifest dan pemeriksaan tautan |
| Risiko desain/P2 | Banyak tutorial/ZIP historis berada dalam tree aktif | Satu manual Markdown sebagai sumber, HTML hasil render;14tutorial dan3ZIP lama dikeluarkan dari tree aktif, histori Git dipertahankan |
| Perilaku belum diuji/P1 | UAC interaktif, MOTW/GPO/browser, endpoint fisik dan Windows10 Home/Pro22H2 | Harus diuji pada lingkungan tersebut; hasil LTSC19044/transfer SSH tidak dipindahkan sebagai klaim lulus |

Tidak mengubah CA, registry, token/sesi, admission atau WireGuard. Enam domain asli
terjaga; Windows10 memakai VM/disk/MAC/IP baru sebagai node uji ketujuh. Private key
endpoint tetap dibuat client; installer tidak membuat identitas atau tunnel.

## Paket dan dokumentasi

Paket final r3: `downloads/vanguard-windows10-11-offline-0.1.12-20261025.zip`,
44.674.789byte, SHA256:
`d0b724f09b82a1684ee80cda09cb7ed86e35b4761675c6a7593fa6fcf7a7ee6f`.
36anggota termasuk manifest,20wheel, Python3.13.17 dan WireGuard1.1.1.
Scan isi ZIP/wheel terhadap inventaris rahasia dan private-key PEM PASS;25file
aplikasi cocok source. Dibanding r1, hanya manual/README/manifest berubah.

Manual18bab memuat instalasi host/Ubuntu, CA rinci13subbagian, token/admin/TOTP,
firewall, profil/trust, installer Windows, CSR/registrasi, pemakaian endpoint,
resource default-deny, audit, backup/pemulihan dan troubleshooting. Validasi
51blok Bash,69tautan HTML, seluruh tautan file Markdown tracked dan credential
scan PASS. HTML dalam ZIP berasal dari sumber manual yang sama.

## Lingkungan dan bukti

- Windows10 Enterprise LTSC2021 Evaluation x64 build19044, Secure Boot/TPM aktif.
  ISO resmi Microsoft diverifikasi dengan PDF hash resmi sebelum instalasi.
  Pengaturan wilayah/keyboard OOBE diselesaikan melalui console setelah interupsi.
  SSH key-only terverifikasi; autologon/password registry/unattend sudah dihapus.
  Edition evaluasi dipakai untuk pengujian, bukan lisensi deployment produksi.
- Sebelum BAT: Python, WireGuard dan endpoint belum ada, dibuktikan `before.json`.
- Linux lokal full24Oktober TERPUTUS tanpa hasil akhir; run25Oktober
  **268PASS/1SKIP795,98s**, JUnit aktual disimpan. Skip memerlukan ACL Windows asli.
- CI40074650339 source29b7afb SUCCESS: Linux3.10 **268PASS/1SKIP291,604s**,
  Linux3.12 **268PASS/1SKIP282,233s**; Windows Server2022 helpers
  **28PASS/2SKIP0,489s** dan9kasus platform sintetis. Ini bukan uji installer VM.
- Linux lokal regresi builder kit/package25Oktober: **12PASS0,19s**; Ruff PASS.

## Hasil Windows10 native

| Pemeriksaan | Hasil aktual |
|---|---|
| Fresh install dengan Python/WireGuard absent | PASS; Python3.13.17/WireGuard1.1.1/VanGuard0.1.12 |
| Smoke9kasus |9PASS: preview, fresh BAT, status, tidak membuat identity/tunnel, reinstall, setup terputus ditolak, repair, uninstall preserve, reinstall setelah uninstall |
| Guard5kasus |5PASS: SID ACL Program Files, path writable ditolak, junction ditolak, publisher salah ditolak, runtime rusak ditolak sebelum eksekusi |
| Policy default/Restricted | PASS: exit0/exit1, policy persisten tidak berubah |
| ZIP final r3 | PASS: BAT0/status0, release baru, config tetap, tanpa identity/tunnel |

Wrapper otomatis pertama berhenti saat kasus Restricted dan tidak menghasilkan
policy/final report. Pengulangan **hanya uji policy**, memakai proses terpisah
untuk stdout/stderr, selesai exit0 dengan laporan PASS. Log awal disimpan; tidak
mengulang fresh install atau menganggap run awal selesai. Penyebab internal
wrapper PowerShell tidak direproduksi terpisah dan tidak diklaim bug installer.
Field generik `missing_runtime_install` pada runner smoke tetap BELUM_DIJALANKAN;
bukti runtime absent→installed berasal dari `before.json`, versi aktual dan
laporan wrapper final, bukan dari field tersebut.

Media ISO/seed dikeluarkan setelah tes. Tidak ada credential/key dipublikasikan.
## Hasil Windows11 native ZIP final r3

Windows11 Enterprise Evaluation x64 build26300: **4PASS** (preview tanpa
mengubah pointer, reinstall dua kali dengan config tetap dan release baru,
status/tanpa identity/tunnel), **5guard PASS**, policy default0/Restricted1 dan
persistent unchanged PASS. Runtime bersama Python3.13.16/WireGuard1.1.1 dipakai
kembali; legacy client0.1.9 dan6hash file identitas utama tidak berubah. Secure
Boot/TPM aktif; enam definisi VM asli hash-identik. Backup pointer/script/data/
identitas dibuat dan diperiksa sebelum mutasi. Instalasi endpoint0.1.12 yang
sudah ada dipertahankan, tidak dihapus untuk memaksakan fresh-test.

Peluncuran wrapper SSH pertama tanpa Wait berakhir sebelum started marker
terbentuk. Dengan sesi SSH dipertahankan dan Wait, runner selesai exit0 dan
laporan diambil dari guest. Ini bukan kegagalan BAT. Bukti Windows11 fresh
runtime absent, uninstall/reinstall paket sebelumnya tetap terpisah pada
[laporan24Oktober](VALIDASI_INSTALLER_2026-10-24.md); tidak diklaim diulang pada r3.

Akhir tes: Windows11 running, Windows10 dan lima Ubuntu shut off. Tidak ada
runner native atau tunnel uji aktif. Media setup Windows10 sudah kosong; backup
dan seed privat tetap disimpan. Password tidak berubah.

**BELUM_TERUJI:** Windows10 Home/Pro22H2/build19045 native, VPN Windows10,
UAC interaktif/cancel, MOTW/GPO/browser dan endpoint fisik. Hasil LTSC19044 tidak
membuktikan semua edisi Windows10. Skenario VPN Windows11 terdahulu bukan hasil
VPN Windows10 atau PC fisik.
Tidak menjumlahkan suite yang overlap. Semua log/backup/credential tetap lokal
pada `state/manual-win10-20261024/` dan inventaris privat di luar repository.
