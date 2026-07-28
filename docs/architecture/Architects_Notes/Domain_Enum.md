Architect's Notes #2
DomainEnum
Purpose

Provide common functionality shared by every enum in the domain.

Without it every enum would duplicate:

display_name
string conversion
parsing
formatting
Mental Model
               DomainEnum
                    ▲
    ┌───────────────┼───────────────┐
    │               │               │
 Severity      Confidence     RiskLevel
                    │
             AnalyzerType
                    │
             ScanStatus

Think of it as the base vocabulary class.

Owns
display_name
from_string()
str()
Does NOT Own
Priority
Weight
Risk calculations

Those belong to each specific enum.

Design Pattern

Template Method (shared behaviour through inheritance)

Why not use plain Enum?

Because every enum would repeat the same code