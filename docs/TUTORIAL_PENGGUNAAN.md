# Tutorial penggunaan VanGuard dari awal sampai akhir

Panduan untuk **VanGuard 0.1.6 pada lab yang sudah terpasang di laptop ini**.
Ikuti bagian 1–6 untuk pemakaian harian, bagian 7 untuk latihan registrasi,
bagian 8 untuk pengujian, dan bagian 9 untuk menutup sesi. Solusi masalah ada
di bagian 10. Panduan ini tidak menjalankan perubahan hanya dengan membacanya.

Jika menyiapkan lingkungan kosong, gunakan [panduan instalasi](DEPLOYMENT.md)
dahulu. Jangan menjalankan installer, membuat CA atau `init` client utama lagi
pada lab yang sudah ada. Status dan pekerjaan berikutnya ada di [checkpoint](CHECKPOINT.md).

## 1. Kenali tempat menjalankan perintah

**Laptop/workstation** adalah terminal Ubuntu milik `lui`, tempat folder
`/home/lui/vanguard` berada. **VM** adalah terminal yang dibuka lewat SSH.
Setiap contoh di bawah menyebutkan tempat menjalankannya. Ketik `exit` untuk
keluar dari SSH dan kembali ke laptop.

| Mesin | IP | Kegunaan |
|---|---|---|
| VM-CA | 192.168.100.10 | Menerbitkan dan mencabut sertifikat |
| VM-SERVER | 192.168.100.20 | Memeriksa identitas dan mengatur peer WireGuard |
| VM-CLIENT | 192.168.100.30 | Tempat karyawan login dan memakai VPN |
| VM-ADMIN | 192.168.100.40 | Dashboard administrator |
| VM-ATTACKER | 192.168.100.50 | Simulasi pengujian keamanan |

| Identitas | Dipakai di mana | Yang dibutuhkan |
|---|---|---|
| Admin dashboard | Browser laptop | Username, password, kode TOTP |
| Karyawan VPN | Aplikasi CLI di VM-CLIENT | Username dan password karyawan |
| Perangkat | Diperiksa otomatis saat admission | Sertifikat, key perangkat dan binding yang sah |

Username akun karyawan tersimpan di inventaris kredensial lokal dan terikat ke
perangkat `vm-client`; ganti `USERNAME_LOKAL` pada contoh perintah dengan nilai itu.
Alamat tunnel utama: client `10.8.0.2` → server `10.8.0.1`. Akses yang tersedia
untuk demo adalah ping server melalui tunnel; ini bukan VPN internet umum atau
bukti akses ke aplikasi manufaktur yang belum dipasang.

## 2. Nyalakan lab

**Di laptop:**

```bash
cd /home/lui/vanguard
bash scripts/open_dashboard.sh
```

Skrip menyalakan lima VM yang sudah ada, menunggu HTTPS dashboard, lalu membuka
browser. Tunggu proses boot. Jika browser tidak terbuka, buka sendiri:
**https://192.168.100.40:5000**.

Periksa kesiapan dari terminal laptop yang sama:

```bash
virsh -c qemu:///system list --all
.venv/bin/python scripts/ssh_preflight.py state/lab/inventory.json
```

Kelima VM seharusnya `running`, dan setiap role pada hasil preflight memiliki
`"ok": true`. Jika SSH belum siap saat boot, tunggu lalu ulangi preflight.
Dashboard yang bisa dibuka belum membuktikan VPN client sudah aktif.

Untuk membuka tampilan pengelolaan VM:

```bash
virt-manager --connect qemu:///system
```

## 3. Aktifkan authenticator dan masuk sebagai admin

Bagian aktivasi HP cukup dilakukan sekali selama secret admin belum berubah.

1. Di file manager laptop, buka `/home/lui/vanguard/state/deployment/aktivasi-admin.html`
   menggunakan Firefox. Halaman privat ini menampilkan username, password yang
   bisa dibuka, dan QR untuk aktivasi TOTP.
2. Pada aplikasi authenticator HP yang mendukung TOTP, pilih tambah akun dan
   pindai QR. Untuk input manual: berbasis waktu, SHA-1, enam digit, 30 detik.
