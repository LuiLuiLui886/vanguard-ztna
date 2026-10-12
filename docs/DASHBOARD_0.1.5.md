# Dashboard VanGuard 0.1.5

Perubahan ini menjawab kebutuhan health check/audit/provisioning pada proposal
§3.3.2 dan alasan pencabutan/riwayat pada §3.4. Enam pemeriksaan admission dan
registrasi tanpa peer tetap berlaku. Panduan dari awal ada pada
[tutorial penggunaan](TUTORIAL_PENGGUNAAN.md).

## Fitur dan cara memakai

| Fitur | Cara memakai | Batas |
|---|---|---|
| Kesehatan layanan | Buka dashboard; CA dan Server diperiksa lewat HTTPS secara terpisah | Liveness, bukan jaminan validity/CRL atau tunnel. Muat ulang untuk pemeriksaan baru |
| Pemeriksaan CA sebelum issuance | Otomatis ketika registrasi belum memiliki sertifikat | Jika gagal, workflow pending tetap bisa diretry; tidak membuat peer |
| Aktivitas administrasi | Lihat 25 peristiwa terbaru dengan waktu Unix, aktor, device ID dan detail terstruktur | Mulai 0.1.5; catatan sebelum upgrade tidak direkonstruksi; bukan audit tahan manipulasi oleh root |
| Riwayat perangkat | Klik **Riwayat perangkat** | Maksimal 100 peristiwa terbaru untuk satu identitas; belum histori renewal 1:N |
| Masa berlaku | Lihat tanggal UTC/fingerprint pada riwayat, status waktu pada tabel | Sertifikat dalam masa berlaku tetap dapat revoked/disabled; admission adalah keputusan final |
| Alasan pencabutan | Pilih alasan lalu **Cabut akses & sertifikat** | Permintaan baru tanpa alasan ditolak. Pada `revoking`, gunakan **Ulangi workflow**; alasan pertama dipertahankan |
| Bundle onboarding | Klik **Unduh bundle onboarding** pada perangkat registered dengan binding akun | Memerlukan sertifikat masih valid dan tidak dicabut pada CRL terbaru; unduhan tidak memberi akses |

Kode alasan: `device_lost`, `suspected_compromise`, `retired`, `access_change`,
`test_cleanup`, `operator_request`. Alasan ini disimpan pada dashboard; reason code
OpenSSL/CRL tetap `cessationOfOperation`. Waktu `revoked_at` adalah penyelesaian
workflow dashboard, bukan timestamp deteksi daemon atau latensi pemutusan.

## Isi bundle

ZIP memuat tepat `device.crt`, `root.crt`, `manifest.json`, dan `README.txt`.
Manifest menyebut device ID, public key WireGuard, IP tunnel, username karyawan,
endpoint, fingerprint serta kewajiban admission. Tidak ada private key, password,
session token, seed TOTP atau konfigurasi peer statis yang menghindari admission.

Verifikasi ID/fingerprint melalui jalur tepercaya. Pasang `device.crt` di direktori
identitas client yang membuat request, mode 0600; key lokal lama harus cocok.
Jangan menimpa trust root hanya berdasarkan ZIP yang belum diverifikasi. Login
karyawan lalu jalankan layanan client seperti tutorial. CLI belum mengimpor manifest
secara otomatis. Koneksi utama CLI tetap khusus 10.8.0.2; identitas uji `.3` memakai
runner/namespace terpisah. Bundle bukan installer atau dukungan Windows.

## Migrasi, audit dan pengujian

Migrasi aditif pada `admin.db` membuat tabel `admin_audit` dan menambah
`devices.revocation_reason` serta `devices.revoked_at`. Device ID, sertifikat,
binding dan key dipertahankan. Record lama memiliki kolom tambahan null.
Audit menyimpan peristiwa dan field operasional terpilih, tanpa body request,
password, token, TOTP atau key. Aktor form berasal dari sesi terautentikasi;
skrip internal yang tidak memberi aktor tercatat `system`.

Backup konsisten sebelum upgrade tetap diperlukan. Paket 0.1.4 tidak menampilkan
fitur ini walaupun kolom tambahan masih ada; rollback tidak boleh mengembalikan
database/CRL lama atau dianggap mempertahankan seluruh bukti baru.

Uji otomatis mencakup migrasi berulang, kegagalan CA/server independen, CSRF/login,
aktor palsu, reason saat retry, CA-only revocation terhadap bundle, kerahasiaan ZIP
dan registrasi tanpa peer. Verifikasi HTTPS lab dapat diulang berurutan dengan
eksperimen identitas lain:

```bash
.venv/bin/python scripts/verify_admin_workflow.py state/lab/inventory.json \
  --state state/deployment/admin-ui-run-baru \
  --admin-onboarding state/deployment/admin-onboarding.json
```

Runner memakai kredensial lab privat dan TOTP, membuat akun/identitas sementara,
menguji form serta bundle, mencabut identitas dan menonaktifkan akun, lalu main
ping. Hasil `admin-workflow.json` harus COMPLETE dengan cleanup PASS. Jangan
menjalankan bersamaan dengan runner lain yang memakai 10.8.0.3. Hasil login otomatis
tidak mengonfirmasi bahwa pengguna sudah memasang authenticator pada HP pribadi.

Belum dicakup: renewal/rotasi sertifikat, notifikasi pemilik, kebijakan per-resource,
Windows dan histori beberapa sertifikat untuk device ID yang sama. Lihat
[matriks proposal](PROPOSAL_ALIGNMENT.md) dan [saran revisi](SARAN_REVISI_PROPOSAL_2026-10-12.md).
