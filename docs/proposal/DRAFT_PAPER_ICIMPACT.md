# Certificate-Based Access Control and Revocation for a Virtualized Digital Media Service Using WireGuard

**Working draft — 11 November 2026. Not ready for submission.** Author names and affiliations await confirmation. The digital media experiment and screenshots are pending; results below are explicitly historical platform evidence. Target: English, at most six pages including references. Final pagination has not been verified.

**Authors:** [Author names, affiliations, city, country, and email; apply the confirmed blind-review rules before submission.]

**Abstract—** Digital media services require access decisions that remain enforceable after a user authenticates. An encrypted tunnel alone does not express whether an employee session remains valid or whether a device certificate has been revoked. This paper presents VanGuard, a prototype that combines employee authentication, certificate-based device admission, and resource-specific authorization around an unmodified WireGuard tunnel. Before installing a live peer, an HTTPS admission service verifies certificate trust and validity, current revocation information, private-key possession, and the registered certificate-to-WireGuard-key binding. Time-limited leases and a reconciliation daemon enforce subsequent access withdrawal. We describe a virtual testbed and a planned evaluation using a controlled digital media download service. Existing platform experiments provide preliminary evidence of admission enforcement, application access control, and revocation, but do not yet establish media-specific performance. The evaluation separates new connection denial, interruption of an ongoing transfer, and peer removal, supported by timestamped logs and screenshots. The contribution is an implementation and evaluation approach for revocable access to a protected service, without changing WireGuard or claiming media-content authenticity.

**Keywords—** zero trust, access control, device certificates, WireGuard, revocation, digital media security

## I. Introduction

A digital media repository may distribute recordings, images, or other assets to authorized users across managed and unmanaged networks. A relevant security problem is continued access after a credential is stolen, a device becomes unauthorized, or an administrator withdraws permission. In this setting, successful login and network reachability should not independently imply permission to retrieve protected content.

Zero trust architecture separates access decisions from implicit trust in network location and considers both subjects and devices [1]. VanGuard applies this principle to a small, centrally administered testbed. It requires an employee session and cryptographic device authentication before activating a WireGuard peer. Resource policy then determines which application can be reached. The proposed media workload is a concrete service to evaluate these controls; it does not add an artificial intelligence model or a media-forensics algorithm.

This study asks three questions. RQ1: Can valid employee credentials authorize access when device authentication fails? RQ2: Does revocation stop new requests and ongoing authorized transfers, and with what observed delay? RQ3: Does the system preserve access restrictions when its authorization dependencies become unavailable?

The intended contributions are a documented admission and revocation design, an explicit threat model for a protected media service, and a reproducible evaluation linking access outcomes to control-plane events. The work does not claim a new cryptographic protocol, hardware-bound identity, or superiority over commercial zero trust products. This draft distinguishes implemented platform behavior from the media experiment that must be completed before submission.

## II. Background and Related Work

NIST SP 800-207 describes zero trust in terms of subjects, assets, resources, authentication, and authorization rather than privileged network location [1]. BeyondCorp illustrates the move away from a privileged enterprise intranet [2]. These sources motivate identity-oriented access control; they do not establish that this prototype satisfies every requirement of a complete enterprise zero trust deployment.

WireGuard associates peer public keys with tunnel addresses and provides encrypted network transport. Its design leaves public-key distribution to mechanisms outside the tunnel protocol [3]. VanGuard uses that separation: X.509 validation and employee-session checks occur over HTTPS before peer activation, while the WireGuard handshake remains unchanged. Certificate and CRL terminology follows the Internet X.509 profile [4]; an application must still decide how certificate status affects an existing authorization.

The scope of this work is the coordination between admission, application policy, and access withdrawal in a virtualized service. A broader comparison with recent certificate-based VPN and software-defined perimeter studies remains necessary before making a novelty claim. Access authentication must also be distinguished from content provenance: authorizing a download neither proves who created the media nor detects a manipulated recording.

## III. System Design and Threat Model

### A. Components and Trust Boundaries

The testbed contains five Ubuntu virtual machines: a certificate authority, a WireGuard gateway and admission server, an administrator dashboard, an authorized client, and an attacker client. The administrator approves registration and binds a device identity to an employee account. The client independently generates its X.509 and WireGuard private keys; registration transfers public material only. The CA signs certificates and maintains revocation state. Registration does not itself install a live peer.

The proposed media service will run behind the gateway's application policy, using the existing internal service endpoint at tunnel address 10.8.0.1 and TCP port 8082. It will serve non-sensitive, controlled test content. This service workload has not yet been deployed or evaluated. The client-facing policy must explicitly identify the authorized device, resource address, protocol, and port. Direct access through the virtual LAN will be included as a negative control.

[FIGURE 1 PLACEHOLDER: Draw the five-node architecture, management boundary, HTTPS admission path, WireGuard data path, and protected media service. Mark the media workload as planned until deployed. This is a design figure, not an experimental screenshot.]

### B. Admission and Authorization

