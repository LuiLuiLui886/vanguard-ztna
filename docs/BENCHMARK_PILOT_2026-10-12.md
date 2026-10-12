# Pilot benchmark — 12 Oktober 2026

Pilot clear dan VanGuard **COMPLETE/PASS**, masing-masing satu sampel. Urutan
VanGuard lalu clear memakai seed 20261010. Cleanup kedua kondisi PASS, peer utama
tetap dapat ping. Ini validasi runner; seri proposal tiga konfigurasi × 10 belum
dilakukan. Baseline WireGuard tanpa admission belum dijalankan.

| Metrik | Clear | VanGuard |
|---|---:|---:|
| Sampel per kondisi | 1 | 1 |
| TCP receiver goodput (Mbps) | 70438,193 | 1559,483 |
| RTT rata-rata, 30 ping (ms) | 0,502 | 0,765 |
| Kehilangan ping | 0% | 0% |
| UDP jitter, offered load 10 Mbps (ms) | 0,056498 | 0,046127 |
| UDP packet loss | 0% | 0% |
| CPU server busy saat TCP | 96,816% | 97,951% |
| CPU server busy saat UDP | 1,046% | 9,806% |
| TCP retransmit pengirim | 0 | 57 |

TCP diukur sekitar 10 detik setelah warmup 2 detik. CPU seluruh VM dihitung dari
delta `/proc/stat`, dengan idle/iowait/steal terpisah, dalam envelope koneksi
kontrol sekitar 12,2 detik yang mencakup warmup dan finalisasi. CPU bukan pemakaian
proses daemon saja dan intervalnya lebih luas daripada interval TCP utama.

Angka clear 70,4 Gbps terjadi pada jaringan virtual dalam host yang sama; jangan
menyamakannya dengan kapasitas NIC fisik, internet atau jaringan manufaktur nyata.
CPU server mendekati penuh pada kedua kondisi TCP. Satu sampel tidak mendukung
kesimpulan statistik atau klaim overhead sertifikat; pembanding WG murni belum ada.

iperf3 3.9 melaporkan counter byte/rate UDP receiver kosong meskipun paket,
jitter dan loss valid. Goodput UDP disimpan `null` dengan alasan eksplisit; tidak
direkonstruksi dari jumlah paket atau diganti dengan rate sender. Metrik throughput
proposal menggunakan TCP. Pilot 10 Oktober gagal pada parser counter tersebut;
bukti kegagalan dan cleanup PASS dipertahankan, kemudian parser diperbaiki dan
regresi diuji sebelum pilot ulang ini.

Bukti lokal: `state/deployment/audit-2026-10-12/benchmark-pilot/benchmark-results.json`.
Pilot gagal sebelumnya: `state/deployment/benchmark-2026-10-10/pilot-1/`.
Runner: [verify_benchmark.py](../scripts/verify_benchmark.py),
[worker](../scripts/benchmark_worker.py), [rencana](BENCHMARK_PLAN.md).
Watchdog dan cleanup membatasi eksperimen, menghapus namespace/rule sementara,
menonaktifkan akun uji dan memeriksa tunnel utama. Status renewal `RUNNING` di
snapshot pengukuran adalah keadaan saat sampel diambil; cleanup akhir PASS
menegaskan proses eksperimen dihentikan.
