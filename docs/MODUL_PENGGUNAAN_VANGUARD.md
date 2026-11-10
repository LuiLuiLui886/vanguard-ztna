# Panduan penggunaan VanGuard

Edisi 11 November 2026 · panduan admin dan pengguna Windows.
Markdown dan HTML adalah dua format dari **manual yang sama**.
Manual yang tertanam di EXE/ZIP rilis lama belum dibangun ulang; gunakan edisi
MD/HTML terbaru di folder `docs` ini saat mengikuti tutorial.
Ganti `/PATH/...`, `ID_PERANGKAT`, `IP_TUNNEL` dan placeholder kapital dengan
nilai yang sudah disiapkan admin; jangan menyalin placeholder apa adanya.

**Versi panduan ini:** source CA 0.1.17; server, admin, dan installer Windows
0.1.15 pada branch `feature/2026-10-22-physical-endpoints`. Versi pada VM harus
diperiksa terlebih dahulu; jangan menyimpulkan versi terpasang hanya dari GitHub.

**Status:** alur lab sudah diuji, tetapi penerapan nyata belum selesai diterima.
Instalasi Windows dari OS kosong, UAC interaktif, PC fisik LAN/Wi-Fi, koneksi TCP
internet yang tetap aktif saat revoke, dan uji daya putus CA masih BELUM_TERUJI.
Lihat [checkpoint](CHECKPOINT.md) dan [hasil validasi](reports/VALIDASI_0.1.15_2026-11-02.md).

**Alur:** siapkan layanan → install endpoint → daftar perangkat → import sertifikat
→ login → connect → uji akses → logout atau revoke.

| Kebutuhan | Mulai dari |
|---|---|
| Baru pertama membaca / memakai lab yang sudah ada | Bagian 0, lalu 1–6 |
| Sistem sudah terpasang, tambah PC Windows | Bagian 0–5 |
| Perangkat sudah terdaftar | Bagian 4 |
| Cabut akses atau lihat aktivitas | Bagian 6 |
| Membuat paket satu BAT/EXE per perangkat | Bagian 7 |
| Memblokir internet tanpa mengubah router | Bagian 8 |
| Memasang backend dan CA dari nol | Bagian 9, lalu kembali ke Bagian 1 |
| Ada kendala | Bagian 10 |

**Pilih paket:** gunakan versi dan checksum pada [halaman unduhan](../downloads/README.md).
Lihat [checkpoint](CHECKPOINT.md) untuk versi yang benar-benar terpasang dan hasil
uji. Instalasi aplikasi tidak otomatis mengaktifkan profil server atau gateway
internet; admin tetap perlu mengikuti konfigurasi pada Bagian 1 dan 8.

## 0. Mulai di sini: komputer dan terminal yang digunakan

Mulai tutorial dari awal berarti mengikuti langkah pemakaian dari awal. Pada
laptop ini backend dan CA sudah terpasang; **lewati Bagian 9**. CA baru hanya
untuk instalasi lingkungan yang benar-benar baru. Setiap komputer Windows baru
mendapat sertifikat perangkat dari CA yang sama.

### 0.1 Arti host, VM, endpoint, dan dashboard

| Istilah | Maksudnya pada sistem ini | Tempat mengetik / membuka |
|---|---|---|
| HOST | Laptop Linux fisik yang menjalankan semua VM; folder proyek ada di `/home/lui/vanguard` | Terminal laptop Linux |
| VM | Komputer virtual yang berjalan di dalam host; masing-masing punya OS, file dan terminal sendiri | Terminal sesudah SSH atau console VM |
| VM-CA | Layanan penerbit dan pencabut sertifikat perangkat | `ubuntu@vm-ca:~$` |
| VM-SERVER | Pemeriksa akses, WireGuard dan gateway | `ubuntu@vm-server:~$` |
| VM-ADMIN | Layanan aplikasi dashboard admin | `ubuntu@vm-admin:~$` |
| Endpoint | PC/laptop Windows yang akan mendapat akses | PowerShell Windows, Run as administrator |
| Dashboard | Halaman web untuk admin mengelola perangkat/akun/izin | Browser host → `https://192.168.100.40:5000` |
| `.venv` | Lingkungan Python proyek di host; bukan nama aplikasi pada semua VM | `/home/lui/vanguard/.venv/bin/python` |
| Profil | File JSON yang mengatur alamat layanan, trust dan mode akses endpoint | Dibuat/disiapkan admin lalu dipakai Windows |

### 0.2 Kenali prompt dan folder sebelum menyalin perintah

Prompt adalah tulisan sebelum kursor; **jangan ikut menyalin prompt atau tanda `$`**.
`~` berarti folder home akun yang sedang dipakai. `~/vanguard` berarti folder proyek.
Folder home host dan folder home VM adalah lokasi berbeda.

| Yang terlihat | Artinya | Langkah berikut |
|---|---|---|
| `lui@lui-Vostro-15-3510:~$` | Terminal host, masih di home | Jalankan `cd /home/lui/vanguard` |
| `lui@lui-Vostro-15-3510:~/vanguard$` | Terminal host sudah di proyek | Perintah `scripts/...` dan `.venv/...` dapat dijalankan |
| `ubuntu@vm-server:~$`, `ubuntu@vm-ca:~$`, atau `ubuntu@vm-admin:~$` | Sudah masuk VM melalui SSH | Jalankan perintah khusus VM itu; jangan ulang helper login host |
| `PS C:\...>` | PowerShell Windows | Jalankan blok bertanda WINDOWS |

**HOST — buka terminal baru pada laptop Linux**, lalu:

```bash
cd /home/lui/vanguard
pwd
ls -l .venv/bin/python scripts/export_endpoint_public.py
.venv/bin/python --version
```

Hasil `pwd` harus `/home/lui/vanguard`; Python harus menampilkan versinya.
Jalankan `cd` lagi pada setiap terminal host baru. Jika prompt sudah `ubuntu@vm-*`,
ketik `exit` untuk kembali dari SSH ke host atau buka terminal host baru.

Jika `.venv/bin/python` tetap tidak ditemukan setelah masuk folder yang benar,
berhenti dan periksa instalasi proyek; jangan membuat ulang CA/VM. Pada host
baru, langkah instalasi Python tersedia di Bagian 9. File `state/` berisi bahan
lokal, sehingga clone GitHub baru tidak otomatis memiliki inventory/sertifikatnya.

