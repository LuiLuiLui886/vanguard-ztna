# Validasi setup terpadu0.1.14 — 28–29 Oktober 2026

Pengguna memilih satu folder offline dan satu BAT utama. Kandidat menambahkan
`deploy/endpoint/windows/Setup-VanGuard.bat` dan `.ps1`, kontrak publik
`vanguard/provision.py`, serta opsi per-device pada
`scripts/build_endpoint_package.py`. Petunjuk operator tetap satu sumber:
[manual Bab14.0](MODUL_PENGGUNAAN_VANGUARD.md).

## Perilaku kandidat

BAT utama mengorkestrasi installer Python/WireGuard/aplikasi yang sudah ada,
memasang profil/root publik yang disiapkan admin, menerapkan lockdown untuk
schema2, membuat key lokal dan mengekspor request publik. Bundle admin harus
terikat CSR/key/WG/device/IP/profile sebelum import. Setelah itu pengguna login
karyawan dan proses connect tetap menjalankan enam pemeriksaan admission.
Registrasi/import/login sendiri tidak menambah peer. UAC, approval admin dan
login tetap diperlukan; bukan instalasi tanpa interaksi manusia sama sekali.

Wizard menyimpan fase tanpa credential dan memeriksa fakta file/runtime/policy
saat resume. Key/config berbeda atau parsial ditolak, tidak dihapus/dibuat ulang.
Paket berisi hanya input publik; tidak membawa password/OTP/token management/
private key. Builder memeriksa pin admin dan menserialisasi ulang sertifikat
publik agar tail PEM tidak ikut tersalin. ROOT CA utama tetap di server CA.

## Bukti dan batas

| Pengujian | Lingkungan | Hasil |
|---|---|---|
| Provisioning, bundle, paket, managed internet awal | Linux lokal/mock OS |44PASS181,48detik sebelum penambahan lock provisioning |
| Regresi akhir profil/platform/provision/internet/paket | Linux lokal/mock OS |110PASS/1SKIP215,74detik; skip ACL native Windows |
| R1 setup tanpa approval | Windows11 build26300, PS1 otomatis |WAITING_APPROVAL/exit20, key lokal/request publik; no tunnel |
| R1 dua resume sebelum approval | Windows11 native |9PASS; key/runtime sama, export hanya4field publik, no tunnel |
| R2 approval import dan dua resume | Windows11 native, PS1 PrepareOnly |9PASS; READY_FOR_LOGIN/exit0, key/runtime sama, no tunnel |
| R3 entrypoint BAT setelah repack | Windows11 native, /prepare-only /nopause |9PASS, exit0, READY_FOR_LOGIN; key/runtime sama, no tunnel |
| Koneksi dari identitas wizard | Windows11 → Linux namespace |PASS: admission/handshake, default-deny/grant TCP+DNS baru, awal+2renewal, logout dan owner cleanup |
| Pemulihan dan preservasi identitas utama | Windows11/Linux |PASS: config/key/runtime lama dan VM XML sama;110inbound asli tetap;0LocalGPO rule/0task test |
| BAT persiapan dan dua kali resume | Windows10 LTSC19044, /prepare-only /nopause |9PASS, WAITING_APPROVAL/exit20; key/runtime sama, export publik, no tunnel |
| BAT impor approval dan dua kali resume | Windows10 LTSC19044 native |9PASS, READY_FOR_LOGIN/exit0; request sama lintas approval, no tunnel |
| Koneksi identitas wizard1004 | Windows10 → Linux namespace |PASS: login tanpa peer, admission/handshake, default-deny/grant TCP+DNS baru,2renewal, logout dan owner cleanup |

R1/R2 belum menguji BAT baru secara langsung. R3 menambahkan flag `/prepare-only`
agar runner menguji BAT yang sama tanpa prompt login; perilaku default login
interaktif/UAC belum boleh disimpulkan dari itu. Paket r3 lokal mencakup patch
profil/renewal audit28Oktober. Hash manifest r3:
`3557fb1719f44a8dc764ee6979614150d2ea87e860b1303d1b91d3cfe1a877d2`.
Paket per-device fixture ini bukan paket untuk dibagikan kepada PC pengguna.

Uji memakai VM Windows11 asli .100.60, backup endpoint/config/identitas pada
folder Program Files privat, XML host dan backup disk lama tetap dipertahankan.
Gateway .100.80 berada dalam namespace Linux, registry `server-wizard-20261028`,
CA sementara dengan histori yang sama. Sertifikat uji baru1003; .3 hanya pada
fixture. Tidak melakukan rollout layanan utama atau mengganti identitas utama.
Saat resume29Oktober seluruh VM mati; Windows11/SERVER dinyalakan kembali dan
transport direkonstruksi tanpa memulihkan state CA lama.

