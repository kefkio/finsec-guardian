from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(eq=False, slots=True)
class Entity(ABC):
    """
    Base class for all domain entities.

    An Entity is defined by its identity rather than by the values
    of its attributes. Two entities are considered equal if they
    share the same unique identifier.
    """

    id: UUID = field(default_factory=uuid4, init=False)

    def __eq__(self, other: object) -> bool:
        """
        Compare entities by identity.
        """
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Hash entities by identity.
        """
        return hash(self.id)

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """
        return f"{self.__class__.__name__}(id={self.id})"