**Cara membaca contoh:** `/PATH/root.crt` berarti “isi alamat file root.crt yang
benar”, bukan folder yang harus dibuat bernama PATH. `ID_PERANGKAT`, `IP_TUNNEL`
dan tulisan kapital serupa harus diisi sesuai data admin. Bagian 1.1 di bawah
memakai lokasi nyata pada host ini supaya tidak perlu menebak `/PATH`.

### 0.2.1 Jika lupa sedang berada di komputer/folder mana

**Terminal Linux (host atau VM):** jalankan tiga perintah baca ini satu per satu:

```bash
hostname
pwd
ls -lah
```

- `hostname`: nama komputer. `vm-ca`, `vm-server`, `vm-admin` berarti terminal VM.
- `pwd`: alamat folder yang sedang dibuka oleh terminal, misalnya `/home/lui`.
- `ls -lah`: isi folder tersebut, termasuk file tersembunyi seperti `.venv`.

`cd` berpindah folder pada terminal itu saja. Membuka file manager tidak otomatis
mengubah folder terminal. Menutup terminal tidak menghapus file, tetapi variabel
seperti `$vg` atau `VG_SSH_USER` tidak otomatis tersedia pada terminal baru.

**HOST — cara kembali ke proyek dari folder mana pun:**

```bash
cd /home/lui/vanguard
pwd
```

`state/endpoint-public-...` adalah path relatif: dihitung dari folder terminal.
`/home/lui/vanguard/state/endpoint-public-...` adalah path absolut: menunjuk tempat
yang sama dari folder mana pun **pada host itu**. File host tidak otomatis muncul
di VM atau Windows; transfer dilakukan pada langkah yang dijelaskan di bawah.

**Cara menyalin perintah:** salin isi kotak kode, tanpa prompt `$`/`PS ...>`.
Jalankan perintah satu per satu dan periksa hasilnya. Untuk perintah interaktif
seperti `configure`, tunggu pertanyaan, isi jawabannya, baru lanjut perintah lain.
Jangan menempel baris perintah berikutnya sebagai jawaban pertanyaan. Pada blok
Python `<<'NAMA'`, salin seluruh blok sampai baris penutup `NAMA`.

### 0.2.2 Peta lokasi file yang sering dipakai

| File/folder | Berada di komputer mana | Cara menggunakan |
|---|---|---|
| `/home/lui/vanguard` | Host Linux | Folder proyek; tempat menjalankan skrip |
| `/home/lui/vanguard/docs/MODUL_PENGGUNAAN_VANGUARD.html` | Host Linux | Manual yang dibuka lewat browser |
| `/home/lui/vanguard/downloads` | Host Linux | EXE/ZIP rilis; pilih versi terbaru menurut README downloads |
| `/home/lui/vanguard/state/endpoint-public-...` | Host Linux | Hasil ekspor trust/profil; akhiran folder berbeda setiap ekspor |
| `/home/lui/vanguard/state/lab/inventory.json` | Host Linux saja | Dibaca helper otomatis; jangan unggah atau salin ke endpoint |
| `/home/lui/VanGuard-Privat` | Host Linux saja | Inventaris credential dan backup privat; bukan bahan transfer pengguna |
| `/etc/vanguard/root.crt` | Masing-masing VM layanan | Root publik yang digunakan layanan pada VM itu |
| `/etc/vanguard/endpoint-profile.json` | VM-ADMIN | Profil aktif; helper menyalin versi publiknya ke host |
| `C:\Program Files\VanGuardTrust` | Windows endpoint | Tempat menyimpan bahan publik dari admin |
| `C:\Program Files\VanGuardEndpoint\VanGuard.bat` | Windows endpoint | Perintah aplikasi setelah EXE diinstal |
| `C:\Program Files\VanGuardEndpointData\identity\request.json` | Windows endpoint, alur manual `init` | Request yang dikirim ke dashboard admin |
| `C:\Program Files\VanGuardEndpointData\enrollment-request.json` | Windows endpoint, wizard per-device | Request wizard; gunakan Bagian 7 |

`state` dan `VanGuard-Privat` menyimpan data penting. Jangan menyalin seluruh folder
ke USB/GitHub. Untuk konfigurasi endpoint, ambil hanya file publik dari folder
hasil ekspor yang berhasil. Request/bundle mengikuti perangkat asalnya.

### 0.2.3 Membuka folder tanpa mengingat perintah terminal

**HOST Linux:** buka aplikasi **Files**, tekan **Ctrl+L**, tempel alamat lengkap,
lalu Enter. Contoh alamat: `/home/lui/vanguard/state`. Pilih folder
`endpoint-public-...` yang tercetak saat ekspor. Alternatif lewat terminal host:

```bash
xdg-open /home/lui/vanguard/state
```

Untuk membaca manual lewat browser host:

```bash
xdg-open /home/lui/vanguard/docs/MODUL_PENGGUNAAN_VANGUARD.html
```

`xdg-open` memerlukan desktop grafis; jangan menjalankannya di terminal SSH VM
untuk membuka folder laptop. Pada host tanpa desktop, gunakan `ls -lah`.

**WINDOWS:** tekan **Win+E** untuk membuka File Explorer, tekan **Ctrl+L**, lalu
masukkan `C:\Program Files\VanGuardTrust` dan Enter. Jika belum ada, foldernya
akan dibuat pada Bagian 2.2. Alamat Linux `/home/lui/...` tidak berlaku di Windows.

### 0.3 Nyalakan backend, lalu buka terminal VM

**HOST — dari `/home/lui/vanguard`:**

```bash
virsh -c qemu:///system list --all
```

Untuk tiap VM yang masih `shut off`, jalankan baris yang sesuai:

```bash
virsh -c qemu:///system start VM-CA
virsh -c qemu:///system start VM-SERVER
virsh -c qemu:///system start VM-ADMIN
```

Lewati `start` jika sudah `running`. Tunggu boot selesai. Tiga layanan ini cukup
untuk melayani endpoint Windows fisik; VM client/attacker hanya untuk skenario lab.

Jika terminal `ubuntu@vm-ca`, `ubuntu@vm-server`, dan `ubuntu@vm-admin` sudah
terbuka, langsung lanjut Bagian 1. Jika belum, buka tiga terminal **host** dan
jalankan pada masing-masing. Baca username SSH dari inventaris privat
`/home/lui/VanGuard-Privat/KREDENSIAL_VANGUARD.md` di host; simpan isinya lokal:

```bash
cd /home/lui/vanguard
read -r -p 'Username SSH VM dari inventaris privat: ' VG_SSH_USER
# Tab CA:
ssh -F /home/lui/.ssh/vanguard_lab_config -o StrictHostKeyChecking=yes "$VG_SSH_USER@192.168.100.10"
```

