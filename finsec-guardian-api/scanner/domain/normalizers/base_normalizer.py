from __future__ import annotations

import re
import unicodedata
from abc import ABC, abstractmethod

from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.normalization_options import (
    NormalizationOptions,
)
from scanner.domain.value_objects.normalization_result import (
    NormalizationResult,
)

# Collapse three or more consecutive newlines into a single blank line.
_BLANK_LINES = re.compile(r"\n{3,}")


class BaseNormalizer(ABC):
    """
    Abstract base class for deterministic source-code normalizers.

    The BaseNormalizer owns the language-independent normalization
    pipeline while delegating all language-specific lexical processing to
    concrete subclasses.

    The normalization pipeline is intentionally deterministic to ensure
    that semantically equivalent source code always produces the same
    canonical representation for fingerprint generation.

    Pipeline

        1. Validate input.
        2. Normalize Unicode (NFC).
        3. Normalize line endings.
        4. Expand tabs.
        5. Perform language-specific normalization.
        6. Collapse excessive blank lines.
        7. Produce a NormalizationResult.

    Operations requiring lexical awareness (for example, comment removal,
    string literal preservation, URI preservation and whitespace
    normalization outside literals) are delegated entirely to the
    language-specific normalizer.
    """

    def __init__(
        self,
        options: NormalizationOptions | None = None,
    ) -> None:
        self._options = (
            options
            if options is not None
            else NormalizationOptions.fingerprinting()
        )

    @property
    def options(self) -> NormalizationOptions:
        """
        Immutable normalization configuration.
        """
        return self._options

    # ==========================================================
    # Public API
    # ==========================================================

    def normalize(
        self,
        source_code: str,
    ) -> NormalizationResult:
        """
        Normalize source code into its canonical representation.
        """
        self._validate_source(source_code)

        normalized = source_code

        if self.options.normalize_unicode:
            normalized = self._normalize_unicode(normalized)

        if self.options.normalize_line_endings:
            normalized = self._normalize_line_endings(normalized)

        if self.options.normalize_tabs:
            normalized = self._normalize_tabs(normalized)

        normalized, comments_removed = (
            self._normalize_language(normalized)
        )

        if self.options.collapse_blank_lines:
            normalized = self._collapse_blank_lines(normalized)

        return NormalizationResult(
            normalized_code=normalized,
            comments_removed=comments_removed,
        )

    # ==========================================================
    # Language-Specific Operations
    # ==========================================================

    @abstractmethod
    def _normalize_language(
        self,
        source_code: str,
    ) -> tuple[str, int]:
        """
        Perform language-specific lexical normalization.

        Implementations are responsible for all operations requiring
        lexical awareness, including:

        - removing comments;
        - preserving string literals;
        - preserving escape sequences;
        - preserving URIs;
        - normalizing whitespace outside literals;
        - counting removed comments.

        Returns:
            Tuple containing:

            - normalized source code;
            - number of comments removed.
        """
        raise NotImplementedError

    # ==========================================================
    # Validation
    # ==========================================================

    @staticmethod
    def _validate_source(
        source_code: str,
    ) -> None:
        """
        Validate normalization input.
        """
        if not isinstance(source_code, str):
            raise DomainValidationError(
                "Source code must be a string."
            )

        if not source_code.strip():
            raise DomainValidationError(
                "Source code cannot be empty."
            )

    # ==========================================================
    # Language-Independent Normalization
    # ==========================================================

    @staticmethod
    def _normalize_unicode(
        source_code: str,
    ) -> str:
        """
        Normalize Unicode into NFC form.
        """
        return unicodedata.normalize(
            "NFC",
            source_code,
        )

    @staticmethod
    def _normalize_line_endings(
        source_code: str,
    ) -> str:
        """
        Convert all line endings to LF.
        """
        return (
            source_code
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )

    @staticmethod
    def _normalize_tabs(
        source_code: str,
    ) -> str:
        """
        Expand tab characters into four spaces.
        """
        return source_code.expandtabs(4)

    @staticmethod
    def _collapse_blank_lines(
        source_code: str,
    ) -> str:
        """
        Collapse runs of blank lines.

        Three or more consecutive newline characters become
        exactly two, preserving a single blank line while
        eliminating excessive vertical whitespace.
        """
        return _BLANK_LINES.sub(
            "\n\n",
            source_code,
        )