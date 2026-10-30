# Uji kelayakan VanGuard — 30 Oktober 2026

**Keputusan: dapat dilanjutkan untuk uji lab terkontrol; belum memenuhi penerimaan
penuh untuk operasi nyata tanpa pendampingan.** Tes yang selesai tidak menemukan
kegagalan regresi source, tetapi endpoint utama Ubuntu sudah kedaluwarsa, backend
utama belum memakai fitur internet kandidat, dan beberapa jalur distribusi serta
pemulihan belum memiliki bukti. Jangan menafsirkan laporan ini sebagai sertifikasi
keamanan, jaminan bebas bug, atau pernyataan semua skenario telah lulus.

Baseline source `7fa2e7c`, aplikasi0.1.14, installer0.1.14-fix1, branch
`feature/2026-10-22-physical-endpoints`. Tes dimulai sekitar00:05WIB, berlanjut
setelah host reboot pada siang hari. Hasil sebelum reboot tetap bukti pada waktu
pengujian, bukan status layanan sekarang. Semua7VM dipertahankan. Main, kernel
WireGuard, CA utama, binding dan histori pencabutan utama tidak diganti.

**Pembaruan13:33WIB:** setelah laporan awal, pengguna mengotorisasi rollout paket
CA/server/admin. Ketiganya kini0.1.14 dengan backup dan verifikasi source. Tabel
versi0.1.11 di bawah adalah hasil pengujian awal, bukan versi terpasang terbaru.
Postflight31Oktober:30/30HTTPS200, CA/DB/integritas histori PASS; sampel
readiness gagal30Oktober tetap dicatat pada jurnal.
Q02 masih memerlukan konfigurasi profil/gateway dan uji endpoint karena update
paket saja tidak mengaktifkan internet terkelola. Lihat [checkpoint](CHECKPOINT.md)
dan [jurnal rollout](PROGRESS_2026-10-30.md) untuk postflight serta kegagalan verifier.

## 1. Hasil aktual dan jenis buktinya

| Bagian | Hasil aktual | Lingkungan dan batas |
|---|---|---|
| Seluruh suite Python | **307 PASS,1 SKIP**,919,32detik;308terkumpul | Linux lokal;1tes ACL khusus Windows dilewati. Backend WireGuard sejumlah tes memakai fake; tidak seluruhnya integrasi VM |
| CA durability/publication |14+5tes dalam suite di atas PASS | OpenSSL/CA sementara, interupsi proses dan kegagalan I/O; bukan power-loss media/host |
| Admission/PKI/karyawan/logout |22/21/13/5tes dalam suite PASS | Signature, validity, CRL, proof, binding, session, logout race/scope; bukan jumlah tambahan terhadap307 |
| Admin/audit/arsip/operasional |30tes admin dan3verifikasi arsip dalam suite PASS | Flask/SQLite terisolasi, TOTP/CSRF, history, archive integrity; tidak login browser admin live ulang |
| Status/readiness |7status,8contention,1capacity dalam suite PASS | Batas timeout, unknown, lock, TLS capacity; termasuk mock dan proses terisolasi |
| Endpoint/profile/provision/package |37profile,12provision,6package dalam suite PASS | Validasi profil/import, alur wizard, kontrak paket; tidak menggantikan UI native |
| Internet/resource |26internet+3resource dalam suite PASS | Kebijakan/sesi/lease, guard sebelum renewal, cleanup gagal; perintah nft beberapa tes memakai mock |
| Source/dependensi/build |Ruff, pip check, Bash syntax, diff check PASS; wheel27anggota cocok source | Source aplikasi tidak diubah dalam pekerjaan ini |
| Artefak publik |2ZIP+EXE SHA256 PASS; ZIP CRC dan hash seluruh manifest PASS |39anggota template kandidat,36anggota stable; bukan bukti penerbit karena EXE unsigned |
| Layanan utama5Ubuntu |CA/server/admin active; CA invariant+CRL ready; DB server/admin quick_check OK |CA/server/admin0.1.11, client/attacker0.1.9; nol live peer |
| HTTPS utama |**30/30 HTTP200**, maksimum3,167detik |15liveness+15readiness melalui jalur admin,5putaran; bukan soak/load benchmark |
| Firewall/negative API utama |**40/40**TCP allow/deny; **7/7**API tanpa izin+LAN/app deny |VM aktual; tidak mengubah firewall/router utama |
| Resource TCP terisolasi |**7perilaku PASS** |nftables nyata pada namespace VM-ATTACKER, ingress veth bernama wg0; tidak ada handshake di tes ini |
| Integrasi HTTPS/WG/nft kandidat |**16perilaku PASS**,runner terakhir exit0 |CA/akun baru, kernel WireGuard nyata, namespace server/client/WAN terpisah pada ATTACKER; rincian bagian2 |
| Windows11 build26300 |28helper PASS/2SKIP POSIX,1,45detik;9gate sintetis;6resume sentinel;10configure;13extractor;6EXE PASS |Python3.13.16 existing; helper tunnel memakai stub, extractor ACL/filesystem native |
| Windows11 instalasi EXE umum |**Exit0**,runtime0.1.14/pip check/clienthelp dan postflight PASS |Installer asli dijalankan di elevated SSH, prasyarat sudah tersedia; bukan klik UAC/fresh OS |
| Windows10 LTSC build19044 |28helper PASS/2SKIP POSIX,1,36detik;9gate sintetis;6resume sentinel;10configure;13extractor;6EXE PASS |Python3.13.17 existing; pengulangan ini tidak reinstall endpoint utama |
| Windows postflight |Hash identitas/config dan profil firewall sama; no tunnel/no managed policy; fixture ACL pulih |Kedua VM; bukti program terpasang Windows10 ditambah pip check, bukan pemasangan baru |
| Manual |Panduan EXE9langkah, TOC/anchor HTML dan5SVG embedded tervalidasi |Manual tunggal MD/HTML; isi EXE/ZIP lama tidak dibangun ulang |