Pada tab server ganti alamat terakhir menjadi `192.168.100.20`; pada tab admin
menjadi `192.168.100.40`. Isi variabel username lagi pada setiap terminal baru.
Sesudah login, jalankan `hostname` dan cocokkan peran. Tutup sesi dengan `exit`;
VM tetap hidup. File konfigurasi SSH di atas hanya tersedia pada host yang sudah
disiapkan. Jika host key berubah, verifikasi lewat console sebelum melanjutkan.

Urutan setelah ini: **Bagian 1** periksa layanan dan ambil profil → **Bagian 2**
install Windows serta buat request → **Bagian 3** admin setujui → **Bagian 4**
import/login/connect → **Bagian 5** uji izin → **Bagian 6** logout/revoke dan audit.
Untuk mode internet terkelola (schema2), ikuti **Bagian 8 sebelum init/enrollment**
pada Bagian 2.2; jangan mengaktifkan lockdown sebelum jalur server teruji.

## 1. Persiapan admin

**Tempat kerja:** HOST = laptop Linux; VM = mesin layanan; WINDOWS = PowerShell
**Run as administrator**; DASHBOARD = browser admin pada jalur management.

| Layanan lab | Alamat |
|---|---|
| CA | 192.168.100.10:8080, HTTPS |
| Server admission / WireGuard | 192.168.100.20:8081 HTTPS / UDP51820 |
| Dashboard admin | https://192.168.100.40:5000 |
| Tunnel server | 10.8.0.1 |

1. Ikuti Bagian 0 sampai ketiga VM menyala dan terminalnya terbuka.
   Lab ini memakai CA existing; jangan generate CA baru untuk setiap komputer.
2. Di setiap terminal VM, periksa `timedatectl status` dan `df -h`, lalu
   jalankan **hanya perintah sesuai VM tersebut**:

   | Terminal | Perintah yang harus menghasilkan `active` |
   |---|---|
   | VM-CA | `sudo systemctl is-active vanguard-ca` |
   | VM-SERVER | `sudo systemctl is-active wg-quick@wg0 vanguard-server vanguard-daemon` |
   | VM-ADMIN | `sudo systemctl is-active vanguard-admin` |

   Jika ada `failed`/`inactive`, periksa status unit tersebut sebelum melanjutkan.

3. Di **VM-ADMIN**, pastikan ketiga pemeriksaan menghasilkan HTTP200 dan `ready`:

   ```bash
   curl --fail --connect-timeout 3 --max-time 8 --cacert /etc/vanguard/root.crt \
     https://192.168.100.10:8080/readyz
   curl --fail --connect-timeout 3 --max-time 8 --cacert /etc/vanguard/root.crt \
     https://192.168.100.20:8081/readyz
   curl --fail --connect-timeout 3 --max-time 8 --cacert /etc/vanguard/root.crt \
     https://192.168.100.40:5000/readyz
   ```

4. Siapkan untuk setiap PC: `profile.json`, `root.crt`, fingerprint root, public
   key WireGuard server, device ID unik, IP tunnel kosong, dan akun karyawan.
   Verifikasi fingerprint/key melalui admin tepercaya. Password dibagikan privat.
5. Pastikan endpoint dapat mencapai server TCP8081 dan UDP51820. Installer
   Windows tidak menyiapkan jaringan host, backend Linux, atau izin aplikasi.

**IP tunnel bukan IP LAN.** Lab mencadangkan10.8.0.2/.3/.4; periksa registry sebelum
mengalokasikan IP lain. PC berbeda harus mempunyai ID dan kunci berbeda.

### 1.1 Ambil profil yang sudah aktif pada lab ini

**Jalur normal untuk sistem existing:** gunakan profil aktif VM-ADMIN. Pada
pemeriksaan 10 November, profil ini **schema2 (internet terkelola)**. Generator
`prepare_endpoint_pilot.py` menghasilkan schema1; jangan menjalankannya hanya
karena ingin menambah komputer pada sistem yang sudah bekerja.

**HOST — terminal lokal, bukan shell VM:** jalankan dua baris ini:

```bash
cd /home/lui/vanguard
.venv/bin/python scripts/export_endpoint_public.py
```

Helper mengambil username, port dan konfigurasi SSH masing-masing VM langsung
dari `state/lab/inventory.json`; tidak ada pertanyaan username dan tidak perlu
mengisi `VG_SSH_USER`. File inventory privat tetap pada host. CA, server dan
admin harus menyala dengan SSH siap dan akses sudo noninteraktif yang sudah
disiapkan. Jika clone baru belum memiliki inventory, helper berhenti dengan
petunjuk; jangan membuat akun atau mengganti kunci untuk memaksa lolos.

Hasil sukses menampilkan **Folder hasil tervalidasi**, mode/schema, fingerprint
root dan public key WireGuard server. Folder baru ada di
`/home/lui/vanguard/state/endpoint-public-.../`, berisi tepat:

- `root.crt`: sertifikat root publik;
- `server-wg.pub`: public key WireGuard server;
- `profile.json`: profil aktif yang telah dicocokkan dengan root dan key server.

Helper memeriksa ketiga bahan sebelum membuat folder hasil. Bila SSH/validasi
gagal, hentikan langkah ini dan periksa layanan; jangan memakai folder kosong
dari percobaan lama. Folder baru tidak menimpa hasil sebelumnya. Catat alamat
folder yang dicetak; tidak perlu menjalankan `mktemp` atau mengatur variabel shell.

Cocokkan fingerprint lewat jalur admin tepercaya. Salin `profile.json` dan
`root.crt` dari folder sukses ke Windows pada Bagian 2.2. Catat fingerprint/
public key untuk configure. Kunci privat, token dan password tidak diekspor.

Jika contoh lama menghasilkan `VG_SSH_USER@...: Permission denied (publickey)`,
nama variabel telah dipakai sebagai username literal. Gunakan helper di atas;
pesan itu tidak membuktikan CA atau password VM rusak.

#### 1.1.1 Menemukan hasil ekspor setelah terminal ditutup

Folder hasil tetap ada walaupun terminal ditutup. **HOST — cari daftar folder:**

```bash
ls -ldt /home/lui/vanguard/state/endpoint-public-*/
```

Urutan tersebut berdasarkan waktu perubahan folder, **bukan jaminan profilnya
paling benar**. Pilih folder dari ekspor yang berhasil dan cocokkan dengan catatan
admin; jangan otomatis memilih folder terbaru dari percobaan yang gagal.

Contoh hasil ekspor yang benar-benar diverifikasi pada **11 November 2026**:
`/home/lui/vanguard/state/endpoint-public-u8wsu2hh`. Pada host ini, cek isinya:

