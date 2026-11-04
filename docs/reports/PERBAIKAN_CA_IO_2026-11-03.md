# Perbaikan waktu penyimpanan CA — 3 November 2026

Status: **CA0.1.17 sudah terpasang**. Pengujian layanan setelah pemasangan
tercatat di bawah; percobaan0.1.16 yang belum mencukupi tetap didokumentasikan.

| Klasifikasi | Lokasi | Bukti dan dampak | Prioritas | Kriteria selesai |
|---|---|---|---|---|
| Risiko desain terkonfirmasi | `vanguard/ca_storage.py:Publication.seal` | Berkas generasi disalin lalu setiap fsync ditunggu berurutan. Pada fixture VM, seal5,487detik untuk generasi berikutnya; lock dapat melewati budget readiness dan fetch CRL. | P1 operasional | Durability/interupsi lulus, waktu berkurang pada VM yang sama, readiness serta fetch CRL nyata berhasil. |
| Perilaku belum teruji | Kegagalan daya perangkat penyimpanan fisik | Uji SIGKILL tidak memutus daya perangkat atau membuktikan cache hardware. | P2 | Uji khusus pada storage yang sesuai, di luar CA utama. |

## Bukti awal

Tiga VM layanan running dan unit active;9/9liveness HTTP200, hanya1/9readiness
HTTP200 pada sampel awal. CA unknown/lock_busy, server daemon CRL unavailable;
admin mewarisi dependensi yang gagal. Dashboard HTTP302 ke/login belum menjadi
bukti akses VPN siap. Sebelumnya satu thread CA teramati menunggu commit filesystem.

Probe lima penulisan sementara di VM-CA: fsync0,376/0,018/0,110/0,017/0,108detik.
QEMU mencatat25.256flush dengan waktu kumulatif sekitar1007detik sejak boot,
tanpa failedflush. Ini bukti latensi, bukan bukti disk rusak atau satu-satunya
penyebab seluruh insiden historis. Host tersisa sekitar1,3GiB dan RAM31GiB.

Fixture terisolasi menggunakan100berkas sertifikat palsu, bukan salinan private
key atau CA operasional. Bentuk berkas memenuhi manifest storage, bukan sertifikat
X.509; jadi ini benchmark publication saja. Tes OpenSSL terpisah memakai CA sementara.

| Sampel | Baseline prepare | Baseline seal total | Kandidat0.1.16 prepare | Kandidat0.1.16 seal total |
|---|---:|---:|---:|---:|
| Generasi pertama | 0,172s | 14,148s | 0,021s | 8,634s |
| Generasi berikutnya | 0,233s | 5,487s | 0,124s | 1,893s |

Generasi pertama mencakup normalisasi permission644fixture awal; recovery
6,315/7,448detik. Generasi berikutnya lebih dekat dengan berkas operasional600.
Fase sebelum recovery turun7,833/5,377s menjadi1,186/1,343s. Hanya dua sampel
perversi pada storage bersama, tidak menjadi SLA atau benchmark terkontrol penuh.

## Perubahan dan jaminan yang dipertahankan

Revisi awal0.1.16 memakai8worker fsync. Rollout nyata setelah backup lulus pemeriksaan
27file kode dan196file state, tetapi postflight29/30 dengan5/5CRL tambahan dan
25/30 tanpa fetch tambahan belum memenuhi kesiapan. Bukti gagal tetap disimpan.
Dashboard login TOTP, halaman utama200 dan logout scoped berhasil. Harness login
pertama melewatkan CSRF; dikoreksi dengan GETlogin/tokenform tanpa mengubah produk.

