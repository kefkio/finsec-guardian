"""
Canonical vulnerability taxonomy for FinSec Guardian.

RuleType represents normalized security rules independently of
the analyzer that produced them.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import ClassVar, Mapping, TypeVar
import re
from functools import lru_cache

from .base import DomainEnum
from .severity import Severity
from .risk_category import RiskCategory

TRuleType = TypeVar("TRuleType", bound="RuleType")


class RuleType(DomainEnum):
    """
    Canonical vulnerability and rule identifiers.

    RuleType represents the security issue itself rather than
    the tool that detected it.
    """

    # ==========================================================
    # Critical Vulnerabilities
    # ==========================================================

    REENTRANCY = "reentrancy"
    ACCESS_CONTROL = "access_control"
    DELEGATECALL = "delegatecall"
    SELFDESTRUCT = "selfdestruct"
    ARBITRARY_STORAGE_WRITE = "arbitrary_storage_write"
    UNINITIALIZED_PROXY = "uninitialized_proxy"

    # ==========================================================
    # High / Medium Vulnerabilities
    # ==========================================================

    INTEGER_OVERFLOW = "integer_overflow"
    INTEGER_UNDERFLOW = "integer_underflow"
    UNCHECKED_CALL = "unchecked_call"
    TX_ORIGIN = "tx_origin"
    TIMESTAMP_DEPENDENCE = "timestamp_dependence"
    DENIAL_OF_SERVICE = "denial_of_service"
    FRONT_RUNNING = "front_running"
    ARBITRARY_STORAGE_READ = "arbitrary_storage_read"
    UNINITIALIZED_STORAGE = "uninitialized_storage"
    WEAK_RANDOMNESS = "weak_randomness"
    ASSERT_VIOLATION = "assert_violation"

    # ==========================================================
    # Quality Rules
    # ==========================================================

    GAS_OPTIMIZATION = "gas_optimization"
    DEAD_CODE = "dead_code"
    STYLE = "style"

    # ==========================================================
    # Unknown
    # ==========================================================

    OTHER = "other"

    # Quoted string annotation for class variable typing
    _PATTERN_MAP: ClassVar[tuple[tuple[str, RuleType], ...]]

    # ==========================================================
    # Construction / Normalization
    # ==========================================================

    @classmethod
    def from_raw_rule(
        cls: type[TRuleType],
        raw_identifier: str,
    ) -> TRuleType:
        """Converts a raw analyzer detector name into the canonical RuleType."""
        if not raw_identifier or not (raw := raw_identifier.strip()):
            return cls.OTHER

        normalized = raw.lower().translate(_DELIMITER_TRANSLATION)
        normalized = _UNDERSCORE_RE.sub("_", normalized).strip("_")

        if not normalized:
            return cls.OTHER

        try:
            return cls(normalized)
        except ValueError:
            pass

        return _cached_map_normalized_to_rule(normalized)

    # ==========================================================
    # Domain Predicates
    # ==========================================================

    @property
    def is_security_vulnerability(self) -> bool:
        """
        Returns True if this rule represents an actionable security issue
        rather than code style, gas optimization, or unknown finding.
        """
        return (
            self is not RuleType.GAS_OPTIMIZATION
            and self is not RuleType.DEAD_CODE
            and self is not RuleType.STYLE
            and self is not RuleType.OTHER
        )

    @property
    def is_quality_rule(self) -> bool:
        """
        Returns True if the rule represents a quality or optimization issue
        rather than a security vulnerability.
        """
        return not (self.is_security_vulnerability or self.is_unknown)

    @property
    def is_unknown(self) -> bool:
        """Returns True if the rule couldn't be normalized to a known category."""
        return self is RuleType.OTHER

    @property
    def is_critical_category(self) -> bool:
        """Returns True if this rule is classified in the top-tier critical risk category."""
        return self.default_severity is Severity.CRITICAL

    # ==========================================================
    # UI & Taxonomy Metadata (Single Source of Truth)
    # ==========================================================

    @property
    def display_name(self) -> str:
        """Human-readable display title (e.g., 'Unchecked Call')."""
        # Prefer explicit display mapping for special cases
        explicit = _DISPLAY_NAMES.get(self)
        if explicit:
            return explicit

        # Default behavior
        return self.value.replace("_", " ").title()

    @property
    def swc_id(self) -> str | None:
        """Returns default SWC Registry ID if mapped."""
        return _SWC_MAP.get(self)

    @property
    def cwe_id(self) -> str | None:
        """Returns default CWE identifier if mapped."""
        return _CWE_MAP.get(self)

    @property
    def owasp_id(self) -> str | None:
        """Returns mapped OWASP control ID if available."""
        return _OWASP_MAP.get(self)

    @property
    def default_severity(self) -> Severity:
        """Return a default Severity for this rule when none provided."""
        return _RULE_SEVERITY.get(self, Severity.INFORMATIONAL)

    @property
    def risk_category(self) -> RiskCategory:
        """High-level risk category for dashboards and aggregation."""
        return _RULE_CATEGORY.get(self, RiskCategory.OTHER)


