from __future__ import annotations

import hashlib

from scanner.domain.enums import Severity


class FingerprintService:
    """
    Domain service responsible for generating deterministic fingerprints
    for findings.

    Fingerprints uniquely identify a finding based on the attributes that
    define its semantic meaning rather than its database identity.

    Two findings describing the same issue should always produce the same
    fingerprint regardless of when or where they were created.
    """

    @staticmethod
    def generate(
        *,
        detector: str,
        title: str,
        severity: Severity | str,
        file_path: str,
        line: int,
    ) -> str:
        """
        Generate a deterministic SHA-256 fingerprint.

        Parameters
        ----------
        detector:
            Name of the analyzer or detector.

        title:
            Finding title.

        severity:
            Finding severity.

        file_path:
            Source file containing the issue.

        line:
            Line number where the issue occurs.
        """

        severity_value = (
            severity.value
            if isinstance(severity, Severity)
            else str(severity)
        )

        normalized = (
            detector.strip().lower(),
            title.strip().lower(),
            severity_value.strip().lower(),
            file_path.strip().replace("\\", "/").lower(),
            str(line),
        )

        payload = "|".join(normalized)

        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def matches(
        fingerprint: str,
        *,
        detector: str,
        title: str,
        severity: Severity | str,
        file_path: str,
        line: int,
    ) -> bool:
        """
        Verify that a fingerprint matches the supplied attributes.
        """
        return fingerprint == FingerprintService.generate(
            detector=detector,
            title=title,
            severity=severity,
            file_path=file_path,
            line=line,
        )