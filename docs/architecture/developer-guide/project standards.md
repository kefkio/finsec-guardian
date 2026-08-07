| Component      | Dataclass Configuration                           | Equality        |
| -------------- | ------------------------------------------------- | --------------- |
| Entity         | `@dataclass(eq=False, slots=True)`                | Identity (UUID) |
| Value Object   | `@dataclass(frozen=True, slots=True, order=True)` | All fields      |
| Enum           | `Enum` subclass                                   | Enum semantics  |
| Domain Service | Regular class                                     | Not applicable  |
