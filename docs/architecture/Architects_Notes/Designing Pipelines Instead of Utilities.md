# Architect's Note #32 – Designing Pipelines Instead of Utilities

One of the architectural goals of FinSec Guardian is to model analysis as a sequence of explicit transformations rather than a collection of unrelated utility functions. Each stage in the fingerprinting pipeline consumes a well-defined domain concept and produces another. This makes the flow of information visible, testable, and extensible.

By expressing the process as:

CodeContext → CodeNormalizer → NormalizedCode → VulnerabilitySignature → FingerprintStrategy → Fingerprint

we gain several advantages:

Each component has a single, well-defined responsibility.
New stages can be introduced without disrupting existing ones.
Individual transformations can be tested independently.
The architecture naturally supports future enhancements, such as AST-based normalization or AI-assisted semantic analysis.

This pipeline-oriented approach treats domain knowledge as a sequence of meaningful transformations rather than a collection of procedural steps, resulting in a system that is easier to reason about and evolve.

Our First Task

We'll begin with CodeContext, but not by writing code immediately.

We'll first refine its API until it feels complete and intuitive. Once we're satisfied that it accurately models the semantic context of a vulnerability, implementing the code will be straightforward. This follows the principle we've been developing throughout the project: design the model first, then let the code become a faithful implementation of that model.