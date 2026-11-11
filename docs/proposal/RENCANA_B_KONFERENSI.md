# Rencana B: paper VanGuard berbasis pengujian VM

Status 11 November 2026: rencana penelitian dan bukti, **bukan paper siap submit**.
Rencana B berjalan sebagai alternatif keluaran penelitian; tidak menghapus
rencana paten atau mengubah instalasi. Dokumen kerja ini berbahasa Indonesia;
naskah submission, judul, caption, tabel dan abstrak akan berbahasa Inggris.

## 1. Target dan aturan yang harus dikonfirmasi

Target pengguna: [ICIMPACT](https://icimpact.telkomuniversity.ac.id/#call-for-paper).
Hasil pencarian situs resmi mencantumkan ICIMPACT2027, 3–5Februari2027,
Bandung/hybrid, maksimal6halaman termasuk referensi, bahasa Inggris, format IEEE,
blind peer review dan EDAS. Deadline submission tercantum **1Oktober2026**,
sudah lewat pada tanggal sesi11November. Akses halaman langsung403; belum ada
bukti perpanjangan. Konfirmasi status submission dengan panitia sebelum menetapkan
jadwal atau membayar. Tidak ada submission/registrasi/email yang dilakukan.

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

**VanGuard: Certificate-Based Admission and Access Revocation for WireGuard in a Virtual Testbed**

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
