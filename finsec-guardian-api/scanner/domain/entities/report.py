from __future__ import annotations

from dataclasses import dataclass

from scanner.domain.entities.entity import Entity


@dataclass(eq=False, slots=True)
class Report(Entity):
    """Minimal placeholder report entity for the domain package."""

    title: str = "Report"
    summary: str = ""

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title cannot be empty")
