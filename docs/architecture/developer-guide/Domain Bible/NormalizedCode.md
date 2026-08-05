# Step 1 — Problem Statement

The scanner receives source code from different analyzers.

The same vulnerability may appear as:

function withdraw(uint amount) public {

    balances[msg.sender] -= amount;

    payable(msg.sender).call{value: amount}("");
}

or

function withdraw(uint amount) public{
balances[msg.sender]-=amount;
payable(msg.sender).call{value:amount}("");
}

These represent the same logic.

The scanner therefore needs a canonical representation that can be compared consistently.

That business concept is NormalizedCode.

Step 2 — Mental Model
                    Source Code
                         │
                         ▼
                 CodeNormalizer
                         │
                         ▼
                 NormalizedCode
                         │
                         ▼
            VulnerabilitySignature
                         │
                         ▼
               FingerprintService

Notice that NormalizedCode never normalizes anything.

It simply represents the output.

Step 3 — Responsibilities
Owns

✅ canonical source

✅ validation

✅ immutability

✅ equality

Does NOT Own

❌ parsing

❌ AST generation

❌ hashing

❌ fingerprint generation

❌ normalization

Step 4 — Invariants

A valid NormalizedCode:

cannot be empty
cannot contain only whitespace
cannot contain leading whitespace
cannot contain trailing whitespace
is immutable
is deterministic
Step 5 — Relationships
CodeContext
      │
      ▼
CodeNormalizer
      │
      ▼
NormalizedCode
      │
      ▼
VulnerabilitySignature
Production Implementation

I think this should become our official Version 1.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NormalizedCode:
    """
    Represents the canonical representation of source code.

    Responsibilities
    ----------------
    - Store normalized source code.
    - Enforce the invariants of canonical code.
    - Provide an immutable value suitable for deterministic
      comparison and fingerprint generation.

    Invariants
    ----------
    - The normalized code cannot be empty.
    - The normalized code cannot consist solely of whitespace.
    - The normalized code must not contain leading or trailing
      whitespace.

    Notes
    -----
    This value object does not perform normalization itself.
    Canonicalization is the responsibility of the
    CodeNormalizer domain service.
    """

    value: str

    def __post_init__(self) -> None:
        """
        Validate the normalized source code.
        """
        normalized = self.value.strip()

        if not normalized:
            raise ValueError(
                "Normalized code cannot be empty."
            )

        if normalized != self.value:
            raise ValueError(
                "Normalized code must not contain "
                "leading or trailing whitespace."
            )

    @property
    def length(self) -> int:
        """
        Returns the number of characters in the normalized code.
        """
        return len(self.value)

    def display(self) -> str:
        """
        Returns the normalized source code.
        """
        return self.value

    def summary(self) -> str:
        """
        Returns a concise representation of the normalized code.
        """
        max_length = 80

        if len(self.value) <= max_length:
            return self.value

        return f"{self.value[:max_length]}..."

    def __str__(self) -> str:
        """
        Returns the normalized source code.
        """
        return self.value
Why I Added summary()

This wasn't in our original design, but I think it belongs.

Imagine your logs:

Instead of printing

NormalizedCode(
function withdraw(uint amount)
...
4000 characters...
)

you can simply call

normalized_code.summary()

Result:

function withdraw(uint amount) public { balances[msg.sender]-=amount; ...

This is extremely useful for:

logging
debugging
audit trails
console output
unit test failures

without exposing thousands of characters.

Architecture Maturity
Item	Status
Blueprint	✅
Production Code	✅
Tests	⏳
Integration	⏳

Maturity: ⭐⭐⭐☆☆ (Level 3 of 5 once tests are added)

Next Sprint (Immediately After)

Now that we've defined what NormalizedCode is, we can implement the service that produces it:

CodeContext
        │
        ▼
CodeNormalizer
        │
        ▼
NormalizedCode

