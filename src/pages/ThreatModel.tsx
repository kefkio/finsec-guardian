import { AlertTriangle, Shield, Zap, Eye, Users, Globe } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface Threat {
  id: string;
  name: string;
  category: string;
  icon: React.ElementType;
  stride: string;
  likelihood: number;
  impact: number;
  riskScore: number;
  status: "active" | "mitigated" | "monitoring";
  description: string;
  mitigations: string[];
}

const threats: Threat[] = [
  {
    id: "T-001",
    name: "Reentrancy Attack on DeFi Pools",
    category: "Smart Contract",
    icon: Zap,
    stride: "Tampering",
    likelihood: 85,
    impact: 95,
    riskScore: 92,
    status: "active",
    description: "Attacker exploits callback mechanisms to re-enter withdraw functions before state updates complete, draining pool funds.",
    mitigations: ["Apply Checks-Effects-Interactions pattern", "Use ReentrancyGuard from OpenZeppelin", "Implement pull-over-push payment patterns"],
  },
  {
    id: "T-002",
    name: "Flash Loan Oracle Manipulation",
    category: "DeFi Protocol",
    icon: Globe,
    stride: "Spoofing",
    likelihood: 70,
    impact: 90,
    riskScore: 82,
    status: "active",
    description: "Attacker uses flash loans to temporarily manipulate price oracle data, enabling profitable trades at artificial prices.",
    mitigations: ["Use TWAP oracles", "Implement Chainlink price feeds", "Add flash loan guards"],
  },
  {
    id: "T-003",
    name: "Front-Running / MEV Extraction",
    category: "Transaction Layer",
    icon: Eye,
    stride: "Information Disclosure",
    likelihood: 90,
    impact: 60,
    riskScore: 75,
    status: "monitoring",
    description: "Miners or bots observe pending transactions and insert their own transactions ahead to profit from price movements.",
    mitigations: ["Use commit-reveal schemes", "Implement Flashbots for private transactions", "Apply slippage protection"],
  },
  {
    id: "T-004",
    name: "Privilege Escalation via Proxy",
    category: "Access Control",
    icon: Users,
    stride: "Elevation of Privilege",
    likelihood: 55,
    impact: 95,
    riskScore: 70,
    status: "mitigated",
    description: "Attacker exploits uninitialized proxy implementation to gain admin access and upgrade contract to malicious version.",
    mitigations: ["Use initializer modifiers", "Implement UUPS pattern with access controls", "Add timelocks on upgrades"],
  },
  {
    id: "T-005",
    name: "Integer Overflow in Token Logic",
    category: "Smart Contract",
    icon: AlertTriangle,
    stride: "Tampering",
    likelihood: 40,
    impact: 80,
    riskScore: 55,
    status: "mitigated",
    description: "Unchecked arithmetic operations allow minting unlimited tokens or bypassing balance checks in pre-0.8.0 contracts.",
    mitigations: ["Use Solidity 0.8+ with built-in overflow checks", "Apply SafeMath for older versions", "Add explicit bounds validation"],
  },
];

const statusStyles: Record<string, string> = {
  active: "bg-destructive text-destructive-foreground",
  mitigated: "bg-success text-success-foreground",
  monitoring: "bg-warning text-warning-foreground",
};

const riskColor = (score: number) => {
  if (score >= 80) return "text-destructive";
  if (score >= 60) return "text-warning";
  if (score >= 40) return "text-info";
  return "text-success";
};

const riskBg = (score: number) => {
  if (score >= 80) return "bg-destructive";
  if (score >= 60) return "bg-warning";
  if (score >= 40) return "bg-info";
  return "bg-success";
};

const ThreatModel = () => {
  const activeThreats = threats.filter((t) => t.status === "active").length;
  const avgRisk = Math.round(threats.reduce((sum, t) => sum + t.riskScore, 0) / threats.length);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Threat <span className="text-gradient-primary">Model</span>
        </h1>
        <p className="text-sm text-muted-foreground font-mono mt-1">
          STRIDE-based threat analysis for DeFi protocols
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">Active Threats</p>
            <p className="text-3xl font-bold text-destructive mt-1">{activeThreats}</p>
          </CardContent>
        </Card>
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">Avg Risk Score</p>
            <p className={`text-3xl font-bold mt-1 ${riskColor(avgRisk)}`}>{avgRisk}</p>
          </CardContent>
        </Card>
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">Mitigated</p>
            <p className="text-3xl font-bold text-success mt-1">
              {threats.filter((t) => t.status === "mitigated").length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Threat Cards */}
      <div className="space-y-4">
        {threats.map((threat) => (
          <Card key={threat.id} className="border-border bg-card overflow-hidden">
            <CardContent className="p-0">
              <div className="flex flex-col lg:flex-row">
                {/* Left: Risk Score */}
                <div className="flex flex-col items-center justify-center p-6 lg:w-32 bg-secondary/30 border-b lg:border-b-0 lg:border-r border-border">
                  <p className={`text-3xl font-bold font-mono ${riskColor(threat.riskScore)}`}>
                    {threat.riskScore}
                  </p>
                  <p className="text-[10px] font-mono text-muted-foreground uppercase mt-1">Risk</p>
                </div>

                {/* Right: Content */}
                <div className="flex-1 p-5 space-y-3">
                  <div className="flex items-start justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <threat.icon className={`h-4 w-4 ${riskColor(threat.riskScore)}`} />
                      <h3 className="font-semibold text-sm">{threat.name}</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="font-mono text-xs">{threat.stride}</Badge>
                      <Badge className={statusStyles[threat.status]}>{threat.status}</Badge>
                    </div>
                  </div>

                  <p className="text-xs text-muted-foreground leading-relaxed">{threat.description}</p>

                  {/* Likelihood / Impact bars */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs font-mono text-muted-foreground">
                        <span>Likelihood</span>
                        <span>{threat.likelihood}%</span>
                      </div>
                      <Progress value={threat.likelihood} className="h-1.5" />
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs font-mono text-muted-foreground">
                        <span>Impact</span>
                        <span>{threat.impact}%</span>
                      </div>
                      <Progress value={threat.impact} className="h-1.5" />
                    </div>
                  </div>

                  {/* Mitigations */}
                  <div className="space-y-1">
                    <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Mitigations</p>
                    {threat.mitigations.map((m, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-primary font-mono">
                        <Shield className="h-3 w-3 shrink-0" />
                        {m}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ThreatModel;
