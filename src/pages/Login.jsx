import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Shield, X, ExternalLink, ChevronRight, Zap, BarChart3, FileSearch,
  Bug, FlaskConical, BookOpen, Menu, Github, Bell, GitBranch,
  TrendingUp, Sparkles, Lock, Eye, Code2, ArrowRight, CheckCircle2
} from "lucide-react";
import { authApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

/* ── Slack SVG icon (no lucide equivalent) ──────────────────────────── */
const SlackIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" className={className} fill="currentColor">
    <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
  </svg>
);

const INTEGRATION_STEPS = [
  {
    icon: Github,
    color: "text-foreground",
    bg: "bg-muted",
    title: "Connect GitHub Repositories",
    description: "Seamlessly link any public or private GitHub repo. DeFiGuard watches every push, PR, and release automatically.",
    badge: "GitHub",
  },
  {
    icon: SlackIcon,
    color: "text-[#4A154B]",
    bg: "bg-[#4A154B]/10",
    title: "Real-Time Slack Alerts",
    description: "Pipe critical vulnerability findings straight to your team's Slack workspace the moment a scan completes.",
    badge: "Slack",
  },
  {
    icon: GitBranch,
    color: "text-cyan-500",
    bg: "bg-cyan-500/10",
    title: "Automated Scan Triggers",
    description: "Configure branch-level triggers — scan on push, on PR open, or on a schedule. Zero manual intervention required.",
    badge: "CI/CD",
  },
  {
    icon: TrendingUp,
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    title: "Code Quality Trend Monitoring",
    description: "Track vulnerability counts, severity trends, and fix velocity across every release. Spot regressions before they ship.",
    badge: "Analytics",
  },
  {
    icon: Sparkles,
    color: "text-violet-500",
    bg: "bg-violet-500/10",
    title: "AI-Powered Insights",
    description: "Our AI engine correlates findings with historical data to surface root causes and suggest targeted refactors.",
    badge: "AI",
  },
  {
    icon: Eye,
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    title: "Unparalleled Codebase Visibility",
    description: "Dependency graphs, hot-spot heatmaps, and cross-contract call analysis give you the full picture every time.",
    badge: "Insights",
  },
];

const TRUST_BADGES = [
  { label: "Slither-powered analysis" },
  { label: "OWASP SC Top 10 aligned" },
  { label: "GitHub & Slack native" },
  { label: "SOC 2-ready audit logs" },
];

const NAV_ITEMS = [
  { label: "QuickScan",     href: "#quickscan",  icon: Zap },
  { label: "Pricing",       href: "#pricing",    icon: BarChart3 },
  { label: "Audit Reports", href: "#reports",    icon: FileSearch },
  { label: "Detectors",     href: "#detectors",  icon: Bug },
  { label: "Web3 Hacklab",  href: "#hacklab",    icon: FlaskConical },
  { label: "Resources",     href: "#resources",  icon: BookOpen },
];

const Login = () => {
  const navigate = useNavigate();
  const [bannerVisible, setBannerVisible] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [tab, setTab] = useState("login");
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ username: "", email: "", password: "" });

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

      {/* ── OWASP SC Top 10 Banner ───────────────────────────────────── */}
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
              DeFi<span className="text-gradient-primary">Guard</span>
            </span>
          </a>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map(({ label, href }) => (
              <a
                key={label}
                href={href}
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
              className="font-mono text-sm"
              onClick={() => setTab("login")}
            >
              Sign in
            </Button>
            <Button
              size="sm"
              className="gradient-primary text-primary-foreground font-mono font-semibold"
              onClick={() => setTab("register")}
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
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground rounded-md hover:bg-muted transition-colors"
              >
                <Icon className="h-4 w-4" />
                {label}
              </a>
            ))}
            <div className="pt-2 flex gap-2">
              <Button variant="outline" size="sm" className="flex-1 font-mono" onClick={() => { setTab("login"); setMobileMenuOpen(false); }}>Sign in</Button>
              <Button size="sm" className="flex-1 gradient-primary text-primary-foreground font-mono" onClick={() => { setTab("register"); setMobileMenuOpen(false); }}>Get started</Button>
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
            Static analysis, threat modelling, and tamper-proof audit reports for
            Solidity smart contracts — powered by Slither and the OWASP SC Top 10.
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

      {/* ── Integrations & Features Section ─────────────────────────── */}
      <section className="w-full bg-muted/30 border-y border-border py-20 px-4">
        <div className="mx-auto max-w-6xl space-y-14">

          {/* Section heading */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1 text-xs font-mono text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5 text-violet-500" />
              Integrations &amp; Intelligence
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground">
              Your entire security workflow,<br />
              <span className="text-gradient-primary">fully automated.</span>
            </h2>
            <p className="text-muted-foreground text-base max-w-xl mx-auto">
              Connect GitHub and Slack in seconds. Configure scan triggers, track quality
              trends with AI, and gain unparalleled codebase insights — all in one platform.
            </p>
          </div>

          {/* Feature cards grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {INTEGRATION_STEPS.map(({ icon: Icon, color, bg, title, description, badge }) => (
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
              <Github className="h-4 w-4" />
              <span>github.com/your-org/your-repo</span>
            </div>
            <div className="flex items-center gap-1.5 text-muted-foreground text-sm font-mono">
              <span>+</span>
              <SlackIcon className="h-4 w-4 text-[#4A154B]" />
              <span>#security-alerts</span>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground hidden sm:block" />
            <Button
              size="sm"
              className="gradient-primary text-primary-foreground font-mono font-semibold"
              onClick={() => document.getElementById('auth-card')?.scrollIntoView({ behavior: 'smooth' })}
            >
              <Zap className="h-3.5 w-3.5 mr-1.5" />
              Start free — connect now
            </Button>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-border py-6 px-4 text-center">
        <p className="text-xs font-mono text-muted-foreground">
          © {new Date().getFullYear()} DeFiGuard · Built on{" "}
          <a
            href="https://scs.owasp.org/sctop10/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            OWASP SC Top 10
          </a>
          {" "}standards
        </p>
      </footer>

    </div>
  );
};

export default Login;
