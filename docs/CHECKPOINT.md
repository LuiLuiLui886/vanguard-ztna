# Checkpoint VanGuard — 30 Oktober 2026

## 30 Oktober — uji kelayakan dan panduan EXE dari nol

**Keputusan: layak untuk uji lab terkontrol, belum penerimaan produksi penuh.**
[Laporan lengkap](UJI_KELAYAKAN_2026-10-30.md) memisahkan scope/bukti dan8temuan.
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

Manual tunggal [Bab14.0.1.1](MODUL_PENGGUNAAN_VANGUARD.md) kini9langkah EXE:
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

Manual tunggal [Bab1.1](MODUL_PENGGUNAAN_VANGUARD.md) kini memuat5diagram:
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
Lihat [validasi EXE](VALIDASI_EXE_2026-10-29.md); bukti privat `state/exe-20261029/`.

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

Laporan: [audit wizard](AUDIT_WIZARD_2026-10-29.md). Template admin0.1.14-fix1 menggantikan template
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

Laporan: [validasi setup terpadu](VALIDASI_SETUP_TERPADU_2026-10-29.md); manual tunggal Bab14.0 diperjelas.
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
retained. Laporan [validasi setup terpadu](VALIDASI_SETUP_TERPADU_2026-10-29.md) dan jurnal29Oktober membedakan bukti.

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
cleanup tetap berjalan saat guard gagal. Lihat [audit bug](AUDIT_BUG_2026-10-28.md) untuk file/fungsi,
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
jaringan, tanpa mengklaim rerun. Lihat [laporan Windows11](VALIDASI_WINDOWS11_INTERNET_2026-10-28.md).

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
terkelola tanpa perubahan router. [Laporan bukti](VALIDASI_INTERNET_2026-10-27.md) dan [manual tunggal
Bab14.1](MODUL_PENGGUNAAN_VANGUARD.md) memisahkan status kandidat dari rilis.

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
usulan wajib konfigurasi router pada catatan sebelumnya. Jurnal: [27 Oktober](PROGRESS_2026-10-27.md).


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
audit ini read-only, tanpa uji live atau perubahan jaringan. Rincian: [jurnal27Oktober](PROGRESS_2026-10-27.md).
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
dengan penjelasan. [Laporan audit dan batas bukti](AUDIT_WINDOWS_CONFIG_2026-10-25.md).

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

[Manual admin18bab](MODUL_PENGGUNAAN_VANGUARD.md) adalah satu sumber resmi; HTML/isi ZIP berasal dari
Markdown yang sama.14tutorial dan3ZIP lama dikeluarkan dari tree aktif, histori
Git tetap. [Paket lengkap](../downloads/README.md) memuat BAT, Python3.13.17, WireGuard1.1.1,
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

[Laporan dan batas bukti](VALIDASI_WINDOWS10_2026-10-25.md): Windows10 Home/Pro22H2 native, VPN Windows10,
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



## Installer Windows lengkap — native selesai dan ZIP sudah di main

Source5aa6e9f memperbaiki BAT default-policy, ACL SID native dan uninstall yang
menghapus script-nya sendiri. ZIP r6 **44.649.724byte** memuat Python3.13.17,
WireGuard1.1.1,20wheel dan panduan setup→CSR→admin→import→login/connect.
[Download/petunjuk](../downloads/README.md), [hasil lengkap](VALIDASI_INSTALLER_2026-10-24.md).

- Native Windows11 build26300: reuse runtime7kasus lulus sebelum bug uninstall
  ditutup; r6 uninstall/reinstall3PASS; guards5PASS; default/explicit policy PASS.
- Native disk overlay dengan runtime absent: **5PASS**, BAT exit0, Python3.13.17,
  WireGuard1.1.1, VanGuard0.1.12; pip check/status PASS, tanpa identitas/tunnel.
- Overlay sudah shutdown normal dan XML disk utama dikembalikan **byte-identik**.
  Hash identitas utama, Python3.13.16, WG1.1.1, client0.1.9 dan SecureBoot/TPM
  cocok snapshot awal setelah boot disk utama. Lima Ubuntu
  tetap shut off. Backup dan overlay dipertahankan, tidak memulihkan state CA.
- Linux lokal41PASS/1SKIP0,38detik; Ruff PASS. CI39998238177 pada2e6ec76 SUCCESS:
  Linux3.10 **268PASS/1SKIP288,229s**,3.12 **268PASS/1SKIP292,874s**;
  Windows helpers **28PASS/2SKIP0,429s**. CI ini mendahului fix uninstall5aa6e9f.
- ZIP identik yang diuji: SHA256
  `91b551183f1f197d7390e32b31ff4de3da33ef62261e73fba572784b05b396dd`.
 36anggota/20wheel/25file aplikasi cocok source, hash/secret scan nested PASS.
- Kredensial tidak diubah dan tetap hanya inventaris privat. Identitas utama
  tidak dipakai untuk enrollment tes; installer0.1.12 terpisah dari client0.1.9.

**Publikasi52cfac9 selesai:** ZIP/docs/runner sudah dipush ke main dan feature.
Main fast-forward dari235df05 melalui merge histori827c664, tanpa force. Dua refs
lama hardening/fix dihapus sesudah terbukti ancestor main; commit/histori utuh,
backup Git bundle tetap lokal. Hanya main dan feature/2026-10-22-physical-endpoints
tersisa lokal/remote; default main dan visibility public dipertahankan. ZIP dari
raw GitHub commit52cfac9 diunduh ulang:44.649.724byte/hash identik paket native.
CI [40072739273](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/40072739273)
pada52cfac9 **SUCCESS**: Linux3.10 **268PASS/1SKIP272,198s**, Linux3.12
**268PASS/1SKIP289,868s**, Windows helpers **28PASS/2SKIP0,333s**. JUnit aktual
diunduh. Pengujian VM native tetap bukti terpisah. Commit penutup hanya docs;
source/test/ZIP tetap identik dengan52cfac9. Modul dan runbook MD/HTML sudah
mengikuti BAT baru. Tidak ada runner native yang masih aktif.

**BELUM_TERUJI:** UAC interaktif/cancel, PC LAN/laptop Wi-Fi fisik, distribusi
MOTW/GPO, reboot-required/runtime1618 nyata, soak panjang, power-loss media CA,
WIN-CLEANUP-02. Jangan menyatakan production ready. Backend/jaringan pilot belum
diaplikasikan pada tugas installer. Admin0.1.12+profil/trust/alokasi ID/IP dan
resource grant perlu disiapkan sebelum enrollment/koneksi fisik.