3. Aktifkan tanggal/waktu otomatis di HP.
4. Buka **https://192.168.100.40:5000**, isi **Username**, **Password**, dan
   **Kode TOTP** terbaru dari HP, lalu klik **Masuk**.
5. Setelah berhasil, halaman menampilkan **Perangkat & admission**.

Sistem membuat secret/QR saat pembuatan akun admin; aplikasi authenticator
menghasilkan kode berkala dari secret itu, dan dashboard memverifikasi kodenya.
Dashboard tidak menyediakan tombol untuk menampilkan kode login TOTP berjalan.
TOTP admin tidak dipakai untuk menggantikan login karyawan.

Kode yang sudah dipakai tidak dapat dipakai lagi untuk login kedua: tunggu kode
berikutnya. Setelah lima kegagalan, tunggu lima menit. Sesi admin berlaku sekitar
30 menit; jika kembali ke halaman login, gunakan kode baru.

Firefox lab sudah memiliki Root CA pada profil yang disiapkan. Untuk browser
lain, impor `state/deployment/root.crt` melalui pengaturan Authorities/CA untuk
website. Ikuti [aktivasi admin](AKTIVASI_ADMIN.md) jika ada peringatan TLS;
jangan melewati peringatan sertifikat yang tidak cocok.

QR/secret TOTP dan password hanya untuk operator. Jangan masukkan halaman aktivasi
ke screenshot laporan atau Git. Login HP oleh operator belum dikonfirmasi dalam
bukti pengujian otomatis.

## 4. Login karyawan dan aktifkan VPN utama

**Dari laptop**, masuk ke VM-CLIENT:

```bash
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.30
```

Prompt sekarang berada di `vm-client`. **Di VM-CLIENT:**

```bash
sudo /opt/vanguard/venv/bin/vanguard-client login --username USERNAME_LOKAL
```

Masukkan password **karyawan**, bukan password admin. Karakter password tidak
muncul saat diketik; ini normal. Jika belum mengetahui password lab, operator
dapat melihatnya secara privat di file lokal laptop
`/home/lui/VanGuard-Privat/KREDENSIAL_VANGUARD.md` menggunakan editor. Dokumen lokal
ini juga memuat kredensial admin dan password console lima VM. Sumber bootstrap
tetap `state/deployment/proposal-2026-10-09/employee-onboarding.json`.
Jangan menaruh password pada argumen perintah, chat atau jurnal.

Login sukses menampilkan username dan `expires_at`, bukan token. Selanjutnya:

```bash
sudo systemctl restart vanguard-client
sudo systemctl status vanguard-client --no-pager
ping -c 3 -W 2 10.8.0.1
sudo wg show wg0
```

Tunggu beberapa detik jika admission masih berlangsung. Target keberhasilan:
layanan aktif, ping mendapat balasan, dan `wg show` menunjukkan handshake serta
transfer. Status service saja belum cukup untuk membuktikan koneksi.

Sesi karyawan berlaku **delapan jam**. Jika expired, ulangi login dan restart
di atas. Renewal perangkat tidak memperpanjang login. Menyalakan laptop/VM
tidak otomatis memperbarui sesi. Client menyimpan token dalam file privat;
password tidak disimpan oleh aplikasi client.

Jangan menjalankan `connect` manual bersamaan dengan service utama: keduanya
akan mencoba memakai interface `wg0`. Untuk pemakaian harian gunakan systemd
seperti contoh di atas.

## 5. Pastikan akses berhasil

**Di browser**, muat ulang dashboard dan cari ID `vm-client`:

- Workflow `registered`: pendaftaran identitas selesai.
- Akun VPN `USERNAME_LOKAL`: binding akun yang digunakan.
- Tunnel `10.8.0.2` dan Peer **Aktif**: peer terlihat pada server.

**Di terminal laptop lain**, periksa server:

```bash
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.20
sudo systemctl is-active vanguard-server vanguard-daemon wg-quick@wg0
sudo wg show wg0
exit
```

Ketiga unit seharusnya `active`. Peer utama memiliki allowed IP `10.8.0.2/32`.
Gunakan `wg show` biasa; format `dump` memuat private key.