```bash
ls -lh /home/lui/vanguard/state/endpoint-public-u8wsu2hh/
```

Harus ada tiga file tidak kosong: `root.crt`, `profile.json`, `server-wg.pub`.
Nama `u8wsu2hh` adalah hasil sesi tersebut, bukan nama wajib. Jika ekspor baru
mencetak nama lain, gunakan nama baru itu secara konsisten. Bila CA/profil berubah,
lakukan ekspor ulang dan validasi; jangan memakai salinan lama hanya karena ada.

**HOST — lihat kembali mode, fingerprint dan public key dari folder pilihan:**

```bash
cd /home/lui/vanguard
.venv/bin/python - /home/lui/vanguard/state/endpoint-public-u8wsu2hh <<'PYTRUST'
import sys
from pathlib import Path
from vanguard.profile import load_profile
folder = Path(sys.argv[1])
profile = load_profile(folder / 'profile.json', folder / 'root.crt')
key = (folder / 'server-wg.pub').read_text().strip()
if key != profile['server_public_key']:
    raise SystemExit('Public key tidak cocok; hentikan dan periksa ekspor.')
print('Folder:', folder)
print('Mode/schema:', profile['schema'])
print('Fingerprint root:', profile['root_sha256'])
print('Public key server:', key)
PYTRUST
```

Ubah hanya alamat folder pada baris pertama pemanggilan Python jika menggunakan
hasil lain. Keluaran ini hanya berisi nilai publik. Jika muncul error/file hilang,
berhenti dan jalankan ekspor lagi setelah layanan siap.

#### 1.1.2 Memindahkan file publik dari host ke Windows

1. **HOST:** buka folder hasil sukses melalui Files. Pilih hanya `root.crt`,
   `profile.json`, dan `server-wg.pub`. Salin ke USB atau media transfer yang
   disetujui; beri folder media nama `VanGuardTrust` agar mudah ditemukan.
2. Catat fingerprint yang sudah diverifikasi admin melalui jalur tepercaya.
   Jangan menjadikan file yang datang dari media transfer sebagai satu-satunya
   sumber kepercayaan tanpa pembandingan dengan admin.
3. **WINDOWS:** buka media tadi lewat File Explorer. Sesudah instalasi EXE,
   siapkan folder tujuan pada Bagian 2.2, lalu salin tiga file ke sana.
4. File `request.json` dibuat **setelah** init pada Windows. Bundle sertifikat
   baru tersedia **setelah** admin menyetujui request. Keduanya bukan keluaran
   helper ekspor, jadi tidak perlu dicari di folder `endpoint-public-...`.

### 1.2 Opsional: buat kandidat profil aplikasi internal baru

Gunakan bagian ini hanya jika admin memang memilih **mode aplikasi internal**.
Pada host existing tersedia `state/deployment/root.crt` dan
`state/deployment/server-wg.pub`; salinan keduanya dicocokkan dengan VM aktif pada
10 November. Periksa kembali jika CA/server berubah. Salinan ini tidak tersedia
pada clone GitHub baru; gunakan bahan publik terverifikasi dari Bagian 1.1.

**HOST — contoh lengkap dengan lokasi pada komputer ini:**

```bash
cd /home/lui/vanguard
.venv/bin/python scripts/prepare_endpoint_pilot.py \
  --root state/deployment/root.crt \
  --server-public-key-file state/deployment/server-wg.pub \
  --output state/profil-aplikasi-pertama
```

Hasil berada di `/home/lui/vanguard/state/profil-aplikasi-pertama/`: profil,
root publik, rencana jaringan dan kandidat env admin. Jika folder sudah ada,
generator menolak menimpa; gunakan nama folder baru, jangan hapus konfigurasi
existing. Generator tidak membuat CA, menerbitkan sertifikat, memasang firewall,
atau menambahkan peer. Alamatnya mengikuti lab pada tabel layanan.

**Hanya bila admin memutuskan menerapkan profil baru**, buat backup konfigurasi/
database VM-ADMIN yang konsisten, pasang profil di `/etc/vanguard/endpoint-profile.json`
dengan owner root:vanguard dan mode0640, pertahankan env lain saat mengatur
`VANGUARD_CLIENT_PROFILE`, lalu restart admin dan ulang readiness. Bundle dan
profil endpoint harus cocok. Ini perubahan mode sistem, bukan syarat menambah PC
pada profil existing.

**PC fisik pada pilot .50/24:** host Linux192.168.50.10 meneruskan koneksi ke
backend .100/24. Operator menyiapkan forwarding dan jalur balik, membatasi endpoint
ke TCP8081/UDP51820. CA, dashboard dan aplikasi internal tidak dibuka langsung
ke LAN. Bila route belum ada, di Windows gunakan adapter yang sudah diperiksa:

```powershell
Get-NetIPConfiguration
# Ganti INDEX_ADAPTER dengan angka adapter LAN/Wi-Fi yang benar.
New-NetRoute -DestinationPrefix '192.168.100.20/32' -InterfaceIndex INDEX_ADAPTER `
  -NextHop '192.168.50.10' -PolicyStore ActiveStore
