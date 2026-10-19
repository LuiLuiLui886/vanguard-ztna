#!/usr/bin/env python3
"""Run as root under unshare --net, never in the guest's primary namespace.

Real Linux TCP/nftables; veth named wg0 simulates tunnel ingress. This is NOT
evidence of a WireGuard handshake, certificate admission or Windows networking.
"""

import json
import os
import select
import socket
import subprocess
import sys
import threading
import time

from deploy.firewall import rules


def command(*args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, timeout=5, **kwargs)


CLIENT = '''import socket,sys
s=socket.socket();s.settimeout(1)
try:
 s.connect((sys.argv[1],int(sys.argv[2])))
 print('connected',flush=True)
 for line in sys.stdin:
  s.sendall(b'probe'); assert s.recv(5)==b'probe'
  print('echo',flush=True)
except (OSError,AssertionError): print('blocked',flush=True)
finally: s.close()
'''


def main():
    if os.geteuid() != 0 or os.readlink('/proc/self/ns/net') == os.readlink('/proc/1/ns/net'):
        raise SystemExit('Requires root inside a separate network namespace')
    child = subprocess.Popen(['unshare', '--net', 'sleep', '300'])
    processes = []
    try:
        for _ in range(100):
            if os.readlink(f'/proc/{child.pid}/ns/net') != os.readlink('/proc/self/ns/net'):
                break
            time.sleep(0.01)
        else:
            raise RuntimeError('Client namespace did not start')
        prefix = ['nsenter', '-t', str(child.pid), '-n']
        command('ip', 'link', 'set', 'lo', 'up')
        command(*prefix, 'ip', 'link', 'set', 'lo', 'up')
        for server, client, server_ip, client_ip in (
            ('wg0', 'test-client', '10.8.0.1/24', '10.8.0.2/24'),
            ('lan0', 'test-lan', '192.168.100.20/24', '192.168.100.30/24'),
        ):
            command('ip', 'link', 'add', server, 'type', 'veth', 'peer', 'name', client)
            command('ip', 'link', 'set', client, 'netns', str(child.pid))
            command('ip', 'address', 'add', server_ip, 'dev', server)
            command('ip', 'link', 'set', server, 'up')
            command(*prefix, 'ip', 'address', 'add', client_ip, 'dev', client)
            command(*prefix, 'ip', 'link', 'set', client, 'up')
        command('nft', '-f', '-', input=rules('server', '192.168.100.1', True, True).encode())
        def serve(port):
            listener = socket.socket()
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(('0.0.0.0', port))
            listener.listen()
            def echo(connection):
                with connection:
                    try:
                        while data := connection.recv(4096):
                            connection.sendall(data)
                    except OSError:
                        pass
            def accept():
                while True:
                    connection, _ = listener.accept()
                    threading.Thread(target=echo, args=(connection,), daemon=True).start()
            threading.Thread(target=accept, daemon=True).start()
            return listener
        listeners = [serve(8082), serve(8083)]
        def start(address='10.8.0.1', port=8082):
            process = subprocess.Popen([*prefix, sys.executable, '-u', '-c', CLIENT,
                                        address, str(port)], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, text=True)
            processes.append(process)
            return process
        def line(process):
            assert select.select([process.stdout], [], [], 3)[0], 'Client response timeout'
            return process.stdout.readline().strip()
        def grant(seconds):
            command('nft', '-f', '-', input=(
                'flush set inet vanguard application_access\n'
                'add element inet vanguard application_access { '
                f'10.8.0.2 . 10.8.0.1 . tcp . 8082 timeout {seconds}s }}\n').encode())
        assert line(start()) == 'blocked'
        grant(30)
        active = start()
        assert line(active) == 'connected'
        active.stdin.write('probe\n')
        active.stdin.flush()
        assert line(active) == 'echo'
        command('nft', 'flush', 'set', 'inet', 'vanguard', 'application_access')
        active.stdin.write('probe\n')
        active.stdin.flush()
        assert line(active) == 'blocked'
        grant(2)
        expiring = start()
        assert line(expiring) == 'connected'
        time.sleep(2.1)
        expiring.stdin.write('probe\n')
        expiring.stdin.flush()
        assert line(expiring) == 'blocked'
        grant(30)
        assert line(start(port=8083)) == 'blocked'
        assert line(start('192.168.100.20')) == 'blocked'
        command(*prefix, 'ip', 'route', 'add', '10.8.0.1/32', 'via', '192.168.100.20', 'dev', 'test-lan')
        assert line(start()) == 'blocked'
        print(json.dumps({'status': 'PASS', 'default_deny': True, 'granted_tcp_echo': True,
                          'active_tcp_after_grant_removal_blocked': True,
                          'active_tcp_after_timeout_blocked': True, 'other_port_denied': True,
                          'lan_address_denied': True, 'tunnel_address_via_lan_denied': True,
                          'wireguard_handshake_tested': False,
                          'nft_version': command('nft', '--version').stdout.decode().strip()}))
        for listener in listeners:
            listener.close()
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=3)
        child.kill()
        child.wait(timeout=3)


if __name__ == '__main__':
    main()
