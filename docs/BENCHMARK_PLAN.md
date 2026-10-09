# Rencana benchmark proposal — belum dieksekusi

Target §3.5.2: tanpa VPN, WireGuard standar tanpa validasi, dan VanGuard dengan
validasi aktif; masing-masing sepuluh pengulangan. Ukur throughput TCP (Mbps),
RTT ICMP (ms), jitter/loss UDP, serta utilisasi CPU **server**. iperf3 menghasilkan
throughput/jitter dan statistik endpoint; RTT memakai ping terpisah. Rujukan:
[manual resmi iperf3](https://software.es.net/iperf/invoking.html).
Flag akhir harus diperiksa terhadap versi paket Ubuntu 22.04 yang benar-benar
dipasang; iperf3 belum tersedia pada pemeriksaan 9 Oktober pukul 14:03.

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
8. CPU server: delta `/proc/stat` selama setiap transfer dengan jam monotonic;
   tampilkan busy%, iowait%, steal% terpisah, tidak menjumlahkan guest dua kali.
   Statistik CPU proses iperf3 saja tidak cukup untuk biaya kernel WireGuard.
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
