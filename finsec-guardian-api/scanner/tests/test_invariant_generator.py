"""Invariant engine test suite.

Validates four research-critical properties:
    1. **Correct generation** — correct rules fire for each Solidity pattern
    2. **Determinism** — identical input always yields identical output
    3. **Deduplication** — no duplicate invariant functions are emitted
    4. **Pattern isolation** — each pattern behaves independently

These are essential for thesis reproducibility and empirical evaluation.
"""

from __future__ import annotations

from django.test import SimpleTestCase

from scanner.services.invariants import InvariantGenerator, InvariantInjector
from scanner.services.invariants.patterns import (
    BoolSanityPattern,
    ContractBalancePattern,
    InvariantPattern,
    OwnerNotZeroPattern,
    UintNonNegativePattern,
)

# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------

_BASIC_CONTRACT = """\
contract Test {
    uint256 balance;
    address owner;
    bool paused;
}
"""

_TOKEN_CONTRACT = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleToken {
    uint256 public totalSupply;
    uint256 balance;
    address public owner;
    address payable recipient;
    bool public paused;
    bool initialized;
    mapping(address => uint256) public balances;

    constructor() {
        owner = msg.sender;
        totalSupply = 1000;
    }
}
"""

_DUPLICATE_VARS_CONTRACT = """\
contract Test {
    uint256 balance;
    uint256 balance;
}
"""

_EMPTY_CONTRACT = """\
contract Empty {}
"""

_NO_STATE_VARS_CONTRACT = """\
contract Test {
    string name;
    bytes data;
}
"""

_INHERITED_CONTRACT = """\
pragma solidity ^0.8.0;

interface IVault {
    function deposit() external payable;
}

