import { Shield, AlertTriangle, FileSearch, Bug } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
const stats = [{
  label: "Contracts Scanned",
  value: "142",
  change: "+12%",
  icon: FileSearch,
  color: "text-primary"
}, {
  label: "Critical Vulns",
  value: "23",
  change: "-8%",
  icon: Bug,
  color: "text-destructive"
}, {
  label: "Active Threats",
  value: "7",
  change: "+2",
  icon: AlertTriangle,
  color: "text-warning"
}, {
  label: "Risk Score",
  value: "72/100",
  change: "-5",
  icon: Shield,
  color: "text-info"
}];
const scanHistory = [{
  date: "Mar 1",
  scans: 12,
  vulns: 4
}, {
  date: "Mar 5",
  scans: 18,
  vulns: 7
}, {
  date: "Mar 10",
  scans: 15,
  vulns: 3
}, {
  date: "Mar 15",
  scans: 22,
  vulns: 9
}, {
  date: "Mar 20",
  scans: 28,
  vulns: 6
}, {
  date: "Mar 25",
  scans: 35,
  vulns: 11
}, {
  date: "Mar 27",
  scans: 30,
  vulns: 5
}];
const vulnDistribution = [{
  name: "Reentrancy",
  value: 35,
  color: "hsl(0, 72%, 51%)"
}, {
  name: "Integer Overflow",
  value: 25,
  color: "hsl(38, 92%, 50%)"
}, {
  name: "Access Control",
  value: 20,
  color: "hsl(280, 80%, 55%)"
}, {
  name: "Front-Running",
  value: 12,
  color: "hsl(199, 89%, 48%)"
}, {
  name: "Other",
  value: 8,
  color: "hsl(220, 10%, 50%)"
}];
const recentScans = [{
  name: "UniswapV3Pool.sol",
  severity: "critical",
  vulns: 3,
  time: "2m ago"
}, {
  name: "AaveFlashLoan.sol",
  severity: "high",
  vulns: 2,
  time: "15m ago"
}, {
  name: "CompoundGovernor.sol",
  severity: "medium",
  vulns: 1,
  time: "1h ago"
}, {
  name: "CurveStableSwap.sol",
  severity: "low",
  vulns: 0,
  time: "3h ago"
}, {
  name: "MakerDAOVault.sol",
  severity: "critical",
  vulns: 4,
  time: "5h ago"
}];
const severityColor = {
  critical: "bg-destructive text-destructive-foreground",
  high: "bg-warning text-warning-foreground",
  medium: "bg-info text-info-foreground",
  low: "bg-success text-success-foreground"
};
const Dashboard = () => {
  return /*#__PURE__*/_jsxs("div", {
    className: "space-y-6",
    children: [/*#__PURE__*/_jsxs("div", {
      children: [/*#__PURE__*/_jsxs("h1", {
        className: "text-2xl font-bold tracking-tight",
        children: ["Security ", /*#__PURE__*/_jsx("span", {
          className: "text-gradient-primary",
          children: "Dashboard"
        })]
      }), /*#__PURE__*/_jsx("p", {
        className: "text-sm text-muted-foreground font-mono mt-1",
        children: "Real-time DeFi smart contract security overview"
      })]
    }), /*#__PURE__*/_jsx("div", {
      className: "grid gap-4 md:grid-cols-2 lg:grid-cols-4",
      children: stats.map(stat => /*#__PURE__*/_jsx(Card, {
        className: "border-border bg-card",
        children: /*#__PURE__*/_jsxs(CardContent, {
          className: "p-4",
          children: [/*#__PURE__*/_jsxs("div", {
            className: "flex items-center justify-between",
            children: [/*#__PURE__*/_jsxs("div", {
              className: "space-y-1",
              children: [/*#__PURE__*/_jsx("p", {
                className: "text-xs text-muted-foreground font-mono uppercase tracking-wider",
                children: stat.label
              }), /*#__PURE__*/_jsx("p", {
                className: "text-2xl font-bold",
                children: stat.value
              })]
            }), /*#__PURE__*/_jsx("div", {
              className: `rounded-md bg-secondary p-2.5 ${stat.color}`,
              children: /*#__PURE__*/_jsx(stat.icon, {
                className: "h-5 w-5"
              })
            })]
          }), /*#__PURE__*/_jsxs("p", {
            className: "mt-2 text-xs font-mono text-muted-foreground",
            children: [/*#__PURE__*/_jsx("span", {
              className: stat.change.startsWith("+") ? "text-success" : "text-primary",
              children: stat.change
            }), " ", "from last week"]
          })]
        })
      }, stat.label))
    }), /*#__PURE__*/_jsxs("div", {
      className: "grid gap-4 lg:grid-cols-3",
      children: [/*#__PURE__*/_jsxs(Card, {
        className: "lg:col-span-2 border-border bg-card",
        children: [/*#__PURE__*/_jsx(CardHeader, {
          className: "pb-2",
          children: /*#__PURE__*/_jsx(CardTitle, {
            className: "text-sm font-mono uppercase tracking-wider text-muted-foreground",
            children: "Scan Activity"
          })
        }), /*#__PURE__*/_jsx(CardContent, {
          children: /*#__PURE__*/_jsx(ResponsiveContainer, {
            width: "100%",
            height: 240,
            children: /*#__PURE__*/_jsxs(AreaChart, {
              data: scanHistory,
              children: [/*#__PURE__*/_jsxs("defs", {
                children: [/*#__PURE__*/_jsxs("linearGradient", {
                  id: "scanGrad",
                  x1: "0",
                  y1: "0",
                  x2: "0",
                  y2: "1",
                  children: [/*#__PURE__*/_jsx("stop", {
                    offset: "5%",
                    stopColor: "hsl(160, 100%, 40%)",
                    stopOpacity: 0.3
                  }), /*#__PURE__*/_jsx("stop", {
                    offset: "95%",
                    stopColor: "hsl(160, 100%, 40%)",
                    stopOpacity: 0
                  })]
                }), /*#__PURE__*/_jsxs("linearGradient", {
                  id: "vulnGrad",
                  x1: "0",
                  y1: "0",
                  x2: "0",
                  y2: "1",
                  children: [/*#__PURE__*/_jsx("stop", {
                    offset: "5%",
                    stopColor: "hsl(0, 72%, 51%)",
                    stopOpacity: 0.3
                  }), /*#__PURE__*/_jsx("stop", {
                    offset: "95%",
                    stopColor: "hsl(0, 72%, 51%)",
                    stopOpacity: 0
                  })]
                })]
              }), /*#__PURE__*/_jsx(CartesianGrid, {
                strokeDasharray: "3 3",
                stroke: "hsl(220, 15%, 18%)"
              }), /*#__PURE__*/_jsx(XAxis, {
                dataKey: "date",
                stroke: "hsl(220, 10%, 50%)",
                fontSize: 11,
                fontFamily: "JetBrains Mono"
              }), /*#__PURE__*/_jsx(YAxis, {
                stroke: "hsl(220, 10%, 50%)",
                fontSize: 11,
                fontFamily: "JetBrains Mono"
              }), /*#__PURE__*/_jsx(Tooltip, {
                contentStyle: {
                  background: "hsl(220, 18%, 10%)",
                  border: "1px solid hsl(220, 15%, 18%)",
                  borderRadius: "0.5rem",
                  fontFamily: "JetBrains Mono",
                  fontSize: "12px"
                }
              }), /*#__PURE__*/_jsx(Area, {
                type: "monotone",
                dataKey: "scans",
                stroke: "hsl(160, 100%, 40%)",
                fill: "url(#scanGrad)",
                strokeWidth: 2
              }), /*#__PURE__*/_jsx(Area, {
                type: "monotone",
                dataKey: "vulns",
                stroke: "hsl(0, 72%, 51%)",
                fill: "url(#vulnGrad)",
                strokeWidth: 2
              })]
            })
          })
        })]
      }), /*#__PURE__*/_jsxs(Card, {
        className: "border-border bg-card",
        children: [/*#__PURE__*/_jsx(CardHeader, {
          className: "pb-2",
          children: /*#__PURE__*/_jsx(CardTitle, {
            className: "text-sm font-mono uppercase tracking-wider text-muted-foreground",
            children: "Vuln Distribution"
          })
        }), /*#__PURE__*/_jsxs(CardContent, {
          children: [/*#__PURE__*/_jsx(ResponsiveContainer, {
            width: "100%",
            height: 160,
            children: /*#__PURE__*/_jsx(PieChart, {
              children: /*#__PURE__*/_jsx(Pie, {
                data: vulnDistribution,
                dataKey: "value",
                cx: "50%",
                cy: "50%",
                innerRadius: 40,
                outerRadius: 65,
                strokeWidth: 2,
                stroke: "hsl(220, 20%, 7%)",
                children: vulnDistribution.map((entry, i) => /*#__PURE__*/_jsx(Cell, {
                  fill: entry.color
                }, i))
              })
            })
          }), /*#__PURE__*/_jsx("div", {
            className: "space-y-1.5 mt-2",
            children: vulnDistribution.map(item => /*#__PURE__*/_jsxs("div", {
              className: "flex items-center justify-between text-xs font-mono",
              children: [/*#__PURE__*/_jsxs("div", {
                className: "flex items-center gap-2",
                children: [/*#__PURE__*/_jsx("div", {
                  className: "h-2 w-2 rounded-full",
                  style: {
                    background: item.color
                  }
                }), /*#__PURE__*/_jsx("span", {
                  className: "text-muted-foreground",
                  children: item.name
                })]
              }), /*#__PURE__*/_jsxs("span", {
                children: [item.value, "%"]
              })]
            }, item.name))
          })]
        })]
      })]
    }), /*#__PURE__*/_jsxs(Card, {
      className: "border-border bg-card",
      children: [/*#__PURE__*/_jsx(CardHeader, {
        className: "pb-2",
        children: /*#__PURE__*/_jsx(CardTitle, {
          className: "text-sm font-mono uppercase tracking-wider text-muted-foreground",
          children: "Recent Scans"
        })
      }), /*#__PURE__*/_jsx(CardContent, {
        children: /*#__PURE__*/_jsx("div", {
          className: "space-y-3",
          children: recentScans.map(scan => /*#__PURE__*/_jsxs("div", {
            className: "flex items-center justify-between rounded-md border border-border bg-secondary/30 px-4 py-3",
            children: [/*#__PURE__*/_jsxs("div", {
              className: "flex items-center gap-3",
              children: [/*#__PURE__*/_jsx(FileSearch, {
                className: "h-4 w-4 text-muted-foreground"
              }), /*#__PURE__*/_jsx("span", {
                className: "font-mono text-sm",
                children: scan.name
              })]
            }), /*#__PURE__*/_jsxs("div", {
              className: "flex items-center gap-3",
              children: [/*#__PURE__*/_jsx(Badge, {
                className: severityColor[scan.severity],
                variant: "secondary",
                children: scan.severity
              }), /*#__PURE__*/_jsxs("span", {
                className: "text-xs text-muted-foreground font-mono",
                children: [scan.vulns, " vulns"]
              }), /*#__PURE__*/_jsx("span", {
                className: "text-xs text-muted-foreground font-mono",
                children: scan.time
              })]
            })]
          }, scan.name))
        })
      })]
    })]
  });
};
export default Dashboard;