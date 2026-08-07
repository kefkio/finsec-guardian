from __future__ import annotations

import hashlib
from pathlib import PurePosixPath, PureWindowsPath
from typing import ClassVar

from scanner.domain.enums import AnalyzerType
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.correlation_component import (
    CorrelationComponent,
)
from scanner.domain.value_objects.source_location import SourceLocation
from scanner.domain.value_objects.vulnerability_signature import (
    VulnerabilitySignature,
)


class FingerprintService:
    """
    Domain service responsible for generating deterministic
    vulnerability fingerprints.

    A fingerprint identifies the semantic identity of a
    vulnerability rather than the identity of a Finding entity.

    Fingerprints are deterministic:
        - identical vulnerabilities always produce the same fingerprint
        - different vulnerabilities produce different fingerprints

    The fingerprint algorithm is versioned so future improvements
    (semantic fingerprints, AST fingerprints, etc.) can coexist
    without invalidating historical scan data.
    """

    ALGORITHM_VERSION: ClassVar[str] = "v1"

    _HASH_ALGORITHM: ClassVar[str] = "sha256"

    @classmethod
    def generate(
        cls,
        *,
        analyzer: AnalyzerType,
        title: str,
        location: SourceLocation,
    ) -> VulnerabilitySignature:
        """
        Generate a deterministic fingerprint for a vulnerability.
        """
        cls._validate_inputs(
            analyzer=analyzer,
            title=title,
            location=location,
        )

        payload = cls._build_payload(
            analyzer=analyzer,
            title=title,
            location=location,
        )

        digest = hashlib.new(
            cls._HASH_ALGORITHM,
            payload.encode("utf-8"),
        ).hexdigest()

        return VulnerabilitySignature(digest)

    @classmethod
    def matches(
        cls,
        fingerprint: VulnerabilitySignature,
        *,
        analyzer: AnalyzerType,
        title: str,
        location: SourceLocation,
    ) -> bool:
        """
        Determine whether a fingerprint matches the supplied
        vulnerability attributes.
        """
        if not isinstance(
            fingerprint,
            VulnerabilitySignature,
        ):
            raise DomainValidationError(
                "Fingerprint must be a VulnerabilitySignature."
            )

        return fingerprint == cls.generate(
            analyzer=analyzer,
            title=title,
            location=location,
        )

    @classmethod
    def algorithm_version(cls) -> str:
        """
        Return the currently active fingerprint algorithm version.
        """
        return cls.ALGORITHM_VERSION

    @classmethod
    def attack_path(cls, component: CorrelationComponent) -> str:
        """
        Generate a deterministic identifier for an attack path component.
        """
        if not isinstance(component, CorrelationComponent):
            raise DomainValidationError(
                "component must be a CorrelationComponent."
            )

        payload = "|".join(
            [
                cls.ALGORITHM_VERSION,
                "attack-path",
                str(component.node_count),
                str(component.edge_count),
                component.entry_finding_id.hex,
                *sorted(finding.id.hex for finding in component.findings),
            ]
        )

        return hashlib.new(
            cls._HASH_ALGORITHM,
            payload.encode("utf-8"),
        ).hexdigest()

    @classmethod
    def _build_payload(
        cls,
        *,
        analyzer: AnalyzerType,
        title: str,
        location: SourceLocation,
    ) -> str:
        """
        Construct the canonical payload used to generate the
        fingerprint.

        NOTE
        ----
        Version 1 intentionally includes physical line numbers.

        Future versions may replace this with semantic identifiers
        such as:

            • AST node
            • Function signature
            • Rule identifier
            • Normalized code fragment

        allowing fingerprints to survive source-code movement.
        """

        normalized_path = cls._normalize_path(
            location.filename
        )

        return "|".join(
            (
                cls.ALGORITHM_VERSION,
                analyzer.value.lower(),
                title.strip().lower(),
                normalized_path,
                str(location.line),
            )
        )

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize a source path so identical files generate
        identical fingerprints regardless of operating system.
        """

        if "\\" in path:
            normalized = PureWindowsPath(path).as_posix()
        else:
            normalized = PurePosixPath(path).as_posix()

        return (
            normalized
            .replace("//", "/")
            .lower()
            .lstrip("/")
        )

    @staticmethod
    def _validate_inputs(
        *,
        analyzer: AnalyzerType,
        title: str,
        location: SourceLocation,
    ) -> None:
        """
        Validate service inputs.
        """

        if not isinstance(
            analyzer,
            AnalyzerType,
        ):
            raise DomainValidationError(
                "Analyzer must be an AnalyzerType."
            )

        if not isinstance(
            location,
            SourceLocation,
        ):
            raise DomainValidationError(
                "Location must be a SourceLocation."
            )

        if not isinstance(
            title,
            str,
        ):
            raise DomainValidationError(
                "Title must be a string."
            )

        if not title.strip():
            raise DomainValidationError(
                "Title cannot be empty."
            )