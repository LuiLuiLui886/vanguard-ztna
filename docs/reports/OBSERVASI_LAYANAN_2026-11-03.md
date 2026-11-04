# Observasi layanan dan kapasitas — 3 November 2026

Status: **PASS untuk observasi backend 10 menit**, bukan penerimaan seluruh sistem.

## Lingkup dan metode

CA terpasang 0.1.17; server/admin 0.1.15. Hanya ketiga VM layanan menyala.
Pemeriksaan HTTPS memakai trust root CA, tanpa mengabaikan validasi sertifikat.
Observer dijalankan di VM admin selama 600 detik, 60 siklus dengan interval target
10 detik: `/readyz` ketiga layanan setiap siklus dan `/healthz` setiap enam siklus.
Target 180 readiness + 30 liveness = 210 permintaan. Timeout koneksi 1 detik dan
baca 7 detik; maksimal tiga worker. Unit sementara dibatasi runtime 660 detik.
Observer menyimpan setiap siklus sehingga hasil parsial tetap dapat dilanjutkan.

Beban adalah daemon normal dan probe baca saja, tanpa enrollment, renewal client,
penerbitan sertifikat, atau workload endpoint tambahan dari harness. Pekerjaan
verifikasi dan pembersihan ISO selesai sebelum observasi yang benar dimulai.

## Temuan dan tindakan

| Klasifikasi | Lokasi dan bukti | Dampak / prioritas | Kriteria selesai / tindakan |
| --- | --- | --- | --- |
| Bug terbukti pada harness, bukan layanan | Observer awal host mendapat ConnectTimeout ke CA; `deploy/firewall.py` dan ruleset aktif mengizinkan CA TCP 8080 hanya dari server/admin | Hasil kesehatan keliru; P2 | Jalankan dari VM admin, simpan kegagalan awal; firewall tidak dilonggarkan |
| Risiko desain/operasional | Free space host 1.330.397.184 byte; salinan fragmen ISO 4.898.582.528 byte masih tertinggal | Ruang sempit untuk disk VM, backup dan log; P1 | Verifikasi data redundan, pulihkan ruang tanpa menghilangkan data unik; selesai terbatas, kapasitas tetap perlu dipantau |
| Perilaku belum diuji dalam sesi ini | Endpoint fisik, instalasi OS baru/UAC, koneksi Internet TCP persisten setelah revoke, beban panjang dan power loss fisik | Tidak dapat menyimpulkan kelayakan seluruh skenario; prioritas sesuai pengujian akhir | Tetap BELUM_TERUJI sampai ada bukti terpisah |

## Pemulihan ruang host

SHA-256 ISO Windows 10 utuh cocok manifest verifikasi lama:
`e4ab2e3535be5748252a8d5d57539a6e59be8d6726345ee10e7afd2cb89fefb5`.
Semua 21 fragmen cocok byte demi byte pada offset masing-masing; pemeriksaan
pemilik, tipe regular, metadata stabil, berkas terbuka dan referensi VM dilakukan
sebelum penghapusan. Definisi tujuh VM tidak berubah. ISO utuh tetap tersedia.

Sebanyak 4.898.582.528 byte (sekitar 4,90 GB / 4,56 GiB) salinan redundan dihapus.
Ruang bebas saat cleanup berubah dari 1.330.397.184 menjadi 6.229.037.056 byte.
Manifest offset, ukuran dan hash beserta prosedur rekonstruksi fragmen disimpan
lokal. Backup, seed privat, bukti lama dan disk VM tidak dihapus.

## Hasil observasi

Periode **2026-11-03T22:43:03.825511+07:00 sampai 2026-11-03T22:53:03.835511+07:00**, durasi aktual
600.01 detik, 60 siklus selesai. **210/210 HTTP 200**:
180 readiness dan 30 liveness. Tidak ada timeout atau respons gagal pada sampel
VM admin ini. `complete.json` menyatakan PASS. Unit sementara tidak lagi
tersedia setelah boot berikutnya, sehingga exit status historis tidak disimpulkan
dari nilai default `systemctl show` untuk unit not-found. Ketiga layanan dan
daemon server terverifikasi active pada 4 November. Angka ini tidak menjadi SLA atau bukti ketahanan semua beban.

