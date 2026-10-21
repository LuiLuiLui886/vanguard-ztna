# Meta prompt VanGuard untuk Codex

Repository: https://github.com/LuiLuiLui886/vanguard-ztna

Dokumen ini menggabungkan tiga pekerjaan: perbaikan sistem, persiapan endpoint fisik, dan installer Windows. Gunakan sebagai spesifikasi tugas di dalam checkout proyek. Dokumen ini tidak menggantikan AGENTS.md dan bukan bukti bahwa implementasi atau pengujian telah selesai.

## Cara menggunakan

1. Simpan file ini di root repository yang dibuka oleh Codex, atau lampirkan isinya pada tugas Codex.
2. Untuk pekerjaan saat ini, gunakan prompt mulai di bawah. Fokus default adalah ENDPOINT_WINDOWS karena ketahanan layanan sedang dikerjakan secara terpisah.
3. Untuk fokus lain, pilih SISTEM, ENDPOINT, WINDOWS, atau SEMUA. SEMUA tetap menghormati pekerjaan ketahanan yang sedang berlangsung; audit dan integrasikan hasilnya, jangan membuat implementasi tandingan.
4. Jika menggunakan lingkungan yang hanya memiliki source code, Codex tetap mengerjakan patch dan pengujian yang tersedia. Pengujian yang memerlukan Windows, WireGuard kernel, VM, atau laptop fisik harus dilaporkan sesuai bukti sebenarnya.

### Prompt mulai

> Baca CODEX_VANGUARD_MASTER_PROMPT.md sebagai spesifikasi tugas dan ikuti instruksi proyek yang berlaku. Fokus: ENDPOINT_WINDOWS. Prioritaskan pilot dua endpoint Windows 11 pada router khusus 192.168.50.0/24 sesuai Bagian B0 dan D1: PC melalui LAN dan laptop endpoint melalui Wi-Fi, dengan seluruh VM tetap di laptop Linux. Audit checkout dan branch perbaikan terbaru terlebih dahulu; jangan kembali ke source main yang lebih lama atau menimpa progres ketahanan. Implementasikan persiapan endpoint dan installer Windows sesuai Bagian B dan C. Siapkan jalur pemasangan manual yang tervalidasi untuk pilot awal sambil melanjutkan installer; laporkan status keduanya secara terpisah. Untuk Bagian A, identifikasi dependensi dan kekurangan yang masih relevan tanpa mengerjakan ulang pekerjaan aktif. Kerjakan source, pengujian terisolasi, dokumentasi, dan paket lokal sampai selesai atau ada hambatan konkret. Siapkan konfigurasi penerapan dan rollback yang dapat ditinjau. Jangan menerapkan perubahan pada VM/router/jaringan/laptop aktif atau memublikasikan paket dalam tugas persiapan ini. Laporkan hasil aktual dan perbarui checkpoint.

### Prompt melanjutkan sesi

> Lanjutkan pekerjaan VanGuard berdasarkan CODEX_VANGUARD_MASTER_PROMPT.md, instruksi proyek, checkpoint, jurnal terbaru, dan kondisi Git saat ini. Verifikasi status pekerjaan terhadap kode serta bukti tes; jangan mengandalkan ringkasan percakapan saja. Pertahankan fokus dan batas penerapan sebelumnya. Kerjakan item pertama yang belum selesai dan tidak terblokir, tanpa mengulang perubahan yang sudah terbukti selesai. Bila ada blocker, jelaskan secara spesifik dan lanjutkan item lain yang tidak bergantung padanya.

---

## Instruksi utama untuk Codex

Kamu bertugas sebagai engineer yang mengimplementasikan perubahan di repository ini. Selesaikan pekerjaan yang dipilih melalui audit terarah, patch, pengujian, dan dokumentasi. Jangan berhenti pada rekomendasi atau menghasilkan meta prompt baru sebagai pengganti implementasi.

### Konteks dan hasil yang dituju

- CA, gateway/server, dashboard admin, dan layanan pendukung tetap berjalan pada VM.
- Pilot terdekat mencakup dua endpoint fisik Windows 11: komputer melalui LAN dan laptop lain melalui Wi-Fi. Laptop Linux pengguna tetap menjadi host seluruh VM; keenam VM lama tetap tersedia untuk regresi, bukan diganti oleh endpoint fisik.
- Pengguna memerlukan konfigurasi yang tidak bergantung pada alamat lab serta pemasangan Windows melalui `.bat` yang menjalankan `.ps1` native.
- Ketahanan layanan sedang diusahakan. Tentukan kondisi terbaru sebelum menyentuh pekerjaan tersebut.
- Pengguna telah menyetujui rencana router khusus 192.168.50.0/24 dan alamat perangkat pada Bagian B0. Host direncanakan melalui LAN. Rencana belum berarti sudah diterapkan; periksa interface, akses administrator, kemampuan router, serta kondisi aktual. Internet publik dan aplikasi bisnis belum menjadi lingkup pilot.
- Review lama mengacu pada commit `c454c0c5931615188bfadc568e3e3d1d2008e353`, versi 0.1.8. Gunakan hanya sebagai petunjuk pencarian, bukan sebagai target checkout atau bukti kondisi terbaru.
- Pemeriksaan 22 Oktober menemukan source 0.1.11 pada `fix/2026-10-20-readiness-lock` di `040dc21`, yang memuat hardening sebelumnya; main masih 0.1.8. Verifikasi ulang ref dan CI saat mulai. Baca checkpoint pada branch kerja terbaru, bukan menganggap catatan historis main sebagai keadaan VM saat ini. Master prompt terbaru di main dapat dibaca terpisah dari source branch kerja; jangan mengganti source dengan main hanya untuk mengambil dokumen ini.

