Architect's Note #12
Why do Entities disable dataclass equality?

Python's dataclass decorator generates value-based equality by default. That behavior is ideal for Value Objects because they are defined entirely by their attributes.

Entities, however, are defined by identity, not by their current state.

By specifying eq=False, we prevent dataclass from generating a field-by-field comparison and preserve the custom __eq__() implementation inherited from Entity. This ensures that two Finding instances with the same UUID are considered the same entity, even if other attributes have changed over time.

This seemingly small configuration is fundamental to maintaining correct Domain-Driven Design semantics throughout the codebase.