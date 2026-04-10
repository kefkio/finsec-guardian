import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Shield, X, ExternalLink, ChevronRight, Zap, BarChart3, FileSearch,
  Bug, AlertOctagon, BookOpen, Menu, Activity, Code2,
  TrendingUp, Sparkles, Lock, Eye, ShieldAlert, ArrowRight, CheckCircle2,
  ScrollText, GitBranch, ScanLine, Cpu, Fingerprint, ClipboardList,
  Sun, Moon
} from "lucide-react";
import { authApi } from "@/lib/api";
import { useTheme } from "@/hooks/use-theme";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const PLATFORM_FEATURES = [
  {
    icon: ScanLine,
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    title: "Slither-Powered Static Analysis",
    description: "Paste or upload any Solidity contract and get a deep static analysis via Slither — the industry-leading smart contract analysis framework from Trail of Bits.",
    badge: "Core Engine",
  },
  {
    icon: ShieldAlert,
    color: "text-rose-500",
    bg: "bg-rose-500/10",
    title: "OWASP SC Top 10 Classification",
    description: "Every vulnerability is mapped to the OWASP Smart Contract Top 10, giving your security and dev teams a shared language to prioritise fixes by real-world risk.",
    badge: "OWASP SC",
  },
  {
    icon: Bug,
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    title: "80+ Vulnerability Detectors",
    description: "From reentrancy and integer overflow to unprotected upgrades and arbitrary send — FinSec Guardian runs 80+ detectors covering the full SWC Registry.",
    badge: "Detectors",
  },
  {
    icon: TrendingUp,
    color: "text-cyan-500",
    bg: "bg-cyan-500/10",
    title: "STRIDE Threat Modelling",
    description: "Model your contracts against the STRIDE threat framework. Assess spoofing, tampering, repudiation, info disclosure, DoS, and privilege escalation risks before deployment.",
    badge: "Threat Model",
  },
  {
    icon: ScrollText,
    color: "text-violet-500",
    bg: "bg-violet-500/10",
    title: "Tamper-Proof Audit Reports",
    description: "Every scan produces an immutable, time-stamped audit report. SHA-256 hashed findings give auditors and regulators a verifiable security record.",
    badge: "Audit Trail",
  },
  {
    icon: Code2,
    color: "text-sky-500",
    bg: "bg-sky-500/10",
    title: "Multi-Version Solidity Support",
    description: "Analyse contracts written in any Solidity version from 0.4.x through 0.8.x. FinSec Guardian automatically selects the right compiler to match your pragma.",
    badge: "Solidity",
  },
];

const TRUST_BADGES = [
  { label: "Slither-powered analysis" },
  { label: "OWASP SC Top 10 aligned" },
  { label: "80+ vulnerability detectors" },
  { label: "Tamper-proof audit trail" },
];

const NAV_ITEMS = [
  { label: "How It Works",    href: "#why",          icon: Zap },
  { label: "Features",        href: "#platform",     icon: BarChart3 },
  { label: "Risk Coverage",   href: "#why",          icon: FileSearch },
  { label: "Free Audit",      href: "#free-audit",   icon: AlertOctagon },
  { label: "OWASP SC Top 10", href: "https://scs.owasp.org/sctop10/", icon: Bug },
  { label: "Resources",       href: "https://github.com/crytic/slither", icon: BookOpen },
];

const VALUE_PROPS = [
  {
    icon: FileSearch,
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    border: "hover:border-emerald-500/40",
    title: "Comprehensive Evaluation",
    badge: "Analysis",
    points: [
      "Deep static analysis of Solidity smart contracts",
      "Detects reentrancy, overflow, access control flaws & more",
      "Findings classified per OWASP Smart Contract Top 10",
    ],
  },
  {
    icon: TrendingUp,
    color: "text-cyan-500",
    bg: "bg-cyan-500/10",
    border: "hover:border-cyan-500/40",
    title: "Actionable Insights",
    badge: "Reports",
    points: [
      "Structured reports with severity-ranked findings",
      "SWC ID, threat classification, and impact per issue",
      "Specific remediation recommendations per vulnerability",
    ],
  },
  {
    icon: Lock,
    color: "text-violet-500",
    bg: "bg-violet-500/10",
    border: "hover:border-violet-500/40",
    title: "Non-Intrusive Analysis",
    badge: "Zero Setup",
    points: [
      "No deployment needed — paste source code directly",
      "Works on undeployed contracts before launch",
      "Zero changes to your existing codebase or toolchain",
    ],
  },
];

