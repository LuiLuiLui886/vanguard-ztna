# Validasi internet terkelola Windows 11 — 28 Oktober 2026

Laporan bukti kandidat0.1.13; langkah operator tetap di
[manual tunggal Bab14.1](MODUL_PENGGUNAAN_VANGUARD.md). Hasil ini hanya untuk
VM Windows11 build26300 yang diuji, bukan sertifikasi semua edisi/build Windows.
ZIP stabil0.1.12 belum memuat mode internet baru.

## Lingkungan dan perlindungan data

Windows11 pada VM asli .100.60, Python3.13.16, WireGuard1.1.1, Secure Boot/TPM
aktif. Kandidat r8 dipasang lewat BAT offline; semua PS1/BAT cocok source
`f861464`. Legacy client0.1.9 dan identitas utama berada di direktori terpisah.
Gateway Linux memakai namespace .100.80, registry baru `server-win11-20261028`
dan CA sementara yang sama dengan uji Windows10. Database lama, index/CRL CA
serta histori pencabutan1001 dipertahankan. Identitas uji baru menggunakan serial
1002 dan .3 hanya dalam namespace uji; private key dibuat di Windows.

Backup disk24Oktober tetap ada. Backup file/config/identitas dan firewall terkini
dibuat sebelum perubahan; host hanya13GiB kosong, sehingga tidak dibuat salinan
disk penuh baru40GiB. Pemulihan dilakukan pada policy/file milik fixture,
bukan restore CA atau seluruh firewall. Backup dan raw log berada di state
lokal/guest ber-ACL, credential hanya inventaris privat. Tugas recovery berwaktu
adalah alat pengaman lab, bukan fitur auto-recovery produk.

## Bukti aktual

| Kasus | Metode | Hasil |
|---|---|---|
| Installer r8 | BAT native offline pada instalasi yang sudah ada | PASS, exit0; bukan fresh install tanpa runtime |
| Runtime final | Metadata/pip check/hash launcher+policy |0.1.13, pip check exit0, empat file hash-identik dengan paket |
| Lockdown awal | Firewall Windows dan TCP nyata | 9PASS: baseline, preview, enable, status, blok internet, bootstrap, local allow injection, rule merging, identitas belum ada |
| Reboot policy | Reboot normal, LastBootUpTime berubah | 6PASS sesudah reboot; belum uji reboot saat tunnel aktif |
| Registrasi/login | Registry+WG nyata | Tidak menambah peer sebelum admission |
| Admission/handshake | Windows11 → gateway Linux namespace | PASS, lease/peer/handshake teramati |
| Tanpa grant internet | TCP1.1.1.1:443 dan query DNS UDP baru | Ditolak; API tetap terjangkau |
| Grant internet | TCP dan DNS baru melewati tunnel | PASS |
| Revoke grant dengan TCP aktif | Stream WAN namespace terkendali | PASS, timeout teramati ≤2,68994detik; peer tetap ada |
| Regrant | Probe TCP/DNS baru | PASS |
| Renewal | Audit accepted server, lease60detik | Awal+3renewal; interval41,125/35,812/33,839detik |
| Logout/cleanup | Server session+peer, service Windows/config/marker | PASS; sesi lokal absent, service1060 dan config/marker absent |
| Reconnect | Login baru, admission/handshake dan TCP/DNS | PASS |
| Revoke sertifikat dengan TCP aktif | OpenSSL CA sementara, serial1002 | Stream reset, peer absent; batas observasi8,31048detik; lihat koreksi assertion di bawah |
| Sesudah revoke | TCP/DNS baru, fresh connect dan owner cleanup | TCP/DNS ditolak; HTTP403; service/config/marker absent |

Alamat93.184.216.34 pada uji stream hanya alamat virtual namespace WAN; tidak
menghubungi pemilik alamat tersebut. Pengukuran waktu mencakup SSH, polling,
API/CA dan timeout TCP; bukan latency kernel presisi. Host dan guest memiliki
jam masing-masing, sehingga timestamp lintas mesin tidak dipakai sebagai latency.

## Koreksi kriteria alat ukur

Runner certificate-revocation awal **FAIL** karena hanya menerima TimeoutError.
Hasil native sebenarnya mencatat ConnectionResetError, ended_at, dan peer absent.
Kriteria network-stop yang benar juga menerima reset/closed. Pemeriksaan ulang
artefak membuktikan stream awal aktif, lalu reset, peer hilang, TCP/DNS baru
ditolak, fresh admission403. **Perilaku jaringan PASS dari bukti yang diperiksa
ulang**, bukan klaim rerun yang tidak dilakukan. Assertion gagal dan runner awal
tetap disimpan. Tidak ada perubahan source produk untuk membuat hasil ini lulus.

Runner stream juga memakai retry terbatas saat penulisan report berhadapan
dengan sharing lock Windows dan menyimpan stderr. Ini belum membuktikan akar
kegagalan runner Windows10 tanggal27; hasil Windows10 tersebut tetap belum
terkonfirmasi dan tidak ditutup oleh bukti Windows11.

## Penutupan dan batas bukti

Pemulihan selesai: tiga profil LocalGPO sesuai snapshot,110aturan inbound asli
masih enabled,0rule LocalGPO dan0task fixture tersisa. State lockdown absent dan
TCP internet biasa kembali hanya sesudah recovery admin eksplisit. Laporan awal
menghitung array nama rule bersarang sebagai satu; verifikasi scalar terpisah
membuktikan seluruh110aturan. Kedua bukti dipertahankan.

Konfigurasi endpoint awal dipulihkan hash-identik. Primary identity, legacy
runtime0.1.9, Secure Boot/TPM dan definisi XML inactive Windows11 tidak berubah.
Kandidat0.1.13 tetap terpasang pada instalasi endpoint terpisah. Identitas uji
revoked diarsipkan privat setelah tunnel/owner cleanup; sesi dan credential
staging dihapus. Akun/identitas uji disabled, serial1002 tetap revoked, grant
kosong; namespace gateway/WAN dan tiga unit transient dihentikan setelah peer
kosong. Root firewall server sama selain counter trafik. CA/DB/CRL/histori dan
backup tetap ada. Windows11 dan SERVER running; lima guest lain shut off.

Tidak ada perbaikan source produk yang diperlukan untuk matriks Windows11 ini.
Source paket sama dengan kandidat yang diuji di Windows10; perubahan sesi ini
adalah bukti native dan dokumentasi. Raw evidence berada di
`state/internet-win11-20261028/` (tidak di-Git), kredensial tetap lokal privat.

IPv6 nyata, perpindahan Wi-Fi, endpoint fisik, Windows11 build/edisi lain,
expiry/daemon-stop/reboot tunnel aktif untuk mode baru tetap BELUM_TERUJI.
Domain atau GPO firewall yang sudah ada tetap ditolak oleh kandidat. Tidak ada
jaminan terhadap pemilik hak administrator lokal penuh yang mengubah policy.
