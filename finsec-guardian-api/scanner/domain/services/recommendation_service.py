from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Sequence

from scanner.domain.catalogs import RECOMMENDATION_CATALOG
from scanner.domain.entities import Finding, Recommendation
from scanner.domain.enums import RuleType
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects import RecommendationTemplate

if TYPE_CHECKING:
    from scanner.domain.entities import Scan


class RecommendationService:
    """
    Stateless domain service responsible for generating canonical
    remediation recommendations from scan findings.

    Multiple findings sharing the same RuleType are collapsed into a
    single Recommendation entity containing all affected finding IDs.
    """

    @classmethod
    def generate(
        cls,
        findings: Sequence[Finding],
    ) -> tuple[Recommendation, ...]:
        """
        Generate deterministic remediation recommendations from findings.
        """
        if not findings:
            return ()

        recommendations: list[Recommendation] = []

        for rule_type, findings_for_rule in cls._group_by_rule_type(findings).items():

            template = cls._template_for(rule_type)

            recommendation = Recommendation.from_template(
                template=template,
                rule_type=rule_type,
                finding_ids=(
                    finding.id
                    for finding in findings_for_rule
                ),
            )

            recommendations.append(recommendation)

        recommendations.sort(
            key=lambda recommendation: (
                -recommendation.priority.weight,
                recommendation.effort.weight,
                recommendation.template_identifier,
            )
        )

        return tuple(recommendations)

    @classmethod
    def generate_for_scan(
        cls,
        scan: Scan,
    ) -> tuple[Recommendation, ...]:
        """
        Generate recommendations directly from a Scan aggregate.
        """
        if scan is None:
            raise DomainValidationError(
                "scan cannot be None."
            )

        return cls.generate(scan.findings)

    @staticmethod
    def _group_by_rule_type(
        findings: Sequence[Finding],
    ) -> dict[RuleType, list[Finding]]:
        """
        Group findings by RuleType so that multiple findings sharing the
        same vulnerability produce a single recommendation.
        """
        grouped: dict[RuleType, list[Finding]] = defaultdict(list)

        for finding in findings:
            grouped[finding.rule_type].append(finding)

        return dict(grouped)

    @staticmethod
    def _template_for(
        rule_type: RuleType,
    ) -> RecommendationTemplate:
        """
        Retrieve the registered RecommendationTemplate for a RuleType.
        """
        try:
            return RECOMMENDATION_CATALOG[rule_type]

        except KeyError as exc:
            raise DomainValidationError(
                f"No recommendation template registered for "
                f"{rule_type.name}."
            ) from exc