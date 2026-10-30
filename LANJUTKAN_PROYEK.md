# Lanjutkan proyek VanGuard

## 31 Oktober01:33WIB — diagnostik readiness lokal selesai diuji, belum rollout

Source `vanguard/health.py` kini mendukung `<role> --diagnose`: alasan kegagalan
allowlist dan durasi, tanpa pesan exception/URL/secret. Subprocess tetap6detik;
API publik/fail-closed tidak berubah. Tes baru `tests/test_health_diagnostics.py`.
Baseline16PASS47,57detik; kandidat26PASS61,39detik. Source staging di ketigaVM
memakai environment/user service:36/36ready; postflight layanan terpasang30/30
HTTP200 dan nolpeer. Config/root/key/index/serial tidak berubah. ManualMD/HTML
Bab7.3 dan API diperbarui; hasil ada pada [laporan uji](docs/UJI_INTEGRASI_0.1.14_2026-10-31.md).

**503 awal belum direproduksi dengan penyebab terkonfirmasi**, bukan fixed.
Kode diagnostik mencerminkan kelas exception library, bukan kepastian fase
jaringan. Source baru belum terpasang pada paket/EXE: VM tetap0.1.14 dengan module
health lama yang hash-nya diverifikasi, kandidat hanya staging. Bukti privat
`state/readiness-20261031/`. Harness awal mencoba server→dashboard yang firewall
memang tidak izinkan; kegagalan itu dipisahkan dari20/20probe server→CA sehat.
Tidak ada restart/ubahfirewall/enrollment pada investigasi ini. KondisiVM/disk/
clientutama expired tetap seperti checkpoint sebelumnya. Berikutnya lanjutkan
observasi insiden bila muncul, review/rollout diagnostik terencana, kapasitasdisk,
penggantian identitas client utama serta deployment/testgatewayinternet.


## 31 Oktober — pengujian layanan0.1.14 selesai, satu readiness sementara gagal

[Laporan uji terbaru](docs/UJI_INTEGRASI_0.1.14_2026-10-31.md) mencatat VM langsung CA/server/admin0.1.14 dengan
sourceclient0.1.14 terisolasi pada Ubuntu (instalasi client utama tetap0.1.9).
Registrasi/login tanpa peer,4admission negatif, handshake nyata, default-deny,
grant aplikasiTCP8082, penolakanLAN/portlain, TCP aktif setelah pencabutan grant,
2renewal otomatis, logoutscope/idempotent dan revokeCA PASS. RevokeCA menghapus
peer8,238detik pada satu sampel. AdminHTTPS/TOTP/arsip/hash PASS. Regresi terisolasi
Linux **89PASS/1SKIP267,83detik**; bukan fullsuite atau Windows native.

Postflight pertama **29/30HTTP200**: server/readyz503, dependencyCA unknown,
dependensi lain ready. Diagnostik langsungCA20/20 dan follow-up30/30HTTP200.
Penyebab503 **BELUM_TERKONFIRMASI**, tidak diklaim fixed. Driver exercise exit1
karena enum alasan cleanup keliru; cleanup terpisah berhasil dan kegagalan
harness lain dijelaskan dalam laporan/jurnal, bukan disembunyikan.

CA invariant/CRL, keduaDB, histori serta identitas utama terjaga. Akun uji disabled,
sertifikat revoked, resource-policy byte-identik, nolpeer/tunnelclient/listenerdemo.
Bukti/backup `state/live014-20261031/` tetap lokal; inventarisprivat diperbarui.
CA/server/admin/clientUbuntu running; attacker/Win10/Win11 off. Clientutama
kembali auto-restart fail-closed (cert/sesi expired). Host1,3GiB free; profiladmin/
gatewayinternet belum dikonfigurasi. Windowsnative/EXE/reboot/outage tidak diuji
ulang. Tidak ada perubahan sourceproduk. Berikutnya kapasitas, investigasi503,
penggantian identitas utama dan deployment/testinternet terencana.


## 31 Oktober01:05WIB — update CA/server/admin0.1.14 selesai diverifikasi

**Ketiga layanan sekarang0.1.14**, bukan0.1.11. CA/server/admin dan daemon/WG
aktif setelah hostboot.27berkas paket masing-masing cocok sourcewheel, pip check
PASS;77berkasCA,9server,6admin config/identity tetap sama backup. CA invariant/CRL
PASS, keduaDB integrity OK.1120baris historis7tabel server dan157baris6tabel admin
terjaga. Nol livepeer; semua7domain definition tetap sama. HTTPS30/30HTTP200,
maksimum3,597detik,5authorization guards PASS. Bukti `state/rollout-20261031-postflight/`.

Postflight30Oktober20/30HTTP200 tetap dicatat, bukan diganti hasil baru. Penyebab
heartbeat crl_available=false pada faseitu belum terkonfirmasi;31Oktober fetch/
signature/waktuCRL serta heartbeat valid tanpa melonggarkan validasi. Ini bukan
klaim soak atau perbaikan akar masalah readiness di semua kondisi. Backup rollout
ada pada `state/rollout-20261030-services/` dan `retry2/`; recovery percobaan pertama
hanya code, tidak rollback CA/DB. Lihat jurnal30/31Oktober untuk kegagalan harness.

Saat ini CA/server/admin running; empat VM lain off akibat hostreboot dan belum
dinyalakan ulang pada tugas pengecekanbackend. Host1,3GiB free. ClientUbuntu utama
cert/sesi expired belum diganti. Profil admin/gatewayinternet masih perlu konfigurasi:
VANGUARD_CLIENT_PROFILE dan VANGUARD_INTERNET_POLICY belum diisi. Updatepaket saja
bukan pemberian akses internet. Selanjutnya kapasitas, replacementidentitas dan
konfigurasi/test deployment internet terencana; jangan reinit CA atau restorehistory.
Hasil dipush sebagai `c694151`; SHA origin feature terverifikasi.
Catatan publikasi ada pada jurnal31Oktober.

## 30 Oktober13:33WIB — CA/server/admin diperbarui ke0.1.14

Permintaan pengguna update tiga layanan sudah diimplementasikan. Preflight benar
0.1.11; kini paket0.1.14 pada CA,server,admin;27berkas wheel masing-masing cocok,
pip check PASS dan semuaunit aktif. Backup quiescent pernode retained, key/root/
index/serial/issued/config/env dipertahankan; tidak restore CA/DB lama. Percobaan
pertama verifier salah menganggap generation transaksi sementara sebagai state
permanen, sehingga code-only recovery dilakukan. Retry dengan whitelist published
state selesai; semua7definisi VM tetap, VM/console dibiarkan aktif untuk pengguna.
Bukti `state/rollout-20261030-services/`, khusus hasil akhir di `retry2/`.
Readiness dan DB postflight dicatat pada jurnal setelah selesai.

Update ini **paket aplikasi**, bukan aktivasi profil/gateway internet. Admin kini
memiliki code dukungan profil dan server memiliki module internet, tetapi env
VANGUARD_CLIENT_PROFILE/VANGUARD_INTERNET_POLICY belum diisi; kebijakan internet
masih perlu deployment terencana. Resource-policy lama tetap. ClientUbuntu utama
cert/sesi expired tetap, perlu penggantian identitas/login; tidak diubah oleh update.
Host sekitar456MiB free, tetap perlu kapasitas sebelum uji/build tambahan berat.
Log diagnostik192MiB telah dikompres lossless dan hash isi diverifikasi; tidak
menghapus bukti/backup. Lihat jurnal30Oktober untuk validasi/publikasi akhir.

## 30 Oktober 12:34 WIB — seluruh VM dibuka untuk uji pengguna

Permintaan pengguna untuk membuka semua VM sudah dilaksanakan: CA, SERVER,
ADMIN, CLIENT Ubuntu, ATTACKER, CLIENT-WINDOWS11 dan CLIENT-WINDOWS10 semuanya
running. Lima console serial dibuka di GNOME Terminal; dua virt-viewer Windows
aktif tanpa error launcher. Virsh domblkerror ketujuhnya: No errors found.
Bukti privat `state/vm-open-20261030-1233/`; disk host sekitar3,2GiB kosong.
Ini status boot/console, bukan pengujian ulang readiness, desktop/login atau VPN.
Sertifikat/sesi client Ubuntu expired dan backend utama0.1.11 tetap seperti
laporan kelayakan; tidak ada perubahan key, akun, grant, CA atau konfigurasi.
VM dan jendela console sengaja dibiarkan aktif untuk pengguna. Catatan terbaru
ini menggantikan kondisi akhir shut off pada sesi pengujian sebelumnya.

## 30 Oktober — uji kelayakan dan panduan EXE dari nol

**Keputusan: layak untuk uji lab terkontrol, belum penerimaan produksi penuh.**
[Laporan lengkap](docs/UJI_KELAYAKAN_2026-10-30.md) memisahkan scope/bukti dan8temuan.
Source baseline7fa2e7c: Linux307PASS/1SKIP919,32detik; Ruff/pip/Bash/build/hash
artefak PASS. HTTPS utama30/30HTTP200, firewall40/40, negative API/LAN7/7;
CA invariant/CRL dan DB server/admin OK. Resource nft/veth7perilaku PASS.
Kandidat namespace HTTPS+WireGuard+nft16record PASS exit0; lease uji12detik,
2renewal manual, CAoutage/startup reconcile, logoutscope dan active TCP revoke.
Run1 gagal membentuk stream sebelum revoke dengan peer client lama; run2observer
terinterupsi; run3fresh client peer lulus. Jangan klaim recovery otomatis state lama.

Windows11 build26300 dan Windows10LTSC19044 masing-masing helper28PASS/2SKIP,
9gate sintetis,6resume sentinel,10configure,13extractor dan6EXE native PASS.
EXE umum Windows11 juga install asli exit0, runtime0.1.14/pip/help PASS;
key/config/profil firewall tetap, old release retained, no new tunnel/lockdown.
Windows10 tidak reinstall kali ini. EXE masih Authenticode NotSigned.
Runner awal stderr/path/ACL gagal; koreksi harness dan postflight terdokumentasi,
bukan hasil fail yang dibuang. Tidak ada source aplikasi atau binary publik diubah.

**Penghalang:** client Ubuntu utama cert expired24Oktober dan sesi expired,
service auto-restart/fail-closed; CA/server/admin utama0.1.11 belum fitur gateway/
profil kandidat. Disk host99% (~3,2GiB free akhir sampel). EXE schema2/UAC/browser,
fresh OS/3010/login interaktif, PC fisik, power-loss CA dan soak masih BELUM_TERUJI.
Bukti native/lifecycle Windows20–29Oktober tetap historis, bukan seluruhnya diulang.

Manual tunggal [Bab14.0.1.1](docs/MODUL_PENGGUNAAN_VANGUARD.md) kini9langkah EXE:
unduh/hash → install → configure (+internet-enable bila schema2) → request →
approval admin → import → login/connect → logout. TOC HTML mendukung subbagian ini.
EXE/ZIP tetap byte-identik; salinan manual di artefak lama belum berisi revisi ini.
Semua3fixture CA/akun dibersihkan (cert revoked/account disabled/invariant OK),
namespace/tunnel uji hilang, unit uji inactive; semua7XML domain cocok baseline.
Inventaris testcredential hanya lokal privat, tidak dipublikasikan.
Bukti lokal `state/qualification-20261030/`; backup Windows11 `VGQual30/before-install`.
Semua7VM kembali shut off melalui shutdown normal; tidak ada runner uji tersisa.
Laporan/panduan dipush pada `62ce345`; SHA origin feature terverifikasi.
Main dan artefak installer tetap; hasil publikasi tercatat pada jurnal30Oktober.

Berikutnya: kapasitas host, penggantian identitas expired tanpa mengubah root/
histori, rollout kandidat terencana, lalu matriks EXEper-device/physical yang tersisa.

## 29 Oktober — flowchart lengkap sistem sampai EXE

Manual tunggal [Bab1.1](docs/MODUL_PENGGUNAAN_VANGUARD.md) kini memuat5diagram:
backend/CA, distribusi+EXE, policy+enrollment, login/admission+izin, lifecycle+audit.
SVG tampil langsung di GitHub; HTML menyematkan gambar untuk penggunaan offline.
Source generator `scripts/render_system_flows.py`; renderer HTML diperbarui.
Batas template/schema1/schema2, blok setelah policy sukses, key di client,
registrasi tanpa peer, enam cek, grant dan lease dijelaskan. Diagram bukan bukti
semua jalur telah diuji. EXE/ZIP publik tetap byte-identik; manual di dalam artefak
lama belum memuat gambar baru. Source aplikasi/VM tidak berubah dalam tugas ini.
Validasi5SVG parse/render dan inspeksi visual, gambar embedded+anchor HTML,
Ruff dan diff PASS. Bukti lokal `state/flows-20261029/`.
Sisa pengujian EXE Windows11/schema2/UAC/fresh OS/PC fisik tetap pada catatan bawah.
Flowchart/manual dipush sebagai `feac013` ke origin feature; SHA remote cocok.

## 29 Oktober — EXE offline dibuat dan diuji di Windows10

Kandidat `downloads/Setup-VanGuard-0.1.14-fix1.exe` (44.718.592byte) membundel
Python/WireGuard/wheel aplikasi0.1.14. SHA256:
`f74a3b7b72373dbe55c1cc5b771938108cc683e930949c861cea7422415c7f69`.
Paket umum memasang runtime/aplikasi; profil/CA publik/alokasi belum disertakan.
Admin dapat build EXE per-device untuk wizard lengkap memakai source C#/.NET
Framework dan Build-Exe.ps1. Key tetap dibuat di client; approval/login serta
enam pemeriksaan admission tetap wajib. EXE unsigned, origin/hash wajib dicek.
Manual tunggal MD/HTML Bab14.0.1 mencakup kedua alur, build dan recovery.

Windows10 LTSC19044:13tes extractor/ACL PASS,6bootstrap EXE final PASS,
6postflight native PASS. Generic EXE menjalankan installer offline sungguhan
hingga exit0; pip check/clienthelp, hash config/key utama dan release lama
terjaga. Device EXE schema1 fixture prepare/resume exit20 menjaga key/config/
request/runtime. Runner awal terinterupsi shutdown sebelum menulis report;
postflight terpisah sesudah boot membuktikan hasilnya, bukan menimpa bukti lama.
Probe final pertama ditolak mutex karena installer lain aktif; retry berurutan
6PASS. Linux paket6PASS0,08detik. Binary terunduh: SHA native cocok, embeddedZIP
CRC+manifest39anggota+kesamaan payload lokal PASS; scan rahasia dan diff PASS.
Lihat [validasi EXE](docs/VALIDASI_EXE_2026-10-29.md); bukti privat `state/exe-20261029/`.

Task uji dihapus,0EXE aktif, service tunnel1060, no managed-policy marker;
backup dan release lama retained. VM Windows10 mengalami event1074 wlms.exe
shutdown dan TrustedInstaller.exe restart; aktivasi/update tidak diubah.
Host sempat414MiB free sehingga VM di-pause sementara;4fragmen ISO publik lama
dipindah ke partisi lokal lain dengan SHA256+fsync+symlink path lama. ISO lengkap,
backup/evidence dan disk VM tetap. Manifest relokasi lokal media-relocation.json.
Host kini~4,1GiB free; Windows10 running, enam VM lain off. Kredensial tidak berubah.

BELUM_TERUJI untuk wrapper: UAC klik/browser/SmartScreen, Windows11, fresh OS
tanpa runtime, reboot3010, login interaktif penuh, physical endpoint dan
power-loss. R1 installer runtime existing tidak membuktikan instalasi prasyarat
pada OS kosong. Signing produksi belum tersedia. Main/stable ZIP tidak diganti.
Source/EXE/manual dipush sebagai `48d184e`; SHA origin feature cocok.
Main tetap. Tidak ada hasil CI baru yang diklaim.

## 29 Oktober — bug resume wizard diperbaiki, kandidat0.1.14-fix1

Source, tes, manual dan template dipush pada `3104030`; SHA origin feature cocok.

Audit03f33c9 membuktikan wizard berhenti ketika paket sama tetapi setup-state
IN_PROGRESS/hilang atau python.exe hilang: native3FAIL sebelum patch. Blok reuse
sekarang memilih installer tepercaya jika runtime belum lengkap; guard ownership,
tunnel dan policy tetap. Tidak menghapus key/config atau menebak metadata rusak.

Baseline Linux55PASS163,42detik; regresi paket6PASS; native PowerShell6PASS memakai
installer sentinel, lalu7PASS installer/venv offline sungguhan pada root fixture
terisolasi di Windows10 LTSC19044. Repair memakai release baru, key/config/request
serta release lama/parsial terjaga; retry lengkap tidak reinstall. Kegagalan awal
fixture akibat path panjang serta timeout observasi tetap dicatat, bukan PASS.
Instalasi utama tetap; no CA issuance, no tunnel/policy, task fixture dihapus.

Laporan: [audit wizard](docs/AUDIT_WIZARD_2026-10-29.md). Template admin0.1.14-fix1 menggantikan template
kandidat sebelumnya di downloads, wheel tetap0.1.14. Admin perlu build ulang
paket per-device supaya checksum mencakup script terbaru. Stable0.1.12/main tetap.
Manual MD/HTML, jurnal dan tes regresi ditambahkan; tidak mengklaim CI baru.
Bukti lokal `state/audit-wizard-20261029/`; backup/fixture lama retained.

Windows10 running, enam VM lain off. Host sempat tersisa2,1GiB disk; periksa
kapasitas sebelum build/VM tambahan, jangan menghapus backup otomatis. Sisa:
fix1 native Windows11, UAC/login default penuh, fresh OS/3010, power-loss,
repair managed policy (tetap memerlukan recovery admin), lifecycle/readiness
internet dan PC fisik. Pengguna bertanya kemungkinan EXE: bisa membungkus alur
offline yang sama, tetapi EXE BELUM_DIBUAT/BELUM_TERUJI; UAC/approval/login dan
key yang dibuat di client harus tetap dipertahankan.

## 29 Oktober — wizard Windows10 dan pencabutan TCP aktif terverifikasi

Dokumentasi/hasil dipush pada `2d6c2db`; SHA origin feature terverifikasi.

Kandidat0.1.14 yang sama diuji pada Windows10 Enterprise LTSC19044/Python3.13.17.
BAT langsung `/prepare-only /nopause`:9kasus pending approval dan9kasus
import/resume PASS; key/runtime/request terjaga, no tunnel sebelum admission.
Client native: login tanpa peer, handshake, default-deny/grant TCP+freshDNS,
2renewal, logout/owner cleanup, login ulang/reconnect PASS. Revoke CA serial1004
menghentikan TCP aktif dan menghapus peer; fresh admission403 dan TCP/DNS baru
ditolak. Batas observasi8,541detik mencakup polling/SSH/CA/timeout TCP, bukan
jaminan latency. Gap pengukuran Windows10 pada27Oktober ditutup eksperimen baru;
log FAIL lama serta kegagalan alat bantu sesi ini tetap disimpan.

Recovery PASS:89inbound asli,0LocalGPO/0task fixture; config dan identitas lama
hash-identik; XML inactive Windows10 tetap. Sertifikat revoked, akun/device
disabled, grant/peer kosong;3unit/2namespace dihentikan. CA check_state/root pin
PASS, histori1001–1004 retained; firewall root server sama selain counter.
Credential hanya inventaris privat, staging VM dibuang, status CLEANED.
Windows10+SERVER running,5guest lain off; kandidat endpoint0.1.14 tetap terpasang.

Laporan: [validasi setup terpadu](docs/VALIDASI_SETUP_TERPADU_2026-10-29.md); manual tunggal Bab14.0 diperjelas.
Source produk/ZIP kandidat tidak berubah; tidak perlu membangun ulang ZIP atau
mengulang suite Linux110PASS/1SKIP hanya untuk dokumentasi. Tidak mengklaim CI baru.
Bukti lokal `state/setup-win10-20261029/`. Branch tetap feature/2026-10-22-physical-endpoints;
main/ZIP stabil0.1.12 tidak diganti. Sisa: UAC/login default interaktif penuh,
fresh OS/reboot3010, PC fisik, lifecycle/readiness internet, edisi/build lain.
Jangan memakai ulang serial revoked untuk eksperimen berikutnya.

## 29 Oktober — setup terpadu0.1.14, validasi dan pemulihan selesai

Pengguna memilih satu folder offline+satu BAT. Source menambah Setup-VanGuard.bat,
Setup-VanGuard.ps1, vanguard.provision dan builder per-device. Manual Bab14.0
menjelaskan admin menyiapkan profil/alokasi, user menjalankan BAT, menunggu
approval bundle, lalu login/connect. Tidak ada token management/private key dalam
paket; key lokal tidak dibuat ulang saat resume. Dua patch audit ikut0.1.14.

Suite Linux110PASS/1SKIP215,74detik. R1 pending approval/resume9PASS dan r2
approval/resume9PASS melalui PS1. R3 repacked BAT langsung9PASS: exit0,
READY_FOR_LOGIN, key/runtime sama, no tunnel. ZIP r3 awal mengalami CRC rusak,
checksum installer menolak dengan benar; repack dari direktori tervalidasi
mempertahankan manifest/pin. Penyebab kerusakan byte belum diketahui, bukti FAIL
retained. Laporan [validasi setup terpadu](docs/VALIDASI_SETUP_TERPADU_2026-10-29.md) dan jurnal29Oktober membedakan bukti.

Login/admission/handshake, default-deny/grant TCP+DNS baru,2renewal, logout dan
owner cleanup PASS memakai client kandidat dan fixture login. Recovery selesai:
110inbound asli terjaga,0LocalGPO/0task test; config/primary identity/legacy runtime/
SecureBoot/TPM/VM XML sama. Test identity1003 revoked dan akun disabled; namespace
serta unit transient dihentikan, CA/DB/histori tetap. Credential staging dibuang.
Windows11+SERVER running,5guest lain shut off. Template offline0.1.14 untuk admin
ada pada downloads tanpa profil/alokasi fixture. Main/ZIP0.1.12 tetap. Source dan
ZIP kandidat dipush pada commit `e0dd7eb`; SHA origin feature terverifikasi.
Tidak ada CI baru yang diklaim. Hasil native/tes lokal dan batasnya ada di laporan.
Sisa: UAC/login interaktif default, Windows10 wizard, OS fresh/reboot3010,
PC fisik, serta lifecycle/readiness internet yang sebelumnya belum diuji.

## 28 Oktober — audit bug lanjutan dan patch source

Patch `ff59047` sudah dipush ke origin feature; SHA remote terverifikasi.
Tidak ada hasil CI baru yang diklaim.

Dua bug dibuktikan dengan tes gagal sebelum patch: profil menerima DNS/route
integer, dan renewal meminta lease sebelum pemeriksaan firewall lokal. Source
sekarang menolak tipe network non-string dan memeriksa guard sebelum renewal;
cleanup tetap berjalan saat guard gagal. Lihat [audit bug](docs/AUDIT_BUG_2026-10-28.md) untuk file/fungsi,
prioritas, bukti dan kriteria selesai. Baseline84PASS/1SKIP; reproduksi4FAIL;
regresi patch awal5PASS. Suite diperluas **98PASS/1SKIP162,45detik**; Ruff,
pip check dan diff PASS. Ini Linux/mock OS, bukan rerun native Windows.

Semua tujuh VM **shut off** saat audit15:37; tidak dinyalakan/diubah. Patch belum
masuk paket r8 atau VM, sehingga hasil native Windows11 di bawah tetap historis
sebelum patch ini. Branch feature sama; main/ZIP stabil tetap. Langkah berikut:
build/reinstall kandidat baru dan native renewal/input invalid Windows10/11 sebelum distribusi.
Readiness internet, native expiry/daemon-stop/reboot tunnel aktif, PC fisik dan
Windows10 active-TCP certificate-revoke tetap pekerjaan tersisa. Jangan menyebut
sistem bebas bug hanya karena tes yang tersedia lulus.

## 28 Oktober — Windows11 native kandidat internet tervalidasi

Laporan/manual dipush pada commit `3c70fee` ke branch feature; SHA remote
terverifikasi. Tidak ada perubahan source produk atau klaim CI baru.

VM Windows11 build26300: installer r8 exit0;9kasus lockdown awal dan6kasus
sesudah reboot PASS. Admission/handshake, default-deny/grant TCP+DNS baru,
3renewal, pencabutan grant saat TCP aktif, logout/cleanup dan reconnect PASS.
Revoke sertifikat1002 memutus TCP aktif dengan reset dan menghapus peer;
fresh admission403. Assertion alat ukur awal hanya menerima timeout sehingga
FAIL; pemeriksaan ulang bukti reset+peer absent+fresh denial PASS perilaku
jaringan, tanpa mengklaim rerun. Lihat [laporan Windows11](docs/VALIDASI_WINDOWS11_INTERNET_2026-10-28.md).

Recovery selesai:110inbound rule asli terjaga,0rule LocalGPO/0task test, config
awal serta primary identity hash-identik. Legacy runtime0.1.9, SecureBoot/TPM dan
XML Windows11 tetap. Endpoint kandidat0.1.13 terpasang terpisah. Akun/identitas
uji disabled, serial revoked, grant/peer kosong; gateway namespace/unit dihentikan,
CA/DB/CRL/histori/backup dipertahankan. Root firewall sama selain counter.

Windows11 dan SERVER sekarang running; lima guest lain shut off. Tidak ada
rollout produksi. Source tidak berubah; main/ZIP stabil0.1.12 tetap. Sisa:
Windows10 active-TCP certificate-revoke belum terkonfirmasi oleh bukti Windows11;
expiry/daemon-stop/active-tunnel reboot mode baru, IPv6 nyata, edisi/build lain,
PC fisik, readiness gate dan paket distribusi final. Jangan mengaktifkan kembali
identitas uji revoked; buat identitas disposable baru bila pengujian dilanjutkan.

## 28 Oktober — regresi akhir selesai; kandidat dipush ke GitHub

Suite fokus terakhir selesai: **120 lulus, 1 dilewati dalam 348,18 detik**
(Linux lokal; sebagian memakai mock OS). Ruff dan pemeriksaan whitespace PASS.
Hasil ini melengkapi bukti native Windows10 tanggal 27 Oktober, bukan pengganti
pengujian Windows11 atau endpoint fisik. Commit source `f861464` sudah dipush
ke origin feature dan SHA remote terverifikasi. Tidak ada klaim hasil CI baru;
workflow push hanya main. Lihat jurnal 28 Oktober untuk rincian publikasi.

Saat resume 28 Oktober 13:37 WIB, seluruh tujuh VM **shut off**; status running
pada catatan di bawah adalah histori. Tidak ada rollout produksi pada sesi ini.
Branch tetap `feature/2026-10-22-physical-endpoints`, kandidat0.1.13; main dan
ZIP stabil0.1.12 tetap. Sisa pengujian dan batasan kandidat tercatat di bagian
27 Oktober serta laporan validasi. Credential dan backup hanya disimpan lokal.

## 27 Oktober — hasil native mode internet dan penutupan fixture

Kandidat0.1.13 berada pada `feature/2026-10-22-physical-endpoints`; main/ZIP stabil
0.1.12 belum diganti. Implementasi memakai gateway Linux dan Local GPO Windows
terkelola tanpa perubahan router. [Laporan bukti](docs/VALIDASI_INTERNET_2026-10-27.md) dan [manual tunggal
Bab14.1](docs/MODUL_PENGGUNAAN_VANGUARD.md) memisahkan status kandidat dari rilis.

Hasil Windows10 LTSC19044 native:9kasus lockdown PASS;6kasus setelah reboot
PASS termasuk local-allow tambahan tidak membuka internet. Admission/handshake,
izin internet default-deny, TCP+DNS baru setelah grant,7renewal, pencabutan grant
saat TCP aktif, logout, cleanup dan reconnect PASS. Pencabutan grant menghentikan
trafik dengan batas observasi2,4306detik (bukan latency kernel presisi). Fault
fetch CRL menghapus peer ≤5,4001detik; ini injeksi fungsi, bukan outage produksi.
Revocation OpenSSL CA sementara menghapus peer, menolak TCP/DNS dan fresh connect
403. **Pengukuran TCP aktif saat revoke sertifikat belum terkonfirmasi** karena
runner stream exit1; laporan FAIL dipertahankan, jangan menyebutnya PASS.

R8 memperbaiki reconnect: pengecualian tunnel disabled sebelum adaptor dihapus.
Jika cleanup policy gagal, tunnel tetap diupayakan stop dan config dipertahankan.
Final reinstall r8 exit0,4file identitas hash-identik dan policy script sesuai
paket. Recovery lokal selesai, Local GPO rule0, state lockdown tidak ada, TCP
internet biasa kembali hanya setelah recovery admin eksplisit.

Identitas/akun uji dinonaktifkan, sertifikat dicabut, grant/peer kosong; kedua
namespace serta3unit transient dihentikan. CA/database/CRL/backup uji tetap ada.
Firewall root server sama setelah normalisasi counter trafik. Windows10 dan
SERVER masih running; lima guest lain shut off. Produksi belum di-rollout.

Bukti source: suite awal280PASS/1SKIP; fokus sebelum detach117PASS/1SKIP;
platform+internet setelah detach46PASS/1SKIP; fault detach1PASS. Suite fokus
terakhir sedang berjalan; lihat jurnal untuk hasil akhir. Jangan menjumlahkan
suite yang tumpang-tindih. Tidak ada hasil Windows11/fisik mode baru.

Sisa prioritas: perbaiki runner/pastikan active-TCP certificate revocation,
uji native expiry/daemon-stop/active-reboot untuk mode internet, Windows11 dan
PC fisik, readiness dependensi internet yang spesifik, paket final distribusi.
Paket r8 lokal tersimpan di `state/internet-20261027/`, belum menggantikan ZIP
GitHub. Jangan memakai generator kit pilot lama untuk schema2 (masih khusus
0.1.12/schema1). Credential hanya inventaris privat; backup disk/XML tidak di-Git.


## 27 Oktober23:34 — uji ketahanan policy Windows dilanjutkan

Dua guest uji (Windows10 dan SERVER) running lagi setelah seluruh VM mati pada
awal resume23:22. Gateway namespace/WAN direkonstruksi memakai CA sementara,
key dan database uji yang sama; produksi tidak di-rollout. Tidak ada identity
Windows uji yang dibuat sampai checkpoint ini.

**Temuan penting:** reboot yang menyelesaikan update OS menambahkan5allow lokal;
TCP probe Python tetap diblok, namun status policy menolak rule asing. Karena
itu jangan memakai r4/r5 sebagai bukti fail-closed menyeluruh setelah reboot.
Kandidat kini memakai Local GPO milik VanGuard, local rule merging disabled,
89inbound rule lama disalin agar akses masuk tetap, backup/recovery kedua store.
Endpoint domain/policy GPO yang sudah ada ditolak. Legacy schema1 hanya untuk
recovery; connect memerlukan policy schema2. R6 gagal pada duplikasi quarantine
transisi; cache dibetulkan tanpa mengabaikan duplicate aturan izin final.

R7 sedang diuji native, termasuk penambahan local allow yang harus tetap tidak
membuka internet. Recovery legacy dan Local GPO r6 berhasil sebelum retry.
State/task/pemulihan lab perlu diperiksa sebelum tindakan berikutnya; jangan
menimpa CA, profile, identitas atau backup. Laporan/jurnal tetap memisahkan
historis PASS/FAIL. Suite terbaru platform+internet46PASS/1SKIP115,28detik;
17regresi internet sebelumnya PASS, termasuk isolasi grant perangkat kedua.
Sisa: hasilr7, reboot baru, admission/grant/renewal/revoke TCP aktif, cleanup,
rebuild/reinstall paket final dan Windows11/fisik. Belum commit/push kandidat.


## 27 Oktober — mode internet terkelola kandidat0.1.13, pengujian berlangsung

Pengguna meminta implementasi tanpa konfigurasi router. Source opt-in schema2,
gateway nft grant per perangkat+karyawan+sesi+lease, API/dashboard izin internet,
lockdown Windows persisten dan recovery admin telah dibuat di branch feature.
**Belum rilis; ZIP stabil25Oktober tetap0.1.12. Jangan menyimpulkan siap produksi.**

- Baseline lokal69PASS/1SKIP; suite luas kandidat280PASS/1SKIP659,17detik.
  Perbaikan native/status sesudah awal suite mempunyai regresi terpisah; suite
  fokus terbaru sedang berjalan. Hasil Linux/mocks bukan bukti VM.
- Windows10 tambahan dan SERVER running; lima VM lain shut off. Produksi tetap
  tidak di-rollout. Gateway uji dalam namespace `vanguard-internet-test` .100.80,
  memakai CA sementara dan database terpisah; bukan CA utama. HTTPS uji/nft
  syntax/native WAN TCP gateway PASS. Windows10 installer kandidat berhasil.
- Preview/enable native menemukan3bug: kutip Python, alias adaptor belum ada,
  prefix IPv6 /0. Perbaikan tersedia; percobaan r4 sedang berjalan, belum dinyatakan
  PASS. Kegagalan mempertahankan quarantine. Recovery eksplisit dua kali PASS;
  ada task pemulihan **khusus lab**. Jangan membiarkan task/identity uji tanpa cleanup.
- Backup disk offline `vanguard-windows10-before-internet-20261027.qcow2` dan XML,
  backup endpoint/policy guest dipertahankan. Credential uji hanya inventaris
  privat host; source/log publik tidak memuat nilainya.
- Manual tunggal Bab14.1 + HTML menjelaskan mode kandidat dan batasnya. User
  masih harus mendapat internet hanya setelah grant/admission; pengujian
  authorized/revoked/reboot/Windows11 belum selesai, jangan mengklaim PASS.

Bukti/runner lanjutan lokal `state/internet-20261027/`; periksa task
VanGuardInternetTestPhase1/Recovery di Windows10 dan hasil `phase1.json` dalam
`C:\Program Files\VanGuardInternetTest`. Runtime r3 dengan policy r4 yang
tercatat; paket final harus dibangun ulang dan diuji. Jurnal27Oktober berisi
intent, kegagalan dan perbaikan. Selanjutnya selesaikan lockdown/reboot,
enrollment disposable10.8.0.3, grant/revocation/TCP aktif, cleanup, lalu paket/tes.


## 27 Oktober — desain berikutnya tanpa konfigurasi router pengguna

Arahan terbaru pengguna: hindari konfigurasi router setiap client; kendali pusat
pada Linux server/admin. Model router bukan prasyarat berikutnya. Usulan teknis
memerlukan agent Windows dengan pemblokiran persisten di endpoint dan gateway
internet Linux; Linux saja tidak dapat memblokir jalur yang melewati router
langsung. Sebelum agent terpasang, perangkat belum dapat dikendalikan. Server
HTTPS/WireGuard harus reachable dari jaringan client. Full-tunnel, enforcement
persisten dan fail-closed internet masih FITUR_BELUM_TERSEDIA/BELUM_TERUJI.
Tidak ada rollout atau perubahan jaringan pada diskusi ini. Arahan ini mengganti
usulan wajib konfigurasi router pada catatan sebelumnya. Jurnal: [27 Oktober](docs/PROGRESS_2026-10-27.md).


