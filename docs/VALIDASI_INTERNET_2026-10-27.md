# Validasi kandidat internet terkelola — 27 Oktober 2026

Ini laporan bukti, bukan manual kedua. Langkah operator berada pada Bab14.1
[manual admin tunggal](MODUL_PENGGUNAAN_VANGUARD.md). Source kandidat0.1.13 di
branch feature; ZIP stabil0.1.12 tidak otomatis berubah. Fixture sudah ditutup; hasil regresi akhir dicatat pada 28 Oktober. Rincian dan batas bukti di bawah.

## Scope dan pemisahan lingkungan

- Router pengguna, kernel/protokol WireGuard, CA utama dan identitas utama tetap.
- Windows10 LTSC2021 Evaluation x64 build19044 pada VM tambahan .100.70.
  Windows11 belum diuji untuk mode internet baru ini.
- Linux Ubuntu22.04 VM-SERVER: namespace `vanguard-internet-test` .100.80,
  interface wg0 terpisah, CA sementara, database/account/management token uji.
  Tidak menggunakan database registry atau CA produksi.
- TCP WAN terkontrol: namespace `vanguard-internet-wan` .100.81, alamat global
  **virtual**93.184.216.34/32 dengan route hanya dalam namespace gateway.
  Tidak menghubungi pemilik alamat global tersebut. TCP internet nyata menggunakan
 1.1.1.1:443 dan dilaporkan terpisah. DNS dipilih1.1.1.1 melalui tunnel.
- Backup offline disk Windows10/XML, endpoint ZIP dan policy firewall dipertahankan.
  State/runner/log mentah di `state/internet-20261027/` (diabaikan Git), credential
  hanya inventaris privat host dan staging ber-ACL privat dalam VM uji.

## Temuan yang direproduksi sebelum perbaikan

| ID / klasifikasi | File/fungsi, bukti | Dampak / prioritas | Perbaikan dan kriteria selesai |
|---|---|---|---|
| INTERNET-API-01 / Bug terbukti | server.internet_permission memakai validator field string; tes bool gagal | Admin tidak bisa memberi grant; P1 | Parse JSON lalu validasi bool eksplisit; API/CSRF/audit regresi PASS |
| WIN-INTERNET-01 / Bug terbukti | Internet-Lockdown preview: Python menerima p[schema], NameError di native stderr | Enable tidak berjalan; P1 | Kutip Python kompatibel PowerShell5; preview r4 PASS |
| WIN-INTERNET-02 / Bug terbukti | New-NetFirewallRule menolak InterfaceAlias untuk adaptor yang belum ada | Enable parsial/quarantine; P1 | Rule awal disabled, attach hanya sesudah admission/service nyata; enable PASS, attach end-to-end perlu bukti tersendiri |
| WIN-INTERNET-03 / Bug terbukti | IPv6 ::/0 ditolak native, rule IPv6 tidak terbentuk | Enable parsial/quarantine; P1 | Dua /1 per keluarga alamat; filter native diterima, enable/status PASS; jalur IPv6 nyata BELUM_TERUJI |
| INTERNET-STATUS-01 / Bug terbukti | Admission.listing memberi true untuk grant device sama, karyawan berbeda; regresi FAIL sebelum patch | Status admin menyesatkan; P2 | Cocokkan binding immutable dan tampilkan unknown untuk policy invalid; regresi PASS |
| WIN-INTERNET-PERF / Risiko desain terukur | status native sekitar79detik melampaui guard30detik | Renewal bisa cleanup karena timeout; P1 | Batch snapshot filter ActiveStore, digest sama; native r5 status5,09detik PASS. Renewal nyata masih diuji |
| INTERNET-BYPASS / Risiko desain | Trafik endpoint tanpa policy tidak melalui Linux; admin lokal dapat mengubah firewall | Jaminan internet universal tidak berlaku; P1 | Scope perangkat terkelola eksplisit, default block persisten, uji fallback; bukan remote attestation |
| INTERNET-AUTOLOGIN / Fitur belum tersedia | connect tetap proses terminal dengan renewal | Reboot memerlukan login/connect lagi | Tidak klaim layanan auto-login/always-on; pemblokiran berdiri sendiri di firewall |
| INTERNET-NATIVE-OTHER / Perilaku belum diuji | Windows11, Home/Pro19045, PC fisik, Wi-Fi berpindah, GPO | Bukti LTSC tidak cukup untuk rollout luas; P1 | Uji native per target setelah backup, jangan mengisi PASS dari mock |

