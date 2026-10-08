# API VanGuard

Semua API menggunakan HTTPS dengan trust anchor `/etc/vanguard/root.crt` yang dipasang
melalui jalur tepercaya. Tidak ada mode `verify=False`. CA trust tidak diunduh tanpa verifikasi.
Respons gagal berbentuk `{"error":"..."}`. Request JSON dibatasi 64 KiB.

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
| POST | `/api/challenge` | Pemilik identitas terdaftar | Challenge untuk proof-of-possession |
| POST | `/api/verify` | Proof-of-possession | Admission; setelah lulus menambahkan peer |

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
{"certificate":"PEM", "wg_public_key":"BASE64"}
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
{"challenge_id":"...", "certificate":"PEM", "wg_public_key":"BASE64", "signature":"BASE64-DER"}
```

Keberhasilan:

```json
{"decision":"ACCEPT", "tunnel_ip":"10.8.0.2", "lease_until":1790000300.0}
```

TTL challenge 60 detik, maksimal 5 outstanding per perangkat. Challenge yang ditemukan
dikonsumsi sebelum validasi proof; retry perlu challenge baru. Endpoint admission dibatasi
30 request/menit/IP serta 240 request/menit global. Lease maksimal 300 detik, dipotong oleh
masa berlaku sertifikat, Root CA, atau CRL. CLI connect memperbarui admission maksimal tiap 60 detik.
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
`crl_signature_invalid`, `crl_invalid`, atau `root_validity`. Pada kegagalan CRL,
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
| POST | `/devices` | Upload `request.json` sebagai field `enrollment` |
| POST | `/devices/<id>/retry` | Melanjutkan workflow parsial |
| POST | `/devices/<id>/revoke` | Disable server dan revoke CA |
| GET | `/devices/<id>/certificate` | Download sertifikat perangkat |
| GET | `/healthz` | Liveness proses |

Semua route perangkat memerlukan login; form POST memerlukan field `csrf`.