Untuk menyimpan pemeriksaan menyeluruh, **di laptop**:

```bash
cd /home/lui/vanguard
tutorial_run="state/deployment/tutorial-$(date +%Y%m%d-%H%M%S)"
.venv/bin/python scripts/health_lab.py state/lab/inventory.json \
  --state "$tutorial_run/health" --samples 3 --interval 10
```

Hasil yang diharapkan: tiga baris `PASS sample`, dan `health.json` di direktori
tersebut berstatus `COMPLETE`. Catat path yang digunakan. Buat nilai
`tutorial_run` baru untuk pengulangan; jangan menimpa bukti sebelumnya.
Jangan menjalankan health bersamaan dengan pencabutan atau shutdown.

## 6. Memakai dashboard

| Bagian/tombol | Cara memakai dan akibatnya |
|---|---|
| Kesehatan layanan | Lihat status HTTPS CA/server saat halaman dimuat; liveness tidak membuktikan tunnel aktif |
| Akun karyawan | Isi username dan password awal minimal 12 karakter; klik **Buat akun karyawan** |
| Registrasi perangkat | Unggah request JSON dari client, isi metadata, pilih akun, klik **Terbitkan sertifikat & daftarkan binding** |
| Unduh sertifikat | Ambil sertifikat milik baris perangkat tersebut untuk dipasang ke client yang membuat request |
| Unduh bundle onboarding | ZIP sertifikat/root publik, manifest dan petunjuk; tanpa private key/token, belum auto-import konfigurasi |
| Riwayat perangkat | Lihat masa berlaku UTC/fingerprint, alasan pencabutan dan aktivitas dengan waktu WIB |
| Edit data perangkat | Ubah nama/departemen/pemilik/platform, lalu **Simpan data perangkat**; identitas dan binding akun tetap |
| Tautkan akun VPN | Hanya muncul untuk perangkat lama berstatus registered yang belum punya akun |
| Ulangi workflow | Lanjutkan workflow yang belum selesai sesudah dependency pulih |
| Aktivitas keamanan server | Lihat peristiwa VPN otomatis dengan waktu WIB dan keterangan bahasa Indonesia |
| Aktivitas administrasi | Buka **Aktivitas admin**, pilih tanggal WIB, pelaku, perangkat atau jenis tindakan; telusuri 50 per halaman |
| Arsip aktivitas | Klik **Simpan arsip aktivitas** untuk semua hasil filter; **Arsip** menampilkan dan mengunduh snapshot CSV/JSON/manifest |
| Keluar | Mengakhiri sesi dashboard; tidak mematikan VPN karyawan |

Registrasi belum mengaktifkan peer. Client harus login dan lolos enam pemeriksaan
perangkat saat admission. Jika tertulis **Status server tidak tersedia** atau
Peer **Tidak tersedia**, keadaan peer belum dapat dipastikan; periksa server.

### Cari dan arsipkan aktivitas admin

1. Klik **Aktivitas admin** di navigasi setelah masuk dashboard.
2. Pilih tanggal mulai/akhir menurut WIB; tanggal akhir mencakup satu hari penuh.
   Isi nama admin, ID perangkat, atau jenis tindakan bila diperlukan.
3. Klik **Tampilkan** untuk meninjau hasil. Urutan mengikuti ID saat tindakan
   dicatat; satu proses dapat menampilkan beberapa tahap seperti diminta, gagal,
   lalu selesai.
4. Klik **Simpan arsip aktivitas**. Arsip mengambil seluruh hasil filter, bukan
   hanya 50 catatan pada halaman itu. Batas satu arsip 10.000 catatan; perkecil
   rentang/filter jika jumlahnya melebihi batas.
5. Klik **Arsip** lalu **Unduh arsip ZIP**. Berkas berisi CSV untuk Excel/LibreOffice,
   JSON terstruktur, manifest pembuat/waktu/filter/jumlah, petunjuk, dan SHA-256.
   Bandingkan checksum ZIP di halaman arsip dengan header `X-Archive-SHA256`.
6. Simpan hasil di folder privat komputer. Arsip dan log sumber tetap berada di
   server admin; backup konsisten database admin untuk menjaga salinan arsip.

