"""Safe Solidity source code injection for auto-generated invariants.

Injects ``echidna_*`` functions inside the body of the last ``contract``
declaration in the source file.  Falls back to appending at EOF if no
contract is detected (e.g. interface-only files).
"""

from __future__ import annotations

import re


class InvariantInjector:
    """Injects invariant function code into a Solidity contract body."""

    # Matches ``contract <Name> ... {`` including inheritance clauses
    # such as ``contract Foo is Bar, Baz {``.
    _CONTRACT_RE = re.compile(r"contract\s+\w+[^{]*\{")

    def inject(self, source_code: str, invariant_code: str) -> str:
        """Insert *invariant_code* into the last contract in *source_code*.

        Invariants are placed immediately after the opening brace of the
        last ``contract`` block so they appear at the top of the contract
        body.  Solidity resolves state-variable references contract-wide,
        so declaration order does not affect correctness.

        If no ``contract`` keyword is found the invariants are appended at
        EOF as a last resort.
        """
        if not invariant_code.strip():
            return source_code

        matches = list(self._CONTRACT_RE.finditer(source_code))

        if not matches:
            # No contract found — append at EOF as a last resort.
            return source_code + "\n" + invariant_code

        last_match = matches[-1]
        insert_pos = last_match.end()

        return (
            source_code[:insert_pos]
            + "\n\n    // === AUTO-GENERATED ECHIDNA INVARIANTS ===\n\n"
            + invariant_code
            + "\n"
            + source_code[insert_pos:]
        )
