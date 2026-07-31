Architect's Note #41 – Build the Engine Before the Vehicle

In layered architectures, there is often pressure to complete visible domain entities before the underlying processing engine exists. This can lead to repeated redesign as new behaviors are discovered.

For FinSec Guardian, the semantic fingerprinting pipeline is foundational. It defines how vulnerabilities are identified, normalized, and tracked over time. Since Finding depends on these concepts for its identity and lifecycle, completing the semantic pipeline first reduces future refactoring and establishes a stable foundation for the remaining aggregates.

A useful heuristic is:

Complete the mechanisms that define an entity's identity before completing the entity itself.

My Recommendation for the Next Sprint

I think we should implement these components in this order:

NormalizedCode (Value Object)
CodeNormalizer (Domain Service)
VulnerabilitySignature (Value Object)
FingerprintStrategy (Abstract Strategy)
SemanticFingerprintStrategy (Concrete Strategy)
FingerprintService (Domain Service)
Return to Finding and complete it with confidence.

This order minimizes redesign, keeps responsibilities clear, and follows the dependency flow we've established throughout the project. It also positions the backend so that, once we reach the application layer, the scanner's core intelligence is already encapsulated within the domain. I think that's the strongest architectural foundation we can build.