Waktu pada layar dan CSV adalah WIB hingga detik; arsip turut menyimpan timestamp
Unix/UTC. Detail menggunakan bahasa Indonesia. Catatan sebelum versi 0.1.5 tidak
direkonstruksi. Arsip bersifat snapshot, bukan tanda tangan digital atau bukti
tahan perubahan oleh root; jangan membagikan hasilnya ke repository publik.

Dua tindakan berikut mengakhiri akses dan digunakan pada identitas latihan:

- **Nonaktifkan [username]** membatalkan sesi dan menghapus peer yang terkait.
  Sertifikat belum otomatis dicabut. Belum ada tombol aktivasi ulang atau reset
  password mandiri pada versi ini.
- **Cabut akses & sertifikat** menonaktifkan identitas dan mencabut sertifikat
  melalui CA. Identitas yang dicabut tidak dapat diaktifkan kembali; gunakan
  identitas/key baru untuk enrollment berikutnya.

Binding akun-perangkat tidak dapat diganti lewat edit metadata. Jangan mencabut
`vm-client` atau menonaktifkan `USERNAME_LOKAL` untuk latihan.

## 7. Latihan lengkap: akun baru → registrasi → admission → pencabutan

Bagian opsional ini memakai identitas terpisah pada VM-CLIENT yang sama, alamat
`10.8.0.3`, tanpa menambah VM. Tujuannya mempelajari workflow dashboard dan admission.
Tunnel utama `10.8.0.2` tetap dipakai untuk demo trafik pada bagian 4–5.

Pastikan tidak ada eksperimen lain memakai `10.8.0.3`. Nama contoh di bawah hanya
untuk **satu kali latihan**. Bila sudah ada, gunakan ID, username dan direktori
baru secara konsisten; jangan hapus bukti atau mengulang identitas yang dicabut.

### 7a. Buat akun latihan di dashboard

Pada **Akun karyawan**, buat username `tutorial-user-01` dengan password unik
minimal 12 karakter yang Anda simpan secara privat. Jangan memakai akun utama
agar penonaktifan di akhir latihan tidak memengaruhinya.

### 7b. Buat request pada VM-CLIENT

Masuk SSH ke `.30` seperti bagian 4, kemudian **di VM-CLIENT**:

```bash
sudo /opt/vanguard/venv/bin/vanguard-client \
  --directory /var/lib/vanguard/tutorial-client-01 init --device-id tutorial-client-01
```

Ini membuat key X.509, key WireGuard dan `request.json` pada direktori baru.
Key tetap berada pada client. Karena `init` memberikan alamat default `.2`,
ubah **request latihan saja** menjadi `.3` sebelum diunggah:

```bash
sudo /opt/vanguard/venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path('/var/lib/vanguard/tutorial-client-01/request.json')
data = json.loads(p.read_text())
assert data['device_id'] == 'tutorial-client-01'
data['tunnel_ip'] = '10.8.0.3'
p.write_text(json.dumps(data, indent=2) + '\n')
PY
exit
```

**Di laptop**, salin request untuk dipilih lewat browser:

```bash
cd /home/lui/vanguard
umask 077
mkdir -p state/tutorial
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.30 \
  'sudo cat /var/lib/vanguard/tutorial-client-01/request.json' \
  > state/tutorial/tutorial-client-01-request.json
```

File ini memuat CSR/public key, bukan private key. Jangan menyalin `identity.key`
atau `wg.key` untuk registrasi.

### 7c. Daftarkan request di dashboard

1. Pilih `state/tutorial/tutorial-client-01-request.json` pada **Request dari aplikasi client**.
2. Isi nama perangkat, departemen, pemilik dan platform dengan data latihan.
   Contoh: nama `Client latihan 01`, departemen `Lab`, pemilik `Operator latihan`,
   platform `Ubuntu 22.04`.
3. Pilih akun `tutorial-user-01`.
4. Klik **Terbitkan sertifikat & daftarkan binding**.
5. Pastikan ID `tutorial-client-01` berstatus `registered`; peer latihan belum aktif.
   Peer utama boleh tetap aktif, sehingga daftar peer server tidak harus kosong.
