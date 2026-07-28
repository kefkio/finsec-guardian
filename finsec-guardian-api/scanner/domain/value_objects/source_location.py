from dataclasses import dataclass
from functools import total_ordering
from typing import Optional

from scanner.domain.exceptions.domain import DomainValidationError


@total_ordering
@dataclass(frozen=True, slots=True)
class SourceLocation:
    """
    Represents the physical location of a finding within a source file.

    A SourceLocation is a Domain Value Object. It is immutable and
    completely defined by its values rather than an identity.

    Examples:
        Token.sol:15
        Token.sol:15:8
        Token.sol:15-20
        Token.sol:15:8-20:4
    """

    filename: str
    line: int
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def __post_init__(self) -> None:
        """
        Validates the integrity of the source location.

        Raises:
            DomainValidationError:
                If any invariant is violated.
        """
        if not self.filename.strip():
            raise DomainValidationError(
                "Filename cannot be empty."
            )

        if self.line < 1:
            raise DomainValidationError(
                "Line number must be greater than zero."
            )

        if self.column is not None and self.column < 1:
            raise DomainValidationError(
                "Column number must be greater than zero."
            )

        if self.end_line is not None and self.end_line < self.line:
            raise DomainValidationError(
                "End line cannot be less than the starting line."
            )

        if self.end_column is not None and self.end_column < 1:
            raise DomainValidationError(
                "End column must be greater than zero."
            )

        if self.end_column is not None and self.column is None:
            raise DomainValidationError(
                "end_column requires column to be set."
            )

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
                "End column cannot be less than the starting column "
                "on the same line."
            )

    @property
    def has_column(self) -> bool:
        """
        Returns True if column information is available.
        """
        return self.column is not None

    @property
    def is_single_line(self) -> bool:
        """
        Returns True if the location spans only one line.
        """
        return (
            self.end_line is None
            or self.end_line == self.line
        )

    @property
    def is_range(self) -> bool:
        """
        Returns True if this location spans multiple lines.
        """
        return not self.is_single_line

    @property
    def effective_end_line(self) -> int:
        """
        Returns the effective ending line.
        """
        return self.end_line or self.line

    @property
    def effective_end_column(self) -> Optional[int]:
        """
        Returns the effective ending column.
        """
        if self.column is None:
            return None

        return self.end_column or self.column

    @property
    def span(self) -> int:
        """
        Returns the number of lines covered by this location.
        """
        return self.effective_end_line - self.line + 1

    def contains(
        self,
        line: int,
        column: Optional[int] = None,
    ) -> bool:
        """
        Returns True if the supplied line (and optional column)
        lies within this source location.
        """
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

    def display(self) -> str:
        """
        Returns a human-readable representation.

        Examples:
            Token.sol:15
            Token.sol:15:8
            Token.sol:15-20
            Token.sol:15:8-20:4
        """
        if self.end_line is None:

            if self.column is None:
                return (
                    f"{self.filename}:{self.line}"
                )

            return (
                f"{self.filename}:"
                f"{self.line}:{self.column}"
            )

        if self.column is None:
            return (
                f"{self.filename}:"
                f"{self.line}-{self.end_line}"
            )

        return (
            f"{self.filename}:"
            f"{self.line}:{self.column}-"
            f"{self.end_line}:"
            f"{self.effective_end_column}"
        )

    def _sort_key(self) -> tuple[str, int, int]:
        """
        Returns the natural ordering key.

        Source locations are ordered by:
            1. Filename
            2. Line
            3. Column
        """
        return (
            self.filename,
            self.line,
            self.column or 0,
        )

    def __lt__(self, other: "SourceLocation") -> bool:
        """
        Compares two SourceLocation objects.
        """
        if not isinstance(other, SourceLocation):
            return NotImplemented

        return (
            self._sort_key()
            < other._sort_key()
        )

    def __str__(self) -> str:
        """
        Returns the display representation.
        """
        return self.display()