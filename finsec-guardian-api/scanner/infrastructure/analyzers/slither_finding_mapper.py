
from __future__ import annotations

from collections.abc import Iterable, Mapping


from scanner.domain.entities import Finding
from scanner.domain.enums import (
    AnalyzerType,
    Confidence,
    RiskLevel,
    Severity,
)
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.services.fingerprint_service import FingerprintService
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.domain.value_objects.source_location import SourceLocation


class SlitherFindingMapper:
    """
    Infrastructure mapper converting Slither detector output into
    domain Finding entities.

    Responsibilities:
        - Map Slither impact to Severity.
        - Map Slither confidence to Confidence.
        - Derive RiskLevel from Severity.
        - Construct SourceLocation.
        - Generate a VulnerabilitySignature through FingerprintService.
        - Preserve Slither-specific identifiers such as SWC IDs.

    This class does not execute Slither and does not persist findings.
    """

    DEFAULT_FILENAME = "contract.sol"
    DEFAULT_CONFIDENCE = Confidence.LOW

    _SEVERITY_MAP = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "informational": Severity.INFORMATIONAL,
        "info": Severity.INFORMATIONAL,
    }

    _CONFIDENCE_MAP = {
        "high": Confidence.HIGH,
        "medium": Confidence.MEDIUM,
        "low": Confidence.LOW,
    }

    @classmethod
    def map_all(
        cls,
        detectors: Iterable[Mapping[str, object]],
        request: AnalysisRequest,
    ) -> tuple[Finding, ...]:
        """
        Convert an iterable of Slither detector dictionaries into
        immutable result collection semantics.
        """
        findings: list[Finding] = []

        for index, detector in enumerate(detectors, start=1):
            try:
                findings.append(
                    cls.map_detector(
                        detector=detector,
                        request=request,
                    )
                )
            except DomainValidationError as exc:
                raise DomainValidationError(
                    f"Failed to map Slither detector #{index}: {exc}"
                ) from exc

        return tuple(findings)

    @classmethod
    def map_detector(
        cls,
        detector: Mapping[str, object],
        request: AnalysisRequest,
    ) -> Finding:
        """
        Convert one Slither detector result into a domain Finding.
        """
        if not isinstance(detector, Mapping):
            raise DomainValidationError(
                "Slither detector must be a mapping."
            )

        if not isinstance(request, AnalysisRequest):
            raise DomainValidationError(
                "request must be an AnalysisRequest."
            )

        title = cls._title(detector)
        description = cls._description(detector)
        recommendation = cls._recommendation(
            detector=detector,
            title=title,
        )

        severity = cls._severity(detector)
        confidence = cls._confidence(detector)
        risk_level = RiskLevel.from_severity(severity)

        location = cls._location(
            detector=detector,
            request=request,
        )

        analyzer = AnalyzerType.SLITHER

        signature = FingerprintService.generate(
            analyzer=AnalyzerType.SLITHER,
            title=title,
            location=location,
        )

        return Finding(
            title=title,
            description=description,
            recommendation=recommendation,
            severity=severity,
            confidence=confidence,
            risk_level=risk_level,
            analyzer=analyzer,
            location=location,
            signature=signature,
            swc_id=cls._optional_string(
                detector.get("swc-id")
            ),
        )

    # ==========================================================
    # Text Mapping
    # ==========================================================

    @classmethod
    def _title(
        cls,
        detector: Mapping[str, object],
    ) -> str:
        value = detector.get("check")

        if not isinstance(value, str) or not value.strip():
            return "Slither Finding"

        return value.strip()

    @classmethod
    def _description(
        cls,
        detector: Mapping[str, object],
    ) -> str:
        value = detector.get("description")

        if not isinstance(value, str):
            raise DomainValidationError(
                "Slither detector description must be a string."
            )

        description = value.strip()

        if not description:
            description = "Slither reported a potential security issue."

        return description

    @classmethod
    def _recommendation(
    cls,
    *,
    detector: Mapping[str, object],
    title: str,
    ) -> str:
        markdown = detector.get("markdown")

        if isinstance(markdown, str) and markdown.strip():
            return markdown.strip()

        return (
            f"Review and remediate the identified issue: {title}."
    )

    # ==========================================================
    # Classification Mapping
    # ==========================================================

    @classmethod
    def _severity(
        cls,
        detector: Mapping[str, object],
    ) -> Severity:
        value = detector.get("impact")

        if not isinstance(value, str):
            raise DomainValidationError(
                "Slither detector impact must be a string."
            )

        normalized = value.strip().lower()

        try:
            return cls._SEVERITY_MAP[normalized]
        except KeyError as exc:
            raise DomainValidationError(
                f"Unsupported Slither impact: {value!r}."
            ) from exc

    @classmethod
    def _confidence(
        cls,
        detector: Mapping[str, object],
    ) -> Confidence:
        value = detector.get("confidence")

        # Slither may omit confidence in some output forms.
        if value is None:
            return cls.DEFAULT_CONFIDENCE

        if not isinstance(value, str):
            raise DomainValidationError(
                "Slither detector confidence must be a string."
            )

        normalized = value.strip().lower()

        if not normalized:
            return cls.DEFAULT_CONFIDENCE

        try:
            return cls._CONFIDENCE_MAP[normalized]
        except KeyError as exc:
            raise DomainValidationError(
                f"Unsupported Slither confidence: {value!r}."
            ) from exc

    # ==========================================================
    # Location Mapping
    # ==========================================================

    @classmethod
    def _location(
        cls,
        *,
        detector: Mapping[str, object],
        request: AnalysisRequest,
    ) -> SourceLocation:
        mapping = cls._extract_source_mapping(detector)

        filename = cls._filename(
            mapping=mapping,
            request=request,
        )

        line = cls._first_line(mapping)

        column = cls._optional_positive_int(
            mapping.get("starting_column")
        )

        end_column = cls._optional_positive_int(
            mapping.get("ending_column")
        )

        if end_column is not None and column is None:
            end_column = None

        end_line = cls._last_line(mapping)

        if end_line is not None and end_line < line:
            end_line = line

        return SourceLocation(
            filename=filename,
            line=line,
            column=column,
            end_line=end_line,
            end_column=end_column,
        )

    @classmethod
    def _extract_source_mapping(
        cls,
        detector: Mapping[str, object],
    ) -> Mapping[str, object]:
        """
        Extract the first usable Slither source_mapping.

        Supports:
            detector["elements"][...]["source_mapping"]
            detector["locations"][...]["source_mapping"]
            detector["source_mapping"]
        """
        elements = detector.get("elements")

        if isinstance(elements, (list, tuple)):
            for element in elements:
                if not isinstance(element, Mapping):
                    continue

                source_mapping = element.get("source_mapping")

                if isinstance(source_mapping, Mapping):
                    return source_mapping

        locations = detector.get("locations")

        if isinstance(locations, (list, tuple)):
            for location in locations:
                if not isinstance(location, Mapping):
                    continue

                source_mapping = location.get("source_mapping")

                if isinstance(source_mapping, Mapping):
                    return source_mapping

        source_mapping = detector.get("source_mapping")

        if isinstance(source_mapping, Mapping):
            return source_mapping

        raise DomainValidationError(
            "Slither detector does not contain a valid source_mapping."
        )

    @classmethod
    def _filename(
        cls,
        *,
        mapping: Mapping[str, object],
        request: AnalysisRequest,
    ) -> str:
        for key in (
            "filename_short",
            "filename_relative",
            "filename_absolute",
            "filename",
        ):
            value = mapping.get(key)

            if isinstance(value, str) and value.strip():
                return value.strip()

        if request.source_filename:
            return request.source_filename

        return cls.DEFAULT_FILENAME

    @staticmethod
    def _first_line(
        mapping: Mapping[str, object],
    ) -> int:
        lines = mapping.get("lines")

        if isinstance(lines, (list, tuple)) and lines:
            first = lines[0]

            if isinstance(first, int) and not isinstance(first, bool):
                if first >= 1:
                    return first

        start_line = mapping.get("starting_line")

        if (
            isinstance(start_line, int)
            and not isinstance(start_line, bool)
            and start_line >= 1
        ):
            return start_line

        raise DomainValidationError(
            "Slither source_mapping does not contain a valid starting line."
        )

    @staticmethod
    def _last_line(
        mapping: Mapping[str, object],
    ) -> int | None:
        lines = mapping.get("lines")

        if isinstance(lines, (list, tuple)) and lines:
            last = lines[-1]

            if isinstance(last, int) and not isinstance(last, bool):
                if last >= 1:
                    return last

        end_line = mapping.get("ending_line")

        if (
            isinstance(end_line, int)
            and not isinstance(end_line, bool)
            and end_line >= 1
        ):
            return end_line

        return None

    @staticmethod
    def _optional_positive_int(
        value: object,
    ) -> int | None:
        if value is None:
            return None

        if isinstance(value, bool) or not isinstance(value, int):
            return None

        if value < 1:
            return None

        return value

    # ==========================================================
    # Generic Helpers
    # ==========================================================

    @staticmethod
    def _optional_string(
        value: object,
    ) -> str | None:
        if not isinstance(value, str):
            return None

        normalized = value.strip()

        return normalized or None