```

Route ini hilang setelah reboot. Jangan menambahkan route kedua jika sudah ada;
periksa kembali jaringan sebelum connect.

## 2. Install Windows dan buat permintaan perangkat

Target paket: Windows10 x64 build19044/19045 atau Windows11 x64. Instalasi perlu
hak administrator lokal. Akun VPN tetap terpisah dari akun admin Windows.

### 2.1 Install EXE umum

1. Unduh EXE terbaru dari [halaman unduhan](../downloads/README.md)
   dari branch `feature/2026-10-22-physical-endpoints`, folder `downloads`, tombol
   **Download raw file**. Tidak perlu GitHub CLI.
2. Cocokkan hash dengan [SHA256SUMS](../downloads/SHA256SUMS) dan nilai tepercaya
   dari admin:

   ```powershell
   Get-FileHash '.\NAMA_FILE_INSTALLER.exe' -Algorithm SHA256
   ```

   Untuk EXE 0.1.15 yang tercatat saat panduan ini diperbarui, SHA-256 adalah
   `01bdfd418cf8ab97543b172d7abaedb1baba507ac215900f895eb18ced591031`.
   Pastikan juga nilai tersebut cocok dengan checksum yang diverifikasi admin.

3. Klik kanan EXE → **Run as administrator**, setujui UAC, tunggu selesai.
   Python, WireGuard dan dependensi disertakan. Jika kebijakan Windows memblokir
   EXE yang belum ditandatangani ini, minta admin meninjau; jangan matikan proteksi.

| Kode hasil | Tindakan |
|---|---|
| 0 | Tahap selesai; EXE umum baru memasang aplikasi |
| 20 | Wizard per-device menunggu bundle persetujuan admin |
| 3010 | Restart Windows, lalu jalankan installer yang sama |
| 1 | Catat error dan periksa; jangan hapus key/config |

**EXE umum belum membuat sertifikat, tunnel atau blokir internet.** Jika admin
memberikan paket per-device, ikuti Bagian7; jangan ulang init pada identitas wizard.

### 2.2 Configure dan buat request

**WINDOWS — setelah EXE selesai terpasang:** klik Start, cari **PowerShell**,
klik kanan → **Run as administrator**, lalu setujui UAC. Terminal bertuliskan
`ubuntu@vm-*` atau `lui@...` adalah terminal Linux, sehingga blok berikut
harus dijalankan pada PC Windows yang akan didaftarkan.

Jalankan ini untuk menyiapkan dan membuka folder trust publik:

```powershell
New-Item -ItemType Directory -Path 'C:\Program Files\VanGuardTrust' -Force | Out-Null
explorer.exe 'C:\Program Files\VanGuardTrust'
```

Lewat File Explorer, salin `root.crt`, `profile.json`, dan `server-wg.pub` dari
media transfer ke folder yang baru terbuka. Jika file lama sudah ada dan berbeda,
berhenti untuk review admin; jangan menimpa trust existing secara sembarang.
Lalu kembali ke **PowerShell Administrator yang sama** dan periksa:

```powershell
Get-Item 'C:\Program Files\VanGuardTrust\root.crt', 'C:\Program Files\VanGuardTrust\profile.json', 'C:\Program Files\VanGuardTrust\server-wg.pub'
Get-Item 'C:\Program Files\VanGuardEndpoint\VanGuard.bat'
```

Ketiga file trust harus terlihat dan ukurannya tidak nol. Jika `Cannot find path`,
periksa tempat menyalin file. Jika `VanGuard.bat` tidak ditemukan, selesaikan
instalasi EXE dahulu; jangan lanjut configure.

Sekarang jalankan **configure saja**, lalu jawab pertanyaannya:

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg configure
```

| Pertanyaan program | Yang diketik sebagai jawaban |
|---|---|
| Path profil publik | `C:\Program Files\VanGuardTrust\profile.json` |
| Path root.crt | `C:\Program Files\VanGuardTrust\root.crt` |
| Fingerprint SHA256 Root CA | Nilai 64 karakter hex yang telah dikonfirmasi admin dari hasil ekspor |
| Public key WireGuard server | Nilai public key server yang telah dikonfirmasi admin |

Pada jawaban interaktif path, tempel alamatnya tanpa tanda kutip luar. Pada
perintah PowerShell, path yang mengandung spasi harus diberi tanda kutip seperti
contoh. Jangan mengetik nama variabel atau perintah berikutnya sebagai jawaban.
Sesudah configure selesai dan prompt `PS ...>` muncul lagi, baru jalankan:

```powershell
& $vg status
& $vg diagnose
```

**Hasil wajib:** konfigurasi lengkap dan server dapat diperiksa. Jika menutup
PowerShell lalu membuka lagi, isi ulang `$vg = Join-Path ...` sebelum memakai
`& $vg`. Jangan mengganti root lama atau mengabaikan TLS agar lolos.

Untuk **perangkat baru**, jalankan:

```powershell
& $vg init
```

Masukkan device ID dan IP tunnel dari admin. Kirim **hanya** berkas berikut:

`C:\Program Files\VanGuardEndpointData\identity\request.json`

**WINDOWS — sesudah init sukses**, buka lokasi request dengan:

```powershell
explorer.exe 'C:\Program Files\VanGuardEndpointData\identity'
```

Pilih `request.json` pada folder yang terbuka. Jika folder tidak terbuka,
tekan Ctrl+L, masukkan
`C:\Program Files\VanGuardEndpointData\identity`, lalu pilih `request.json`.
Kirim hanya file itu kepada admin. Jangan menjalankan init ulang hanya karena
lupa lokasi file; identitas yang sudah dibuat harus tetap dipakai.

Kunci X.509 dan WireGuard dibuat di PC. Jangan kirim `identity.key`, `wg.key`,
token, atau seluruh folder identity. Jika memakai schema2, aktifkan policy
Bagian8 **sebelum** init/enrollment. Perangkat yang sudah punya identitas melewati init.

## 3. Daftarkan perangkat di dashboard

**DASHBOARD ADMIN:**

1. Buka `https://192.168.100.40:5000` melalui jalur management yang diizinkan.
   Pastikan sertifikat HTTPS dipercaya dari root yang sudah diverifikasi.
2. Login admin menggunakan password dan TOTP authenticator.
3. Buat atau pilih **akun karyawan**. Bagikan kredensial melalui jalur privat.
4. Unggah request dari PC; pilih akun karyawan dan metadata perangkat. Cocokkan
   device ID, IP tunnel dan permintaan dari PC asal.
5. Tunggu status **registered**. Jika pending, perbaiki penyebab lalu retry.
6. Unduh **bundle perangkat**, kirim ke PC asal melalui jalur tepercaya.

**Agar file request/bundle mudah ditemukan:** di HOST admin, siapkan folder
transfer khusus (isinya hanya request dan bundle publik yang dipilih):

```bash
mkdir -p /home/lui/Downloads/VanGuard
xdg-open /home/lui/Downloads/VanGuard
```

Salin request dari PC asal ke subfolder bernama device ID agar beberapa PC tidak
tertukar. Pada dialog upload browser, buka folder perangkat itu dan pilih
`request.json`. Setelah mengunduh bundle, tekan **Ctrl+J** pada browser →
**Tampilkan dalam folder**. Catat lokasi hasil; gunakan Save As atau pindahkan
bundle ke subfolder perangkat yang sama. Nama bundle mengikuti hasil dashboard;
jangan menganggap semua unduhan bernama `approval.zip`.

Kirim bundle ke PC yang membuat request. Simpan pada folder yang mudah ditemukan
pengguna, misalnya folder `VanGuardTransfer` yang dibuat sendiri melalui File
Explorer. Lokasi folder Downloads dapat berbeda antar akun/perangkat; gunakan
alamat yang benar-benar terlihat di Explorer, bukan menebak nama akun.

CA menerbitkan sertifikat dari CSR; root CA tidak dibuat ulang. Registrasi dan
login karyawan saja **belum** menambahkan peer atau memberikan akses VPN.