PC fisik, fresh OS tanpa runtime dengan wizard baru, reboot
runtime3010, UAC interaktif, login dialog/console default dan interrupted install
wizard di setiap fase tetap BELUM_TERUJI. Hasil installer lama untuk prasyarat
Windows10/11 bukan pengganti matriks wizard baru. Tidak ada klaim bebas bug atau
siap produksi. Tidak mengganti ZIP stabil0.1.12 secara otomatis.

Raw log/paket/JUnit tetap lokal di `state/setup-wizard-20261028/`, credential
hanya di inventaris privat. Perkembangan dan penutupan akhir ada pada checkpoint.

## Koreksi artefak ZIP saat resume

ZIP r3 yang tersimpan mengalami kegagalan CRC pada installer Python; SHA berbeda
dari catatan build28Oktober. BAT menolak checksum sebelum instalasi (FAIL aman).
Penyebab perubahan byte **belum diketahui**. Direktori sumber terverifikasi,
lalu dikemas ke ZIP baru, tanpa mengganti pin runtime atau menonaktifkan guard.
CRC dan semua manifest entry diverifikasi di host, SHA ZIP dan setiap file hasil
ekstraksi diverifikasi lagi di Windows. Repack ini kemudian lulus9kasus BAT.
ZIP rusak/log awal dipertahankan lokal, bukan dipublikasikan.

Template admin GitHub berbeda dari paket fixture: tidak menyertakan profile,
root CA uji, provision per-device atau approval. Admin harus menyiapkan paket
per-device memakai profil/alokasi nyata sesuai manual sebelum user menjalankan
BAT. Template menggunakan wheel/skrip yang sama dengan kandidat yang diuji;
manifest berbeda karena input per-device tidak disertakan. Status tetap kandidat.

## Penutupan fixture

Logout diikuti cleanup pemilik: service1060, config/marker/session absent.
Akun dan identitas uji dinonaktifkan, serial1003 dicabut, grant/peer kosong.
Dua unit transient dihentikan dan namespace gateway dihapus; CA/database/CRL
serta histori dipertahankan. Firewall root server sama selain counter trafik.
Recovery admin mengembalikan profil LocalGPO dan mempertahankan110rule inbound;
0rule LocalGPO dan0task fixture tertinggal. Config awal hash-identik, identitas
utama/legacy0.1.9/SecureBoot/TPM/definisi XML tidak berubah. Kandidat endpoint0.1.14
terpasang terpisah. Request/approval/identity uji revoked dan wizard-state akhir
diarsipkan privat, credential staging guest dihapus; inventaris host CLEANED.
Windows11 dan SERVER tetap running, lima VM lain shut off. Tidak rollout produksi.

Koneksi diuji memakai client dari paket terpasang dengan fixture login, bukan
simulasi keyboard pada prompt BAT. Dialog UAC dan login default tetap belum diuji.
Tidak ada CI baru yang diklaim. Source/module/skrip cocok kandidat native; Ruff,
pip check dan diff whitespace PASS. Template publik tidak memuat data fixture.


## Tambahan Windows10 — 29 Oktober, kandidat yang sama

VM Windows10 Enterprise LTSC Evaluation build19044 memakai Python3.13.17 dan
endpoint0.1.14. Source produk tidak berubah pada sesi ini. Paket per-device baru
memakai root/gateway sementara yang sama, registry terpisah dan serial1004;
konfigurasi/identitas lama disimpan sebelum pengujian. Checksum ZIP dan seluruh
entry diverifikasi sebelum dan setelah transfer;41entry, SHA ZIP
`b186891719d24d5d4b161758c4c6326ef92aa861fa6e1d5ef32e3fa9d207f38f`.
Paket fixture tidak dipublikasikan sebagai installer pengguna.

BAT dijalankan sebagai SYSTEM melalui Task Scheduler dengan `/prepare-only
/nopause`, bukan simulasi klik UAC.9kasus menunggu approval dan9kasus impor/resume
lulus. CA sementara menerbitkan sertifikat dari CSR endpoint; API management
mendaftarkan binding perangkat dan karyawan. Bagian ini tidak menguji ulang UI
pendaftaran dashboard. Request publik identik lintas approval; tidak ada peer
sebelum login/admission. Wheel cocok source Python saat pengujian, launcher
terpasang cocok manifest dan pip check lulus.

Client dari paket terpasang diuji dengan fixture login: handshake, default-deny
serta grant TCP/freshDNS, dua renewal46,085/36,604detik, logout, owner cleanup,
login ulang dan reconnect lulus. Pemanggilan client fixture terpisah dari prompt
BAT dan preflight launcher interaktif; ini bukan bukti jalur klik-ke-koneksi penuh.

