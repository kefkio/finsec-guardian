Architect's Note #46 – Domain Services Encapsulate Business Transformations

A Domain Service exists when an important domain operation does not naturally belong to an Entity or Value Object. CodeNormalizer transforms one domain concept (CodeContext) into another (NormalizedCode) without owning identity or persistent state.

The service should expose a minimal public API while decomposing its algorithm into small private steps. This keeps the business capability stable even as the implementation evolves—from simple textual normalization today to language-aware or AST-based normalization in the future. Callers depend only on the transformation, not on how it is achieved.