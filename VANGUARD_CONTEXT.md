Register device
      ↓
CA certificate issued
      ↓
Store WG identity in registry
      ↓
Client /api/verify
      ↓
X.509 + CRL + proof-of-possession
      ↓
ACCEPT
      ↓
wg set peer
      ↓
WireGuard handshake

Operational decision — 8 October 2026:
CRL validation remains strict: lastUpdate <= actual validator time < nextUpdate.
If a freshly fetched, correctly signed CRL is ahead by at most one second, wait
once for that boundary and run all CRL checks again using actual local time.
Never accept it before lastUpdate, extend nextUpdate, or fall back to stale CRLs.
Larger clock skew and failed revalidation remain fail-closed. Recheck challenge
expiration after CRL/proof validation before adding a live peer.