Pengujian TCP aktif menggunakan echo WAN terisolasi. Sebelum revoke,218balasan
tercatat dan stream masih hidup. Pencabutan serial1004 melalui CA nyata diikuti
TimeoutError, peer absent, probe TCP/DNS baru ditolak, fresh admission403.
Izin internet masih enabled saat pencabutan, sehingga efek bukan dari penghapusan
grant. Batas observasi8,541detik mencakup SSH, transaksi CA, polling serta timeout
TCP; bukan ukuran presisi kernel atau jaminan waktu respons umum.

Kegagalan alat bantu tetap disimpan: probe versi Python -c salah quoting di
PowerShell; observer TCP dibaca sebelum file siap; cleanup mengulang pengubahan
grant sesudah device disabled menghasilkan409. Versi diperiksa ulang lewat
--version/pip show, observer menunggu laporan tersedia sebelum revoke, cleanup
memeriksa state aktual (disabled/grant false/no peer) sebelum menghentikan unit.
Tidak melewati validasi installer, mengulang penerbitan, atau mengubah source
produk untuk mengatasi kegagalan alat ukur. Hasil gagal lama27Oktober tetap
historis; hasil29Oktober adalah eksperimen baru yang menutup gap TCP Windows10.

### Klasifikasi temuan sesi ini

| Temuan | Klasifikasi | File/fungsi dan bukti | Dampak/prioritas | Kriteria selesai/status |
|---|---|---|---|---|
| Wizard Windows10 belum terverifikasi | Perilaku yang belum diuji saat awal | Setup-VanGuard.bat/ps1;18assertion native PASS | P1, risiko distribusi tanpa bukti | Persiapan/impor/resume tanpa rotasi key atau tunnel: selesai dalam cakupan PrepareOnly |
| TCP Windows10 saat certificate-revoke | Perilaku yang belum diuji saat awal | Authority.revoke, Admission.reconcile, client.connect; stream aktif berhenti, peer absent, fresh403 | P1, bukti pencabutan akses | Selesai pada VM LTSC19044 dan CA/namespace sementara |
| Alat ukur membaca laporan terlalu awal | Bug yang berhasil dibuktikan pada fixture | state/setup-win10-20261029/cut_stream-first.py; FileNotFound sebelum revoke | P2, false failure observasi | Pemeriksaan file terbatas lalu ulang pada stream hidup; PASS, log awal retained |
| UAC/login default, fresh OS/3010, PC fisik | Perilaku yang belum diuji | Jalur interaktif Setup-VanGuard.ps1 dan VanGuard.ps1 belum dijalankan penuh | P1 sebelum distribusi luas | BELUM_TERUJI; perlu native dengan topologi sesuai, input operator dan restart nyata |

Tidak ada bug produk baru yang berhasil dibuktikan oleh sesi ini. Pengujian ini
bukan bukti bahwa tidak ada bug. Risiko local administrator mengubah endpoint,
lifecycle/readiness internet dan seluruh edisi/build lain tetap dibatasi menurut
manual/checkpoint. Suite Linux110PASS/1SKIP adalah hasil sesi sebelumnya pada
source yang sama; tidak dijalankan ulang untuk perubahan dokumentasi saja.
Bukti sesi ini lokal: `state/setup-win10-20261029/`; inventaris credential tetap
hanya di direktori privat, tidak di GitHub.

### Penutupan Windows10

Recovery admin terkonfirmasi: profil firewall pulih,89inbound asli tetap enabled,
0rule LocalGPO,0task fixture; internet biasa kembali setelah recovery eksplisit.
Config dan identitas sebelum uji dipulihkan hash-identik. Serial1004 tetap revoked,
akun/device disabled, grants/peers kosong. Service tunnel1060, config tunnel dan
marker owner absent; sesi dihapus setelah logout final. Credential staging guest
dihapus; inventaris host berstatus CLEANED. Identity uji/request/approval disimpan
pada arsip privat `C:\Program Files\VanGuardSetup10Test`.

Tiga unit transient dan kedua namespace dihentikan/dihapus. Root firewall server
sama selain counter. `Authority.check_state()` PASS: relasi index, counter,
sertifikat dan CRL konsisten; root fingerprint sama, revocation1001–1004 retained.
Tidak restore index/CRL, menebak counter atau membuat ulang CA. XML inactive
Windows10 sama sebelum/sesudah; domain lain tidak didefinisikan ulang. Endpoint
kandidat0.1.14 tetap terpasang, release lama serta backup dipertahankan.
Status akhir: Windows10 dan SERVER running; Windows11 dan empat Ubuntu lain off.
