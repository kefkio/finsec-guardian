# FinSec Guardian Frontend — Overview

**Status:** Production Ready  
**Version:** 1.0.0  
**Framework:** React 18 + Vite 5 + Tailwind CSS  
**Audience:** Researchers, Users, Developers, Architects

---

## Executive Summary

FinSec Guardian is a **secure-by-design** Solidity smart contract security analysis platform. The frontend is a hardened React application that integrates with a multi-engine analysis backend (Slither, Mythril, Echidna, Heuristic), normalizes findings, computes aggregate risk scores, and delivers tamper-proof audit reports.

This document provides a **complete overview** of the frontend application: vision, features, technology stack, architecture, project structure, and development workflow.

---

## Vision & Philosophy

> FinSec Guardian practises the security disciplines it audits. Every layer of the stack — frontend, API, transport, and crawl surface — is hardened against OWASP Top 10 and OWASP Smart Contract Top 10 threat vectors.

### Core Principles

1. **Security-First** — No component is built without threat modeling; hardened headers, input validation, and access controls are foundational
2. **Developer Experience** — Clear APIs, modular components, comprehensive tooling
3. **Transparency** — Security controls and audit trails are visible to the user
4. **Explainability** — Risk scores, threat models, and findings are actionable, not just noise

---

## Platform Capabilities

### 1. Smart Contract Scanner

The core feature enabling pre-deployment vulnerability detection.

**Workflow:**
1. User pastes Solidity source code (supports 0.4.x → 0.8.x) and/or enters a contract address
2. Frontend validates syntax, contract name extraction, and Ethereum address format
3. Contract is sent to backend via authenticated HTTPS
4. Four analysis engines run in parallel (Slither, Mythril, Echidna, Heuristic)
5. On-chain intelligence layer runs if a contract address is provided (Etherscan)
6. Findings are normalized into a unified schema
7. Risk score is computed using weighted exponential saturation model
8. Results rendered as an audit report with risk grade (A–F) and On-Chain Intelligence panel

**Address-only scanning:** Users can submit just a contract address (no source code) to obtain on-chain intelligence and reputation scoring without static analysis.

**Analysis Engines:**

| Engine | Type | Purpose | Execution Mode |
|--------|------|---------|-----------------|
| **Slither** | Static Analysis | 80+ vulnerability detectors | Python venv |
| **Mythril** | Symbolic Execution | Code path exploration, state analysis | Python venv |
| **Echidna** | Property-Based Fuzzing | Invariant violation detection | Docker container |
| **Heuristic** | Regex-Based Rules | Custom logic-flaw patterns | In-process |

**Result Components:**
- SWC ID (CWE mapping)
- Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- Confidence score (0–100%)
- Human-readable description
- Specific code line number
- Remediation guidance
- Originating analyzer(s)

**Risk Grading:**

```
Grade A: Risk Score 0–20   (Safe)
Grade B: Risk Score 21–40  (Low Risk)
Grade C: Risk Score 41–60  (Medium Risk)
Grade D: Risk Score 61–80  (High Risk)
Grade F: Risk Score 81–100 (Critical Risk)
```

### 2. Security Dashboard

Real-time overview of security posture.

**Key Performance Indicators (KPIs):**
- Total contracts scanned
- Critical vulnerabilities detected
- Active security threats
- Aggregate platform risk score

**Visualizations:**
- Scan activity timeline (last 30 days)
- Vulnerability distribution by severity (bar chart)
- Risk trend (line chart)

**Recent Activity Feed:**
- Latest scans with summary (findings count, risk grade)
- Quick access to detailed reports

### 3. Threat Model Catalogue

STRIDE-based threat library with risk scoring and mitigations.

**Coverage:**
- Spoofing Identity
- Tampering with Data
- Repudiation of Actions
- Information Disclosure
- Denial of Service
- Elevation of Privilege

**Per-Threat Entry:**
- Description and attack scenario
- Likelihood score (1–5)
- Impact score (1–5)
- Derived risk score (likelihood × impact)
- Recommended controls
- OWASP mapping

### 4. Audit Log

Immutable security event timeline.

**Captured Events:**
- Scan creation, completion, deletion
- Threat updates
- Record modifications
- User authentication (sign in, sign out, failed attempts)
- Settings changes

**Searchable Fields:**
- Event type (filter by severity)
- Actor (user who triggered event)
- Resource (contract, threat, record)
- Timestamp range
- Context (what changed, why)

