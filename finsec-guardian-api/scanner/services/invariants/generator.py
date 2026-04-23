"""Core invariant generation engine.

Applies all registered ``InvariantPattern`` rules against Solidity source
code and returns a structured result containing generated invariant function
bodies, their names, and metadata for downstream tracking.
"""

from __future__ import annotations

import re

from .patterns import (
    BoolSanityPattern,
    ContractBalancePattern,
    InvariantPattern,
    OwnerNotZeroPattern,
    UintNonNegativePattern,
)


class InvariantGenerator:
    """Generates Echidna-compatible invariant functions from Solidity source.

    Usage::

        gen = InvariantGenerator()
        result = gen.generate(source_code)
        # result["code"]  → Solidity function bodies
        # result["count"] → number of unique invariants
        # result["names"] → list of echidna_* function names
    """

    def __init__(self, patterns: list[InvariantPattern] | None = None) -> None:
        self.patterns: list[InvariantPattern] = patterns or [
            UintNonNegativePattern(),
            OwnerNotZeroPattern(),
            BoolSanityPattern(),
            ContractBalancePattern(),
        ]

    def generate(self, source_code: str) -> dict:
        """Analyse *source_code* and return generated invariants.

        Returns::

            {
                "code":  str   — joined Solidity function bodies,
                "count": int   — number of unique invariants generated,
                "names": list  — ``echidna_*`` function names for tagging,
            }
        """
        invariants: list[str] = []

        for pattern in self.patterns:
            invariants.extend(pattern.match(source_code))

        # Deduplicate while preserving deterministic order.
        seen: set[str] = set()
        unique: list[str] = []
        for inv in invariants:
            normalised = inv.strip()
            if normalised not in seen:
                seen.add(normalised)
                unique.append(normalised)

        code = "\n\n".join(unique)
        names = re.findall(r"function\s+(echidna_\w+)", code)

        return {
            "code": code,
            "count": len(unique),
            "names": names,
        }
