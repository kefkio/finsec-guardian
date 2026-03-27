import { AlertTriangle, Shield, Zap, Eye, Users, Globe } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
const threats = [{
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
  mitigations: ["Apply Checks-Effects-Interactions pattern", "Use ReentrancyGuard from OpenZeppelin", "Implement pull-over-push payment patterns"]
}, {
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
  mitigations: ["Use TWAP oracles", "Implement Chainlink price feeds", "Add flash loan guards"]
}, {
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
  mitigations: ["Use commit-reveal schemes", "Implement Flashbots for private transactions", "Apply slippage protection"]
}, {
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
  mitigations: ["Use initializer modifiers", "Implement UUPS pattern with access controls", "Add timelocks on upgrades"]
}, {
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
  mitigations: ["Use Solidity 0.8+ with built-in overflow checks", "Apply SafeMath for older versions", "Add explicit bounds validation"]
}];
const statusStyles = {
  active: "bg-destructive text-destructive-foreground",
  mitigated: "bg-success text-success-foreground",
  monitoring: "bg-warning text-warning-foreground"
};
const riskColor = score => {
  if (score >= 80) return "text-destructive";
  if (score >= 60) return "text-warning";
  if (score >= 40) return "text-info";
  return "text-success";
};
const riskBg = score => {
  if (score >= 80) return "bg-destructive";
  if (score >= 60) return "bg-warning";
  if (score >= 40) return "bg-info";
  return "bg-success";
};
const ThreatModel = () => {
  const activeThreats = threats.filter(t => t.status === "active").length;
  const avgRisk = Math.round(threats.reduce((sum, t) => sum + t.riskScore, 0) / threats.length);
  return /*#__PURE__*/_jsxs("div", {
    className: "space-y-6",
    children: [/*#__PURE__*/_jsxs("div", {
      children: [/*#__PURE__*/_jsxs("h1", {
        className: "text-2xl font-bold tracking-tight",
        children: ["Threat ", /*#__PURE__*/_jsx("span", {
          className: "text-gradient-primary",
          children: "Model"
        })]
      }), /*#__PURE__*/_jsx("p", {
        className: "text-sm text-muted-foreground font-mono mt-1",
        children: "STRIDE-based threat analysis for DeFi protocols"
      })]
    }), /*#__PURE__*/_jsxs("div", {
      className: "grid gap-4 md:grid-cols-3",
      children: [/*#__PURE__*/_jsx(Card, {
        className: "border-border bg-card",
        children: /*#__PURE__*/_jsxs(CardContent, {
          className: "p-4",
          children: [/*#__PURE__*/_jsx("p", {
            className: "text-xs font-mono uppercase tracking-wider text-muted-foreground",
            children: "Active Threats"
          }), /*#__PURE__*/_jsx("p", {
            className: "text-3xl font-bold text-destructive mt-1",
            children: activeThreats
          })]
        })
      }), /*#__PURE__*/_jsx(Card, {
        className: "border-border bg-card",
        children: /*#__PURE__*/_jsxs(CardContent, {
          className: "p-4",
          children: [/*#__PURE__*/_jsx("p", {
            className: "text-xs font-mono uppercase tracking-wider text-muted-foreground",
            children: "Avg Risk Score"
          }), /*#__PURE__*/_jsx("p", {
            className: `text-3xl font-bold mt-1 ${riskColor(avgRisk)}`,
            children: avgRisk
          })]
        })
      }), /*#__PURE__*/_jsx(Card, {
        className: "border-border bg-card",
        children: /*#__PURE__*/_jsxs(CardContent, {
          className: "p-4",
          children: [/*#__PURE__*/_jsx("p", {
            className: "text-xs font-mono uppercase tracking-wider text-muted-foreground",
            children: "Mitigated"
          }), /*#__PURE__*/_jsx("p", {
            className: "text-3xl font-bold text-success mt-1",
            children: threats.filter(t => t.status === "mitigated").length
          })]
        })
      })]
    }), /*#__PURE__*/_jsx("div", {
      className: "space-y-4",
      children: threats.map(threat => /*#__PURE__*/_jsx(Card, {
        className: "border-border bg-card overflow-hidden",
        children: /*#__PURE__*/_jsx(CardContent, {
          className: "p-0",
          children: /*#__PURE__*/_jsxs("div", {
            className: "flex flex-col lg:flex-row",
            children: [/*#__PURE__*/_jsxs("div", {
              className: "flex flex-col items-center justify-center p-6 lg:w-32 bg-secondary/30 border-b lg:border-b-0 lg:border-r border-border",
              children: [/*#__PURE__*/_jsx("p", {
                className: `text-3xl font-bold font-mono ${riskColor(threat.riskScore)}`,
                children: threat.riskScore
              }), /*#__PURE__*/_jsx("p", {
                className: "text-[10px] font-mono text-muted-foreground uppercase mt-1",
                children: "Risk"
              })]
            }), /*#__PURE__*/_jsxs("div", {
              className: "flex-1 p-5 space-y-3",
              children: [/*#__PURE__*/_jsxs("div", {
                className: "flex items-start justify-between flex-wrap gap-2",
                children: [/*#__PURE__*/_jsxs("div", {
                  className: "flex items-center gap-2",
                  children: [/*#__PURE__*/_jsx(threat.icon, {
                    className: `h-4 w-4 ${riskColor(threat.riskScore)}`
                  }), /*#__PURE__*/_jsx("h3", {
                    className: "font-semibold text-sm",
                    children: threat.name
                  })]
                }), /*#__PURE__*/_jsxs("div", {
                  className: "flex items-center gap-2",
                  children: [/*#__PURE__*/_jsx(Badge, {
                    variant: "outline",
                    className: "font-mono text-xs",
                    children: threat.stride
                  }), /*#__PURE__*/_jsx(Badge, {
                    className: statusStyles[threat.status],
                    children: threat.status
                  })]
                })]
              }), /*#__PURE__*/_jsx("p", {
                className: "text-xs text-muted-foreground leading-relaxed",
                children: threat.description
              }), /*#__PURE__*/_jsxs("div", {
                className: "grid grid-cols-2 gap-4",
                children: [/*#__PURE__*/_jsxs("div", {
                  className: "space-y-1",
                  children: [/*#__PURE__*/_jsxs("div", {
                    className: "flex justify-between text-xs font-mono text-muted-foreground",
                    children: [/*#__PURE__*/_jsx("span", {
                      children: "Likelihood"
                    }), /*#__PURE__*/_jsxs("span", {
                      children: [threat.likelihood, "%"]
                    })]
                  }), /*#__PURE__*/_jsx(Progress, {
                    value: threat.likelihood,
                    className: "h-1.5"
                  })]
                }), /*#__PURE__*/_jsxs("div", {
                  className: "space-y-1",
                  children: [/*#__PURE__*/_jsxs("div", {
                    className: "flex justify-between text-xs font-mono text-muted-foreground",
                    children: [/*#__PURE__*/_jsx("span", {
                      children: "Impact"
                    }), /*#__PURE__*/_jsxs("span", {
                      children: [threat.impact, "%"]
                    })]
                  }), /*#__PURE__*/_jsx(Progress, {
                    value: threat.impact,
                    className: "h-1.5"
                  })]
                })]
              }), /*#__PURE__*/_jsxs("div", {
                className: "space-y-1",
                children: [/*#__PURE__*/_jsx("p", {
                  className: "text-xs font-mono text-muted-foreground uppercase tracking-wider",
                  children: "Mitigations"
                }), threat.mitigations.map((m, i) => /*#__PURE__*/_jsxs("div", {
                  className: "flex items-center gap-2 text-xs text-primary font-mono",
                  children: [/*#__PURE__*/_jsx(Shield, {
                    className: "h-3 w-3 shrink-0"
                  }), m]
                }, i))]
              })]
            })]
          })
        })
      }, threat.id))
    })]
  });
};
export default ThreatModel;