### Audit awal dan cara bekerja

1. Temukan root Git, branch, commit, remote, status perubahan lokal, serta kemampuan lingkungan eksekusi. Checkout lokal yang dipilih pengguna adalah dasar pekerjaan. Jika perlu membandingkan upstream, fetch tanpa menimpa checkout; jangan otomatis pull, merge, reset, atau kembali ke commit acuan.
2. Baca AGENTS.md/instruksi yang berlaku, VANGUARD_CONTEXT.md, LANJUTKAN_PROYEK.md, docs/CHECKPOINT.md, dan jurnal terbaru yang relevan. Baca docs/SECURITY.md, docs/API.md, docs/WINDOWS_CLIENT.md, serta instruksi direktori yang akan diubah. Jika file berpindah, cari penggantinya.
3. Periksa diff sebelum mengedit. Identifikasi pekerjaan selesai, sedang berjalan, belum dikerjakan, dan terblokir. Jangan membuang perubahan lokal, melakukan stash otomatis, atau mengubah branch/worktree yang dipakai pekerjaan lain. Gunakan branch tugas yang sesuai atau worktree terpisah bila benar-benar diperlukan; jangan kehilangan dependensi perubahan lokal.
4. Buat rencana ringkas dan petakan dependensi. Ikuti kebiasaan repo untuk mencatat intent sebelum kelompok perubahan serta hasil sesudahnya. Gunakan checkpoint/handoff yang sudah ada; hindari dokumen status yang saling bertentangan.
5. Jalankan baseline yang relevan. Bedakan kegagalan sebelum perubahan dari regresi baru. Gunakan CI dan konfigurasi proyek untuk menentukan perintah tes, lint, build, dan packaging; jangan mengasumsikan jumlah tes lama masih berlaku.
6. Verifikasi temuan dengan file/fungsi dan bukti. Klasifikasikan sebagai BUG_TERBUKTI, RISIKO_DESAIN, FITUR_BELUM_ADA, atau BELUM_TERUJI. Temuan lama yang sudah ditutup cukup diverifikasi, tidak perlu diimplementasikan ulang.
7. Buat perubahan terfokus. Hindari rewrite, framework baru, abstraksi berlebihan, dan perubahan kosmetik yang tidak mendukung tujuan. Pertanyaan hanya untuk keputusan yang memblokir tindakan konkret; lanjutkan pekerjaan lain yang tidak bergantung pada jawaban.

### Batas arsitektur dan penerapan

- Pertahankan lima VM Ubuntu dan client Windows yang sudah ada. Jangan membangun ulang lab untuk memudahkan perubahan.
- Gunakan WireGuard standar tanpa modifikasi kernel/handshake. Admission HTTPS harus berhasil sebelum peer ditambahkan.
- Pertahankan validasi signature X.509, masa berlaku, freshness CRL, revocation, proof of private-key possession, serta binding sertifikat–key WireGuard pada registry. Sesi karyawan yang valid dan binding identitas immutable tetap wajib.
- Registrasi, instalasi, import bundle, startup, serta health check tidak boleh memberikan akses atau menambahkan peer secara otomatis.
- Jangan menonaktifkan verifikasi TLS, menerima CRL kedaluwarsa, memakai peer statis sebagai jalan pintas, atau memperlonggar default-deny agar tes lolos.
- Private key dibuat di endpoint. Jangan memasukkan secret, password, OTP, token sesi, token management, atau inventaris kredensial ke Git, paket, laporan, maupun log.
- Jangan membuat ulang CA atau mengembalikan index/CRL lama. Rollback paket tidak boleh menghidupkan kembali identitas yang sudah dicabut.
- Tugas persiapan mengizinkan edit source, contoh konfigurasi, build lokal, dan tes terisolasi. Perubahan pada VM aktif, jaringan host, CA aktif, database operasional, atau laptop pengguna berada di tahap penerapan terpisah.
- Siapkan konfigurasi, dampak, backup, dan rollback yang konkret sebelum meminta keputusan penerapan. Hormati otorisasi yang sudah diberikan dalam sesi. Tidak perlu persetujuan berulang untuk pekerjaan lokal yang sudah termasuk lingkup tugas.
- Jangan push, publish release, atau memasang paket pada perangkat pengguna dalam tugas persiapan ini.

## Bagian A — Perbaikan sistem dan integrasi pekerjaan ketahanan

Untuk fokus SISTEM/SEMUA, kerjakan item yang masih relevan dan tidak sedang dimiliki pekerjaan lain. Untuk fokus ENDPOINT_WINDOWS/ENDPOINT/WINDOWS, audit kontrak serta dependensinya; jangan membuat implementasi ketahanan paralel. Jika perubahan penting sedang berlangsung pada file yang sama, catat blocker spesifik dan kerjakan bagian yang independen.

### A1. Konsistensi state CA

