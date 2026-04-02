import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Shield, X, ExternalLink, ChevronRight, Zap, BarChart3, FileSearch, Bug, FlaskConical, BookOpen, Menu } from "lucide-react";
import { authApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

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
        <div className="w-full max-w-sm">
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
