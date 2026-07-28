Architect's Notes #4
Confidence
Purpose

Represents how certain an analyzer is that the finding is a true positive.

Mental Model
Analyzer

↓

Confidence

↓

How sure are we?
Example
Integer Overflow

↓

Low Confidence

↓

Needs Manual Review
Owns
weight
priority
is_high_confidence
Does NOT Own

Severity.

These are independent concepts.

Biggest Lesson

High Severity

≠

High Confidence

Architect's Notes #5
AnalyzerType
Purpose

Represents who or what produced the finding.

Mental Model
Slither

↓

Finding

↑

Mythril

↑

AI

↑

Manual Review

Every finding has an origin.

Owns
is_automated
supports_reproducibility
is_ai_powered