# ==========================================================
# Post-Class Initialization for Pattern Map (Specific -> Generic)
# ==========================================================

RuleType._PATTERN_MAP = (
    ("uninitialized_proxy", RuleType.UNINITIALIZED_PROXY),
    ("storage_write", RuleType.ARBITRARY_STORAGE_WRITE),
    ("storage_read", RuleType.ARBITRARY_STORAGE_READ),
    ("unchecked_call", RuleType.UNCHECKED_CALL),
    ("low_level_call", RuleType.UNCHECKED_CALL),
    ("reentrancy", RuleType.REENTRANCY),
    ("reentrant", RuleType.REENTRANCY),
    ("overflow", RuleType.INTEGER_OVERFLOW),
    ("underflow", RuleType.INTEGER_UNDERFLOW),
    ("unchecked", RuleType.UNCHECKED_CALL),
    ("delegatecall", RuleType.DELEGATECALL),
    ("tx_origin", RuleType.TX_ORIGIN),
    ("txorigin", RuleType.TX_ORIGIN),
    ("timestamp", RuleType.TIMESTAMP_DEPENDENCE),
    ("block_timestamp", RuleType.TIMESTAMP_DEPENDENCE),
    ("dos", RuleType.DENIAL_OF_SERVICE),
    ("denial", RuleType.DENIAL_OF_SERVICE),
    ("front_run", RuleType.FRONT_RUNNING),
    ("frontrun", RuleType.FRONT_RUNNING),
    ("uninitialized", RuleType.UNINITIALIZED_STORAGE),
    ("random", RuleType.WEAK_RANDOMNESS),
    ("entropy", RuleType.WEAK_RANDOMNESS),
    ("blockhash", RuleType.WEAK_RANDOMNESS),
    ("selfdestruct", RuleType.SELFDESTRUCT),
    ("suicide", RuleType.SELFDESTRUCT),
    ("assert", RuleType.ASSERT_VIOLATION),
    ("gas", RuleType.GAS_OPTIMIZATION),
    ("dead", RuleType.DEAD_CODE),
    ("unused", RuleType.DEAD_CODE),
    ("style", RuleType.STYLE),
    ("format", RuleType.STYLE),
    ("naming", RuleType.STYLE),
    ("access", RuleType.ACCESS_CONTROL),
    ("owner", RuleType.ACCESS_CONTROL),
    ("auth", RuleType.ACCESS_CONTROL),
)


# Module-level helpers for faster normalization and mapping
_DELIMITER_TRANSLATION = str.maketrans(
    {
        "-": "_",
        " ": "_",
        ".": "_",
        "/": "_",
        ":": "_",
        "(": "_",
        ")": "_",
        "[": "_",
        "]": "_",
    }
)

_UNDERSCORE_RE = re.compile(r"_+")


@lru_cache(maxsize=2048)
def _cached_map_normalized_to_rule(normalized: str) -> RuleType:
    """Cached fallback that maps a normalized token to a RuleType via pattern matching."""
    for pattern, rule in RuleType._PATTERN_MAP:
        if pattern in normalized:
            return rule

    return RuleType.OTHER


# ==========================================================
# Immutable Standards Classification Maps
# ==========================================================

_SWC_MAP: Mapping[RuleType, str] = MappingProxyType(
    {
        RuleType.REENTRANCY: "SWC-107",
        RuleType.ACCESS_CONTROL: "SWC-105",
        RuleType.DELEGATECALL: "SWC-112",
        RuleType.SELFDESTRUCT: "SWC-106",
        RuleType.ARBITRARY_STORAGE_WRITE: "SWC-124",
        RuleType.INTEGER_OVERFLOW: "SWC-101",
        RuleType.INTEGER_UNDERFLOW: "SWC-101",
        RuleType.UNCHECKED_CALL: "SWC-104",
        RuleType.TX_ORIGIN: "SWC-115",
        RuleType.TIMESTAMP_DEPENDENCE: "SWC-116",
        RuleType.DENIAL_OF_SERVICE: "SWC-113",
        RuleType.FRONT_RUNNING: "SWC-114",
        RuleType.UNINITIALIZED_STORAGE: "SWC-109",
        RuleType.WEAK_RANDOMNESS: "SWC-120",
        RuleType.ASSERT_VIOLATION: "SWC-110",
    }
)

_CWE_MAP: Mapping[RuleType, str] = MappingProxyType(
    {
        RuleType.REENTRANCY: "CWE-841",
        RuleType.ACCESS_CONTROL: "CWE-284",
        RuleType.INTEGER_OVERFLOW: "CWE-190",
        RuleType.INTEGER_UNDERFLOW: "CWE-191",
        RuleType.UNCHECKED_CALL: "CWE-252",
        RuleType.TX_ORIGIN: "CWE-287",
        RuleType.DENIAL_OF_SERVICE: "CWE-400",
        RuleType.WEAK_RANDOMNESS: "CWE-330",
    }
)


