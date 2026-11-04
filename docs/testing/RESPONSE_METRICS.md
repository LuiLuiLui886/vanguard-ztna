# MTTD dan MTTR untuk S-01

Proposal §1.2 dan §1.3 mendefinisikan **MTTR sebagai Mean Time to Respond**,
bukan recovery/repair. Batasan simulasi ancamannya adalah kebocoran kredensial
pengguna pada perangkat asing. Acuan dibaca ulang 9 Oktober 2026 melalui
[proposal asli](https://docs.google.com/document/d/1FWkmRWSUzfvPzLz1S2Bdxv2lCrgtB35IMzyWPZNX6BA/edit).
Catatan lama yang meminta eksperimen pemulihan layanan untuk mengukur MTTR
merupakan interpretasi yang dikoreksi; hasil lama tidak diubah menjadi MTTD/MTTR.

## Definisi operasional sebelum eksperimen

Unit observasi: satu POST `/api/verify` dari VM-ATTACKER setelah login karyawan
yang valid dan challenge sah, memakai sertifikat/public key salinan tetapi proof
dari private key yang berbeda. Identitas perangkat uji tidak pernah mendapat peer
dari permintaan penyerang. Sepuluh percobaan memakai challenge baru; tidak ada
pengulangan challenge, tebakan password massal, atau perubahan waktu node.

Tiga batas di proses server memakai `time.monotonic_ns()`:

1. **t0**: Flask menerima request pada `before_request`, sebelum JSON/validasi.
2. **td**: objek penolakan `Rejected` dibuat ketika pemeriksaan proof gagal.
3. **tr**: JSON respons penolakan sudah dibuat; audit kebijakan sebelumnya selesai.
   Titik ini diambil sebelum penyimpanan telemetry, finalisasi header HTTP dan
   pengiriman melalui Gunicorn/TLS/jaringan.

**MTTD aplikasi = mean(td − t0)**. **MTTR Respond aplikasi = mean(tr − td)**.
Mean(tr − t0) dicatat terpisah sebagai durasi total request sampai respons siap.
RTT attacker diukur pada satu jam monotonic attacker dari sebelum POST sampai
respons HTTP diterima. Tidak mengurangkan jam dari VM yang berbeda.

Definisi ini mengukur respons otomatis aplikasi terhadap request yang bisa diamati,
bukan waktu sejak password bocor, keputusan operator/SOC, atau deteksi semua jenis
insiden. Default-deny sudah mencegah akses sebelum respons dikirim; angka MTTR
bukan lama penyerang diberi akses. Waktu jaringan/TLS/antrian sebelum Flask dan
penyimpanan telemetry setelah tr tidak termasuk metrik server, tetapi tercakup
dalam RTT. Kebocoran password sebelumnya tidak diketahui waktunya.

## Instrumentasi 0.1.4

Server membuat ID korelasi acak sendiri pada challenge/verify dan mengembalikannya
sebagai `X-VanGuard-Request-ID`. Header dari pemanggil tidak dipercaya/dipakai ulang.
Audit `admission_timing` menyimpan endpoint, status, reason dan tiga durasi ns;
tidak menyimpan body, password, token sesi, sertifikat, signature atau nonce.
Response body dan enam pemeriksaan admission tetap sama.

Telemetry dicatat untuk penolakan aplikasi 400/403. Request sukses, endpoint
manajemen/login, 429 dan 503 tidak dihitung sebagai kejadian pada dataset ini.
Pembatasan tersebut menghindari penambahan log timing tanpa batas setelah throttle.
Skrip eksperimen hanya menerima status 403 dengan reason `proof_invalid`, tepat
sepuluh request ID unik dan durasi integer nonnegatif yang konsisten. Missing
audit, rate limit, kegagalan koneksi atau contoh parsial membuat eksperimen gagal;
tidak diganti dengan angka nol atau rata-rata sebagian.

## Pelaksanaan dan pemulihan

```bash
.venv/bin/python scripts/verify_response_metrics.py state/lab/inventory.json \
  --state state/deployment/response-metrics-baru
```

Prasyarat: server/client/attacker memakai 0.1.4, lab sehat, sesi main masih valid;
tidak ada eksperimen lain memakai 10.8.0.3. Script membuat akun dan sertifikat
sementara, menjalankan sepuluh proof salah dari attacker, menggabungkan audit
server menggunakan ID korelasi, lalu menunjukkan kontrol positif pada client sah.
Cleanup mencabut/disable identitas dan akun, serta memeriksa ping client utama.
Jangan mencabut identitas utama atau mengubah key server/CA.

`response-metrics.json` menyimpan tahap/status/nama identitas. Attacker juga
menyimpan sampel nonrahasia secara atomik setelah setiap request pada path
`attacker_output` di laporan. Jika SSH terputus, periksa file itu dan audit; hasil
RUNNING bukan PASS. Cleanup identitas yang tertinggal sebelum run baru. Gunakan
direktori hasil baru dan simpan run gagal tanpa menggabungkan sampelnya diam-diam.

Sajikan sepuluh nilai, mean, median, sample standard deviation, min/max dan RTT.
Tidak mengklaim perbaikan terhadap sistem lain tanpa dataset pembanding.
