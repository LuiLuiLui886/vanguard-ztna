# Penyelarasan VanGuard terhadap proposal

Acuan: [proposal TA Louis Andreas](https://docs.google.com/document/d/1FWkmRWSUzfvPzLz1S2Bdxv2lCrgtB35IMzyWPZNX6BA/edit),
dibaca ulang 12 Oktober 2026. Pengguna menetapkan kesesuaian proposal sebagai tujuan
pekerjaan berikutnya. Status tabel ini adalah hasil audit implementasi dan bukti,
bukan pernyataan bahwa seluruh proposal telah selesai.

Audit per bagian dan contoh redaksi tersedia pada
[saran revisi proposal](SARAN_REVISI_PROPOSAL_2026-10-12.md). Proposal Google Docs
tidak ditimpa. Perubahan aplikasi 0.1.5 dan bukti terbaru dicatat pada
[jurnal 12 Oktober](PROGRESS_2026-10-12.md); bukti 0.1.3/0.1.4 tetap historis.

## Matriks kebutuhan

| Acuan | Kebutuhan | Status audit 12 Oktober dan pekerjaan berikutnya |
|---|---|---|
| §1.2–1.3, §3.1 | Client, server gateway, CA, dashboard; simulasi manufaktur | Empat komponen pada empat VM + VM attacker tersedia. Kolom departemen/pemilik tersedia sejak 0.1.3; data organisasi nyata belum diisi. |
| §1.2 | WireGuard tanpa perubahan source/kernel | Sesuai. Admission HTTPS terpisah mendahului handshake standar. |
| §1.2, §3.2.3 | Single-tier private CA, tanpa IdP/SSO eksternal | Sesuai: OpenSSL CA internal. Aplikasi TOTP bukan IdP/SSO. |
| §1.2, §3.3.1 | X.509 terikat public key WireGuard | Sesuai, ditambah proof-of-possession dan challenge sekali pakai. |
| §1.2–1.3 | PEP/IEP, default-deny, mikrosegmentasi | Firewall dan admission tersedia. Perlu pemetaan kebijakan/resource dan bukti isolasi skenario manufaktur; jangan mengklaim segmentasi aplikasi/departemen dari firewall host saja. |
| §3.2.1 | Client Python Linux dan Windows | Ubuntu 22.04 teruji. 15 Oktober: Windows tambahan terpasang; 23 tes native lulus, enrollment tanpa peer, login/sesi invalid/PoP invalid, admission, handshake, ping, admission ulang, cleanup dan coexistence dengan Ubuntu terverifikasi. Revocation Windows, renewal otomatis jangka panjang dan reboot saat tunnel aktif masih belum diuji; lihat WINDOWS_CLIENT.md. |
| §3.3.2 | Login admin 2FA | Ada, tes TOTP/CSRF/replay lulus; onboarding HP pribadi belum dikonfirmasi. |
| §3.3.2 | Nama, departemen, pemilik, platform | Implementasi 0.1.3 terpasang; validasi/edit dan kompatibilitas data lama lulus suite lokal/guest/CI. Metadata bukan bukti kondisi/attestation perangkat. |
| §3.3.2 | Health check CA, issuance, sinkronisasi, audit | 0.1.5: health CA sebelum issuance; status HTTPS CA/server terpisah, audit admin aktor/waktu/peristiwa, workflow retry idempotent. Liveness bukan jaminan CRL atau tunnel sah. |
| §3.3.2 | Provisioning bundle dan notifikasi endpoint | 0.1.5: ZIP sertifikat/root publik, manifest binding dan petunjuk; bukan private key atau wg0.conf siap bypass. CLI belum auto-import manifest; notifikasi pemilik/endpoint belum tersedia. |
| §3.3.3 | Revocation aktif, log dan notifikasi | CA revoke + disable/daemon, audit dan alasan bisnis tersedia. S-04 berulang 10/10 adalah bukti 0.1.3 untuk ICMP. Notifikasi pemilik dan pemutusan sesi TCP/aplikasi belum diuji. |
| §3.4 | Riwayat sertifikat per perangkat dan alasan pencabutan | 0.1.5: periode/fingerprint sertifikat, riwayat aktivitas per identitas, alasan dan waktu workflow revoke selesai. Satu sertifikat per identitas; belum renewal atau histori 1:N. Audit lama tidak direkonstruksi; reason CRL tetap cessationOfOperation. |
| §3.5.1, F-01–F-06 | Sah, asing, revoked, expired, revoke aktif, registrasi | Bukti fungsi dan lab tersedia. Expired terutama fixture. S-04 membuktikan dua tunnel pada VM-CLIENT yang sama dengan namespace sementara, belum dua mesin client independen. |
| §3.5.2 | Tanpa VPN / WireGuard / VanGuard, masing-masing 10 kali | Runner dan cleanup tersedia; pilot pertama 10 Oktober FAIL pada parser UDP, cleanup PASS. [Pilot ulang clear/VanGuard 12 Oktober](BENCHMARK_PILOT_2026-10-12.md) PASS, n=1 per kondisi. Seri formal tiga × 10 belum dilakukan; pengecualian admission khusus baseline masih diperlukan. |
| §3.5.2 | Throughput, latency, jitter, CPU | Runner memisahkan TCP goodput, RTT ping, UDP jitter/loss dan CPU server. Counter goodput UDP iperf 3.9 yang kosong dilabel tidak tersedia, bukan direkayasa. Belum ada dataset tiga kondisi lengkap. |
| S-01 | Kredensial valid, perangkat asing | PASS pada VM-ATTACKER 9 Oktober: login akun karyawan valid berhasil, sertifikat tidak ada/binding salah/proof dengan key berbeda/replay ditolak tanpa peer baru. Kontrol positif perangkat sah, disable akun dan cleanup PASS. Bukti pada laporan 0.1.3; bukan jaminan pengikatan hardware. |
| S-02 | Sertifikat revoked dipakai kembali | Sudah diuji pada fixture dan identitas lab sementara. Berbeda dengan replay challenge yang juga diuji. |
| S-03 | Penyadapan lalu lintas tunnel | PASS 3/3: marker ada pada 20 paket kontrol wg0 per putaran, tidak ada pada 20 paket underlay eth0; nol kernel drop. Capture jalur client, bukan MITM attacker atau bukti kriptografi formal. [Hasil](SECURITY_RESULTS_2026-10-09.md). |
| S-04 | Sesi terputus <60 detik sesudah revoke | PASS 10/10 untuk ICMP: CA-only revoke, peer hilang dengan audit, 25 probe tanpa reply, readmission 403. Batas atas termasuk SSH/konfirmasi 7,351–12,737 detik. Belum penutupan sesi TCP/aplikasi atau timestamp deteksi internal. [Hasil](SECURITY_RESULTS_2026-10-09.md). |
| §1.2–1.3 | MTTD dan MTTR | Proposal menyebut MTTR **Respond** untuk akun valid pada perangkat asing. 0.1.4: 10 percobaan S-01 dengan proof key salah, mean MTTD aplikasi 69,649 ms dan MTTR Respond aplikasi 19,383 ms. Timestamp satu jam monotonic server; bukan onset kebocoran, RTT atau recovery. [Definisi](RESPONSE_METRICS.md). |

## Keputusan arsitektur yang harus diselaraskan

Proposal §1.2 melarang perubahan kernel, tetapi §3.3.1/§3.3.4 menggambarkan
sertifikat berada dalam handshake WireGuard. Implementasi memakai admission HTTPS
sebelum aktivasi peer; pertukaran kunci sesi tetap protokol WireGuard standar.
Ini bukan implementasi ekstensi AKE pada pesan WireGuard.

Proposal §3.3.2 menyebut peer aktif saat registrasi dan bundle berisi private key.
Instruksi proyek terbaru menetapkan registry-only sampai admission enam pemeriksaan,
dengan key independen dibuat di client. Pertahankan aturan tersebut sampai ada
keputusan eksplisit atas konflik; jangan mengubah protokol atau mengendurkan admission
hanya untuk mencocokkan uraian yang saling bertentangan.

Baseline WireGuard murni memerlukan peer yang disiapkan tanpa admission VanGuard.
Karena itu belum boleh dieksekusi pada lab saat ini. Sebelum meminta keputusan,
siapkan rencana berisi isolasi tes, backup, durasi, pemulihan konfigurasi dan bukti
bahwa kelima node serta identitas utama tetap dipertahankan.

## Urutan pekerjaan

1. Selesai: metadata dashboard, validasi dan kompatibilitas data lama (0.1.3).
2. Selesai: akun karyawan, rollout lima VM dan bukti S-01 live (9 Oktober).
3. Selesai: S-03/S-04 untuk ICMP dan metrik deteksi/Respond aplikasi S-01 (0.1.4).
   Cakupan SOC/kejadian kebocoran awal, recovery dan sesi TCP/aplikasi belum diukur.
4. [Protokol dan runner benchmark](BENCHMARK_PLAN.md) tersedia; lengkapi pilot
   sebelum seri tiga konfigurasi × 10. Pengecualian baseline WG belum diberikan.
5. 0.1.5 memperbaiki health/audit/reason/validity/bundle publik; lanjutkan renewal
   sertifikat, notifikasi pemilik serta keputusan cakupan Windows dan kebijakan
   resource. Jangan mengarang departemen/pemilik nyata.
6. Rekonsiliasi setiap baris dengan hasil aktual, lalu susun evaluasi TA.

Klaim penurunan insiden, throughput tanpa overhead, autentikasi perangkat fisik
yang tidak bisa dikloning, dan superioritas terhadap produk lain belum dibuktikan.
Kepemilikan private key membuktikan identitas kriptografis; salinan seluruh key
di perangkat lain tetap berada di luar jaminan pengikatan hardware.