**Event Severity Tags:**
- 🔴 **Critical** — Scan deletion, massive finding change
- 🟠 **High** — Threat updates, permission changes
- 🟡 **Medium** — New scan, record addition
- 🟢 **Low** — Dashboard view, filter selection

### 5. Tamper-Proof Records

Hash-chain record integrity verification.

**Implementation:**
- Each record (scan, threat, audit event) is assigned a SHA-256 hash
- Hash chain: `H(record_i) = SHA256(H_prev || record_data_i)`
- Client-side verification on Records page
- Any modification or deletion breaks the chain
- Visual indicator shows chain integrity status

**Use Cases:**
- Demonstrate audit trail immutability for compliance
- Detect unauthorized data tampering
- Support legal/forensic investigations

### 6. On-Chain Intelligence

Live blockchain data analysis for deployed contracts.

**Capabilities:**
- Transaction statistics (count, unique callers, failure rate)
- High-value transaction table (≥ 10 ETH threshold)
- Repeated caller detection (bot/exploit patterns)
- Function call distribution (top method signatures)
- Contract age and activity timeline
- Suspicious pattern flags (high failure rate, abnormal withdrawals)
- Reputation score (0–100) with signed risk adjustment

**UI:** Rendered via the `OnChainIntelligence` component in five collapsible accordion sections: Overview Stats, Transaction Patterns, Value Flow Analysis, Caller Analysis, and Suspicious Patterns.

**Trigger:** Appears automatically on `Scanner` and `ScanDetail` pages when a valid contract address (0x + 40 hex chars) is associated with the scan.

### 7. Settings & Profile Management

User account and platform configuration.

**Account Settings:**
- Username, email, password change
- API key management (read-only)
- Session management (active devices)

**Scanner Settings:**
- Default Solidity version
- Analysis engine preferences (enable/disable Mythril, Echidna, etc.)
- Timeout settings (max execution time per engine)
- Invariant generation strategy (regex vs. AST)

**Security Settings:**
- Two-factor authentication (planned)
- OAuth integrations (planned)
- API rate limit view

---

## Technology Stack

### Frontend Framework & Build

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Runtime** | Node.js | 18+ (20+ recommended) | JavaScript engine |
| **Framework** | React | 18 | UI library, component model |
| **Build Tool** | Vite | 5 | Dev server, optimized bundling |
| **Styling** | Tailwind CSS | 3 | Utility-first CSS framework |
| **CSS-in-JS** | N/A | — | No runtime CSS-in-JS (performance priority) |

### UI Component Libraries

| Library | Purpose | Key Components |
|---------|---------|-----------------|
| **shadcn/ui** | Unstyled, composable components | Dialog, Sheet, Tabs, Alert |
| **Radix UI** | Headless component primitives | Accessible form controls |
| **lucide-react** | Icon library | 300+ SVG icons |
| **Recharts** | React charting library | LineChart, BarChart, PieChart |

### Routing & State Management

| Library | Version | Purpose |
|---------|---------|---------|
| **React Router** | v6 | Client-side routing, lazy code splitting |
| **TanStack Query** | v5 | Server state management, caching, synchronization |
| **React Context** | Built-in | Theme provider, global UI state |

### API & HTTP

| Library | Purpose |
|---------|---------|
| **Fetch API** | Native HTTP client (no axios dependency) |
| **JWT** | Client-side token management, silent refresh |
| **localStorage** | Persistent token storage |

### Testing & QA

| Framework | Purpose | Coverage |
|-----------|---------|----------|
| **Vitest** | Unit & component tests | Component logic, hooks, utilities |
| **React Testing Library** | Component testing | User-centric assertions |
| **Playwright** | End-to-end tests | Full user workflows |

### Development Tools

| Tool | Purpose |
|------|---------|
| **ESLint** | Code linting, style enforcement |
| **Prettier** | Code formatting |
| **npm scripts** | Task automation |

---

## Project Structure

### Directory Layout

