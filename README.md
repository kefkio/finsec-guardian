# FinSec Guardian

FinSec Guardian is a frontend security workstation prototype for Solidity contract analysis and DeFi risk operations.

It currently provides a complete analyst UI with:
- Contract scan workflow and findings panel
- Threat model visualization
- Audit log timeline
- Tamper-evident record chain simulation
- Security settings dashboard

Important: the scanner logic is currently mock/demo logic in the UI, not a real Solidity static analysis engine yet.

## What This Project Is

- A React + JavaScript + Vite application
- A cybersecurity-focused dashboard experience for smart contract security operations
- A foundation to plug in real analysis backends (Slither/Mythril/Semgrep/custom rules)

## Current Feature Set

### 1) Contract Scanner
- Paste Solidity source code in an editor panel
- Trigger a scan workflow with progress state
- View categorized findings (critical/high/medium/low/info)
- Read recommendations per finding with SWC-style IDs

Current behavior:
- Scanner results are mock findings defined in the frontend
- No compiler parsing, AST pass, symbolic execution, or bytecode analysis yet

### 2) Security Dashboard
- High-level KPI cards (contracts scanned, critical vulns, active threats, risk score)
- Scan activity chart and vulnerability distribution chart
- Recent scans list

Current behavior:
- Dashboard data is static demo data

### 3) Threat Model
- STRIDE-oriented threat cards
- Likelihood/impact scoring and derived risk score
- Mitigation recommendations by threat type

Current behavior:
- Threat records are static demo scenarios

### 4) Audit Log
- Searchable event stream UI
- Severity-tagged timeline entries with actor/resource/IP context

Current behavior:
- Entries are static demo events

### 5) Tamper-Proof Records
- Client-side hash chain simulation (SHA-256 via browser crypto API)
- Add records, verify chain integrity, and simulate tampering
- Display simulated Solidity contract for anchoring concept

Current behavior:
- No wallet connection, no deployed contract, no on-chain writes yet

## Tech Stack

- React 18
- JavaScript (JSX)
- Vite 5
- Tailwind CSS
- shadcn/ui + Radix UI
- Recharts (visualizations)
- React Router
- TanStack Query (available in app setup)
- Vitest + Testing Library
- Playwright (configured)

## Project Structure

- src/pages/Scanner.jsx: scanner flow and findings UI (mock analysis)
- src/pages/Dashboard.jsx: security metrics and charts
- src/pages/ThreatModel.jsx: threat catalog and risk modeling view
- src/pages/AuditLog.jsx: security event timeline
- src/pages/TamperProofRecords.jsx: hash-chain simulation and verification
- src/pages/Settings.jsx: security and scanner settings UI
- src/components/AppLayout.jsx: sidebar + routed layout shell

## Getting Started

### Prerequisites
- Node.js 18+ (Node.js 20+ recommended)
- npm

### Install

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Lint

```bash
npm run lint
```

### Unit/Component Tests

```bash
npm run test
```

### Watch Tests

```bash
npm run test:watch
```

## Security Scanner Scope (Planned)

The intended scanner scope includes:
- SWC-aligned rule detection
- Reentrancy, access control, arithmetic safety, DoS patterns
- Compiler/version hygiene checks
- Severity scoring and remediation guidance
- JSON report export and CI integration

Suggested implementation path:
1. Add a backend analysis service (Node/Python)
2. Integrate Slither or Mythril for first-pass findings
3. Normalize findings to a shared schema
4. Replace mock findings in the scanner page with API responses
5. Persist scan history and audit events

## Known Limitations

- No real static analysis pipeline yet
- No file upload parser or multi-contract project support
- No authentication backend
- No persistent storage/database
- No blockchain RPC, wallet, or contract deployment integration
- Most pages currently use in-memory/static data

## Recommended Next Milestones

1. Build a real scanner API and connect the scanner UI
2. Add finding suppression/baselines and report export
3. Add user auth + RBAC + persistent audit storage
4. Add on-chain anchoring for tamper-proof records
5. Add CI mode for repository-based contract scans

## Vision

FinSec Guardian is positioned as a unified smart contract security operations console:
- Analyze Solidity contracts
- Track threat posture over time
- Preserve tamper-evident security events
- Support audit and compliance workflows

This repository currently delivers the interface foundation and interaction model needed to evolve into that full platform.
