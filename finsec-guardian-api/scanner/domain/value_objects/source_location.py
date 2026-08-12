from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering

from scanner.domain.exceptions.domain import DomainValidationError


@total_ordering
@dataclass(frozen=True, slots=True)
class SourceLocation:
    """
    Immutable Value Object representing the physical location of a
    finding within a source file.

    Examples:
        Token.sol:15
        Token.sol:15:8
        Token.sol:15-20
        Token.sol:15:8-20:4
    """

    filename: str
    line: int
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        """
        Validate the integrity of the source location.
        """

        # ==========================================================
        # Filename
        # ==========================================================

        if not isinstance(self.filename, str):
            raise DomainValidationError(
                "Filename must be a string."
            )

        filename = self.filename.strip()

        if not filename:
            raise DomainValidationError(
                "Filename cannot be empty."
            )

        object.__setattr__(
            self,
            "filename",
            filename,
        )

        # ==========================================================
        # Line
        # ==========================================================

        self._validate_positive_integer(
            self.line,
            "Line number",
        )

        # ==========================================================
        # Column
        # ==========================================================

        if self.column is not None:
            self._validate_positive_integer(
                self.column,
                "Column number",
            )

        # ==========================================================
        # End Line
        # ==========================================================

        if self.end_line is not None:
            self._validate_positive_integer(
                self.end_line,
                "End line",
            )

            if self.end_line < self.line:
                raise DomainValidationError(
                    "End line cannot be less than the starting line."
                )

        # ==========================================================
        # End Column
        # ==========================================================

        if self.end_column is not None:
            self._validate_positive_integer(
                self.end_column,
                "End column",
            )

            if self.column is None:
                raise DomainValidationError(
                    "end_column requires column to be set."
                )

        # ==========================================================
        # Same-line Column Ordering
        # ==========================================================

        if (
            self.end_column is not None
            and self.column is not None
            and (
                self.end_line is None
                or self.end_line == self.line
            )
            and self.end_column < self.column
        ):
            raise DomainValidationError(
                "End column cannot be less than the starting "
                "column on the same line."
            )

    # ==========================================================
    # Validation Helpers
    # ==========================================================

    @staticmethod
    def _validate_positive_integer(
        value: object,
        field_name: str,
    ) -> None:
        """
        Validate a positive integer value.

        bool is explicitly rejected because bool is a subclass
        of int in Python.
        """
        if isinstance(value, bool) or not isinstance(value, int):
            raise DomainValidationError(
                f"{field_name} must be an integer."
            )

        if value < 1:
            raise DomainValidationError(
                f"{field_name} must be greater than zero."
            )

    # ==========================================================
    # Availability
    # ==========================================================

    @property
    def has_column(self) -> bool:
        """
        Return True when column information is available.
        """
        return self.column is not None

    @property
    def has_end_position(self) -> bool:
        """
        Return True when an explicit end position is available.
        """
        return (
            self.end_line is not None
            or self.end_column is not None
        )

    # ==========================================================
    # Range Properties
    # ==========================================================

    @property
    def is_single_line(self) -> bool:
        """
        Return True when the location spans one source line.
        """
        return (
            self.end_line is None
            or self.end_line == self.line
        )

    @property
    def is_range(self) -> bool:
        """
        Return True when the location spans multiple lines.
        """
        return not self.is_single_line

    @property
    def effective_end_line(self) -> int:
        """
        Return the effective ending line.

        When no explicit end line is supplied, the starting
        line is treated as the ending line.
        """
        return self.end_line or self.line

    @property
    def effective_end_column(self) -> int | None:
        """
        Return the effective ending column.

        When no explicit end column is supplied, the starting
        column is used when available.
        """
        if self.column is None:
            return None

        return self.end_column or self.column

    @property
    def span(self) -> int:
        """
        Return the number of source lines covered.
        """
        return (
            self.effective_end_line
            - self.line
            + 1
        )

    # ==========================================================
    # Domain Queries
    # ==========================================================

    def contains(
        self,
        line: int,
        column: int | None = None,
    ) -> bool:
        """
        Return True if the supplied position lies within
        this source location.
        """
        if not isinstance(line, int) or isinstance(line, bool):
            return False

        if column is not None and (
            not isinstance(column, int)
            or isinstance(column, bool)
        ):
            return False

        if not (
            self.line
            <= line
            <= self.effective_end_line
        ):
            return False

        if column is None:
            return True

        if self.column is None:
            return True

        if (
            line == self.line
            and column < self.column
        ):
            return False

        if (
            line == self.effective_end_line
            and self.end_column is not None
            and column > self.end_column
        ):
            return False

        return True

    # ==========================================================
    # Presentation
    # ==========================================================

    def display(self) -> str:
        """
        Return a human-readable representation.

        Examples:
            Token.sol:15
            Token.sol:15:8
            Token.sol:15-20
            Token.sol:15:8-20:4
        """
        if self.end_line is None:
            if self.column is None:
                return f"{self.filename}:{self.line}"

            return (
                f"{self.filename}:"
                f"{self.line}:"
                f"{self.column}"
            )

        if self.column is None:
            return (
                f"{self.filename}:"
                f"{self.line}-"
                f"{self.end_line}"
            )

        return (
            f"{self.filename}:"
            f"{self.line}:"
            f"{self.column}-"
            f"{self.end_line}:"
            f"{self.effective_end_column}"
        )

    # ==========================================================
    # Ordering
    # ==========================================================

    def _sort_key(self) -> tuple[str, int, int]:
        """
        Return the natural ordering key:

            1. filename
            2. line
            3. column
        """
        return (
            self.filename,
            self.line,
            self.column or 0,
        )

    def __lt__(
        self,
        other: object,
    ) -> bool:
        """
        Compare source locations deterministically.
        """
        if not isinstance(other, SourceLocation):
            return NotImplemented

        return self._sort_key() < other._sort_key()

    # ==========================================================
    # String Representation
    # ==========================================================

    def __str__(self) -> str:
        return self.display()