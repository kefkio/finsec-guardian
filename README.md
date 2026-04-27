# FinSec Guardian

**Research-Oriented Multi-Engine Smart Contract Security Platform**

FinSec Guardian is a cybersecurity research platform for analyzing Solidity smart contracts before deployment. It combines multiple security analysis techniques into a unified pipeline that helps identify vulnerabilities, prioritize risk, and generate explainable audit results.

The project was built as both an engineering system and a research prototype—demonstrating how heterogeneous security tools can be orchestrated into a single decision-support framework.

----

## Why FinSec Guardian?

Smart contract security tools often operate independently, producing fragmented findings, inconsistent severity ratings, and noisy outputs.

FinSec Guardian addresses this by providing:

- **Multi-engine analysis** through complementary security tools  
- **Unified findings model** across different scanners  
- **Explainable risk scoring** instead of raw tool outputs  
- **Persistent scan records** for benchmarking and historical review  
- **Modular architecture** for future cybersecurity research extensions  

---

## Core Capabilities

### Multi-Engine Security Analysis

FinSec Guardian integrates multiple approaches:

- **Slither** — static vulnerability detection  
- **Mythril** — symbolic execution analysis  
- **Echidna** — property-based fuzz testing  
- **Heuristic Engine** — custom rule-based logic checks  
- **Etherscan Intelligence** — optional on-chain metadata enrichment  

### Risk Intelligence Layer

Outputs from different tools are normalized into a common schema and evaluated using a deterministic scoring model based on:

- Severity  
- Confidence  
- Tool reliability weighting  
- Aggregate exposure patterns  

### Audit & Evidence Layer

- Persistent scan history  
- Structured findings database  
- Threat records  
- Audit logs  
- Tamper-evident integrity workflows  

---

## Research Context

FinSec Guardian serves as a broader experimental foundation for future research in:

- machine learning–assisted vulnerability classification  
- anomaly detection using historical scan data  
- adaptive cybersecurity risk scoring  
- security analytics for financial systems  
- trust frameworks for digital infrastructures  

By storing findings over time, the platform supports future dataset creation, benchmarking, and longitudinal cybersecurity studies.

---

## System Architecture

```text
Frontend (React + Vite)
        ↓
REST API (Django + DRF)
        ↓
Scan Orchestrator
 ├── Slither
 ├── Mythril
 ├── Echidna
 ├── Heuristic Engine
 └── Etherscan Layer
        ↓
Risk Scoring Engine
        ↓
PostgreSQL Persistence

```
## Technology Stack
```Frontend
React 18
Vite 5
Tailwind CSS
TanStack Query
React Router
Backend
Python 3
Django 5
Django REST Framework
JWT Authentication
PostgreSQL
Security Tooling
  -Slither
  -Mythril
  -Echidna
```
---
## Quick Start

  ### Clone Repository
</>Bash
``` 
git clone https://github.com/kefkio/finsec-guardian.git
cd finsec
```
  ### Run Full Platform
  </>Bash
  ```
chmod +x run.sh
./run.sh
```
---
### Access
  Frontend: http://localhost:8080
  Backend: http://localhost:8000

### Screenshots / Demo Preview (Very Important)
```
## Interface Preview

| Dashboard | Scanner |
|----------|---------|
| (<img width="960" height="474" alt="WXWorkCapture_1777293840411" src="https://github.com/user-attachments/assets/add6adc0-96ad-4737-a8af-f17f043dda78" />
 | (image) |

| Findings Report | Threat Model |
|----------------|--------------|
| (image) | (image) |
```
### Use Cases

- Audit a Solidity contract before deployment
- Compare findings across multiple security tools
- Generate explainable risk reports for stakeholders
- Benchmark smart contract vulnerabilities over time
- Build datasets for ML-based security research

## Project Status

Current Version: Research Prototype (Active Development)

Implemented:
- Full-stack web platform
- Multi-engine orchestration
- Risk scoring engine
- Persistent scan records

In Progress:
- Advanced reporting
- CI/CD integrations
- Expanded engine coverage

###Roadmap
## Roadmap

- Foundry integration
- Semgrep smart contract rules
- Machine learning classifier for findings
- Historical anomaly detection
- GitHub Actions CI scanner
- Public API access
- Expanded chain intelligence

## Research Contributions
## Research Contributions

FinSec Guardian explores:

  1. Multi-engine vulnerability aggregation
  2. Explainable deterministic risk scoring
  3. Cross-tool normalization pipelines
  4. Persistent security telemetry datasets
  5. Future AI-assisted vulnerability prioritization

## Installation Notes / Requirements
- Node.js 18+
- Python 3.10+
- PostgreSQL
- Docker (optional for Echidna)

Author Section
## Author

Kefa Waweru Kioge  
Graduate Student (Fall 2026)  
University of Michigan–Dearborn  

Research Interests:
Cybersecurity, Applied AI Security, Blockchain Security, Secure Systems