contract Vault is IVault {
    address public owner;
    uint256 funds;

    function deposit() external payable override {
        funds += msg.value;
    }
}
"""

_MULTI_OWNER_CONTRACT = """\
contract MultiOwner {
    address public owner;
    address public previousOwner;
    address admin;
    uint256 count;
}
"""


# =======================================================================
# 1. Correct invariant generation
# =======================================================================


class TestBasicGeneration(SimpleTestCase):
    """Test 1 — Correct rules fire for each variable category."""

    def test_basic_contract_produces_expected_invariants(self):
        gen = InvariantGenerator()
        result = gen.generate(_BASIC_CONTRACT)

        self.assertGreater(result["count"], 0)
        self.assertIn("echidna_balance_non_negative", result["code"])
        self.assertIn("echidna_owner_not_zero", result["code"])

    def test_token_contract_produces_all_categories(self):
        gen = InvariantGenerator()
        result = gen.generate(_TOKEN_CONTRACT)

        code = result["code"]
        # uint → non-negative
        self.assertIn("echidna_totalSupply_non_negative", code)
        self.assertIn("echidna_balance_non_negative", code)
        # address owner → not-zero
        self.assertIn("echidna_owner_not_zero", code)
        # bool → sanity
        self.assertIn("echidna_paused_valid", code)
        self.assertIn("echidna_initialized_valid", code)
        # contract balance — always present
        self.assertIn("echidna_contract_balance_non_negative", code)

    def test_all_names_follow_echidna_convention(self):
        gen = InvariantGenerator()
        result = gen.generate(_TOKEN_CONTRACT)

        for name in result["names"]:
            self.assertTrue(
                name.startswith("echidna_"),
                f"{name} does not follow echidna_ naming convention",
            )

    def test_count_matches_names_length(self):
        gen = InvariantGenerator()
        result = gen.generate(_TOKEN_CONTRACT)
        self.assertEqual(result["count"], len(result["names"]))


# =======================================================================
# 2. Determinism (critical for research reproducibility)
# =======================================================================


class TestDeterminism(SimpleTestCase):
    """Test 2 — Same input always produces identical output."""

    def test_deterministic_code_output(self):
        gen = InvariantGenerator()
        r1 = gen.generate(_BASIC_CONTRACT)
        r2 = gen.generate(_BASIC_CONTRACT)

        self.assertEqual(r1["code"], r2["code"])
        self.assertEqual(r1["count"], r2["count"])

    def test_deterministic_across_instances(self):
        r1 = InvariantGenerator().generate(_TOKEN_CONTRACT)
        r2 = InvariantGenerator().generate(_TOKEN_CONTRACT)

        self.assertEqual(r1["code"], r2["code"])
        self.assertEqual(r1["names"], r2["names"])

    def test_deterministic_names_ordering(self):
        gen = InvariantGenerator()
        r1 = gen.generate(_TOKEN_CONTRACT)
        r2 = gen.generate(_TOKEN_CONTRACT)

        self.assertEqual(r1["names"], r2["names"])


# =======================================================================
# 3. Deduplication
# =======================================================================


class TestDeduplication(SimpleTestCase):
    """Test 3 — Duplicate state variable declarations produce unique invariants."""

    def test_duplicate_vars_are_deduplicated(self):
        gen = InvariantGenerator()
        result = gen.generate(_DUPLICATE_VARS_CONTRACT)

        # names list should contain no duplicates
        self.assertEqual(len(result["names"]), len(set(result["names"])))

    def test_code_contains_no_duplicate_functions(self):
        gen = InvariantGenerator()
        result = gen.generate(_DUPLICATE_VARS_CONTRACT)

        occurrences = result["code"].count("echidna_balance_non_negative")
        self.assertEqual(occurrences, 1, "Duplicate function body detected")


# =======================================================================
# 4. Pattern isolation
# =======================================================================


class TestPatternIsolation(SimpleTestCase):
    """Test 4 — Each pattern matches only its target category."""

    def test_uint_pattern_only_matches_uint_vars(self):
        pattern = UintNonNegativePattern()
        results = pattern.match(_TOKEN_CONTRACT)
        joined = "\n".join(results)

        self.assertIn("echidna_totalSupply_non_negative", joined)
        self.assertIn("echidna_balance_non_negative", joined)
        # Must NOT match address or bool vars
        self.assertNotIn("owner", joined)
        self.assertNotIn("paused", joined)

    def test_uint_pattern_filters_solidity_keywords(self):
        src = "uint256 public count; uint256 immutable cap;"
        pattern = UintNonNegativePattern()
        results = pattern.match(src)
        names = "\n".join(results)

        self.assertIn("echidna_count_", names)
        self.assertIn("echidna_cap_", names)
        self.assertNotIn("echidna_public_", names)
        self.assertNotIn("echidna_immutable_", names)

    def test_owner_pattern_only_matches_owner_addresses(self):
        pattern = OwnerNotZeroPattern()
        results = pattern.match(_TOKEN_CONTRACT)
        joined = "\n".join(results)

        self.assertIn("echidna_owner_not_zero", joined)
        # recipient is an address but not an owner
        self.assertNotIn("recipient", joined)

    def test_owner_pattern_matches_multiple_owner_vars(self):
        pattern = OwnerNotZeroPattern()
        results = pattern.match(_MULTI_OWNER_CONTRACT)

        names = "\n".join(results)
        self.assertIn("echidna_owner_not_zero", names)
        self.assertIn("echidna_previousOwner_not_zero", names)
        # admin has no "owner" in the name
        self.assertNotIn("admin", names)

    def test_bool_pattern_only_matches_bool_vars(self):
        pattern = BoolSanityPattern()
        results = pattern.match(_TOKEN_CONTRACT)
        joined = "\n".join(results)

        self.assertIn("echidna_paused_valid", joined)
        self.assertIn("echidna_initialized_valid", joined)
        # Must NOT match uint or address
        self.assertNotIn("balance", joined)
        self.assertNotIn("owner", joined)

    def test_contract_balance_pattern_always_emits(self):
        pattern = ContractBalancePattern()
        results = pattern.match("")
        self.assertEqual(len(results), 1)
        self.assertIn("echidna_contract_balance_non_negative", results[0])

    def test_custom_patterns_override_defaults(self):
        gen = InvariantGenerator(patterns=[ContractBalancePattern()])
        result = gen.generate(_TOKEN_CONTRACT)
        self.assertEqual(result["count"], 1)
        self.assertIn("echidna_contract_balance_non_negative", result["code"])


# =======================================================================
# 5. Empty / minimal contract safety
# =======================================================================


class TestEmptyContractSafety(SimpleTestCase):
    """Test 5 — Generator handles edge-case contracts without crashing."""

    def test_empty_contract(self):
        gen = InvariantGenerator()
        result = gen.generate(_EMPTY_CONTRACT)

        self.assertIsInstance(result, dict)
        self.assertIn("code", result)
        self.assertIn("count", result)
        self.assertIn("names", result)
        self.assertIsNotNone(result["code"])

    def test_empty_source_string(self):
        gen = InvariantGenerator()
        result = gen.generate("")

        # ContractBalancePattern always fires
        self.assertEqual(result["count"], 1)
        self.assertIn("echidna_contract_balance_non_negative", result["names"])

    def test_comment_only_source(self):
        gen = InvariantGenerator()
        result = gen.generate("// just a comment\n/* block */")
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result["count"], 1)  # balance pattern still fires


# =======================================================================
# 6. No false positives
# =======================================================================


class TestNoFalsePositives(SimpleTestCase):
    """Test 6 — Contracts without matching types only get the baseline."""

    def test_no_false_positive_for_string_and_bytes(self):
        gen = InvariantGenerator()
        result = gen.generate(_NO_STATE_VARS_CONTRACT)

        # Only the contract-level balance invariant should appear
        self.assertIn("echidna_contract_balance_non_negative", result["code"])
        # No uint/address/bool-based invariants
        self.assertNotIn("echidna_name_", result["code"])
        self.assertNotIn("echidna_data_", result["code"])


# =======================================================================
# 7. Injector tests
# =======================================================================


class TestInvariantInjector(SimpleTestCase):
    """Validates safe Solidity code injection."""

    def test_inject_into_simple_contract(self):
        injector = InvariantInjector()
        code = "function echidna_test() public view returns (bool) { return true; }"
        result = injector.inject(_EMPTY_CONTRACT, code)

        self.assertIn("// === AUTO-GENERATED ECHIDNA INVARIANTS ===", result)
        self.assertIn("echidna_test", result)
        # Invariant must be inside the contract body
        brace_pos = result.index("contract Empty {")
        inv_pos = result.index("echidna_test")
        close_brace = result.rindex("}")
        self.assertGreater(inv_pos, brace_pos)
        self.assertLess(inv_pos, close_brace)

    def test_inject_targets_last_contract(self):
        injector = InvariantInjector()
        code = "function echidna_ok() public view returns (bool) { return true; }"
        result = injector.inject(_INHERITED_CONTRACT, code)

        self.assertIn("echidna_ok", result)
        # Should inject into Vault (last contract), not IVault
        vault_pos = result.index("contract Vault is IVault {")
        inv_pos = result.index("echidna_ok")
        self.assertGreater(inv_pos, vault_pos)

    def test_inject_empty_code_returns_unchanged(self):
        injector = InvariantInjector()
        result = injector.inject(_TOKEN_CONTRACT, "   ")
        self.assertEqual(result, _TOKEN_CONTRACT)

    def test_inject_without_contract_appends_at_eof(self):
        injector = InvariantInjector()
        src = "// just a comment"
        code = "function echidna_x() public view returns (bool) { return true; }"
        result = injector.inject(src, code)
        self.assertIn("echidna_x", result)


# =======================================================================
# 8. End-to-end integration
# =======================================================================


class TestEndToEnd(SimpleTestCase):
    """Test the full generate → inject pipeline."""

    def test_generate_and_inject_round_trip(self):
        gen = InvariantGenerator()
        injector = InvariantInjector()

        inv = gen.generate(_TOKEN_CONTRACT)
        result = injector.inject(_TOKEN_CONTRACT, inv["code"])

        # All generated function names must appear in injected output
        for name in inv["names"]:
            self.assertIn(name, result)

    def test_injected_code_preserves_original_contract(self):
        gen = InvariantGenerator()
        injector = InvariantInjector()

        inv = gen.generate(_TOKEN_CONTRACT)
        result = injector.inject(_TOKEN_CONTRACT, inv["code"])

        # Original state vars still present
        self.assertIn("uint256 public totalSupply", result)
        self.assertIn("address public owner", result)
        self.assertIn("bool public paused", result)

    def test_inherited_contract_round_trip(self):
        gen = InvariantGenerator()
        injector = InvariantInjector()

        inv = gen.generate(_INHERITED_CONTRACT)
        result = injector.inject(_INHERITED_CONTRACT, inv["code"])

        for name in inv["names"]:
            self.assertIn(name, result)
        # Original function still intact
        self.assertIn("function deposit()", result)


# =======================================================================
# 9. Robustness (fuzz-style)
# =======================================================================


class TestRobustness(SimpleTestCase):
    """Generator must never crash on arbitrary input."""

    def test_random_strings_do_not_crash(self):
        gen = InvariantGenerator()
        adversarial_inputs = [
            "",
            "   ",
            "uint256",
            "contract { }",
            "contract X { function() }",
            "bool bool bool",
            "address address address",
            "\x00\x01\x02",
            "a" * 10_000,
            "pragma solidity ^99.99.99;",
            "contract\n" * 100,
        ]

        for source in adversarial_inputs:
            result = gen.generate(source)
            self.assertIsInstance(result, dict, f"Failed on input: {source[:50]!r}")
            self.assertIn("code", result)
            self.assertIn("count", result)
            self.assertIn("names", result)