Audit operasi OpenSSL, locking, penulisan index, serial, crlnumber, CRL, cache sertifikat, publikasi file, dan sinkronisasi disk. Riwayat counter kosong setelah shutdown adalah petunjuk; verifikasi penyebabnya. Atomic rename satu file tidak membuktikan transaksi multi-file aman.

Perbaiki penyebab yang terbukti dan deteksi state parsial saat restart. Recovery harus mempertahankan semua pencabutan serta kontinuitas counter. Jika konsistensi tidak dapat dibuktikan, hentikan operasi terkait dengan diagnosis jelas. Jangan menebak counter atau memakai backup lama tanpa rekonsiliasi yang menjaga revocation.

Uji pada CA sementara: interupsi pada batas operasi penting, kegagalan penulisan, retry, dan proses bersamaan. Pastikan tidak ada penerbitan/binding ganda yang tidak terlacak dan sertifikat revoked tetap ditolak. Laporkan secara terpisah bukti process-crash dan power-loss.

### A2. Lease, revocation, daemon, dan pemulihan client

Audit lease/sesi/sertifikat expired, akun disabled, revocation, CA unavailable, daemon stopped/hung, kegagalan renewal, serta reboot client. Jika watchdog dibutuhkan, definisikan pemantau, heartbeat dari rekonsiliasi yang benar-benar selesai, deadline, dan tindakan fail-closed; loop macet tidak dapat menjadi satu-satunya pengawas dirinya sendiri.

Definisikan serta ukur batas pencabutan akses. Uji koneksi aktif, renewal berulang, dua client, kegagalan teardown, dan reconnect. Pencabutan individual tidak boleh memutus client sah lainnya. Cleanup hanya boleh menyentuh service/interface/proses milik aplikasi. Pertahankan konfigurasi jika teardown belum terkonfirmasi. Reconnect wajib admission baru.

### A3. Logout dan lifecycle sesi

Periksa apakah logout server sudah ada. Jika belum, implementasikan logout terautentikasi dan idempotent yang menginvalidasi token, challenge terkait, serta lease/peer yang masih terikat pada sesi itu. Tangani race dengan admission/renewal tanpa menghapus akses dari sesi sah yang lebih baru.

Bedakan disconnect tunnel, penghapusan sesi lokal, dan pencabutan sesi server. Jika server tidak terjangkau, tampilkan hasil parsial dengan jujur. Uji token/challenge lama ditolak, retry aman, cakupan pencabutan tepat, dan log bebas rahasia.

### A4. Status yang akurat dan readiness

Pisahkan perangkat terdaftar, lease valid, peer terpasang, handshake terakhir, transfer, dan hasil akses aplikasi. Peer terpasang bukan bukti koneksi berhasil. Data gagal dibaca harus berstatus tidak diketahui dengan waktu pengamatan terakhir.

Pertahankan liveness sederhana dan buat readiness sesuai dependensi masing-masing layanan: konsistensi CA, CRL, database, interface, dan freshness rekonsiliasi. Batasi waktu pemeriksaan; jangan menerbitkan sertifikat atau mengaktifkan peer. Lindungi rincian operasional. Admission tetap melakukan validasi sendiri.

### A5. Lifecycle sertifikat, otorisasi resource, dan audit

- Bedakan renewal lease dari renewal sertifikat. Sediakan peringatan expiry dan alur penggantian identitas yang diaudit serta mempertahankan binding immutable. Perubahan model identitas memerlukan desain/migrasi eksplisit.
- Siapkan kebijakan untuk satu aplikasi uji: identitas/akun, resource, protokol, dan port. Metadata departemen bukan izin otomatis. Tetap default-deny; jangan membuka seluruh subnet. Jika target belum dipilih, gunakan resource disposable untuk tes terisolasi.
- Uji resource diizinkan/ditolak, bypass langsung dari LAN, dan sesi TCP yang sudah established saat akses dicabut. Jangan flush koneksi/firewall secara global atau merusak akses administrasi.
- Audit peristiwa relevan seperti login gagal, lockout, logout, revocation, dan recovery tanpa rahasia. Labeli identitas pada login gagal sebagai belum terautentikasi. Definisikan rotasi, pemantauan pertumbuhan, dan arsip yang dapat diperiksa; jangan menghapus bukti lama secara default atau mengklaim checksum kebal manipulasi root.

Kriteria selesai A: perbaikan terkonfirmasi, regresi keamanan lulus pada lingkungan yang tersedia, bukti keterbatasan dicatat, serta pekerjaan ketahanan yang sudah ada tetap terintegrasi.

## Bagian B — Server tetap VM, endpoint menjadi perangkat fisik

### B0. Topologi pilot dan rencana IP yang disetujui pengguna

Ada tiga perangkat fisik dan satu router pribadi khusus pengujian. Seluruh VM tetap berada pada laptop Linux pengguna. PC dan laptop Windows adalah dua perangkat client tambahan dengan identitas terpisah.

| Perangkat/jaringan | Rencana alamat | Sambungan/peran |
| --- | --- | --- |
| Router khusus | 192.168.50.1/24 | Gateway LAN dan Wi-Fi pengujian |
| Laptop Linux pengguna | 192.168.50.10/24 | Host VM; direncanakan melalui LAN, verifikasi interface nyata |
| PC Windows 11 | 192.168.50.20/24 | Endpoint fisik pertama melalui LAN |
| Laptop Windows 11 lain | 192.168.50.30/24 | Endpoint fisik kedua melalui Wi-Fi |
| Jaringan internal VM | 192.168.100.0/24 | Pertahankan CA .10, SERVER .20, CLIENT .30, ADMIN .40, ATTACKER .50, Windows VM .60 |
| Jaringan WireGuard | 10.8.0.0/24 | Server .1, alokasi client lama .2/.4 dan reservasi eksperimen .3 tetap dijaga |

