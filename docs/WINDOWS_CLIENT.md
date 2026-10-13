# Client Windows tambahan — persiapan 0.1.7

Permintaan 13 Oktober 2026 menambahkan client Windows di samping lima VM Ubuntu.
VM-CLIENT lama tidak diganti. Status instalasi terbaru ada di
[checkpoint](CHECKPOINT.md) dan [jurnal](PROGRESS_2026-10-13.md).
Kode client lintas platform belum berarti tunnel Windows sudah terbukti hidup.

| Node | LAN | Tunnel | Peran |
|---|---|---|---|
| VM-CLIENT | 192.168.100.30 | 10.8.0.2 | Client Ubuntu yang lama |
| VM-CLIENT-WINDOWS | 192.168.100.60 | 10.8.0.4 | Client Windows tambahan |

CA, server, dashboard dan attacker tetap pada alamat/peran semula. Alamat tunnel
10.8.0.3 tetap untuk eksperimen, bukan Windows. Kedua client membuat key X.509
dan WireGuard masing-masing; key/certificate Ubuntu tidak disalin ke Windows.

## VM dan kebutuhan host

Rencana Windows 11: 2 vCPU, 4096 MiB RAM, disk sparse 80 GiB, UEFI Secure Boot
dengan enrolled Microsoft keys dan TPM virtual 2.0. Disk SATA dan NIC e1000e
dipilih agar installer awal tidak memerlukan driver VirtIO terpisah. VNC hanya
listen localhost dan bisa dibuka dengan:

```bash
virt-viewer --connect qemu:///system VM-CLIENT-WINDOWS
```

Host saat pemeriksaan memiliki RAM 7,5 GiB. Instalasi Windows dilakukan saat
kelima Ubuntu mati. Pengujian awal cukup CA/server/Windows; hidupkan dashboard
saat enrollment, dan client Ubuntu bila menguji dua client. Jangan menganggap
VM-ATTACKER atau client lain hidup jika tidak diperiksa. Autostart Windows mati.

Paket host: `ovmf swtpm swtpm-tools`. Skrip
`scripts/create_windows_client.py --output DIREKTORI_BUKTI` menghasilkan rencana;
`--define` membuat satu disk dan domain **tanpa menginstal OS atau menyalakannya**.
Skrip menolak domain/disk yang sudah ada. `--resume` terbatas pada kegagalan define
yang sudah tercatat setelah disk dibuat; jangan gunakan pada guest terpasang.
Lima XML domain Ubuntu dibandingkan sebelum/sesudah dan backup tetap privat.