An employee authenticates over HTTPS and receives a session associated with the device binding. A subsequent device challenge and proof must use the same valid session. The admission service checks the certificate signature against the trusted root, the validity period, the freshness and validity of the CRL, the certificate serial against revocation records, private-key proof-of-possession, and the certificate-to-WireGuard-public-key registry binding.

A successful decision authorizes a live WireGuard peer with its assigned tunnel address. A failed or indeterminate decision does not authorize a new peer. The challenge is single-use and expires; possession of a copied certificate without the corresponding private key is insufficient. After admission, the resource policy remains default-deny. A peer entry or a recent handshake is therefore not equivalent to permission to access every service.

### C. Access Withdrawal and Dependency Failure

The implementation uses leases of at most 300 seconds, capped by the employee-session expiry. Lease renewal repeats authorization checks and does not extend certificate validity. A daemon reconciles active peers against current access conditions. Its configured interval is five seconds after the preceding cycle completes, so this interval is not a guaranteed revocation latency. Dependency requests, scheduling, and enforcement operations contribute to the observed delay.

Invalid or unavailable revocation information causes access leases to be invalidated and peer removal to be attempted. The deployment also uses service supervision and tunnel shutdown on daemon termination. The resulting behavior must be observed at the application, not inferred solely from a healthy process indicator. Authenticated logout targets the supplied session and its owned access; an older session must not revoke access owned by a newer session.

### D. Adversary and Assumptions

The attacker controls a separate client VM and may possess valid employee credentials, a copied public certificate, or a previously observed challenge. The attacker does not initially possess the legitimate device's private keys and cannot administer the CA, gateway, hypervisor, or dashboard. The evaluation includes invalid proof, replay, revocation, and direct-path access attempts within the authorized lab.

The root trust anchor and initial profile distribution are assumed trustworthy. A compromise of the root CA or gateway administrator is outside the evaluated threat model. Copying both private keys and the complete client state is not prevented by cryptographic identity binding alone. The system does not provide deepfake detection, watermarking, storage encryption, or tamper-evident logging. Audit records support operational traceability but are not an immutable external ledger.

## IV. Experimental Method

### A. Versioning and Workload

The planned media evaluation will freeze the verified deployment combination: CA 0.1.17 and gateway, dashboard, and Ubuntu client 0.1.15. Before execution, the experiment record will include installed-source hashes, operating-system versions, host and guest resource allocations, time synchronization, and dependency readiness. Historical results from other releases remain separate datasets.

The media workload will use a versioned synthetic asset, with its size, SHA-256 digest, delivery rate, and server settings recorded. A sustained download will be long enough for revocation to occur during transfer. Counters at the receiver will distinguish application bytes already buffered from new network delivery. A digest comparison on a completed authorized download will check transfer correctness; it will not establish authorship or resistance to malicious content replacement.

### B. Scenarios and Controls

Table I defines the planned media-service experiments. Each scenario includes an authorized positive control and the relevant denied condition. Disposable test identities will be revoked or disabled during cleanup; primary identities and CA history will be preserved.

**TABLE I. MEDIA-SERVICE EVALUATION PLAN — NOT YET EXECUTED**

| Scenario | Required observation |
| --- | --- |
| Registration and login only | No live peer or protected media access before device admission |
| Valid device and account | Admission, explicit resource grant, and successful media download |
| Stolen credentials, invalid device proof | Denial, no attacker peer, and no protected media bytes |
| Revoked, expired, mismatched, or replayed identity evidence | Separate denied cases with correlated reasons and no new authorized access |
| Revocation during download | Timed access withdrawal, receiver-byte observations, and denied reconnection |
| Direct LAN path or unauthorized port | Application remains unreachable outside the authorized path/policy |
| Renewal, logout, and dependency failure | Scoped withdrawal and fail-closed behavior under the stated condition |

The target is at least ten independently initialized runs for the primary denial and revocation measurements. This is a collection plan, not an achieved sample count or a statistical power claim. Run order, background load, failed attempts, and timeouts will be retained. Results will report sample size and descriptive statistics rather than replacing missing measurements with zero.

### C. Timing and Evidence

For revocation, one observer will record the interval from its request initiation to the first observed access failure, with request acknowledgement recorded separately. This operational interval includes request transport and polling uncertainty; it is not the exact internal enforcement instant. The probe interval and timeout will be reported. Peer disappearance and application-transfer interruption will be measured separately. Timestamps from different VMs will not be subtracted to manufacture precise latency.

For application rejection timing, the existing instrumentation distinguishes request-handler entry, detection of an invalid proof, and completion of the denial response. These boundaries exclude network time outside the handler and do not measure time since credential theft. Any historical metric is labeled with its original release and definition.

Screenshots will show genuine client, gateway, and dashboard states from identifiable runs. Each selected image will be linked to timestamps, scenario identifiers, and retained logs. Secrets and personal information will be redacted in publication copies; original evidence will remain private. Screenshots illustrate observations, while logs and receiver counters support quantitative claims.

[FIGURE 2 PLACEHOLDER: Insert a genuine, readable multi-panel screenshot from one media run: authorized transfer, administrator revocation, and subsequent client denial. No screenshot has been supplied or generated for this draft.]

