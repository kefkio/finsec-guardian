# Frontend — Security Architecture

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Security Engineers

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Token Management](#authentication--token-management)
3. [Route Protection](#route-protection)
4. [API Security](#api-security)
5. [Input Validation](#input-validation)
6. [Content Security Policy](#content-security-policy)
7. [Bot Mitigation](#bot-mitigation)
8. [Data Handling](#data-handling)
9. [OWASP Alignment](#owasp-alignment)

---

## Overview

The frontend is a **trust boundary** — it is the first line of defence against malicious input and the last line of defence for user credentials. Security is layered: authentication, route guards, input validation, transport security, and output sanitisation each operate independently.

**Related documents:**
- [Frontend Overview](overview.md) — application architecture
- [UI System](ui-system.md) — component library
- [Threat Model](../threat-model.md) — system-wide threat analysis
- [System Architecture](../system-architecture.md) — cross-cutting security concerns

---

## Authentication & Token Management

### JWT Flow

1. User submits credentials on `/login`
2. `authApi.login()` sends POST to `/api/auth/login/`
3. Backend returns `{ access, refresh }` (SimpleJWT)
4. `tokenStorage.set(access, refresh)` persists to `localStorage`
5. Every subsequent API call includes `Authorization: Bearer <access_token>`

### Token Storage

```javascript
export const tokenStorage = {
  getAccess:  () => localStorage.getItem('finsec_access_token'),
  getRefresh: () => localStorage.getItem('finsec_refresh_token'),
  set: (access, refresh) => {
    localStorage.setItem('finsec_access_token', access);
    if (refresh) localStorage.setItem('finsec_refresh_token', refresh);
  },
  clear: () => {
    localStorage.removeItem('finsec_access_token');
    localStorage.removeItem('finsec_refresh_token');
  },
  isAuthenticated: () => !!localStorage.getItem('finsec_access_token'),
};
```

**Key names:** `finsec_access_token`, `finsec_refresh_token` — namespaced to avoid collision with other applications on the same origin.

### Silent Token Refresh

On HTTP 401 response, the `request()` function automatically:

1. Calls `refreshAccessToken()` with the stored refresh token
2. If successful: stores new access token, retries the original request **once** (`retry = false` on second attempt)
3. If refresh fails: clears all tokens, redirects to `/login`

```javascript
async function request(path, options = {}, retry = true) {
  // ... send request with Bearer token ...
  if (res.status === 401 && retry) {
    await refreshAccessToken();
    return request(path, options, false);  // Single retry
  }
}
```

This prevents infinite retry loops — a failed refresh token always terminates the session.

---

## Route Protection

### ProtectedRoute Component

All routes except `/login` are wrapped in a `ProtectedRoute` guard:

```javascript
const ProtectedRoute = ({ children }) => {
  if (!tokenStorage.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};
```

**Routing structure:**

| Route | Protection | Component |
|-------|-----------|-----------|
| `/login` | Public | `Login` |
| `/` | Protected | `Index` (Dashboard) |
| `/scanner` | Protected | `Scanner` |
| `/scanner/:id` | Protected | `ScanDetail` |
| `/threats` | Protected | `ThreatModel` |
| `/audit-log` | Protected | `AuditLog` |
| `/records` | Protected | `TamperProofRecords` |
| `/settings` | Protected | `Settings` |
| `*` | Protected | `NotFound` |

The `AppLayout` component renders the sidebar and content outlet, ensuring consistent navigation across all protected pages.

---

## API Security

### Transport

- All API calls use HTTPS in production
- `BASE_URL` is configured via `VITE_API_URL` environment variable
- Default: `http://localhost:8000/api` (development only)

### Request Headers

Every authenticated request includes:

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### CORS

Backend enforces whitelist-only CORS:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:8080` (alternative dev port)

No wildcard origins (`*`) are allowed.

### Error Handling

| Status | Behaviour |
|--------|-----------|
| 200–299 | Parse JSON response |
| 204 | Return `null` (no body) |
| 401 | Attempt silent refresh → retry once → redirect to `/login` |
| 4xx / 5xx | Parse error JSON, throw with `detail` message |

Error messages surface via `sonner` toast notifications.

---

## Input Validation

### Contract Address Validation

Ethereum addresses are validated on the frontend before submission:

```javascript
function isValidEthAddress(addr) {
  return /^0x[0-9a-fA-F]{40}$/.test(addr);
}
```

- Must start with `0x`
- Must be exactly 42 characters (2 + 40 hex)
- Invalid addresses disable the Scan button

### Source Code Handling

- Source code is sent as raw text (no file processing on the frontend)
- DRF serializer validation on the backend enforces non-empty source for source-code scans
- Address-only scans bypass source validation entirely

### Finding Description Sanitisation

Scanner.jsx sanitises finding descriptions to prevent XSS from analyzer output:

```javascript
function sanitizeDescription(text) {
  // Strip HTML tags and normalise whitespace
}
```

---

## Content Security Policy

The `public/index.html` sets a restrictive CSP meta tag:

- `default-src 'self'` — only load resources from the same origin
- `script-src 'self'` — no inline scripts
- `style-src 'self' 'unsafe-inline'` — Tailwind requires inline styles
- `img-src 'self' data:` — allow data URIs for icons
- `connect-src 'self' <API_URL>` — restrict API connections

---

## Bot Mitigation

### robots.txt

`public/robots.txt` blocks known malicious crawlers:

```
User-agent: AhrefsBot
Disallow: /

User-agent: SemrushBot
Disallow: /

User-agent: *
Disallow: /api/
Allow: /
```

This prevents API endpoint discovery by web scrapers while allowing legitimate search engine indexing of the public login page.

### Login Honeypot

The Login page includes a honeypot field (`<input>` hidden via CSS) that bots fill automatically. If the honeypot field has a value on form submission, the request is silently discarded.

---

## Data Handling

### Sensitive Data

| Data Type | Storage | Exposure |
|-----------|---------|----------|
| Access token | `localStorage` | Sent in `Authorization` header only |
| Refresh token | `localStorage` | Sent to `/api/auth/refresh/` only |
| Credentials | Never stored | Sent once during login/register |
| Source code | In-memory (`useState`) | Sent to API, never cached |
| Findings | TanStack Query cache | In-memory, garbage collected on unmount |

### Token Lifecycle

1. **Created:** On successful login (stored in `localStorage`)
2. **Used:** On every authenticated API request (Bearer header)
3. **Refreshed:** Automatically on 401 response
4. **Cleared:** On logout or failed refresh

No tokens are ever sent as URL parameters or stored in cookies.

---

## OWASP Alignment

| OWASP Top 10 | Mitigation |
|--------------|-----------|
| **A01 Broken Access Control** | `ProtectedRoute` guard, JWT on all API calls, backend `IsAuthenticated` |
| **A02 Cryptographic Failures** | HTTPS transport, no sensitive data in URLs |
| **A03 Injection** | DRF serializer validation, finding description sanitisation |
| **A05 Security Misconfiguration** | CORS whitelist, CSP headers, no debug mode in production |
| **A07 Identity & Auth Failures** | JWT access+refresh flow, single-retry refresh, automatic session cleanup |
| **A09 Security Logging** | Every mutating API call logged as `AuditEvent` on the backend |