# Protokol benchmark proposal

Implementasi runner/pilot dimulai 10 Oktober 2026. Status hasil aktual ada di
[checkpoint](CHECKPOINT.md) dan [jurnal](PROGRESS_2026-10-10.md); jangan menganggap
tersedianya runner sebagai keberhasilan seri formal.

Target §3.5.2: tanpa VPN, WireGuard standar tanpa validasi, dan VanGuard dengan
validasi aktif; masing-masing sepuluh pengulangan. Ukur throughput TCP (Mbps),
RTT ICMP (ms), jitter/loss UDP, serta utilisasi CPU **server**. iperf3 menghasilkan
throughput/jitter dan statistik endpoint; RTT memakai ping terpisah. Rujukan:
[manual resmi iperf3](https://software.es.net/iperf/invoking.html).
Flag diperiksa terhadap `iperf3 --help` dari paket Ubuntu 22.04 **iperf 3.9** yang
dipasang pada client/server 10 Oktober. Tidak ada daemon iperf persisten.

## Konfigurasi yang diusulkan

| Kondisi | Jalur data | Validasi |
|---|---|---|
| Clear | VM-CLIENT 192.168.100.30 → VM-SERVER 192.168.100.20 | Tidak membuat peer VPN; hanya port benchmark sementara |
| WG standar | Namespace sementara pada dua VM yang sama, peer/key uji saja | Tanpa validasi sertifikat; memerlukan pengecualian eksplisit aturan admission |
| VanGuard | Client uji 10.8.0.3 → server 10.8.0.1 pada wg0 | Akun sah dan enam pemeriksaan sebelum peer; renewal tetap aktif |

Tidak membuat VM keenam, mengubah kernel WireGuard, atau menimpa identitas utama.
WG standar memakai interface terpisah pada namespace server/client, socket pada
namespace asal, dan port UDP khusus 51821. Alamat 10.8.0.1/.3 di namespace uji tidak
mengubah route/alamat utama. Endpoint clear/WG/VanGuard menjalankan iperf3 dengan
versi, ukuran payload dan parameter yang sama.

## Urutan dan parameter praregistrasi

1. Backup privat config/source/state yang relevan; simpan ruleset stateless,
   daftar peer/route/interface, versi kernel/iperf3, vCPU/RAM/MTU serta beban idle.
   Pertahankan CA index/CRL terbaru saat pemulihan.
2. Pasang iperf3 dari paket Ubuntu pada client/server tanpa mengaktifkan daemon
   persisten. Jalankan server uji sebagai transient unit dengan RuntimeMaxSec.
3. Pilot tiap kondisi satu kali, terpisah dari dataset. Bila parameter harus
   berubah, dokumentasikan dan ulang pilot sebelum seri formal.
4. Sepuluh blok; urutan tiga kondisi diacak dengan seed yang direkam sehingga
   efek waktu/beban tidak selalu menguntungkan satu kondisi. Istirahat 5 detik
   sebelum pengukuran; tidak menjalankan pytest/CI guest atau eksperimen lain.
5. TCP: satu aliran, arah client→server, 10 detik ukur setelah 2 detik warmup.
   Gunakan receiver goodput, simpan sender/retransmit sebagai diagnosis terpisah.
6. UDP: satu aliran, payload 1200 byte, tawaran tetap 10 Mbps, durasi sama;
   jitter dan loss dari receiver. Ini bukan uji kapasitas maksimum UDP.
7. RTT: 30 echo-request berinterval 0,1 detik, payload 56 byte; simpan tiap summary
   dan loss. Label RTT, bukan latensi satu arah.
8. CPU server: delta `/proc/stat` pada envelope koneksi kontrol iperf dengan jam
   monotonic server, termasuk warmup dan finalisasi. Poll `/proc/net/tcp` setiap
   50 ms; awal memakai counter tepat sebelum koneksi pertama teramati, akhir
   setelah server one-off keluar. Simpan durasi dan gap polling maksimum;
   tolak window di luar 11,5–16 detik atau gap >0,5 detik. Window ini berbeda
   dari 10 detik throughput; tidak mengurangkan timestamp dua node. Tampilkan
   busy%, idle%, iowait%, steal% terpisah; guest sudah tercakup dalam user/nice.
   Counter turun membuat sampel tidak valid, termasuk iowait yang dapat turun
   menurut [dokumentasi kernel](https://docs.kernel.org/filesystems/proc.html).
   Utilisasi mencakup seluruh VM server dan overhead sampler, bukan proses iperf saja.
9. Simpan hasil mentah JSON/CSV, status per subtes, checksum dan semua kegagalan.
   Laporkan n/mean/median/sample SD/min/max. Analisis berpasangan antarblok;
   jangan menyimpulkan overhead nol hanya dari rata-rata yang mirip.

Topologi memakai VM pada satu workstation, bukan jaringan manufaktur nyata.
Pertahankan layanan utama sebagai beban latar yang sama pada ketiga kondisi;
laporkan bahwa baseline mengisolasi jalur data, bukan uninstall seluruh VanGuard.
CPU total tetap mencakup beban latar tersebut. Biaya login/admission diukur terpisah
dan tidak disamakan dengan overhead throughput setelah tunnel terbentuk.

## Batas mutasi dan pemulihan yang perlu ditinjau

- Target hanya VM-CLIENT dan VM-SERVER; CA/admin untuk enrollment VanGuard uji.
- Rule sementara clear: sumber .30, tujuan .20, port TCP/UDP 5201 dan ICMP saja.
  Rule tunnel: sumber 10.8.0.3, tujuan 10.8.0.1, interface wg0, TCP/UDP 5201.
  Rule WG standar: UDP 51821 hanya .30→.20; namespace tidak memiliki forwarding
  atau route ke resource lain. Tidak membuka akses dari attacker/LAN umum.
- Semua nama unit/interface/namespace/comment unik. Daftarkan cleanup timer
  **sebelum** rule/peer dibuat. Batas satu kondisi 120 detik; timer 180 detik;
  estimasi seri 30 kondisi sekitar 20–30 menit termasuk setup/cleanup.
- `finally` menghentikan iperf unit, menghapus namespace/interface/peer/rule uji
  miliknya, menonaktifkan identitas VanGuard sementara dan timer. Timer menjaga
  batas hidup resource jika proses host terputus. Identitas utama tetap berjalan.
- Setelah setiap kondisi cocokkan ruleset stateless dan pastikan main ping;
  setelah seri ulang firewall 40 pemeriksaan/health dan audit tidak ada resource uji.
- Jika waktu habis/host terputus: jangan menyebut subtes selesai; periksa checkpoint
  beserta unit/timer, bersihkan resource berdasarkan nama run, simpan hasil parsial.

## Batas otorisasi baseline

[AGENTS.md](../AGENTS.md) menyatakan: “A device must pass certificate admission
before becoming a live WireGuard peer.” Baseline WG standar sengaja tidak melakukan
validasi sertifikat, sehingga bertentangan dengan aturan itu meski terisolasi.
**Belum ada persetujuan pengecualian dan baseline belum dijalankan.** Permintaan
melanjutkan proyek/push umum tidak ditafsirkan sebagai perubahan aturan tersebut.

Sebelum pelaksanaan, siapkan runner dan cleanup untuk direview, validasi jalur clear/
VanGuard yang tetap sesuai aturan, lalu minta keputusan khusus untuk peer uji WG
standar dalam namespace/masa hidup di atas. Tanpa pengecualian, laporkan benchmark
tiga kondisi sebagai belum lengkap, bukan mengganti label salah satu kondisi.

## Runner dan pemulihan

```bash
.venv/bin/python scripts/verify_benchmark.py state/lab/inventory.json pilot \
  --state state/deployment/benchmark-pilot-baru --modes clear vanguard
```

Default hanya clear/VanGuard, satu blok pilot dengan urutan seed `20261010`.
`series` mensyaratkan ketiga kondisi dan sepuluh blok. WG standar ditolak tanpa
`--wg-exception-reference` yang mencatat persetujuan eksplisit operator; menulis
flag sendiri tidak memberikan otorisasi. Jalur tersebut belum boleh dieksekusi.

Worker guest tersimpan privat dengan nama run unik. Hasil host `benchmark-results.json`
dicatat setiap tahap; snapshot sebelum/sesudah, raw JSON iperf, counter CPU dan
output ping disimpan terpisah. File guest masih tersedia pada `resources.directory`
jika koneksi host terputus. `remote_tools` dan `watchdogs` merekam perintah cleanup:
worker `cleanup-client`/`cleanup-server` memakai config `<remote_tools>/<comment>.json`.
Timer admin memakai akun vanguard dan EnvironmentFile admin untuk mencabut identitas
serta menonaktifkan akun sementara; file config/worker admin dimiliki vanguard.

Timer 180 detik dipasang sebelum admission/rule. Unit iperf 45 detik, subprocess
client 30 detik, renewal 120 detik, dan host menolak kondisi yang melewati 120 detik.
Cleanup menghentikan unit sebelum menghapus namespace; namespace yang masih dipegang
proses membuat cleanup FAIL, bukan dilaporkan bersih. Firewall stateless, route,
daftar interface/namespace dibandingkan dengan snapshot; ping utama harus pulih.
Lease awal dan renewal baru harus terbukti pada kondisi VanGuard. MTU tunnel uji
ditetapkan 1420; clear memakai MTU underlay aktual yang direkam dalam snapshot.

Jika interrupted, jangan menimpa direktori hasil atau mengulang saat `.3` masih
reserved. Periksa hasil timer/JSON dan pulihkan resource run tersebut; jangan
menghapus namespace/peer identitas lain. Pilot tidak digabung ke seri formal.

## Kompatibilitas iperf 3.9

Pilot pertama 10 Oktober gagal pada validasi UDP; cleanup PASS. Raw JSON receiver
mencatat packets/jitter/loss, tetapi bytes dan bitrate bernilai nol setelah omit.
Runner sejak 12 Oktober mempertahankan jitter/loss receiver dan menandai goodput
UDP yang tidak tersedia sebagai `null` dengan alasan; tidak menghitungnya dari
jumlah packet atau menggantinya dengan sender goodput. Throughput utama proposal
tetap TCP receiver goodput dan tetap harus positif/konsisten. Simpan bukti gagal
asli pada `state/deployment/benchmark-2026-10-10/pilot-1/`.
