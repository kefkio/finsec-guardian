from enum import Enum
from typing import TypeVar


T = TypeVar("T", bound="DomainEnum")


class DomainEnum(str, Enum):
    """
    Base class for all domain enumerations.

    Provides common functionality shared across all enums in the
    domain layer, including string conversion, display formatting,
    and case-insensitive parsing.
    """

    @property
    def display_name(self) -> str:
        """
        Returns a human-readable representation.

        Example:
            "very_high" -> "Very High"
        """
        return self.value.replace("_", " ").title()

    @classmethod
    def from_string(cls: type[T], value: str) -> T:
        """
        Creates an enum instance from a string.

        Parsing is case-insensitive and ignores leading/trailing
        whitespace.

        Raises:
            ValueError:
                If the supplied value is not valid.
        """
        normalized = value.strip().lower()

        try:
            return cls(normalized)

        except ValueError as exc:
            valid = ", ".join(member.value for member in cls)

            raise ValueError(
                f"Invalid {cls.__name__}: '{value}'. "
                f"Expected one of: {valid}."
            ) from exc

    def __str__(self) -> str:
        """
        Returns the enum's underlying value.
        """
        return self.value