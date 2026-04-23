"""Reusable invariant pattern rules for Echidna property-based fuzzing.

Each pattern class detects a category of state variables in Solidity source
code and emits corresponding ``echidna_*`` invariant functions.  The pattern
engine is intentionally regex-based — an AST-based upgrade path is planned
for future iterations.

Adding a new invariant category:
    1. Subclass ``InvariantPattern``.
    2. Implement ``match()`` returning a list of Solidity function bodies.
    3. Register the pattern in ``InvariantGenerator.__init__``.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

# Solidity keywords that regex may accidentally capture as variable names.
_SOLIDITY_KEYWORDS: frozenset[str] = frozenset({
    "public", "private", "internal", "external", "constant", "immutable",
    "override", "virtual", "payable", "memory", "storage", "calldata",
    "returns", "indexed", "anonymous", "pure", "view",
})

# Non-capturing group that matches zero or more Solidity modifiers between
# a type keyword and the actual variable name.
_MODIFIERS = r"(?:(?:public|private|internal|external|constant|immutable|override|virtual)\s+)*"


class InvariantPattern(ABC):
    """Base class for invariant pattern detectors."""

    @abstractmethod
    def match(self, source_code: str) -> list[str]:
        """Return a list of Solidity ``echidna_*`` function bodies."""


class UintNonNegativePattern(InvariantPattern):
    """Generates ``uint >= 0`` sanity checks for unsigned integer state vars.

    Always true by Solidity semantics — a violation indicates compiler-level
    corruption or an unexpected storage-slot collision.
    """

    def match(self, source_code: str) -> list[str]:
        vars_ = re.findall(rf"\buint\d*\s+{_MODIFIERS}(\w+)", source_code)
        return [
            f"function echidna_{v}_non_negative() public view returns (bool) {{\n"
            f"    return {v} >= 0;\n"
            f"}}"
            for v in vars_
            if v not in _SOLIDITY_KEYWORDS
        ]


class OwnerNotZeroPattern(InvariantPattern):
    """Ensures ``address`` variables containing *owner* are never zero.

    Detects ownership invalidation — the zero-address owner effectively
    disables all ``onlyOwner`` guarded functions.
    """

    def match(self, source_code: str) -> list[str]:
        vars_ = re.findall(
            rf"\baddress\s+(?:payable\s+)?{_MODIFIERS}(\w+)", source_code,
        )
        return [
            f"function echidna_{v}_not_zero() public view returns (bool) {{\n"
            f"    return {v} != address(0);\n"
            f"}}"
            for v in vars_
            if v not in _SOLIDITY_KEYWORDS and "owner" in v.lower()
        ]


class BoolSanityPattern(InvariantPattern):
    """Generates boolean sanity checks (always true; detects corruption).

    A violation indicates storage corruption or unexpected state mutation
    that pushed a bool storage slot outside ``{0, 1}``.
    """

    def match(self, source_code: str) -> list[str]:
        vars_ = re.findall(rf"\bbool\s+{_MODIFIERS}(\w+)", source_code)
        return [
            f"function echidna_{v}_valid() public view returns (bool) {{\n"
            f"    return {v} == true || {v} == false;\n"
            f"}}"
            for v in vars_
            if v not in _SOLIDITY_KEYWORDS
        ]


class ContractBalancePattern(InvariantPattern):
    """Asserts ``address(this).balance >= 0`` — detects unexpected drains.

    Always true at the EVM level, but a violation under Echidna's symbolic
    model flags potential accounting bugs.
    """

    def match(self, source_code: str) -> list[str]:
        return [
            "function echidna_contract_balance_non_negative() public view returns (bool) {\n"
            "    return address(this).balance >= 0;\n"
            "}"
        ]