## Bukti aktual

| Pengujian | Lingkungan/metode | Hasil |
|---|---|---|
| Baseline terkait endpoint/resource/platform | Linux lokal |69PASS/1SKIP56,23detik |
| Suite luas kandidat awal | Linux lokal, termasuk mock OS/WG pada unit tertentu |280PASS/1SKIP659,17detik |
| Regresi terbaru backend/status/admin/profil/paket | Linux lokal |117PASS/1SKIP319,97detik; tidak dijumlahkan dengan suite luas |
| Suite fokus final r8 (hasil dibaca 28 Oktober) | Linux lokal/mock OS |120PASS/1SKIP348,18detik; admin/paket/profil/internet/platform |
| Ruff dan diff whitespace | Source |PASS |
| Sintaks nft gateway + HTTPS dan WAN TCP | VM Linux namespace nyata |PASS; belum bukti trafik Windows |
| Install kandidat r1/r3 | Windows10 native BAT offline |PASS; instalasi bukan bukti admission/internet |
| Phase1 r4 sebelum identitas | Windows10 native, firewall/real TCP |7PASS: baseline, preview, enable, status, internet blocked, API reachable, identity absent |
| Status batch r5 memakai state r4 | Windows10 native |exit0,5,09detik; digest tetap cocok |
| Recovery policy setelah r2 dan r3 gagal | Windows10 native task admin |exit0, state aktif hilang, backup historis tersimpan; baseline TCP retry PASS |
| Reboot r7, policy schema2 | Windows10 native |6PASS setelah last boot berubah; termasuk blok TCP, bootstrap dan local-allow injection |
| Phase1 r7 Local GPO | Windows10 native |9PASS, termasuk local allow tambahan tidak membuka TCP internet |
| Regresi platform+internet schema2 | Linux lokal/mock OS |46PASS/1SKIP115,28detik |
| Admission/handshake + grant default-deny | Windows10 → gateway namespace |PASS; registrasi/login tanpa peer, tanpa grant TCP/DNS ditolak, grant membuka TCP dan DNS baru |
| Renewal | Native Windows10 |8ACCEPT tercatat: koneksi awal+7renewal; interval sekitar33–42detik |
| Cabut izin internet saat TCP aktif | Native Windows10, controlled WAN stream |PASS;211balasan, data berhenti; timeout teramati ≤2,4306detik termasuk overhead ukur; peer tetap ada |
| Logout dan cleanup | Native Windows10 |PASS; sesi/peer dicabut, service1060, config/marker/token dibersihkan oleh pemilik |
| Kegagalan fetch CRL | Fault injection gateway, native peer/nft/Windows |Peer removed ≤5,4001detik observasi; TCP/freshDNS gagal, cleanup PASS; bukan outage CA produksi |
| Reconnect setelah cleanup r8 | Native Windows10 |Dua koneksi/handshake baru, policy valid; koneksi kedua TCP+freshDNS PASS |
| Revocation OpenSSL nyata | CA sementara, native Windows10/Linux |Peer removed, TCP/freshDNS ditolak, cleanup PASS, fresh reconnect403 |
| TCP aktif saat revocation sertifikat | Native fixture |BELUM_TERKONFIRMASI: runner stream exit1, report tanpa status akhir; assertion FAIL dipertahankan |

Raw gagal r1/r2/r3 dipertahankan sebagai bukti regresi, tidak diganti laporan
sukses. Target uji awal memakai runtime r3 dengan patch policy yang terlacak. R8 menambah
detach rule sebelum adaptor dihapus, serta menolak state legacy untuk koneksi.
Paket r8 dibangun/verify manifest; hasil reinstall final harus dilihat di checkpoint.
`pytest` executable tanpa `python -m` sempat gagal collection karena root modul
scripts/deploy tidak ada di sys.path; runner yang benar digunakan untuk hasil
suite di atas. Kesalahan nama tabel pada tes tambahan dikoreksi lalu dites ulang.