## 4. Import, login, connect dan logout

**WINDOWS:** buka PowerShell Administrator. Untuk endpoint dari EXE umum:

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg import-bundle
```

Jawab pertanyaan lokasi bundle dan tunggu selesai. Setelah prompt PowerShell
kembali, jalankan perintah berikut satu per satu; tunggu setiap langkah selesai:

```powershell
& $vg status
& $vg diagnose
& $vg login
& $vg connect
```

- Saat import, buka File Explorer dan temukan ZIP bundle yang diterima. Gunakan
  **Copy as path/Salin sebagai jalur**, lalu tempel sebagai jawaban program dan
  hapus tanda kutip luar bila ikut tersalin. Bundle harus cocok dengan profil,
  root dan kunci PC yang membuat request. Jangan tempel alamat folder saja.
- Saat login, masukkan akun karyawan dan password secara interaktif.
- Biarkan terminal **connect** terbuka untuk renewal lease.
- Server menambah peer hanya setelah sesi dan enam pemeriksaan perangkat lolos.
  Jangan menambahkan peer statis melalui GUI WireGuard.

**Mengakhiri pemakaian:** Ctrl+C pada terminal connect. Atau di terminal admin kedua:

```powershell
$vg = Join-Path $env:ProgramFiles 'VanGuardEndpoint\VanGuard.bat'
& $vg disconnect
& $vg logout
```

Disconnect menutup tunnel; logout mencabut sesi server. Jika server tidak
terjangkau, pencabutan **belum terkonfirmasi**: retry setelah layanan pulih.
Jika cleanup gagal, pertahankan config sampai tunnel berhenti dan kepemilikannya
jelas. Setelah reboot, periksa route, login bila sesi habis, lalu connect kembali.

**Repair/reinstall:** disconnect dahulu, lalu jalankan installer tepercaya yang
sama; pertahankan key/config. Jika lockdown aktif, ikuti recovery Bagian8 dahulu.
Uninstall melalui `C:\Program Files\VanGuardEndpointData\tools\Uninstall-VanGuard.bat`
mempertahankan identitas serta Python/WireGuard bersama; tetap lakukan revoke
oleh admin bila perangkat tidak akan digunakan lagi.

**Client Ubuntu yang sudah terdaftar:**

```bash
sudo /opt/vanguard/venv/bin/vanguard-client login --username AKUN_KARYAWAN
sudo systemctl restart vanguard-client
```

Jangan jalankan connect foreground bersamaan dengan service. Sertifikat yang
kedaluwarsa perlu penggantian identitas oleh admin; login tidak memperpanjangnya.

## 5. Beri izin aplikasi dan uji koneksi

**VM-SERVER:** sediakan aplikasi uji dan aktifkan firewall application-policy
serta `VANGUARD_RESOURCE_POLICY`. Profil client saja tidak memberi izin aplikasi.

Untuk demo, siapkan folder publik `/srv/vanguard-pilot-demo` beserta `index.html`,
lalu jalankan jika port/unit belum digunakan:

```bash
sudo systemd-run --unit=vanguard-pilot-demo --uid=vanguard \
  --property=NoNewPrivileges=yes --property=ProtectSystem=strict \
  --property=ProtectHome=yes /usr/bin/python3 -m http.server 8082 \
  --bind 10.8.0.1 --directory /srv/vanguard-pilot-demo
```

Tambahkan grant ke **kandidat** kebijakan server, pertahankan grant sah lainnya:

```json
{"grants":[{"device_id":"ID_PERANGKAT","username":"AKUN_KARYAWAN","resource":"internal-demo","address":"10.8.0.1","protocol":"tcp","port":8082}]}
```

Validasi kandidat sebelum dipasang pada path `VANGUARD_RESOURCE_POLICY`:

```bash
sudo /opt/vanguard/venv/bin/python -c \
  "from vanguard.resource_policy import load_policy; print('valid; grants:',len(load_policy('/etc/vanguard/resource-policy.candidate.json')))"
```

Operator mempublikasikan file tervalidasi dengan penggantian atomic, owner root
mode0600. Jangan mengganti policy aktif dengan contoh kosong atau menambah elemen
nft manual. Gate harus sudah aktif sebelum uji.

**WINDOWS setelah connect:**

```powershell
curl.exe --connect-timeout 3 --max-time 8 http://10.8.0.1:8082/
```

| Uji | Hasil yang diharapkan |
|---|---|
| Akun + perangkat sah + grant sesuai | Aplikasi dapat diakses lewat tunnel |
| Tanpa grant, port lain, atau akses LAN langsung | Ditolak |
| Logout/revoke saat koneksi aktif | Akses terkait berhenti; perangkat lain tetap bekerja |
| Sertifikat expired/revoked atau akun nonaktif | Admission ditolak |

Periksa lease, peer, handshake, dan hasil HTTP **secara terpisah**. Peer terpasang
belum membuktikan akses aplikasi. Hentikan demo setelah pengujian:
`sudo systemctl stop vanguard-pilot-demo`.

## 6. Cabut akses, ganti identitas dan simpan audit

| Tindakan admin | Langkah |
|---|---|
| Cabut satu perangkat | Pilih perangkat → alasan → **Cabut akses & sertifikat**. Tunggu `revoked`; pastikan peer hilang dan akses ditolak |
| Status `revoking` | Perbaiki dependency → **Ulangi workflow**. Belum dianggap selesai |
| Nonaktifkan karyawan | Nonaktifkan akun. Sesi/akses akun dibatalkan; sertifikat tidak otomatis dicabut |
| Ganti identitas expired/hilang | Cabut identitas lama; buat ID dan kedua key baru di endpoint; gunakan form penggantian pada riwayat perangkat. Akun/IP diwariskan |
| Lihat aktivitas | **Aktivitas admin** → filter waktu WIB, pelaku atau perangkat → **Tampilkan** |
| Arsipkan aktivitas | **Simpan arsip aktivitas** → **Arsip** → unduh ZIP dan cocokkan SHA256 |

Simpan bukti/backup secara privat. Arsip tidak menghapus log asli. Jangan reset
CA, mengembalikan index/CRL lama, atau menimpa kunci lama untuk memaksa recovery.
Sebelum upgrade, backup konsisten saat service terkait berhenti; verifikasi arsip
sebelum mengubah runtime. Pemulihan kode tidak berarti rollback histori CA/database.

## 7. Opsional: satu BAT atau EXE per perangkat

Jalur ini menggantikan konfigurasi manual Bagian2.2. Admin menyiapkan profil,
root dan alokasi; pengguna menjalankan wizard yang sama sampai connect.

**HOST, dari folder proyek:** contoh di bawah adalah template build opsional;
isi semua `/PATH/...` dari lokasi hasil ekstraksi sendiri. Ambil folder `wheels` dan `runtimes` dari
[template offline](../downloads/README.md), verifikasi checksum, lalu:

```bash
cd /home/lui/vanguard
.venv/bin/python scripts/build_endpoint_package.py \
  --wheelhouse /PATH/windows-wheels --runtime-directory /PATH/runtime-installers \
  --output /PATH/paket-perangkat-baru \
  --profile /PATH/profile.json --root /PATH/root.crt \
  --device-id ID_PERANGKAT --tunnel-ip IP_TUNNEL \
  --expected-root-sha256 FINGERPRINT_ROOT_64_HEX \
  --expected-server-key PUBLIC_KEY_WIREGUARD_SERVER
