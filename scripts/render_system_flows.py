#!/usr/bin/env python3
"""Render the manual's current-system flowcharts as standalone offline SVGs."""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'docs/assets/flows'
COLORS = {'step': ('#edf5ff', '#245a8d'), 'ask': ('#fff4d6', '#946200'),
          'ok': ('#e3f5ea', '#246744'), 'stop': ('#fff0ed', '#a33e32')}


def draw(name, title, nodes, edges):
    height = 125 + 145 * (max(n[1] for n in nodes.values()) + 1)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="{height}" '
           f'viewBox="0 0 1060 {height}" role="img" aria-labelledby="title">',
           f'<title id="title">{escape(title)}</title>',
           '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" '
           'refY="5" orient="auto"><path d="M0,0 L9,5 L0,10" fill="#40576c"/></marker></defs>',
           f'<rect width="1060" height="{height}" fill="white"/>',
           f'<text x="40" y="38" font-family="sans-serif" font-size="23" '
           f'font-weight="bold" fill="#173d5a">{escape(title)}</text>']
    positions = {key: (70 + 560 * n[0], 85 + 145 * n[1]) for key, n in nodes.items()}
    for start, end, label in edges:
        x, y = positions[start]
        tx, ty = positions[end]
        if x == tx:
            points = [(x + 180, y + 100), (tx + 180, ty)]
            lx, ly = x + 85, y + 128
        elif y == ty:
            points = [(x + 360, y + 50), (tx, ty + 50)]
            lx, ly = x + 390, y + 40
        else:
            # Side branches return through the gap between rows.
            points = [(x + 180, y + 100), (x + 180, ty - 22),
                      (tx + 180, ty - 22), (tx + 180, ty)]
            lx, ly = min(x, tx) + 390, ty - 30
        coords = ' '.join(f'{a},{b}' for a, b in points)
        svg.append(f'<polyline points="{coords}" fill="none" stroke="#40576c" '
                   'stroke-width="2" marker-end="url(#arrow)"/>')
        if label:
            svg.append(f'<text x="{lx}" y="{ly}" font-family="sans-serif" '
                       f'font-size="15" fill="#273e52">{escape(label)}</text>')
    for key, (_, _, text, style) in nodes.items():
        x, y = positions[key]
        fill, stroke = COLORS[style]
        if style == 'ask':
            svg.append(f'<polygon points="{x+180},{y} {x+360},{y+50} '
                       f'{x+180},{y+100} {x},{y+50}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        else:
            svg.append(f'<rect x="{x}" y="{y}" width="360" height="100" rx="12" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        lines = text.split('|')
        top = y + 55 - (len(lines) - 1) * 10
        for i, line in enumerate(lines):
            svg.append(f'<text x="{x+180}" y="{top+i*20}" text-anchor="middle" '
                       f'font-family="sans-serif" font-size="16" fill="#162d40">{escape(line)}</text>')
    svg.append('</svg>')
    (OUT / (name + '.svg')).write_text('\n'.join(svg) + '\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    draw('01-backend', '1. Persiapan CA, server dan dashboard', {
        'a': (0, 0, 'Operator: inventaris, alamat, waktu|backup dan akses console', 'step'),
        'b': (0, 1, 'CA sudah ada?', 'ask'),
        'c': (0, 2, 'Instalasi BARU: buat Root CA privat|single-tier dan lindungi private key', 'step'),
        'd': (1, 1, 'Pakai CA dan histori yang ada|Periksa konsistensi; jangan init ulang', 'ok'),
        'e': (0, 3, 'Siapkan HTTPS, trust dan secret layanan|CA menerbitkan sertifikat dan CRL', 'step'),
        'f': (0, 4, 'Server: WireGuard, validator, daemon|firewall default-deny dan resource|Gateway internet bila mode terkelola', 'step'),
        'g': (0, 5, 'Dashboard: akun admin dan TOTP|Akun karyawan, binding, audit|CA/server diakses lewat API berizin', 'step'),
        'h': (0, 6, 'Dependensi siap?', 'ask'),
        'i': (1, 6, 'Perbaiki dependensi yang gagal|Status gagal/tidak diketahui|Jangan memberi akses lewat bypass', 'stop'),
        'j': (0, 7, 'Admin siapkan profil publik, root CA|alokasi perangkat/IP dan pin server|Lanjut diagram 2', 'ok'),
    }, [('a','b',''),('b','c','Tidak'),('b','d','Ya'),('c','e',''),('d','e',''),
        ('e','f',''),('f','g',''),('g','h',''),('h','i','Tidak'),('h','j','Ya')])
    draw('02-installer', '2. Paket admin sampai EXE pada endpoint', {
        'a': (0, 0, 'Admin distribusikan paket tepercaya|EXE umum atau EXE per perangkat|Periksa asal dan SHA256', 'step'),
        'b': (0, 1, 'User klik EXE dan setujui UAC|Wrapper verifikasi payload dan cache|Ekstraksi belum memasang policy', 'step'),
        'c': (0, 2, 'Paket per perangkat?', 'ask'),
        'd': (1, 2, 'EXE umum di GitHub: install runtime|Python, WireGuard dan aplikasi|Tidak mengaktifkan blok internet baru', 'step'),
        'e': (1, 3, 'Admin lanjut konfigurasi Bab11-12|atau bangun EXE per perangkat|dengan profil, root dan alokasi publik', 'step'),
        'f': (0, 3, 'Wizard memasang atau memakai ulang|runtime lengkap yang terverifikasi|Input lewat terminal; belum ada GUI', 'step'),
        'g': (0, 4, 'Validasi pin dan pasang profil|Konflik ditolak; key/config dipertahankan|Lanjut diagram 3', 'ok'),
        'h': (1, 5, 'Batal UAC / error sebelum policy:|belum mengaktifkan blok baru|Policy lama tidak otomatis dipulihkan', 'stop'),
        'i': (0, 5, 'Jika runtime meminta restart: kode3010|Restart manual, jalankan paket lagi|Belum berarti siap connect', 'step'),
    }, [('a','b',''),('b','c',''),('c','d','Tidak'),('d','e',''),('c','f','Ya'),('f','g','')])
    draw('03-enrollment', '3. Policy Windows dan pendaftaran perangkat', {
        'a': (0, 0, 'Profil terverifikasi', 'step'),
        'b': (0, 1, 'Schema2 terkelola?', 'ask'),
        'c': (0, 2, 'Aktifkan / periksa policy Windows|SETELAH BERHASIL: internet langsung|diblok; jalur kontrol terbatas tersedia', 'stop'),
        'd': (1, 1, 'Schema1: akses aplikasi internal|Tidak mengaktifkan lockdown internet', 'step'),
        'e': (0, 3, 'Endpoint membuat atau memakai key|X.509 dan WireGuard miliknya sendiri|Ekspor request PUBLIK', 'step'),
        'f': (0, 4, 'Admin login + TOTP di dashboard|Periksa request dan binding karyawan|CA yang ada menandatangani sertifikat', 'step'),
        'g': (0, 5, 'Bundle sudah tersedia?', 'ask'),
        'h': (1, 5, 'Menunggu admin: kode20|Jalankan paket lagi setelah disetujui|Lockdown yang aktif tetap berlaku', 'stop'),
        'i': (0, 6, 'Import bundle; cek kecocokan binding|Private key tetap di endpoint|Registrasi belum menambah peer', 'step'),
        'j': (0, 7, 'Siap login; lanjut diagram 4|Sertifikat yang sudah ada dicek ulang|/prepare-only berhenti tanpa connect', 'ok'),
    }, [('a','b',''),('b','c','Ya'),('b','d','Tidak'),('c','e',''),('d','e',''),
        ('e','f',''),('f','g',''),('g','h','Tidak'),('g','i','Ya'),('i','j','')])
    draw('04-access', '4. Login, admission dan izin lalu lintas', {
        'a': (0, 0, 'Karyawan login lewat HTTPS|Server memeriksa akun dan binding|Login saja belum menambah peer', 'step'),
        'b': (0, 1, 'Connect: challenge dan proof|Endpoint membuktikan kepemilikan key|Server memeriksa sesi karyawan', 'step'),
        'c': (0, 2, 'Enam cek: signature CA, masa berlaku,|CRL terkini, serial pencabutan,|proof key dan binding public key WG', 'step'),
        'd': (0, 3, 'Sesi dan semua cek lolos?', 'ask'),
        'e': (1, 3, 'Tolak admission / gagal tertutup|Tidak memberi peer/lease baru|Internet langsung tetap diblok di schema2', 'stop'),
        'f': (0, 4, 'Server memasang peer dan lease|Client membangun tunnel WireGuard|Periksa handshake dan konektivitas', 'step'),
        'g': (0, 5, 'Periksa kebijakan lalu lintas|Lease/sesi valid tetap diperlukan|Tunnel aktif bukan izin semua tujuan', 'step'),
        'h': (0, 6, 'Aplikasi internal: identitas + resource|protokol + port harus diizinkan|Tidak ada izin = tolak', 'step'),
        'i': (1, 6, 'Internet terkelola: gateway aktif|dan grant internet untuk identitas|Tanpa grant = tolak internet gateway', 'step'),
        'j': (0, 7, 'Trafik yang diizinkan dapat lewat|Renewal berkala; lanjut diagram 5|Lease renewal tidak memperpanjang cert', 'ok'),
    }, [('a','b',''),('b','c',''),('c','d',''),('d','e','Tidak'),('d','f','Ya'),
        ('f','g',''),('g','h','Aplikasi'),('g','i','Internet'),('h','j','Izin valid'),('i','j','Izin valid')])
    draw('05-lifecycle', '5. Penghentian akses, pemulihan dan audit', {
        'a': (0, 0, 'Koneksi aktif dan renewal berkala|Pantau sesi, lease, CA/CRL dan policy|Status gagal diperiksa = tidak diketahui', 'step'),
        'b': (0, 1, 'Admin revoke sertifikat|CA mencatat serial dan menerbitkan CRL|Server/daemon mencabut akses terkait', 'stop'),
        'c': (1, 1, 'Pemicu lain: logout, akun nonaktif,|lease/sesi habis atau renewal gagal|Scope pemutusan sesuai sesi/identitas', 'stop'),
        'd': (0, 2, 'Peer/izin terkait dihentikan|Akses baru ditolak sesuai policy|Tidak menjanjikan pemutusan nol detik', 'stop'),
        'e': (0, 3, 'Client menghentikan tunnel miliknya|Cleanup gagal: pertahankan config|Logout offline: server belum terkonfirmasi', 'step'),
        'f': (0, 4, 'Schema2: lockdown tetap aktif|Disconnect/reboot tidak otomatis|membuka kembali internet langsung', 'stop'),
        'g': (0, 5, 'Operator periksa penyebab dan state|Revoke perlu identitas pengganti sah|Koneksi baru wajib login/admission valid', 'step'),
        'h': (1, 5, 'Recovery policy oleh admin lokal|Pastikan ownership dan tunnel berhenti|Pulihkan backup policy secara terencana', 'step'),
        'i': (0, 6, 'Audit sepanjang proses: waktu, aktor,|aksi, hasil dan alasan yang aman|Arsip tanpa membuang bukti lama', 'ok'),
        'j': (1, 6, 'Rekam terpisah: registered, lease,|peer, handshake dan transfer|Jangan mencatat password/token/key', 'step'),
    }, [('a','b','Revoke'),('a','c','Pemicu lain'),('b','d',''),('c','d',''),
        ('d','e',''),('e','f',''),('f','g',''),('g','h','Recovery lokal'),('g','i',''),('h','j','')])


if __name__ == '__main__':
    main()
