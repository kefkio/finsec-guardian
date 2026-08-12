from __future__ import annotations

from dataclasses import dataclass
from scanner.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    """Immutable Value Object for analysis context."""

    source_code: str
    contract_name: str | None = None
    source_filename: str | None = None
    solidity_version: str | None = None

    def __post_init__(self) -> None:
        self._validate_and_strip("source_code", self.source_code)
        self._normalize_optional_string("contract_name", self.contract_name)
        self._normalize_optional_string("source_filename", self.source_filename)
        self._normalize_optional_string("solidity_version", self.solidity_version)

    def _validate_and_strip(self, field_name: str, value: str) -> None:
        if not isinstance(value, str):
            raise DomainValidationError(f"{field_name} must be a string.")

        stripped = value.strip()
        if not stripped:
            raise DomainValidationError(f"{field_name} cannot be empty.")

        object.__setattr__(self, field_name, stripped)

    def _normalize_optional_string(
        self,
        field_name: str,
        value: str | None,
    ) -> None:
        if value is None:
            return

        if not isinstance(value, str):
            raise DomainValidationError(f"{field_name} must be a string or None.")

        stripped = value.strip()
        object.__setattr__(self, field_name, stripped if stripped else None)

    @property
    def has_contract_name(self) -> bool:
        return self.contract_name is not None

    @property
    def has_source_filename(self) -> bool:
        return self.source_filename is not None

    @property
    def has_solidity_version(self) -> bool:
        return self.solidity_version is not None