Mask perangkat fisik adalah 255.255.255.0 dan gateway 192.168.50.1. Alamat fisik yang direncanakan manual berada di luar pool DHCP usulan 192.168.50.100–192.168.50.200. Verifikasi konflik alamat, pool aktual, reservasi, serta interface lain sebelum penerapan. Jangan menyamakan IP antarperangkat atau mengganti subnet NAT VM menjadi subnet fisik yang sama.

LAN dan SSID pengujian harus mengizinkan komunikasi yang diperlukan antarketiga perangkat. Periksa guest/client isolation hanya pada jaringan uji yang dituju. Konfirmasi model/akses router, interface LAN host, build/arsitektur Windows 11, dan hak administrator endpoint. Jangan mengasumsikan jaringan uji memiliki internet; siapkan paket/dependensi terverifikasi sebelum pengujian. Jangan menanyakan ulang OS endpoint atau rencana subnet yang sudah diketahui.

**Pekerjaan konektivitas yang harus disiapkan:**

1. Inventarisasi route, interface, jaringan libvirt, firewall host/VM/router, versi paket terpasang dan status layanan. Bedakan rencana alamat dari bukti konfigurasi aktual. Hindari mengaktifkan semua VM client/attacker sekaligus jika RAM host tidak mencukupi; definisinya tetap dipertahankan.
2. Evaluasi lebih dahulu routing terbatas dari kedua endpoint menuju VM-SERVER 192.168.100.20 melalui host 192.168.50.10. Bila cocok, siapkan route /32 ke server pada endpoint, atau route pada router jika kemampuannya mendukung, beserta jalur balik dan forwarding host. Default gateway endpoint tetap router .50.1. Jangan menganggap menambahkan route saja cukup: aturan libvirt NAT dan seluruh firewall yang dilewati harus diperiksa.
3. Untuk jalur routing tersebut, izinkan hanya sumber fisik .50.20/.50.30 menuju API TCP8081 dan WireGuard UDP51820 di VM-SERVER. Pertahankan akses lab lama dan administrasi yang sah. Jangan membuka akses langsung endpoint ke CA/dashboard atau aplikasi internal melalui LAN. Jangan flush ruleset global, mematikan firewall Windows, atau menambahkan NIC fisik langsung ke bridge NAT libvirt.
4. Jika routing tidak memungkinkan, siapkan alternatif port forwarding terbatas pada alamat LAN host. Dokumentasikan port eksternal/internal, source IP yang terlihat, aturan balasan, dan rollback. Konfigurasi API serta endpoint WireGuard harus konsisten dengan alamat yang dipakai endpoint; identitas TLS harus sesuai. Jangan membuka port WAN/internet secara otomatis.
5. Siapkan profil publik dan panduan penerapan terpisah untuk host Linux, router, VM-SERVER, PC LAN, dan laptop Wi-Fi. Sertakan pemeriksaan sebelum/sesudah serta cara mengembalikan route dan aturan milik pilot. Bedakan persiapan jaringan oleh operator dari installer aplikasi: installer tidak mengganti IP, DHCP, gateway, atau DNS utama endpoint.

Jika routing mempertahankan akses API melalui 192.168.100.20, verifikasi sertifikat yang ada sebelum memutuskan penerbitan baru. Bila alamat API berubah, siapkan SAN yang cocok tanpa mematikan verifikasi TLS. Semua pilihan tetap mengikuti kontrak konfigurasi Bagian B1; keberhasilan routing tidak menjadi alasan mempertahankan ketergantungan IP hardcoded pada client/bundle.

### B0.1. Prioritas pekerjaan menjelang pilot

Prioritaskan konektivitas, profil client, paket Windows yang dapat dipasang manual, enrollment, dan uji satu endpoint sebelum keduanya bersamaan. Installer lengkap tetap dikerjakan sesuai Bagian C; jalur manual yang berhasil tidak berarti installer selesai. Siapkan wheel, dependensi Windows dan manifest versi/hash tanpa private key atau sesi. Jangan hanya membawa paket dari main0.1.8 atau menganggap semua perubahan deployment ikut berada di dalam wheel: cocokkan juga unit/config dengan source teruji terbaru.

Siapkan dua device ID dan dua pasangan key yang dibuat pada endpoint masing-masing, dengan IP tunnel baru yang dipastikan unik oleh registry/admin. Jangan gunakan IP LAN .50.20/.50.30 sebagai IP tunnel, menyalin identitas VM, atau mengambil alokasi .2/.3/.4. Verifikasi model binding akun pada versi terbaru; masing-masing endpoint harus memiliki binding dan sesi yang sah.

Gunakan `internal-demo` pada 10.8.0.1:8082 sebagai target awal apabila kebijakan terbaru masih sesuai. Siapkan prosedur menjalankan layanan demo sementara dan grant eksplisit untuk kedua identitas. Demo dan grant hasil tes terdahulu telah dibersihkan menurut catatan repo; jangan menganggap target sudah aktif. Uji aplikasi lain menjadi tahap berikutnya, tanpa memperluas AllowedIPs atau policy secara otomatis.

### B1. Audit dan satu kontrak konfigurasi

Periksa khususnya vanguard/client.py, admin.py, ca.py, common.py, deploy/firewall.py, deploy/install.sh, unit systemd, environment examples, generator bundle, dan bootstrap Windows. Buat tabel lokasi, nilai hardcoded, fungsi, perubahan yang diperlukan, dan dampaknya.

Pisahkan API HTTPS, endpoint UDP WireGuard, alamat listen layanan, IP LAN endpoint, IP tunnel, subnet backend, serta resource tujuan. Mengubah parameter API tidak boleh meninggalkan endpoint WireGuard pada alamat lab. Jangan melakukan penggantian IP global.

Pilih satu skema konfigurasi sederhana sesuai repo, dengan versi dan precedence yang jelas. Gunakan kontrak sama pada client, bundle, dan generator deployment. Cakup endpoint API/WireGuard, port, server public key, root trust, listen address, subnet/IP tunnel, serta rute/resource yang diizinkan. Jangan membuat skema installer yang bersaing dengan konfigurasi client.

Validasi IP/hostname, port, CIDR, konflik alamat, dan input sebelum subprocess/generasi file. Pertahankan profil lab lama. Jangan memperluas AllowedIPs ke default route atau seluruh LAN tanpa kebutuhan eksplisit; route bukan pengganti kebijakan otorisasi. Jaga alokasi lama, termasuk reservasi eksperimen 10.8.0.3 bila masih berlaku pada checkout terbaru. Alokasi endpoint baru harus diverifikasi registry/admin.

### B2. Konektivitas dan TLS

Gunakan keputusan topologi/IP pada Bagian B0. Tandai BELUM_DIKETAHUI hanya untuk detail yang belum diverifikasi: interface host, model/kemampuan router, hak administrator, build/arsitektur Windows, internet untuk dependensi, dan pilihan routing atau port forwarding. Target pilot awal mengikuti Bagian B0.1; aplikasi bisnis/domain produksi belum ditetapkan.

Siapkan topologi serta matriks sumber–tujuan–protokol–port untuk pilihan yang sesuai: interface VM tambahan melalui bridge bila didukung, routing terkontrol, atau port forwarding terbatas. Jangan menganggap bridge Wi-Fi sama dengan Ethernet. Pertahankan isolasi backend CA/admin sejauh memungkinkan.

API admission harus dapat diakses sebelum tunnel terbentuk; endpoint UDP WireGuard juga harus terjangkau. Client tidak otomatis memerlukan akses langsung ke CA atau dashboard. Untuk NAT/port forwarding, dokumentasikan alamat eksternal/internal, source address yang terlihat firewall, dan identitas TLS.

Sertifikat HTTPS harus memiliki SAN yang cocok dengan hostname/IP yang digunakan client. Sesuaikan helper issuance yang masih membatasi alamat lab dengan validasi serta batas penerbitan yang jelas. Siapkan konfigurasi/CSR; jangan mengganti sertifikat aktif atau root CA dalam tahap persiapan.

Untuk aplikasi pada gateway, periksa binding dan firewall input. Untuk aplikasi pada server lain, siapkan forwarding, jalur balik, dan firewall kedua sisi; SNAT hanya jika alasan serta dampaknya dijelaskan. Cegah jalur LAN alternatif yang melewati kontrol akses. Akses dari internet adalah profil deployment terpisah, bukan port publik otomatis.

### B3. Enrollment dan client Ubuntu

Endpoint membuat key X.509 dan WireGuard sendiri. Hasilkan CSR/public key untuk admin, daftarkan device ID dan IP tunnel unik, lalu tautkan akun karyawan. Jangan menduplikasi identitas VM.

Bundle hanya berisi data yang sesuai untuk client, sertifikat publik, dan petunjuk platform. Import harus memeriksa kecocokan identitas/key/sertifikat dan tidak menimpa identitas lama. Konfirmasi trust root serta server public key melalui jalur administrasi tepercaya, bukan semata karena unduhan bundle berhasil.

Pertahankan kompatibilitas client Ubuntu yang sudah ada. Pemasangan Ubuntu fisik merupakan pekerjaan lanjutan bila dipilih; prioritas pilot saat ini adalah dua endpoint Windows 11. Setiap alur pemasangan client harus terpisah dari installer role server, menjaga jaringan utama, melindungi key/token, dan tidak membuat identitas baru saat reinstall. Integrasikan hanya CLI yang benar-benar tersedia.

Kriteria selesai B: profil lab tetap bekerja; profil custom konsisten pada client/bundle/deployment; TLS sesuai identitas; input invalid ditolak; onboarding tidak mengaktifkan peer; tersedia topologi, matriks konektivitas, contoh tanpa secret, dan prosedur pilot. Nilai jaringan yang belum diketahui tidak boleh diperlakukan sebagai konfigurasi siap pakai.

## Bagian C — Installer Windows native melalui BAT dan PowerShell

### C1. Paket dan pengalaman pengguna

