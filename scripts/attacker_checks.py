#!/usr/bin/env python3
"""Bounded negative checks against the authorized five-VM lab; no traffic flooding."""

import argparse

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trust", default="/etc/vanguard/root.crt")
    args = parser.parse_args()
    checks = [
        ("GET", "https://192.168.100.20:8081/api/devices", None, 401),
        (
            "POST",
            "https://192.168.100.20:8081/api/verify",
            {
                "challenge_id": "fabricated",
                "certificate": "fabricated",
                "wg_public_key": "fabricated",
                "signature": "fabricated",
            },
            403,
        ),
        (
            "POST",
            "https://192.168.100.20:8081/api/challenge",
            {"certificate": "fabricated", "wg_public_key": "fabricated"},
            400,
        ),
    ]
    failed = False
    for method, url, body, expected in checks:
        try:
            response = requests.request(
                method, url, json=body, verify=args.trust, timeout=10, allow_redirects=False
            )
            ok = response.status_code == expected
            print(
                f"{'PASS' if ok else 'FAIL'} {method} {url}: {response.status_code} (expected {expected})"
            )
        except requests.RequestException as exc:
            ok = False
            print(f"UNVERIFIED {url}: {type(exc).__name__}")
        failed |= not ok
    raise SystemExit(int(failed))


if __name__ == "__main__":
    main()
