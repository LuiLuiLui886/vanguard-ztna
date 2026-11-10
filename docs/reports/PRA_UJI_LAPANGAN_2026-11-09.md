# Pemeriksaan sebelum uji lapangan — 9–10 November 2026

Status: **pemeriksaan source dan backend selesai; penerimaan endpoint fisik BELUM_TERUJI**.
Source diperbarui fast-forward ke `ef14b07`; perubahan flowchart pengguna
terpelihara. Tidak ada pembaruan runtime atau reset identitas pada sesi ini.

## Keputusan versi admin dan server

| Peran | Terpasang dan diperiksa | Keputusan |
| --- | --- | --- |
| CA | 0.1.17 | Pertahankan perbaikan penyimpanan CA yang sudah terpasang |
| Server dan daemon | 0.1.15 | Pertahankan; tidak ada perbaikan perilaku peran ini pada 0.1.17 |
| Admin | 0.1.15 | Pertahankan; kode dashboard dan dependensi tidak berubah pada 0.1.17 |
| Installer Windows | Paket rilis 0.1.15 | Tidak rebuild; eksekusi Windows native tidak diulang pada sesi ini |

Perbandingan terhadap source rilis 0.1.15 `7e5d632` menunjukkan perubahan runtime
hanya di `vanguard/ca_storage.py` dan nomor versi. Fungsi baru `sync_generation`
dan perubahan `Publication.seal` dipakai operasi CA. Server mengimpor
`durable_write` dari modul itu; perbandingan AST membuktikan fungsi tersebut
tidak berubah. Kode admin,
admission, session, policy, daemon dan batas dependensi tidak berubah.

Hash seluruh 27 anggota source terpasang per VM cocok dengan versi acuannya:
CA dengan source 0.1.17, server/admin dengan 0.1.15. Mengubah nomor versi keduanya
saja tidak menambahkan perbaikan akses atau dashboard. Keputusan ini mengikuti
izin pengguna untuk mempertahankan versi yang sesuai, bukan klaim versi lama
selalu lebih aman. Tidak diperlukan rollout/rollback karena runtime tidak diubah.

## Temuan, bukti dan kriteria selesai

| Klasifikasi | File/fungsi atau lokasi | Bukti dan dampak | Prioritas | Kriteria selesai / tindakan |
| --- | --- | --- | --- | --- |
| Bug terbukti pada pemeriksaan source | `tests/test_ca_seal_barrier.py` import | Ruff I001 pada dua blok; CI lint gagal | P2 | Susun ulang import saja; ruff akhir PASS |
| Bug terbukti pada petunjuk tes lokal | `README.md` | `.venv/bin/pytest` gagal 6 import saat collection; module runner dipakai CI | P2 | Gunakan `.venv/bin/python -m pytest`; hasil suite akhir dicatat terpisah |
| Risiko operasional teramati | Boot CA/server dan resource host | Awal 13/30 HTTPS HTTP200; timeout CA/server juga terjadi saat SSH banner; host teramati menunggu I/O 21–24% | P1 sebelum mulai uji | Tunggu boot dan wajib lulus postflight; penyebab spesifik timeout belum terbukti, jangan menyebut sudah diperbaiki oleh update |
| Fitur deployment belum tersedia pada lokasi saat pemeriksaan | `scripts/pilot_preflight.py` / Ethernet host | Host memakai Wi-Fi 192.168.66.9; belum Ethernet 192.168.50.10; laporan BLOCKED | P1 lapangan | Hubungkan router pilot, tetapkan alamat sesuai rencana, buktikan forwarding/return path dan filter host; flag ip_forward saja tidak cukup |
| Risiko operasional | Kapasitas filesystem host | `df` pada 10 November: tersisa sekitar 3,2 GiB, penggunaan 99%; backup dan bukti membutuhkan ruang | P1 sebelum pilot | Sediakan kapasitas untuk backup dan log; jangan menghapus bukti lama secara otomatis |
| Risiko operasional | Sertifikat identitas Windows existing | `vm-client-windows` berakhir 14 November 2026 06:16:28 UTC / 13:16:28 WIB | P1 bila memakai identitas ini sesudah batas | Gunakan penggantian identitas resmi sebelum sesi yang melewati masa berlaku; tidak reset key atau menganggap renewal lease memperpanjang sertifikat |
| Perilaku belum diuji sesi ini | PC fisik LAN/Wi-Fi, Windows existing/domain-GPO, TCP internet aktif saat revoke | Perangkat fisik tidak dipakai pada sesi ini | P1 penerimaan pilot | Jalankan runbook lapangan; jangan menyamakan tes Linux atau backend dengan hasil endpoint fisik |

## Bukti VM yang sudah diperoleh

- CA/server/admin dinyalakan dari kondisi shut off. Empat VM lainnya tetap mati;
  seluruh tujuh definisi dipertahankan.
- Root dan sertifikat HTTPS ketiga layanan masih dalam masa berlaku. TLS layanan
  tersisa sekitar 318,6 hari pada saat snapshot; ini berbeda dari sertifikat perangkat.
- `pip check` pada ketiga runtime mengembalikan exit 0. Ini memeriksa konsistensi
  dependensi, bukan sertifikasi bebas seluruh kerentanan.
