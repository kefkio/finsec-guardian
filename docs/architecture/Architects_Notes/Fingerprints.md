# Architect's Note #26 – 
## Fingerprints Should Represent Semantics, Not Coordinates

A vulnerability's identity should be derived from its semantic meaning rather than its physical position in a source file. Line numbers, formatting, and comments are incidental details that frequently change during normal software maintenance. If these transient attributes influence the fingerprint, identical vulnerabilities will appear as new issues after harmless edits, reducing the usefulness of historical tracking and regression analysis.

By constructing fingerprints from stable semantic elements—such as vulnerability type, contract, function, and normalized code context—FinSec Guardian identifies the vulnerability itself rather than its current location. This produces fingerprints that remain stable across routine code changes and provides a more reliable foundation for deduplication, suppression, historical comparison, and cross-analyzer correlation.