# ==========================================================
# Additional classification mappings
# ==========================================================

_RULE_SEVERITY: Mapping[RuleType, Severity] = MappingProxyType(
    {
        RuleType.REENTRANCY: Severity.CRITICAL,
        RuleType.ACCESS_CONTROL: Severity.CRITICAL,
        RuleType.DELEGATECALL: Severity.CRITICAL,
        RuleType.SELFDESTRUCT: Severity.CRITICAL,
        RuleType.ARBITRARY_STORAGE_WRITE: Severity.CRITICAL,
        RuleType.UNINITIALIZED_PROXY: Severity.CRITICAL,
        RuleType.INTEGER_OVERFLOW: Severity.HIGH,
        RuleType.INTEGER_UNDERFLOW: Severity.HIGH,
        RuleType.UNCHECKED_CALL: Severity.HIGH,
        RuleType.TX_ORIGIN: Severity.HIGH,
        RuleType.TIMESTAMP_DEPENDENCE: Severity.MEDIUM,
        RuleType.DENIAL_OF_SERVICE: Severity.HIGH,
        RuleType.FRONT_RUNNING: Severity.HIGH,
        RuleType.WEAK_RANDOMNESS: Severity.HIGH,
    }
)


_OWASP_MAP: Mapping[RuleType, str] = MappingProxyType(
    {
        RuleType.REENTRANCY: "SC03",
        RuleType.ACCESS_CONTROL: "SC02",
        RuleType.DELEGATECALL: "SC08",
        RuleType.SELFDESTRUCT: "SC09",
        RuleType.ARBITRARY_STORAGE_WRITE: "SC05",
        RuleType.UNINITIALIZED_PROXY: "SC10",
        RuleType.INTEGER_OVERFLOW: "SC04",
        RuleType.INTEGER_UNDERFLOW: "SC04",
        RuleType.UNCHECKED_CALL: "SC06",
        RuleType.TX_ORIGIN: "SC11",
        RuleType.TIMESTAMP_DEPENDENCE: "SC12",
        RuleType.DENIAL_OF_SERVICE: "SC13",
        RuleType.FRONT_RUNNING: "SC14",
        RuleType.ARBITRARY_STORAGE_READ: "SC05",
        RuleType.UNINITIALIZED_STORAGE: "SC05",
        RuleType.WEAK_RANDOMNESS: "SC15",
        RuleType.ASSERT_VIOLATION: "SC16",
        RuleType.GAS_OPTIMIZATION: "SC-GAS",
        RuleType.DEAD_CODE: "SC-STYLE-01",
        RuleType.STYLE: "SC-STYLE-02",
        RuleType.OTHER: "SC-OTHER",
    }
)


_RULE_CATEGORY: Mapping[RuleType, RiskCategory] = MappingProxyType(
    {
        RuleType.REENTRANCY: RiskCategory.LOGIC,
        RuleType.ACCESS_CONTROL: RiskCategory.AUTHORIZATION,
        RuleType.DELEGATECALL: RiskCategory.LOGIC,
        RuleType.SELFDESTRUCT: RiskCategory.LOGIC,
        RuleType.ARBITRARY_STORAGE_WRITE: RiskCategory.STORAGE,
        RuleType.ARBITRARY_STORAGE_READ: RiskCategory.STORAGE,
        RuleType.UNINITIALIZED_STORAGE: RiskCategory.STORAGE,
        RuleType.UNINITIALIZED_PROXY: RiskCategory.AUTHORIZATION,
        RuleType.INTEGER_OVERFLOW: RiskCategory.ARITHMETIC,
        RuleType.INTEGER_UNDERFLOW: RiskCategory.ARITHMETIC,
        RuleType.UNCHECKED_CALL: RiskCategory.LOGIC,
        RuleType.TX_ORIGIN: RiskCategory.AUTHENTICATION,
        RuleType.TIMESTAMP_DEPENDENCE: RiskCategory.LOGIC,
        RuleType.DENIAL_OF_SERVICE: RiskCategory.LOGIC,
        RuleType.FRONT_RUNNING: RiskCategory.LOGIC,
        RuleType.WEAK_RANDOMNESS: RiskCategory.RANDOMNESS,
        RuleType.ASSERT_VIOLATION: RiskCategory.LOGIC,
        RuleType.GAS_OPTIMIZATION: RiskCategory.GAS,
        RuleType.DEAD_CODE: RiskCategory.STYLE,
        RuleType.STYLE: RiskCategory.STYLE,
        RuleType.OTHER: RiskCategory.OTHER,
    }
)


_DISPLAY_NAMES: Mapping[RuleType, str] = MappingProxyType(
    {
        RuleType.TX_ORIGIN: "TX Origin",
        RuleType.DENIAL_OF_SERVICE: "Denial of Service",
    }
)

@property
def has_classification(self) -> bool:
    return (
        self.cwe_id is not None
        or self.swc_id is not None
        or self.owasp_id is not None
    )