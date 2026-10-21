# API VanGuard

Semua API menggunakan HTTPS dengan trust anchor `/etc/vanguard/root.crt` yang dipasang
melalui jalur tepercaya. Tidak ada mode `verify=False`. CA trust tidak diunduh tanpa verifikasi.
Respons gagal berbentuk `{"error":"..."}`. Request JSON dibatasi 64 KiB.

## Tambahan0.1.9

Paket sudah di-rollout20 Oktober. Hasil dan keterbatasan bukti operasional ada
pada [matriks validasi](VALIDASI_ROLLOUT_2026-10-20.md).

Deployment mengikuti [checkpoint](CHECKPOINT.md); endpoint berikut tersedia
pada0.1.9. [Readiness0.1.10](READINESS_0.1.10.md) menunggu lock CA
maksimal3,5detik dan memeriksa dependency admin secara paralel; batas subprocess
tetap6detik. Versi0.1.11 terpasang pada ketiga layanan dan mengurangi I/O
publikasi CA; kontrak API tetap sama. Readiness yang gagal tetap503, tanpa
cache status sehat. Setelah patch kapasitas unit CA8thread, postflight93/93
respons HTTP200; sampel sebelumnya tetap menyimpan503. Ini bukan jaminan beban
tak terbatas. Lihat [catatan kapasitas](CA_SERVICE_CAPACITY.md) dan checkpoint.

| Method | Path | Akses dan hasil |
|---|---|---|
| GET | `/readyz` | Publik pada CA/server/admin; 200 ready atau 503 not_ready, dependency ready/not_ready/unknown, probe maksimal 6 detik |
| POST | `/api/employee/logout` | Server; JSON employee_session wajib. Mencabut satu token, challenge dan lease terkait; revoked dan peer_removal_confirmed true hanya setelah berhasil |
| GET | `/api/operations` | Server bearer management; ukuran DB/audit/disk dan sampel pertumbuhan, tidak mengembalikan isi credential |
| GET | `/operations` | Dashboard sesi admin; status penyimpanan admin/server |
| POST | `/devices/<id>/replace` | Dashboard sesi admin + CSRF + upload enrollment; identitas lama wajib revoked, ID/key baru dari client, akun dan IP diwariskan |

Logout memakai lock yang sama dengan verify. Retry token tercabut bersifat
idempotent melalui hash tombstone; token asing ditolak 403. Invalidasi token
di-commit sebelum penghapusan peer; kegagalan kernel menghasilkan 503 dan perlu
retry. Lease yang sudah diambil alih sesi lain tidak dihapus oleh retry sesi lama.
Token expired dipertahankan sebagai record invalid agar logout masih dapat
memastikan penghapusan akses. Token/hash tidak dikembalikan pada audit.

`GET /api/devices` menambahkan registered, lease_valid, peer_present,
last_handshake (Unix; nol belum pernah), rx_bytes/tx_bytes kumulatif dan observed_at.
`live` adalah alias kompatibilitas peer_present, dapat null bila pemeriksaan
gagal. Lease_valid memeriksa sesi dan binding selain expiry/enabled. Byte
kumulatif bukan laju transfer dan tidak membuktikan aktivitas aplikasi saat ini.

Readiness membaca CRL yang sudah ada; tidak memanggil endpoint penerbit CRL,
menerbitkan sertifikat atau menambah peer. `/healthz` tetap liveness sederhana.
Client Remote kini hanya menampilkan kode HTTP untuk error upstream, sehingga
body upstream tidak tersalin ke log/UI.

Sejak 0.1.4, challenge/verify mengembalikan `X-VanGuard-Request-ID` acak buatan
server untuk korelasi audit. Nilai request header caller tidak dipakai ulang.
Penolakan aplikasi 400/403 dapat menghasilkan audit `admission_timing` dengan
`schema`, `request_id`, `endpoint`, `status`, `reason`, `detect_ns`, `respond_ns`,
`total_ns`, `clock` dan `response_boundary`. Metrik memakai monotonic server;
`total_ns = detect_ns + respond_ns`. Tidak ada password/token/body/nonce dalam
event tersebut. Arti batas waktunya ada di [RESPONSE_METRICS.md](RESPONSE_METRICS.md).
Event hanya dapat dibaca melalui endpoint audit manajemen yang sudah dilindungi.

## VM-CA — `https://192.168.100.10:8080`

| Method | Path | Akses | Input/hasil |
|---|---|---|---|
| GET | `/healthz` | Publik | Liveness proses |
| GET | `/api/ca/certificate` | Publik | Root certificate PEM; bukan mekanisme bootstrap trust |
| GET | `/api/ca/crl` | Publik | CRL PEM bertanda tangan, diterbitkan kembali pada setiap fetch |
| POST | `/api/ca/issue` | Bearer CA token | `device_id`, `csr`; hasil `certificate`, `serial` (hex) |
| POST | `/api/ca/revoke` | Bearer CA token | `serial` (hex); hasil `revoked: true` |

