### Architect's Note #25 – Normalize Before You Hash

A fingerprint should identify the business concept, not the incidental representation.

Before generating a hash, the data should be normalized into a stable signature that excludes fields likely to change over time, such as descriptions, recommendations, or confidence levels. By hashing only the canonical characteristics of a vulnerability—such as rule identifier, source location, and code context—we ensure that identical vulnerabilities produce identical fingerprints across scans, analyzer versions, and reporting formats.

This separation between signature construction and hash generation follows the Single Responsibility Principle. The FindingSignature value object defines what constitutes the identity of a vulnerability, while the FingerprintService defines how that identity is converted into a stable fingerprint.