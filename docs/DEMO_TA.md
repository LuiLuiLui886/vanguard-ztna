# Panduan demo Tugas Akhir VanGuard

## Persiapan

1. Dari workstation, jalankan `bash scripts/open_dashboard.sh` untuk menyalakan
   lima VM yang sudah ada dan membuka dashboard.
2. Ikuti [aktivasi administrator](AKTIVASI_ADMIN.md) untuk TOTP di HP, lalu login
   ke `https://192.168.100.40:5000`.
3. Client memerlukan sesi akun karyawan sejak 0.1.3. Bila sesi delapan jam sudah
   habis, login ulang pada VM-CLIENT dan restart layanan sesuai
   [panduan akun karyawan](EMPLOYEE_ACCESS.md). TOTP admin tidak menggantikan login ini.
4. Periksa lab dengan direktori bukti baru:

```bash
.venv/bin/python scripts/health_lab.py state/lab/inventory.json \
  --state state/deployment/demo-health-baru
```

Hasil PASS berarti layanan, lease, binding peer dan ping teramati sehat. Bila
gagal, baca JSON hasil dan checkpoint sebelum menjalankan skenario lainnya.

## Urutan demonstrasi

| Langkah | Yang ditunjukkan | Penjelasan |
|---|---|---|
| Topologi | Lima VM dan peran CA/server/client/admin/attacker | Trust dan kontrol dibagi antar node |
| Identitas | Sertifikat X.509 dan public key WG di registry | Kunci X.509 berbeda dari kunci WireGuard |
| Akses sah | Akun karyawan, peer `10.8.0.2/32`, handshake dan ping | Sesi akun dan enam pemeriksaan perangkat wajib sah |
| S-01 | Akun valid pada perangkat attacker | Login berhasil; VPN tetap ditolak tanpa proof perangkat yang sah |
| Serangan negatif | Skrip attacker mendapat 401/403/400 | Endpoint terjangkau, identitas/permintaan tidak sah ditolak |
| Registrasi dan pencabutan | Uji identity sementara di bawah | Registrasi belum memberi akses; CRL mengakhiri akses |
| Lease dan gangguan CA | Bukti `operations-lease.json` dan laporan sebelumnya | Akses perlu renewal dan CRL yang valid |
| Audit dan recovery | Alasan removal serta log JSON tahap pengujian | Keputusan bisa ditelusuri dan pekerjaan bisa dilanjutkan |

Pada VM-CLIENT, jalankan `ping -c 3 10.8.0.1`. Pada VM-SERVER, gunakan
`sudo wg show wg0` untuk handshake/peer. Jangan gunakan format `dump` dalam laporan
karena memuat private key. Pada VM-ATTACKER:

```bash
/opt/vanguard/venv/bin/python /opt/vanguard/attacker_checks.py
```

Uji registrasi, proof, binding, replay, pencabutan CA dan cleanup bisa dijalankan
dari workstation dengan identitas sementara pada `10.8.0.3`:

```bash
.venv/bin/python scripts/verify_identity.py state/lab/inventory.json \
  --state state/deployment/demo-identity-baru
```

Skrip menggunakan client VM yang sudah ada, tanpa menambah node. Tidak ada tunnel
kedua; peer sementara ditambah hanya sesudah admission sah dan kemudian dicabut.
Client utama tetap memakai `10.8.0.2`. Jangan klik pencabutan `vm-client` untuk demo:
pencabutan terminal dan memerlukan identitas baru bila ingin reenrollment.

Demonstrasi S-01 memakai kredensial akun sementara yang valid pada VM-ATTACKER:

```bash
.venv/bin/python scripts/verify_employee.py state/lab/inventory.json \
  --state state/deployment/demo-s01-baru
```

Jalankan sesudah skrip identity selesai, bukan bersamaan. Hasil mencakup penolakan
perangkat asing, kontrol positif, disable akun, dan cleanup identitas sementara.

## Bukti laporan

Gunakan [laporan implementasi](IMPLEMENTATION_REPORT.md), hasil JUnit lokal/guest,
dan ringkasan JSON sesi. Sertakan hasil gagal/interupsi secara jujur bila terjadi.
File kredensial, QR/seed TOTP, private key, backup state dan env bukan lampiran TA.

Lease 300 detik dan reboot memutus akses sementara; bukti yang sudah tersedia bisa
dipakai tanpa mengulangi eksperimen saat demo. Jangan menjalankan uji gangguan saat
`health_lab.py` sedang mengamati stabilitas. Reboot workstation memerlukan jadwal
operator karena akan menutup alat dan sesi yang sedang digunakan.