```
finsec-guardian/
├── src/
│   ├── pages/
│   │   ├── Login.jsx                # Public landing + auth (sign in/register/honeypot)
│   │   ├── Index.jsx                # Dashboard (KPIs, charts, activity feed)
│   │   ├── Scanner.jsx              # Contract scanner (paste, analyze, address scan, findings)
│   │   ├── ScanDetail.jsx           # Scan detail (findings, risk, On-Chain Intelligence)
│   │   ├── ThreatModel.jsx          # STRIDE threat catalogue with risk scoring
│   │   ├── AuditLog.jsx             # Security event timeline (searchable, filterable)
│   │   ├── TamperProofRecords.jsx   # Hash-chain integrity verification
│   │   └── Settings.jsx             # User account & platform settings
│   │
│   ├── components/
│   │   ├── AppLayout.jsx            # Authenticated area shell (sidebar + outlet)
│   │   ├── ProtectedRoute.jsx       # Route guard (redirect to /login if not authenticated)
│   │   ├── Navbar.jsx               # Top nav with user menu, theme toggle
│   │   ├── Sidebar.jsx              # Navigation menu (Scanner, Dashboard, Threats, etc.)
│   │   ├── ScanCard.jsx             # Scan summary card (used in dashboard)
│   │   ├── FindingCard.jsx          # Vulnerability finding detail card
│   │   ├── ThreatCard.jsx           # Threat model card (STRIDE entry)
│   │   ├── AuditEventRow.jsx        # Single audit event table row
│   │   ├── RecordHash.jsx           # Hash-chain display and verification
│   │   └── OnChainIntelligence.jsx  # Etherscan on-chain data panels
│   │
│   ├── hooks/
│   │   ├── use-auth.js              # Authentication state & methods (login, logout, refresh)
│   │   ├── use-theme.js             # Theme state (light/dark) with localStorage
│   │   ├── use-mobile.js            # Responsive breakpoint detection (mobile vs desktop)
│   │   ├── use-scan.js              # Scanner state (contract, findings, analysis)
│   │   ├── use-audit-log.js         # Audit log queries & filtering
│   │   └── use-debounce.js          # Debounced input (search, filters)
│   │
│   ├── lib/
│   │   ├── api.js                   # HTTP client with JWT auth & silent refresh
│   │   ├── auth.js                  # Token storage & JWT decoding utilities
│   │   ├── utils.js                 # Tailwind classname utilities
│   │   ├── constants.js             # App constants (API endpoints, risk grades, etc.)
│   │   └── validators.js            # Form validation (email, password, contract syntax)
│   │
│   ├── App.jsx                      # Root component (routing, providers)
│   ├── main.jsx                     # Vite entry point
│   └── index.css                    # Global Tailwind imports & custom CSS
│
├── public/
│   ├── robots.txt                   # Crawler policy (blocks malicious bots)
│   ├── favicon.ico                  # App icon
│   └── index.html                   # HTML entry point (CSP, security headers)
│
├── vite.config.js                   # Vite bundler configuration
├── vitest.config.js                 # Vitest configuration
├── tailwind.config.js               # Tailwind CSS customization
├── .eslintrc.cjs                    # ESLint rules
├── .prettierrc.json                 # Prettier formatting rules
├── package.json                     # Dependencies & scripts
├── package-lock.json                # Dependency lock file
├── README.md                        # This file
└── docs/
    ├── security-architecture.md     # Detailed security controls
    ├── ui-system.md                 # Component design, patterns, patterns
    └── api-integration.md           # Backend API reference
```

### Key Directories Explained

#### `src/pages/` — Page Components

Each page is a top-level route that combines multiple smaller components and hooks.

- **Login.jsx** — Public page (no auth required). Hosts sign-in form, registration form, and honeypot bot trap. Also the landing page.
- **Index.jsx** — Dashboard (auth required). Displays KPIs, charts, recent scans. Uses `<TanStackQuery>` to fetch scan summary data.
- **Scanner.jsx** — Contract analyzer (auth required). Paste Solidity, trigger analysis, view findings. Real-time progress updates.
- **ThreatModel.jsx** — STRIDE threat library (auth required). Search, filter, view risk scoring details.
- **AuditLog.jsx** — Security event timeline (auth required). Search by actor, timestamp, severity. Export to CSV.
- **TamperProofRecords.jsx** — Hash chain verification (auth required). Display record timeline with hash values. Client-side verification.
- **Settings.jsx** — Account & platform configuration (auth required). Password change, API key rotation, scanner preferences.

#### `src/components/` — Reusable Components

Small, focused, single-responsibility components that are composed into pages.

- **AppLayout.jsx** — Shared authenticated area (sidebar, navbar). Uses `<Outlet>` from React Router to render child pages.
- **ProtectedRoute.jsx** — Route guard. Checks authentication state; redirects to `/login` if not authenticated.
- **ScanCard.jsx** — Visual scan summary (used in dashboard). Shows contract name, findings count, risk grade.
- **FindingCard.jsx** — Single vulnerability finding. Expandable with remediation guidance.
- **ThreatCard.jsx** — STRIDE threat entry with likelihood/impact scores and controls.