Buat satu titik masuk `.bat` dengan logika utama `.ps1`. Usulan file: Install-VanGuard.bat, Install-VanGuard.ps1, VanGuard.ps1, Uninstall-VanGuard.ps1, konfigurasi contoh, manifest, dan README berbahasa Indonesia. Sesuaikan dengan struktur repo; jangan menggandakan fungsi.

Pengguna membuka installer, melihat prasyarat, menyetujui UAC bila diperlukan, memasang aplikasi, kemudian mendapat status dan langkah enrollment. Jendela harus menampilkan hasil akhir/kesalahan yang dapat ditindaklanjuti, lokasi log, dan exit code yang benar. Tangani path berspasi/karakter khusus, working directory, quoting, pembatalan UAC, serta argumen tanpa eval atau command injection.

Paket client harus bisa digunakan tanpa Git, clone repo, WSL, atau Git Bash. Target pilot adalah kedua endpoint Windows 11 pada Bagian B0; verifikasi arsitektur/build sebenarnya, jangan langsung menganggap x64 atau runtime sudah tersedia. Nyatakan matriks OS/arsitektur/PowerShell/Python/WireGuard berdasarkan bukti; usahakan bootstrap kompatibel Windows PowerShell 5.1 bila sesuai kebutuhan proyek. Jangan mengklaim dukungan versi yang belum diuji.

### C2. Runtime, distribusi, dan integritas

Deteksi Python/WireGuard yang sudah terpasang sebelum mengunduh. Gunakan runtime Python native yang cocok dengan pyproject.toml dan lingkungan aplikasi terisolasi. Jangan mengubah PATH global atau paket Python milik aplikasi lain tanpa kebutuhan dan pilihan yang jelas.

Jika perlu unduhan, gunakan sumber resmi, versi yang ditetapkan, artefak yang mendukung pip/venv sesuai kebutuhan, dan verifikasi integritas dari manifest/sumber tepercaya sebelum eksekusi elevated. Verifikasi signature serta expected publisher bila tersedia. Hash yang dihitung dari unduhan itu sendiri tidak membuktikan autentisitas. Jangan mengarang URL, checksum, versi, atau signature.

Kunci dependensi yang sesuai Windows dan sediakan build wheel/paket lokal yang dapat diulang. Tangani unduhan parsial, hash salah, internet terputus, installer lain sedang berjalan, exit code, dan reboot-required. Jangan reboot paksa. Jika menyediakan mode offline, semua artefak harus tersedia dan tervalidasi; mode tersebut tidak boleh diam-diam mengunduh.

Jangan bypass UAC, Group Policy, Defender, atau SmartScreen dan jangan mengubah execution policy mesin secara permanen. Jika distribusi membutuhkan signing organisasi, jelaskan kebutuhan dan statusnya; jangan mengklaim paket telah ditandatangani ketika belum.

### C3. Privilege, state, dan idempotensi

Pisahkan binary/runtime, konfigurasi, identitas, dan log. Pilih lokasi berdasarkan kebutuhan client serta ACL yang sudah ada; dokumentasikan identitas OS yang menjalankan aplikasi dan kebutuhan elevasinya. Hindari direktori writable oleh pengguna biasa sebagai sumber kode yang dijalankan elevated.

Buat direktori privat sebelum menulis key/token. Verifikasi ACL efektif pada Windows native, termasuk inheritance, reparse point/junction, dan file sementara. Pertahankan perlindungan di vanguard/windows.py; jangan menyalin logika kriptografi ke PowerShell.

Gunakan staging/state pemasangan dan lock untuk menangani instalasi bersamaan atau terputus. Reinstall/repair tidak boleh mengganti key, sertifikat, device ID, atau konfigurasi pengguna. Jangan melaporkan sukses ketika baru sebagian selesai. Preview/dry-run tidak boleh menginstal, membuat key, atau mengubah konfigurasi. Saring log; hindari transcript yang merekam kredensial.

### C4. Jaringan dan enrollment

Jangan menjalankan deploy/windows/bootstrap.ps1 provisioning VM pada laptop fisik. Installer tidak boleh mengubah IP LAN, DHCP, DNS utama, default gateway, firewall global, SSH, autologon, atau NIC berdasarkan MAC/IP lab.

Installer tidak membuat tunnel atau peer aktif. Saat connect, perubahan interface/route harus sesuai konfigurasi tunnel tervalidasi dan dibersihkan saat disconnect. Deteksi konflik subnet/VPN tanpa mengambil alih service/interface WireGuard lain.

Gunakan konfigurasi serta enrollment dari Bagian B. Tampilkan status berbeda: terpasang, belum enrollment, sertifikat tersedia, perlu login, admission diterima, tunnel terpasang, dan bukti koneksi bila tersedia. Alokasi IP tidak boleh didasarkan hanya pada ping.

### C5. Launcher, renewal, dan lifecycle penggunaan

Sediakan launcher/shortcut sederhana untuk konfigurasi/status, request enrollment, import bundle, login, connect, disconnect, diagnosis, dan logout jika backend tersedia. Audit CLI terbaru terlebih dahulu. Jika fungsi belum ada, implementasikan kontrak minimal yang diperlukan atau tandai dependensi spesifik; jangan menyediakan menu yang selalu melaporkan sukses.

Password diminta interaktif tanpa echo; jangan simpan pada JSON, argumen command line, atau log. Jaga proses renewal selama koneksi berlangsung. Tangani connect berulang, penutupan launcher, kegagalan renewal, serta teardown belum selesai. Stop hanya proses/service milik sesi aplikasi itu, bukan penghentian massal berdasarkan nama.

