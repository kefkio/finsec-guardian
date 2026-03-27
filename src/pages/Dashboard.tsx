import { Shield, AlertTriangle, FileSearch, Activity, TrendingUp, Bug } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const stats = [
  { label: "Contracts Scanned", value: "142", change: "+12%", icon: FileSearch, color: "text-primary" },
  { label: "Critical Vulns", value: "23", change: "-8%", icon: Bug, color: "text-destructive" },
  { label: "Active Threats", value: "7", change: "+2", icon: AlertTriangle, color: "text-warning" },
  { label: "Risk Score", value: "72/100", change: "-5", icon: Shield, color: "text-info" },
];

const scanHistory = [
  { date: "Mar 1", scans: 12, vulns: 4 },
  { date: "Mar 5", scans: 18, vulns: 7 },
  { date: "Mar 10", scans: 15, vulns: 3 },
  { date: "Mar 15", scans: 22, vulns: 9 },
  { date: "Mar 20", scans: 28, vulns: 6 },
  { date: "Mar 25", scans: 35, vulns: 11 },
  { date: "Mar 27", scans: 30, vulns: 5 },
];

const vulnDistribution = [
  { name: "Reentrancy", value: 35, color: "hsl(0, 72%, 51%)" },
  { name: "Integer Overflow", value: 25, color: "hsl(38, 92%, 50%)" },
  { name: "Access Control", value: 20, color: "hsl(280, 80%, 55%)" },
  { name: "Front-Running", value: 12, color: "hsl(199, 89%, 48%)" },
  { name: "Other", value: 8, color: "hsl(220, 10%, 50%)" },
];

const recentScans = [
  { name: "UniswapV3Pool.sol", severity: "critical", vulns: 3, time: "2m ago" },
  { name: "AaveFlashLoan.sol", severity: "high", vulns: 2, time: "15m ago" },
  { name: "CompoundGovernor.sol", severity: "medium", vulns: 1, time: "1h ago" },
  { name: "CurveStableSwap.sol", severity: "low", vulns: 0, time: "3h ago" },
  { name: "MakerDAOVault.sol", severity: "critical", vulns: 4, time: "5h ago" },
];

const severityColor: Record<string, string> = {
  critical: "bg-destructive text-destructive-foreground",
  high: "bg-warning text-warning-foreground",
  medium: "bg-info text-info-foreground",
  low: "bg-success text-success-foreground",
};

const Dashboard = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Security <span className="text-gradient-primary">Dashboard</span>
        </h1>
        <p className="text-sm text-muted-foreground font-mono mt-1">
          Real-time DeFi smart contract security overview
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="border-border bg-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground font-mono uppercase tracking-wider">
                    {stat.label}
                  </p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </div>
                <div className={`rounded-md bg-secondary p-2.5 ${stat.color}`}>
                  <stat.icon className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-2 text-xs font-mono text-muted-foreground">
                <span className={stat.change.startsWith("+") ? "text-success" : "text-primary"}>
                  {stat.change}
                </span>{" "}
                from last week
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Scan Activity Chart */}
        <Card className="lg:col-span-2 border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground">
              Scan Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={scanHistory}>
                <defs>
                  <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(160, 100%, 40%)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(160, 100%, 40%)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="vulnGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(0, 72%, 51%)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(0, 72%, 51%)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 15%, 18%)" />
                <XAxis dataKey="date" stroke="hsl(220, 10%, 50%)" fontSize={11} fontFamily="JetBrains Mono" />
                <YAxis stroke="hsl(220, 10%, 50%)" fontSize={11} fontFamily="JetBrains Mono" />
                <Tooltip
                  contentStyle={{
                    background: "hsl(220, 18%, 10%)",
                    border: "1px solid hsl(220, 15%, 18%)",
                    borderRadius: "0.5rem",
                    fontFamily: "JetBrains Mono",
                    fontSize: "12px",
                  }}
                />
                <Area type="monotone" dataKey="scans" stroke="hsl(160, 100%, 40%)" fill="url(#scanGrad)" strokeWidth={2} />
                <Area type="monotone" dataKey="vulns" stroke="hsl(0, 72%, 51%)" fill="url(#vulnGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Vulnerability Distribution */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground">
              Vuln Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie data={vulnDistribution} dataKey="value" cx="50%" cy="50%" innerRadius={40} outerRadius={65} strokeWidth={2} stroke="hsl(220, 20%, 7%)">
                  {vulnDistribution.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-1.5 mt-2">
              {vulnDistribution.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full" style={{ background: item.color }} />
                    <span className="text-muted-foreground">{item.name}</span>
                  </div>
                  <span>{item.value}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Scans */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground">
            Recent Scans
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentScans.map((scan) => (
              <div
                key={scan.name}
                className="flex items-center justify-between rounded-md border border-border bg-secondary/30 px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <FileSearch className="h-4 w-4 text-muted-foreground" />
                  <span className="font-mono text-sm">{scan.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Badge className={severityColor[scan.severity]} variant="secondary">
                    {scan.severity}
                  </Badge>
                  <span className="text-xs text-muted-foreground font-mono">
                    {scan.vulns} vulns
                  </span>
                  <span className="text-xs text-muted-foreground font-mono">{scan.time}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