```

Gunakan wheel/runtime yang sesuai versi paket. Satu alokasi hanya untuk satu PC;
paket tidak memuat password, token management atau private key.

**WINDOWS:** ekstrak seluruh paket → jalankan `Setup-VanGuard.bat` → setujui UAC.
Kirim `C:\Program Files\VanGuardEndpointData\enrollment-request.json` ke admin.
Admin melakukan Bagian3. Masukkan path bundle ke wizard, atau simpan sebagai
`C:\Program Files\VanGuardEndpointData\approval.zip` lalu jalankan BAT yang sama.
Lanjutkan login dan connect. Exit20 berarti menunggu approval, bukan gagal.

**Membungkus menjadi EXE:** salin paket dan folder `deploy/endpoint/exe` ke komputer
build Windows admin. Jalankan:

```powershell
& 'C:\Program Files\VanGuardBuild\source\Build-Exe.ps1' `
  -Package 'C:\Program Files\VanGuardBuild\paket-perangkat-baru' `
  -Output 'C:\Program Files\VanGuardBuild\Setup-Perangkat-Baru.exe'
Get-FileHash 'C:\Program Files\VanGuardBuild\Setup-Perangkat-Baru.exe' -Algorithm SHA256
```

Folder `source` berisi `Build-Exe.ps1`, `VanGuardSetup.cs` dan `app.manifest`.
Bagikan EXE dan checksum tepercaya; simpan metadata build. EXE per-device memakai
alur wizard di atas, sedangkan EXE umum unduhan tetap perlu configure manual.

## 8. Opsional: internet terkelola tanpa konfigurasi router

**Mode ini memerlukan gateway Linux dan policy Windows.** Linux saja tidak dapat
memblokir koneksi PC yang langsung menuju router. Gunakan endpoint terkelola;
admin lokal penuh tetap dapat mengubah firewall. Mode ini IPv4, IPv6 diblok.

1. **Operator Linux:** siapkan uplink WAN, IPv4 forwarding, NAT gateway, jalur
   admission yang dapat dijangkau dan jalur management/pemulihan. Backup dahulu.
   Generate kandidat firewall lab, ganti `eth0` dengan uplink yang benar:

   ```bash
   python3 deploy/firewall.py server --management-ip 192.168.100.1 \
     --windows-client --application-policy --internet-uplink eth0 --print-only \
     > gateway-internet.candidate.nft
   sudo nft --check --file gateway-internet.candidate.nft
   ```

   Review subnet/aturan, lalu terapkan dalam maintenance dengan console dan
   rollback tersedia. Perintah di atas **hanya validasi**, belum mengaktifkan gateway.
2. Buat `/var/lib/vanguard/server/internet-policy.json` berisi `{"grants":[]}`
   **hanya bila belum ada**, owner root mode0600. Pasang `VANGUARD_INTERNET_POLICY`
   ke path itu pada env server **dan daemon**. Pastikan path boleh ditulis unit;
   validasi dengan `vanguard.internet.load_internet_policy`, restart terencana,
   lalu periksa readiness dan nft. Jangan menimpa policy/grant lama.
3. Buat profil **schema2** dari profil sah: `allowed_ips` berisi
   `["0.0.0.0/1","128.0.0.0/1"]`, tambahkan
   `"internet":{"mode":"managed-ipv4","dns":["1.1.1.1"]}`. Validasi profil,
   pertahankan root/key/resource, pasang profil sama di admin dan endpoint.
4. **WINDOWS setelah configure, sebelum enrollment:** sediakan console dan media
   transfer request/bundle. Jalankan:

   ```powershell
   & $vg internet-preview
   & $vg internet-enable
   & $vg internet-status
   ```

   Internet langsung diblok **setelah enable berhasil**, bukan saat klik EXE umum.
   Wizard per-device schema2 menjalankan tahap ini. Endpoint domain atau GPO yang
   bertentangan ditolak; jangan memaksa atau menghapus policy organisasi.
5. Daftarkan perangkat dan import bundle (Bagian3–4). Di dashboard pilih
   **Izin internet melalui gateway → Izinkan setelah admission**. Login dan connect.
6. Uji internet/DNS, penolakan jalur langsung, logout/revoke saat TCP aktif,
   reboot dan isolasi perangkat lain. Jangan menganggap PASS hanya karena install sukses.

**Recovery:** disconnect, pastikan tunnel/service berhenti, lalu admin lokal
menjalankan `& $vg internet-recover` dan mengonfirmasi `PULIHKAN`. Ini memulihkan
policy sebelum lockdown dan dapat membuka internet langsung; **bukan revoke server**.
Jangan hapus state/backup firewall. Maintenance runtime saat lockdown aktif harus
melalui recovery terencana. Tidak ada fallback otomatis yang membuka internet.

## 9. Khusus instalasi backend dan CA baru

**Lewati bagian ini pada lab yang sudah terpasang.** Contoh otomatis berikut
khusus topologi lab lima Ubuntu22.04: CA.10, SERVER.20, CLIENT.30, ADMIN.40,
ATTACKER.50 pada192.168.100.0/24; gateway host.1. Windows adalah client tambahan,
bukan pengganti Ubuntu. Installer tidak memasang OS Windows.

### 9.1 Siapkan host dan inventory

Siapkan KVM/libvirt, media OS resmi terverifikasi, SSH operator dan storage yang
cukup. Pada HOST kosong, provisioning lima Ubuntu tersedia melalui:

```bash
sudo python3 scripts/create_lab.py --image /PATH/UBUNTU22_IMAGE.img \
  --public-key /PATH/OPERATOR_KEY.pub --operator NAMA_USER_HOST \
  --output /PATH/INVENTORY_PRIVAT_BARU