- SQLite server/admin `PRAGMA integrity_check` menghasilkan `ok` secara read-only.
- Login admin dengan credential existing dan TOTP: HTTP302, dashboard HTTP200 dalam
  0,158 detik, logout HTTP302, sesi uji ditutup. Sesi pengguna lain tidak dicabut.
- Profil admin schema 2 menunjuk HTTPS `.100.20:8081`; route split-default sesuai
  internet terkelola. Policy aplikasi/internet valid, masing-masing 0 grant, dan
  set enforcement 0 elemen. Tidak memberi izin permanen hanya demi uji.
- Forwarding IPv4 server=1; heartbeat daemon berumur 4,75 detik saat diperiksa.
- Pemeriksaan invariant CA lulus di bawah lock. Hash root, private key root,
  index dan serial tetap sama dengan baseline privat sebelum rollout 3 November.
- CRL valid saat snapshot; seluruh 35 serial revokasi dari backup sebelumnya masih
  ada. Tidak menerbitkan sertifikat, mengubah counter atau memulihkan state lama.
- Sertifikat tiga identitas enabled masih valid saat snapshot; lease waktunya
  tidak aktif, tidak ada peer hidup. Belum menguji admission endpoint baru hari ini.

## Hasil akhir tes

Sampel tambahan ketika suite Linux masih berjalan: **30/30 HTTPS HTTP200**,
CA 0.1.17, server/admin 0.1.15 active. Ini beban gabungan pengujian lokal dan VM,
bukan postflight tanpa beban maupun pengujian endpoint.

Baseline source Linux selesai 9 November: **355 PASS, 1 SKIP, 0 failure/error**,
1010,63 detik. Satu skip: `Requires real Windows ACL APIs`; bukan hasil Windows
native. Fixture CA memakai OpenSSL nyata, tes jaringan tertentu memakai adapter
mock; angka ini tidak membuktikan handshake endpoint fisik. Ruff dan pip check
lokal lulus. Perubahan kode hanya urutan import pada tes; README menggunakan
module runner sesuai CI.

Setelah boot ulang 10 November, SSH siap setelah 3 percobaan pada CA/server
serta 4 pada admin. Probe awal menghasilkan **28/30 HTTP200**: readiness server
dan admin mengembalikan HTTP503 dengan database `unknown` pada putaran pertama.
Empat putaran berikutnya seluruhnya HTTP200. Ini bukti ketidaksiapan sesaat,
bukan bukti database rusak maupun perbaikan penyebabnya.

Postflight terpisah setelah layanan stabil selesai **10 November 11:53 WIB**:
**30/30 HTTPS HTTP200**, verifikasi TLS aktif, CA 0.1.17 dan server/admin 0.1.15
seluruhnya `active`. Diagnostik read-only ketiga peran juga `ready`; pemeriksaan
database server/admin masing-masing 0,8/0,6 ms pada sampel itu. Batas waktu
readiness dan fail-closed tetap dipertahankan. Kegagalan collection, sampel boot
awal 9 November dan 28/30 pada 10 November disimpan, tidak ditimpa hasil retry.
Penyebab spesifik gangguan boot belum dibuktikan; kelulusan setelah stabil tidak
menutup risiko startup atau menggantikan uji jangka panjang.

Saat selesai, CA/server/admin running; empat domain lain shut off. Ketujuh
definisi VM tetap tersedia. Ruang host sekitar **3,2 GiB (99% terpakai)**; belum
ada penghapusan atau pemindahan backup. Ini membatasi kesiapan backup pilot.

Bukti privat: `state/preflight-20261109/` (inventory berhasil di `retry/`),
`state/preflight-20261110/` (sampel boot) dan subfolder `settled/` (postflight akhir).
Jurnal: [9 November](../progress/PROGRESS_2026-11-09.md) dan
[10 November](../progress/PROGRESS_2026-11-10.md).
Panduan penerapan: [dokumen lapangan](../PERSIAPAN_UJI_LAPANGAN.md).

## Langkah menuju pilot kampus

1. Hubungkan host Ethernet `.50.10` ke router khusus; periksa alamat endpoint,
   jalur `/32` ke server, forwarding host/libvirt, NAT dan jalur balik.
2. Jalankan readiness setelah boot; jangan mulai install/lockdown selama layanan
   unknown, timeout atau HTTP503. Sediakan waktu startup dan ruang disk/backup yang cukup.
3. Periksa domain/GPO/build Windows, profil dan fingerprint, akun serta alokasi ID/IP.
4. Siapkan grant aplikasi sesuai identitas/resource/protokol/port. Berikan grant
   internet hanya setelah skenario tanpa izin diuji; policy kosong bukan bug.
5. Jalankan satu PC terlebih dahulu, kemudian Wi-Fi dan keduanya bersamaan. Catat
   dua renewal, logout, reboot, revoke koneksi aktif dan recovery sesuai runbook.
6. Jangan membawa identitas Windows yang kedaluwarsa; tiap komputer baru membuat
   key sendiri. Bekukan versi pilot yang terverifikasi dan simpan hasil per build.
