from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from django.utils import timezone

from scanner.domain.entities.entity import Entity
from scanner.domain.exceptions import DomainValidationError


@dataclass(slots=True)
class SmartContract(Entity):
    """
    Represents a smart contract within the scanning domain.

    A SmartContract is the primary artifact analyzed by the
    security engine. It owns the original source code and
    metadata required throughout the scanning lifecycle.

    The entity is responsible for maintaining the integrity
    of the contract while exposing domain behavior intrinsic
    to the contract itself.
    """

    filename: str

    contract_name: str

    source_code: str

    compiler_version: str | None = None

    language: str = "Solidity"

    source_hash: str | None = None

    created_at: datetime = field(
        default_factory=timezone.now
    )

    updated_at: datetime = field(
        default_factory=timezone.now
    )

    def __post_init__(self) -> None:
        """
        Validates the SmartContract invariants.
        """
        if not self.filename.strip():
            raise DomainValidationError(
                "Filename cannot be empty."
            )

        if not self.contract_name.strip():
            raise DomainValidationError(
                "Contract name cannot be empty."
            )

        if not self.source_code.strip():
            raise DomainValidationError(
                "Source code cannot be empty."
            )

        if not self.language.strip():
            raise DomainValidationError(
                "Language cannot be empty."
            )

    # ==========================================================
    # Domain Behavior
    # ==========================================================

    def rename(self, new_name: str) -> None:
        """
        Renames the smart contract.
        """
        new_name = new_name.strip()

        if not new_name:
            raise DomainValidationError(
                "Contract name cannot be empty."
            )

        self.contract_name = new_name
        self.updated_at = timezone.now()

    def update_source(self, source_code: str) -> None:
        """
        Updates the source code.

        Updating the source invalidates any previously
        computed source hash.
        """
        source_code = source_code.strip()

        if not source_code:
            raise DomainValidationError(
                "Source code cannot be empty."
            )

        self.source_code = source_code

        # The source has changed, therefore any existing
        # hash or fingerprint is no longer valid.
        self.source_hash = None

        self.updated_at = timezone.now()

    def update_hash(self, source_hash: str) -> None:
        """
        Updates the source hash.

        The hash is computed by a domain service and
        stored by the entity.
        """
        source_hash = source_hash.strip()

        if not source_hash:
            raise DomainValidationError(
                "Source hash cannot be empty."
            )

        self.source_hash = source_hash
        self.updated_at = timezone.now()

    # ==========================================================
    # Derived Properties
    # ==========================================================

    @property
    def has_source(self) -> bool:
        """
        Returns True if source code exists.
        """
        return bool(self.source_code.strip())

    @property
    def has_hash(self) -> bool:
        """
        Returns True if the contract has a source hash.
        """
        return self.source_hash is not None

    @property
    def is_compiled(self) -> bool:
        """
        Returns True if a compiler version has been assigned.
        """
        return self.compiler_version is not None

    @property
    def line_count(self) -> int:
        """
        Returns the number of lines in the source code.
        """
        return len(self.source_code.splitlines())

    @property
    def source_size(self) -> int:
        """
        Returns the size of the source code in characters.
        """
        return len(self.source_code)

    @property
    def last_modified(self) -> datetime:
        """
        Returns the timestamp of the most recent update.
        """
        return self.updated_at