#### `src/hooks/` — Custom React Hooks

Encapsulate stateful logic and side effects for reuse across components.

- **use-auth.js** — Authentication state (`user`, `token`, `isLoading`), login/logout/refresh methods.
- **use-theme.js** — Dark/light mode toggle, persisted to localStorage.
- **use-mobile.js** — Responsive design detection (breakpoint listener).
- **use-scan.js** — Scanner workflow state (contract text, analysis progress, findings list).
- **use-audit-log.js** — Fetch audit events, apply filters, sorting.

#### `src/lib/` — Utilities & Constants

Pure functions and configuration that don't require React.

- **api.js** — HTTP client with JWT authentication. Handles silent token refresh on 401. All requests go through this.
- **auth.js** — JWT token utilities (storage, decoding, expiration checks).
- **utils.js** — Tailwind classname merging, color mappings, etc.
- **constants.js** — App-wide constants (API base URL, risk grade thresholds, severity colors).
- **validators.js** — Email regex, password strength, Solidity contract syntax validation.

#### `public/` — Static Assets

- **robots.txt** — Crawler policy. Disallows malicious bots (AhrefsBot, SemrushBot, etc.) and `/api/` paths. Allows search engines.
- **index.html** — HTML entry point with CSP meta tag and security headers.
- **favicon.ico** — Application icon.

---

## Development Workflow

### Prerequisites

