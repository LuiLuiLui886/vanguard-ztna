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

## Perintah Windows pada manual

Alur pengguna memakai Set-Location ke folder aplikasi, lalu perintah singkat
`.\VanGuard.bat ACTION`, satu aksi per blok. Configure/import/login/connect
terpisah dengan jawaban prompt, hasil dan jeda BAT.14pemanggilan dicocokkan
terhadap action launcher; HTML/tautan valid. Ini revisi dokumentasi, tanpa tes
Windows native atau rebuild paket lama.

## Petunjuk terminal dan file

Manual diperinci pada Bagian0.2.1–0.2.3 dan1.1.1–1.1.2: posisi terminal,
peta folder, membuka file manager, menemukan hasil ekspor lama dan transfer
bahan publik. Bagian2–4 menunjukkan lokasi file Windows/request/bundle dan
jawaban prompt. Snippet membaca trust existing berhasil; HTML dan tautan valid.
Tidak ada perubahan aplikasi atau pengujian Windows native pada edit manual ini.

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
| VM | Lima Ubuntu tetap terdaftar; seluruh5Ubuntu shut off pada pemeriksaan terbaru; dua Windows dihapus |
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

## Klarifikasi installer Windows — 11 November

Preferensi pengguna mempertahankan versi teruji berlaku khusus installer Windows.
EXE0.1.15, ZIP template dan launcher BAT/PowerShell identik SHA-256 dengan rilis
7e5d632; revisi kemudahan terbaru hanya panduan. Tidak dilakukan rollback atau
perubahan runtime. Bukti native historis tetap terbatas pada lingkungan uji;
endpoint fisik/fresh OS/UAC/GPO BELUM_TERUJI. Gunakan installer0.1.15 yang tersedia.

## Panduan Windows diselaraskan — 11 November

Manual MD/HTML Bagian2.1 kini memakai nama EXE0.1.15 dan folder Downloads nyata,
checksum serta petunjuk tidak mengulang instalasi/init untuk revisi dokumentasi.
Halaman unduhan dan dokumen lapangan selaras; manual dalam paket belum dibangun
ulang.14action cocok launcher, hash EXE/ZIP cocok rilis dan0tautan rusak.
Tidak ada perubahan runtime atau uji Windows native baru; lanjut pilot fisik
sesudah backend/jaringan siap.

## Rencana B konferensi — 11 November

Pengguna ingin paper Inggris maksimal6halaman termasuk referensi, pengujian VM
dan screenshot. [Rencana lengkap](proposal/RENCANA_B_KONFERENSI.md) tersedia; belum draft siap submit.
Pengguna mengonfirmasi deadline diperpanjang30November2026 dan kategori
cyber/network diEDAS; situs publik masih menampilkan tanggal lama. Fokus
layanan media digital telah dipilih, eksperimennya belum dijalankan. Screenshot/log perlu diinventaris; tidak
ada bukti baru yang dibuat, tidak otomatis membuat ulang WindowsVM. Pengujian
fisik tetap pekerjaan terpisah; runtime dan instalasi tidak berubah.

## Draft paper Inggris — 11 November

[Draft awal](proposal/DRAFT_PAPER_ICIMPACT.md) dan DOCX tersedia. Hasil media, screenshot, penulis
dan pagination6halaman belum lengkap. Hasil historis0.1.15 diberi label terpisah;
empat sumber primer diverifikasi. GoogleDrive kini terhubung; draft sudah
masuk tab Draft VanGuard pada GoogleDoc target, template t.0 tetap identik.
ExportPDF menunjukkan4halaman draft termasuk referensi;3halaman lain adalah
template asli. Lengkapi bukti nyata/gambar dan periksa ulang pagination sebelum
review pembimbing.
Tidak ada perubahan runtime/VM atau submission konferensi.
