import { Shield, Search, AlertTriangle, Link2, ScrollText, Zap, Lock, Eye, ArrowRight, ChevronRight, Hexagon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";

const features = [
  {
    icon: Search,
    title: "Contract Scanner",
    description: "Deep static analysis of Solidity smart contracts. Detect reentrancy, overflow, and access control flaws before deployment.",
    color: "text-primary",
    glow: "glow-primary",
  },
  {
    icon: AlertTriangle,
    title: "Threat Modeling",
    description: "Automated STRIDE-based threat models for DeFi protocols. Visualize attack surfaces and prioritize mitigations.",
    color: "text-warning",
    glow: "glow-danger",
  },
  {
    icon: Link2,
    title: "Tamper-Proof Records",
    description: "SHA-256 hash-chained audit ledger with blockchain anchoring. Cryptographic proof that records haven't been altered.",
    color: "text-accent",
    glow: "glow-accent",
  },
  {
    icon: ScrollText,
    title: "Audit Log",
    description: "Immutable timeline of every security event, scan, and configuration change across your organization.",
    color: "text-info",
    glow: "glow-primary",
  },
];

const metrics = [
  { value: "142+", label: "Contracts Scanned" },
  { value: "23", label: "Critical Vulns Found" },
  { value: "99.9%", label: "Uptime SLA" },
  { value: "<2s", label: "Avg Scan Time" },
];

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      {/* Nav */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="container mx-auto flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg gradient-primary">
              <Shield className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold tracking-tight">
              DeFi<span className="text-gradient-primary">Guard</span>
            </span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-mono">Features</a>
            <a href="#metrics" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-mono">Metrics</a>
            <a href="#security" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-mono">Security</a>
          </nav>
          <Button onClick={() => navigate("/")} className="gradient-primary text-primary-foreground font-mono text-sm">
            Launch App <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6">
        {/* Background effects */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[800px] rounded-full bg-primary/5 blur-[120px]" />
          <div className="absolute top-1/3 left-1/4 w-[400px] h-[400px] rounded-full bg-accent/5 blur-[100px]" />
          <div className="absolute inset-0 scanline opacity-30" />
        </div>

        <div className="container mx-auto relative z-10 max-w-5xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 mb-8">
            <div className="h-2 w-2 rounded-full bg-primary animate-pulse-glow" />
            <span className="text-xs font-mono text-primary">SECURITY ENGINE ACTIVE</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.1] mb-6">
            Smart Contract
            <br />
            <span className="text-gradient-primary">Security Suite</span>
          </h1>

          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
            Military-grade vulnerability detection for DeFi protocols. Scan contracts, model threats, and maintain tamper-proof audit records — all in one platform.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              size="lg"
              onClick={() => navigate("/")}
              className="gradient-primary text-primary-foreground font-mono text-sm h-12 px-8 glow-primary"
            >
              Enter Dashboard <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate("/scanner")}
              className="font-mono text-sm h-12 px-8 border-border hover:border-primary/50 hover:bg-primary/5"
            >
              <Search className="mr-2 h-4 w-4" /> Try Scanner
            </Button>
          </div>

          {/* Terminal preview */}
          <div className="mt-16 mx-auto max-w-3xl rounded-xl border border-border bg-card/80 backdrop-blur-sm overflow-hidden shadow-2xl">
            <div className="flex items-center gap-2 border-b border-border px-4 py-3">
              <div className="h-3 w-3 rounded-full bg-destructive/60" />
              <div className="h-3 w-3 rounded-full bg-warning/60" />
              <div className="h-3 w-3 rounded-full bg-success/60" />
              <span className="ml-3 text-xs font-mono text-muted-foreground">defiguard scan --deep UniswapV3Pool.sol</span>
            </div>
            <div className="p-5 font-mono text-xs text-left space-y-1.5">
              <p className="text-muted-foreground">[<span className="text-primary">INFO</span>] Loading contract: UniswapV3Pool.sol</p>
              <p className="text-muted-foreground">[<span className="text-primary">INFO</span>] Running static analysis engine...</p>
              <p className="text-muted-foreground">[<span className="text-warning">WARN</span>] Potential reentrancy at <span className="text-foreground">swap():L142</span></p>
              <p className="text-muted-foreground">[<span className="text-destructive">CRIT</span>] Unchecked external call at <span className="text-foreground">flash():L298</span></p>
              <p className="text-muted-foreground">[<span className="text-warning">WARN</span>] Missing access control on <span className="text-foreground">setFee():L401</span></p>
              <p className="text-muted-foreground">[<span className="text-primary">INFO</span>] Hash chain anchored: <span className="text-primary">0x7f3a...e9c1</span></p>
              <p className="text-success mt-3">✓ Scan complete — 3 findings (1 critical, 2 warnings)</p>
            </div>
          </div>
        </div>
      </section>

      {/* Metrics */}
      <section id="metrics" className="py-16 px-6 border-y border-border/50">
        <div className="container mx-auto max-w-4xl">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {metrics.map((m) => (
              <div key={m.label} className="text-center">
                <p className="text-3xl md:text-4xl font-bold text-gradient-primary">{m.value}</p>
                <p className="text-xs font-mono text-muted-foreground mt-2 uppercase tracking-wider">{m.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-6">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
              Built for <span className="text-gradient-primary">DeFi Security</span>
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Every tool you need to audit, monitor, and prove the integrity of smart contract systems.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-5">
            {features.map((f) => (
              <Card key={f.title} className="border-border bg-card/50 hover:bg-card transition-colors group">
                <CardContent className="p-6">
                  <div className={`inline-flex items-center justify-center h-10 w-10 rounded-lg bg-secondary mb-4 ${f.color}`}>
                    <f.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-bold mb-2">{f.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{f.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Security Pillars */}
      <section id="security" className="py-20 px-6 border-t border-border/50">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
              Security <span className="text-gradient-primary">Principles</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: Lock, title: "Zero Trust", desc: "Every action is authenticated and verified. No implicit trust boundaries." },
              { icon: Eye, title: "Full Transparency", desc: "Open audit trails with cryptographic proofs. Nothing is hidden." },
              { icon: Zap, title: "Real-Time Detection", desc: "Continuous monitoring with sub-second threat identification." },
            ].map((p) => (
              <div key={p.title} className="text-center p-6">
                <div className="inline-flex items-center justify-center h-12 w-12 rounded-xl gradient-primary mb-4">
                  <p.icon className="h-6 w-6 text-primary-foreground" />
                </div>
                <h3 className="font-bold mb-2">{p.title}</h3>
                <p className="text-sm text-muted-foreground">{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="container mx-auto max-w-3xl text-center">
          <div className="rounded-2xl border border-primary/20 bg-primary/5 p-12">
            <h2 className="text-3xl font-bold mb-4">
              Ready to Secure Your Contracts?
            </h2>
            <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
              Start scanning your smart contracts for vulnerabilities in seconds.
            </p>
            <Button
              size="lg"
              onClick={() => navigate("/")}
              className="gradient-primary text-primary-foreground font-mono h-12 px-8 glow-primary"
            >
              Launch DeFiGuard <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-8 px-6">
        <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-mono text-muted-foreground">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-primary" />
            <span>DeFiGuard v1.0.0</span>
          </div>
          <p>© 2026 DeFiGuard. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
