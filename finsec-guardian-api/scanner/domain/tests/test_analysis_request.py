from __future__ import annotations

import pytest

from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.analysis_request import AnalysisRequest


def test_analysis_request_valid_instantiation_and_stripping() -> None:
    request = AnalysisRequest(
        source_code="  contract Test {}  ",
        contract_name="  TestContract  ",
        source_filename="  Test.sol  ",
        solidity_version="  0.8.20  ",
    )

    assert request.source_code == "contract Test {}"
    assert request.contract_name == "TestContract"
    assert request.source_filename == "Test.sol"
    assert request.solidity_version == "0.8.20"

    assert request.has_contract_name is True
    assert request.has_source_filename is True
    assert request.has_solidity_version is True


def test_analysis_request_normalizes_empty_optional_fields_to_none() -> None:
    request = AnalysisRequest(
        source_code="contract Test {}",
        contract_name="   ",
        source_filename="",
        solidity_version=None,
    )

    assert request.contract_name is None
    assert request.source_filename is None
    assert request.solidity_version is None

    assert request.has_contract_name is False
    assert request.has_source_filename is False
    assert request.has_solidity_version is False


def test_analysis_request_raises_error_for_empty_source_code() -> None:
    with pytest.raises(
        DomainValidationError,
        match="source_code cannot be empty",
    ):
        AnalysisRequest(source_code="   ")


@pytest.mark.parametrize(
    "source_code",
    [None, 123, [], {}],
)
def test_analysis_request_rejects_invalid_source_code_type(
    source_code,
) -> None:
    with pytest.raises(
        DomainValidationError,
        match="source_code must be a string",
    ):
        AnalysisRequest(source_code=source_code)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("contract_name", 42),
        ("contract_name", []),
        ("source_filename", 42),
        ("source_filename", []),
        ("solidity_version", 42),
        ("solidity_version", []),
    ],
)
def test_analysis_request_rejects_invalid_optional_field_types(
    field_name,
    value,
) -> None:
    with pytest.raises(
        DomainValidationError,
        match=f"{field_name} must be a string or None",
    ):
        AnalysisRequest(
            source_code="contract T {}",
            **{field_name: value},
        )


def test_analysis_request_is_immutable() -> None:
    request = AnalysisRequest(
        source_code="contract Test {}",
    )

    with pytest.raises(AttributeError):
        request.source_code = "contract Updated {}"  # type: ignore[misc]


def test_analysis_request_value_equality() -> None:
    req1 = AnalysisRequest(
        source_code="contract T {}",
        contract_name="T",
    )
    req2 = AnalysisRequest(
        source_code="contract T {}",
        contract_name="T",
    )

    assert req1 == req2
    assert hash(req1) == hash(req2)


def test_analysis_request_optional_metadata_defaults_to_none() -> None:
    request = AnalysisRequest(
        source_code="contract Test {}",
    )

    assert request.contract_name is None
    assert request.source_filename is None
    assert request.solidity_version is None

    assert request.has_contract_name is False
    assert request.has_source_filename is False
    assert request.has_solidity_version is False