Token CA hanya untuk VM-ADMIN. OpenSSL menandatangani CSR P-256 yang CN-nya sesuai device ID.
Extension permintaan CSR tidak disalin: CA menetapkan CA:false, digitalSignature, clientAuth.
Sertifikat perangkat berlaku 30 hari; CRL berlaku satu jam. Retry CSR identik mengembalikan
sertifikat yang tersimpan, termasuk jika sertifikat tersebut sudah dicabut; buat identitas baru
untuk reenrollment. Revoke serial yang sudah dicabut bersifat idempotent.

## VM-SERVER — `https://192.168.100.20:8081`

| Method | Path | Akses | Fungsi |
|---|---|---|---|
| GET | `/healthz` | Publik | Liveness; bukan jaminan CA/daemon/tunnel sehat |
| POST | `/api/devices` | Bearer server token | Mendaftarkan binding, tanpa `wg set` |
| GET | `/api/devices` | Bearer server token | Daftar registry, enabled, lease, keberadaan peer |
| POST | `/api/devices/<device_id>/disable` | Bearer server token | Disable permanen, batalkan challenge, hapus peer |
| GET | `/api/audit` | Bearer server token | 200 peristiwa terakhir |
| GET/POST | `/api/employees` | Bearer server token | Daftar akun tanpa hash; buat akun dengan username/password |
| POST | `/api/employees/<username>/disable` | Bearer server token | Nonaktifkan akun/sesi dan hapus peer miliknya |
| POST | `/api/devices/<device_id>/employee` | Bearer server token | Ikat perangkat ke username aktif; immutable |
| POST | `/api/employee/login` | Username/password karyawan | Sesi karyawan, tidak menambah peer |
| POST | `/api/challenge` | Sesi karyawan + identitas terdaftar | Challenge untuk proof-of-possession |
| POST | `/api/verify` | Sesi yang sama + proof-of-possession | Admission; setelah lulus menambahkan peer |

Mulai 0.1.3 login menerima `username` dan `password` melalui HTTPS; hasil berisi
`session_token`, `username`, dan `expires_at` (Unix). Sesi berlaku 8 jam dan tidak
memberi hak management. Password 12–256 karakter, disimpan sebagai hash scrypt.
Lima kegagalan per username/IP mengunci login selama 5 menit. Server menyimpan
hash token saja. Perangkat tanpa binding akun tidak bisa melakukan admission.

Registrasi:

```json
{
  "device_id": "vm-client",
  "certificate": "-----BEGIN CERTIFICATE-----\n...",
  "wg_public_key": "base64-public-key-32-byte",
  "tunnel_ip": "10.8.0.2"
}
```

Nama dibatasi `[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}`. Device ID, sertifikat, dan public key
bersifat immutable. IP tidak boleh bentrok dengan perangkat enabled. Disable tidak
menghidupkan kembali identitas lama; IP boleh dipakai identitas baru setelah disable.
Implementasi validator alamat membatasi subnet `10.8.0.0/24`, mengecualikan network,
server, dan broadcast. Client lab tetap meminta `10.8.0.2`.

Challenge request:

```json
{"certificate":"PEM", "wg_public_key":"BASE64", "employee_session":"TOKEN-PRIVAT"}
```

Response memuat `challenge_id`, `nonce`, `expires_at` (Unix seconds), `tunnel_ip`, `message`.
Pesan yang ditandatangani adalah UTF-8 JSON **sort_keys=True, separators=(',', ':')**:

```json
{"certificate_sha256":"...","challenge_id":"...","nonce":"...","protocol":"vanguard-admission-v1","tunnel_ip":"10.8.0.2","wg_public_key":"..."}
```

Client membangun ulang pesan tersebut, lalu menandatanganinya dengan private key X.509
menggunakan ECDSA P-256/SHA-256. Signature ASN.1 DER dikirim sebagai base64 standar.

Verify request:

```json
{"challenge_id":"...", "certificate":"PEM", "wg_public_key":"BASE64", "signature":"BASE64-DER", "employee_session":"TOKEN-PRIVAT"}
```

Keberhasilan:

```json
{"decision":"ACCEPT", "tunnel_ip":"10.8.0.2", "lease_until":1790000300.0}
```

