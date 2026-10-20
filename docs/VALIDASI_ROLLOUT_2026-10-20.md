# Rollout dan validasi VanGuard 0.1.9 — 20 Oktober 2026

Status pekerjaan: **IN_PROGRESS — pengujian Windows lanjutan**. Bukti privat berada
pada `state/deployment/hardening-20261019-2316/` dan
`state/deployment/hardening-20261020/`. Credential hanya di inventaris privat host.

## Paket dan pemulihan

Kelima Ubuntu serta Windows sudah memakai0.1.9. Wheel SHA256:
`e60f30d0294ae999aaec0817a56921a394fbed943de493a3d3878e3d7089ee9a`.
Kode aplikasi berasal dari42028cf. Commit317722e memperbaiki pemeriksaan arsip;
[CI39380655167](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/39380655167)
lulus. CI42028cf:202 PASS/1 SKIP pada masing-masing Ubuntu3.10/3.12,
28 PASS/2 SKIP helper Windows. Suite overlap tidak dijumlahkan.

Backup Ubuntu dibuat setelah layanan terkait dihentikan: state, konfigurasi,
unit systemd dan venv; server juga konfigurasi WireGuard. Arsip dan SHA diverifikasi.
CA30entri lolos pemeriksaan invariant serta transaksi pada salinan terisolasi.
Upgrade/refresh CRL mempertahankan root/index/serial; tidak merekonstruksi counter.
Windows menyimpan backup ZIP client+venv dengan ACL privat di
`C:\ProgramData\VanGuard\backups\hardening-20261020`; integritas ZIP/hash dan
hash lima berkas identitas utama sebelum/sesudah cocok. Dependensi paket PASS.

Pemulihan harus memakai **state terbaru**: hentikan admission/tunnel, pertahankan
manifest transaksi dan histori pencabutan, lalu pulihkan paket/config yang kompatibel.
Jangan restore index/CRL atau database akses lama dari backup. Jika manifest belum
selesai, gunakan kode transaksi baru untuk menyelesaikannya sebelum downgrade.

Gate aplikasi aktif pada server, default-deny. Rollback firewall saat pemasangan
mengembalikan runtime serta file aturan lama, tidak menghapus firewall seluruhnya.
SSH baru diverifikasi sebelum timer rollback dibatalkan. Grant memerlukan pasangan
identitas+akun dan resource `internal-demo`,10.8.0.1,TCP8082. Perubahan file policy
baru berlaku setelah sinkronisasi daemon; uji menunggu state nft, bukan jeda tetap.

## Matriks bukti aktual

| Pengujian | Ubuntu VM asli | Windows VM asli |
|---|---|---|
| Register/login tanpa peer | PASS | PASS |
| Admission, handshake dan HTTP dengan grant | PASS | PASS |
| Default-deny, LAN server, port lain | PASS | PASS |
| Route tunnel IP langsung melalui LAN | PASS | BELUM_TERUJI ulang |
| Dua renewal otomatis | PASS64,79/64,86detik | PASS67,18/71,73detik |
| TCP aktif terblokir setelah grant dihapus | PASS | BELUM_TERUJI ulang |
| Lease300detik habis tanpa renewal | PASS; pengamatan peer hilang+9,30detik | IN_PROGRESS |
| Sesi kedaluwarsa | PASS; fault deadline pada sesi disposable | BELUM_TERUJI ulang |
| Logout bersamaan renewal/idempotent/scope | PASS | BELUM_TERUJI ulang |
| Logout unreachable mempertahankan token | PASS | IN_PROGRESS |
| CA offline, peer dihapus, readiness503 | PASS | BELUM_TERUJI ulang |
| Stop daemon produksi menutup wg0 | PASS | BELUM_TERUJI ulang |
| SIGSTOP daemon → watchdog → wg0 hilang | PASS, unit produksi | BELUM_TERUJI ulang |
| Reboot client dengan tunnel aktif | PASS, fresh admission berhasil | IN_PROGRESS |
| Cleanup gagal menahan config | PASS; injeksi kegagalan, tunnel nyata | IN_PROGRESS |
| Revoke CA memblokir TCP aktif/readmission | PASS | IN_PROGRESS |
| Penggantian immutable/same akun/IP | PASS, dua key baru dari client | BELUM_TERUJI ulang |
| Akun disabled menghapus peer/menolak admission | PASS | BELUM_TERUJI ulang |

Fault injection sesi mengubah deadline **hanya sesi uji**; berbeda dari menunggu
8jam asli. Injeksi cleanup sengaja menggagalkan fungsi down; recovery menjalankan
backend asli dengan ownership sama dan memastikan tunnel/service hilang sebelum
menghapus config. Ini bukan simulasi semua jenis kegagalan OS.

Healthz/readyz ketiga layanan lewat HTTPS200. Dashboard terautentikasi password/TOTP
menampilkan status terpisah, warning kedaluwarsa dan halaman pertumbuhan penyimpanan.
Arsip WIB/filter/create/download/checksum serta scan seluruh isi ZIP PASS.
Bukti lama tidak dihapus. Sistem tidak memperpanjang sertifikat lewat renewal lease.

## Temuan yang diverifikasi

| Klasifikasi/prioritas | Lokasi dan bukti | Dampak dan kriteria selesai |
|---|---|---|
| Bug terbukti/P2, fixture | prepare_live.py privat: script0600 dijalankan nobody, journal Permission denied dan socket kosong | Hasil HTTP awal tidak sah; diperbaiki0644 pada script tanpa rahasia, loopback200 serta seluruh HTTP ulang PASS |
| Perilaku belum diuji/P2, fixture | Runner sementara KillMode default gagal cleanup, config/interface tertinggal | Penyebab tepat tidak disimpulkan; pulih setelah cocokkan key/address/alias dan lock. Runner mengikuti KillMode=mixed unit produksi; cleanup berikutnya PASS |
| Bug terbukti/P2, pemeriksaan | scripts/verify_activity_archive.py main memindai byte ZIP terkompresi | Secret sintetis tidak ditemukan di kontainer tetapi ada di isi. Perbaikan memeriksa semua anggota ZIP; workflow live PASS |
| Risiko desain/P2 | Penerapan edit resource policy melalui loop daemon, biaya transaksi CA/fsync pada storage host | Tidak instan; verifikasi state nft. Akses tetap dibatasi deadline set. Ukur skala/latensi sebelum beban besar |
| Perilaku belum diuji/P1 | Ketahanan CA pada kehilangan daya disk/host nyata | SIGKILL/manifest dan rollout konsisten bukan bukti power-loss media; perlu lingkungan salinan dan prosedur khusus, bukan mematikan CA utama sembarangan |

Identitas utama tidak direvoke. Kedua identitas Linux disposable sudah direvoke,
akun dinonaktifkan dan slot eksperimen.3 dibebaskan sebelum pengujian Windows.
Lima Ubuntu dan satu Windows dipertahankan; kernel/handshake WireGuard tidak diubah.
