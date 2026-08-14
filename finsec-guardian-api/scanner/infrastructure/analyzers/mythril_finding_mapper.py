from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

from scanner.domain.entities.finding import Finding
from scanner.domain.enums import (
    AnalyzerType,
    Confidence,
    RiskLevel,
    Severity,
)
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.domain.value_objects.source_location import SourceLocation
from scanner.domain.value_objects.vulnerability_signature import (
    VulnerabilitySignature,
)


class MythrilFindingMapper:
    """
    Maps raw Mythril issue dictionaries into V2 domain Finding objects.

    The mapper performs structural translation only. It does not execute
    Mythril and does not persist anything.
    """

    _SEVERITY_MAP: dict[str, Severity] = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "informational": Severity.INFORMATIONAL,
        "info": Severity.INFORMATIONAL,
    }

    _CONFIDENCE_MAP: dict[Severity, Confidence] = {
        Severity.CRITICAL: Confidence.HIGH,
        Severity.HIGH: Confidence.HIGH,
        Severity.MEDIUM: Confidence.HIGH,
        Severity.LOW: Confidence.MEDIUM,
        Severity.INFORMATIONAL: Confidence.MEDIUM,
    }

    _RISK_MAP: dict[Severity, RiskLevel] = {
        Severity.CRITICAL: RiskLevel.CRITICAL,
        Severity.HIGH: RiskLevel.HIGH,
        Severity.MEDIUM: RiskLevel.MEDIUM,
        Severity.LOW: RiskLevel.LOW,
        Severity.INFORMATIONAL: RiskLevel.VERY_LOW,
    }

    @classmethod
    def map_all(
        cls,
        *,
        issues: Sequence[Mapping[str, Any]],
        request: AnalysisRequest,
    ) -> tuple[Finding, ...]:
        """
        Map all Mythril issues into domain findings.

        Malformed individual issues are skipped rather than preventing
        valid findings from being returned.
        """
        findings: list[Finding] = []

        for issue in issues:
            finding = cls.map_one(
                issue=issue,
                request=request,
            )

            if finding is not None:
                findings.append(finding)

        return tuple(findings)

    @classmethod
    def map_one(
        cls,
        *,
        issue: Mapping[str, Any],
        request: AnalysisRequest,
    ) -> Finding | None:
        """
        Map one Mythril issue into a domain Finding.

        Returns None for malformed issues that cannot provide enough
        information to construct a valid domain finding.
        """
        if not isinstance(issue, Mapping):
            return None

        title = cls._clean_text(
            issue.get("title"),
        )

        if not title:
            return None

        description = cls._build_description(
            issue,
        )

        recommendation = cls._build_recommendation(
            issue,
        )

        severity = cls._map_severity(
            issue.get("severity"),
        )

        confidence = cls._CONFIDENCE_MAP[
            severity
        ]

        risk_level = cls._RISK_MAP[
            severity
        ]

        swc_id = cls._normalise_optional_text(
            issue.get("swc_id"),
        )

        function_name = cls._normalise_optional_text(
            issue.get("function"),
        )

        line = cls._normalise_line(
            issue.get("lineno"),
        )

        location = SourceLocation(
            filename=request.source_filename or "contract.sol",
            line=line,
            column=None,
            end_line=line,
            end_column=None,
        )

        signature = cls._build_signature(
            request=request,
            issue=issue,
            title=title,
            function_name=function_name,
            line=line,
            swc_id=swc_id,
        )

        return Finding(
            title=title,
            description=description,
            recommendation=recommendation,
            severity=severity,
            confidence=confidence,
            risk_level=risk_level,
            analyzer=AnalyzerType.MYTHRIL,
            location=location,
            signature=signature,
            swc_id=swc_id,
        )

    # ==========================================================
    # Severity / classification
    # ==========================================================

    @classmethod
    def _map_severity(
        cls,
        raw_severity: Any,
    ) -> Severity:
        value = str(
            raw_severity or "medium"
        ).strip().lower()

        return cls._SEVERITY_MAP.get(
            value,
            Severity.MEDIUM,
        )

    # ==========================================================
    # Text handling
    # ==========================================================

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @classmethod
    def _normalise_optional_text(
        cls,
        value: Any,
    ) -> str | None:
        cleaned = cls._clean_text(value)
        return cleaned or None

    # ==========================================================
    # Location
    # ==========================================================

    @staticmethod
    def _normalise_line(
        value: Any,
    ) -> int:
        """
        Mythril normally reports a source line number.

        Domain SourceLocation requires a positive line number, so
        malformed or missing values are normalised to line 1.
        """
        try:
            line = int(value)
        except (TypeError, ValueError):
            return 1

        return max(1, line)

    # ==========================================================
    # Description / recommendation
    # ==========================================================

    @classmethod
    def _build_description(
        cls,
        issue: Mapping[str, Any],
    ) -> str:
        long_description = cls._clean_text(
            issue.get("description_long"),
        )

        short_description = cls._clean_text(
            issue.get("description_short"),
        )

        if long_description:
            return long_description

        if short_description:
            return short_description

        title = cls._clean_text(
            issue.get("title"),
        )

        return (
            f"Mythril identified a potential vulnerability: "
            f"{title}."
        )

    @classmethod
    def _build_recommendation(
        cls,
        issue: Mapping[str, Any],
    ) -> str:
        """
        Mythril does not currently provide a dedicated remediation
        field through the runner, so produce a conservative generic
        recommendation tied to the detected issue.
        """
        title = cls._clean_text(
            issue.get("title"),
        )

        swc_id = cls._normalise_optional_text(
            issue.get("swc_id"),
        )

        if swc_id:
            return (
                f"Review and remediate the `{title}` finding "
                f"associated with {swc_id}. Confirm the affected "
                "execution path and apply the appropriate defensive "
                "pattern."
            )

        return (
            f"Review and remediate the `{title}` finding. "
            "Confirm the affected execution path and apply the "
            "appropriate defensive pattern."
        )

    # ==========================================================
    # Fingerprinting
    # ==========================================================

    @staticmethod
    def _build_signature(
        *,
        request: AnalysisRequest,
        issue: Mapping[str, Any],
        title: str,
        function_name: str | None,
        line: int,
        swc_id: str | None,
    ) -> VulnerabilitySignature:
        """
        Build a deterministic analyzer-independent fingerprint input.

        Source code is intentionally not included in full because a
        stable source hash already exists at the SmartContract level.
        """
        source_hash = (
            hashlib.sha256(
                request.source_code.encode("utf-8"),
            ).hexdigest()
        )

        code = str(
            issue.get("code") or ""
        ).strip()

        material = "|".join(
            [
                AnalyzerType.MYTHRIL.value,
                source_hash,
                swc_id or "",
                title.lower(),
                function_name or "",
                str(line),
                code,
            ]
        )

        digest = hashlib.sha256(
            material.encode("utf-8"),
        ).hexdigest()

        return VulnerabilitySignature(
            digest,
        )