from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CodeContext:
    """
    Represents the semantic context surrounding a vulnerability
    within source code.

    Unlike SourceLocation, which describes the physical location
    of code within a file, CodeContext represents the logical
    location of a vulnerability within the program's structure.

    A CodeContext intentionally stores only the canonical source
    code associated with the context. Derived representations,
    such as normalized code, are the responsibility of the
    CodeNormalizer domain service.
    """

    contract_name: str
    function_name: str
    source_code: str

    def __post_init__(self) -> None:
        """
        Validate the integrity of the code context.
        """
        fields = {
            "Contract name": self.contract_name,
            "Function name": self.function_name,
            "Source code": self.source_code,
        }

        for field_name, value in fields.items():
            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot be empty."
                )

    def display(self) -> str:
        """
        Returns a human-readable representation of the
        semantic code context.

        Example:
            Vault::withdraw
        """
        return (
            f"{self.contract_name}"
            f"::{self.function_name}"
        )

    def __str__(self) -> str:
        """
        Returns the default string representation.
        """
        return self.display()