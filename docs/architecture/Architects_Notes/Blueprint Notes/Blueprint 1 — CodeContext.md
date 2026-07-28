# Blueprint 1 — CodeContext

### Purpose

CodeContext represents the semantic location of code being analyzed.

Unlike SourceLocation, which describes physical coordinates, CodeContext describes the logical structure of the program.

Think of it as the answer to:

"Where in the program does this vulnerability live?"

### Responsibilities

A CodeContext should know:

- Contract

- Function

- Source Snippet

- Normalized Source

- (Optional) AST Path

- (Optional) Parent Contract

- (Optional) Modifiers

It should not know:

- Severity
- Analyzer
- Fingerprint
- Risk

Those belong elsewhere.

Proposed Fields
    - contract_name: str

    - function_name: str

    - source_snippet: str

    - normalized_source: str

Future versions can add:

    - ast_path: str | None

    - inheritance_chain: tuple[str, ...]

    - modifiers: tuple[str, ...]

    - visibility: str

Notice something...this design is aimed for evolution without over-engineering.

Why Store Both Source and Normalized Source? . Because they serve different purposes.

Example:

    Original:

## Original Vulnerable Code

```solidity
        function withdraw() {
        balances[msg.sender] -= amount;
        msg.sender.call{value: amount}("");
        } 
```

Normalized:

```solidity 
    functionwithdraw(){
    balances[msg.sender]-=amount;
    msg.sender.call{value:amount}("");
    }
    
```

The normalized version is deterministic.

The original version is useful for reports.

Different responsibilities.

