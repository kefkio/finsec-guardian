# Frontend — UI System

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Designers

---

## Table of Contents

1. [Overview](#overview)
2. [Component Library](#component-library)
3. [Page Components](#page-components)
4. [Data Fetching Strategy](#data-fetching-strategy)
5. [Styling System](#styling-system)
6. [Icons & Visualisations](#icons--visualisations)
7. [Custom Hooks](#custom-hooks)
8. [Patterns & Conventions](#patterns--conventions)

---

## Overview

The FinSec Guardian frontend uses a **composition-based UI architecture** built on shadcn/ui (Radix primitives) + Tailwind CSS. Components are unstyled at the primitive level and themed via Tailwind utility classes, producing a consistent, accessible interface without runtime CSS-in-JS overhead.

**Related documents:**
- [Frontend Overview](overview.md) — full frontend architecture
- [Security Architecture](security-architecture.md) — authentication and hardening
- [System Architecture](../system-architecture.md) — how the frontend fits the overall system

---

## Component Library

### shadcn/ui Primitives

50+ components from `src/components/ui/`, each wrapping a Radix UI primitive with Tailwind styling:

| Category | Components |
|----------|-----------|
| **Layout** | Card, Separator, AspectRatio, Resizable, ScrollArea |
| **Navigation** | Tabs, NavigationMenu, Breadcrumb, Sidebar, Menubar |
| **Forms** | Input, Textarea, Select, Checkbox, RadioGroup, Switch, Slider, Label, Form, InputOTP |
| **Feedback** | Alert, AlertDialog, Badge, Progress, Skeleton, Toast, Toaster, Sonner |
| **Overlay** | Dialog, Drawer, Sheet, Popover, Tooltip, HoverCard, ContextMenu, DropdownMenu, Command |
| **Data** | Table, Pagination, Accordion, Collapsible, Toggle, ToggleGroup |
| **Visualisation** | Chart (Recharts wrapper), Calendar, Carousel, Avatar |

### Application Components

| Component | Purpose | Used In |
|-----------|---------|---------|
| `AppLayout` | Authenticated shell (sidebar + content outlet) | All protected routes |
| `NavLink` | Sidebar navigation item with active state | AppLayout |
| `OnChainIntelligence` | Etherscan on-chain data accordion panels (~400 lines) | Scanner, ScanDetail |

---

## Page Components

| Page | Route | Key Features |
|------|-------|-------------|
| **Login** | `/login` | Sign-in/register forms, honeypot bot trap, JWT auth |
| **Index** (Dashboard) | `/` | KPI cards (`Scan count`, `Critical findings`, `Active threats`, `Risk score`), severity bar chart, scan activity timeline, recent scans table |
| **Scanner** | `/scanner` | Source code textarea (with Clear/Load Example), contract name input, contract address input (with inline Scan button + Globe icon + validation), mutation-driven scan, findings list with severity badges, risk grade card, On-Chain Intelligence panel |
| **ScanDetail** | `/scanner/:id` | Findings table, statistics, risk breakdown, On-Chain Intelligence (lazy-loaded when `contract_address` present) |
| **ThreatModel** | `/threats` | STRIDE threat catalogue, likelihood × impact risk matrix, search and filter |
| **AuditLog** | `/audit-log` | Searchable event timeline, severity tags, actor/resource filters |
| **TamperProofRecords** | `/records` | SHA-256 hash-chain display, client-side chain verification, integrity status |
| **Settings** | `/settings` | User preferences, scanner configuration |
| **NotFound** | `*` | 404 fallback |

---

## Data Fetching Strategy

All API communication uses **TanStack Query v5** for server state management.

### Query Configuration

```javascript
const queryClient = new QueryClient();
```

### Stale Times

| Data Type | Stale Time | Rationale |
|-----------|-----------|-----------|
| Scan list | 30 s | Users expect near-real-time scan status |
| Scan detail | 30 s | Same scan page may be opened repeatedly |
| Findings | 60 s | Findings don't change after scan completion |
| Statistics | 60 s | Computed metrics are stable |
| On-chain data | 60 s | Etherscan data changes infrequently |
| Threats | 60 s | Threat catalogue is semi-static |
| Audit events | 30 s | Users expect recent events |

### Mutation Pattern

Scans use `useMutation` with `onSuccess` / `onError` callbacks wired to `sonner` toasts:

```javascript
const mutation = useMutation({
  mutationFn: () => scannerApi.createScan(payload),
  onSuccess: (data) => { /* extract findings, set state */ },
  onError: (error) => toast.error(error.message),
});
```

### Lazy Fetching

Conditional queries use `enabled` flags:

```javascript
useQuery({
  queryKey: ['onchain', scan.id],
  queryFn: () => scannerApi.getOnChainData(scan.id),
  enabled: !!scan.contract_address,  // Only fetch when address exists
});
```

---

## Styling System

### Tailwind CSS

- **Config:** `tailwind.config.js` with custom colour tokens, border-radius, and font family
- **Utility-first:** No custom CSS classes — all styling via Tailwind utilities
- **Dark mode:** `class` strategy via `use-theme.js` hook
- **CSS variables:** Theme colours defined as HSL CSS custom properties (`--primary`, `--background`, etc.)

### Design Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--background` | white | slate-950 | Page background |
| `--foreground` | slate-950 | slate-50 | Primary text |
| `--primary` | brand blue | brand blue | Buttons, links, accents |
| `--destructive` | red-600 | red-500 | Delete actions, critical badges |
| `--muted` | slate-100 | slate-800 | Secondary backgrounds |
| `--border` | slate-200 | slate-800 | Card and input borders |

### Severity Colour System

Findings and badges use a consistent severity-to-colour mapping:

| Severity | Badge Class | Border Class | Bar Class |
|----------|-------------|-------------|-----------|
| **Critical** | `bg-red-600 text-white` | `border-l-red-500` | `bg-red-500` |
| **High** | `bg-orange-500 text-white` | `border-l-orange-500` | `bg-orange-500` |
| **Medium** | `bg-yellow-500 text-black` | `border-l-yellow-500` | `bg-yellow-500` |
| **Low** | `bg-blue-500 text-white` | `border-l-blue-500` | `bg-blue-500` |
| **Info** | `bg-muted text-muted-foreground` | `border-l-muted-foreground` | `bg-muted-foreground` |

---

## Icons & Visualisations

### Icons

**Library:** Lucide React — tree-shakeable SVG icons.

Common icons by context:
- Scanner: `Code2`, `Play`, `Search`, `Globe`, `Shield*` family
- Dashboard: `Activity`, `TrendingUp`, `Clock`, `FileText`
- On-Chain: `Users`, `AlertTriangle`, `ArrowUpRight`, `ArrowDownRight`, `Hash`, `Zap`
- Navigation: `ChevronDown`, `ChevronRight`, `ExternalLink`, `Download`

### Charts

**Library:** Recharts — React-native SVG charting.

| Chart Type | Component | Usage |
|-----------|-----------|-------|
| Bar chart | `BarChart` | Severity distribution on Dashboard |
| Line chart | `LineChart` | Scan activity timeline |
| Progress | `Progress` (shadcn) | Scan progress, reputation score |

---

## Custom Hooks

| Hook | File | Purpose |
|------|------|---------|
| `use-theme` | `hooks/use-theme.js` | Dark/light mode toggle, persists to `localStorage` |
| `use-mobile` | `hooks/use-mobile.jsx` | Responsive breakpoint detection (`(max-width: 768px)`) |
| `use-toast` | `hooks/use-toast.js` | Toast notification state management |

---

## Patterns & Conventions

### File Naming
- Pages: `PascalCase.jsx` (e.g., `Scanner.jsx`, `ScanDetail.jsx`)
- Components: `PascalCase.jsx` (e.g., `OnChainIntelligence.jsx`)
- Hooks: `use-kebab-case.js` (e.g., `use-theme.js`)
- Utilities: `camelCase.js` (e.g., `api.js`, `utils.js`)
- UI primitives: `lowercase.jsx` (e.g., `button.jsx`, `card.jsx`)

### Component Structure
- Props destructured at function signature
- `useState` / `useMemo` / `useRef` at top
- Queries and mutations below state
- Event handlers as inner functions
- JSX returned at bottom

### Import Order
1. React hooks
2. Third-party libraries (TanStack Query, React Router, Recharts, Lucide)
3. shadcn/ui components
4. Application components
5. Utilities and API

### Error Handling
- All API errors surface via `sonner` toasts
- TanStack Query `error` states render fallback UI per component
- `ProtectedRoute` redirects to `/login` on missing auth