Angka antarbaris saling mencakup; **jangan dijumlahkan menjadi total tes unik**.
Gate9kasus memakai fakta build sintetis, sehingga bukan9edisi OS yang benar-benar
terpasang. Tidak ada hasil CI GitHub baru yang diklaim.

## 2. Integrasi jaringan kandidat yang benar-benar dijalankan

Harness memakai source kandidat, HTTPS dengan verifikasi root/SAN, WireGuard
kernel dan nftables nyata di namespace terpisah dalam VM-ATTACKER. Key perangkat
dibuat oleh proses client. CA, akun dan database seluruhnya disposable. Tujuan
WAN `9.9.9.9` dibuat **di namespace lokal**, tidak menghubungi layanan internet
pada alamat tersebut. Hasilnya bukan pengujian ISP/router/Wi-Fi atau DNS publik.

Run terakhir membuktikan:

1. Registrasi dan login HTTPS belum memasang peer.
2. Admission perangkat sah memasang peer; handshake WireGuard terjadi.
3. Aplikasi internal dan internet simulasi default-deny; grant eksplisit mengizinkan TCP.
4. Akses langsung LAN dan port lain ditolak.
5. Pencabutan grant internet menghentikan TCP aktif, sementara grant aplikasi tetap berlaku.
6. Dua renewal **manual** diterima; bukan dua siklus worker60detik.
7. Logout sesi lama mempertahankan peer sesi baru; logout sesi aktif idempotent menghapus peer.
8. Lease uji12detik habis secara alami dan reconcile menutup akses.
9. CA tidak tersedia menghapus peer dan menolak admission; startup reconcile memerlukan admission baru.
10. Sesudah fresh peer client, pencabutan sertifikat menghentikan TCP aktif dan menolak admission berikutnya.
11. Akun disposable dinonaktifkan dan invariant CA tetap benar.

Ada16record PASS karena beberapa butir di atas berisi lebih dari satu record.
Lease12detik sengaja memperpendek tes; **konfigurasi produksi300detik tidak berubah**.
Reconcile dipanggil harness, bukan unit daemon produksi. Penghentian daemon,
watchdog dan reboot aktif produksi tidak diulang oleh harness ini.

Run pertama lulus14record lalu gagal membentuk stream sebelum pencabutan setelah
server peer dihapus/ditambah dan state peer client lama dipakai. Pencabutan belum
terjadi pada kegagalan tersebut. Run kedua terinterupsi koneksi observer dan
mencatat BrokenPipeError. Run terakhir memakai observer systemd dengan batas waktu,
log durable, serta memulai ulang peer client setelah startup reconcile;16record
PASS dan exit0. **Ini membuktikan jalur koneksi baru, bukan pemulihan otomatis
semua state tunnel lama.** Kedua bukti gagal dipertahankan.

## 3. Temuan dan kriteria selesai

P1 menghalangi penggunaan target atau penerimaan penuh; P2 perlu diselesaikan
sebelum memperluas pilot. Kategori dibedakan agar kondisi operasional tidak salah
dilaporkan sebagai bug algoritma.