TTL challenge 60 detik, maksimal 5 outstanding per perangkat. Challenge yang ditemukan
dikonsumsi sebelum validasi proof; retry perlu challenge baru. Endpoint admission dibatasi
30 request/menit/IP serta 240 request/menit global. Lease maksimal 300 detik, dipotong oleh
masa berlaku sertifikat, Root CA, CRL, dan sesi karyawan. CLI connect memperbarui admission maksimal tiap 60 detik.
Sesi verify harus sama dengan sesi challenge dan masih aktif setelah fetch CRL/proof.
Masa challenge diperiksa kembali sebelum `wg set`. Fetch CRL yang bertanda tangan
sah tetapi <=1 detik lebih maju dapat menunggu satu kali lalu divalidasi ulang;
tidak ada penerimaan CRL sebelum lastUpdate atau setelah nextUpdate.

### Audit penghapusan peer

Event `peer_removed` menyimpan `device_id` (null untuk key asing) dan `detail`
berupa string JSON, misalnya:

```json
{"reason":"lease_expired","wg_public_key":"BASE64-PUBLIC-KEY","lease_until":1790000300.0}
```

Alasan mencakup `startup_reset`, `device_disabled`, `lease_expired`, `unknown_peer`,
`binding_mismatch`, `certificate_revoked`, `certificate_future`, `certificate_expired`,
`certificate_invalid`, `crl_unavailable`, `crl_future`, `crl_expired`,
`crl_signature_invalid`, `crl_invalid`, `employee_session_invalid`, atau `root_validity`. Pada kegagalan CRL,
`crl_error` memberikan detail diagnostik termasuk waktu issuer/validator bila relevan.
Peristiwa lama sebelum diagnosis terstruktur bisa berisi teks biasa; konsumen audit
harus mempertahankannya sebagai riwayat dan tidak mengasumsikan selalu JSON.

Status: `400` input tidak valid, `401` token tidak sah, `403` admission ditolak,
`404` identitas tidak ditemukan, `409` konflik binding, `429` rate limit,
`503` operasi lokal/dependency gagal. Dashboard menerjemahkan penolakan upstream menjadi `502`.

## VM-ADMIN — `https://192.168.100.40:5000`

Antarmuka HTML; POST memakai form/multipart, cookie sesi, dan CSRF token.

| Method | Path | Fungsi |
|---|---|---|
| GET/POST | `/login` | Password + TOTP |
| POST | `/logout` | Invalidasi sesi pada database |
| GET | `/` | Dashboard, status perangkat, audit |
| POST | `/devices` | Upload `enrollment`; metadata display_name/department/owner/platform dan employee_username |
| POST | `/devices/<id>/metadata` | Edit metadata; tidak mengubah sertifikat/key/binding |
| POST | `/devices/<id>/employee` | Tautkan username ke perangkat lama |
| POST | `/employees` | Buat akun karyawan dengan username/password |
| POST | `/employees/<username>/disable` | Nonaktifkan akun karyawan |
| POST | `/devices/<id>/retry` | Melanjutkan workflow parsial |
| POST | `/devices/<id>/revoke` | Disable server dan revoke CA |
| GET | `/devices/<id>/certificate` | Download sertifikat perangkat |
| GET | `/healthz` | Liveness proses |

Semua route perangkat memerlukan login; form POST memerlukan field `csrf`.

## Dashboard 0.1.5

Endpoint berikut memerlukan sesi admin hasil password/TOTP; semua POST tetap
memerlukan CSRF. `GET /devices/<id>/history` menampilkan masa berlaku/fingerprint,
alasan/waktu workflow pencabutan serta 100 audit administrasi terbaru per identitas.
`GET /devices/<id>/bundle` mengirim ZIP materi publik setelah pemeriksaan workflow,
binding akun, validity dan CRL; tidak menambah peer. `POST /devices/<id>/revoke`
sekarang mewajibkan field `reason` dari enum pada [panduan dashboard](DASHBOARD_0.1.5.md).
Reason tidak ditambahkan ke kontrak CA API; reason CRL OpenSSL tetap sama.

## Dashboard 0.1.6 — halaman audit terautentikasi

Route HTML memakai sesi password/TOTP dan pemeriksaan CSRF untuk POST:

| Method | Path | Fungsi |
|---|---|---|
| GET | `/activity` | Filter tanggal WIB, aktor, ID perangkat dan peristiwa; 50 catatan per halaman |
| POST | `/activity/archives` | Buat snapshot seluruh hasil filter. Field `csrf` wajib |
| GET | `/activity/archives` | Daftar arsip snapshot beserta waktu, pelaku, jumlah, filter dan checksum |
| GET | `/activity/archives/<id>/download` | Validasi checksum dan unduh ZIP; hash SHA-256 ada pada header respons |

Rentang tanggal pada filter bersifat inklusif menurut hari WIB. Field CSV/JSON
dibatasi pada detail aman yang dikenal UI; kode event lama yang belum dikenal
ditampilkan dengan keterangan umum. Batas arsip 10.000 catatan dan 8 MiB data
sebelum kompresi. Pembuatan/unduhan arsip dicatat pada audit dashboard.