Disconnect harus menghentikan koneksi secara terkontrol; logout juga menginvalidasi sesi server bila tersedia. Jika backend belum mendukung, laporkan batasnya dan integrasikan dengan Bagian A3. Jangan menyamakan peer/service terpasang dengan handshake atau akses aplikasi berhasil.

### C6. Upgrade, repair, dan uninstall

Upgrade mempertahankan identitas/config dan memeriksa kompatibilitas state. Tangani proses aktif sebelum mengganti binary/runtime. Repair memulihkan komponen aplikasi tanpa enrollment atau rotasi key otomatis.

Uninstall menghentikan komponen milik instalasi, memverifikasi teardown, lalu menghapus binary/shortcut miliknya. Jangan menghapus Python/WireGuard yang digunakan bersama. Pertahankan identitas/config secara default; penghapusan identitas memerlukan pilihan eksplisit dengan dampak yang jelas.

Penghapusan lokal bukan revocation server. Sertakan prosedur decommission oleh admin dan jangan mengklaim akses telah dicabut tanpa konfirmasi. Rollback paket/config tidak mengembalikan state keamanan CA.

Kriteria selesai C: source installer/launcher/uninstaller, paket lokal tanpa secret, manifest integritas, panduan admin/pengguna, serta tes fresh install, reinstall, repair, upgrade, dan uninstall sesuai lingkungan. Jika dependensi terverifikasi/signing/native Windows belum tersedia, laporkan bagian yang belum bisa diselesaikan dan berikan build/test path yang konkret; jangan memberi label release siap distribusi.

## Bagian D — Verifikasi, pilot, dan pelaporan

### D1. Kriteria pilot PC LAN dan laptop Wi-Fi

Siapkan checklist berikut dalam panduan pilot, dengan status PASS/FAIL/BELUM_DIJALANKAN dan bukti per perangkat. Jalankan pada lingkungan fisik hanya ketika akses serta otorisasi penerapannya tersedia.

1. Preflight: alamat/mask/gateway sesuai rencana atau perubahan yang disetujui; tidak ada konflik subnet; API sebelum tunnel dapat diakses dengan TLS valid; readiness layanan diperiksa. Keberhasilan ping atau tes TCP saja tidak membuktikan jalur UDP WireGuard siap.
2. Uji PC Windows 11 LAN terlebih dahulu: pemasangan, generate key/CSR, enrollment/binding, login tanpa peer, admission, handshake, dan akses HTTP demo dengan grant. Tanpa grant, akses harus ditolak. Catat versi paket, konfigurasi publik, waktu, dan hasil tanpa rahasia.
3. Ulangi pada laptop Windows 11 Wi-Fi dengan identitas dan IP tunnel berbeda. Buktikan komunikasi melalui SSID uji yang dimaksud, termasuk pembentukan ulang koneksi setelah putus Wi-Fi secara terkontrol.
4. Hubungkan keduanya bersamaan. Buktikan dua identitas/lease/handshake dan akses aplikasi masing-masing; revoke atau logout endpoint pertama lalu pastikan aksesnya terputus dan endpoint kedua tetap berfungsi. Verifikasi kembali setelah peran ditukar menggunakan sesi/identitas uji yang sah, tanpa menghidupkan kembali identitas revoked.
5. Uji penolakan akses aplikasi langsung melalui LAN, perangkat tidak terdaftar, serta grant/lease/sesi yang tidak berlaku. Uji renewal berulang dan cleanup normal; catat pengujian expiry/reboot yang benar-benar dilakukan, bukan menyalin bukti Windows VM sebagai bukti endpoint fisik.
6. Siapkan recovery untuk risiko WIN-CLEANUP-02 jika masih relevan: cabut akses di server, verifikasi ownership dan keadaan service/proses, lalu konfirmasi teardown sebelum mengarsipkan/menghapus config. Jangan mengganti key atau menghapus service VPN lain agar koneksi berikutnya berhasil.
7. Setelah pilot, cabut identitas/sesi disposable dan grant terkait, hentikan demo sementara, serta pulihkan route/aturan sementara milik pilot. Pertahankan akses admin, CA state terbaru, identitas utama dan bukti pengujian.

Laporkan secara terpisah kesiapan PC LAN, laptop Wi-Fi, dan penggunaan bersamaan. Jika konektivitas/TLS, binding identitas, enforcement akses atau pemulihan gagal, tandai langkah itu sebagai penghambat sebelum memperluas pilot. Jangan menyatakan siap produksi; uji power-loss CA dan soak panjang yang belum dilakukan tetap dicatat terpisah, bukan dilakukan mendadak pada CA utama untuk mengejar jadwal.

### Pengujian yang wajib dibedakan

| Lapisan | Bukti yang dicari | Batas klaim |
| --- | --- | --- |
| Unit dan regresi lokal | Validasi config, state, race, import, error path | Tidak membuktikan jaringan/ACL Windows nyata |
| Integrasi terisolasi | Admission, revocation, lease, resource, cleanup | Laporkan jika WireGuard/OS masih mock |
| Windows native VM | BAT/PowerShell, UAC, ACL, service, reboot, installer | Tidak menggantikan uji jaringan laptop fisik |
| Pilot endpoint fisik | Enrollment sampai akses aplikasi dan pencabutan | Berlaku untuk topologi serta versi yang benar-benar diuji |

