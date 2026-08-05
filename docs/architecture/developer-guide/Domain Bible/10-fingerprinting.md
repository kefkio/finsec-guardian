# Fingerprinting

Fingerprinting is the process of generating a stable, deterministic identifier for a vulnerability.
It is a domain concern because it captures the semantic identity of a finding rather than its database identity.

## Fingerprint Service

`FingerprintService` is a domain service that generates `VulnerabilitySignature` objects.

Key responsibilities:

- Validate analyzer, title, and location inputs.
- Build a canonical payload from analyzer metadata, normalized file path, title, and line number.
- Hash the payload using a versioned algorithm.
- Provide a `matches()` helper for equality checks.

## Versioning and Stability

The fingerprint algorithm is versioned so that future improvements can coexist with historical data.
This avoids invalidating prior scan results when the signature strategy evolves.

## Domain Rationale

Fingerprint generation belongs in the domain because:

- it derives from domain facts about the vulnerability
- it is used for duplicate detection and correlation
- it must remain stable even when infrastructure or reporting formats change

## Current Behavior

The existing `FingerprintService` normalizes file paths, lowercases titles, and includes the analyzer type.
It uses SHA-256 to produce a normalized `VulnerabilitySignature`.

Future versions may evolve the payload to include richer semantic identifiers such as AST nodes, function signatures, or normalized code fragments.