Latensi permintaan dalam detik; persentil memakai nearest rank pada sampel:

| Layanan | Endpoint | HTTP 200 | p50 | p95 | Maksimum |
| --- | --- | ---: | ---: | ---: | ---: |
| ca | `/readyz` | 60/60 | 1.112 | 2.311 | 2.682 |
| ca | `/healthz` | 10/10 | 0.018 | 0.021 | 0.021 |
| server | `/readyz` | 60/60 | 1.355 | 2.312 | 2.728 |
| server | `/healthz` | 10/10 | 0.009 | 0.012 | 0.012 |
| admin | `/readyz` | 60/60 | 1.427 | 2.334 | 2.722 |
| admin | `/healthz` | 10/10 | 0.009 | 0.013 | 0.013 |

Bukti privat `state/stability-20261103-2238/`: hasil benar di `vm-admin/`,
ringkasan `summary.json`, checksum hasil `observation-sha256.json`. Sampel host
salah asal tetap di akar folder bersama `interrupted.json`; tidak ditimpa.

## Penyimpanan dan kesiapan desktop

Metrik awal diambil 3 November sekitar 22:41 WIB, metrik akhir baru diambil
4 November sekitar 12:31 WIB setelah melanjutkan sesi dan boot VM. Selisihnya
mencakup jeda serta boot; jangan mengatribusikannya hanya ke observasi 10 menit.
Ukuran journal di bawah menjumlahkan file `*.journal`, bukan jumlah entri log;
ukuran tetap tidak berarti tidak ada penulisan log.

| VM | DB sebelum → sesudah (byte) | Audit sebelum → sesudah | Journal sebelum → sesudah (byte) |
| --- | ---: | ---: | ---: |
| ca | Tidak memakai DB ini | — | 58720256 → 67108864 |
| server | 323584 → 323584 | 1285 → 1285 | 67108864 → 67108864 |
| admin | 196608 → 196608 | 169 → 169 | 75497472 → 83886080 |

SQLite server dan admin lulus `PRAGMA integrity_check` (`ok`) dalam mode baca.
Jumlah audit dan timestamp tertua dibandingkan; tidak ada penghapusan audit oleh
pekerjaan ini. Kesamaan jumlah bukan bukti kriptografis semua isi baris.
Pada 4 November, AT-SPI mengonfirmasi tiga console VM dan jendela terminal SSH
tampil. Prompt CA/server terbaca; judul terminal admin menunjukkan host yang
benar dan `who` mengonfirmasi sesi SSH dengan shell bash aktif. Tidak ada penggantian password atau autologin.
Empat VM lain tetap mati; seluruh tujuh definisi VM dipertahankan.

## Pekerjaan berikutnya

- Pantau kapasitas host; sekitar 5,4 GiB pada 4 November masih terbatas untuk pertumbuhan disk VM.
- Uji beban lebih lama dengan endpoint aktif dan renewal, setelah kapasitas memadai.
- Lanjutkan pengujian fisik LAN/Wi-Fi ketika perangkat tersedia; jangan menyamakan
  observasi backend ini dengan Windows native, fresh OS, UAC atau uji daya putus.
- Jangan ulang rollout CA atau cleanup fragmen; keduanya sudah selesai. Gunakan
  checkpoint terbaru dan bukti tersimpan untuk melanjutkan.


Tidak ada perubahan kode aplikasi, password, identitas, histori pencabutan,
konfigurasi router atau firewall dalam tindak lanjut ini. Pengujian Linux terpilih
100 PASS dari perbaikan CA sebelumnya adalah bukti terpisah, bukan suite yang
baru dijalankan oleh observasi ini.

## Pemeriksaan ulang 4 November

Seluruh VM awalnya mati ketika sesi dilanjutkan. CA, server dan admin dinyalakan;
empat VM lain tetap mati. Pemeriksaan baru **30/30 HTTPS HTTP 200** setelah boot,
versi CA 0.1.17 dan server/admin 0.1.15 active. Bukti baru disimpan terpisah di
`state/resume-20261104-1230/`. Angka ini tidak dicampur dengan 210 pemeriksaan
kemarin. Tidak ada rollout atau pemulihan state CA yang diulang.
