from __future__ import annotations

from dataclasses import dataclass

from scanner.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """
    Immutable result produced by a source-code normalizer.

    A NormalizationResult represents the canonical source code generated
    during normalization together with metadata describing the
    normalization process.

    Instances are immutable to guarantee deterministic behaviour
    throughout the fingerprinting pipeline.
    """

    normalized_code: str
    comments_removed: int = 0

    def __post_init__(self) -> None:
        """
        Validate the normalization result.
        """
        if not isinstance(self.normalized_code, str):
            raise DomainValidationError(
                "normalized_code must be a string."
            )

        if not self.normalized_code.strip():
            raise DomainValidationError(
                "normalized_code cannot be empty."
            )

        if not isinstance(self.comments_removed, int):
            raise DomainValidationError(
                "comments_removed must be an integer."
            )

        if self.comments_removed < 0:
            raise DomainValidationError(
                "comments_removed cannot be negative."
            )

    # ==========================================================
    # Derived Properties
    # ==========================================================

    @property
    def has_comments_removed(self) -> bool:
        """
        Return True if one or more comments were removed during
        normalization.
        """
        return self.comments_removed > 0

    @property
    def line_count(self) -> int:
        """
        Return the number of lines in the normalized source code.
        """
        return len(self.normalized_code.splitlines())

    @property
    def character_count(self) -> int:
        """
        Return the number of characters in the normalized source code.
        """
        return len(self.normalized_code)

    # ==========================================================
    # Dunder Methods
    # ==========================================================

    def __len__(self) -> int:
        """
        Return the length of the normalized source code.
        """
        return self.character_count

    def __str__(self) -> str:
        """
        Return the normalized source code.
        """
        return self.normalized_code