## Koreksi setelah OS update/reboot

WIN-INTERNET-04 (P1): update Windows menambahkan5allow outbound lokal baru,
sebagian Enforced. Probe TCP Python masih gagal tetapi status menolak. Bukti ini
menunjukkan model PersistentStore saja belum cukup. Kandidat beralih ke Local
GPO milik sendiri dengan local rule merging disabled.89rule inbound aktif lama
disalin dengan nama milik VanGuard; asli dipertahankan. State schema2 menyimpan
snapshot profile/store dan kepemilikan untuk recovery; schema1 hanya recovery.
Domain/policy firewall GPO yang sudah ada ditolak. R6 sempat gagal karena cache
menghitung duplikasi quarantine dua store sebagai konflik; r7 menguji hanya
5rule final yang dihash sambil tetap menolak allow GPO asing. Recovery r6 selesai
sebelum retry. R7 kemudian9PASS dan6PASS sesudah reboot normal. Hasil r4/r5 tetap
historis, bukan bukti aman terhadap perubahan rule setelah update.

## Reconnect dan batas pengukuran TCP

WIN-INTERNET-05: setelah tunnel dihapus, Windows mengubah InterfaceAlias rule
menjadi ID numerik sehingga digest tidak cocok untuk reconnect. R8 menonaktifkan
pengecualian tunnel dan mengatur Any **sebelum** uninstall adaptor, menyimpan
hash baru. Hanya rule milik VanGuard yang direstriksi. Jika detach gagal, uninstall
masih diupayakan tetapi config/owner marker tetap untuk inspeksi. Regresi kegagalan
PASS Linux/mock OS; cleanup dan reconnect native r8 PASS. Private key tidak berubah.

Runner active TCP saat certificate revocation exit1, report berhenti pada37balasan
tanpa ended_at/error. Penyebab pencatat belum dibuktikan; jangan memakai38,91detik
polling gagal sebagai latency revocation. CA revoke/peer removal/probe deny dan
fresh-connect403 mempunyai bukti terpisah. DNS resolver bisa menjawab cache setelah
pemutusan; laporan membedakan dns_success cache dari dns_fresh_udp random-query.

## Batas dan kriteria penerapan

Sebelum rollout masih perlu melengkapi pengukuran TCP aktif saat pencabutan
sertifikat, expiry/daemon-stop native untuk mode baru, serta uji Windows11/fisik.
Bukti mode baru untuk authorized TCP/DNS, renewal, grant-removal, logout, fault
fetch CRL, reboot policy dan reconnect/cleanup tersedia seperti tabel di atas. Uji isolasi perangkat kedua, native Windows11 dan fisik
belum digantikan tes mock. Startup/maintenance/recovery harus menjaga akses
console; task recovery berwaktu pada lab **bukan fitur produk**. Jangan restore
CA/index/CRL lama, menebak counter, menambah peer manual atau menghapus config
sebelum kepemilikan/penghentian tunnel terkonfirmasi.

## Penutupan fixture dan paket lokal

Reinstall final r8 Windows10 exit0;4file identitas hash-identik dan policy script
terpasang cocok paket. Recovery admin memverifikasi tiga profile cocok snapshot dan89inbound rule
asli tetap enabled, Local GPO rule0, state
lockdown tidak ada dan TCPinternet biasa berhasil setelah recovery eksplisit.
Akun/identitas disposable disabled, serial dicabut, grant/peer kosong. Namespace
gateway/WAN serta unit transient dihentikan; CA/DB/CRL/backup dipertahankan.
Firewall root server identik secara aturan; hanya counter trafik berbeda.
Paket r8 lokal tidak menggantikan ZIP stabil GitHub. Main belum di-rollout.
Readiness spesifik gate internet, native expiry/daemon-stop/active-reboot mode
baru, Windows11 dan endpoint fisik tetap pekerjaan tersisa.
