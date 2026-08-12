from __future__ import annotations

import pytest

from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.source_location import SourceLocation


# ==========================================================
# Construction
# ==========================================================


def test_valid_source_location() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=15,
        column=8,
        end_line=20,
        end_column=4,
    )

    assert location.filename == "Token.sol"
    assert location.line == 15
    assert location.column == 8
    assert location.end_line == 20
    assert location.end_column == 4


def test_filename_is_stripped() -> None:
    location = SourceLocation(
        filename="  Token.sol  ",
        line=15,
    )

    assert location.filename == "Token.sol"


# ==========================================================
# Validation
# ==========================================================


@pytest.mark.parametrize(
    "filename",
    ["", "   ", None, 123],
)
def test_invalid_filename_is_rejected(filename) -> None:
    with pytest.raises(DomainValidationError):
        SourceLocation(
            filename=filename,
            line=1,
        )  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "line",
    [0, -1, None, "1", True],
)
def test_invalid_line_is_rejected(line) -> None:
    with pytest.raises(DomainValidationError):
        SourceLocation(
            filename="Token.sol",
            line=line,
        )  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "column",
    [0, -1, None],
)
def test_invalid_column_values_are_rejected(column) -> None:
    if column is None:
        location = SourceLocation(
            filename="Token.sol",
            line=1,
            column=None,
        )
        assert location.column is None
        return

    with pytest.raises(DomainValidationError):
        SourceLocation(
            filename="Token.sol",
            line=1,
            column=column,
        )


def test_boolean_column_is_rejected() -> None:
    with pytest.raises(DomainValidationError):
        SourceLocation(
            filename="Token.sol",
            line=1,
            column=True,
        )  # type: ignore[arg-type]


def test_end_line_cannot_precede_start_line() -> None:
    with pytest.raises(DomainValidationError):
        SourceLocation(
            filename="Token.sol",
            line=10,
            end_line=9,
        )


def test_end_column_requires_column() -> None:
    with pytest.raises(DomainValidationError):
        SourceLocation(
            filename="Token.sol",
            line=10,
            end_column=5,
        )


def test_end_column_cannot_precede_start_column_on_same_line() -> None:
    with pytest.raises(DomainValidationError):
        SourceLocation(
            filename="Token.sol",
            line=10,
            column=8,
            end_column=4,
        )


def test_end_column_can_be_less_than_start_column_on_later_line() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
        column=8,
        end_line=12,
        end_column=4,
    )

    assert location.end_column == 4


# ==========================================================
# Availability / Range
# ==========================================================


def test_has_column() -> None:
    assert SourceLocation(
        filename="Token.sol",
        line=10,
        column=5,
    ).has_column

    assert not SourceLocation(
        filename="Token.sol",
        line=10,
    ).has_column


def test_has_end_position() -> None:
    assert SourceLocation(
        filename="Token.sol",
        line=10,
        end_line=12,
    ).has_end_position

    assert SourceLocation(
        filename="Token.sol",
        line=10,
    ).has_end_position is False


def test_single_line_location() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
    )

    assert location.is_single_line
    assert not location.is_range


def test_explicit_same_line_location() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
        column=4,
        end_line=10,
        end_column=12,
    )

    assert location.is_single_line
    assert not location.is_range


def test_multi_line_location() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
        end_line=15,
    )

    assert location.is_range
    assert not location.is_single_line


# ==========================================================
# Effective End Position
# ==========================================================


def test_effective_end_line_defaults_to_start_line() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
    )

    assert location.effective_end_line == 10


def test_effective_end_column_defaults_to_start_column() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
        column=5,
    )

    assert location.effective_end_column == 5


def test_effective_end_column_is_none_without_column() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
    )

    assert location.effective_end_column is None


def test_span_for_single_line_location() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
    )

    assert location.span == 1


def test_span_for_multi_line_location() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
        end_line=15,
    )

    assert location.span == 6


# ==========================================================
# contains()
# ==========================================================


def test_contains_line() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
        end_line=15,
    )

    assert location.contains(10)
    assert location.contains(12)
    assert location.contains(15)
    assert not location.contains(9)
    assert not location.contains(16)


def test_contains_column_within_single_line_range() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
        column=5,
        end_line=10,
        end_column=12,
    )

    assert location.contains(10, 5)
    assert location.contains(10, 8)
    assert location.contains(10, 12)

    assert not location.contains(10, 4)
    assert not location.contains(10, 13)


def test_contains_with_no_column_information() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
        end_line=15,
    )

    assert location.contains(12, 999)


def test_contains_multi_line_range_with_columns() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
        column=5,
        end_line=15,
        end_column=8,
    )

    assert location.contains(10, 5)
    assert location.contains(10, 50)
    assert location.contains(12, 1)
    assert location.contains(15, 8)

    assert not location.contains(10, 4)
    assert not location.contains(15, 9)


def test_contains_rejects_invalid_query_types() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
    )

    assert not location.contains("10")  # type: ignore[arg-type]
    assert not location.contains(10, "5")  # type: ignore[arg-type]


# ==========================================================
# Presentation
# ==========================================================


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        (
            SourceLocation(
                filename="Token.sol",
                line=15,
            ),
            "Token.sol:15",
        ),
        (
            SourceLocation(
                filename="Token.sol",
                line=15,
                column=8,
            ),
            "Token.sol:15:8",
        ),
        (
            SourceLocation(
                filename="Token.sol",
                line=15,
                end_line=20,
            ),
            "Token.sol:15-20",
        ),
        (
            SourceLocation(
                filename="Token.sol",
                line=15,
                column=8,
                end_line=20,
                end_column=4,
            ),
            "Token.sol:15:8-20:4",
        ),
    ],
)
def test_display(location: SourceLocation, expected: str) -> None:
    assert location.display() == expected
    assert str(location) == expected


# ==========================================================
# Ordering
# ==========================================================


def test_source_locations_are_ordered_by_filename_then_position() -> None:
    first = SourceLocation(
        filename="A.sol",
        line=20,
    )
    second = SourceLocation(
        filename="B.sol",
        line=1,
    )

    assert first < second


def test_source_locations_are_ordered_by_line() -> None:
    first = SourceLocation(
        filename="Token.sol",
        line=10,
    )
    second = SourceLocation(
        filename="Token.sol",
        line=20,
    )

    assert first < second


def test_source_locations_are_ordered_by_column() -> None:
    first = SourceLocation(
        filename="Token.sol",
        line=10,
        column=5,
    )
    second = SourceLocation(
        filename="Token.sol",
        line=10,
        column=10,
    )

    assert first < second


# ==========================================================
# Immutability
# ==========================================================


def test_source_location_is_immutable() -> None:
    location = SourceLocation(
        filename="Token.sol",
        line=10,
    )

    with pytest.raises(AttributeError):
        location.filename = "Other.sol"  # type: ignore[misc]


def test_source_location_value_equality() -> None:
    first = SourceLocation(
        filename="Token.sol",
        line=10,
        column=5,
    )
    second = SourceLocation(
        filename="Token.sol",
        line=10,
        column=5,
    )

    assert first == second
    assert hash(first) == hash(second)