## 27 Oktober — batas kontrol internet diklarifikasi

Audit tujuh gambar Sharing/Dokumentasi TA menunjukkan enrollment, bukan bukti
akses VPN atau pencabutan internet. Profil publik hanya10.8.0.1/32 dan resource
TCP8082. Revoke saat ini memutus peer/akses aplikasi VanGuard; tidak mengendalikan
jalur internet langsung melalui router. Pemblokiran internet sebelum admission
dan setelah revoke adalah FITUR_BELUM_TERSEDIA untuk kebutuhan baru tersebut.
Rancangan berikutnya memerlukan gateway/firewall jaringan terkelola, larangan
WAN langsung, pengecualian bootstrap/manajemen, serta pengujian IPv4/IPv6 dan
koneksi aktif. Model router belum diketahui; jangan mengganti route/firewall
aktif hanya dengan menyalin contoh full-tunnel. Semua VM sekarang shut off;
audit ini read-only, tanpa uji live atau perubahan jaringan. Rincian: [jurnal27Oktober](docs/PROGRESS_2026-10-27.md).
Status running pada26Oktober di bawah adalah riwayat, bukan keadaan terkini.


## 26 Oktober — seluruh VM dinyalakan dan konsol dibuka

Sesuai permintaan pengguna, tujuh VM running: CA, SERVER, ADMIN, CLIENT,
ATTACKER, Windows11, dan Windows10. Lima Ubuntu terbuka pada konsol teks
gnome-terminal/virsh; dua Windows terbuka di virt-viewer. Ketujuh jendela
terverifikasi pada desktop. Windows10 sempat shutdown normal pada start pertama;
start kedua dan pemeriksaan akhir berhasil. Penyebab shutdown belum diuji.
Tidak mengubah source, definisi/disk VM, identitas atau credential; tidak login
otomatis. Readiness aplikasi belum diuji pada tindakan ini. Bukti lokal
`state/vm-start-20261026/final.json`; jurnal `docs/PROGRESS_2026-10-26.md`.
Catatan keadaan VM di bawah adalah riwayat sebelum startup26Oktober.


## 25 Oktober malam — perbaikan konfigurasi Windows tervalidasi

WIN-CONFIG-01 diperbaiki pada source/paket **307b86a**: retry pasangan root/profil
identik memulihkan state parsial tanpa menimpa trust berbeda. Status parsial exit1
dengan penjelasan. [Laporan audit dan batas bukti](docs/AUDIT_WINDOWS_CONFIG_2026-10-25.md).

- ZIP fix1 **44.675.510 byte**, SHA256 `26ba30082b2c21da3a0d81d9670f5ae7e2eb5157cca566b662fbafb2d1790515`.
  Unduhan ulang GitHub byte-identik paket yang diuji. Gunakan ZIP tunggal di main;
  versi aplikasi Python tetap0.1.12, launcher PowerShell diperbaiki.
- Windows10 LTSC19044 **dan** Windows11 build26300: BAT reinstall/status exit0,
  config tetap, **10regresi per VM** dari launcher terpasang PASS; tanpa identitas
  endpoint/tunnel baru.6hash identitas utama Windows11/runtime legacy tetap.
- Linux lokal41PASS/1SKIP0,29s. **CI40212688642 SUCCESS** pada307b86a:
  Linux3.10 268 PASS / 1 SKIP, 277.415 detik; Linux3.12 268 PASS / 1 SKIP, 290.527 detik;
  Windows Server helpers28PASS/2SKIP0,380s +10regresi konfigurasi PASS.
  JUnit/report aktual diunduh; bukti CI tidak menggantikan VM desktop/backend.
- Enam XML original hash-identik. Windows11 running; Windows10/lima Ubuntu
  shut off. Backup sebelum mutasi/credential tetap privat; tidak mengganti CA.
  Bukti lokal `state/bug-review-20261025/`. Commit penutupan hanya dokumentasi;
  source/paket tetap307b86a, main dan feature tetap dua branch.

Tersisa **BELUM_TERUJI**: PC fisik, Windows10 Home/Pro19045, VPN10, UAC/MOTW/GPO,
configure serentak/power-loss serta backlog CA soak/WIN-CLEANUP-02. Lanjut pilot
sesudah backend/trust/routing siap. Tidak ada klaim bebas bug/production-ready.
Catatan berikut adalah riwayat paket r3 sebelum perbaikan ini.

**25 Oktober — installer Windows10/11 dan manual tunggal tervalidasi dan sudah di main.**

[Manual admin18bab](docs/MODUL_PENGGUNAAN_VANGUARD.md) adalah satu sumber resmi; HTML/isi ZIP berasal dari
Markdown yang sama.14tutorial dan3ZIP lama dikeluarkan dari tree aktif, histori
Git tetap. [Paket lengkap](downloads/README.md) memuat BAT, Python3.13.17, WireGuard1.1.1,
20wheel offline dan manual. File ZIP25Oktober44.674.789byte, SHA256
`d0b724f09b82a1684ee80cda09cb7ed86e35b4761675c6a7593fa6fcf7a7ee6f`.

- Windows10 LTSC2021 Evaluation x64 build19044:9smoke/5guards/policy PASS;
  runtime absent→installed terbukti. ZIP final r3 reinstall/status0, config tetap,
  tanpa identity/tunnel. Wrapper policy awal tidak selesai; retry terpisah PASS.
- Windows11 Enterprise Evaluation build26300: r3 preview/reinstall dua kali/status
  **4PASS**, guards5PASS, policy PASS.6hash identitas utama/runtime lama tetap;
  endpoint0.1.12 terpisah dari client legacy0.1.9. Fresh11 tetap bukti24Oktober.
- Linux lokal25Oktober **268PASS/1SKIP795,98s**, builder12PASS0,19s, Ruff/tautan/
  secret scan/paket PASS. Run full24Oktober TERPUTUS, bukan bukti lulus.
  CI40074650339 source29b7afb: Linux3.10/3.12 masing-masing268PASS/1SKIP,
  Windows helpers28PASS/2SKIP; berbeda dari tes VM native.
- Enam XML asli identik; Windows11 running, Windows10 dan lima Ubuntu shut off.
  ISO/seed Windows10 sudah ejected; tidak ada runner/tunnel uji aktif. Backup/key/
  credential hanya lokal. Jangan provisioning/format VM10 atau reset credential.

[Laporan dan batas bukti](docs/VALIDASI_WINDOWS10_2026-10-25.md): Windows10 Home/Pro22H2 native, VPN Windows10,
UAC interaktif/cancel, browser/MOTW/GPO, PC LAN/laptop Wi-Fi tetap BELUM_TERUJI.
CA power-loss/soak/WIN-CLEANUP-02 tetap terbuka; keberhasilan installer bukan
bukti backend sehat. Pilot membutuhkan admin0.1.12, profil/trust/routing dan
alokasi identitas sebelum enrollment/connect; jangan ulang init CA.

Publikasi **e77e0eb** selesai pada main+feature (dua branch, fast-forward).
ZIP unduhan ulang GitHub byte-identik paket native. **CI40171300671 SUCCESS**:
Linux3.10 268PASS/1SKIP278,016s; Linux3.12 268PASS/1SKIP284,573s;
Windows helpers28PASS/2SKIP0,372s. JUnit aktual diunduh. Penutupan berikutnya
hanya dokumentasi; source/ZIP tetap e77e0eb. Berikutnya pilot fisik sesuai
manual setelah backend/trust/routing siap. Bukti privat `state/manual-win10-20261024/`;
jurnal aktif25Oktober. Catatan di bawah merupakan riwayat sebelumnya.



**24 Oktober: installer native selesai dan ZIP sudah di main.**
Baca [checkpoint](docs/CHECKPOINT.md) dan [hasil installer](docs/VALIDASI_INSTALLER_2026-10-24.md).
Paket r6 satu ZIP memuat Python/WireGuard/wheel/BAT/panduan. Missing-runtime native
5PASS, uninstall/reinstall3PASS, guards5PASS, policy PASS. Lokal41PASS/1SKIP.

VM Windows sudah kembali ke XML/disk utama (byte-identik); hash identitas/runtime/SecureBoot/TPM
cocok snapshot awal sesudah boot. Lima Ubuntu tidak diubah/shut off. Jangan boot overlay
lagi. Publikasi52cfac9 sudah dipush ke main+feature; ZIP unduhan ulang GitHub cocok
paket native. Branch kini hanya main dan feature/2026-10-22-physical-endpoints,
histori hardening/fix tetap ada dalam main. CI40072739273 SUCCESS: Linux3.10/3.12 masing-masing268PASS/1SKIP;
Windows helpers28PASS/2SKIP. Source/test/ZIP final tetap52cfac9; penutupan hanya
dokumentasi. Berikutnya pilot PC LAN sesuai runbook, setelah backend/trust/route/
alokasi identitas siap; kemudian laptop Wi-Fi. Tidak ada runner uji yang aktif. Panduan utama: [downloads](downloads/README.md).