| ID / kategori | File/fungsi atau lokasi dan bukti | Dampak/prioritas | Kriteria selesai |
|---|---|---|---|
| Q01 — Risiko desain/operasional |VM-CLIENT `/var/lib/vanguard/client/device.crt` expired2026-10-24T06:09:33Z; sesi expired; service auto-restart11kali saat sampel; wg0 absent. `client.admit`/validator tetap menolak |**P1** client utama tidak siap digunakan. Fail-closed benar; login saja tidak memperpanjang sertifikat |Admin menjalankan penggantian immutable identity sesuai manual, mempertahankan sejarah/key lama, kemudian login/admission/handshake ulang. Tidak reinit CA atau overwrite identitas demi tes hijau |
| Q02 — Fitur belum tersedia di deployment utama |VM CA/server/admin masih0.1.11; internet kandidat ada pada `vanguard.internet`, `deploy/firewall.py` dan dashboard baru |**P1** EXE0.1.14 tidak membuat backend utama otomatis mendukung profil/bundle/gateway kandidat |Rollout terencana dengan backup, versi/config cocok, readiness, enrollment profil, grant dan revoke dari endpoint nyata lulus |
| Q03 — Risiko desain/operasional |Host disk99%, sekitar2,8–3,8GiB kosong selama sesi; disk sparse VM bertambah saat boot |**P1** risiko kehabisan ruang saat build/backup/VM/CA publication |Siapkan kapasitas kerja dan cadangan sesuai ukuran snapshot/VM, pantau pertumbuhan; jangan menghapus backup/bukti otomatis |
| Q04 — Fitur belum tersedia |`deploy/endpoint/exe/Build-Exe.ps1`; EXE publik `Get-AuthenticodeSignature` = NotSigned |**P2** distribusi masih membutuhkan asal/hash tepercaya dan evaluasi kebijakan organisasi |Code signing dengan identitas penerbit sah, verifikasi signature dan uji distribusi browser; tidak mematikan SmartScreen |
| Q05 — Perilaku belum diuji |EXE per-device schema2, klik UAC/SmartScreen/MOTW, login wizard interaktif penuh, fresh OS tanpa runtime dan kode3010 nyata |**P1** belum boleh menyatakan instalasi satu klik pasti sukses pada semua PC |Matriks native dengan backup, input operator, batas policy dan exit/reboot tercatat. Bukti BAT atau EXE umum tidak menggantikannya |
| Q06 — Perilaku belum diuji/risiko pemulihan |`client.connect`, WindowsTunnel cleanup; histori WIN-CLEANUP-02; run1 namespace memakai state peer lama |**P2** belum ada jaminan pemulihan otomatis semua interupsi/tunnel lama |Reproduksi terkontrol, ownership dan stop terkonfirmasi, config dipertahankan saat gagal; fresh connection dan recovery otomatis diuji terpisah |
| Q07 — Perilaku belum diuji |`ca_storage.Publication`, durability lintasfile/host/media |**P1** untuk klaim tahan power-loss fisik |Uji disk/host mati mendadak pada CA disposable dan verifikasi index/counter/CRL/issued; tidak rollback/menebak counter |
| Q08 — Perilaku belum diuji |PC fisik LAN/Wi-Fi, perpindahan jaringan, OS/edisi lain, firewall domain/organisasi, beban panjang |**P1** untuk penerapan luas |Uji tiap target nyata, jalur bypass/IPv6 dan pemulihan; benchmark proposal3konfigurasi×10 serta soak terpisah. Tes parser benchmark bukan pengukuran throughput |

**Bug aplikasi baru yang berhasil dibuktikan:** belum ada dari suite yang selesai.
Ini tidak menutup kemungkinan bug pada jalur Q05–Q08. Kondisi Q01 dan Q02 nyata,
sehingga tidak memberikan keputusan “siap produksi” meskipun regresi lulus.

## 4. Kegagalan alat uji dan batas riwayat

Runner Windows awal menangkap stderr pengujian sertifikat rusak sebagai exception
parent. Pada pengulangan dengan stdout/stderr terpisah, exit0 dan10kasus konfigurasi
lulus; traceback `Invalid certificate` adalah keluaran kasus negatif yang benar.
Windows11 compiler C# juga sempat gagal akibat path relatif; path absolut memberi
13PASS. Tidak mengubah source aplikasi untuk menghilangkan pesan kasus negatif.
Runner cleanup pertama Windows11 menolak ACL fixture yang sengaja dibuat writable;
rule Users fixture kemudian dilepas dan Assert-SafePath lulus. Bukti awal retained.

Observer status PowerShell awal membesar karena metadata provider diserialisasi;
pengambilan ulang memakai `IO.File.ReadAllText`. Semua output mentah tetap lokal.
Interupsi host mematikan VM; itu **bukan** tes durability yang terkontrol.

Matriks VM lifecycle20Oktober dan managed Windows27–29Oktober tetap menjadi
**bukti historis**; tidak dihitung ulang sebagai uji sekarang. Native internet
lockdown/reboot/TCP revoke Windows bukan bagian EXE umum yang diuji30Oktober.

## 5. Penggunaan, bukti dan tindak lanjut

Panduan langkah EXE tersedia dalam [manual tunggal Bab14.0.1.1](MODUL_PENGGUNAAN_VANGUARD.md#14011-langkah-dari-nol-memakai-exe-yang-tersedia-di-github),
termasuk configure, init, tugas admin, import, login/connect dan logout. Mode
schema2 membutuhkan `internet-enable` sukses dan gateway/grant yang siap;
EXE umum sendiri tidak mengaktifkan lockdown.

Bukti privat: `state/qualification-20261030/` (`linux.xml`, laporan health/firewall,
artefak, laporan native kedua Windows dan run namespace). Fixture/backup guest
Windows: `C:\Program Files\VGQual30`; backup sebelum install Windows11 ada di
`before-install`. Tidak ada credential, token atau private key yang dipublikasikan.
Inventaris akun uji hanya `/home/lui/VanGuard-Privat/`.

Berikutnya: selesaikan kapasitas host dan penggantian identitas kedaluwarsa;
rencanakan rollout kandidat; lalu tutup matriks EXE schema2/UAC/fresh OS dan pilot
fisik. Lihat [checkpoint](CHECKPOINT.md) untuk status cleanup/publikasi akhir.