6. Klik **Unduh sertifikat** pada baris latihan. Nama berkasnya `tutorial-client-01.crt`.

Jika workflow tertahan, baca pesan error, perbaiki koneksi CA/server, lalu gunakan
**Ulangi workflow** pada baris yang sama. Jangan unggah request itu sebagai
pendaftaran baru berulang kali.

### 7d. Pasang sertifikat, login dan lakukan admission

**Di laptop**, dengan asumsi browser menyimpan sertifikat di `Downloads`:

```bash
scp -F ~/.ssh/vanguard_lab_config ~/Downloads/tutorial-client-01.crt \
  192.168.100.30:/home/ubuntu/tutorial-client-01.crt
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.30
```

Sesuaikan path sumber jika folder unduhan berbeda. **Di VM-CLIENT:**

```bash
sudo install -m 0600 /home/ubuntu/tutorial-client-01.crt \
  /var/lib/vanguard/tutorial-client-01/device.crt
sudo /opt/vanguard/venv/bin/vanguard-client \
  --directory /var/lib/vanguard/tutorial-client-01 login --username tutorial-user-01
sudo /opt/vanguard/venv/bin/vanguard-client \
  --directory /var/lib/vanguard/tutorial-client-01 admit
```

Masukkan password latihan saat login. Admission yang berhasil menghasilkan
`"decision": "ACCEPT"` dan `"tunnel_ip": "10.8.0.3"`. Muat ulang dashboard:
peer latihan menjadi aktif sampai lease habis atau akses dicabut.

Perintah `admit` **menambahkan peer di server setelah validasi**, tetapi tidak
membuat interface atau memperbarui lease otomatis pada client. Jangan memakai
`connect` untuk latihan `.3`: CLI koneksi utama versi ini khusus `10.8.0.2`.
Tidak ada klaim trafik `.3` berdasarkan `admit` saja. Untuk demo trafik gunakan
tunnel utama; pengujian trafik pencabutan terpisah dijelaskan di bagian 8.

### 7e. Cabut identitas latihan dan tutup akunnya

1. Di dashboard, pastikan baris yang dipilih adalah **tutorial-client-01**.
2. Pilih alasan **Pembersihan pengujian**, lalu klik **Cabut akses & sertifikat**.
   Tunggu workflow `revoked` dan peer tidak aktif.
3. Jika tertulis `revoking`, pulihkan dependency yang gagal dan klik **Ulangi workflow**
   sampai selesai; jangan menganggap pencabutan selesai hanya karena tombol diklik.
4. Di VM-CLIENT, ulangi perintah `admit` latihan. Permintaan harus ditolak. Pesan
   dapat menyebut perangkat disabled atau sertifikat revoked sesuai tahap pemeriksaan.
5. Di dashboard, klik **Nonaktifkan tutorial-user-01**.
6. Di VM-CLIENT, jalankan `ping -c 3 -W 2 10.8.0.1`: koneksi utama tetap mendapat balasan.

Simpan direktori latihan secara privat sebagai bukti; jangan mengunggah key/token.
Selesaikan cleanup ini sebelum menjalankan skrip pengujian lain yang memakai `.3`.
Pencabutan melalui dashboard menggabungkan disable dan revoke; pengujian CA-only
untuk membuktikan deteksi CRL tersedia lewat runner identity pada bagian berikut.

## 8. Pengujian dan bukti untuk TA

Untuk demo cepat, tunjukkan topologi, login admin, ping tunnel utama, status peer,
kemudian hasil penolakan attacker. **Di laptop**, masuk ke attacker:

```bash
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.50
/opt/vanguard/venv/bin/python /opt/vanguard/attacker_checks.py
exit
```

Skrip menguji tiga request negatif. HTTP 401/403/400 sesuai skenario adalah
penolakan yang diharapkan; kegagalan koneksi berlabel `UNVERIFIED` bukan bukti
keamanan. Skrip ini berbeda dari skenario S-01 dengan kredensial valid.

Untuk pengujian lengkap berikut, pastikan main ping sehat dan tidak ada latihan
manual `.3` yang masih aktif. **Di laptop**, buat direktori run baru:

