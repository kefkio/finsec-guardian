## Finding Invariants (Version 1)

1. Must have a unique identity (UUID).  
2. Must have a non-empty title.  
3. Title length must be within acceptable limits.  
4. Must have a non-empty description.  
5. Must have a non-empty recommendation.  
6. Must have a valid Severity.  
7. Must have a valid Confidence.  
8. Must have a valid AnalyzerType.  
9. Must have a valid SourceLocation.  
10. Equality is based solely on identity.  

---

### Not Included
- Fingerprint  
- Scan  
- Report  
- Risk calculation  

These are important concepts, but they belong to services or other aggregates, not to the invariants of the `Finding` entity itself.
