# Code Normalizer

This is a foundational service, so let's design it properly. The CodeNormalizer should be pure, deterministic, stateless, and independent of Django and Solidity analyzers. Its only responsibility is to transform semantically equivalent source code into a canonical representation.

Objectives

The service should:

Normalize line endings (CRLF → LF)
Normalize Unicode (NFC)
Remove trailing whitespace
Collapse multiple blank lines
Normalize tabs to spaces
Normalize spacing around operators and punctuation
Optionally remove comments
Produce deterministic output

It should not:

Parse Solidity ASTs (future enhancement)
Rename identifiers
Modify code semantics
Depend on Slither, Mythril, or Django
Proposed Location
scanner/
└── domain/
    └── services/
        └── code_normalizer.py
Public API

I recommend a simple static API:

normalized = CodeNormalizer.normalize(
    code,
    remove_comments=True,
)

This keeps it easy to use from the FingerprintService.

Internal Design
normalize()
    │
    ├── normalize_unicode()
    ├── normalize_line_endings()
    ├── normalize_tabs()
    ├── remove_comments()
    ├── normalize_whitespace()
    ├── collapse_blank_lines()
    └── strip()