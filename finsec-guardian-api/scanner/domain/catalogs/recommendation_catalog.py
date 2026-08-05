from __future__ import annotations

from collections.abc import Mapping
from typing import Final
from types import MappingProxyType

from scanner.domain.enums import (
    AnalyzerType,
    RecommendationPriority,
    RemediationEffort,
)
from scanner.domain.value_objects.recommendation_template import (
    RecommendationTemplate,
)

"""
Canonical remediation knowledge base.

This catalog contains immutable remediation guidance used by the
RecommendationService to translate Findings into actionable
Recommendations.

The catalog intentionally contains no business logic.
"""


RECOMMENDATION_CATALOG: Final[
    Mapping[AnalyzerType, RecommendationTemplate]
] = MappingProxyType(
    {
        AnalyzerType.REENTRANCY: RecommendationTemplate(
            identifier="reentrancy",
            title="Protect Against Reentrancy",
            description=(
                "The contract performs external calls before completing "
                "internal state updates, allowing recursive execution."
            ),
            remediation=(
                "Apply the Checks-Effects-Interactions pattern, "
                "update state before external calls, and consider "
                "using OpenZeppelin ReentrancyGuard."
            ),
            priority=RecommendationPriority.HIGH,
            effort=RemediationEffort.MEDIUM,
            cwe="CWE-841",
            swc="SWC-107",
            owasp="SC05",
            references=(
                "https://swcregistry.io/docs/SWC-107",
                "https://docs.openzeppelin.com/contracts/security",
            ),
            tags=(
                "reentrancy",
                "external-calls",
                "security",
            ),
            requires_manual_review=True,
            automation_available=False,
            estimated_fix_hours=6.0,
        ),

        AnalyzerType.ACCESS_CONTROL: RecommendationTemplate(
            identifier="access-control",
            title="Implement Proper Access Control",
            description=(
                "Critical functionality is not adequately protected "
                "by authorization checks."
            ),
            remediation=(
                "Restrict privileged operations using ownership, "
                "role-based access control, or capability-based authorization."
            ),
            priority=RecommendationPriority.HIGH,
            effort=RemediationEffort.LOW,
            cwe="CWE-284",
            swc="SWC-105",
            owasp="SC01",
            references=(
                "https://swcregistry.io/docs/SWC-105",
                "https://docs.openzeppelin.com/contracts/access-control",
            ),
            tags=(
                "authorization",
                "roles",
                "ownership",
            ),
            automation_available=True,
            estimated_fix_hours=2.0,
        ),

        AnalyzerType.INTEGER_OVERFLOW: RecommendationTemplate(
            identifier="integer-overflow",
            title="Prevent Integer Overflow and Underflow",
            description=(
                "Arithmetic operations may overflow or underflow."
            ),
            remediation=(
                "Use Solidity 0.8+ built-in overflow protection or "
                "SafeCast where explicit casting is required."
            ),
            priority=RecommendationPriority.HIGH,
            effort=RemediationEffort.LOW,
            cwe="CWE-190",
            swc="SWC-101",
            owasp="SC08",
            references=(
                "https://swcregistry.io/docs/SWC-101",
            ),
            tags=(
                "overflow",
                "underflow",
                "arithmetic",
            ),
            automation_available=True,
            estimated_fix_hours=1.5,
        ),

        AnalyzerType.TIMESTAMP_DEPENDENCE: RecommendationTemplate(
            identifier="timestamp-dependence",
            title="Avoid Timestamp Dependence",
            description=(
                "Business logic depends on block timestamps, which can "
                "be manipulated within protocol limits."
            ),
            remediation=(
                "Avoid using block.timestamp for critical security "
                "decisions or randomness."
            ),
            priority=RecommendationPriority.MEDIUM,
            effort=RemediationEffort.LOW,
            swc="SWC-116",
            references=(
                "https://swcregistry.io/docs/SWC-116",
            ),
            tags=(
                "timestamp",
                "blockchain",
            ),
            automation_available=False,
            estimated_fix_hours=2.0,
        ),

        AnalyzerType.DENIAL_OF_SERVICE: RecommendationTemplate(
            identifier="denial-of-service",
            title="Prevent Denial of Service",
            description=(
                "Contract execution may become unavailable due to "
                "unbounded operations or failing external interactions."
            ),
            remediation=(
                "Avoid unbounded loops, prefer pull-based payments, "
                "and isolate failure-prone external calls."
            ),
            priority=RecommendationPriority.HIGH,
            effort=RemediationEffort.MEDIUM,
            swc="SWC-113",
            references=(
                "https://swcregistry.io/docs/SWC-113",
            ),
            tags=(
                "availability",
                "dos",
            ),
            requires_manual_review=True,
            automation_available=False,
            estimated_fix_hours=5.0,
        ),
    }
)


def get_template(
    analyzer: AnalyzerType,
) -> RecommendationTemplate | None:
    """
    Return the canonical recommendation template associated with an analyzer.

    Returns:
        RecommendationTemplate if one exists, otherwise None.
    """
    return RECOMMENDATION_CATALOG.get(analyzer)