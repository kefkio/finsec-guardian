Architect's Notes #3
Severity
Purpose

Represents how dangerous a vulnerability is.

Severity measures impact only.

It does not consider:

confidence
exploitability
business importance
Mental Model
Finding

↓

Severity

↓

How bad is this vulnerability?
Example
Reentrancy

↓

Critical

Even if the contract has never been deployed,

the severity remains Critical.

Owns
priority
is_high_risk
Does NOT Own
Overall Risk
Risk Score
Collaborates With
Finding

Risk Engine
Important Lesson

Severity is intrinsic to the vulnerability.

It rarely changes.