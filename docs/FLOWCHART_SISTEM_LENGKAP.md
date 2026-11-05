# Flowchart lengkap sistem VanGuard

Edisi 5 November 2026 — **satu diagram terhubung dari persiapan sampai pemulihan**.
CA 0.1.17; server/admin dan installer Windows 0.1.15 menurut checkpoint terakhir.
Diagram menjelaskan implementasi, bukan bukti semua uji lapangan sudah lulus.
Di GitHub, buka diagram untuk memperbesar atau melihat layar penuh.

```mermaid
flowchart TD
    START([Mulai]) --> PLAN["Operator: inventaris, izin lab, backup, jam dan console<br/>Pilih mode aplikasi atau internet terkelola"]
    PLAN --> NET["Router pilot 192.168.50.0/24<br/>Host .10, PC LAN .20, laptop Wi-Fi .30<br/>Host meneruskan jalur ke VM backend 192.168.100.0/24"]
    NET --> CAEX{"CA operasional sudah ada?"}
    CAEX -->|Ya| KEEP["Gunakan root dan histori existing<br/>Jangan init ulang atau restore index/CRL lama"]
    CAEX -->|Tidak: lingkungan baru| NEW["Buat Root CA satu kali<br/>Lindungi private key CA dan backup konsisten"]
    KEEP --> BACKEND
    NEW --> BACKEND
    BACKEND["Nyalakan VM CA, server dan admin<br/>HTTPS, CRL, WireGuard, daemon dan dashboard<br/>Firewall serta kebijakan resource default-deny"] --> HEALTH{"Readiness, trust, jam,<br/>routing dan dependensi siap?"}
    HEALTH -->|Tidak atau unknown| FIX["Tunda admission baru; perbaiki penyebab<br/>Jangan bypass TLS, CRL atau firewall"]
    FIX --> HEALTH
    HEALTH -->|Ya| PROFILE["Admin siapkan root PUBLIK, profil, pin server<br/>ID dan IP unik serta akun karyawan<br/>Internet terkelola perlu gateway Linux dan NAT"]
    PROFILE --> INSTALL["Distribusi EXE atau folder BAT tepercaya<br/>Cek SHA256, UAC, OS x64 dan path<br/>Pasang atau gunakan ulang Python, WireGuard, aplikasi"]
    INSTALL --> INSTOK{"Instalasi berhasil?"}
    INSTOK -->|Tidak| INSTFAIL["Catat error atau reboot yang diminta<br/>Pertahankan key/config; perbaiki lalu ulang paket"]
    INSTFAIL --> INSTALL
    INSTOK -->|Ya| PACKAGE{"Paket per-device?"}
    PACKAGE -->|Ya| WIZ["Wizard memakai profil dan alokasi admin<br/>Resume dengan state yang sama"]
    PACKAGE -->|Tidak: EXE umum| MANUAL["Admin menjalankan configure<br/>EXE umum saja belum memblokir internet"]
    WIZ --> TRUST
    MANUAL --> TRUST
    TRUST["Cocokkan root fingerprint, profil dan public key server<br/>Periksa konflik subnet dan jalur HTTPS admission"] --> TRUSTOK{"Konfigurasi dan trust valid?"}
    TRUSTOK -->|Tidak| TRUSTFAIL["Hentikan konfigurasi; periksa profil dan jaringan<br/>Jangan mengganti root atau melewati TLS untuk memaksa lolos"]
    TRUSTFAIL -->|Setelah perbaikan sah| TRUST
    TRUSTOK -->|Ya| MODE{"Internet terkelola schema2?"}
    MODE -->|Tidak: schema1| APPONLY["Hanya aplikasi internal dilindungi<br/>Mode ini tidak memblokir internet langsung"]
    MODE -->|Ya| GPO{"Gateway siap, tanpa konflik domain/GPO,<br/>preview policy berhasil?"}
    GPO -->|Tidak| POLICYFAIL["Tunda mode internet; tinjau bersama admin<br/>Jangan hapus kebijakan organisasi atau paksa bypass"]
    POLICYFAIL -->|Prasyarat selesai| GPO
    GPO -->|Ya| LOCK["Aktifkan policy Windows sebelum enrollment<br/>Blok internet langsung dan IPv6<br/>Jalur admission dan WireGuard tetap tersedia"]
    APPONLY --> IDENTITY
    LOCK --> IDENTITY
    IDENTITY{"Identitas perangkat sudah ada?"}
    IDENTITY -->|Tidak| KEYS["ENDPOINT membuat key X.509 dan CSR<br/>serta pasangan key WireGuard independen<br/>Private key tidak dikirim ke admin atau CA"]
    KEYS --> REQUEST["Kirim request.json PUBLIK ke admin"]
    IDENTITY -->|Ya| EXIST["Pertahankan key/config milik endpoint<br/>Periksa sertifikat dan state enrollment"]
    EXIST --> CERTREADY{"Sertifikat dan bundle sesuai?"}
    CERTREADY -->|Belum selesai enrollment| REQUEST
    CERTREADY -->|Expired, revoked atau key hilang| REPLACE
    CERTREADY -->|Ya| LOGIN
    REQUEST --> ADMIN["Admin login dashboard dengan password dan TOTP<br/>Periksa request, ID/IP, pemilik dan binding karyawan"]
    ADMIN --> ISSUE["CA menandatangani CSR menjadi sertifikat perangkat<br/>Server menyimpan registry dan binding immutable<br/>Registrasi BELUM menambahkan peer WireGuard"]
    ISSUE --> BUNDLE{"Workflow selesai dan bundle tersedia?"}
    BUNDLE -->|Belum| PENDING["Pending: perbaiki penyebab dan retry<br/>Wizard menunggu approval dengan exit20<br/>Lockdown yang aktif tetap berlaku"]
    PENDING --> BUNDLE
    BUNDLE -->|Ya| IMPORT["Endpoint import bundle<br/>Cocokkan root, profil, sertifikat dan key lokal"]
    IMPORT --> IMPORTOK{"Import valid?"}
    IMPORTOK -->|Tidak| PENDING
    IMPORTOK -->|Ya| LOGIN["Karyawan login melalui HTTPS<br/>Akun aktif dan binding perangkat wajib valid<br/>Login saja belum memberi peer atau akses"]
    LOGIN --> SESSION{"Sesi karyawan valid?"}
    SESSION -->|Tidak| DENYLOGIN["Tolak login/admission<br/>Perbaiki akun, sesi atau binding secara sah"]
    DENYLOGIN --> LOGIN
    SESSION -->|Ya| CHALLENGE["Connect meminta challenge sekali pakai<br/>Endpoint menandatangani proof dengan key lokal<br/>Challenge terikat pada sesi yang sama"]
    CHALLENGE --> SIX["Server menjalankan enam pemeriksaan perangkat<br/>1. Signature X.509 terhadap Root CA<br/>2. Masa berlaku sertifikat<br/>3. CRL terkini dan valid<br/>4. Serial tidak dicabut<br/>5. Proof-of-possession private key<br/>6. Binding sertifikat dan public key WireGuard"]
    SIX --> ADMIT{"Sesi, challenge dan seluruh cek lolos?"}
    ADMIT -->|Tidak| DENY["Fail-closed: tidak memberi lease/peer baru<br/>Catat alasan aman; lockdown schema2 tetap aktif"]
    ADMIT -->|Ya| PEER["Server memasang peer WireGuard dan lease terbatas<br/>Lease tidak melewati akhir sesi<br/>Kernel dan handshake WireGuard tidak diubah"]
    PEER --> TUNNEL["Client membuka tunnel miliknya<br/>Periksa handshake, transfer dan konektivitas<br/>Terminal connect tetap berjalan untuk renewal"]
    TUNNEL --> ACCESS{"Jenis trafik yang diminta?"}
    ACCESS -->|Aplikasi| RESOURCE{"Lease/sesi valid dan grant identitas,<br/>resource, protokol, port cocok?"}
    ACCESS -->|Internet schema2| INTERNET{"Lease/sesi valid, gateway siap<br/>dan grant internet perangkat aktif?"}
    RESOURCE -->|Ya| ALLOW["Izinkan hanya trafik yang memenuhi kebijakan"]
    INTERNET -->|Ya| ALLOW
    RESOURCE -->|Tidak| DROP["Default-deny: tolak trafik terkait dan akses aplikasi lewat LAN<br/>Tunnel aktif bukan izin semua tujuan"]
    INTERNET -->|Tidak| DROP
    ALLOW --> MONITOR
    DROP --> MONITOR
    MONITOR["Client renewal; daemon rekonsiliasi peer dan policy<br/>Pantau sesi, lease, sertifikat, CRL dan kesehatan<br/>Bedakan registered, lease, peer, handshake, transfer"] --> EVENT{"Peristiwa berikutnya?"}
    EVENT -->|Renewal berkala| CHALLENGE
    EVENT -->|Admin mengubah grant| ACCESS
    EVENT -->|Logout karyawan| LOGOUT["Logout terautentikasi dan idempotent<br/>Cabut token, challenge dan akses milik sesi itu<br/>Koordinasi dengan renewal; pertahankan sesi lain"]
    LOGOUT --> LOGOK{"Pencabutan server dan pemutusan terkonfirmasi?"}
    LOGOK -->|Tidak atau offline| RETRY["Pencabutan/pemutusan belum terkonfirmasi<br/>Simpan bukti; retry setelah layanan pulih<br/>Logout lokal saja tidak cukup"]
    RETRY --> LOGOUT
    LOGOK -->|Ya| CLEAN
    EVENT -->|Admin revoke perangkat| REVOKE["Admin memasukkan alasan pencabutan<br/>CA memperbarui histori serial dan CRL<br/>Server menonaktifkan akses perangkat terkait"]
    REVOKE --> REVOKED{"Workflow revoke selesai?"}
    REVOKED -->|Belum| REVOKING["Tetap revoking; periksa penyebab dan retry<br/>Jangan klaim pemutusan tanpa bukti"]
    REVOKING --> REVOKE
    REVOKED -->|Ya| REMOVE
    EVENT -->|Lease/sesi habis, akun nonaktif,<br/>sertifikat invalid atau CRL tidak tersedia| REMOVE["Invalidasi akses sesuai cakupan<br/>Server/daemon menghapus peer dan izin terkait<br/>Ukur penghentian; tidak menjanjikan nol detik"]
    EVENT -->|Disconnect, reboot client<br/>atau koneksi terputus| CLEAN
    REMOVE --> CLEAN
    DENY --> TROUBLE["Periksa akun, waktu, CRL, binding,<br/>sertifikat dan dependensi; tanpa bypass"]
    TROUBLE --> NEXT
    CLEAN["Client menghentikan tunnel yang dimilikinya<br/>Cleanup gagal: pertahankan konfigurasi<br/>Pastikan ownership dan tunnel berhenti"] --> CLOSED["Schema2: lockdown tetap berlaku<br/>Disconnect/reboot tidak otomatis membuka internet"]
    CLOSED --> NEXT{"Tindakan lanjutan yang sah?"}
    NEXT -->|Sesi/layanan pulih dan identitas valid| LOGIN
    NEXT -->|Sertifikat revoked/expired atau key hilang| REPLACE["Penggantian identitas melalui admin<br/>Revoke identitas lama bila perlu; simpan histori<br/>Endpoint membuat ID/key baru; binding pemilik/IP diwariskan"]
    REPLACE --> KEYS
    NEXT -->|Maintenance lokal| RECOVER["Admin lokal memastikan tunnel berhenti dan ownership jelas<br/>Konfirmasi recovery policy Windows dari state sah<br/>Bisa membuka internet langsung; bukan revoke server"]
    RECOVER --> FINISH([Catat kondisi akhir dan hasil uji])
    NEXT -->|Selesai tanpa membuka lockdown| FINISH
    ISSUE -.-> AUDIT
    DENY -.-> AUDIT
    LOGOUT -.-> AUDIT
    REVOKE -.-> AUDIT
    RECOVER -.-> AUDIT
    FINISH --> AUDIT["Audit lifecycle: waktu WIB, aktor, aksi, hasil, alasan aman<br/>Filter dan arsip CSV/JSON/manifest dari dashboard<br/>Pertahankan histori; jangan catat password, OTP, token atau private key"]
    MONITOR -.-> OBS["Pemeriksaan gagal: status tidak diketahui<br/>Liveness bukan readiness; daemon macet perlu penanganan<br/>Jangan klaim peer langsung hilang saat daemon berhenti"]
    OBS -.-> AUDIT
    classDef stop fill:#fff1f0,stroke:#b42318,color:#521b15;
    classDef decision fill:#fff8df,stroke:#a07800,color:#403000;
    classDef safe fill:#e9f7ef,stroke:#287a50,color:#143d28;
    classDef note fill:#eef3ff,stroke:#4566a0,color:#20304e;
    class TRUSTFAIL,FIX,INSTFAIL,POLICYFAIL,PENDING,DENYLOGIN,DENY,DROP,RETRY,REVOKING stop;
    class TRUSTOK,CAEX,HEALTH,INSTOK,PACKAGE,MODE,GPO,IDENTITY,CERTREADY,BUNDLE,IMPORTOK,SESSION,ADMIT,ACCESS,RESOURCE,INTERNET,EVENT,LOGOK,REVOKED,NEXT decision;
    class KEEP,PEER,ALLOW,FINISH safe;
    class AUDIT,OBS,PROFILE,SIX note;
```

**Cara membaca:** panah penuh adalah alur/tindakan; panah putus-putus adalah
pencatatan atau observasi lintas proses. Pilihan trafik berlaku per tujuan,
bukan berarti koneksi hanya boleh memakai salah satunya. Renewal lease tidak
memperpanjang sertifikat. Audit mencakup kejadian yang tersedia pada komponen
terkait; bukan jaminan setiap operasi client tercatat di dashboard.

**Batas:** mode internet dapat terhalang domain/GPO; jangan menghapus kebijakan
organisasi. Internet langsung baru diblok setelah policy endpoint aktif,
bukan hanya karena klik EXE atau registrasi CA. Pemutusan TCP aktif dan penerimaan
PC kampus tetap membutuhkan bukti uji lapangan tersendiri.

Langkah operasional: [manual](MODUL_PENGGUNAAN_VANGUARD.md),
[panduan lapangan dan terminal VM](PERSIAPAN_UJI_LAPANGAN.md),
[status pengujian](CHECKPOINT.md). Diagram lama tetap disimpan sebagai arsip;
untuk alur keseluruhan gunakan satu diagram ini.