## V. Preliminary Evidence and Discussion

### A. Existing Platform Evidence

The available records establish preliminary behavior of the underlying platform, not the proposed media workload. The November 2–3 release record for version 0.1.15 documents successful HTTPS admission and WireGuard integration, denial without an application grant, access with an explicit TCP 8082 grant, and blocking of an active internal application TCP flow after grant withdrawal. A Linux CA-only revocation sample recorded peer removal after 6.828 seconds, blocking of the active test flow, and denial of readmission. That value is a single historical observation, not a mean or service-level guarantee.

Separate historical Windows tests used version 0.1.15 on Windows 10 build 19044 and Windows 11 build 26300. The records contain 122 and 98 probes, respectively, covering managed Internet access transitions, renewals, and revocation. These counts are individual probe observations, not independent replicated experiments. Recorded peer-removal times were 10.056 and 4.359 seconds, each from one revocation sample. They do not establish a controlled performance difference between Windows versions.

**TABLE II. HISTORICAL PLATFORM OBSERVATIONS — NOT MEDIA RESULTS**

| Environment and release | Recorded observation | Interpretation limit |
| --- | --- | --- |
| Linux integration, 0.1.15 | Resource allow/deny and active internal TCP blocking; peer removal 6.828 s in one CA-only revoke sample | Generic application fixture; one timing sample |
| Windows 10 build 19044, 0.1.15 | 122 probes; peer removal 10.056 s in one sample | New Internet connection probes; no ongoing media-transfer test |
| Windows 11 build 26300, 0.1.15 | 98 probes; peer removal 4.359 s in one sample | Different environment; not a paired OS comparison |

The Windows experiments invoked installed client APIs directly and do not prove a complete interactive installer workflow on a fresh physical machine. The Windows guests have subsequently been retired; their retained evidence must not be presented as a new run. These observations motivate the controlled media experiment but cannot substitute for it.

### B. Pending Media Results

[RESULTS PENDING: Add the completed Table I outcomes, the number of independent runs, transfer-interruption measurements, timing distributions, and the screenshot run identifiers. Update the abstract and conclusion only after these observations have been verified.]

No measured media throughput, download-interruption distribution, media-service bypass outcome, or content-integrity result is available in this draft. No numerical improvement over plain WireGuard or another access-control system is claimed. Before submission, the new dataset must show whether the controls continue to work during the actual workload, including transfers already in progress.

### C. Interpretation

The distinction between registration, admission, and resource permission is central to the design. A user can be registered and authenticated without receiving a live tunnel peer; a live peer can remain unable to reach a resource without a grant. Similarly, removing an authorization should be evaluated through both the control state and attempted data transfer. A dashboard label alone cannot demonstrate that active traffic has stopped.

The preliminary observations support the feasibility of enforcing these transitions in the tested platform. They do not establish comprehensive media security: a legitimately authorized recipient may retain previously downloaded bytes, and revocation cannot retract those copies. Resilience also includes a tradeoff: refusing access when the CA cannot be validated protects the authorization boundary but reduces availability.

## VI. Limitations and Conclusion

All planned new experiments use VMs on a shared host, where resource contention can affect timing. Historical measurements were collected at different development stages and will not be pooled as if they came from one controlled trial. Fresh Windows installation, physical endpoints, sustained production load, and physical CA power-loss behavior remain outside the present evidence. Startup readiness timeouts have occurred in prior observations; later successful probes do not establish that their cause has been eliminated.

VanGuard implements certificate-based admission, employee-session checks, and resource-specific access withdrawal around an unchanged WireGuard tunnel. The existing platform evidence justifies further evaluation of a protected digital media service. The media workload, repeated measurements, and genuine screenshots remain necessary to substantiate the proposed application-specific conclusions. This draft therefore presents an implemented control architecture and a defined evaluation method, rather than a completed media-security validation.

## References

[1] S. Rose, O. Borchert, S. Mitchell, and S. Connelly, “Zero Trust Architecture,” NIST SP 800-207, Aug. 2020, doi: 10.6028/NIST.SP.800-207. https://doi.org/10.6028/NIST.SP.800-207

[2] R. Ward and B. Beyer, “BeyondCorp: A New Approach to Enterprise Security,” ;login:, vol. 39, no. 6, pp. 6–11, 2014. https://research.google/pubs/beyondcorp-a-new-approach-to-enterprise-security/

[3] J. A. Donenfeld, “WireGuard: Next Generation Kernel Network Tunnel,” in Proc. Network and Distributed System Security Symposium (NDSS), 2017, doi: 10.14722/ndss.2017.23160. https://www.ndss-symposium.org/wp-content/uploads/2017/09/ndss2017_04A-3_Donenfeld_paper.pdf

[4] D. Cooper, S. Santesson, S. Farrell, S. Boeyen, R. Housley, and W. Polk, “Internet X.509 Public Key Infrastructure Certificate and Certificate Revocation List (CRL) Profile,” RFC 5280, May 2008, doi: 10.17487/RFC5280. https://www.rfc-editor.org/rfc/rfc5280