Pilih tes berdasarkan risiko perubahan. Pertahankan regresi untuk registrasi tanpa peer; penolakan sesi invalid, sertifikat expired/revoked, proof salah, replay, dan identitas tidak terdaftar; serta isolasi dua client. Jangan menghapus tes atau melemahkan assertion agar lulus.

Untuk konfigurasi: uji profil lab/custom, konsistensi bundle, SAN cocok/salah, konflik subnet/IP, serta tidak ada perubahan jaringan utama. Untuk Windows: fresh install, prasyarat tersedia/tidak cocok, path khusus, UAC dibatalkan, offline jika didukung, download/hash gagal, interupsi, reinstall, upgrade, repair, uninstall, preservasi key, ACL, dan exit code. Gunakan runner Windows native bila tersedia; tandai sisanya BELUM_DIJALANKAN.

Mulai dari satu endpoint fisik dan satu resource uji, kemudian lanjutkan kedua endpoint bersamaan sesuai Bagian D1: inventarisasi baseline, install, generate key/CSR, enrollment, login, admission, handshake, akses resource yang diizinkan, penolakan resource lain serta bypass LAN, renewal, disconnect/logout, revocation saat TCP aktif, reboot, dan cleanup. Tentukan indikator serta waktu yang harus direkam. Gunakan identitas uji dan jangan menambahkan peer statis.

Lakukan tes terarah setiap perubahan dan suite proyek yang relevan sebelum handoff. Jangan terus memperluas tes setelah risiko konkret sudah cukup diverifikasi. Untuk tahap penerapan kelak, siapkan urutan rollout, backup konsisten, rollback konfigurasi, serta cara menjaga akses administrasi.

### Laporan akhir dan checkpoint

Perbarui jurnal intent/hasil, checkpoint, dan handoff sesuai repo. Laporkan:

1. Fokus tugas, branch/commit dasar, dan pekerjaan pengguna yang diintegrasikan.
2. Ringkasan perubahan beserta file dan dampak terhadap perilaku.
3. Temuan beserta klasifikasi dan status: SELESAI_TERVERIFIKASI, IMPLEMENTASI_BELUM_UJI_TARGET, BELUM_DIJALANKAN, atau BLOCKED.
4. Perintah tes aktual, hasil passed/failed/skipped, alasan skip, dan lingkungan. Jangan menyalin hasil lama seolah hasil run baru.
5. Lokasi paket, panduan, contoh konfigurasi, serta batas dukungan.
6. Kekurangan yang masih relevan, keputusan deployment yang diperlukan, dan langkah berikutnya yang dapat dijalankan.

Jangan menyatakan siap produksi hanya karena build/unit test berhasil. Bedakan kode selesai, tes target selesai, dan rollout selesai. Jika sesi berhenti karena batas lingkungan/waktu, catat pekerjaan parsial serta langkah berikutnya tanpa mengklaim sudah selesai.

---

## Pilihan prompt fokus lainnya

### Perbaikan sistem

> Baca CODEX_VANGUARD_MASTER_PROMPT.md. Fokus: SISTEM. Audit progres ketahanan yang sudah ada, lalu kerjakan hanya kekurangan Bagian A yang belum selesai dan tidak bertabrakan dengan pekerjaan aktif. Prioritaskan konsistensi CA serta pencabutan/expiry/fail-closed berdasarkan bukti. Sertakan pengujian dan handoff Bagian D. Pertahankan batas persiapan lokal pada dokumen ini.

### Endpoint fisik

> Baca CODEX_VANGUARD_MASTER_PROMPT.md. Fokus: ENDPOINT. Implementasikan Bagian B dan siapkan verifikasi/pilot Bagian D. Audit dependensi Bagian A dan gunakan hasil yang sudah tersedia. Selesaikan konfigurasi, TLS/onboarding, panduan jaringan, dan pemasangan client Ubuntu; tetapkan kontrak yang akan dipakai installer Windows. Jangan menebak detail jaringan atau mengubah lingkungan aktif.

### Installer Windows

> Baca CODEX_VANGUARD_MASTER_PROMPT.md. Fokus: WINDOWS. Implementasikan Bagian C menggunakan kontrak konfigurasi terbaru dari Bagian B. Jika prasyarat client belum tersedia, buat perubahan minimum yang diperlukan tanpa menduplikasi skema konfigurasi. Kerjakan build lokal, pengujian yang tersedia, panduan, serta handoff Bagian D. Laporkan dengan jelas tes Windows native atau endpoint fisik yang belum dijalankan.

## Acuan cara memberi tugas kepada Codex

Spesifikasi ini memakai konteks proyek, batas perubahan, hasil yang diminta, dan cara verifikasi yang eksplisit. Instruksi proyek tetap berada pada AGENTS.md; dokumen tugas ini dibaca melalui prompt mulai.

- Dokumentasi prompting: https://developers.openai.com/codex/prompting/
- Instruksi proyek AGENTS.md: https://developers.openai.com/codex/guides/agents-md/

Spesifikasi teknis VanGuard disusun dari kebutuhan pengguna serta review repository sebelumnya. Codex tetap harus memverifikasi kondisi checkout terbaru saat menjalankannya.
