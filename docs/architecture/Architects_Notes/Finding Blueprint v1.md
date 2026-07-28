### Finding Blueprint v1

                    Finding Entity
                          │
     ┌────────────────────┴────────────────────┐
     │                                         │
  Identity                                 Business
     │                                         │
 UUID(id)                             title
                                      description
                                      recommendation

                          │
                          ▼

                  Classification
          ┌──────────┬────────────┬────────────┐
          │          │            │            │
      Severity   Confidence   RiskLevel   AnalyzerType

                          │
                          ▼

                  SourceLocation
               filename
               line
               column
               end_line
               end_column

                          │
                          ▼

#### Validation Rules
    ✓ title required.
    ✓ title <= 200 chars.
    ✓ description required.
    ✓ recommendation required.
    ✓ valid enums.
    ✓ valid SourceLocation.
    ✓ critical severity ⇒ critical risk.
    ✓ fingerprint required.

### Behaviors

    summary()
    
    matches()
                    
    same_location()
                    
    same_analyzer()

    is_critical()

    is_actionable()

    has_precise_location()

### Collaborators

Finding
   │
   ├──────── FingerprintService
   │
   ├──────── Report
   │
   ├──────── Scan
   │
   └──────── RiskScorer

## Dependency Map

SourceLocation
        ▲
        │
        │
Finding────────Severity
   ▲             ▲
   │             │
   │             │
Report────────RiskLevel
   ▲
   │
Scan