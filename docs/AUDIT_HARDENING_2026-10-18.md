# Audit ketahanan VanGuard — 18 Oktober 2026

Audit dimulai pada c454c0c dengan working tree bersih. Branch kerja
`hardening/2026-10-18-resilience`. Baseline Linux berjalan terpisah; angka review
lama bukan bukti VM. Pemeriksaan libvirt: enam domain ada, semuanya shut off.

| ID / klasifikasi | File/fungsi dan bukti | Dampak / prioritas | Kriteria selesai |
|---|---|---|---|
| CA-01 Bug terbukti | ca.Authority.issue; SIGKILL sesudah OpenSSL signing sebelum cache, retry menghasilkan dua baris index untuk CSR sama. tests/test_ca_durability.py gagal pada source awal | Issuance orphan dan retry tidak konsisten; P1 | Satu transaksi state dan cache, recovery maju idempotent, uji kill sebelum/saat/sesudah commit |
| CA-02 Bug terbukti | ca.Authority.crl menerima serial kosong; uji counter serial gagal karena tidak ditolak | State CA tidak konsisten tetap melayani sebagian operasi; P1 | Validasi relasi index/serial/arsip/CRL sebelum mutasi; rusak ditolak tanpa menebak atau rollback |
| CA-03 Risiko desain | OpenSSL mengubah beberapa file, _crl hanya rename crl.pem; tidak ada fsync maupun journal lintas file | Shutdown dapat menghasilkan sebagian state; P1 | Staging terisolasi, durable commit intent dan roll-forward seluruh manifest; uji interupsi; power-loss disk tetap pengujian berbeda |
| LC-01 Risiko desain | LinuxTunnel.preflight kosong; connect finally memanggil down walau up gagal | Dapat mengganggu interface wg0 yang bukan milik proses; P1 | Preflight menolak interface existing/unknown, kepemilikan dibuktikan saat cleanup; config dipertahankan jika tidak pasti |
| LC-02 Risiko desain | daemon_main sleep/reconcile, unit tanpa watchdog | Hang menunda penghapusan peer expired; P1 | Supervisor watchdog dengan heartbeat hanya setelah reconcile selesai; pengujian systemd/VM terpisah |
| LO-01 Fitur belum tersedia | API/Employees/client hanya login, tidak ada logout karyawan | Token tetap berlaku hingga expiry/disable; P1 | Logout scoped, idempotent, challenge/lease dicabut, race renewal dan retry failure diuji |
| ST-01 Risiko desain | Admission.listing dan dashboard menyebut peer.live Aktif; hanya keberadaan peer | Menyamakan peer dengan lease/handshake/transfer; P2 | Status terpisah, kegagalan unknown, tidak mengklaim koneksi dari peer saja |
| ST-02 Fitur belum tersedia | /healthz liveness saja | Dependency rusak tampak hidup; P2 | /readyz bounded read-only tanpa issuance, peer tambahan atau rahasia |
| CE-01 Fitur belum tersedia | certificate_summary hanya valid/expired; binding immutable sudah ada | Warning dan replacement terpandu belum ada; P2 | Warning expiry, workflow identitas baru mempertahankan histori/binding lama |
| RP-01 Fitur belum tersedia | firewall hanya ICMP tunnel, belum ada resource aplikasi | Akses aplikasi/port dan TCP revoke belum dibuktikan; P2 | Policy eksplisit default deny, pengujian LAN bypass dan TCP aktif |
| AU-01 Fitur belum tersedia | audit SQLite lokal tanpa metrik ukuran/retensi | Pertumbuhan storage tidak dipantau; P2 | Ukuran/ambang aman, kejadian penting tanpa secret, tidak purge histori otomatis |
| VM-01 Perilaku belum diuji | Bukti Windows lama satu renewal; lease expiry IN_PROGRESS, reboot aktif/revocation belum lengkap | Batas klaim operasional; P1 | Bukti baru Ubuntu/Windows native/VM, repeated renewal, cleanup failure, expiry/revoke/reboot; selain yang dijalankan BELUM_TERUJI |

Reproduksi awal CA: 2 FAIL, 1 PASS; log privat
`state/hardening/2026-10-18/ca-before.log`. Ini OpenSSL nyata pada direktori sementara,
bukan perubahan CA utama. Penyebab counter kosong pada power-loss host historis
belum direproduksi; jangan menyamakan SIGKILL proses dengan kehilangan daya disk.

## Intent perbaikan CA

Mutasi OpenSSL dilakukan pada salinan state privat terisolasi di bawah lock CA.
Hanya setelah operasi lengkap dan semua file disinkronkan, manifest commit durable
ditulis. Publikasi file satu per satu dapat terputus; operasi berikutnya wajib
menyelesaikan manifest yang sama sebelum membaca/mengubah state. Tidak pernah
mengembalikan snapshot lama atau menghitung counter baru berdasarkan tebakan.
Kerusakan tanpa commit intent lengkap ditolak untuk pemeriksaan operator.