- **Node.js 18+** (20+ recommended) — [Download](https://nodejs.org/)
- **npm 8+** or **yarn 1.22+** — Included with Node.js
- **Git** — For version control
- **finsec-guardian-api running locally** — Backend must be accessible at `http://localhost:8000/` (or `VITE_API_URL` env var)

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/finsec-guardian.git
cd finsec-guardian

# Install dependencies
npm install

# Create .env.local with backend URL
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

### Development Server

```bash
npm run dev
```

Opens `http://localhost:5173/` by default. HMR (hot module replacement) enabled — changes auto-reload.

### Production Build

```bash
npm run build
```

Outputs optimized bundle to `dist/`. ~120 KB gzipped JavaScript.

### Preview Production Build

```bash
npm run preview
```

Locally serves the production build to verify optimization.

### Linting & Formatting

```bash
# Lint with ESLint
npm run lint

# Format with Prettier
npm run format

# Fix lint errors (auto-fixable)
npm run lint -- --fix
```

### Testing

```bash
# Run unit & component tests
npm run test

# Watch mode (re-run on file change)
npm run test:watch

# Coverage report
npm run test:coverage

# Run E2E tests (Playwright)
npm run test:e2e
```

---

## Architecture Overview

### High-Level Data Flow

```
User Input (Sign In / Paste Contract)
        ↓
[Input Validation]
        ↓
[API Client] → Authenticated HTTPS Request
        ↓
[Backend API] (Django REST)
        ↓
[Analysis Pipeline] (Slither, Mythril, Echidna, Heuristic)
        ↓
[Normalized Findings + Risk Score]
        ↓
[API Response] → Authenticated HTTPS Response
        ↓
[React State] (TanStack Query caching)
        ↓
[Component Rendering]
        ↓
[User Views Results + Downloads Report]
```

### Authentication Flow

1. User enters credentials on `/login`
2. Frontend sends POST to `/api/auth/login/` with email + password
3. Backend validates and returns `access_token` + `refresh_token`
4. Frontend stores tokens in `localStorage`
5. On each API request, frontend adds `Authorization: Bearer <access_token>` header
6. If response is HTTP 401 (token expired), frontend sends refresh token to `/api/auth/refresh/`
7. Backend returns new `access_token`
8. Frontend retries original request with new token (transparent to user)
9. If refresh fails, frontend clears tokens and redirects to `/login`

### Component Tree (Example: Scanner Page)

```
<App>
  <Router>
    <Routes>
      <Route path="/scanner" element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route element={<Scanner />}>
            <Scanner>
              <Navbar />
              <Sidebar />
              <main>
                <ScannerInput />    # Paste contract here
                <AnalysisProgress /> # Progress bar during analysis
                <FindingsList>      # List of findings
                  {findings.map(f => <FindingCard />)}
                </FindingsList>
                <RiskScoreCard />    # Grade A–F
              </main>
            </Scanner>
          </Route>
        </Route>
      </Route>
    </Routes>
  </Router>
</App>
```

---

## Known Limitations

| Limitation | Impact | Workaround | Timeline |
|------------|--------|-----------|----------|
| No file upload | Single-file scanning only | Copy/paste Solidity source | Q3 2024 |
| No multi-contract projects | Analyze Hardhat/Truffle repos as separate files | Manual split | Q3 2024 |
| No on-chain anchoring | Tamper-proof records are client-side only | Not suitable for high-stakes audits | Q4 2024 |
| Dashboard metrics not real-time | 30-second delay after scan completion | Refresh page manually | Q2 2024 |
| No CI/CD integration | Can't scan in GitHub Actions | Manual uploads | Q4 2024 |
| Regex-based invariant generation | Limited to syntactic patterns | Upgrade to AST-based (Slither IR) | Q3 2024 |

---

## Roadmap

### Q2 2024

- [x] Core scanner UI
- [x] Dashboard KPIs & charts
- [x] Threat model catalogue
- [x] Audit log with filtering
- [ ] Dashboard real-time metrics (WebSocket updates)
- [ ] Email notifications for scan completion

### Q3 2024

- [ ] File upload (single + multi-file)
- [ ] Hardhat/Truffle project detection
- [ ] AST-based invariant generation (upgrade from regex)
- [ ] Dark mode theme (currently light-only)
- [ ] Report export to PDF

### Q4 2024

- [ ] On-chain record anchoring (EVM-compatible)
- [ ] CI/CD mode: GitHub Action, GitLab CI integration
- [ ] Foundry integration (Forge + Anvil)
- [ ] Semgrep analyzer (additional engine)
- [ ] Two-factor authentication

### 2025

- [ ] Public `/free-audit` scanner (unauthenticated, limited results)
- [ ] Slack integration (notifications, audit log export)
- [ ] API webhooks (scan completion, new threats)
- [ ] Vulnerability database sync (latest CWE/SWC mappings)
- [ ] Team management (share scans, role-based access)

---

## Deployment

### Environment Variables

Create `.env.local` (development) or `.env.production` (production):

```bash
# Backend API base URL
VITE_API_URL=https://api.finsec-guardian.com

# (Optional) Analytics
VITE_ANALYTICS_ID=your_ga_id

# (Optional) Feature flags
VITE_ENABLE_FILE_UPLOAD=false
VITE_ENABLE_ON_CHAIN_ANCHORING=false
```

### Build & Host

```bash
# Build production bundle
npm run build

# Output: dist/ directory (static HTML/JS/CSS)

# Host on any static server:
# - Vercel: `vercel deploy`
# - Netlify: `netlify deploy --prod --dir=dist`
# - GitHub Pages: `git push origin main` + configure Pages
# - AWS S3 + CloudFront: `aws s3 sync dist/ s3://bucket/ --delete`
# - Docker: See Dockerfile
```

### Docker Deployment

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Support & Contribution

### Issues & Bug Reports

Report issues via GitHub Issues. Include:
- Browser + version
- Reproduction steps
- Screenshots/video if UI-related
- Browser console errors

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/scanner-ui-improvements`)
3. Commit changes (`git commit -m "..."`)
4. Push to branch (`git push origin feature/...`)
5. Open a pull request with description of changes

**Code Style:** ESLint + Prettier enforced. Run `npm run lint -- --fix` before pushing.

**Testing:** Add tests for new features. Maintain >80% coverage. Run `npm run test` before push.

---

## Vision Statement

FinSec Guardian is a **unified smart contract security operations console** — and a demonstration that security tooling must itself be hardened. The frontend is not just a wrapper around backend APIs; it is a **trust boundary** that implements JWT authentication, input validation, CORS restrictions, CSP headers, bot mitigation, and immutable audit trails.

Users should feel confident that the platform analyzing their smart contracts is itself built with the same rigor, transparency, and explainability it teaches.

---

## Contact & Resources

| Resource | Link |
|----------|------|
| GitHub | https://github.com/your-org/finsec-guardian |
| API Docs | https://docs.finsec-guardian.com/api |
| Security Report | security@finsec-guardian.com |
| Data Subject Rights | datasubjectsrights@finsec.com |
| Bug Bounty | https://bugbounty.finsec-guardian.com |

---

**Document Version:** 1.0  
**Last Updated:** April 2026  
**Maintained By:** FinSec Guardian Team