UAC interaktif, PC fisik, MOTW/GPO, soak/power-loss CA dan WIN-CLEANUP-02 tetap
BELUM_TERUJI. Jangan ulang init CA/identitas lama atau membuat peer statis.
Kredensial tetap inventaris lokal. Riwayat di bawah bukan status operasional baru.

Panduan dan hasil CI telah dipush pada **c76c8f0**, branch
`feature/2026-10-22-physical-endpoints`; SHA remote terverifikasi.

**23 Oktober15:48WIB — CI kandidat berhasil; PC belum install.**
Workflow39926592953 pada0411127 SUCCESS: Linux3.10/3.12 masing-masing266PASS/1SKIP;
Windows Server2022 helpers28PASS/2SKIP + parse PowerShell PASS. JUnit aktual
tersimpan di state/pilot-continuation-20261023/. Bukan uji installer Windows11
atau PC fisik. Lokal kit/package10PASS; checksum ZIP lama tetap sama.

[Mulai dari ZIP di PC LAN](https://github.com/LuiLuiLui886/vanguard-ztna/blob/31c69816f4860869f3483dab86d3452bdb54333c/downloads/README.md#mulai-di-pc-windows-lan) kini
menjelaskan runtime, ekstraksi, isian installer, exit code dan status awal.
Host masih BLOCKED: Ethernet enp3s0 tanpa IPv4.50.10, Wi-Fi.50.101, enam VM mati;
firewall UNKNOWN (sudo noninteraktif unavailable). Tidak mengubah VM/jaringan.
Lanjutkan pemasangan kandidat di PC dan persiapan backend/trust/jaringan sesuai
runbook; enrollment/connect menunggu siap. Windows11 native/fisik, power-loss,
soak dan WIN-CLEANUP-02 tetap belum ditutup. Lihat checkpoint/jurnal terbaru.

**ZIP kit sudah di GitHub23Oktober:** commit artefak6479c8c tersedia di
branch feature/2026-10-22-physical-endpoints; kedua ZIP di downloads/ diunduh
ulang dari GitHub dan checksum identik lokal (PASS). Baca [README download](downloads/README.md) untuk clone/pull, checksum,
ekstraksi dan installer Windows. Artefak kandidat lama dipertahankan; native/fisik
tetap belum diuji. Gunakan git pull --ff-only pada branch tersebut, lalu buka folder downloads/.

**23 Oktober — seluruh source/dokumentasi sudah dipush.** Branch
`feature/2026-10-22-physical-endpoints`, ref369ac96 dan blob BAT/runbook terverifikasi
remote.10tes lokal PASS; tanpa merge main/rollout/CI baru. ZIP/state/credential
tetap lokal. Hasil dicatat di [jurnal23Oktober](docs/PROGRESS_2026-10-23.md).
Catatan belum-push di bawah merupakan histori22Oktober, bukan larangan terbaru.

**Dokumentasi penerapan revisi2:** [runbook17bab](docs/MODUL_PENGGUNAAN_VANGUARD.md)
mencakup instalasi, topologi, syarat lanjut, troubleshooting, operasi harian dan
serah terima. Modul utama Bab15.5 sudah terhubung. Hasil native/fisik tetap belum
diuji; source aplikasi0.1.12r3 tidak berubah. ZIP dokumen:
`dist/vanguard-dokumentasi-penerapan-20261022-r2.zip`; kit lengkap terbaru:
`dist/vanguard-installation-20261022-docs-r2.zip`.103tautan/12blokbash valid;
hash dan hasil lengkap ada pada checkpoint/jurnal.

**Persiapan pemasangan nyata22 Oktober:** topologi lama dikonfirmasi pengguna.
Baca [panduan langkah instalasi](docs/MODUL_PENGGUNAAN_VANGUARD.md) dan checkpoint
terbaru. Kit menggabungkan Windows r3/profil publik/wheel admin/checklist/pemeriksa
read-only.10tes lokal tambahan PASS; native Windows dan pilot masih belum diuji.
Preflight host BLOCKED: Ethernet pilot belum siap dan tiga backend mati. Belum
mengubah VM/router/endpoint atau push. Kit `dist/vanguard-installation-20261022.zip`101anggota terverifikasi tersedia;
hash ZIP/manifest pada checkpoint/jurnal. Buka START_HERE.html.


Cek ulang GitHub22 Oktober13.00WIB: belum ada prompt baru; main235df05 dan
master prompt tidak berubah, kedua branch lain/PR#1 tanpa instruksi tambahan.
Tetap lanjut dari hasil lokal di bawah sesuai batas persiapan; tidak ada push.


**22 Oktober — kandidat endpoint Windows0.1.12 disiapkan lokal.** Fokus master
prompt235df05 ENDPOINT_WINDOWS pada branch
`feature/2026-10-22-physical-endpoints`, dasar040dc21, commit implementasi52976be. Jangan checkout main0.1.8
mengganti hardening terbaru. Lima repo/tujuh branch diperiksa; prompt agent hanya
VanGuard. Batas terbaru **tidak push/publish atau menerapkan VM/router/jaringan/
endpoint aktif** pada tugas persiapan ini.

Profil publik, import bundle tervalidasi, scoped disconnect, allowlist TLS,
generator pilot dan kandidat installer offline tersedia. Paket lokal
`dist/endpoint-windows-0.1.12-candidate-r3.zip`; gunakan r3, bukan kandidat pertama.
Runtime Python3.13x64/WireGuard harus tersedia, paket unsigned. Identity/key tetap
client; installer/import/login tidak menambah peer. Native Windows dan pilot
PC LAN/laptop Wi-Fi BELUM_DIJALANKAN; jangan klaim siap distribusi.

Full suite r2 **260PASS/1SKIP501,29detik** pada Linux/Python3.12.3. Skip ACL
Windows native. Baseline81PASS/1SKIP, terarah109PASS/1SKIP, package4PASS adalah
suite overlap, jangan dijumlahkan. Full run pertama TERPUTUS, bukti disimpan.
Baca [checkpoint](docs/CHECKPOINT.md), [pilot lengkap](docs/ENDPOINT_WINDOWS_PILOT.md),
[jurnal22 Oktober](docs/PROGRESS_2026-10-22.md), serta
[modul tunggal Bab15.3](docs/MODUL_PENGGUNAAN_VANGUARD.html).

Enam VM teramati mati dan tidak diubah. Ethernet host belum tersambung; jaringan
aktif masih Wi-Fi.66/24, bukan router pilot.50/24. IP tunnel.5/.6 baru usulan,
periksa registry. Sebelum rollout, verifikasi admin/arsitektur perangkat, trust,
libvirt/host firewall/routing lalu jalankan matriks native secara terpisah dengan
otorisasi tahap penerapan. WIN-CLEANUP-02/CApowerloss/soak belum ditutup.
Kredensial tetap hanya inventaris privat. Catatan di bawah adalah histori.

**21 Oktober — patch kapasitas CA selesai.** Unit CA dari40c7f74 kini satu
worker/8thread. Paket CA/server/admin tetap0.1.11; client/attacker/Windows0.1.9.
Timeout, TLS, lock, identitas dan admission tetap. Regresi TLS nyata membuktikan
thread penuh memblokir handshake;16tes lokal PASS. CI39575685564 SUCCESS:
219PASS/1SKIP masing-masing Linux3.10/3.12,28PASS/2SKIP helper Windows.

Postflight93/93HTTP200; tambahan beban yang sama seperti baseline menghasilkan
120/120HTTPS berhasil dan40/40probe server ready (sebelumnya36/120 serta3/40
failure). Backup/unit/invariant/hash/enam XML PASS, nol peer/grant. Lima Ubuntu
running, Windows shut off. Kriteria mitigasi skenario terukur terpenuhi; bukan
jaminan overload tak terbatas. Bukti di state/hardening/2026-10-21-parallel/.

Lanjutkan soak, WIN-CLEANUP-02 dan power-loss media CA yang BELUM_TERUJI.
Jangan ulang rollout unit atau restore index/CRL/database. Main/hardening tetap
terpisah. Baca [checkpoint](docs/CHECKPOINT.md),
[catatan kapasitas](docs/CA_SERVICE_CAPACITY.md), [jurnal](docs/PROGRESS_2026-10-21.md)
dan [modul tunggal](docs/MODUL_PENGGUNAAN_VANGUARD.html). Credential hanya lokal.
Catatan di bawah merupakan riwayat sebelum patch kapasitas, bukan status terbaru.

**21 Oktober — CA/server/admin0.1.11 sudah terpasang.** Optimasi publikasi CA
menghindari rewrite file identik dan menggabungkan fsync direktori; manifest
penuh dan roll-forward tetap berlaku. Benchmark terisolasi2,458–2,606 menjadi
1,165–1,201detik. Lokal218PASS/1SKIP; CI39572681808 SUCCESS Linux218/1 pada
masing-masing3.10/3.12 dan Windows helper28/2. Source e0e58dd sudah dipush pada
`fix/2026-10-20-readiness-lock`; main/hardening belum digabung.

Backup ketiga layanan terverifikasi,23anggota aplikasi per VM/15hash/invariant
CA/enam XML terjaga. Nol peer dan grant kosong. Lima Ubuntu running, Windows
shut off; client/attacker/Windows tetap0.1.9. Jangan reset password/enrollment.
Postflight HTTPS31HTTP200/2HTTP503; diagnosis60sampel berikutnya ready tetapi
memakai probe admin terinstrumentasi. Belum boleh menyatakan readiness stabil.

Pengukuran HTTPS penutup: berurutan30/30HTTP200, paralel29HTTP200/1HTTP503,
liveness3/3HTTP200. Bukti gagal tetap disimpan.

Lanjutkan diagnosis503 dashboard, soak, WIN-CLEANUP-02 dan bukti power-loss CA.
Jangan restore state CA/database atau menebak counter. Baca [checkpoint](docs/CHECKPOINT.md),
[jurnal aktif](docs/PROGRESS_2026-10-21.md), [rincian patch](docs/READINESS_0.1.10.md)
dan [modul tunggal](docs/MODUL_PENGGUNAAN_VANGUARD.html). Runner rollout sudah
selesai; jangan dijalankan ulang. Credential dan backup hanya di lokasi privat.
Bagian berikut merupakan riwayat, bukan status paket/VM terkini.

**20 Oktober — rollout0.1.9 dan matriks VM selesai.** Lima Ubuntu dan satu
Windows dipertahankan. Linux/Windows live lulus untuk lifecycle, resource gate,
logout bersamaan renewal, reboot aktif, revoke TCP, penggantian immutable serta
akun disabled. Seluruh identitas disposable dicabut, akun uji disabled, grant
kosong, nol peer; task/config/tunnel Windows bersih dan demo sementara dihentikan.

CA/server/admin/Windows running; client Ubuntu/attacker mati untuk RAM. Invariant
CA, enam XML, hash identitas utama dan Secure Boot/TPM PASS. CI0695e03 SUCCESS:
205 PASS/1 SKIP pada masing-masing Linux3.10/3.12,28 PASS/2 SKIP Windows helper.
Jangan menjumlahkan suite overlap atau menyebut helper sebagai pengujian VPN.

**Lanjutan yang diperlukan:** power-loss media CA BELUM_TERUJI; reproduksi
WIN-CLEANUP-02 (interupsi segera setelah instalasi) sebelum mengubah recovery
otomatis. Config wajib dipertahankan sampai ownership dan service berhenti
terkonfirmasi. HEALTH-LOCK-01/P2: readiness sementara503 karena shared lock CA
berbenturan dengan transaksi;30sampel18ready/12konflik lock, bukan kerusakan
invariant/CRL. Liveness200 tidak berarti readiness stabil. Verifikasi retry
terbatas/deadline sebelum perubahan. Jangan ulang enrollment identitas uji lama
atau restore index/CRL.
Benchmark boot berulang/soak panjang belum dilakukan. Source/perbaikan arsip
sudah pada branch `hardening/2026-10-18-resilience`. Fetch terakhir menemukan
origin/main76af7e6 berisi dokumentasi endpoint/installer yang belum digabung;
main lokal c454c0c tetap. Baca catatan integrasi pada checkpoint sebelum tugas baru.

Baca [checkpoint](docs/CHECKPOINT.md), [matriks bukti](docs/VALIDASI_ROLLOUT_2026-10-20.md),
[jurnal aktif](docs/PROGRESS_2026-10-20.md), serta
[modul tunggal](docs/MODUL_PENGGUNAAN_VANGUARD.html). Credential tetap hanya di
inventaris privat host. Riwayat berikut dipertahankan sebagai bukti historis;
status IN_PROGRESS atau versi lama di dalamnya bukan status operasional terkini.

**19 Oktober2026 — hardening kandidat teruji; Windows timer diperbaiki.**
Source0.1.9 dan modul sudah dipush ke branch `hardening/2026-10-18-resilience`
(publikasi aplikasi84f4a81, timer Windows42028cf); main tetap c454c0c. CA/lifecycle/logout/readiness/
resource/audit belum di-rollout ke layanan utama. Linux lengkap199 PASS/1 SKIP,
client final29 PASS/1 SKIP, Windows native28 PASS/2 SKIP. Jangan jumlahkan suite
yang overlap; perintah tunnel pada native memakai stub.

VM Windows yang sama sudah memakai clock/timer Hyper-V. Microbenchmark waktu
turun2,63–3,18detik ke0,045–0,051detik per sejuta panggilan; boot penuh hingga
SSH27,49detik pada satu sampel. Secure Boot,TPM,hash identitas dan kelima XML
Ubuntu terjaga. Windows running/viewer tersedia; lima Ubuntu shut off. Paket
utama Windows masih0.1.8;0.1.9 hanya staging. Password tidak diubah.

CI39283176466 untuk42028cf terakhir queued, bukan PASS. Langkah berikutnya periksa hasil CI,
lalu rollout dengan backup dan matriks VPN guest termasuk expiry/revoke/reboot.
Baca [checkpoint](docs/CHECKPOINT.md), [audit](docs/AUDIT_HARDENING_2026-10-18.md),
[rollout](docs/HARDENING_0.1.9.md), [Windows](docs/WINDOWS_CLIENT.md) dan
[jurnal aktif](docs/PROGRESS_2026-10-19.md). Bukti privat:state/hardening/2026-10-19/.

**17 Oktober 2026 — seluruh materi sudah menjadi satu modul.**
Gunakan [modul utama](docs/MODUL_PENGGUNAAN_VANGUARD.md) atau
[satu HTML siap baca/cetak](docs/MODUL_PENGGUNAAN_VANGUARD.html).
Materi CA/PKI lengkap sekarang berada di bab 5.3 (13 subbagian), dilanjutkan
instalasi, administrasi dan pemakaian Ubuntu/Windows dalam dokumen yang sama.
Alamat panduan CA lama hanya menunjuk ke modul agar tautan historis tetap hidup.
Validasi kelengkapan, Bash, tautan/fragment, rahasia dan renderer PASS; bukti di
state/documentation/2026-10-17/unified-module-validation.json. Tidak ada perubahan
VM atau CA. Siap commit/push; hasil publikasi dicatat di jurnal.
Langkah berikutnya praktik memakai modul dan lanjutkan gap operasional checkpoint.

**17 Oktober 2026 — rincian CA/PKI selesai disusun dan divalidasi.**
Bab 5.3 modul sekarang menjelaskan generate CA dan tahapan terkait. Baca
[panduan CA/PKI lengkap](docs/MODUL_PENGGUNAAN_VANGUARD.md) atau
[HTML siap cetak](docs/MODUL_PENGGUNAAN_VANGUARD.md), mencakup 13 bagian dari konsep
hingga backup dan troubleshooting. Uji CA sementara di host PASS, termasuk
signing TLS/perangkat dan penolakan sertifikat setelah revoke. Struktur kedua
dokumen, sintaks contoh Bash, tautan dan scan rahasia PASS. Bukti di
state/documentation/2026-10-17/. Tidak mengubah CA/VM produksi.
Panduan/modul sudah dipush pada commit 7e54bb5; remote main terverifikasi cocok.
CI commit dokumentasi belum dinyatakan lulus; lihat jurnal untuk hasil publikasi.
Pekerjaan operasional berikutnya tetap mengikuti checkpoint di bawah.

**17 Oktober2026 — modul penggunaan lengkap.** Tugas terbaru: audit checkpoint,
modul teknisi/admin/karyawan, dan akses password console Windows. Baca
[modul lengkap](docs/MODUL_PENGGUNAAN_VANGUARD.md) atau
[HTML siap cetak](docs/MODUL_PENGGUNAAN_VANGUARD.html).

Keenam VM ditemukan shut off; tugas ini tidak menjalankan deployment atau tes
live ulang. Bukti15 Oktober menunjukkan satu renewal otomatis Windows PASS
(61,83detik), cleanup PASS dan CI78ff14e SUCCESS. Bukti lease expiry terakhir
tetap IN_PROGRESS. Counter CA pernah dipulihkan, durability belum diperbaiki.

Password Windows tersedia pada kartu lokal
`/home/lui/VanGuard-Privat/AKSES_WINDOWS_TERBARU.txt`; akun/password tidak diubah.
Kredensial tetap di luar Git. Kartu/inventaris0600 dan folder0700.
Modul/HTML tervalidasi sudah dipush ke main: commit modul d162980 tercakup pada
remote e9104a4 yang telah dicocokkan. Pengguna meminta push setelah informasi
visibility public disampaikan; visibility tidak diubah. Referensi repository
private di catatan historis tidak menggambarkan status sekarang.
Berikutnya jalankan sesi pengguna mengikuti modul serta periksa health saat boot.
Lihat [checkpoint](docs/CHECKPOINT.md) dan [jurnal17 Oktober](docs/PROGRESS_2026-10-17.md).

## Riwayat handoff15 Oktober

**Status operasional terbaru 15 Oktober 13:38 WIB:** host sempat reboot;
enam VM ditemukan mati. CA, SERVER dan Windows sedang dinyalakan bertahap.
Hasil integrasi di bawah adalah bukti sebelum reboot. Uji lease-expiry/renewal
otomatis terinterupsi, belum dinyatakan lulus. CI78ff14e sudah SUCCESS.

**15 Oktober 2026 — client Windows tambahan berhasil diuji langsung.**

- Enam domain tetap ada; lima definisi Ubuntu sama dengan backup awal.
- Windows 11 Enterprise Evaluation build 26300, Secure Boot/TPM aktif,
  LAN `192.168.100.60`, tunnel `10.8.0.4`. Login console dan SSH key-only PASS;
  SSH hanya dari host `.1`. Kedua CD sudah dikeluarkan; seed/backup privat tetap.
- Windows memakai client **0.1.8**, Python 3.13.16 dan WireGuard 1.1.1.
  23 tes native Windows PASS. Cleanup menunggu service benar-benar terhapus;
  timeout/error mempertahankan config untuk inspeksi. Ubuntu tidak di-upgrade.
- Akun karyawan Windows terpisah, enrollment lewat admin HTTPS/TOTP dan root CA
  bundle terverifikasi. Registrasi/login tidak menambah peer. Sesi invalid serta
  proof invalid ditolak. Admission sah, handshake, ping dan admission ulang PASS.
- Dua client Ubuntu `.2` dan Windows `.4` aktif bersamaan: dua handshake/ping PASS.
  Cleanup Windows PASS; Ubuntu tetap bisa ping. Ini bukti integrasi awal, bukan
  seluruh skenario keamanan atau benchmark formal Windows.
- OpenSSH bawaan terinterupsi; fallback resmi Microsoft Win32-OpenSSH MSI
  `10.0.0.0p2-Preview` berhasil, hash/tanda tangan terverifikasi. Paket GitHub ini
  perlu pemeliharaan manual; rincian pada panduan Windows.
- Windows, CA, SERVER, ADMIN dan CLIENT running saat pemeriksaan; ATTACKER mati.
  Tunnel Windows sudah ditutup setelah tes; jalankan `connect` untuk pemakaian.
  Autologon dinonaktifkan. Password/username hanya inventaris privat host.
- Bukti privat: `state/deployment/windows-2026-10-15/`; backup pra-enrollment:
  `state/backups/before-windows-enrollment-20261015/`. Jangan rollback CA index/CRL.

Berikutnya: uji pencabutan menggunakan identitas disposable, renewal otomatis
jangka panjang dan reboot Windows, lalu gap proposal/benchmark yang masih terbuka.
Baca [jurnal 15 Oktober](docs/PROGRESS_2026-10-15.md) dan
[panduan Windows](docs/WINDOWS_CLIENT.md). Status push/CI dicatat setelah selesai.

## Catatan historis

**14 Oktober 2026 — IN PROGRESS: pemulihan instalasi client Windows tambahan.**
Lima Ubuntu tetap utuh dan shut off selama instalasi (RAM host terbatas).
ISO resmi selesai, SHA256 cocok hash penerbit. Instalasi kemarin terputus saat
image apply 90%; disk tidak bootable, bukan OS siap pakai. Backup disk sudah dibuat
sebelum recovery. Setup berjalan kembali memakai partisi yang ada, dengan seed
pemulihan tanpa wipe/format. Jangan jalankan ulang script first-install atau seed awal.

VM-CLIENT-WINDOWS: 4 GiB, 2 vCPU, 80 GiB, UEFI Secure Boot/TPM, VNC localhost.
LAN .60/tunnel .4 masih rencana sampai dibuktikan guest. Source 0.1.7 `3467802`
sudah di GitHub private, CI Linux masing-masing 160 PASS + 1 SKIP dan Windows
20 PASS; VPN guest/enrollment/firewall live belum dilakukan. Baca
[jurnal 14 Oktober](docs/PROGRESS_2026-10-14.md),
[checkpoint](docs/CHECKPOINT.md) dan [panduan Windows](docs/WINDOWS_CLIENT.md).
Bukti privat: `state/deployment/windows-2026-10-14/`.

**12 Oktober 2026: 0.1.6 live, push, dan CI selesai.** Dashboard terbaru
terpasang pada VM-ADMIN; empat VM lain tetap 0.1.5. Tes admin terakhir 26 PASS;
verifikasi HTTPS/TOTP final 4/4 PASS dan arsip 17 aktivitas terverifikasi.
CI final: 137/137 PASS pada Python 3.10 dan 3.12, tanpa error/failure/skip.
Perbaikan sesuai audit proposal
mencakup health dashboard, audit admin, alasan/waktu pencabutan, history/validity
sertifikat dan bundle publik. 132 tes lokal + 132 guest PASS; UI HTTPS live dan
pilot clear/VanGuard n=1 PASS. Identity, firewall dan health akhir PASS.
Source 0.1.5 `8eeffaa` sudah dipush private; CI sebelumnya masing-masing 132 tes
Python 3.10/3.12 lulus. Source awal 0.1.6 `a478111` dan revisi final `49dd332`
sudah dipush private; CI final lulus pada kedua versi Python.

Baca AGENTS.md, VANGUARD_CONTEXT.md, [checkpoint](docs/CHECKPOINT.md) dan
[jurnal 12 Oktober](docs/PROGRESS_2026-10-12.md) sebelum melanjutkan.

- [Catatan revisi proposal per bagian](docs/SARAN_REVISI_PROPOSAL_2026-10-12.md)
  memuat konflik arsitektur, contoh redaksi, metrik dan perbaikan daftar pustaka.
- [Tutorial dari awal sampai akhir](docs/MODUL_PENGGUNAAN_VANGUARD.md),
  [aktivitas dan arsip 0.1.6](docs/MODUL_PENGGUNAAN_VANGUARD.md), serta
  [fitur dashboard 0.1.5](docs/MODUL_PENGGUNAAN_VANGUARD.md).
- [Hasil pilot dan batas kesimpulan](docs/BENCHMARK_PILOT_2026-10-12.md);
  seri formal tiga konfigurasi × 10 belum dijalankan.
- Kredensial hanya di komputer ini:
  `/home/lui/VanGuard-Privat/KREDENSIAL_VANGUARD.md`, di luar repository.
  Admin/VPN utama dan password console lima VM tersedia di sana; jangan unggah.
- Bukti privat: `state/deployment/audit-2026-10-12/`; backup sebelum 0.1.5:
  `state/backups/before-0.1.5-2026-10-12/`.

VM sempat ditemukan mati sesudah interupsi. Pemulihan counter CRL kosong dan
config client tertinggal dicatat pada jurnal serta `shutdown-recovery.json`.
Pemulihan COMPLETE; data revocation lama dipertahankan. Jangan mengembalikan
CA index/CRL lama. Sesi VPN utama berakhir **12 Oktober 2026 21:39:08 WIB**;
perlu login ulang saat expired.

Identity ulang/cleanup PASS, firewall 40 pemeriksaan PASS, health 7/7 selama
82,75 detik dengan nol removal. Inventaris kredensial lokal sudah diperbarui.
Tahap dashboard 0.1.6 selesai dan terdokumentasi. Berikutnya lanjutkan gap proposal
serta isu operasional yang masih tercatat pada checkpoint.
Setelah itu lanjutkan gap proposal: baseline WG membutuhkan pengecualian admission eksplisit,
renewal sertifikat, notifikasi, Windows, resource policy dan bukti TCP/aplikasi.
Jangan menjalankan eksperimen .3 bersamaan atau recreate topologi lima node.

GitHub: [repository private](https://github.com/LuiLuiLui886/vanguard-ztna),
branch main; CLI `state/tooling/github/cli/usr/bin/gh`.
[Laporan aktif](docs/IMPLEMENTATION_REPORT.md), [arsip resume](docs/LANJUTKAN_PROYEK_2026-10-10.md).
TOTP HP pribadi dan reboot workstation belum terverifikasi.
Seluruh TA belum selesai. Update checkpoint/resume sebelum berhenti.
Tindak lanjut operasional: ketahanan counter CA terhadap shutdown mendadak dan
warning control socket Gunicorn; lihat checkpoint untuk bukti pemulihan.

12 Oktober 2026 16:11 WIB: kelima VM running; login password console pada ttyS0
terverifikasi dan lima jendela terminal sudah dibuka untuk pengguna. Password tidak
diubah. Sesi console sengaja dibiarkan aktif; Ctrl+] melepaskan console tanpa
mematikan VM. Bukti ada pada `state/deployment/console-login-2026-10-12/`.

Dashboard 0.1.6 menyimpan snapshot arsip admin pada VM-ADMIN dan salinan final lokal
privat `state/deployment/activity-0.1.6/final-check/admin-activity.zip` mode 0600.
Backup pra-upgrade dan backup final tersedia pada `state/backups/`.