## Resolusi kandidat dan batas bukti — 19 Oktober

Semua perubahan di bawah berada pada source 0.1.9; belum berarti rollout VM.
Baseline baru 163 PASS/1 SKIP Linux, regresi 18 Oktober 198 PASS/1 SKIP.
Perubahan review CA/status/logout 19 Oktober: 26 PASS. Bukti asli tetap privat
pada state/hardening/{2026-10-18,2026-10-19}/. Tidak ada pemulihan counter utama.

| ID | Implementasi / verifikasi nyata | Status kriteria selesai dan sisa |
|---|---|---|
| CA-01/02/03 | ca.py transaction/check_state dan ca_storage.Publication; OpenSSL nyata, SIGKILL setelah signing dan sembilan kombinasi issue/revoke/CRL × batas publikasi; root key/revocation dipertahankan | Perbaikan source teruji; power-loss filesystem, kapasitas/latensi arsip besar dan rollout CA utama BELUM_TERUJI |
| LC-01 | client.LinuxTunnel memeriksa interface/alias, lock lintas proses; WindowsTunnel menolak cleanup service tidak dimiliki; repeated renewal lima siklus dan kegagalan cleanup mempertahankan config | Regresi command stub/helper lulus; cleanup kegagalan kernel/service nyata masih BELUM_TERUJI pada kandidat |
| LC-02 | daemon heartbeat sesudah reconcile; unit Type=notify/WatchdogSec=90 dan stop hook | Transient systemd pada VM-ATTACKER benar-benar watchdog dan menjalankan hook; hang unit VanGuard produksi beserta penghentian wg0 BELUM_TERUJI |
| LO-01 | Admission.logout_employee + tombstone hash; lock bersama verify; client.logout_employee dan CLI; tests/test_logout.py | Idempotensi, scope sesi, retry kegagalan dan race renewal teruji lokal; logout VPN guest dan jaringan putus BELUM_TERUJI |
| ST-01 | WireGuard.observations/Admission.listing + dashboard; lease memeriksa sesi aktif, peer/handshake/RX/TX terpisah | Regresi status termasuk observasi gagal/expired PASS; tampilan dengan seluruh layanan aktif BELUM_TERUJI |
| ST-02 | health.probe/bounded_readiness dan /readyz semua layanan | Uji CA read-only/counter rusak/deadline/heartbeat boot lain PASS; readiness HTTPS seluruh VM BELUM_TERUJI |
| CE-01 | admin.certificate_summary/register(replaces=...), identity_replacements dan form riwayat | Warning dan penggantian immutable teruji lokal; enrollment pengganti nyata belum dilakukan agar identitas utama tetap utuh |
| RP-01 | resource_policy.NftResources + gate nftables TCP8082 default deny sebelum established; explicit identity/resource/protocol/port | Namespace kernel VM-ATTACKER PASS untuk LAN bypass, port lain, active TCP revoke/expiry. Menggunakan veth bernama wg0, bukan WireGuard; integrasi admission → resource → revoke BELUM_TERUJI |
| AU-01 | operations.storage_summary, /operations, audit logout/replacement, safe upstream errors | Ukuran/growth/snapshot dan histori tidak terhapus teruji lokal; tidak ada purge otomatis. Log systemd/arsip CA tetap perlu pemantauan operator |
| VM-01 | Lima Ubuntu dan Windows tetap ada; tidak mengganti OS/node/identity | Matriks VPN 0.1.9 belum lengkap, tetap terbuka; hasil native dicatat terpisah di checkpoint |

### Temuan tambahan yang diverifikasi ulang

| ID / klasifikasi | File/fungsi dan bukti | Dampak / prioritas | Perbaikan dan kriteria selesai |
|---|---|---|---|
| CA-04 Bug terbukti pada kandidat | ca_storage.prepare menghapus staging tanpa commit saat retry; uji interrupted counter melihat bukti hilang | Kehilangan bukti interupsi, P2 | Arsipkan staging belum committed; cleanup hanya marker completed. Regresi memeriksa counter rusak tetap berada di arsip; PASS |
| ST-03 Bug terbukti pada kandidat | Admission.listing hanya deadline lease; sesi diubah expired tanpa reconcile, status tetap valid | Status menyesatkan sebelum siklus daemon, P2 | Periksa employee lease owner dan require_hash; status lease false walau peer masih ada; PASS |
| LC-03 Bug terbukti pada kandidat | client.local_lock mengikuti symlink open/chmod; reproduksi temp target mode0644 berubah0600 | Perubahan file di luar lock saat client elevated, P1 | O_NOFOLLOW, fstat regular/satu link/pemilik dan fchmod fd; symlink/hardlink ditolak tanpa perubahan target, competing lock ditolak; 29 PASS/1 SKIP client Linux |