```bash
cd /home/lui/vanguard
tutorial_run="state/deployment/tutorial-tests-$(date +%Y%m%d-%H%M%S)"
```

Jalankan satu per satu; tunggu selesai dan periksa hasil/cleanup sebelum berikutnya:

```bash
.venv/bin/python scripts/verify_employee.py state/lab/inventory.json \
  --state "$tutorial_run/s01"
```

Ini membuat akun/identitas sementara, login dari attacker dengan password valid,
menguji penolakan perangkat tidak sah, kontrol positif dan disable akun.

```bash
.venv/bin/python scripts/verify_identity.py state/lab/inventory.json \
  --state "$tutorial_run/identity"
```

Ini menguji registrasi tanpa peer, proof/binding/replay, pencabutan langsung
melalui CA, penghapusan peer dan penolakan admission ulang.

```bash
.venv/bin/python scripts/verify_response_metrics.py state/lab/inventory.json \
  --state "$tutorial_run/metrics"
```

Ini menjalankan sepuluh percobaan proof salah setelah login valid. Hasil ada di
`response-metrics.json`. MTTD mengukur request sampai deteksi di aplikasi;
MTTR berarti **Respond**, dari deteksi sampai JSON penolakan siap. RTT jaringan
dicatat terpisah. Ikuti [definisi metrik](RESPONSE_METRICS.md) saat menulis laporan.

Skrip menggunakan identitas sementara dan mencoba cleanup; jangan jalankan
bersamaan. Jika gagal/terputus, periksa `status`, tahap terakhir, device ID,
username dan hasil cleanup pada JSON. `RUNNING`, `FAIL` atau `INTERRUPTED`
bukan PASS. Simpan bukti dan selesaikan cleanup sebelum mengulang.

Setelah seluruh pengujian selesai:

```bash
.venv/bin/python scripts/health_lab.py state/lab/inventory.json \
  --state "$tutorial_run/health-after" --samples 3 --interval 10
```

Gunakan [panduan demo](DEMO_TA.md), [hasil S-01 terukur](RESPONSE_METRICS_2026-10-10.md)
dan [hasil S-03/S-04](SECURITY_RESULTS_2026-10-09.md) untuk presentasi. Prosedur
capture/putus trafik ICMP ada pada [protokol eksperimen](SECURITY_EXPERIMENTS.md).
S-03/S-04 yang tercatat berasal dari 0.1.3; jangan menyebutnya hasil ulang 0.1.4.
Benchmark tiga kondisi masih tahap rencana, sehingga belum ada hasil yang bisa
dipresentasikan sebagai eksperimen selesai.

## 9. Selesai menggunakan sistem

### Hanya keluar dari dashboard

Klik **Keluar**. VPN karyawan tetap berjalan. Tutup juga halaman aktivasi privat.

### Hanya memutus VPN pada client

**Di VM-CLIENT:**

```bash
sudo systemctl stop vanguard-client
sudo systemctl is-active vanguard-client
```

Status menjadi `inactive`; interface client diturunkan secara normal. Peer pada
server dapat tetap terlihat sampai lease habis karena stop lokal bukan revoke.
Token sesi juga tidak otomatis dibatalkan. Untuk menghubungkan kembali, login
ulang bila expired lalu `sudo systemctl start vanguard-client`.

### Mematikan seluruh lab

Pastikan pengujian dan cleanup selesai, catat hasil/path bukti, dan logout admin.
Hentikan client seperti di atas, kemudian keluar dari SSH. **Di laptop:**

```bash
virsh -c qemu:///system shutdown VM-CLIENT
virsh -c qemu:///system shutdown VM-ATTACKER
virsh -c qemu:///system shutdown VM-ADMIN
virsh -c qemu:///system shutdown VM-SERVER
```

Periksa `virsh -c qemu:///system list --all` sampai keempatnya `shut off`, lalu:

```bash
virsh -c qemu:///system shutdown VM-CA
virsh -c qemu:///system list --all
```

Tunggu CA juga `shut off` sebelum mematikan laptop. `shutdown` mengirim permintaan
shutdown normal; bukan jaminan VM sudah mati seketika. Jika belum selesai,
periksa console lewat Virtual Machine Manager. Jangan memakai `destroy`, `undefine`
atau menghapus disk untuk menutup sesi biasa.

