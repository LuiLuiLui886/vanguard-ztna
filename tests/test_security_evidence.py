import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from security_worker import identifiers, pcap_summary
from verify_security import summarize_bounds


def pcap(payload, endian='<'):
    magic = b'\xd4\xc3\xb2\xa1' if endian == '<' else b'\xa1\xb2\xc3\xd4'
    return (magic + struct.pack(endian + 'HHIIII', 2, 4, 0, 0, 65535, 1)
            + struct.pack(endian + 'IIII', 1, 0, len(payload), len(payload)) + payload)


@pytest.mark.parametrize('endian', ['<', '>'])
def test_capture_positive_control_and_ciphertext_distinguished(endian):
    marker = b'controlledmarker'
    positive = pcap_summary(pcap(b'icmp-' + marker + b'-payload', endian), marker)
    negative = pcap_summary(pcap(b'wireguard-encrypted-synthetic-packet', endian), marker)
    assert positive['packets'] == negative['packets'] == 1
    assert positive['marker_packets'] == 1 and negative['marker_packets'] == 0
    assert positive['sha256'] != negative['sha256']


@pytest.mark.parametrize('data', [b'', b'badheader' * 4,
                                pcap(b'payload')[:-1], pcap(b'payload') + b'partial'])
def test_incomplete_capture_cannot_pass(data):
    with pytest.raises(ValueError):
        pcap_summary(data, b'payload')


def test_marker_in_global_header_is_not_packet_evidence():
    assert pcap_summary(pcap(b'payload'), b'\xd4\xc3\xb2\xa1')['marker_packets'] == 0


def test_snaplen_truncation_rejected():
    data = pcap(b'packet')
    data = data[:36] + struct.pack('<I', 100) + data[40:]
    with pytest.raises(ValueError):
        pcap_summary(data, b'packet')


def test_cleanup_rejects_main_interface_and_shell_syntax():
    for identifier in ('wg0', 'VM-CLIENT', 'vgs12345678;id', '../wg0'):
        with pytest.raises(ValueError):
            identifiers(dict(namespace='vgs12345678', interface=identifier, comment='vgs12345678'))


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -1, 60])
def test_invalid_or_failing_latency_not_summarized(value):
    with pytest.raises(ValueError):
        summarize_bounds([{'status': 'PASS', 'confirmed_block_upper_seconds': value}])


def test_only_complete_bounds_are_summarized_without_inventing_mttd():
    rounds = [{'status': 'PASS', 'confirmed_block_upper_seconds': v} for v in (8, 10, 12)]
    result = summarize_bounds(rounds)
    assert result['n'] == 3 and result['mean_upper_seconds'] == 10
    assert result['MTTD'] is None and result['MTTR'] is None
    rounds[0]['status'] = 'RUNNING'
    with pytest.raises(ValueError):
        summarize_bounds(rounds)