Risiko desain yang masih diterima sebagai batas kandidat: transaksi menyalin
seluruh arsip CA sehingga biaya I/O bertambah; tombstone/session/audit dan bukti
interupsi dipertahankan sehingga storage perlu pemantauan. Health tidak memutasi
state dan bukan bukti otorisasi. Perubahan admin root yang sengaja memanipulasi
interface/service/filesystem berada di luar trust model. Kriteria operasional
belum selesai sampai skenario VM masing-masing memiliki bukti sendiri.

LC-04 — **Bug terbukti, P2**: client.local_lock pada Windows membaca byte sebelum
menguncinya. Tes native competing operation gagal dengan PermissionError
(27 PASS/2 SKIP/1 FAIL), sedangkan Linux lulus. Dampak: penolakan operasi paralel
menghasilkan exception mentah. Perbaikan menggunakan fstat.st_size tanpa membaca
byte terkunci dan menangani kegagalan inisialisasi sebagai Rejected. Kriteria
selesai: tes competing/release pada Windows native dan Linux lulus; hasil akhir
dicatat pada checkpoint. Bukti gagal disimpan sebagai first-windows-native.log.

WIN-PERF-01 — **Risiko desain/P2, perbaikan terukur**: template
scripts/create_windows_client.domain_xml dan XML guest tidak menyediakan
hypervclock/vpindex/synic/stimer. Satu juta pembacaan perf_counter membutuhkan
2,63–3,18detik sebelum perubahan,0,045–0,051detik sesudahnya (tiga pengulangan).
Dampak: overhead timer Windows. Konfigurasi minimal beserta dependensinya sudah
diterapkan setelah backup/shutdown normal. Boot/SSH, Secure Boot/TPM dan
hash identitas PASS; native28 PASS/2 SKIP; lima definisi Ubuntu sama. Kriteria
keamanan/boot tercapai; persentase percepatan desktop/boot umum tetap belum
terbukti karena hanya satu sampel startup per konfigurasi dan tipe boot berbeda.

## Pembaruan20 Oktober: rollout dan bukti VM

Status historis BELUM_TERUJI pada tabel19 Oktober tidak otomatis menjadi bukti
terkini. [Matriks rollout](VALIDASI_ROLLOUT_2026-10-20.md) mencatat CA utama
backup/invariant/upgrade, lifecycle Linux lengkap, produksi watchdog, logout
race/scope, HTTP policy nyata dan Windows native/live secara terpisah.

AUD-T01 Bug terbukti/P2: scripts/verify_activity_archive.py main memeriksa secret
hanya pada byte ZIP terkompresi. Reproduksi sintetis membuktikan false negative.
Helper assert_no_credentials kini membuka semua anggota; tiga regresi lulus,
workflow admin live dan scan isi arsip lulus. Tidak ada bukti secret bocor dari
arsip yang dihasilkan aplikasi. Kriteria selesai terpenuhi.

WIN-CLEANUP-02 Risiko desain/P2: WindowsTunnel.down membatasi konfirmasi15detik.
Pada interupsi segera setelah install dalam fault injection, uninstall kembali
tetapi service tetap RUNNING/Disabled. Config dipertahankan, logout memutus
akses server; operator memverifikasi path/ownership, stop dan uninstall hingga
1060 sebelum arsip/hapus config. Penyebab keterlambatan OS belum dipastikan;
jangan mengklaim semua cleanup otomatis lulus. Kriteria lanjutan: reproduksi
terkontrol startup/stop race dan pemulihan otomatis yang tetap memastikan
ownership. Perpanjangan timeout saja bukan bukti penyebab teratasi.

HEALTH-LOCK-01 — **Risiko desain/P2, terverifikasi20 Oktober**:
`vanguard/health.py:probe/ca_state` mengambil shared lock secara nonblocking.
Dua snapshot akhir mengamati503 pada CA atau dependency CA/server, meskipun
liveness200. Diagnosis30sampel menghasilkan18ready dan12BlockingIOError saat
lock; tidak ada kegagalan invariant/CRL pada sampel tersebut. Dampak: contention
transaksi dapat menimbulkan not_ready sementara dan merambat ke admin.
Tidak mengubah503 menjadi200 atau melewati lock. Kriteria selesai berikutnya:
ukur durasi transaksi, uji retry terbatas pada contention singkat/panjang,
pastikan keseluruhan deadline6detik dan timeout dependency konsisten, dan
buktikan probe tetap read-only tanpa menerbitkan CRL atau memulihkan transaksi.

Matriks Windows VM20 Oktober sekarang mencakup expiry, logout race/scope,
reboot aktif, resource gate/TCP aktif, CA/daemon stop/watchdog, replacement dan
disable akun; seluruh hasil aktual terdapat pada matriks rollout. Semua akun/
identitas disposable sudah ditutup dan bukti lama tetap dipertahankan. Bukti
live ini tidak menutup tiga risiko di atas atau membuktikan soak beban panjang.
