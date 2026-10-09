# Rencana uji Tugas Akhir

Jalankan pengujian pada lima VM yang diizinkan. Catat waktu UTC, device ID, serial sertifikat,
hasil API, audit server, `wg show wg0`, dan ping. Jangan memasukkan private key/token/TOTP
ke laporan. `/healthz` saja tidak membuktikan admission atau koneksi tunnel.

| Skenario | Langkah | Hasil yang harus dibuktikan |
|---|---|---|
| Boot bersih | Start server dan daemon | Peer kosong |
| Registrasi | Upload CSR/WG key melalui admin | Sertifikat dan binding ada, peer tetap kosong |
| Admission sah | Client challenge + proof | ACCEPT, satu peer dengan 10.8.0.2/32 |
| S-01 akun dicuri | Login akun karyawan valid dari attacker; tanpa sertifikat atau dengan sertifikat publik dan key berbeda | Login 200; admission ditolak; tidak ada peer attacker |
| Sesi akun | Token hilang/salah, akun lain, token berbeda setelah challenge atau sesi expired saat CRL fetch | Ditolak sebelum peer ditambahkan |
| Disable akun | Nonaktifkan akun yang memiliki peer aktif; coba sesi lama lagi | Peer hilang dan admission ditolak |
| Legacy dan metadata | Perangkat lama tanpa binding akun; edit nama/departemen/pemilik/platform | Legacy gagal tertutup sampai binding/login; metadata tidak mengubah identitas |
| Handshake | Client connect, ping 10.8.0.1 | latest handshake terisi, paket lewat tunnel |
| Tanpa token | Attacker memanggil GET /api/devices | 401, registry tidak dibocorkan |
| Sertifikat palsu | Attacker mengirim sertifikat tak tepercaya | Ditolak, tidak ada peer baru |
| Tanpa private key | Sertifikat sah dengan signature yang salah | Ditolak |
| WG key berbeda | Gunakan public key di luar binding | Ditolak |
| Replay | Kirim ulang body verify yang pernah sukses | Ditolak; satu penambahan peer saja |
| Challenge expired | Tunda lebih dari 60 detik | Ditolak |
| Sertifikat expired/future | Fixture lokal dengan periode tidak sah | Ditolak tanpa mengubah waktu VM bersama |
| CRL salah/stale | Fixture CRL unsigned/future/expired | Ditolak |
| Revocation sebelum verify | Cabut setelah challenge diterbitkan | Verify ditolak |
| Revocation saat aktif | Cabut perangkat yang sedang ping | Peer hilang, tunnel berhenti |
| Lease expired | Hentikan renewal tanpa menghapus peer | Peer dihapus daemon setelah lease habis |
| CA offline | Hentikan CA saat peer aktif | Admission gagal; daemon menghapus peer |
| Peer asing | Sisipkan key asing pada adapter WireGuard dalam suite lokal | Daemon menghapusnya; tidak menambah peer live tanpa admission |
| Restart | Restart API/daemon | Peer/lease dibersihkan, perlu admission ulang |
| Daemon gagal | Stop daemon melalui systemd | wg0 dan API ikut berhenti |
| TOTP | Password benar dengan TOTP salah/replay | Login gagal |
| CSRF | POST admin tanpa CSRF | 403 |
| Workflow parsial | Putus akses registry sesudah CA issue | pending_registry; retry memakai sertifikat yang sama |
| Batas detik CRL | Fixture bertanda tangan sah 50 ms di masa depan | Tunggu, validasi ulang; diterima hanya setelah lastUpdate |
| Clock tidak maju | Simulasikan jam tetap/future lebih dari satu detik | CRL ditolak; tidak ada toleransi validitas |
| Challenge habis saat fetch | Lewatkan TTL ketika mengambil CRL | Verify ditolak sebelum penambahan peer |

## Bukti yang bisa dilanjutkan

`scripts/verify_operations.py` menyimpan hasil setiap langkah secara atomik, dengan
status RUNNING/COMPLETE/FAIL/INTERRUPTED. Run baru memerlukan direktori `--state`
baru jika file fase tersebut sudah ada. Untuk melanjutkan reboot yang terhenti:

```bash
.venv/bin/python scripts/verify_operations.py state/lab/inventory.json reboot --resume
```

Role yang sudah memiliki hasil PASS dilewati. RUNNING yang tertinggal setelah
proses mati harus diperiksa, bukan dianggap selesai. `scripts/verify_identity.py`
menulis nama identitas, direktori, tahap aktif, hasil admission/revocation dan
cleanup setelah setiap langkah; gunakan nama tersebut untuk memeriksa cleanup
identitas sementara jika proses terputus. Identitas utama tidak boleh dicabut.

`scripts/verify_employee.py` menjalankan S-01 dari VM-ATTACKER dengan akun dan
identitas sementara. Kredensial hanya lewat stdin, tidak dicetak; private key
perangkat tidak dikirim ke attacker. Jalankan terpisah dari `verify_identity.py`
karena keduanya memakai peer sementara `10.8.0.3`. Pengamatan disable akun sekali
yang mencakup waktu SSH bukan nilai MTTD/MTTR atau bukti trafik S-04 berulang.

Unit/integration tests lokal mencakup komponen PKI, API Flask, workflow admin, concurrency
challenge, dan lifecycle melalui adapter WireGuard. OpenSSL CA sungguhan menghasilkan
sertifikat dan CRL di temporary directory. Uji tersebut tidak memodifikasi konfigurasi
WireGuard atau firewall host.

Pengujian jaringan harus dijalankan terpisah pada VM: TLS dengan SAN IP, firewall, deployment
systemd, handshake kernel, reboot, dan pemutusan akses end-to-end. Hasil yang belum diuji
harus diberi status **belum terverifikasi**, bukan lulus.