Saat melanjutkan besok, ulangi bagian 2, login karyawan bila sesi expired, lalu
bagian 5. Akun/CA/key/sertifikat lama tetap dipakai; tidak perlu registrasi ulang.

## 10. Jika terjadi masalah

| Gejala | Pemeriksaan / tindakan |
|---|---|
| Dashboard tidak bisa dibuka | Cek lima VM running dan preflight; pada VM-ADMIN cek `sudo systemctl status vanguard-admin --no-pager` |
| SSH connection refused saat boot | Tunggu boot, ulangi preflight; lihat console jika tetap gagal |
| SSH host key berubah | Verifikasi identitas VM; jangan menghapus known_hosts atau menonaktifkan pemeriksaan begitu saja |
| Browser menolak sertifikat | Periksa IP URL, jam laptop dan trust Root CA seperti bagian 3 |
| Password admin benar tetapi login gagal | Gunakan TOTP terbaru, waktu HP otomatis, jangan ulang kode yang sudah dipakai; tunggu lima menit setelah lima kegagalan |
| Employee session expired | Login karyawan ulang di VM-CLIENT, kemudian restart vanguard-client |
| registered tetapi peer tidak aktif | Pastikan cert sudah dipasang, sesi karyawan valid, binding akun benar dan client berjalan; registrasi sendiri belum admission |
| Certificate does not match identity.key | Sertifikat salah perangkat; pasang unduhan milik request/ID yang sesuai tanpa mengganti private key |
| Peer tidak tersedia di dashboard | Periksa server dan koneksi admin → server; status ini belum membuktikan peer hilang |
| Ping gagal meski service active | Periksa log client, peer/handshake server, CA/CRL dan waktu VM; jangan menambah peer manual |
| wg0.conf exists | Ada sisa interface/config atau proses lain; periksa service dan `sudo wg show`, jangan langsung menghapus key/config |
| pending_issue / pending_registry / revoking | Baca error pada baris perangkat, pulihkan CA/server, gunakan Ulangi workflow |
| Akun disabled atau sertifikat revoked | Tidak bisa dipulihkan lewat login; lakukan enrollment identitas baru sesuai prosedur, tanpa menghidupkan sertifikat lama |
| Direktori hasil pengujian sudah ada | Pilih nama run baru dan pertahankan bukti lama |

Log yang berguna **pada VM sesuai perannya**:

```bash
# VM-CLIENT
sudo journalctl -u vanguard-client -n 50 --no-pager
# VM-SERVER
sudo journalctl -u vanguard-server -u vanguard-daemon -n 50 --no-pager
# VM-CA
sudo journalctl -u vanguard-ca -n 50 --no-pager
# VM-ADMIN
sudo journalctl -u vanguard-admin -n 50 --no-pager
```

Gunakan `timedatectl status` pada VM yang bermasalah untuk memeriksa sinkronisasi
waktu. Baca log secara lokal dan periksa isinya sebelum membagikan.

## 11. Catatan agar pekerjaan bisa dilanjutkan

Catat waktu, tujuan, ID akun/perangkat latihan, file/VM yang berubah, direktori
bukti, hasil aktual, status cleanup, error dan langkah berikutnya dalam
`docs/PROGRESS_YYYY-MM-DD.md`. Tulis rencana sebelum perubahan, hasil setelahnya;
perbarui `docs/CHECKPOINT.md` dan `LANJUTKAN_PROYEK.md` sebelum berhenti.

Jangan mencatat password, token, QR/seed TOTP, private key, isi env atau backup
privat ke dokumentasi/Git. Backup CA tidak boleh dipulihkan ke index/CRL lama
yang mengaktifkan kembali sertifikat dicabut. Panduan ini diverifikasi terhadap
source CLI/template dan dokumentasi 0.1.5; latihan manual serta shutdown di atas
tidak dijalankan saat penulisan tutorial.

Penjelasan migrasi, audit dan batas bundle ada pada [panduan dashboard 0.1.5](DASHBOARD_0.1.5.md).
