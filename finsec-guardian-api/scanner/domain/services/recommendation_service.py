from __future__ import annotations

from collections.abc import Iterable

from scanner.domain.catalogs import RECOMMENDATION_CATALOG
from scanner.domain.entities import Finding, Recommendation
from scanner.domain.enums import RuleType
from scanner.domain.value_objects import RecommendationTemplate

class RecommendationService:
    """
    Stateless domain service responsible for generating canonical
    remediation recommendations from security findings.

    The service performs no I/O and contains no remediation knowledge.
    It simply orchestrates transformation from Findings to
    Recommendations using the Recommendation Catalog.
    """

    @classmethod
    def generate(
        cls,
        findings: tuple[Finding, ...],
    ) -> tuple[Recommendation, ...]:
        """
        Generate unique recommendations for a collection of findings.
        """
        raise NotImplementedError

    recommedations = [
    for each finding in findings:
        determine the rule type of the finding

        look up the recommendation template in the RECOMMENDATION_CATALOG using the rule type

        build a Recommendation object using the template and the finding's details  

    ]
_template_for (rule_type: RuleType) -> RecommendationTemplate: