from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NormalizedCode:
    """
    Represents the canonical representation of source code.

    A NormalizedCode value object stores source code that has
    already been normalized and is suitable for deterministic
    comparison, fingerprint generation, and deduplication.

    The normalization process itself is performed by the
    CodeNormalizer domain service.
    """

    value: str

    def __post_init__(self) -> None:
        """
        Validate the integrity of the normalized code.
        """
        if not self.value.strip():
            raise ValueError(
                "Normalized code cannot be empty."
            )

        if self.value != self.value.strip():
            raise ValueError(
                "Normalized code must not contain leading "
                "or trailing whitespace."
            )

    @property
    def length(self) -> int:
        """
        Returns the length of the normalized code.
        """
        return len(self.value)

    def display(self) -> str:
        """
        Returns the normalized source code.
        """
        return self.value

    def __str__(self) -> str:
        """
        Returns the default string representation.
        """
        return self.display()