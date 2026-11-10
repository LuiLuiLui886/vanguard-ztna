# Checkpoint VanGuard — 11 November 2026

## Cara menggunakan checkpoint

File ini hanya berisi status terbaru dan pekerjaan tersisa. Catatan sebelum
cleanup tersimpan lengkap di [arsip checkpoint](history/checkpoints/CHECKPOINT_2026-11-10_before_cleanup.md).
Bukti terbaru ada di [jurnal 11 November](progress/PROGRESS_2026-11-11.md).

## Perubahan terbaru 11 November

Atas permintaan pengguna, VM Windows11/10 beserta dua disk OS dihapus setelah
backup privat135file identitas/config terverifikasi dan shutdown normal. XML,
NVRAM/TPM serta seluruh hasil uji host dipertahankan; tidak ada backup OS lengkap.
Lima XML VM Ubuntu sama persis. Ruang bebas kini sekitar77GiB. Jangan membuat
ulang VM Windows otomatis; endpoint fisik harus menjalani pengujian tersendiri.

Ekspor profil kini satu perintah pada host, tanpa prompt username:
`/home/lui/vanguard/.venv/bin/python /home/lui/vanguard/scripts/export_endpoint_public.py`.
Ekspor aktual schema2 lulus; hasil tersedia di `state/endpoint-public-u8wsu2hh/`.
Helper dan preflight lulus14tes Linux terarah. Preflight kini mewajibkan5Ubuntu,
namun tetap BLOCKED karena Ethernet.50.10 tidak aktif saat pemeriksaan terakhir.

## Source dan panduan aktif

- Branch: `feature/2026-10-22-physical-endpoints`; main tidak otomatis sama.
- Manual terbaru: [MD](MODUL_PENGGUNAAN_VANGUARD.md) dan
  [HTML](MODUL_PENGGUNAAN_VANGUARD.html), satu manual dalam dua format.
  Edisi 11 November memakai helper ekspor otomatis pada Bagian1.1.
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
| VM | Lima Ubuntu tetap terdaftar; CA/server/admin running, client/attacker off; dua Windows dihapus |
| Host | Saat cek11November memakai Wi-Fi192.168.66.9; Ethernet.50.10 belum aktif |
| Kapasitas | Ruang disk sekitar77GiB bebas setelah penghapusan dua disk Windows |

Runtime CA/backend dan firewall tidak diubah; pensiun Windows sesuai izin pengguna. Periksa
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

1. Sambungkan Ethernet host pada pilot .50/24; periksa alamat .50.10 dan
   reservation/exclusion DHCP router. Koneksi sekarang masih Wi-Fi .66.9.
2. Periksa forwarding/filter libvirt, rute /32 endpoint dan jalur balik.
   Alamat host dan ip_forward=1 tidak membuktikan traffic Windows→server lolos.
3. Periksa readiness sebelum lockdown. Telusuri timeout jika terulang.
4. Sediakan kapasitas backup/log tanpa menghapus bukti atau state CA.
5. Identitas VM Windows lama disimpan sebagai histori dan backup privat;
   komputer fisik memakai ID/key baru. Jangan menyalin key lama ke endpoint baru.
6. Ikuti dokumen lapangan untuk satu endpoint dahulu, kemudian LAN/Wi-Fi bersama;
   catat hasil nyata dan skenario yang masih BELUM_TERUJI.

## Cleanup 10 November

Perubahan dipush pada `ec45628`; SHA remote terverifikasi pada branch feature.

Empat folder ekstraksi dist yang identik dengan ZIP dipertahankan arsipnya,
lalu salinan ekstraksinya dihapus bersama cache dan build sementara: 373 file,
51.780.579 byte logis. Snapshot checkpoint/handoff lama masuk history; kedua
file aktif diringkas. Source, tes, manual, installer, histori, credential lokal,
state dan VM dipertahankan. Manifest privat: `state/cleanup-20261110/`.
