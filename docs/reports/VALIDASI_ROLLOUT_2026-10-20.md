# Rollout dan validasi VanGuard 0.1.9 — 20 Oktober 2026

Status pekerjaan: **rollout dan matriks lifecycle VM selesai; risiko tersisa dicatat**.
Bukti privat berada
pada `state/deployment/hardening-20261019-2316/` dan
`state/deployment/hardening-20261020/`. Credential hanya di inventaris privat host.

## Paket dan pemulihan

Kelima Ubuntu serta Windows sudah memakai0.1.9. Wheel SHA256:
`e60f30d0294ae999aaec0817a56921a394fbed943de493a3d3878e3d7089ee9a`.
Kode aplikasi berasal dari42028cf. Commit0695e03 menambahkan regresi pemeriksaan
arsip; [CI39382689148](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/39382689148)
lulus:205 PASS/1 SKIP pada masing-masing Ubuntu3.10/3.12,28 PASS/2 SKIP helper
Windows. Tiga regresi arsip lokal juga PASS0,07detik. Suite overlap tidak dijumlahkan.

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
| Route tunnel IP langsung melalui LAN | PASS | PASS; route uji dipulihkan, HTTP tunnel kembali200 |
| Dua renewal otomatis | PASS64,79/64,86detik | PASS67,18/71,73detik |
| TCP aktif terblokir setelah grant dihapus | PASS | PASS; peer tetap terpasang, grant dipulihkan dan HTTP kembali200 |
| Lease300detik habis tanpa renewal | PASS; pengamatan peer hilang+9,30detik | PASS; pengamatan+16,52detik |
| Sesi kedaluwarsa | PASS; fault deadline pada sesi disposable | PASS; fault deadline pada sesi disposable |
| Logout bersamaan renewal/idempotent/scope | PASS | PASS; retry sesi lama mempertahankan lease sesi baru |
| Logout unreachable mempertahankan token | PASS | PASS; logout live juga memutus akses |
| CA offline, peer dihapus, readiness503 | PASS | PASS peer/HTTP dan pemulihan; readiness diukur pada Linux |
| Stop daemon produksi menutup wg0 | PASS | PASS |
| SIGSTOP daemon → watchdog → wg0 hilang | PASS, unit produksi | PASS, unit produksi |
| Reboot client dengan tunnel aktif | PASS, fresh admission berhasil | PASS; service Stopped/Manual, recovery lalu fresh admission berhasil |
| Cleanup gagal menahan config | PASS; injeksi kegagalan, tunnel nyata | PASS; recovery operator setelah timeout service nyata |
| Revoke CA memblokir TCP aktif/readmission | PASS | PASS |
| Penggantian immutable/same akun/IP | PASS, dua key baru dari client | PASS, dua key baru dari Windows |
| Akun disabled menghapus peer/menolak admission | PASS | PASS |

Fault injection sesi mengubah deadline **hanya sesi uji**; berbeda dari menunggu
8jam asli. Injeksi cleanup sengaja menggagalkan fungsi down; recovery menjalankan
backend asli dengan ownership sama dan memastikan tunnel/service hilang sebelum
menghapus config. Ini bukan simulasi semua jenis kegagalan OS.

Healthz ketiga layanan lewat HTTPS200. Readiness pernah200 pada ketiganya, tetapi
dua snapshot penutup menunjukkan503 sementara pada CA atau dependensinya.
Diagnosis read-only30sampel:18ready,12BlockingIOError saat mengambil shared lock;
tidak ditemukan kegagalan invariant/CRL pada sampel itu. Bukti503 dipertahankan;
ini bukan bukti readiness selalu stabil. Dashboard terautentikasi password/TOTP
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
| Risiko desain/P2, WIN-CLEANUP-02 | vanguard/windows.py WindowsTunnel.down; interupsi segera setelah up meninggalkan service RUNNING/Disabled melewati timeout | Config ditahan dan logout mencabut akses; operator memverifikasi path/lock, stop, uninstall1060 sebelum menghapus config. Penyebab OS belum pasti. Selesai bila reproduksi terkontrol dan recovery otomatis terbukti aman tanpa menghapus milik proses lain |
| Risiko desain/P2, HEALTH-LOCK-01 | vanguard/health.py probe/ca_state memakai LOCK_SH\|LOCK_NB;30sampel menghasilkan18ready dan12BlockingIOError pada lock, bukan invariant/CRL | Readiness503 saat transaksi eksklusif berlangsung dapat merambat ke server/admin. Ukur durasi transaksi dan rancang retry terbatas dalam keseluruhan deadline; selesai bila contention singkat ditangani, contention panjang tetap unknown, read-only dan timeout keseluruhan tetap teruji |
| Perilaku belum diuji/P1 | Ketahanan CA pada kehilangan daya disk/host nyata | SIGKILL/manifest dan rollout konsisten bukan bukti power-loss media; perlu lingkungan salinan dan prosedur khusus, bukan mematikan CA utama sembarangan |

Identitas utama tidak direvoke. Kedua identitas Linux disposable sudah direvoke,
akun dinonaktifkan dan slot eksperimen.3 dibebaskan sebelum pengujian Windows.
Kedua identitas Windows disposable juga sudah direvoke dan akunnya dinonaktifkan;
task pengujian dihapus setelah cleanup tunnel terkonfirmasi. Grant kembali kosong.
Lima Ubuntu dan satu Windows dipertahankan; kernel/handshake WireGuard tidak diubah.

Pemeriksaan akhir: invariant CA PASS, enam XML sama dengan backup,13file
identitas/config CA/server/admin dan5file identitas utama Windows cocok.
Windows0.1.9/pip check, Secure Boot/TPM PASS; task/service/config aktif uji absen.
Demo sementara dihentikan dan listener8082 hilang. CA/server/admin/Windows
running; client Ubuntu dan attacker shut off untuk membatasi penggunaan RAM.
Tidak ada aplikasi bisnis permanen atau grant baru yang ditinggalkan oleh tes.
