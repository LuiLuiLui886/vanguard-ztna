# Checkpoint VanGuard — 18 November 2026

## Status terbaru — uji baru di CLI native

Pengguna memilih uji baru. Run `cli-20261118-r01`, serial102A, selesai pada
18November01:01WIB (17November18:01UTC). [Figure2 native](proposal/figures/cli-20261118/figure-2-native-cli-20261118.png)
adalah capture langsung jendela GNOME Terminal, bukan log yang dirender browser.
[Laporan CLI](testing/results/cli-20261118/README.md) menyimpan sumber workload,
log, hash, metode capture dan batas bukti. Hasil17November tidak ditimpa.

Kontrol2.880.044byte hash-cocok. Penerima HTTP200 dan counter meningkat; setelah
pencabutan lewat HTTPS admin terautentikasi, timeout pada98.304byte, reconnect
serta readmission ditolak. Peer hilang. Satu run baru, bukan rata-rata latensi.
CA/server/admin/client tetap versi0.1.17/0.1.15/0.1.15/0.1.15 (hash diverifikasi).
Startup admin503/databaseunknown disimpan; readiness kemudian200 sebelumtransfer.
Tidak ada CRL peer withdrawal pada audit identitas baru; bukan bukti perbaikan
kegagalan sebelumnya. Postflight semua backend200/ready melalui jalur sah.

Cleanup lulus: akun uji nonaktif, logout terkonfirmasi, peer/tunnel/listenerhilang,
policy pulih byte-identik, identitas utama/root/keyCA/indexlama tetap. Serial1029
lama dan102A baru tetap diCRL. Empat Ubuntu hidup, attacker mati; Windows tidak
dibuat ulang. Client utama tetapstop karena sesi kedaluwarsa sebelum eksperimen.

Dua MD/DOCX lokal memuat gambar CLI; XML/ZIP/embeddedPNG valid. GoogleDocs dan
pagination akhir enam halaman belum selesai. Berikutnya sinkronisasi kedua tab,
periksa layout, lanjut investigasi startup/CRL dan matriks pengujian tersisa.
Bukti privat: `/home/lui/VanGuard-Privat/conference-evidence/cli-20261118-r01/`.

## Riwayat — Figure 2 dari uji media 17 November

Satu run representatif `media-20261117-r01` selesai. [Figure 2](proposal/figures/figure-2-media-revocation-20261117.png)
dan [laporan bukti](testing/results/media-20261117/README.md) tersedia. Kontrol
unduh 2.880.044 byte hash-cocok; transfer aktif berhenti pada 122.880 byte setelah
pencabutan melalui dashboard. Koneksi ulang dan admission ulang ditolak; peer
hilang. Ini bukan sampel latensi rata-rata, uji Windows, atau matriks lengkap.

CA/server/admin/client berjalan; attacker mati. Windows tidak dibuat ulang.
Versi terpasang CA 0.1.17, lainnya 0.1.15. Cleanup terverifikasi: akun uji nonaktif,
logout terkonfirmasi, policy kembali byte-identik, tunnel/listener uji berhenti,
identitas utama dan histori CA tetap. Client utama sengaja tetap berhenti karena
sesi karyawan sudah kedaluwarsa sebelum eksperimen; perlu login sah untuk dipakai.
Host saat uji Wi-Fi 10.211.64.20/22, RAM 7,5 GiB; bukan konfigurasi lapangan .50.10.

Kegagalan CRL/upstream sempat menghapus peer secara fail-closed; penyebab belum
terisolasi. Readiness akhir dari jalur yang diizinkan: CA/server/admin 200/ready.
Timeout akses CA dari host sesuai filter sumber TCP8080, bukan bukti CA mati.
Percobaan gagal dan keterbatasan buffer/timer dicatat; jangan hanya menyalin run
berhasil. Tidak ada perubahan source layanan maupun rollback state CA.

Draft MD/DOCX Inggris dan Indonesia lokal memuat Figure 2; gambar DOCX embedded
serta XML/ZIP valid, pagination setelah gambar BELUM_TERUJI. Google Docs belum
sinkron karena konektor/session tidak tersedia. Berikutnya: sinkronisasi kedua
tab, periksa batas enam halaman, isolasi kegagalan CRL, lengkapi matriks dan run
independen. Bukti privat di `/home/lui/VanGuard-Privat/conference-evidence/media-20261117-r01/`.
Catatan di bawah adalah riwayat keputusan/status sebelumnya.

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
delapan sumber primer diverifikasi (empat diambil dari proposal dengan metadata
penerbit yang dikoreksi). GoogleDrive kini terhubung; draft sudah
masuk tab Draft VanGuard pada GoogleDoc target, template t.0 tetap identik.
ExportPDF menunjukkan4halaman draft termasuk referensi;3halaman lain adalah
template asli. Lengkapi bukti nyata/gambar dan periksa ulang pagination sebelum
review pembimbing.
Tidak ada perubahan runtime/VM atau submission konferensi.

## Referensi paper diperluas — tahap awal 13 November

Draft MD/DOCX dan tab Draft VanGuard kini memuat12artikel jurnal2022–2025,
dalam batas2022–2026. Empat artikel proposal dipertahankan, delapan tambahan;
empat sumber lama/nonjurnal dipindahkan ke catatan teknis RencanaB. Dasar
kelayakan kuartil adalah JIF/JCR2024 Q1–Q3 dengan kategori dan URL bukti;
SJR-saja BELUM_DIVERIFIKASI, preferensi pengguna belum dijawab. Jangan menyebut
JCR sebagai SJR atau mengklaim daftar ini jurnal SINTA2.

Skill academic-research-suite3.24.2 terpasang di luar repo, commit sumber
82725acb393c4410ac6f47634a7f51b40a162fa4; mode citation-check dipakai inline.
Metadata12artikel cocok sumber primer;12DOI tidak cocok dengan catatan pada
dataset RetractionWatch73.786baris13November. Ketiadaan kecocokan bukan
jaminan mutlak status artikel. Audit sitasi:13kemunculan,12sumber unik,
0orphan,urutan[1]–[12]. Penulis final/self-citation belum dapat dinilai.

Readback GoogleDocs:12referensi/8paragraf tambahan cocok, template t.0 dan
2tabel/28sel tetap. PDF8halaman total=3template+5draft termasuk referensi;
bukan jumlah halaman final setelah gambar/hasil. Dua placeholder gambar dan
hasil media tetap PENDING, metode/angka hasil historis tidak berubah. Belum
siap submit. Lanjutkan konfirmasi basis kuartil, penulis, dan eksperimen media.
Lihat RencanaB Bagian11–12 untuk audit/sumber dan jurnal13November untuk bukti.

Revisi referensi sudah dipush pada7549689 ke feature/2026-10-22-physical-endpoints;
SHA remote cocok dengan commit lokal pada verifikasi13November. Main tidak berubah.

## Terbaru — perluasan menjadi 20 referensi, 13 November

MD/DOCX dan tabDraft VanGuard kini20artikel jurnal2022–2026,21sitasi dan
0orphan, urutan pertama[1]–[20].8tambahan diverifikasi sumberprimer/Crossref;
kuartilJCR2024 Q1–Q3 terverifikasi, kelayakanSJR-saja masihBELUM_DIVERIFIKASI.
Lihat [RencanaB Bagian13](proposal/RENCANA_B_KONFERENSI.md) untuk metadata,
bukti kategori/ISSN, pemetaan fungsi/tes/laporan dan batas tiap klaim. Tidak
menyamakan kajianliteratur dengan pengujianVanGuard atau bukti novelty.

Readback110paragraf/sel cocokMD kecuali spasi labelAbstract yang sudah ada;
template t.0 dan2tabel/28sel terpelihara. EksporPDF:8halaman total=3template+
5draft termasuk20referensi; halaman desain/referensi diperiksa secara visual.
DOCXZIP/XML valid; paginationDOCX belum dirender. Pencocokan20DOI dan20judul
padaRetractionWatch73.786record tidak menemukan kecocokan; bukan jaminan.
Audit lokal:state/conference-draft-20261111/twenty-citation-audit.json.

Hasil media,2gambar,sampelindependen,penulis dan layoutfinal masihPENDING.
Tidak ada uji baru/perubahanruntime/VM/CA. Bukti lama dipertahankan. Berikutnya
selesaikan eksperimenmedia yang terencana, bukan menyalin angka artikel lain.
Publikasi dokumentasi dikonfirmasi14November:commit a84e783 pada branchfeature,
SHAremote cocok denganlokal. Catatan penutup ada pada jurnal14November;
main tidak diubah.

## Draft bahasa Indonesia — 17 November 2026

Versi Indonesia lengkap tersedia di GoogleDocs target yang sama, tab
**Draft Indonesia** (`t.2hkf7oqqsqly`), serta
[MD](proposal/DRAFT_PAPER_ICIMPACT_ID.md)/[DOCX](proposal/DRAFT_PAPER_ICIMPACT_ID.docx).
Template dan tab Inggris tetap identik dengan snapshot sebelum penambahan.
Revision conflict awal diselesaikan dengan membaca ulang; format pengguna
dipertahankan dan teks Inggris tidak berubah.

110paragraf/sel cocokMD,2tabel/28sel,20referensi/DOI dan21sitasi setara sumber.
Waktu6,828/10,056/4,359 memakai koma desimal dengan nilai yang sama; versi,
build,alamat/port/lease danjumlahprobe tetap. PDF14halaman total=3template+
5Inggris+6Indonesia. Previewjudul/tabel/referensi diperiksa, header tabel
diulang dan entri bibliografi utuh. DOCXZIP/XMLvalid; paginationDOCX belum
dirender. Tidak ada perubahan runtime,VM atau hasilpengujian.

VersiIndonesia untuk penelaahan; naskah pengajuan tetapInggris. Hasilmedia,
screenshot asli,runindependen,penulis dan kelayakanSJR tetapPENDING. Lihat
RencanaB14 dan jurnal17November untuk lokasi, validasi serta hasil publikasi.

Publikasi dikonfirmasi:90f7178 dipush ke branchfeature, SHAremote cocoklokal.
Tugas terjemahan selesai; tidak ada submission atau eksperimen baru.

Publikasi Figure 2: commit `2545624` terkonfirmasi pada branch feature; bukti, dua draft lokal dan laporan sudah di GitHub. Google Docs belum sinkron.

Publikasi CLI native18November: commit `20718ff` terkonfirmasi di branch feature; gambar dan kedua draft lokal sudah di GitHub. Google Docs/pagination masih tertunda.

## Caption Google Docs — 18 November

Konektor kembali tersedia. Fig.1/Fig.2 beserta penjelasan dan rujukan silang sudah ditambahkan langsung ke tab DraftInggris dan DraftIndonesia; gambar/tekslama/template terpelihara. PDF16halaman:3template+7Indonesia+6Inggris, caption dicek visual. Catatan dan caption ada di [CAPTION_FIGURE_IEEE.md](proposal/CAPTION_FIGURE_IEEE.md). Caption selesai; teks hasil eksperimen GoogleDocs dan labeldiagramPLANNED masih perlu sinkronisasi. Jangan menimpa gambar/layout pengguna dengan draftlokal secara penuh.

## Sitasi akhir kalimat — 18 November

Kedua tab GoogleDocs dan draftlokal MD/DOCX sekarang memakai angka[n] sebelum titik akhir kalimat, tanpa atribusi nama penulisnaratif.21kemunculan/20referensi perbahasa diperiksa; bibliografi,caption,gambar dan tabel tetap. Perubahan hanya28paragraf sitasi. PDFGoogleDocs tetap16halaman, tidak menyatakan seluruhhasilmedia lokal sudahsinkronkeDocs. Bukti:state/numeric-citations-20261118/.
