# Protokol S-03 dan S-04 — 9 Oktober 2026

Tujuan: melengkapi bukti proposal pada lab Ubuntu 22.04 yang sama, tanpa perubahan
aplikasi 0.1.3 atau protokol WireGuard. Tidak menjalankan benchmark baseline tanpa
admission. Rencana ditulis sebelum pilot; hasil aktual dicatat terpisah.

## S-03: observasi ciphertext dengan kontrol positif

Tiga pengulangan memakai tunnel utama yang telah lolos admission. Pada VM-CLIENT,
tcpdump merekam bersamaan interface underlay (hasil `ip route get`) untuk UDP
host server/port 51820 dan wg0 untuk ICMP antara 10.8.0.2 dan 10.8.0.1. Setelah
kedua capture siap, kirim 10 echo-request, interval 0,1 detik, payload 96 byte,
dengan pola acak 16 byte yang sengaja bukan data pengguna.

Syarat lulus per pengulangan: ping berhasil, capture utuh tanpa kernel drop,
minimal 20 paket pada kedua capture, marker ada di 20 paket kontrol plaintext
(request/reply), dan tidak ditemukan pada paket underlay. Parser menolak pcap
terpotong; marker pada header file tidak dihitung. Capture mentah/log disimpan
privat dengan checksum; ringkasan nonrahasia tersedia untuk GitHub/TA.

Hasil hanya menunjukkan marker uji tidak tampak pada capture underlay yang
diamati. Tidak membuktikan kriptografi secara formal, tidak berarti metadata
IP/ukuran/timing tersembunyi, dan bukan pengujian man-in-the-middle VM-ATTACKER.
Pada switch virtual, capture di attacker biasa belum tentu melihat unicast client;
capture pada underlay client memberi observasi jalur yang diketahui membawa paket.

## S-04: revoke CA saat perangkat memiliki akses nyata

Pilot satu pengulangan harus valid sebelum seri 10 pengulangan. Setiap pengulangan
memakai akun dan identitas baru `s04-*` pada 10.8.0.3. Registrasi harus tanpa peer;
login karyawan dan admission sah mendahului aktivasi peer. Interface sementara
dibuat di namespace asal VM-CLIENT, lalu dipindahkan ke namespace terisolasi pada
VM yang sama. Hanya route 10.8.0.1/32 berada di namespace uji; route/interface utama
tidak diubah. Perilaku socket mengikuti [dokumentasi WireGuard network namespaces](https://www.wireguard.com/netns/).

Server mendapat satu izin ICMP sementara: interface wg0, sumber 10.8.0.3,
tujuan 10.8.0.1. Tidak ada izin TCP, forwarding atau bypass LAN. Timer systemd
180 detik disiapkan sebelum mutasi pada client/server untuk membersihkan resource
dengan nama/comment unik. Cleanup normal menghapus namespace, rule dan timer,
serta mencabut/disable identitas dan akun. Ruleset stateless sebelum/sesudah wajib
identik dan client utama harus tetap bisa ping. Lima VM tetap dipertahankan.

Setelah handshake, lima probe berturut-turut wajib menerima reply. Kirim revoke
**hanya ke CA**, sehingga penghapusan peer harus berasal dari daemon pembaca CRL,
bukan endpoint disable server. Probe sesudahnya mencari kombinasi kehilangan reply,
peer kernel hilang, dan audit `certificate_revoked`. Konfirmasi dengan 25 echo-request
berinterval 0,2 detik yang seluruhnya tidak menerima reply. Readmission wajib 403.
Ini menguji akses ICMP, belum mengukur penutupan koneksi TCP/aplikasi manufaktur.

## Definisi waktu dan batas kesimpulan

- `t0`: monotonic workstation sebelum memanggil SSH admin untuk request revoke CA.
- `first_block_upper_seconds`: waktu dari t0 sampai probe gagal dan peer hilang
  pertama kali teramati dengan audit sebab pencabutan.
- `confirmed_block_upper_seconds`: waktu dari t0 sampai rangkaian 25 probe tanpa
  reply selesai. Semua pengulangan harus <60 detik.
- Angka tersebut adalah **batas atas waktu observasi**, termasuk SSH, request,
  polling, pembacaan audit dan konfirmasi. Tidak mengurangi overhead secara tebakan.
- Semua durasi memakai satu jam monotonic; timestamp UTC audit disimpan sebagai
  korelasi, tidak dikurangkan dengan jam VM lain. Sajikan tiap nilai, n, mean,
  median, min, max. Nilai bukan estimasi latensi deteksi daemon yang presisi.
- Audit 0.1.3 ditulis setelah peer dihapus. Eksperimen S-04 ini tidak memiliki
  timestamp deteksi/respons terpisah; **MTTD/MTTR pada dataset ini tetap null**.
  Koreksi acuan proposal: MTTR berarti Respond, bukan recovery. Pengukuran S-01
  terpisah pada 0.1.4 memakai [definisi aplikasi](RESPONSE_METRICS.md); jangan
  mengganti label batas atas S-04 dengan metrik tersebut.

## Menjalankan dan memulihkan

```bash
.venv/bin/python scripts/verify_security.py state/lab/inventory.json capture \
  --rounds 3 --state state/deployment/security-capture-baru
.venv/bin/python scripts/verify_security.py state/lab/inventory.json revocation \
  --rounds 1 --state state/deployment/security-pilot-baru
.venv/bin/python scripts/verify_security.py state/lab/inventory.json revocation \
  --rounds 10 --state state/deployment/security-series-baru
```

Gunakan direktori baru. Jangan jalankan paralel dengan uji identity/S-01 atau
gangguan lain; semuanya memakai 10.8.0.3. Hindari ping utama lain saat capture agar
kontrol positif tepat 20 paket. Semua langkah dan nama resource tersimpan atomik
pada `security-results.json`. RUNNING setelah proses mati bukan PASS. Timer tidak
mencabut sertifikat atau menonaktifkan akun; periksa device_id dan lakukan cleanup
identity menggunakan helper `Verification.cleanup_identity` sebelum menjalankan seri
baru. Jangan menghapus namespace/rule yang bukan milik run tersebut.

Jika cleanup gagal, periksa `rounds[].resources`, `watchdogs`, `cleanup.errors`
dan tahap terakhir. Config worker privat di lokasi `remote_tools`; aksi
`cleanup-client` / `cleanup-server` dengan config run dapat diulang idempotent.
Setelah pemulihan, ulang health/firewall dengan direktori baru. Jangan menghapus
bukti gagal atau menggabungkannya diam-diam dengan seri pengukuran yang lulus.
