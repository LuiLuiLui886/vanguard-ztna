# Checkpoint VanGuard — 10 November 2026

## Cara menggunakan checkpoint

File ini hanya berisi status terbaru dan pekerjaan tersisa. Catatan sebelum
cleanup tersimpan lengkap di [arsip checkpoint](history/checkpoints/CHECKPOINT_2026-11-10_before_cleanup.md).
Bukti per langkah ada di [jurnal 10 November](progress/PROGRESS_2026-11-10.md).

## Source dan panduan aktif

- Branch: `feature/2026-10-22-physical-endpoints`; main tidak otomatis sama.
- Manual terbaru: [MD](MODUL_PENGGUNAAN_VANGUARD.md) dan
  [HTML](MODUL_PENGGUNAAN_VANGUARD.html), satu manual dalam dua format.
  Edisi 10 November sudah dipush pada `8a87469` sebelum cleanup.
- Mulai manual dari Bagian 0: host adalah laptop Linux fisik. Jalankan
  `cd /home/lui/vanguard` sebelum memakai `.venv` atau `scripts/`.
  Prompt `ubuntu@vm-*` berarti sudah masuk VM; inventory hanya ada di host.
- Gunakan profil existing schema2 dari VM-ADMIN (manual Bagian 1.1).
  Generator profil schema1 adalah opsi aplikasi internal, bukan langkah wajib.
- [Dokumen lapangan](PERSIAPAN_UJI_LAPANGAN.md) dan
  [flowchart lengkap](FLOWCHART_SISTEM_LENGKAP.md) tetap aktif.

## Versi dan kondisi operasional terakhir

| Komponen | Kondisi terakhir yang diverifikasi |
| --- | --- |
| CA | 0.1.17; invariant CA dan 35 revokasi lama terjaga pada audit 9 November |
| Server/admin | 0.1.15 dipertahankan; delta 0.1.17 hanya relevan ke penyimpanan CA |
| Installer Windows | 0.1.15 di downloads; EXE/ZIP belum dibangun ulang untuk edisi manual terbaru |
| VM | Ketujuh domain running saat pemeriksaan 10 November; lima Ubuntu lolos SSH |
| Tampilan | Lima terminal SSH dan dua viewer Windows diluncurkan; tampilan fisik layar belum diverifikasi |
| Host | Ethernet enp3s0 statis 192.168.50.10/24, gateway/DNS .50.1; ping router berhasil |
| Kapasitas | RAM 31 GiB; ruang disk sekitar 480 MiB (100% terpakai) pada pemeriksaan setelah cleanup |

Tidak mengubah runtime, CA, firewall atau konfigurasi VM pada cleanup. Periksa
ulang status aktual sebelum pengujian; tabel ini adalah catatan pengamatan.

## Bukti dan batas pengujian

- Baseline Linux 9 November: **355 PASS, 1 SKIP**, 0 failure/error, 1010,63 detik.
  Skip membutuhkan Windows ACL asli. Bukan hasil endpoint fisik.
- Postflight 10 November: 30/30 HTTPS HTTP200 setelah stabil. Sampel boot gagal
  13/30 dan 28/30 tetap tersimpan. Readiness paralel sempat timeout lagi saat
  pemeriksaan kesalahan SSH; retry berurutan ketiganya ready. Penyebab timeout
  belum terbukti; tidak menyimpulkan sudah diperbaiki.
- Manual terbaru diuji dengan ekspor bahan publik lewat SSH ke VM dan validasi
  profil schema2; generator schema1 diuji pada direktori sementara.
- Push sebelumnya gagal saat DNS router tidak menjawab; kueri DNS publik
  berhasil dan push ulang sukses. Konfigurasi DNS belum diubah.
- PC Windows fisik LAN/Wi-Fi, instalasi OS kosong/UAC/GPO dan pemutusan TCP
  internet aktif belum diterima. Jangan menyamakan kelulusan VM dengan uji fisik.

## Pekerjaan berikut

1. Pastikan .50.10 dicadangkan/dikecualikan dari DHCP router. Host sudah memakai
   alamat itu, tetapi konfigurasi pool router belum diverifikasi.
2. Periksa forwarding/filter libvirt, rute /32 endpoint dan jalur balik.
   Alamat host dan ip_forward=1 tidak membuktikan traffic Windows→server lolos.
3. Periksa readiness sebelum lockdown. Telusuri timeout jika terulang.
4. Sediakan kapasitas backup/log tanpa menghapus bukti atau state CA.
5. Identitas vm-client-windows berakhir **14 November 2026 13:16:28 WIB**.
   Gunakan alur penggantian resmi jika diperlukan; renewal lease tidak memperpanjangnya.
6. Ikuti dokumen lapangan untuk satu endpoint dahulu, kemudian LAN/Wi-Fi bersama;
   catat hasil nyata dan skenario yang masih BELUM_TERUJI.

## Cleanup 10 November

Empat folder ekstraksi dist yang identik dengan ZIP dipertahankan arsipnya,
lalu salinan ekstraksinya dihapus bersama cache dan build sementara: 373 file,
51.780.579 byte logis. Snapshot checkpoint/handoff lama masuk history; kedua
file aktif diringkas. Source, tes, manual, installer, histori, credential lokal,
state dan VM dipertahankan. Manifest privat: `state/cleanup-20261110/`.
