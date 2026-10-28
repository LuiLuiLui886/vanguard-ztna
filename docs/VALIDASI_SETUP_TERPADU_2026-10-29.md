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

Windows10 wizard, PC fisik, fresh OS tanpa runtime dengan wizard baru, reboot
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