Revisi0.1.17 mengganti hanya barrier generasi privat pada `Publication.seal`.
Semua write ditutup, permission600 dan hash anggota dihitung, lalu
`sync_generation` menunggu Linux `syncfs` selesai sebelum barrier folder dan
penulisan manifest. Pada Linux>=5.8 dengan symbol libc tersedia, syncfs menyimpan
seluruh data/metadata filesystem dan mengembalikan error writeback. Semua anggota
harus berada pada filesystem yang sama dengan generasi. Platform/kernel lama
memakai fsync setiap anggota seperti sebelumnya. Dasar semantik ada pada
[Linux man-pages syncfs](https://man7.org/linux/man-pages/man2/sync.2.html).

Ini juga menyinkronkan write lain pada filesystem VM yang sama; beban luar CA
masih dapat memengaruhi waktu. Tidak memakai sync asynchronous atau menonaktifkan
barrier. ErrorEIO/ENOSPC, kegagalan anggota, atau filesystem berbeda menghentikan
commit. Bukti uncommitted diarsipkan saat transaksi berikutnya. Tidak mengubah
format jurnal, recovery, counter, CRL, aturan admission, atau timeout readiness.

Manifest durable tetap menjadi keputusan commit untuk seluruh generasi; satu
rename tidak dianggap cukup untuk state CA. Private key dibuat client; histori
revokasi dan binding tidak diganti. Patch tidak menggunakan cache CRL usang.

Fixture0.1.17 pada VM yang sama: prepare0,845/0,037s; seal5,747/1,139s. Fase
sebelum recovery0,677/0,345s; recovery5,070/0,793s. Sampel awal tetap mencakup
normalisasi permission fixture, bukan kondisi operasional biasa. Tidak menganggap
sampel benchmark sebagai bukti readiness deployment.

## Validasi source dan rencana deployment

Baseline CA19PASS74,93detik. Kandidat CA22PASS76,09detik mencakup regresi lama
serta tiga kasus baru: commit menunggu flush tertahan, errorflush meninggalkan
state lama dan bukti, dan SIGKILL selama flush sebelumcommit. Suite lama menguji
SIGKILL saat publication issuance/revoke/CRL dan roll-forward seluruh generasi.
Health31PASS34,94detik danPKI/admission43PASS201,26detik pada revisi0.1.16.
Revisi0.1.17: CA26PASS76,94detik, termasuk errorEIO/ENOSPC dari wrapper syncfs,
fallbackkernel5.4 dan penolakan filesystem berbeda. Health/PKI/admission
revisi akhir74PASS222,08detik. Total final100PASS pada suite yang dipilih, bukan
klaim full suite348tes atau pengujian Windows ulang.

Wheel0.1.17 ditujukan ke CA saja. Server/admin/client dan EXE/ZIP tetap0.1.15;
perubahan ini tidak memerlukan pembaruan Windows. Backup privat kode/config/state
CA dibuat setelah producer dihentikan dan transaksi selesai. Pemulihan hanya
mengembalikan kode, tidak memulihkan CA state/counter/CRL/database lama.

Bukti privat: `state/ca-io-20261103/`; riwayat sebelum patch tetap di
`state/ready-20261103/`. Jurnal: [3November](../progress/PROGRESS_2026-11-03.md).


## Hasil rollout0.1.17 dan pemakaian aktual

Sesudah producer API/daemon dihentikan sementara dan writer CA selesai, backup
kode/config/state baru dibuat dan diverifikasi. CA dipasang dari wheel yang cocok
27file source. Seluruh hash state sebelum start cocok dan invariantCA PASS.
Server/admin dihidupkan kembali pada0.1.15; tidak mengubah WireGuard/kernel,
konfigurasi identitas, timeout, atau password. Tidak menjalankan rollback.

Postflight dengan fetchCRL tambahan: **30/30HTTPS health/readiness HTTP200**,
**5/5CRL valid**; waktu3,642/3,998/3,573/1,733/0,884detik. NomorCRL meningkat,
seluruh35revokasi tetap ada. KernelCA5.15.0-202 mendukung jalur syncfs; pengecekan
root/key/index/serial/sertifikat/config pascarollout lulus terhadap backup.

Login admin menggunakan credential existing dan TOTP asli: redirect302,
halaman dashboard2000,274detik, logout sesi uji302 dan redirectlogin setelahnya.
Sesi pengguna lain tidak dicabut; password/token/OTP tidak dicetak atau dipush.
Tiga terminalSSH desktop tetap memiliki sesi login; tidak ada peer VPN yang
sedangaktif. Pengujian ini tidak otomatis menghubungkan endpoint user.

Pengamatan beban normal berikutnya juga **30/30HTTPS HTTP200**, dengan daemon
aktif dan tanpa fetchCRL tambahan dari harness. Bukti `v2/normal-postflight.json`. Hasil sampel
bukan jaminan latency semua beban. Disk host sekitar1,2GiB bebas; kapasitas perlu
ditambah sebelum soak/pengujian panjang. Gangguan daya fisik, kerusakan storage,
dan beban banyak endpoint tetap BELUM_TERUJI. Backup dan bukti gagal dipertahankan.


## Pemeriksaan setelah host reboot

Pada22:25host uptime3menit dan seluruh VM mati. CA/server/admin dinyalakan kembali,
tanpa mengulang install. Pemeriksaan baru **30/30HTTPS health/readiness HTTP200**,
CA0.1.17 danserver/admin0.1.15 active. TerminalSSH desktop ketiganya showing dan
shellprompt sudahlogin; consoleSerial1 dibuka. EmpatVM lain tetapoff.
Bukti `reboot-2226/normal-postflight.json` terpisah dari pengujian sore hari.
Ini bukti startup berikutnya, bukan simulasi kehilangan daya pada transaksiCA.