const Login = () => {
  const navigate = useNavigate();
  const { theme, toggle: toggleTheme } = useTheme();
  const [bannerVisible, setBannerVisible] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [tab, setTab] = useState("login");
  const [loading, setLoading] = useState(false);
  const [auditConsent, setAuditConsent] = useState(false);
  const [auditRequested, setAuditRequested] = useState(false);
  const [form, setForm] = useState({ username: "", email: "", password: "" });

  const scrollToAuth = (t = "login") => {
    setTab(t);
    document.getElementById("auth-card")?.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  const handleChange = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.login(form.username, form.password);
      navigate("/", { replace: true });
    } catch (err) {
      toast.error(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.register(form.username, form.email, form.password);
      toast.success("Account created — please log in.");
      setTab("login");
      setForm((prev) => ({ ...prev, password: "" }));
    } catch (err) {
      toast.error(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">

      {/* ── OWASP Banner ─────────────────────────────────────────────── */}
      {bannerVisible && (
        <div className="relative bg-gradient-to-r from-cyan-600 via-teal-600 to-emerald-600 text-white text-sm">
          <a
            href="https://scs.owasp.org/sctop10/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 px-10 py-2.5 hover:opacity-90 transition-opacity"
          >
            <Shield className="h-4 w-4 shrink-0" />
            <span className="font-mono font-medium">
              🔐 OWASP Smart Contract Top 10 — know the top vulnerabilities before you deploy
            </span>
            <ExternalLink className="h-3.5 w-3.5 shrink-0" />
            <span className="ml-1 underline underline-offset-2 font-semibold">View list →</span>
          </a>
          <button
            onClick={() => setBannerVisible(false)}
            aria-label="Dismiss banner"
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-white/20 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* ── Top Navigation Bar ───────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2.5 shrink-0">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-primary">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <span className="text-base font-bold tracking-tight text-foreground">
              FinSec<span className="text-gradient-primary">Guardian</span>
            </span>
          </a>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map(({ label, href }) => (
              <a
                key={label}
                href={href}
                target={href.startsWith('http') ? '_blank' : undefined}
                rel={href.startsWith('http') ? 'noopener noreferrer' : undefined}
                className="px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground rounded-md hover:bg-muted transition-colors"
              >
                {label}
              </a>
            ))}
          </nav>

          {/* CTA buttons */}
          <div className="hidden md:flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="p-2 text-muted-foreground hover:text-foreground"
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="font-mono text-sm"
              onClick={() => scrollToAuth("login")}
            >
              Sign in
            </Button>
            <Button
              size="sm"
              className="gradient-primary text-primary-foreground font-mono font-semibold"
              onClick={() => scrollToAuth("register")}
            >
              Get started <ChevronRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border bg-background px-4 pb-4 pt-2 space-y-1">
            {NAV_ITEMS.map(({ label, href, icon: Icon }) => (
                <a
                  key={label}
                  href={href}
                  target={href.startsWith('http') ? '_blank' : undefined}
                  rel={href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground rounded-md hover:bg-muted transition-colors"
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </a>
            ))}
            <div className="pt-2 flex gap-2">
              <Button variant="outline" size="sm" className="flex-1 font-mono" onClick={() => { scrollToAuth("login"); setMobileMenuOpen(false); }}>Sign in</Button>
              <Button size="sm" className="flex-1 gradient-primary text-primary-foreground font-mono" onClick={() => { scrollToAuth("register"); setMobileMenuOpen(false); }}>Get started</Button>
              <Button variant="outline" size="sm" onClick={toggleTheme} aria-label="Toggle theme" className="px-3">
                {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        )}
      </header>

      {/* ── Hero + Auth Card ─────────────────────────────────────────── */}
      <main className="flex flex-1 flex-col items-center justify-center px-4 py-16 gap-12">

        {/* Hero text */}
        <div className="text-center max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-muted px-3 py-1 text-xs font-mono text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Smart Contract Security Platform
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-foreground leading-tight">
            Audit smarter.<br />
            <span className="text-gradient-primary">Deploy safer.</span>
          </h1>
          <p className="text-base text-muted-foreground max-w-lg mx-auto leading-relaxed">
            Paste any Solidity contract and get a full static analysis report in seconds —
            powered by Slither, classified against the OWASP Smart Contract Top 10, with
            tamper-proof audit records built in.
          </p>
        </div>

        {/* Auth Card */}
        <div className="w-full max-w-sm" id="auth-card">
          <Card className="border-border bg-card shadow-lg">
            <CardHeader className="pb-3">
              <div className="flex gap-1 rounded-md bg-muted p-1 font-mono text-xs">
                {["login", "register"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className={`flex-1 rounded py-1.5 font-semibold capitalize transition-colors ${
                      tab === t
                        ? "bg-background text-foreground shadow"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {t === "login" ? "Sign in" : "Register"}
                  </button>
                ))}
              </div>
              <CardTitle className="sr-only">
                {tab === "login" ? "Sign in" : "Create account"}
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground pt-1">
                {tab === "login"
                  ? "Sign in to access your security dashboard."
                  : "Create a free account to get started."}
              </CardDescription>
            </CardHeader>

            <CardContent>
              <form
                onSubmit={tab === "login" ? handleLogin : handleRegister}
                className="space-y-4"
              >
                <div className="space-y-1.5">
                  <Label htmlFor="username" className="font-mono text-xs">Username</Label>
                  <Input
                    id="username"
                    name="username"
                    autoComplete="username"
                    required
                    value={form.username}
                    onChange={handleChange}
                    className="font-mono text-sm"
                    placeholder="your_username"
                  />
                </div>

                {tab === "register" && (
                  <div className="space-y-1.5">
                    <Label htmlFor="email" className="font-mono text-xs">Email</Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      value={form.email}
                      onChange={handleChange}
                      className="font-mono text-sm"
                      placeholder="you@example.com"
                    />
                  </div>
                )}

                <div className="space-y-1.5">
                  <Label htmlFor="password" className="font-mono text-xs">Password</Label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete={tab === "login" ? "current-password" : "new-password"}
                    required
                    value={form.password}
                    onChange={handleChange}
                    className="font-mono text-sm"
                    placeholder="••••••••"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full gradient-primary text-primary-foreground font-mono font-semibold"
                >
                  {loading
                    ? tab === "login" ? "Signing in…" : "Creating account…"
                    : tab === "login" ? "Sign in" : "Create account"}
                </Button>
              </form>
            </CardContent>
          </Card>

          <p className="mt-4 text-center text-xs text-muted-foreground">
            By signing up you agree to our{" "}
            <a href="#" className="underline underline-offset-2 hover:text-foreground">Terms</a>
            {" "}and{" "}
            <a href="#" className="underline underline-offset-2 hover:text-foreground">Privacy Policy</a>.
          </p>
        </div>
      </main>

      {/* ── Value Props Section ──────────────────────────────────────── */}
      <section id="why" className="w-full py-20 px-4">
        <div className="mx-auto max-w-6xl space-y-12">

          {/* Heading */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-muted px-3 py-1 text-xs font-mono text-muted-foreground">
              <Shield className="h-3.5 w-3.5 text-emerald-500" />
              Why FinSec Guardian
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground">
              Catch vulnerabilities<br />
              <span className="text-gradient-primary">before they're exploited.</span>
            </h2>
            <p className="text-muted-foreground text-base max-w-xl mx-auto leading-relaxed">
              Paste your Solidity source code and get a full vulnerability report —
              OWASP SC Top 10 classified findings, SWC IDs, severity ratings,
              and concrete remediation steps.
            </p>
          </div>

          {/* Three pillars */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {VALUE_PROPS.map(({ icon: Icon, color, bg, border, title, badge, points }) => (
              <div
                key={title}
                className={`relative rounded-xl border border-border bg-card p-8 space-y-5 transition-all duration-200 hover:shadow-lg ${border}`}
              >
                <div className="flex items-start justify-between">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${bg}`}>
                    <Icon className={`h-6 w-6 ${color}`} />
                  </div>
                  <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-muted-foreground border border-border rounded-full px-2 py-0.5">
                    {badge}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-foreground">{title}</h3>
                <ul className="space-y-3">
                  {points.map((pt) => (
                    <li key={pt} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                      <CheckCircle2 className={`h-4 w-4 shrink-0 mt-0.5 ${color}`} />
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* CTA nudge */}
          <div className="flex justify-center">
            <Button
              size="sm"
              className="gradient-primary text-primary-foreground font-mono font-semibold"
              onClick={() => document.getElementById('auth-card')?.scrollIntoView({ behavior: 'smooth' })}
            >
              Get started — it's free <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
            </Button>
          </div>
        </div>
      </section>

      {/* ── Integrations & Features Section ─────────────────────────── */}
      <section id="platform" className="w-full bg-muted/30 border-y border-border py-20 px-4">
        <div className="mx-auto max-w-6xl space-y-14">

          {/* Section heading */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1 text-xs font-mono text-muted-foreground">
              <Activity className="h-3.5 w-3.5 text-emerald-500" />
              Platform Capabilities
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground">
              One contract scan.<br />
              <span className="text-gradient-primary">Your full vulnerability picture.</span>
            </h2>
            <p className="text-muted-foreground text-base max-w-xl mx-auto">
              FinSec Guardian runs Slither static analysis against your Solidity contracts,
              maps every finding to the OWASP SC Top 10, and delivers structured reports
              with actionable remediation — in seconds.
            </p>
          </div>

          {/* Feature cards grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {PLATFORM_FEATURES.map(({ icon: Icon, color, bg, title, description, badge }) => (
              <div
                key={title}
                className="group relative rounded-xl border border-border bg-background p-6 space-y-4 hover:border-primary/40 hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-start justify-between">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${bg}`}>
                    <Icon className={`h-5 w-5 ${color}`} />
                  </div>
                  <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-muted-foreground border border-border rounded-full px-2 py-0.5">
                    {badge}
                  </span>
                </div>
                <div className="space-y-1.5">
                  <h3 className="text-sm font-semibold text-foreground">{title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{description}</p>
                </div>
                <div className="flex items-center gap-1 text-xs font-mono text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                  Learn more <ArrowRight className="h-3 w-3" />
                </div>
              </div>
            ))}
          </div>

          {/* Trust badges */}
          <div className="flex flex-wrap items-center justify-center gap-3">
            {TRUST_BADGES.map(({ label }) => (
              <div
                key={label}
                className="flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-xs font-mono text-muted-foreground"
              >
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                {label}
              </div>
            ))}
          </div>

          {/* CTA row */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2.5 text-sm font-mono text-muted-foreground">
              <Code2 className="h-4 w-4 text-emerald-500" />
              <span>Paste Solidity contract</span>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground hidden sm:block" />
            <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2.5 text-sm font-mono text-muted-foreground">
              <ScrollText className="h-4 w-4 text-cyan-500" />
              <span>Get vulnerability report</span>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground hidden sm:block" />
            <Button
              size="sm"
              className="gradient-primary text-primary-foreground font-mono font-semibold"
              onClick={() => document.getElementById('free-audit')?.scrollIntoView({ behavior: 'smooth' })}
            >
              <Zap className="h-3.5 w-3.5 mr-1.5" />
              Try free scan
            </Button>
          </div>
        </div>
      </section>

      {/* ── Free Audit CTA Section ──────────────────────────────────── */}
      <section id="free-audit" className="w-full py-20 px-4">
        <div className="mx-auto max-w-2xl">
          <div className="relative rounded-2xl border border-border bg-card p-8 sm:p-12 space-y-8 overflow-hidden">
            {/* Decorative glow */}
            <div className="pointer-events-none absolute -top-20 -right-20 h-64 w-64 rounded-full bg-emerald-500/10 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-cyan-500/10 blur-3xl" />

            {/* Heading */}
            <div className="relative space-y-3 text-center">
              <div className="inline-flex items-center gap-2 rounded-full border border-border bg-muted px-3 py-1 text-xs font-mono text-muted-foreground">
                <Shield className="h-3.5 w-3.5 text-emerald-500" />
                Free Security Assessment
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight">
                Sign Up to Discover Your{" "}
                <span className="text-gradient-primary">Critical Security Risks</span>
              </h2>
              <p className="text-sm text-muted-foreground max-w-lg mx-auto leading-relaxed">
              Submit your Solidity contract and receive a full Slither-powered vulnerability
              report — OWASP SC Top 10 classified findings, SWC IDs, severity ratings,
              and specific remediation steps. No deployment required.
              </p>
            </div>

            {/* Privacy consent */}
            <div className="relative rounded-xl border border-border bg-background/60 p-5 space-y-3">
              <p className="text-xs text-muted-foreground leading-relaxed">
                FinSec Guardian respects your privacy and will only use your personal
                information to contact you about new product information, sales offers,
                research, and/or invitations to events. If you consent to FinSec Guardian
                using your personal information for these purposes, please check the box
                below. You will have the opportunity to unsubscribe at any time by
                contacting{" "}
                <a
                  href="mailto:datasubjectsrights@finsec.com"
                  className="text-primary hover:underline font-mono"
                >
                  datasubjectsrights@finsec.com
                </a>
                .
              </p>
              <label className="flex items-start gap-3 cursor-pointer group">
                <div className="relative mt-0.5 shrink-0">
                  <input
                    type="checkbox"
                    id="audit-consent"
                    checked={auditConsent}
                    onChange={(e) => setAuditConsent(e.target.checked)}
                    className="sr-only"
                  />
                  <div
                    className={`h-4 w-4 rounded border-2 transition-all duration-150 flex items-center justify-center ${
                      auditConsent
                        ? "border-emerald-500 bg-emerald-500"
                        : "border-border bg-background group-hover:border-primary"
                    }`}
                  >
                    {auditConsent && (
                      <svg viewBox="0 0 10 8" className="h-2.5 w-2.5 fill-none stroke-white stroke-2 stroke-round">
                        <polyline points="1,4 3.5,6.5 9,1" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                  </div>
                </div>
                <span className="text-xs text-muted-foreground leading-relaxed">
                  I agree that FinSec Guardian may use my personal information for the
                  purposes described above, including sending product updates, security
                  insights, and event invitations.
                </span>
              </label>
            </div>

            {/* CTA button */}
            <div className="relative flex flex-col items-center gap-3">
              {auditRequested ? (
                <div className="flex items-center gap-2 text-emerald-500 font-mono text-sm font-semibold">
                  <CheckCircle2 className="h-5 w-5" />
                  Request received — we'll be in touch shortly!
                </div>
              ) : (
                <Button
                  size="lg"
                  disabled={!auditConsent}
                  className="gradient-primary text-primary-foreground font-mono font-bold px-8 disabled:opacity-40 disabled:cursor-not-allowed"
                  onClick={() => {
                    if (auditConsent) setAuditRequested(true);
                  }}
                >
                  <FileSearch className="h-4 w-4 mr-2" />
                  Request Free Audit &amp; Analysis
                </Button>
              )}
              {!auditConsent && !auditRequested && (
                <p className="text-[11px] text-muted-foreground font-mono">
                  Please accept the privacy terms above to continue.
                </p>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-border py-6 px-4 text-center">
        <p className="text-xs font-mono text-muted-foreground">
          © {new Date().getFullYear()} FinSec Guardian · Built on{" "}
          <a
            href="https://scs.owasp.org/sctop10/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            OWASP SC Top 10
          </a>
          {" "}standards · Contact{" "}
          <a href="mailto:datasubjectsrights@finsec.com" className="text-primary hover:underline">
            datasubjectsrights@finsec.com
          </a>
        </p>
      </footer>

    </div>
  );
};

export default Login;
