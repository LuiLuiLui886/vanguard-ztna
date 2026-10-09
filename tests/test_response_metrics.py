import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_response_metrics import summarize


def samples():
    return [{'request_id': str(i), 'http_status': 403, 'reason': 'proof_invalid',
             'detect_ns': 2_000_000, 'respond_ns': 1_000_000, 'total_ns': 3_000_000,
             'attacker_rtt_ns': 20_000_000} for i in range(10)]


def test_response_metrics_keep_detection_response_and_rtt_separate():
    result = summarize(samples())
    assert result['MTTD_application']['mean_ms'] == 2
    assert result['MTTR_respond_application']['mean_ms'] == 1
    assert result['request_to_response_ready']['mean_ms'] == 3
    assert result['attacker_RTT']['mean_ms'] == 20


@pytest.mark.parametrize('change', ['duplicate', 'throttled', 'negative', 'nan', 'mismatch'])
def test_invalid_incident_evidence_cannot_be_reported(change):
    rows = samples()
    field, value = {'duplicate': ('request_id', '1'), 'throttled': ('http_status', 429),
                    'negative': ('detect_ns', -1), 'nan': ('respond_ns', float('nan')),
                    'mismatch': ('total_ns', 100)}[change]
    rows[0][field] = value
    with pytest.raises(ValueError):
        summarize(rows)