Sumber media: [Microsoft Evaluation Center](https://www.microsoft.com/en-us/evalcenter/download-windows-11-enterprise).
Windows 11 Enterprise Evaluation berlaku 90 hari, bukan lisensi permanen.
Catat edisi/build, sumber, ukuran dan checksum ISO. File `.part` belum dapat dipakai.
Persyaratan resmi: [Windows 11 VM](https://learn.microsoft.com/en-us/windows/whats-new/windows-11-requirements).
Setup awal Windows dan penerimaan lisensi harus diselesaikan sebelum klaim live.

## Instalasi aplikasi di Windows

1. Pasang Python 3.12 atau lebih baru dari [python.org](https://www.python.org/downloads/windows/)
   dan [WireGuard for Windows resmi](https://www.wireguard.com/install/).
   Periksa tanda tangan installer. Jalankan PowerShell sebagai Administrator.
2. Atur LAN `192.168.100.60/24`, gateway/DNS `192.168.100.1`, dan sinkronkan jam.
   Jangan mematikan firewall Windows. Akses administrasi guest dibatasi host.
3. Pasang wheel VanGuard 0.1.7 yang sudah lulus CI pada virtualenv Python lokal.
   Dependensi Windows memakai pywin32; Gunicorn hanya untuk Linux.
4. Jalankan client sebagai Administrator. Default direktori adalah
   `C:\ProgramData\VanGuard\client`, dengan ACL SYSTEM/Administrators.
   Mode POSIX 0600 bukan pengganti ACL Windows. Path reparse point ditolak.

```powershell
python -m vanguard.client init --device-id vm-client-windows --tunnel-ip 10.8.0.4
```

`request.json` memuat CSR, public key WireGuard, device ID dan tunnel address.
Daftarkan request publik melalui dashboard, buat akun karyawan terpisah, dan
ikat akun itu ke `vm-client-windows`. Dokumentasikan nilai akun/password hanya
di inventaris privat komputer host. Registrasi ini belum menambahkan peer hidup.

Salin sertifikat hasil CA sebagai `device.crt` dan root CA yang telah diverifikasi
sebagai `root.crt` ke direktori client; keduanya publik. Simpan key privat hasil
init di guest. Root ini menjadi trust HTTPS sekaligus identitas CA lab.

```powershell
python -m vanguard.client login --username USERNAME_LOKAL
python -m vanguard.client admit
python -m vanguard.client connect --server-key PUBLIC_KEY_SERVER
```

Ganti placeholder dengan inventaris lokal/public key server terverifikasi.
Login meminta password tersembunyi dan menyimpan token sesi, bukan password.
Biarkan proses `connect` berjalan selama akses dibutuhkan. Ctrl+C membersihkan
tunnel. Setelah restart, login ulang jika sesi expired lalu jalankan `connect`.

Backend menggunakan [WireGuard tunnel service resmi](https://git.zx2c4.com/wireguard-windows/about/docs/enterprise.md),
`WireGuardTunnel$vanguard-client`. Service diubah ke demand start agar boot tidak
otomatis memulai konfigurasi lama. Lease server tetap membatasi akses jika proses
client mati mendadak. Kegagalan renewal memicu pelepasan tunnel. Bila pelepasan
gagal, konfigurasi dipertahankan agar retry menolak mengambil alih tanpa inspeksi.
Untuk pemulihan setelah crash, pastikan proses lama sudah berhenti, lalu uninstall
service khusus ini sebelum menghapus `vanguard-client.conf`; jangan hapus key.

## Server dan validasi wajib

Firewall server memerlukan perluasan eksplisit:

```bash
sudo python3 deploy/firewall.py server --management-ip 192.168.100.1 --windows-client
```

Gunakan source yang disalin ke VM-SERVER dan prosedur rollback timer yang sama
seperti [deployment](DEPLOYMENT.md). Konfirmasi akses lewat SSH baru sebelum
mematikan timer rollback. Flag ini membuka API 8081/UDP 51820 dari .60 dan ICMP
dari .4 **hanya pada wg0**. Drop bypass LAN dan forward default drop tetap berlaku.
Default tanpa flag mempertahankan firewall lima VM lama. Deployment firewall ini
harus dibuktikan, bukan dianggap terjadi karena source sudah berubah.

Urutan bukti guest Windows yang harus disimpan sebelum menyatakan dukungan penuh:

1. OS/build, TPM/Secure Boot, LAN, sinkronisasi jam dan ACL identitas.
2. Enrollment tanpa peer; login saja juga tidak menambahkan peer.
3. Admission enam pemeriksaan, handshake WireGuard dan ping 10.8.0.1.
4. Client Ubuntu dan Windows hidup bersamaan tanpa konflik alamat/key.
5. Sertifikat/sesi tidak sah ditolak; revocation Windows menghentikan Windows,
   sementara client Ubuntu tetap berfungsi. Gunakan identitas uji untuk pencabutan.
6. Ctrl+C, kegagalan renewal dan reboot: cleanup, demand start dan lease expiry.

CI Windows hanya menguji helper client, file/sesi dan ACL native; backend command
diuji dengan stub. CI itu tidak membuktikan handshake atau admission di VM lab.
Runner benchmark/security/health lama masih menargetkan lima Ubuntu; jangan
menghitungnya sebagai bukti Windows atau menjalankannya lewat SSH Linux pada .60.
