# Rencana B: paper VanGuard berbasis pengujian VM

Status 11 November 2026: draft awal tersedia, **bukan paper siap submit**.
Rencana B berjalan sebagai alternatif keluaran penelitian; tidak menghapus
rencana paten atau mengubah instalasi. Dokumen kerja ini berbahasa Indonesia;
naskah submission, judul, caption, tabel dan abstrak akan berbahasa Inggris.

## 1. Target dan aturan yang harus dikonfirmasi

Target pengguna: [ICIMPACT](https://icimpact.telkomuniversity.ac.id/#call-for-paper).
Hasil pencarian situs resmi mencantumkan ICIMPACT2027, 3–5Februari2027,
Bandung/hybrid, maksimal6halaman termasuk referensi, bahasa Inggris, format IEEE,
blind peer review dan EDAS. Deadline submission tercantum **1Oktober2026**,
sudah lewat pada tanggal sesi11November. Pengguna kemudian mengonfirmasi
perpanjangan sampai **30November2026** dan kategori cyber/network diEDAS.
Pakai tanggal tersebut sebagai target kerja berdasarkan informasi pengguna;
situs publik lama belum memverifikasi perpanjangan. Tidak ada submission,
registrasi, pembayaran atau email yang dilakukan.

[Dokumen pengguna](https://docs.google.com/document/d/1S9KanGfrsU7Ir62cIVfqIDfHBTnBfJDdKgZ96y26a4k/edit)
berhasil dibaca lewat ekspor teks: template IEEE untuk A4. Pertahankan style/margin
bawaannya; hapus semua petunjuk/contoh template saat menyusun naskah final.
Ekspor teks belum memverifikasi tata letak PDF akhir.

Kecocokan track adalah penilaian sementara: Track3 memuat digital identity/access
management; Track4 berfokus keamanan sistem AI/media. VanGuard saat ini studi
kontrol akses umum, belum eksperimen AI/media/kesehatan. Konfirmasi scope dengan
panitia/pembimbing; jangan menambahkan klaim AI demi cocok dengan judul track.
Pastikan aturan anonimisasi karena istilah blind review belum menjelaskan apakah
identitas penulis/repository harus disembunyikan. Pertahankan batas6halaman.

## 2. Fokus paper dan kontribusi yang akan diuji

Usulan judul Inggris:

**Certificate-Based Access Control and Revocation for a Virtualized Digital Media Service Using WireGuard**

Fokus media disetujui pengguna: layanan distribusi berkas media uji pada VM,
dengan autentikasi perangkat dan pencabutan akses. Layanan/eksperimen media
belum dijalankan; hasil aplikasi generik lama tidak diberi label hasil media.

Fokus: apakah kredensial karyawan yang sah tetap tidak memberi akses pada perangkat
yang gagal autentikasi; apakah pencabutan menghentikan akses yang sudah aktif;
apakah kondisi dependensi gagal tetap menolak akses. Installer adalah alat
pendukung eksperimen, bukan otomatis kebaruan penelitian.

Kontribusi yang akan dijelaskan dan diverifikasi:

1. Admission HTTPS dengan enam pemeriksaan sertifikat/perangkat dan sesi karyawan
   sebelum aktivasi peer; WireGuard tetap standar.
2. Pengikatan identitas sertifikat ke public key WireGuard, lease, pencabutan dan
   kebijakan aplikasi eksplisit yang dapat ditelusuri melalui audit.
3. Evaluasi VM yang dapat diulang: kontrol positif/negatif, latensi respons dan
   pencabutan, serta perilaku kegagalan dan keterbatasannya.

Ini calon kontribusi rekayasa, belum klaim pertama/unggul dari semua karya lain.
Review related work diperlukan sebelum menyatakan novelty. Awali landasan dengan
[NIST SP800-207](https://doi.org/10.6028/NIST.SP.800-207); tambahkan penelitian
primer yang relevan setelah benar-benar dibaca. Jangan memakai daftar referensi
contoh fisika dalam template sebagai referensi penelitian VanGuard.

## 3. Lingkungan dan versi

| Node yang dipertahankan | Peran |
| --- | --- |
| VM-CA,192.168.100.10 | Penerbitan/revokasi sertifikat dan CRL |
| VM-SERVER,192.168.100.20 | Admission, gateway WireGuard, daemon dan aplikasi uji |
| VM-CLIENT,192.168.100.30 | Endpoint Ubuntu sah; private key dibuat di client |
| VM-ADMIN,192.168.100.40 | Dashboard, registry dan audit admin |
| VM-ATTACKER,192.168.100.50 | Percobaan perangkat asing pada lab yang diizinkan |

Acuan runtime: CA0.1.17; server/admin/clientUbuntu0.1.15. Verifikasi versi aktual,
commit/hash, kernel/OS, alokasi RAM/vCPU, jam dan readiness sebelum run baru.
Pemeriksaan terakhir kelima VM shut off. Tidak ada pengujian baru dalam rencana ini.
Semua VM berbagi host: hasil performa harus membahas contention dan tidak boleh
digeneralisasi sebagai hasil deployment fisik.

Windows10/11 VM sudah dipensiunkan atas izin pengguna. Hasil native historis tetap
tersimpan. **Memakai VM untuk paper tidak otomatis berarti membuat ulang Windows.**
Utamakan lima Ubuntu untuk pengambilan bukti baru; Windows menjadi hasil tambahan
historis dengan tanggal/build/versi tepat. Bila paper wajib memuat screenshot atau
uji Windows baru, kebutuhan instalasi ulang harus ditentukan terpisah.

Jangan memulihkan snapshot state CA lama, menebak counter atau mengganti identitas
utama untuk mengulang eksperimen. Pakai identitas disposable, registrasi resmi,
backup serta cleanup terverifikasi; simpan semua run gagal.

## 4. Matriks eksperimen dan screenshot

Kolom bukti adalah daftar yang harus diambil, bukan bukti sudah tersedia.

| ID | Eksperimen | Bukti screenshot dan log | Kriteria hasil |
| --- | --- | --- | --- |
| E01 | Registrasi dan login sebelum admission | Registry admin serta daftar peer server pada run yang sama | Identitas terdaftar tetapi belum ada peer milik identitas uji |
| E02 | Perangkat sah + akun aktif | Client connect, peer/handshake, request aplikasi berizin | Enam pemeriksaan lulus; akses sesuai kebijakan |
| E03 | Akun karyawan valid pada perangkat asing | Penolakan dengan reason aman, audit dan daftar peer | Permintaan ditolak; tidak ada peer penyerang; kontrol sah tetap berhasil |
| E04 | Sertifikat invalid/expired/revoked, PoP salah, binding salah, replay | Output tiap kasus dan audit yang berkorelasi | Masing-masing ditolak; fixture expired diberi label bila bukan VM langsung |
| E05 | Revoke saat akses aktif | Sebelum: stream aplikasi berjalan; sesudah: event revoke, stream gagal dan peer hilang | Tidak ada transfer aplikasi lanjutan, readmission ditolak; waktu terukur |
| E06 | Logout dan dua renewal | Lease sebelum/sesudah, logout, audit; sesi lain sebagai kontrol | Renewal tidak memperpanjang sertifikat; logout hanya memutus cakupannya |
| E07 | CA tidak tersedia/daemon berhenti/lease habis | Waktu fault, status dependency, peer dan probe aplikasi | Fail-closed; pemulihan tidak menambah peer tanpa admission baru |
| E08 | Default-deny aplikasi dan jalur LAN | Port/protokol yang diizinkan dan percobaan akses langsung | Hanya identity/resource/protocol/port yang diberi izin berhasil |

Mulai E01–E03, kemudian E05/E08; lengkapi E04/E06/E07 sesuai cakupan paper.
Enam pemeriksaan admission tetap wajib walaupun gambar paper hanya menampilkan
kasus representatif. Pemblokiran akses aplikasi tidak sama dengan pemutusan
seluruh internet. Bila mengklaim internet Windows terkelola, gunakan dataset
khusus; jangan menukar bukti TCP aplikasi Linux dengan TCP internet Windows.

Rencana sampling: setidaknya10percobaan independen untuk metrik inti E03/E05,
dengan challenge/run ID baru dan kondisi tercatat. Ini target pengumpulan,
bukan jumlah hasil yang sudah diperoleh atau jaminan kecukupan statistik.
Laporkan n, gagal/timeout, median, mean, simpangan baku dan min/max dari data asli.
Tandai koneksi baru vs stream TCP yang sudah aktif. Ukur revoke dari konfirmasi
operasi yang didefinisikan ke observasi hilangnya akses menggunakan satu jam
monotonic observer; catat interval probe sebagai resolusi/batas pengukuran.

Gunakan [definisi metrik proyek](../testing/RESPONSE_METRICS.md): MTTR pada proposal
berarti Respond, bukan Recovery. Metrik aplikasi bukan waktu sejak password bocor.
Jangan mencampur angka dari versi, OS atau eksperimen berbeda menjadi satu rata-rata.
Jika tidak menjalankan baseline WireGuard murni/clear yang terisolasi, jangan
mengklaim overhead lebih rendah atau superioritas performa.

## 5. Pengambilan screenshot yang bisa ditelusuri

1. Tentukan run ID, node, versi dan skenario sebelum memulai. Buka terminal VM
   atau dashboard nyata; screenshot tidak dibuat dari mockup/rekonstruksi.
2. Simpan log/CSV asli dan screenshot sebelum–sesudah. Tampilkan konteks waktu,
   skenario, hasil akses serta peer yang relevan. Status dashboard saja tidak
   membuktikan paket benar-benar diblokir.
3. Simpan asli secara privat di luar Git, misalnya
   `/home/lui/VanGuard-Privat/conference-evidence/<RUN_ID>/` dengan izin privat.
   Buat manifest berisi filename, SHA-256, waktu, node, versi, ID skenario dan
   path log pendukung. Jangan menaruh credential dalam manifest publik.
4. Buat salinan untuk paper: tutup password, OTP/QR seed, token, private key,
   cookie dan identitas personal. Pertahankan data hasil; nyatakan crop/redaksi
   di caption bila relevan. Jangan mengedit screenshot untuk mengganti hasil.
5. Pilih1gambar gabungan2–3panel yang terbaca pada ukuran cetak. Simpan seluruh
   screenshot asli sebagai bukti pendukung TA. Tabel/plot dari log memberi
   bukti kuantitatif; screenshot menjadi ilustrasi run yang teridentifikasi.

Tidak mengasumsikan screenshot historis sudah lengkap. Inventaris gambar dan
pencocokan dengan log masih pekerjaan berikutnya. Jangan memublikasikan folder
privat/ZIP bukti mentah ke GitHub tanpa sanitasi.

## 6. Susunan paper Inggris, total maksimal6halaman

| Bagian | Anggaran halaman | Isi |
| --- | ---: | --- |
| Title, Abstract, Keywords, I. Introduction | 1.00 | Masalah, ruang lingkup, kontribusi dan ringkasan hasil yang sudah tersedia |
| II. Background and Related Work | 0.50 | Zero trust, admission dan celah yang diteliti |
| III. System Design and Threat Model | 1.00 | Satu diagram alur, binding, trust boundary dan batas ancaman |
| IV. Experimental Method | 0.75 | Topologi VM, versi, kontrol, sampling dan definisi metrik |
| V. Results and Discussion | 1.50 | Matriks hasil, plot pengukuran dan satu gambar screenshot gabungan |
| VI. Limitations and Conclusion | 0.50 | Single-host VM, bukti Windows historis dan batas generalisasi |
| References | 0.75 | Sumber primer yang dibaca dan benar-benar dipakai |
| Total | 6.00 | Termasuk gambar, tabel dan referensi |

Anggaran ini rencana, bukan verifikasi jumlah halaman. Gunakan template A4
pengguna dan hitung halaman PDF final; kurangi isi bila melampaui6halaman,
jangan mengecilkan font/margin. Tidak menjadikan paper sebagai manual instalasi.
Abstrak final ditulis setelah hasil dipilih; jangan mengisi angka sementara.

## 7. Bukti yang sudah ada dan batas pemakaiannya

- [Validasi0.1.15](../reports/VALIDASI_0.1.15_2026-11-02.md): integrasi Linux,
  Windows10build19044 dan Windows11build26300. Dua hasil revoke Windows adalah
  sampel tunggal masing-masing OS, bukan rata-rata atau perbandingan OS terkontrol.
- [Validasi rollout20Oktober](../reports/VALIDASI_ROLLOUT_2026-10-20.md): matriks
  lifecycle historis versi0.1.9; labeli versinya, jangan disebut hasil0.1.15.
- [Pra-uji9November](../reports/PRA_UJI_LAPANGAN_2026-11-09.md): baseline lokal
 355PASS/1SKIP terpisah dari pengujian VM; kelulusan unit test bukan acceptance fisik.
- [Audit CA0.1.17](../reports/PERBAIKAN_CA_IO_2026-11-03.md): bukti durability
  terisolasi; bukan bukti putus daya fisik atau jaminan readiness tanpa timeout.

Bukti aktual harus dicocokkan lagi dengan log sebelum dikutip dalam paper.
Jangan mengklaim tahan cloning seluruh private key, kebaruan protokol WireGuard,
production-ready, penurunan insiden organisasi, atau semua Windows sudah teruji.

## 8. Urutan penyelesaian

1. Pastikan deadline masih terbuka, track cocok, template dan aturan blind review.
2. Sepakati judul, penulis, kontribusi dan batas paper dengan pembimbing.
3. Inventaris log/screenshot; tentukan kekurangan yang membutuhkan run VM baru.
4. Siapkan backend/backup dan identitas uji; jalankan matriks, rekam bukti dan cleanup.
5. Susun tabel/plot serta naskah Inggris; isi hanya hasil yang telah diverifikasi.
6. Tinjau klaim, referensi, anonimisasi, keterbacaan gambar dan PDF maksimal6halaman.
7. Serahkan draft untuk persetujuan pengguna/pembimbing. Pengiriman ke konferensi
   dan pembayaran belum diotorisasi oleh penyusunan rencana ini.

Jika deadline target tertutup, naskah dan dataset tetap bisa disiapkan untuk venue
berikutnya yang scope-nya cocok. Penerimaan paper tetap keputusan reviewer.

## 9. Draft awal dan status Google Docs

- [Naskah Inggris](DRAFT_PAPER_ICIMPACT.md) dan [file Word](DRAFT_PAPER_ICIMPACT.docx).
- Sekitar3808kata termasuk catatan editor, tabel dan referensi; bukan bukti6halaman.
  DOCX memakai A4 dan geometri dua kolom dari template. Draft kini juga ada
  pada tab **Draft VanGuard** di GoogleDoc pengguna. ExportPDF13November
  menunjukkan5halaman draft termasuk referensi, terpisah dari3halaman template
  asli. Setelah gambar/hasil final dimasukkan, pagination wajib diperiksa ulang.
- Dua placeholder gambar dan satu placeholder hasil media sengaja belum diisi.
  Tidak ada screenshot buatan, angka media rekaan atau nama penulis yang ditebak.
- Angka6.828/10.056/4.359detik serta122/98probe berasal dari
  [laporan0.1.15](../reports/VALIDASI_0.1.15_2026-11-02.md); semuanya berlabel
  historis dan sampel tunggal/probe. Audit ulang log mentah sebelum submission.
- Dua puluh artikel jurnal2022–2026: empat dari
  proposal dan enam belas tambahan. DOI/metadata dicocokkan; bukti kuartil yang
  dipakai adalah JCR2024, bukan SJR. Lihat audit Bagian11 dan13. Ini bukan tinjauan
  sistematis seluruh literatur atau bukti novelty mutlak.
- Target GoogleDoc adalah tautan pengguna diBagian1. Template asli disimpan
  lokal di state/conference-draft-20261111/template-original.docx (diabaikan Git).
  GoogleDrive sudah terhubung dan draft berhasil ditulis pada tabbaru
  t.9hvk2e9fx9bh; tabtemplate t.0 dipertahankan identik berdasarkan readback.
  Semua paragraf dan28sel pada2tabel native cocok draft lokal. Tidak perlu
  mengimpor ulang salinanWord untuk melihat draft pada dokumen target.

Jika memakai Word sebagai jalan sementara, unduh DOCX lalu buka melalui Google
Docs sebagai dokumen terpisah untuk meninjau. Untuk mengisi template target,
pindahkan isi tiap bagian dan gunakan style template; periksa kembali tabel,
kolom dan jumlah halaman. Jangan menganggap impor otomatis menjamin formatIEEE.

## 10. Referensi proposal yang dipakai dalam paper

Proposal dibaca ulang melalui GoogleDocs pada11November. Nomor di bawah
mengacu daftar pustaka proposal, bukan nomor sitasi pada paper. Proposal asli
tidak diedit. Empat judul relevan dipakai dengan metadata penerbit; entri lainnya
belum diaudit menyeluruh dan tidak otomatis dianggap salah.

| Proposal → paper | Perbedaan metadata dan sumber verifikasi |
| --- | --- |
| [1] → [7], ZT-VPN | Penulis terverifikasi: Zohaib, Sajjad, Iqbal, Yousaf, Haseeb, Muhammad; Information15(11),734,2024. Proposal menulis Alshehri/Alzahrani dan15(4), serta tambahan kata Environments pada judul. [Penerbit](https://www.mdpi.com/2078-2489/15/11/734). |
| [8] → [8], industrial remote access | Penulis Federici, Martintoni, Senni; Electronics12(3),566,2023. Proposal menulis Iurshina/Boussard/Bonald dan12(5). [Penerbit](https://www.mdpi.com/2079-9292/12/3/566). |
| [9] → [11], WireGuard vs OpenVPN | Penulis Anyam, Singh, Larijani, Philip; Computers14(8),326,2025. Proposal menulis Owezarski/Lagraa sebagai coauthor. [Penerbit](https://www.mdpi.com/2073-431X/14/8/326). |
| [10] → [12], overlay/VPN performance | Penulis Gentile, Macrì, Greco, Fazio; FutureInternet16(8),283,2024. Proposal menulis Aiello/Mongelli/Papaleo dan16(3). [Penerbit](https://www.mdpi.com/1999-5903/16/8/283). |

Empat sumber proposal disitasi pada BagianII paper, bukan hanya ditambahkan ke daftar.
Naskah MD/DOCX dan tab Draft VanGuard telah disinkronkan. ExportPDF13November setelah penyaringan
tetap5halaman draft termasuk20referensi;3halaman lain adalah template.
Hasil media/screenshot masih PENDING. Penambahan referensi tidak menambah bukti
implementasi atau menjamin novelty/penerimaan paper.

## 11. Audit tahap pertama: 12 referensi — 13 November 2026

Catatan tahap pertama dipertahankan di bawah. Status terkini adalah20referensi;
audit delapan tambahan dan pemetaan bukti tersedia diBagian13.

Batas pengguna: artikel jurnal SINTA2 atau Q1–Q3, lima tahun terakhir.
Rentang kerja ditetapkan2022–2026 inklusif. Daftar pada tahap ini berisi12artikel
jurnal, bukan prosiding/preprint/standar:2dari2022,4dari2023,5dari2024,
dan1dari2025. Empat sumber lama diganti dalam paper; jejaknya diBagian12.

**Dasar kuartil: JIF/JCR2024, dirilis Juni2025, bukan SJR atau CiteScore.**
Pertanyaan preferensi SJR-saja belum dijawab. Pemilihan JCR adalah asumsi kerja
yang tercantum juga pada catatan editor draft, bukan persetujuan pengguna
terhadap kesetaraan metrik. Seluruh kandidat memenuhi Q1–Q3 pada kategori
JCR yang dicatat di bawah; **kelayakan khusus SJR masih BELUM_DIVERIFIKASI**.
Tidak ada klaim akreditasi SINTA2 untuk jurnal internasional ini. Jika aturan
kampus mensyaratkan SJR, validasi SJR tetap wajib sebelum daftar dinyatakan final.
Tahun peringkat tidak disamakan dengan tahun terbit atau diklaim paling baru.

Bukti peringkat: [katalog resmi UEFISCDI](https://uefiscdi.gov.ro/scientometrie-reviste)
dan [tabel JCR2024, edisi Juni2025](https://uefiscdi.gov.ro/resource-865584-JCR_2024.iunie2025.pdf),
kolom **JIF Quartile**, bukan AIS Quartile. Nomor ISSN digunakan untuk
membedakan jurnal bernama mirip. Salinan dan SHA-256 disimpan di state lokal.
Pemeriksaan struktur PDF bawaan ARS menghasilkan UNAVAILABLE karena pypdf
tidak terpasang; ekstraksi Poppler dapat dibaca tetapi itu bukan PASS struktur.
Peringkat juga dicocokkan bila tersedia ke pengumuman penerbit
[Information](https://www.mdpi.com/about/announcements/12307),
[Sensors](https://www.mdpi.com/journal/sensors/news-and-conferences/news/12201),
dan [Computers](https://www.mdpi.com/journal/computers/history).

| Ref | Artikel, tahun, dan bukti identitas sumber | Jurnal / ISSN | JIF quartile2024 dan kategori | Pemakaian dalam paper |
| --- | --- | --- | --- | --- |
| [1] | Syed et al.,2022, Zero trust architecture (ZTA): A comprehensive survey. [DOI](https://doi.org/10.1109/ACCESS.2022.3174679) | IEEE Access /2169-3536 | Q2; Computer Science, Information Systems | Landasan autentikasi, akses dan segmentasi; bukan bukti kelulusan VanGuard. |
| [2] | Dhiman et al.,2024, A review and comparative analysis of relevant approaches of zero trust network model. [Penerbit](https://www.mdpi.com/1424-8220/24/4/1328) | Sensors /1424-8220 | Q2; Instruments & Instrumentation | Perbandingan pendekatan dan tantangan implementasi. |
| [3] | Fernandez dan Brazhuk,2024, A critical analysis of Zero Trust Architecture (ZTA). [DOI](https://doi.org/10.1016/j.csi.2024.103832) | Computer Standards & Interfaces /0920-5489 | Q2; Computer Science, Software Engineering | Perlunya model ancaman dan kontrol yang dapat diuji. |
| [4] | Phiayura dan Teerakanok,2023, A comprehensive framework for migrating to zero trust architecture. [Repositori penulis](https://murex.mahidol.ac.th/en/publications/a-comprehensive-framework-for-migrating-to-zero-trust-architectur/) | IEEE Access /2169-3536 | Q2; Computer Science, Information Systems | Migrasi dan dependensi operasional, bukan hasil implementasi organisasi. |
| [5] | Tsai et al.,2024, Strategy for implementing of zero trust architecture. [DOI](https://doi.org/10.1109/TR.2023.3345665) | IEEE Transactions on Reliability /0018-9529 | Q1; Computer Science, Software Engineering | Strategi perlindungan resource dan batas penerapan. Tahun artikel2024 meskipun DOI memuat2023. |
| [6] | Adahman et al.,2022, An analysis of zero-trust architecture and its cost-effectiveness for organizational security. [Penerbit](https://www.sciencedirect.com/science/article/pii/S0167404822003042) | Computers & Security /0167-4048 | Q1; Computer Science, Information Systems | Membedakan model biaya/risiko organisasi dari hasil teknis VM. |
| [7] | Zohaib et al.,2024, Zero trust VPN (ZT-VPN). [Penerbit](https://www.mdpi.com/2078-2489/15/11/734) | Information /2078-2489 | Q2; Computer Science, Information Systems | Related work VPN, sertifikat dan sesi; kontrol health/location tidak diklaim ada di VanGuard. |
| [8] | Federici et al.,2023, A zero-trust architecture for remote access in industrial IoT infrastructures. [Penerbit](https://www.mdpi.com/2079-9292/12/3/566) | Electronics /2079-9292 | Q3; Computer Science, Information Systems; Q2 pada Engineering, Electrical & Electronic | Pemisahan otorisasi jaringan/resource; tidak mengklaim jaminan TEE. |
| [9] | Khan et al.,2023, A survey on X.509 public-key infrastructure, certificate revocation, and their modern implementation on blockchain and ledger technologies. [Repositori penulis](https://researchportal.hkust.edu.hk/en/publications/a-survey-on-x509-public-key-infrastructure-certificate-revocation/) | IEEE Communications Surveys & Tutorials /1553-877X | Q1; Computer Science, Information Systems | Konteks PKI/pencabutan; bukan klaim implementasi blockchain. |
| [10] | Berbecaru dan Lioy,2023, An evaluation of X.509 certificate revocation and related privacy issues in the web PKI ecosystem. [Repositori penulis](https://iris.polito.it/handle/11583/2980760) | IEEE Access /2169-3536 | Q2; Computer Science, Information Systems | Temuan soft-fail browser memotivasi uji status pencabutan; tidak digeneralisasi sebagai hasil VPN. |
| [11] | Anyam et al.,2025, Empirical performance analysis of WireGuard vs. OpenVPN. [Penerbit](https://www.mdpi.com/2073-431X/14/8/326) | Computers /2073-431X | Q2; Computer Science, Interdisciplinary Applications | Kondisi lingkungan harus dicatat; angka performanya bukan hasil VanGuard. |
| [12] | Gentile et al.,2024, Overlay and virtual private networks security performances analysis. [Penerbit](https://www.mdpi.com/1999-5903/16/8/283) | Future Internet /1999-5903 | Q2; Computer Science, Information Systems | Membedakan pengukuran RTT/bandwidth dari enforcement akses. |

Metadata judul/penulis/tahun/volume/halaman/DOI dicocokkan dengan sumber primer
penerbit atau repositori penulis. Crossref memberi metadata10artikel; dua
permintaanMDPI terkena429 dan diverifikasi lewat halaman penerbit, bukan
dinyatakan lolos API. Ringkasan isi dipakai sesuai bagian yang bisa dibaca;
tidak mengklaim semua full text telah ditelaah menyeluruh.

Audit memakai **academic-research-suite3.24.2**, workflow academic-paper,
mode citation-check dan citation_compliance_agent, dijalankan inline.
[Skill sumber](https://github.com/Imbad0202/academic-research-skills-codex/blob/82725acb393c4410ac6f47634a7f51b40a162fa4/skills/academic-research-suite/SKILL.md)
dipasang di /home/lui/.codex/skills/academic-research-suite melalui skill-installer.
Commit sumber82725acb393c4410ac6f47634a7f51b40a162fa4; tidak menjalankan
plugin hooks, eksperimen, layanan model eksternal atau submission.

Hasil audit sitasi lokal:12referensi unik,12DOI,13kemunculan sitasi,
0sitasi tanpa referensi,0referensi tanpa sitasi; urutan kemunculan[1]–[12]
cocok. Gaya numerik IEEE dipertahankan, DOI yang semula diduplikasi sebagai
URL diringkas menjadi satu DOI bertautan pada GoogleDocs. Seluruh nama penulis
referensi dipertahankan. Self-citation belum dapat dinilai karena daftar penulis
paper belum dikonfirmasi. Tidak ada pemeriksaan Turnitin/iThenticate.

Pemeriksaan [Retraction Watch melalui Crossref](https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/)
mengunduh dataset publik resmi13November:73.786catatan. Pencocokan12DOI
ke OriginalPaperDOI tidak menemukan catatan; pencocokan judul dilakukan untuk
10entri yang tersedia dalam cache metadata. Ini **bukan jaminan tidak pernah
ada pencabutan**, bukan penilaian kebenaran seluruh isi artikel, dan bukan
cakupan lengkap expression of concern/correction. Periksa lagi menjelang submit.
SHA-256 dataset:2ec0f845f1bbc1259278a461573308953f2f4ec7fde6d46aaae0eaceef38c7b0.

Tab Draft VanGuard, MD dan DOCX telah diperbarui. Readback12referensi dan
8paragraf related work cocok; template asli tetap identik,2tabel/28sel tetap.
Catatan editor menjelaskan batas JCR/SJR. Ekspor PDF terakhir8halaman total:
3template asli +5draft, termasuk referensi. Font/margin tidak diperkecil.
Gambar dan hasil media masih PENDING; jumlah halaman akhir diperiksa kembali
setelah bukti dimasukkan. Naskah belum siap submit.

## 12. Landasan teknis di luar daftar jurnal aktif

Empat rujukan awal berikut tetap berguna sebagai dokumen teknis/historis,
tetapi tidak dihitung dalam20referensi jurnal atau rentang2022–2026:

- [NIST SP800-207,2020](https://doi.org/10.6028/NIST.SP.800-207).
- [BeyondCorp,2014](https://research.google/pubs/beyondcorp-a-new-approach-to-enterprise-security/).
- [Paper WireGuard,NDSS2017](https://doi.org/10.14722/ndss.2017.23160).
- [RFC5280,2008](https://www.rfc-editor.org/rfc/rfc5280).

Pembatasan daftar referensi adalah keputusan penyusunan paper; standar teknis
dan arsitektur implementasi tidak berubah. Jika pembimbing membutuhkan sitasi
normatif langsung, sepakati pengecualiannya dahulu; jangan mengubah tahun atau
mengganti sumber standar dengan jurnal seolah jurnal tersebut menerbitkan standar.

## 13. Dukungan literatur terhadap pekerjaan VanGuard — tambahan 13 November

**Status terkini:20artikel jurnal,21kemunculan sitasi,0orphan,urutan pertama
[1]–[20].** Delapan artikel ditambahkan ke BagianIII–IV, bukan sekadar daftar
pustaka. Distribusi tahun edisi final:2022=2,2023=5,2024=9,2025=2,2026=2.
Sumber baru melengkapi kebijakan resource, autentikasi, lifecycle sertifikat,
otorisasi berkelanjutan, batas audit, dan metode pengujian.

Literatur mendukung alasan desain dan pilihan metode. Bukti bahwa implementasi
VanGuard bekerja berasal dari source, regresi, dan laporan eksperimen VanGuard
sendiri. Jumlah referensi atau kuartil jurnal tidak membuktikan sistem aman,
selesai, bebas bug, atau memiliki kebaruan yang belum pernah diteliti.

### 13.1 Identitas dan kelayakan delapan sumber tambahan

Semua memakai dasar yang sama:kolomJIF padaJCR2024 resmiUEFISCDI diBagian11.
Kategori adalah **Computer Science, Information Systems**, kecualiACMComputing
Surveys yang memakai **Computer Science, Theory & Methods**. Tahun2024 adalah
tahun pemeringkatan, bukan otomatis tahun artikel. SJR khusus tetap
BELUM_DIVERIFIKASI; tidak ada klaim akreditasi SINTA untuk sumber ini.

| Ref | Artikel dan bukti primer | Jurnal / ISSN / JCR2024 | Bagian sumber yang diperiksa dan batas pemakaian |
| --- | --- | --- | --- |
| [13] | Zanasi, Russo, Colajanni,2024. Flexible zero trust architecture for the cybersecurity of industrial IoT infrastructures. [Penerbit](https://www.sciencedirect.com/science/article/pii/S1570870524000258), [repositori penulis](https://cris.unibo.it/handle/11585/958250). DOI10.1016/j.adhoc.2024.103414. | Ad Hoc Networks /1570-8705 /Q1 | Abstrak dan§3:microsegmentation, pengelolaan kebijakan pusat dan enforcement terdistribusi. VanGuard memakai gateway pusat; ketahanan terdistribusi sumber ini tidak diwarisi. |
| [14] | Ang, Chekole, Zhou,2025. Unveiling the covert vulnerabilities in multi-factor authentication protocols: A systematic review and security analysis. [Penerbit](https://doi.org/10.1145/3734864), [institusi penulis](https://repository.sutd.edu.sg/esploro/outputs/journalArticle/Unveiling-the-Covert-Vulnerabilities-in-Multi-Factor/9911699509846). | ACM Computing Surveys /0360-0300 /Q1 | Abstrak:kelemahan desain dapat tetap ada padaMFA. Mendukung perlunya pengujian negatif; bukan bukti eksploitasi atau kekebalanTOTPVanGuard. Tidak mengklaim telaah menyeluruh37halaman. |
| [15] | Göppert, Walz, Sikora,2024. A survey on life-cycle-oriented certificate management in industrial networking environments. [Penerbit](https://www.mdpi.com/2224-2708/13/2/26). DOI10.3390/jsan13020026. | Journal of Sensor and Actuator Networks /2224-2708 /Q2 | §2 dan§5.2.6:proof-of-possession serta perbedaan permintaan pencabutan dan distribusi statusCRL. Bukan pembuktian transaksi storageCA atau waktu revokeVanGuard. |
| [16] | Ameer, Praharaj, Sandhu, Bhatt, Gupta,2024. ZTA-IoT: A novel architecture for zero-trust in IoT systems and an ensuing usage control model. [Penerbit](https://doi.org/10.1145/3671147). | ACM Transactions on Privacy and Security /2471-2566 /Q2 | §4.1, algoritmeADE langkahvi:periksa ulang dan hentikan operasi panjang jika otorisasi tidak berlaku. Model IoT berbasis skor berbeda dari rekonsiliasi periodikVanGuard. |
| [17] | Guardiola-Múzquiz, Soriano-Salvador,2023. SealFSv2: Combining storage-based and ratcheting for tamper-evident logging. [Penerbit](https://link.springer.com/article/10.1007/s10207-022-00643-1). | International Journal of Information Security /1615-5262 /Q2 | Abstrak dan§1–2:forward integrity membutuhkan perlindungan log khusus. VanGuard belum memakaiSealFSv2/ratchet; checksum arsip bukan bukti tahan manipulasi olehroot. Edisi2023, onlineDesember2022. |
| [18] | Sáez-de-Cámara, Flores, Arellano, Urbieta, Zurutuza,2024. Gotham testbed: A reproducible IoT testbed for security experiments and dataset generation. [Institusi penulis](https://research.mondragon.edu/documentos/6416a58c5db420433b7b6cab?lang=en), [naskah diterima](https://ebiltegia.mondragon.edu/xmlui/bitstream/handle/20.500.11984/6000/Gotham_Testbed_A_Reproducible_IoT_Testbed_for_Security_Experiments_and_Dataset_Generation.pdf?isAllowed=y&sequence=1). DOI10.1109/TDSC.2023.3247166. | IEEE Transactions on Dependable and Secure Computing /1545-5971 /Q1 | §3.2.4,6.1–6.2,7:konfigurasi, skrip dan topologi yang dapat direproduksi; batas emulasi. Tahun edisi final2024; DOI/online2023 tidak mengubah tahun sitasi final. VanGuard tidak menggunakanGotham atau meminjam hasilnya. |
| [19] | Kampourakis, Kampourakis, Takaronis, Gkioulos,2026. A systematic review of cybersecurity testbeds for smart environments: Architectures, attack coverage, and defensive evidence. [Penerbit](https://www.mdpi.com/1999-5903/18/9/445). DOI10.3390/fi18090445. | Future Internet /1999-5903 /Q2 | §3,5,9Tabel7,10–11:bedakan bukti emulasi, fisik, dan rekomendasi. Penerapan pelabelan bukti padaVanGuard adalah inferensi metodologis; domain asalnya smart environments. |
| [20] | Chang, Xu,2026. Design and implementation of a zero trust access control model driven by session lifecycle. [Penerbit](https://doi.org/10.1109/ACCESS.2026.3669103). | IEEE Access /2169-3536 /Q2 | §III-E,IV-B/C,V-B/C:receipt enforcement sebagai batas ukur, kegagalan dependensi dan tradeoff keamanan/ketersediaan. Hasil latensinya tidak dibandingkan denganVanGuard karena arsitektur dan batas timer berbeda. |

Metadata8tambahan berhasil dicocokkan melaluiCrossref dan sumber primer.
Nomor artikelACM293/22 diperiksa pada penerbit, karena fieldCrossref tidak
menyertakannya. HalamanACM/IEEE/Elsevier tertentu menolak pembukaan langsung;
teks primer terindeks dan repositori penulis dipakai dengan batas cakupan di
atas, bukan mengklaim semuaPDF berhasil diunduh atau dibaca penuh.

### 13.2 Peta literatur → implementasi → bukti → batas

Tabel ini adalah penelusuran bukti pada13November, **bukan pengujian ulang**.
Keberadaan fungsi tes saja tidak dinyatakan sebagai hasilPASS terbaru.

| Pekerjaan yang didukung | Literatur | Source/tes yang dapat ditelusuri | Bukti VanGuard dan batas kesimpulan |
| --- | --- | --- | --- |
| Registrasi berbeda dari admission; enam pemeriksaan perangkat | [1],[7],[9],[15] | [Admission.register/verify](../../vanguard/server.py), [validate_certificate/verify_proof](../../vanguard/pki.py), [regresi admission](../../tests/test_admission.py) | [Laporan0.1.15](../reports/VALIDASI_0.1.15_2026-11-02.md):admissionHTTPS/WG dan penolakan nyata. Tidak membuktikan hardware binding atau perlindungan jika seluruh private key dicuri. |
| TOTP admin, sesi karyawan, proof perangkat adalah kontrol terpisah | [7],[14] | [dashboard](../../vanguard/admin.py), test_login_requires_totp_and_rejects_replay pada[tes admin](../../tests/test_admin.py), [tes logout](../../tests/test_logout.py) | [Pra-uji9November](../reports/PRA_UJI_LAPANGAN_2026-11-09.md) merekam login/TOTP/logout; tidak berarti ketahanan terhadap seluruh seranganMFA/phishing. |
| CRL segar, certificate expiry, penggantian identitas | [9],[10],[15] | [validate_crl](../../vanguard/pki.py), [Authority.revoke](../../vanguard/ca.py), test_identity_replacement_preserves_old_binding_and_requires_revocation pada[tes admin](../../tests/test_admin.py) | [Laporan0.1.15](../reports/VALIDASI_0.1.15_2026-11-02.md):replacement primaryUbuntu danCA-only revoke. Renewallease tidak memperpanjang sertifikat; pencabutan harus terdistribusi dan diterapkan. |
| Lease, logout terlingkup dan pencabutan saat sesi berjalan | [16],[20] | [Admission.reconcile/logout_employee](../../vanguard/server.py), [regresi logout/renewal](../../tests/test_logout.py) | [Laporan0.1.15](../reports/VALIDASI_0.1.15_2026-11-02.md):renewal/logout dan satu waktu peer-removal per lingkungan. Bukan distribusi statistik, SLA, atau bukti media download sudah berhenti. |
| Resource/protokol/port eksplisit;default-deny dan penolakanLAN | [8],[13] | [NftResources.sync](../../vanguard/resource_policy.py), [tes resource policy](../../tests/test_resource_policy.py) | [Laporan0.1.15](../reports/VALIDASI_0.1.15_2026-11-02.md):grantTCP8082, activeinternalTCPblocking dan pemeriksaan bypass. InternetTCPpanjang/media workload tetapBELUM_TERUJI. |
| Dependencyfailure dan fail-closed | [10],[20] | [Admission.reconcile](../../vanguard/server.py), [health](../../vanguard/health.py), [tes admission](../../tests/test_admission.py) | [Laporan lifecycle20Oktober](../reports/VALIDASI_ROLLOUT_2026-10-20.md) dan[pra-ujiNovember](../reports/PRA_UJI_LAPANGAN_2026-11-09.md) dipisahkan menurutversi. Readiness503 historis tidak dihapus oleh probe berikutnya yang sukses. |
| KonsistensiCA saat interupsi | [15] sebagai konteks lifecycle saja | [Authority.transaction/check_state](../../vanguard/ca.py), [regresi durability](../../tests/test_ca_durability.py) | [PerbaikanCA0.1.17](../reports/PERBAIKAN_CA_IO_2026-11-03.md):26kasusdurability/interupsi/error/fallback dan74health/PKI/admission. Literatur yang ditambahkan tidak membuktikan atomicity lintasfile; power-lossmedia fisik tetapBELUM_TERUJI. |
| Audit timestamp dan arsip yang tidak menghapus bukti | [17] sebagai pembanding batas | [ActivityArchive.create](../../vanguard/admin_activity.py), [tes arsip](../../tests/test_admin.py) | Source membentuk snapshotCSV/JSON+checksum; audit integritasdatabase tercatat pada[pra-ujiNovember](../reports/PRA_UJI_LAPANGAN_2026-11-09.md). Tidak menyediakanforward integrity atau ledgerimmutable. |
| Reproduksibilitas dan pelabelan buktiLinux/mock/Windows/VM/fisik | [11],[12],[18],[19] | [Metode pada draftBagianIV](DRAFT_PAPER_ICIMPACT.md), [laporan0.1.15](../reports/VALIDASI_0.1.15_2026-11-02.md) | 122/98probeWindows bukan122/98runindependen; hasil tamuVM yang telah dipensiunkan bukan penerimaanendpointfisik. Topologi/build/config/skrip dan bukti asli harus dipertahankan. |

### 13.3 Validasi naskah dan yang masih tersisa

MD/DOCX dan tabDraft VanGuard tersinkron:3808kata,20referensi/DOIunik,
21sitasi; tidak ada referensi tanpa sitasi atau sebaliknya. Angka historis,
dua tabel,placeholdergambar dan hasilmediaPENDING dipertahankan. Readback
memastikan7paragraf revisi dan8referensi tambahan cocok; template t.0 identik.
EksporPDF terakhir8halaman=3template+5draft, termasuk20referensi. Halaman
desain dan daftar pustaka dirender/diperiksa, tanpa clipping/overlap; tidak
mengecilkanfont/margin. DOCXZIP/XML valid, tetapi paginationDOCX belum dirender.

Pencocokan20DOI dan20judul ternormalisasi dengan datasetRetractionWatch
73.786record13November tidak menemukan kecocokan. MetadataCrossref8tambahan
tidak memiliki update-to; keduanya bukan jaminan tidak ada koreksi/retraction,
dan bukan pemeriksaan plagiarisme. Ulangi status sumber menjelang submission.
Data audit lokal:state/conference-draft-20261111/expanded-metadata.json dan
twenty-citation-audit.json. Tahun/DOI/kuartil tidak boleh direka untuk memenuhi
syarat jurnal.

Tersisa:hasil dan screenshotmedia nyata, runindependen, penulis/afiliasi,
penetapanSJR jika wajib, pemeriksaan pembimbing dan pagination setelah gambar.
Tidak ada eksperimenbaru, perubahanruntime/VM/CA, atau klaim selesai melalui
penambahan referensi ini.