```

Jangan jalankan bila VM/jaringan tersebut sudah ada. Konfirmasi host key SSH lewat
console. Isi inventory lima role mengikuti `deploy/inventory.example.json`, lalu
jalankan `python3 scripts/ssh_preflight.py /PATH/inventory.json`; semua harus `ok`.

Di root repo commit yang disetujui, siapkan runtime dan arsip source:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -c deploy/constraints.txt .
git archive --format=tar.gz HEAD -o /PATH/vanguard-source.tar.gz
```

### 9.2 Install, generate CA dan siapkan admin

**HOST, hanya lingkungan baru:** gunakan direktori state privat yang sama untuk
semua fase. Jangan gunakan `--phase all` untuk setup ini.

```bash
.venv/bin/python scripts/deploy_lab.py /PATH/inventory.json \
  --state /PATH/STATE_PRIVAT --archive /PATH/vanguard-source.tar.gz --phase install
.venv/bin/python scripts/deploy_lab.py /PATH/inventory.json \
  --state /PATH/STATE_PRIVAT --phase configure
.venv/bin/python scripts/deploy_lab.py /PATH/inventory.json \
  --state /PATH/STATE_PRIVAT --phase admin
```

- `install`: memasang aplikasi/unit sesuai role, belum menjalankan service/firewall.
- `configure`: membuat CA pada VM-CA bila belum ada, membuat key/CSR HTTPS di tiap
  layanan, menandatanganinya, memasang root publik, token env dan identitas client Ubuntu.
- `admin`: membuat akun dashboard dan onboarding TOTP di state privat. Daftarkan
  TOTP ke authenticator; catat username/password hanya di inventaris privat.

Perintah CA yang dipakai fase configure adalah:
`sudo -u vanguard /opt/vanguard/venv/bin/vanguard-ca init`.
**Jangan menjalankannya lagi sesudah configure.** Root/private key tetap di CA;
setiap endpoint baru hanya membuat CSR dan kunci sendiri.

Di VM-CA, periksa root dan CRL yang sudah dihasilkan:

```bash
openssl x509 -in /etc/vanguard/root.crt -noout -subject -issuer -dates -fingerprint -sha256
openssl verify -check_ss_sig -CAfile /etc/vanguard/root.crt /etc/vanguard/root.crt
sudo openssl crl -in /var/lib/vanguard/ca/crl.pem -noout -lastupdate -nextupdate
```

Cocokkan fingerprint melalui console CA sebelum mempercayai salinan root. Fase
configure menyiapkan HTTPS SAN.10/.20/.40; private key HTTPS tetap pada VM asal.
Jangan memakai contoh lab untuk alamat lain tanpa mengubah SAN/routing yang sesuai.

### 9.3 Firewall dan mulai layanan

Di setiap guest, pasang nftables dan salin `deploy/firewall.py` ke
`/opt/vanguard/firewall.py`. Jalankan sesuai role:

```bash
sudo python3 /opt/vanguard/firewall.py ROLE --management-ip 192.168.100.1
# Khusus SERVER, gunakan ini sebagai pengganti baris ROLE di atas:
sudo python3 /opt/vanguard/firewall.py server --management-ip 192.168.100.1 \
  --windows-client --application-policy
```

Skrip memasang timer rollback120detik. Buka **SSH baru**, pastikan firewall aktif,
baru hentikan `vanguard-firewall-rollback.timer` pada guest tersebut. Bila gagal,
gunakan console/rollback. Siapkan policy aplikasi kosong dan env
`VANGUARD_RESOURCE_POLICY` sebelum memberi grant di Bagian5.

**HOST:**

```bash
.venv/bin/python scripts/deploy_lab.py /PATH/inventory.json \
  --state /PATH/STATE_PRIVAT --phase start
```

Layanan dimulai CA → server → admin. Sebelum admission, server harus tanpa peer:
`sudo wg show wg0 peers`. Lanjutkan pemeriksaan Bagian1, profil, lalu endpoint.
Backup CA lengkap harus menjaga root/key/index/serial/crlnumber/CRL/sertifikat
sebagai satu state konsisten; jangan memulihkan sebagian file lama.

## 10. Masalah umum dan pemeriksaan akhir

| Gejala | Tindakan |
|---|---|
| `.venv/bin/python: No such file or directory` | Di HOST jalankan `cd /home/lui/vanguard`, lalu cek `.venv/bin/python`; ikuti Bagian 0.2 |
| Inventory tidak ditemukan pada `ubuntu@vm-*` | Sudah login ke VM; helper login hanya untuk host. Lanjut pemeriksaan layanan Bagian 1 |
| `/PATH/...` tidak ditemukan | Itu placeholder. Gunakan file nyata atau ikuti pengambilan profil Bagian 1.1 |
| Readiness503/unknown | Periksa service, jam, disk dan dependency. Catat kegagalan; HTTP200 sesudah retry tidak menghapus kejadian awal |
| Configure ditolak | Cocokkan profil/root/fingerprint/key; jangan hapus trust lama untuk memaksa lolos |
| Login gagal | Periksa akun karyawan, password, status aktif dan koneksi HTTPS |
| Pending registration / exit20 | Tunggu admin; perbaiki dependency, gunakan request/key yang sama |
| Connect gagal | Periksa sertifikat, sesi, binding, route dan UDP51820; jangan pasang peer manual |
| Tunnel ada tetapi aplikasi gagal | Periksa grant resource/protokol/port dan service aplikasi |
| Sesi habis | Login kembali; renewal lease tidak memperpanjang sertifikat |
| Cleanup belum pasti | Pertahankan config; pastikan pemilik dan tunnel/service berhenti |
| Sertifikat dicabut/expired | Admin menjalankan alur penggantian identitas Bagian6 |

Sebelum serah terima, buktikan: akses sah berhasil, tanpa izin ditolak, revoke
memutus akses terkait, perangkat lain tetap bekerja, logout dan cleanup selesai.
Catat waktu, versi/OS, PASS/FAIL/BELUM_TERUJI dan lokasi bukti; jangan merekam password,
OTP, token atau private key. Simpan backup sebelum upgrade; uninstall bukan revoke.

**Referensi:** [checkpoint](CHECKPOINT.md), [API](API.md),
[keamanan](SECURITY.md), [hasil uji 0.1.15](reports/VALIDASI_0.1.15_2026-11-02.md).
**[Flowchart lengkap sistem dalam satu diagram](FLOWCHART_SISTEM_LENGKAP.md)** mencakup backend, installer, pendaftaran, akses, pencabutan, recovery dan audit.