Bukti privat `state/installer-20261024/`, jurnal `PROGRESS_2026-10-24.md`.
Pemulihan disk sudah selesai; jangan menjalankan prepare_overlay.py lagi.
Langkah berikutnya: ikuti downloads/SETUP_WINDOWS untuk PC LAN, selesaikan backend
admin0.1.12+profil, routing/trust dan alokasi identitas sebelum connect; lalu laptop
Wi-Fi dan uji simultan. Tidak ada installer/prasyarat tambahan yang perlu diunduh
untuk jalur runtime yang telah dibundel. Hasil fisik wajib dicatat terpisah.

## Lanjutan PC LAN dan validasi CI — 23 Oktober 15:48 WIB

Panduan dan hasil CI telah dipush pada **c76c8f0**, branch
`feature/2026-10-22-physical-endpoints`; SHA remote terverifikasi.

Pengguna mengonfirmasi ZIP belum diekstrak/installer belum dijalankan. Panduan
[Mulai di PC Windows LAN](https://github.com/LuiLuiLui886/vanguard-ztna/blob/31c69816f4860869f3483dab86d3452bdb54333c/downloads/README.md#mulai-di-pc-windows-lan)
kini memuat urutan runtime, ekstraksi/checksum, tiga input installer, exit code,
dan status normal sebelum configure/enrollment. Kedua ZIP lama tetap identik.

[CI39926592953](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/39926592953)
pada **0411127** SUCCESS, JUnit diunduh dan diperiksa:

- Ubuntu22.04/Python3.10: **266 PASS/1 SKIP**,282,577detik.
- Ubuntu22.04/Python3.12: **266 PASS/1 SKIP**,282,436detik.
- Windows Server2022/Python3.12 helpers: **28 PASS/2 SKIP**,0,272detik;
  parsing PowerShell bootstrap/endpoint/pilot juga berhasil. Ini bukan fresh
  install Windows11, UAC atau tunnel nyata. Skip Windows adalah dua tes lock
  POSIX; skip Linux memerlukan API ACL Windows asli.
- Lokal Linux: **10 PASS**,0,078detik, khusus kit/package; suite overlap tidak
  dijumlahkan. Checksum ZIP,7tautan README/anchor, validasi modul/secret scan PASS.

Host15:42WIB **BLOCKED**: Ethernet enp3s0 UP tanpa IPv4 pilot.50.10, Wi-Fi
.50.101/24, keenam VM shut off. Firewall nftables/iptables **UNKNOWN** karena
inspeksi sudo noninteraktif tidak tersedia. Flag forwarding/bridge bukan bukti
koneksi. Tidak ada perubahan VM/router/host/endpoint atau credential.

Tidak ada bug implementasi baru yang dibuktikan pada sesi ini. Pemasangan native
Windows11, uji PC LAN/laptop Wi-Fi dan koneksi simultan tetap **BELUM_DIJALANKAN**
(perilaku belum diuji). Gap WIN-CLEANUP-02, soak dan power-loss CA tetap terbuka.
Berikutnya: pasang prasyarat/kit di PC, kemudian siapkan backend, trust, alokasi
identitas dan jaringan sesuai runbook sebelum enrollment/connect. Jangan
menambahkan peer statis atau mengulang init identitas utama.

Bukti privat: `state/pilot-continuation-20261023/`; hasil publikasi panduan dicatat
pada jurnal. Source aplikasi/installer tetap kandidat0.1.12 yang diuji0411127.

## ZIP instalasi tersedia di GitHub —23 Oktober

Commit artefak **6479c8c** telah dipush non-force pada branch
`feature/2026-10-22-physical-endpoints`. Dua ZIP kini berada di downloads/ dan
ikut clone/pull biasa. Baca [petunjuk download](../downloads/README.md) serta
[checksum](../downloads/SHA256SUMS). Tidak memerlukan Git LFS atau release terpisah.

- Kit lengkap12.421.751byte, SHA256
  `19ede36ca3967f4717e012e3d027e341331bc837fda57cbc8255eefceb078f30`.
- Dokumentasi338.739byte, SHA256
  `3a5b707a3fb191a2c684a70323b091dd00af97d81e70be623b1a22f8922f6b41`.
- Kedua artefak diunduh ulang dari raw GitHub pada commit6479c8c; ukuran dan
  SHA256 identik lokal, PASS. Ref remote juga cocok commit publikasi.
- ZIP/manifests/nestedwheel/secret scan PASS;20wheel Windows tersedia. Aplikasi,
  installer dan konfigurasi tidak berubah. Native/fisik tetap BELUM_DIJALANKAN.
- dist/state tetap diabaikan secara umum, kredensial/privatekey/stateVM tetap
  lokal. Izin pengguna untuk ZIP menggantikan pembatasan artefak sebelumnya.

Bukti state/publication-20261023/zip/. Tidak ada merge main atau perubahan VM/
jaringan. Paket adalah snapshot22Oktober: README downloads/checkpoint Git ini
menjelaskan publikasi yang terjadi23Oktober.

## Publikasi pembaruan —23 Oktober selesai

Branch `feature/2026-10-22-physical-endpoints` sudah dipush non-force ke GitHub.
Ref remote369ac96 cocok HEAD lokal sesudah publikasi; blob installer BAT dan
runbook INSTALL_REALWORLD.md juga cocok melalui API GitHub. Semua implementasi
serta dokumentasi sampai e9162aa ikut, ditambah catatan otorisasi publikasi.

Validasi hari ini:10tes kit/package PASS0,36detik, Ruff/pip check/diffcheck PASS,
201blob unik pada5commit baru+perubahan pending lolos inventory-secret scan;
modul/tautan/syntax dan izin inventaris PASS. Tidak menjalankan CI baru atau
mengulang suite penuh hari ini. Bukti state/publication-20261023/.

Source installer BAT/PowerShell, source aplikasi, builder, tests dan panduan kini
tersedia remote. ZIP/wheel di dist, state dan credential tetap lokal; tidak
membuat release atau merge main. Tidak ada perubahan VM/router/endpoint. Native
Windows installer/pilot fisik tetap BELUM_DIJALANKAN. Catatan no-push22Oktober
bersifat historis dan digantikan izin eksplisit pengguna23Oktober.

## Pembaruan dokumentasi penerapan — revisi2

Artefak terbaru: `dist/vanguard-dokumentasi-penerapan-20261022-r2.zip` (338.739byte)
dan kit lengkap `dist/vanguard-installation-20261022-docs-r2.zip` (12.421.751byte).
ZIP kit SHA256 `19ede36ca3967f4717e012e3d027e341331bc837fda57cbc8255eefceb078f30`;
manifest `4649b11f89a18ba08da9df32fe4e30aa0b940796f86eedcb06dd045df1ce701e`.
17bab,103tautan/anchor,12blokbash syntax dan secret scan PASS.101anggota kit
hash PASS; windows/backend/checks/config byte-for-byte identik dengan kit lama.
Native Windows/physical tidak diuji pada pekerjaan dokumentasi ini. Artefak lama
utuh; gunakan revisi docs-r2 untuk panduan terbaru. Bukti state/realworld-docs-20261022/.

INSTALL_REALWORLD.md/.html sekarang berisi17bab bernomor, daftar isi dan petunjuk
pembaca. Tambahan: rencana/topologi, syarat lanjut/berhenti per tahap, observasi
aman, native checklist, troubleshooting, bukti penerimaan, operasi harian dan
serah terima. Modul utama Bab15.5 menautkan bagian yang sesuai, termasuk CA Bab5.3.
Tidak ada perubahan aplikasi/installer/VM/jaringan/credential atau hasil native
baru. Kit dokumentasi revisi2 disiapkan dengan mempertahankan artefak sebelumnya;
hash/hasil validasi akhir dicatat dalam jurnal22 Oktober. Tugas ini tidak push.


## Status terbaru — kit pemasangan nyata (persiapan lokal)

Pengguna mengonfirmasi router.50/24, host Linux+VM, PC Windows LAN dan laptop
Windows Wi-Fi. Panduan **INSTALL_REALWORLD.md/.html** menyediakan langkah operator/
pengguna lengkap, backup, runtime resmi, admin upgrade, enrollment/demo dan rollback.
Modul tunggal Bab15.4 menautkan panduan. Source aplikasi/installer r3 tidak diubah.

Baru: scripts/build_realworld_kit.py menyatukan kandidat Windows r3, profil/root
publik yang diserialisasi ulang, wheel admin yang cocok, kandidat firewall, demo,
pemeriksa host/endpoint read-only dan checklist60kasus. deploy/pilot/verify_kit.py
menolak hash salah, anggota tambahan/hilang serta symlink. Root dari bundle tetap
bukan trust independen; fingerprint dan key wajib dicek ke layanan aktif.

Tes tambahan lokal **10PASS** (kit/host assessment/package); bukan uji native.
Host preflight aktual13.25WIB **BLOCKED**: Ethernet.50.10 belum tersedia dan
VM-CA/SERVER/ADMIN shut off. Bridge/forwarding flag saja tidak membuktikan jalur.
Keenam VM tetap ada/mati, jaringan masih Wi-Fi.66/24. Tidak ada live mutation/push.
Kit final `dist/vanguard-installation-20261022.zip` tersedia,12.403.926byte,
101anggota hash PASS. ZIP SHA256
`30d08dac0fbf4964ff75e07d4dbc96e0f997105dbabb9519d3284433babc5b6c`;
manifest `e4e942e40fc621094d12e2fbd6ab55a4cf6943949490d0746f0e35251aa0a9ef`.
Buka START_HERE.html atau docs/INSTALL_REALWORLD.html sesudah verifikasi hash.
Panduan80tautan lokal/11blokbash dan credential scan PASS.
Runtime installer tidak disertakan; Python3.13x64/WireGuard dari sumber resmi
wajib diverifikasi. PowerShell baru/native installer/fisik BELUM_DIJALANKAN.

Berikutnya: selesaikan backup/router/kabel/IP dan inspeksi host/libvirt firewall;
validasi root/key/alokasi lalu uji native dan PC dahulu, laptop, keduanya. Jangan
memulihkan CA lama atau mengklaim produksi. Bukti state/realworld-20261022/.

## Riwayat — hasil kandidat endpoint dan pemeriksaan prompt

## Status terbaru — persiapan endpoint fisik dan Windows0.1.12

Pemeriksaan ulang GitHub22 Oktober13.00WIB: **belum ada prompt baru**. Fetch/API
mengonfirmasi main235df05,fix040dc21,hardening52e31db; master prompt remote identik
lokal. PR#1 tidak memiliki body/komentar instruksi baru. Commit implementasi52976be
dan handoffbc514d5 tetap menjadi hasil lokal terbaru; tidak ada tes/rollout/push
baru pada pemeriksaan ini. Lihat jurnal22 Oktober untuk bukti pemeriksaan.

Fokus master prompt235df05: **ENDPOINT_WINDOWS, lokal saja**. Lima repo/tujuh
branch GitHub akun lokal diperiksa; hanya VanGuard mempunyai prompt tugas agent.
Source dasar040dc21 bersih dipertahankan, branch baru
`feature/2026-10-22-physical-endpoints`, commit implementasi lokal **52976be**.
Tidak merge source main0.1.8. Tidak push,
publish release atau menerapkan perubahan VM/router/host/endpoint sesuai batas
master prompt yang diminta pengguna. Semua hasil paket di bawah kandidat lokal.

- Profil schema1 konsisten antara generator/admin/client; API HTTPS dan WG endpoint
  tidak lagi terkunci alamat lab bila profil diberikan. Root/key diperiksa, route
  /32 dan resource eksplisit, tunnel10.8/24 tetap sesuai registry server.
- Import bundle cocok original request/private keys/root/profil tanpa overwrite
  identitas atau memberikan peer. Init dengan profil wajib ID/IP dialokasikan.
- Disconnect scoped meminta proses pemilik membersihkan tunnel; logout server
  tetap berbeda. Cleanup gagal mempertahankan config. Launcher memeriksa overlap
  subnet/route sebelum admission. Admission enam cek+sesi tetap wajib.
- Helper TLS menerima DNS/IP tambahan hanya melalui allowlist operator; diuji
  pada CA sementara. Generator profil/firewall physical hanya generate-only.
- Kandidat Windows BAT/PowerShell offline, staging runtime, mutex, guard install
  terputus, launcher dan uninstall preserve identity. Target buildcp313/win_amd64,
  Python/WireGuard harus sudah terpasang. Unsigned, BELUM_UJI_TARGET.
- Paket `dist/endpoint-windows-0.1.12-candidate-r3.zip`,20wheel/27anggota manifest,
  12.007.094byte. ZIP SHA256
  `689f3b2303fe7f5d4b03c31f8b32a6aa9b6adcf152a4c75232e37794eb942f61`.
  Manifest SHA256 `47b50e47e156e1b41ff11ffba01e0e76433eb5f96cfde81b4b6df8361f530cb1`.
  Build ulang identik, hash/dependency closure/cross-platform pip offline dry-run
  PASS; bukan native install. Kandidat pertama dan wheel awal tetap disimpan.
- Baseline lokal81PASS/1SKIP; terarah109PASS/1SKIP; package-final4PASS. Jangan
  menjumlahkan suite overlap. Suite penuh pertama TERPUTUS tanpa JUnit; runr2
  selesai **260PASS/1SKIP dalam501,29detik**, Python3.12.3/Linux. Skip ACL native
  Windows pada Linux. Bukti full-linux-r2.xml/log; tidak ada VM/network test baru.
- Ruff/pip check/bash syntax PASS; modul15bab/39blokbash/65tautan/15tabel valid,
  scan credential dan izin inventaris privat PASS. PowerShell native tidak ada
  di host; parse PS pada workflow baru BELUM_DIJALANKAN, tidak push/run CI.

Kondisi audit22 Oktober: keenam VM **shut off**, tidak dinyalakan/diubah. Ethernet
enp2s0 NO-CARRIER, Wi-Fi host192.168.66.9/24; backend NAT virbr-vg.100.1/24.
Firewall host berprivilege belum dapat dibaca noninteraktif. Paket VM terakhir
tercatat0.1.11 CA/server/admin,0.1.9 client/attacker/Windows; bukan pemeriksaan
service hidup hari ini. Plan router.50.1,host.50.10,PC.50.20,laptop.50.30 belum
terpasang. Usulan tunnel.5/.6 belum dialokasikan; .2/.3/.4 tetap dicadangkan.

Bukti lokal `state/endpoint-20261022/`; public-pilot berisi profil/root/admin env/
network-plan, server-firewall.candidate.nft hanya kandidat. Kredensial tidak diubah,
tetap inventaris privat di luar Git. Tidak ada backup/live rollout baru karena
tidak ada perubahan aktif. Panduan [pilot](ENDPOINT_WINDOWS_PILOT.md),
[jurnal](PROGRESS_2026-10-22.md), [modul tunggal Bab15.3](MODUL_PENGGUNAAN_VANGUARD.html)
menjelaskan audit, langkah admin/pengguna, backup dan rollback terencana.

Berikutnya: setelah persiapan lokal selesai, penilaian paket/native Windows secara
terpisah (UAC/ACL/path/hash/fresh/reinstall/repair/upgrade/uninstall/interupsi/key
preservation), lalu penerapan jaringan yang disetujui. Verifikasi model/router,
admin/build/arsitektur kedua endpoint, host firewall/libvirt chain/return path,
registry alokasi, root/key terhadap layanan aktif; pilot PC dahulu, laptop lalu
bersamaan. Prasyarat otomatis/shortcut GUI/signing/ARM64 belum tersedia. Semua
hasil fisik BELUM_DIJALANKAN. WIN-CLEANUP-02/power-loss CA/soak tetap tersisa;
jangan restore CA lama atau menganggap kandidat menutup masalah itu.

## Riwayat21 Oktober — kapasitas HTTPS CA terverifikasi

Source konfigurasi40c7f74 sudah dipush dan unit CA kini **satu worker/8thread**.
Paket CA/server/admin tetap0.1.11, client/attacker/Windows0.1.9. Tidak ada perubahan
timeout, verifikasi TLS, lock CA, admission, credential atau identitas perangkat.

- HEALTH-CAPACITY-01/P2: empat thread sebelumnya dapat penuh oleh fan-out probe
  serta CRL daemon. Regresi Gunicorn/TLS nyata gagal saat handshake koneksi
  kelima sebelum patch;16tes terarah lokal PASS34,71detik sesudah patch.
- CI39575685564 SUCCESS pada40c7f74: masing-masing Linux3.10/3.12 **219PASS/1SKIP**,
  Windows helper **28PASS/2SKIP**. Tidak mengulang tunnel Windows pada pekerjaan ini.
- Backup CA/unit169file terverifikasi, systemd-analyze verify PASS, unit aktif
  cocok source8thread;15hash identitas/state, invariant CA,23anggota paket per
  layanan dan enam definisi VM tetap. Nol peer dan grant kosong.
- HTTPS asli dari VM-ADMIN **93/93HTTP200** (90readiness paralel+3liveness),
  maksimum2,934detik. Dengan tambahan probe diagnostik: HTTPS120/120 berhasil
  (maks2,173detik), server40/40ready (maks2,662detik). Sebelum perubahan, pola
  yang sama menghasilkan36/120HTTPS503 dan3/40serverunknown. Semua hasil lama
  disimpan; ini bukti skenario terukur, bukan jaminan beban tak terbatas.
- Lima Ubuntu running; Windows shut off. Tidak ada runner VM tersisa setelah
  penutupan. Credential hanya di inventaris privat host dan tidak diubah.

Bukti privat baru: `state/hardening/2026-10-21-parallel/`. Rollout unit selesai;
jangan menjalankan ulang rollout.py. Pemulihan hanya unit4thread yang di-backup,
reload systemd dan restart terencana; **jangan restore state CA/database**.
Arsip source0.1.11 lama tetap dipertahankan; patch unit ada pada Git40c7f74 dan
harus dipasang bersama source terkini, bukan diasumsikan ikut upgrade wheel.

Baca [catatan kapasitas](CA_SERVICE_CAPACITY.md), [jurnal](PROGRESS_2026-10-21.md),
[modul](MODUL_PENGGUNAAN_VANGUARD.html) dan [audit](AUDIT_HARDENING_2026-10-18.md).
**Berikutnya:** soak dan kapasitas lebih tinggi BELUM_TERUJI; WIN-CLEANUP-02
perlu reproduksi race startup/cleanup dengan ownership terkonfirmasi; power-loss
media CA tetap BELUM_TERUJI. Jangan menambah timeout atau menganggap seluruh
failure OS/overload sudah ditangani. Main/hardening belum digabung.

## Riwayat21 Oktober — rollout paket0.1.11 sebelum patch kapasitas

Source e0e58dd di branch `fix/2026-10-20-readiness-lock` sudah dipush.
Perubahan `Publication.publish_file/recover` mempertahankan file identik dan
menggabungkan barrier direktori, dengan fsync setiap inode serta seluruh parent
sebelum commit dihapus. Manifest penuh, lock, staging dan roll-forward tetap
wajib. Tidak ada restore index/CRL, tebakan counter, atau perubahan admission.

- Lokal Linux218PASS/1SKIP488,85detik;34 tes terarah PASS86,54detik.
  CI39572681808 SUCCESS: Linux3.10/3.12 masing-masing218PASS/1SKIP;
  Windows helper28PASS/2SKIP. Helper bukan pengujian tunnel Windows VM.
- Benchmark CA sementara bergantian (tiga tiap versi,77anggota/74identik):
  0.1.10=2,458–2,606detik;0.1.11=1,165–1,201detik. Ini bukan SLA atau bukti
  power-loss disk. Bukti awal yang tidak stabil tetap disimpan.
- Rollout CA/server/admin0.1.11 selesai setelah backup konsisten terverifikasi;
  pip check,23anggota aplikasi per VM,15hash identitas/state, invariant CA,
  enam definisi VM, nol peer dan grant kosong PASS. Pemulihan jika perlu hanya
  paket0.1.10, dengan state terbaru tetap dipertahankan.
- Postflight HTTPS awal31HTTP200/2HTTP503, maksimum1,731detik. Dua503 pada
  admin dependency server. Diagnosis tambahan60sampel ready maksimal1,764detik
  memakai probe admin terinstrumentasi, bukan seluruhnya endpoint dashboard.
  Ini tidak membatalkan hasil gagal. HEALTH-LOCK-01 masih mitigasi parsial.
- Lima Ubuntu running; Windows shut off. Client Ubuntu/attacker/Windows tetap
  0.1.9. Tidak ada perubahan password, key, enrollment atau service Windows.
  Inventaris credential hanya di direktori privat host, tidak dikirim ke GitHub.

Baca [jurnal21 Oktober](PROGRESS_2026-10-21.md),
[catatan readiness/CA](READINESS_0.1.10.md), [audit](AUDIT_HARDENING_2026-10-18.md)
dan [modul tunggal](MODUL_PENGGUNAAN_VANGUARD.html). Bukti privat:
`state/hardening/2026-10-21-readiness/`. Jangan mengulang runner rollout yang
sudah mempunyai rollout-steps.json atau menimpa hasil gagal.


Pengukuran HTTPS penutup21 Oktober: berurutan30/30HTTP200 (maks1,074detik),
paralel29HTTP200/1HTTP503 (maks2,314detik), liveness3/3HTTP200. Satu503 pada
admin dependency server; CA/database ready. Ini membatasi klaim: optimasi CA
terukur, tetapi readiness paralel belum stabil. Bukti final-https-samples.json
tersimpan privat; seluruh hasil gagal sebelumnya dipertahankan.

**Pekerjaan tersisa:** diagnosis503 pada HTTPS dashboard dengan pembuktian
akar masalah sebelum patch; soak beban; power-loss media CA BELUM_TERUJI;
WIN-CLEANUP-02 membutuhkan reproduksi interupsi startup dan ownership sebelum
pemulihan otomatis. Jangan hapus config ketika service belum pasti berhenti.
Main/hardening belum digabung; perubahan origin/main76af7e6 harus dipertahankan.

## Riwayat20 Oktober — rollout0.1.9 dan matriks VM selesai

Semua enam node sudah memakai **0.1.9** pada branch
[hardening/2026-10-18-resilience](https://github.com/LuiLuiLui886/vanguard-ztna/tree/52e31dbbfb044306fdd1bddcbee9dd5f42608c59).
Branch hardening masih terpisah dari main. Baca [matriks bukti](VALIDASI_ROLLOUT_2026-10-20.md) dan
[jurnal 20 Oktober](PROGRESS_2026-10-20.md); riwayat di bawah bukan status terkini.

- Ubuntu dan Windows VM asli: admission/handshake/HTTP, default-deny/LAN/port,
  TCP aktif setelah grant/revoke, dua renewal otomatis, natural lease expiry,
  session expiry terarah, CA outage/recovery, daemon stop/watchdog, logout
  race/idempotensi/scope, reboot aktif dan fresh admission PASS. Replacement
  memakai ID dan dua key baru dari client, akun/IP tetap; disable akun PASS.
- Seluruh identitas disposable Linux/Windows direvoke, kedua akun disabled,
  grant kosong dan nol live peer. Task/tunnel/config uji Windows sudah hilang;
  demo HTTP sementara dihentikan. Jangan ulang enrollment identitas uji lama.
- CA invariant setelah seluruh pencabutan PASS. Enam definisi VM sama dengan
  backup; hash root/key/config utama CA/server/admin dan lima file identitas
  utama Windows cocok. Secure Boot/TPM, versi0.1.9 dan pip check Windows PASS.
- Liveness ketiganya200; readiness sementara503 pada CA/dependensinya terbukti
  akibat konflik lock. Diagnosis30sampel:18ready,12BlockingIOError saat lock,
  tanpa kegagalan invariant/CRL. **HEALTH-LOCK-01/P2** belum diperbaiki; jangan
  mengartikan liveness200 sebagai seluruh dependency siap.
- CA/server/admin/Windows running; Ubuntu client dan attacker shut off untuk
  membatasi RAM host. Keenam VM tetap ada, tidak ada node diganti.
- CI [39382689148](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/39382689148)
  pada0695e03 SUCCESS: **205 PASS/1 SKIP** masing-masing Ubuntu Python3.10/3.12;
  **28 PASS/2 SKIP** Windows helper. Tiga regresi ZIP lokal PASS. CI helper tidak
  menggantikan bukti tunnel VM, dan suite overlap tidak dijumlahkan.
- Perbaikan AUD-T01 sudah dipush: pemeriksaan credential memindai isi setiap
  anggota ZIP, bukan byte kontainer terkompresi. Tidak ada bukti kebocoran pada
  arsip aplikasi. Modul tetap satu Markdown/HTML termasuk CA/PKI.

**Pekerjaan tersisa:** power-loss disk/host CA masih **BELUM_TERUJI**, berbeda
dari SIGKILL/transaksi terisolasi. WIN-CLEANUP-02 masih risiko P2: interupsi segera
setelah instalasi pernah meninggalkan service RUNNING/Disabled melewati timeout;
config ditahan dan operator berhasil stop/uninstall1060 setelah ownership cocok.
Normal cleanup dan recovery reboot lulus, tetapi bukan bukti seluruh kegagalan OS
pulih otomatis. Berikutnya reproduksi terkontrol pada identitas disposable dan
salinan CA khusus untuk uji durability; jangan restore index/CRL lama atau menebak
counter. Untuk HEALTH-LOCK-01, ukur durasi contention lalu uji retry terbatas
tanpa melonggarkan unknown/deadline/read-only. Benchmark boot berulang dan soak
beban panjang belum dilakukan.

Bukti privat: `state/deployment/hardening-20261019-2316/` dan
`state/deployment/hardening-20261020/`. Password tidak diubah; inventaris privat
hanya diperbarui status akun uji. Jangan commit bukti berisi credential/key.
Dokumentasi penutup53ea89c sudah dipush dan SHA remote cocok; pencatatan hasilnya
ada di jurnal aktif. Tidak ada runner pengujian VM yang masih berjalan.

Fetch penutup menemukan `origin/main` maju ke76af7e6 dengan dokumentasi dosen
serta spesifikasi endpoint fisik/installer Windows; main lokal tetap c454c0c.
Perubahan upstream itu tidak mengubah source aplikasi dan belum digabung ke
branch ini. [Spesifikasi pada main](https://github.com/LuiLuiLui886/vanguard-ztna/blob/76af7e63ec8e90e80377721f0d0bd6d07f1ba0da/CODEX_VANGUARD_MASTER_PROMPT.md)
adalah lingkup persiapan lanjutan yang terpisah, bukan fitur yang sudah selesai.
Pertahankan kedua histori saat integrasi; jangan menimpa checkpoint terbaru
dengan status historis pada main.

## Riwayat19 Oktober: kandidat0.1.9 teruji dan timer Windows diperbaiki

Branch [hardening/2026-10-18-resilience](https://github.com/LuiLuiLui886/vanguard-ztna/tree/52e31dbbfb044306fdd1bddcbee9dd5f42608c59).
CA b922f03, lifecycle/features65c486e dan dokumentasi84f4a81 sudah dipush;
SHA remote84f4a81 terverifikasi; commit timer42028cf juga sudah dipush.
Main tetap c454c0c. Hasil artefak/publikasi ada di [jurnal19 Oktober](PROGRESS_2026-10-19.md).
Kandidat aplikasi belum di-rollout ke CA/server/admin/client utama.

- Baseline Linux18 Oktober163 PASS/1 SKIP. Full19 Oktober199 PASS/1 SKIP,
  663,47detik; suite dimulai sebelum tiga tes lock ditambahkan. Client final
  tersendiri29 PASS/1 SKIP. Suite overlap tidak dijumlahkan.
- Windows native final28 PASS/2 SKIP khusus POSIX; sesudah timer berubah,
  ulangi28 PASS/2 SKIP (0,68detik). ACL/locking native, command tunnel memakai stub.
- Provision XML2 PASS; Ruff,pip check,Bash,build wheel/23berkas cocok source,
  CLI dan validasi modul/scan rahasia PASS. Bukti state/hardening/2026-10-19/.
- TCP/nftables namespace VM-ATTACKER PASS untuk LAN/port deny dan TCP aktif
  revoke/expiry; wg0 berupa veth. Watchdog transient systemd dan stop hook PASS.
  Ini bukti18 Oktober, bukan pengujian ulang VPN atau unit produksi.
- Windows yang sama memakai hypervclock/vpindex/synic/stimer. Microbenchmark
  sejuta pembacaan waktu turun2,63–3,18detik ke0,045–0,051detik. SSH sesudah
  boot penuh27,49detik; satu sampel, bukan jaminan waktu desktop umum.
  Secure Boot/TPM dan hash identitas PASS. XML lima Ubuntu sama. Backup XML,
  hasil sebelum/sesudah dan recovery pada [panduan Windows](WINDOWS_CLIENT.md).
- Akhir pemeriksaan: Windows running dengan viewer; lima Ubuntu shut off.
  Password tidak di-reset; credential/bukti privat tetap hanya di host.
  Paket Windows utama masih0.1.8; kandidat0.1.9 diuji di staging.
- CI terbaru [39283176466](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/39283176466)
  untuk42028cf masih queued pada pemeriksaan terakhir; belum dinyatakan PASS.
  Pembatalan run84f4a81 diminta karena sudah digantikan.
- BELUM_TERUJI: rollout0.1.9 utama, Windows VPN revoke/reboot tunnel aktif,
  seluruh matriks lifecycle guest, power-loss disk dan benchmark boot berulang.
  Selanjutnya periksa CI, ikuti [backup/rollout](HARDENING_0.1.9.md) dan gunakan
  identitas disposable untuk matriks VM. Jangan rollback CA/index/CRL.

Baca [audit/resolusi](AUDIT_HARDENING_2026-10-18.md). Modul gabungan bagian15.1/15.2
memuat fitur kandidat dan pemakaian Windows setelah perbaikan.

## Terbaru: satu modul lengkap termasuk CA/PKI

Sesuai permintaan pengguna, seluruh panduan CA telah digabung ke bab 5.3
[modul utama](MODUL_PENGGUNAAN_VANGUARD.md), tersedia sebagai
[satu HTML siap baca/cetak](MODUL_PENGGUNAAN_VANGUARD.html).
Ada 13 subbagian CA dengan daftar isi HTML yang dapat diklik. Alamat panduan
lama menjadi penunjuk ke modul; riwayat materi tetap ada dalam Git.

- Validasi PASS: 15 bab, 39 blok Bash, 55 tautan HTML, 15 tabel; seluruh 22 blok
  contoh dari panduan CA lama tetap ada. ID/tujuan fragment HTML valid, scan
  rahasia/permission privat, Ruff renderer dan git diff --check PASS.
- Bukti: state/documentation/2026-10-17/unified-module-validation.json.
  Ini penggabungan dokumentasi; tidak menjalankan contoh pada VM atau mengubah CA.
  Bukti kriptografi terisolasi sebelumnya tetap berlaku sebagai bukti historis.
- Siap commit/push; hasil publikasi dicatat di jurnal. Berikutnya gunakan modul
  tunggal untuk praktik; gap operasional Windows/durability CA tetap terbuka.

## Terbaru: penjelasan generate CA secara rinci

Bab 5.3 modul diperluas dan ditautkan ke [panduan CA/PKI](MODUL_PENGGUNAAN_VANGUARD.md)
serta [HTML siap cetak](MODUL_PENGGUNAAN_VANGUARD.md). Panduan 13 bagian menjelaskan
root/key, CSR, signing HTTPS, trust, issuance perangkat, CRL/revoke, backup,
masa berlaku dan troubleshooting dengan lokasi eksekusi/hasil setiap langkah.

- Uji CA sementara di host PASS: parameter root, penolakan init ulang, CSR/TLS,
  IP salah ditolak, profil perangkat/cache retry, CRL satu jam dan pencabutan
  menghasilkan error 23. Bukti privat: state/documentation/2026-10-17/ca-guide-validation.json.
- Struktur modul PASS: 15 bab, 25 blok Bash, 28 tautan, 11 tabel. Panduan CA:
  13 bagian, 21 blok Bash, 15 tautan, 5 tabel. Scan rahasia, Ruff renderer dan
  git diff --check PASS. Tidak ada pemeriksaan visual/PDF baru.
- Tidak mengubah aplikasi, CA produksi, trust, key, akun atau VM. Transfer SSH,
  restart layanan dan backup pada panduan tidak dijalankan di lab pada tugas ini.
- Panduan/modul sudah dipush pada commit 7e54bb5; SHA remote main cocok.
  Hasil publikasi dicatat di jurnal. CI commit dokumentasi belum dinyatakan lulus.
  Gap operasional sebelumnya tetap terbuka; langkah berikutnya sesi pengguna
  mengikuti modul, lalu pengujian Windows/durability CA sesuai daftar di bawah.

## Terbaru: modul penggunaan dan audit bukti

Tugas terbaru pengguna adalah modul lengkap dan akses password Windows.
[Modul Markdown](MODUL_PENGGUNAAN_VANGUARD.md) dan
[HTML siap baca/cetak](MODUL_PENGGUNAAN_VANGUARD.html) memuat15bab untuk teknisi,
admin dan karyawan, dari instalasi hingga penggunaan/arsip/shutdown.

- Pemeriksaan17 Oktober: keenam VM shut off. Tidak ada boot/deployment atau
  pengujian VPN live ulang pada tugas dokumentasi ini.
- Bukti15 Oktober: automatic-renewal.log PASS, dua admission berjarak61,83detik
  dengan cleanup. Ini satu siklus, bukan soak test. lease-expiry-after-renewal.json
  tetap IN_PROGRESS; penghapusan peer setelah expiry belum terbukti.
- CA pernah dipulihkan13457→13458, signature/revocation/index/key terjaga.
  Pemulihan tidak membuktikan masalah durability counter telah diperbaiki.
- CI78ff14e/run38692866340 SUCCESS: Linux3.10/3.12 masing-masing163 PASS+1 SKIP;
  Windows23 PASS. Bukti tersimpan di state/deployment/windows-2026-10-15/.
- Kartu console Windows: /home/lui/VanGuard-Privat/AKSES_WINDOWS_TERBARU.txt,
  dibuat dari inventaris lokal tanpa reset. Login terakhir terverifikasi15 Oktober.
  Folder0700, inventaris/kartu0600; nilai rahasia tidak masuk modul atau Git.
- Modul tervalidasi:15bab,22blok Bash,26tautan HTML,10tabel; scan rahasia/ruff PASS.
  Modul commit d162980 sudah dipush; remote main e9104a4 terverifikasi.
  Pengguna meminta push setelah informasi repository public disampaikan.
  Visibility tetap public; catatan private pada riwayat bukan status saat ini.
- Langkah berikutnya: gunakan modul untuk sesi pengguna, periksa health dan sesi
  akun saat boot; lanjutkan durability CA, lease expiry, revocation Windows dan
  reboot tunnel aktif dengan bukti baru. Jangan ulangi init/enrollment utama.

Catatan15 Oktober di bawah adalah riwayat. Hasil yang lebih baru pada paragraf
di atas menggantikan status renewal yang sebelumnya masih terinterupsi.
Lihat [jurnal17 Oktober](PROGRESS_2026-10-17.md) untuk validasi/push dokumentasi.

## Riwayat checkpoint15 Oktober

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
Baca [jurnal 15 Oktober](PROGRESS_2026-10-15.md) dan
[panduan Windows](WINDOWS_CLIENT.md). Status push/CI dicatat setelah selesai.

## Catatan historis 14 Oktober

**IN PROGRESS: pemulihan instalasi Windows tambahan.** Seluruh lima Ubuntu
utuh dan shut off selama setup. VM keenam running: 4 GiB, 2 vCPU, 80 GiB,
UEFI Secure Boot/TPM2, VNC localhost. Rencana LAN .60/tunnel .4 tetap.

- ISO selesai dan SHA256 cocok hash Microsoft EN-US. Instalasi 13 Oktober
  terputus pada image apply 90%; EFI kosong, C:\Windows belum ada.
- Backup disk sebelum recovery: volume libvirt
  `vanguard-windows-before-recovery-20261014.qcow2`. Jangan hapus bukti/backup.
- Setup diulang pada partisi disk0/3 yang ada, menggunakan seed privat
  `vanguard-windows-recovery-auto-20261014.iso` **tanpa DiskConfiguration**.
  Seed awal yang memformat disk telah dikeluarkan. Jangan memakai ulang seed
  awal, recreate disk/domain, atau mengulang first-install script.
- Setup masih berlangsung; OS/login/SSH/VPN **belum dinyatakan berhasil**.
  Periksa console, lalu laporan guest `C:\ProgramData\VanGuard\windows-setup.json`.
  Setelah bootstrap, keluarkan media seed; kredensial hanya inventaris lokal.
- Source 0.1.7 `3467802` dipush private. CI `38366413893` sukses: Linux3.10/3.12
  masing-masing160 PASS +1 SKIP; Windows20 PASS. Belum bukti tunnel guest nyata.
- Bukti privat `state/deployment/windows-2026-10-14/`, log guest lama disalin ke
  `C:\VG-Recovery-20261014`. [Jurnal](PROGRESS_2026-10-14.md),
  [panduan Windows](WINDOWS_CLIENT.md). Autostart tetap mati.

Tahap 0.1.6 sebelumnya selesai dan dipush (`49dd332`, dokumentasi `aa291f1`), CI
137 PASS Python 3.10/3.12. VM-ADMIN terakhir 0.1.6; empat Ubuntu lain 0.1.5.
Catatan running 12 Oktober di bawah merupakan bukti historis, bukan status hari ini.

## Keadaan dan bukti

- CA .10, SERVER .20, CLIENT .30, ADMIN .40, ATTACKER .50 pada 192.168.100.0/24.
  Tunnel server 10.8.0.1/client 10.8.0.2; identitas uji sementara .3.
- Rollout/integritas COMPLETE: 14 berkas aplikasi per VM cocok source saat rollout,
  config/CA/key/identitas utama cocok backup. Tidak reenrollment utama.
- Dashboard baru: health, audit admin, alasan/waktu revoke, validity/history,
  bundle publik. [Panduan](MODUL_PENGGUNAAN_VANGUARD.md).
- VM-ADMIN: 0.1.6 mencatat tindakan dengan waktu WIB, uraian Indonesia, filter
  50/halaman dan arsip CSV/JSON/manifest. [Panduan](MODUL_PENGGUNAAN_VANGUARD.md).
- 137 tes lokal PASS; HTTPS/TOTP archive workflow live PASS. Bukti dan ZIP 0600:
  `state/deployment/activity-0.1.6/live/`.
- Backup konsisten admin sebelum migrasi:
  `state/backups/before-0.1.6-2026-10-12/`.
- [Pilot benchmark](BENCHMARK_PILOT_2026-10-12.md) selesai n=1; iperf3 3.9 tersedia
  pada client/server, tanpa daemon permanen. Pilot gagal 10 Oktober dipertahankan.
- Bukti aktif: `state/deployment/audit-2026-10-12/`.
  Backup: `state/backups/before-0.1.5-2026-10-12/`.
- Sesi utama terakhir di `resume.json` berakhir **12 Oktober 2026 21:39:08 WIB**;
  tidak diperpanjang oleh renewal atau boot. Periksa expiry aktual sebelum demo.
- Kredensial lokal: `/home/lui/VanGuard-Privat/KREDENSIAL_VANGUARD.md` di luar repo,
  mode 0600; folder 0700. Password console lima VM disiapkan, SSH tetap memakai key.
  Password admin/VPN utama cocok hash aktual. Akun uji lama dicatat tanpa mengarang
  password yang hanya tersimpan sebagai hash.

## Pemulihan dan hasil akhir lab

VM ditemukan mati lagi sesudah interupsi. Sesudah boot, identity gagal akibat
counter CRL kosong dan client tertahan config tunnel sisa. Backup CA dibuat
sebelum pemulihan counter secara monoton; jangan mengembalikan index/CRL lama.
`shutdown-recovery.json` **COMPLETE**: signature CRL valid, nomor 11641 ke 11642,
index/key/root/serial tetap dan seluruh revocation lama dipertahankan. Config
client lama dibackup setelah interface dipastikan mati; tunnel utama pulih.

Identity ulang **COMPLETE/PASS**, termasuk proof/binding/replay, CA-only revoke
dan cleanup. Firewall **40 pemeriksaan PASS**, API tanpa otorisasi dan bypass LAN
ditolak. Health **7/7 PASS selama 82,75 detik**, dua deadline lease, nol removal.
Tidak ada eksperimen aktif. Inventaris privat terbaru memuat satu admin, 22 akun
karyawan (satu aktif) dan lima akun console; nilai rahasia tidak masuk Git.

Source 0.1.5 `8eeffaa` dipush private dan CI-nya masing-masing 132 PASS Python
3.10/3.12. Source awal 0.1.6 `a478111` sudah dipush dan CI lulus. Revisi pencatatan
akses dashboard/filter/arsip dipush sebagai `49dd332`; CI `38232712179` lulus
137/137 pada Python 3.10 dan 3.12, nol failure/error/skip. Artefak terverifikasi
tersimpan lokal pada `state/deployment/ci-49dd332/`. Jangan jalankan eksperimen
.3/benchmark bersamaan. Backup CA sebelum repair ada pada direktori bukti audit.

## Sesi berikutnya

1. Baca AGENTS.md, VANGUARD_CONTEXT.md, checkpoint dan jurnal terbaru.
2. Periksa lima domain lama; jangan recreate lab/CA. Autostart VM masih nonaktif.
3. Preflight lalu health dengan direktori bukti baru. Login ulang karyawan secara
   privat jika expired, sesuai [panduan](MODUL_PENGGUNAAN_VANGUARD.md).
4. Lanjutkan gap [matriks proposal](PROPOSAL_ALIGNMENT.md) dan
   [saran revisi](SARAN_REVISI_PROPOSAL_2026-10-12.md). Baseline WG tanpa admission
   belum diotorisasi; [rencana isolasi/cleanup](BENCHMARK_PLAN.md) sudah tersedia.
5. Catat intent sebelum perubahan dan hasil sesudahnya. Credential/state/key/disk
   tetap lokal. GitHub private; CLI `state/tooling/github/cli/usr/bin/gh`.

S-01 kuantitatif tetap bukti 0.1.4; S-03/S-04 ICMP tetap bukti 0.1.3, tidak diulang
penuh. [Laporan aktif](IMPLEMENTATION_REPORT.md), [tutorial](MODUL_PENGGUNAAN_VANGUARD.md),
[checkpoint lama](CHECKPOINT_2026-10-10.md). Login HP pribadi,
reboot workstation, serta penyebab shutdown belum terverifikasi.
Tindak lanjut operasional: ketahanan counter CA saat shutdown mendadak dan warning
control socket Gunicorn pada sandbox service; API dan admission sudah lulus uji akhir.
Status 0.1.6 diperbarui 12 Oktober: deployment dashboard VM-ADMIN final telah lulus.
Tes admin setelah perubahan terakhir 26 PASS; verifikasi HTTPS/TOTP final 4/4 PASS.
Wheel final terpasang dengan force-reinstall setelah ditemukan pip mempertahankan
wheel versi sama. Backup kedua menjaga database yang sudah berisi arsip uji.
Arsip final 17 baris, ZIP dan hash isi cocok, tanpa password/seed TOTP. Rincian
dan bukti privat ada pada `docs/PROGRESS_2026-10-12.md`. Source/dokumen final sudah
dipush private; CI Python 3.10/3.12 masing-masing 137 PASS. Empat VM lain tetap
0.1.5 dan tidak perlu di-rollout.

## Console operator — 12 Oktober 2026 16:11 WIB

Lima VM running dan login password console sudah terverifikasi pada `/dev/ttyS0`.
Lima jendela GNOME Terminal terbuka, masing-masing tersambung ke VM-CA, VM-SERVER,
VM-CLIENT, VM-ADMIN dan VM-ATTACKER; sesi shell sengaja dibiarkan untuk pengguna.
Bukti privat `state/deployment/console-login-2026-10-12/`; password tetap hanya di
inventaris lokal. Ctrl+] melepaskan console tanpa shutdown. Tidak ada reboot atau
perubahan konfigurasi aplikasi pada langkah ini.
