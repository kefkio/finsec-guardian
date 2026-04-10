import { useQuery } from "@tanstack/react-query";
import { scannerApi, threatsApi } from "@/lib/api";
import { 
  Shield, AlertTriangle, FileSearch, Bug, TrendingDown, TrendingUp, Activity,
  Clock, CheckCircle2, AlertCircle, Zap, Lock
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, LineChart, Line, ComposedChart, Bar, Legend,
  ScatterChart, Scatter
} from "recharts";

const scanHistory = [
  { date: "Mar 1", scans: 12, vulns: 4, critical: 1, resolved: 2 },
  { date: "Mar 5", scans: 18, vulns: 7, critical: 2, resolved: 3 },
  { date: "Mar 10", scans: 15, vulns: 3, critical: 0, resolved: 5 },
  { date: "Mar 15", scans: 22, vulns: 9, critical: 3, resolved: 4 },
  { date: "Mar 20", scans: 28, vulns: 6, critical: 1, resolved: 7 },
  { date: "Mar 25", scans: 35, vulns: 11, critical: 4, resolved: 8 },
  { date: "Mar 27", scans: 30, vulns: 5, critical: 2, resolved: 6 },
];

const vulnDistribution = [
  { name: "Reentrancy", value: 35, color: "#ef4444" },
  { name: "Integer Overflow", value: 25, color: "#f97316" },
  { name: "Access Control", value: 20, color: "#a855f7" },
  { name: "Front-Running", value: 12, color: "#0ea5e9" },
  { name: "Other", value: 8, color: "#6b7280" },
];

const severityMatrix = [
  { x: 15, y: 85, size: 400, severity: "CRITICAL", count: 4, color: "#ef4444" },
  { x: 45, y: 65, size: 250, severity: "HIGH", count: 8, color: "#f97316" },
  { x: 70, y: 40, size: 150, severity: "MEDIUM", count: 12, color: "#eab308" },
  { x: 85, y: 20, size: 80, severity: "LOW", count: 5, color: "#22c55e" },
];

const staticRecentScans = [
  { id: 1, name: "UniswapV3Pool.sol", severity: "critical", vulns: 3, time: "2m ago", status: "in-progress", risk: 95 },
  { id: 2, name: "AaveFlashLoan.sol", severity: "high", vulns: 2, time: "15m ago", status: "completed", risk: 78 },
  { id: 3, name: "CompoundGovernor.sol", severity: "medium", vulns: 1, time: "1h ago", status: "completed", risk: 42 },
  { id: 4, name: "CurveStableSwap.sol", severity: "low", vulns: 0, time: "3h ago", status: "completed", risk: 18 },
  { id: 5, name: "MakerDAOVault.sol", severity: "critical", vulns: 4, time: "5h ago", status: "completed", risk: 88 },
];

const severityColor = {
  critical: "bg-red-500/20 text-red-400 border-red-500/30",
  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  low: "bg-green-500/20 text-green-400 border-green-500/30",
};

const severityBg = {
  critical: "bg-red-500/10",
  high: "bg-orange-500/10",
  medium: "bg-yellow-500/10",
  low: "bg-green-500/10",
};

const statusConfig = {
  "in-progress": { icon: Activity, color: "text-blue-400", label: "Scanning" },
  "completed": { icon: CheckCircle2, color: "text-green-400", label: "Completed" },
};

function relativeTime(isoString) {
  if (!isoString) return "";
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function buildScanHistory(scans) {
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    return {
      date: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      dateStr: d.toISOString().slice(0, 10),
      scans: 0,
      vulns: 0,
    };
  });
  scans.forEach(scan => {
    const scanDate = scan.created_at?.slice(0, 10);
    const day = days.find(d => d.dateStr === scanDate);
    if (day) {
      day.scans++;
      day.vulns += scan.total_findings || 0;
    }
  });
  return days;
}

function StatCard({ label, value, change, icon: Icon, trend, bgGradient }) {
  const isPositive = change?.startsWith("+") || trend === "up";
  const TrendIcon = trend === "up" ? TrendingUp : TrendingDown;
  
  return (
    <Card className="relative overflow-hidden border-border/50 bg-card/50 backdrop-blur-xl hover:bg-card/70 transition-all duration-300 group">
      <div className={`absolute inset-0 ${bgGradient} opacity-0 group-hover:opacity-10 transition-opacity`} />
      <CardContent className="relative p-3 sm:p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-xs font-mono text-muted-foreground uppercase tracking-widest mb-2">
              {label}
            </p>
            <p className="text-2xl sm:text-3xl font-bold text-foreground">
              {value}
            </p>
            {change && (
              <div className="flex items-center gap-1 mt-2">
                <TrendIcon className={`w-3 h-3 ${isPositive ? "text-red-400" : "text-green-400"}`} />
                <span className={`text-xs font-mono ${isPositive ? "text-red-400" : "text-green-400"}`}>
                  {change}
                </span>
                <span className="text-xs text-muted-foreground">from last week</span>
              </div>
            )}
          </div>
          <div className="rounded-lg bg-secondary/60 p-3 group-hover:bg-secondary transition-colors">
            <Icon className="w-5 h-5 text-muted-foreground" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

const Dashboard = () => {
  const { data: scansData, isLoading } = useQuery({
    queryKey: ['dashboard-scans'],
    queryFn: scannerApi.getDashboardScans,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const { data: threatsData } = useQuery({
    queryKey: ['threats'],
    queryFn: threatsApi.getThreats,
    staleTime: 60_000,
  });

  const allScans = Array.isArray(scansData) ? scansData : (scansData?.results || []);
  const totalScans = scansData?.count ?? allScans.length;

  const criticalVulns = allScans.reduce((s, sc) => s + (sc.critical_count || 0), 0);
  const highVulns = allScans.reduce((s, sc) => s + (sc.high_count || 0), 0);
  const mediumVulns = allScans.reduce((s, sc) => s + (sc.medium_count || 0), 0);
  const lowVulns = allScans.reduce((s, sc) => s + (sc.low_count || 0), 0);
  const totalVulns = criticalVulns + highVulns + mediumVulns + lowVulns;

  const activeThreats = Array.isArray(threatsData)
    ? threatsData.length
    : (threatsData?.results?.length ?? 0);

  const riskScore = totalScans === 0 ? 0 : Math.min(99, Math.round(
    (criticalVulns * 25 + highVulns * 10 + mediumVulns * 4 + lowVulns) / Math.max(totalScans, 1)
  ));

  const WEEK_MS = 7 * 24 * 3600 * 1000;
  const now = Date.now();
  const thisWeekScans = allScans.filter(s => now - new Date(s.created_at).getTime() <= WEEK_MS);
  const lastWeekScans = allScans.filter(s => {
    const age = now - new Date(s.created_at).getTime();
    return age > WEEK_MS && age <= 2 * WEEK_MS;
  });
  const thisWeekCritical = thisWeekScans.reduce((s, sc) => s + (sc.critical_count || 0), 0);
  const lastWeekCritical = lastWeekScans.reduce((s, sc) => s + (sc.critical_count || 0), 0);
  const scanChange = lastWeekScans.length > 0
    ? `${thisWeekScans.length >= lastWeekScans.length ? '+' : ''}${thisWeekScans.length - lastWeekScans.length}`
    : null;
  const criticalChange = lastWeekCritical > 0
    ? `${thisWeekCritical >= lastWeekCritical ? '+' : ''}${thisWeekCritical - lastWeekCritical}`
    : null;

  const recentScans = allScans.length > 0
    ? allScans.slice(0, 5).map(scan => ({
        name: scan.contract_name || 'Unnamed Contract',
        vulns: scan.total_findings || 0,
        severity: scan.critical_count > 0 ? 'critical'
          : scan.high_count > 0 ? 'high'
          : scan.medium_count > 0 ? 'medium'
          : 'low',
        time: relativeTime(scan.created_at),
        status: scan.status === 'complete' ? 'completed' : scan.status,
        risk: Math.min(99,
          (scan.critical_count || 0) * 25 +
          (scan.high_count || 0) * 10 +
          (scan.medium_count || 0) * 4 +
          (scan.low_count || 0)
        ),
      }))
    : staticRecentScans;

  const chartData = (() => {
    const built = buildScanHistory(allScans);
    return built.some(d => d.scans > 0) ? built : scanHistory;
  })();

  const vulnDistributionData = totalVulns > 0
    ? [
        { name: "Critical", value: Math.round(criticalVulns / totalVulns * 100), color: "#ef4444" },
        { name: "High",     value: Math.round(highVulns   / totalVulns * 100), color: "#f97316" },
        { name: "Medium",   value: Math.round(mediumVulns / totalVulns * 100), color: "#eab308" },
        { name: "Low",      value: Math.round(lowVulns    / totalVulns * 100), color: "#22c55e" },
      ].filter(v => v.value > 0)
    : vulnDistribution;

  const severityMatrixData = totalVulns > 0
    ? [
        criticalVulns > 0 && { x: 15, y: 85, size: criticalVulns * 80, severity: "CRITICAL", count: criticalVulns, color: "#ef4444" },
        highVulns   > 0 && { x: 40, y: 65, size: highVulns   * 60, severity: "HIGH",     count: highVulns,     color: "#f97316" },
        mediumVulns > 0 && { x: 65, y: 40, size: mediumVulns * 40, severity: "MEDIUM",   count: mediumVulns,   color: "#eab308" },
        lowVulns    > 0 && { x: 85, y: 20, size: lowVulns    * 20, severity: "LOW",      count: lowVulns,      color: "#22c55e" },
      ].filter(Boolean)
    : severityMatrix;

  const lastScanTime = allScans[0]?.created_at ? relativeTime(allScans[0].created_at) : '—';
  const resolvedCount = allScans.filter(s => s.status === 'complete').length;

  return (
    <div className="min-h-screen bg-background p-6 md:p-8">
      {/* Animated background grid */}
      <div className="fixed inset-0 pointer-events-none opacity-10">
        <div className="absolute inset-0 bg-grid-pattern" />
      </div>

      <div className="relative z-10 space-y-8">
        {/* Header */}
        <div className="space-y-2 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-400 to-cyan-400 animate-pulse" />
            <span className="text-xs font-mono text-muted-foreground">SECURITY OPERATIONS CENTER</span>
          </div>
          <h1 className="text-2xl sm:text-4xl md:text-5xl font-bold text-foreground">
            Smart Contract Security Dashboard
          </h1>
          <p className="text-sm text-muted-foreground font-mono mt-2">
            Real-time threat detection and vulnerability analysis
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-3 md:gap-4 lg:grid-cols-4">
          <StatCard
            label="Total Scans"
            value={isLoading ? "…" : totalScans.toString()}
            change={scanChange}
            icon={FileSearch}
            trend={scanChange?.startsWith('+') ? "up" : "down"}
            bgGradient="bg-gradient-to-br from-blue-500 to-blue-600"
          />
          <StatCard
            label="Critical Vulns"
            value={isLoading ? "…" : criticalVulns.toString()}
            change={criticalChange}
            icon={AlertTriangle}
            trend={criticalChange?.startsWith('+') ? "up" : "down"}
            bgGradient="bg-gradient-to-br from-red-500 to-red-600"
          />
          <StatCard
            label="Active Threats"
            value={isLoading ? "…" : activeThreats.toString()}
            icon={AlertCircle}
            bgGradient="bg-gradient-to-br from-orange-500 to-orange-600"
          />
          <StatCard
            label="Risk Score"
            value={isLoading ? "…" : riskScore.toString()}
            icon={Shield}
            bgGradient="bg-gradient-to-br from-yellow-500 to-yellow-600"
          />
        </div>

        {/* Main Analytics Grid */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Scan Activity Chart */}
          <Card className="lg:col-span-2 border-border/50 bg-card/50 backdrop-blur-xl overflow-hidden">
            <CardHeader className="border-b border-border/50 pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-mono uppercase tracking-widest text-card-foreground/80 mb-1">
                    Scan Activity & Vulnerability Trend
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">7-day historical analysis</p>
                </div>
                <div className="flex gap-2">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-cyan-400" />
                    <span className="text-xs text-muted-foreground">Scans</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-red-400" />
                    <span className="text-xs text-muted-foreground">Vulns Found</span>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={chartData}>
                  <defs>
                    <linearGradient id="scanGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(186, 100%, 50%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(186, 100%, 50%)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="vulnGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(0, 84%, 60%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(0, 84%, 60%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="4 4" stroke="rgba(100, 116, 139, 0.2)" vertical={false} />
                  <XAxis 
                    dataKey="date" 
                    stroke="rgba(148, 163, 184, 0.5)" 
                    fontSize={12} 
                    fontFamily="JetBrains Mono"
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis 
                    stroke="rgba(148, 163, 184, 0.5)" 
                    fontSize={12} 
                    fontFamily="JetBrains Mono"
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "0.75rem",
                    fontFamily: "JetBrains Mono",
                    fontSize: "12px",
                    color: "hsl(var(--card-foreground))",
                    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
                  }}
                  cursor={{ fill: "hsl(var(--muted) / 0.3)" }}
                  />
                  <Bar dataKey="scans" fill="hsl(186, 100%, 50%)" fillOpacity={0.3} radius={[4, 4, 0, 0]} />
                  <Line 
                    type="monotone" 
                    dataKey="vulns" 
                    stroke="hsl(0, 84%, 60%)" 
                    strokeWidth={3}
                    dot={{ fill: "hsl(0, 84%, 60%)", r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Vulnerability Distribution */}
          <Card className="border-border/50 bg-card/50 backdrop-blur-xl">
            <CardHeader className="border-b border-border/50 pb-4">
              <CardTitle className="text-sm font-mono uppercase tracking-widest text-card-foreground/80">
                Threat Classification
              </CardTitle>
              <p className="text-xs text-muted-foreground mt-1">Vulnerability types identified</p>
            </CardHeader>
            <CardContent className="p-6">
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={vulnDistributionData}
                    dataKey="value"
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={65}
                    strokeWidth={2}
                    stroke="rgba(15, 23, 42, 0.8)"
                  >
                    {vulnDistributionData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-4">
                {vulnDistributionData.map(item => (
                  <div key={item.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: item.color }} />
                      <span className="text-muted-foreground font-mono">{item.name}</span>
                    </div>
                    <span className="text-card-foreground font-semibold">{item.value}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Risk Matrix */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-xl">
          <CardHeader className="border-b border-border/50 pb-4">
            <CardTitle className="text-sm font-mono uppercase tracking-widest text-card-foreground/80">
              Risk Assessment Matrix
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-1">Severity vs. Frequency analysis</p>
          </CardHeader>
          <CardContent className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="4 4" stroke="rgba(100, 116, 139, 0.2)" />
                <XAxis 
                  type="number" 
                  dataKey="x" 
                  name="Frequency" 
                  stroke="rgba(148, 163, 184, 0.5)"
                  label={{ value: "Frequency", position: "insideBottomRight", offset: -10, fill: "rgba(148, 163, 184, 0.7)" }}
                />
                <YAxis 
                  type="number" 
                  dataKey="y" 
                  name="Severity" 
                  stroke="rgba(148, 163, 184, 0.5)"
                  label={{ value: "Severity", angle: -90, position: "insideLeft", fill: "rgba(148, 163, 184, 0.7)" }}
                />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "0.75rem",
                    fontFamily: "JetBrains Mono",
                    fontSize: "12px",
                    color: "hsl(var(--card-foreground))",
                  }}
                  cursor={{ fill: "hsl(var(--muted) / 0.3)" }}
                  formatter={(value) => `${value.severity}: ${value.count} issues`}
                />
                {severityMatrixData.map(item => (
                  <Scatter key={item.severity} name={item.severity} data={[item]} fill={item.color} />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Recent Scans Table */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-xl">
          <CardHeader className="border-b border-border/50 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-mono uppercase tracking-widest text-card-foreground/80">
                  Recent Security Scans
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-1">Latest contract analysis results</p>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Clock className="w-4 h-4" />
                Live Updates
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-3">
              {recentScans.map((scan, i) => {
                const StatusIcon = statusConfig[scan.status]?.icon || Activity;
                const statusColor = statusConfig[scan.status]?.color || "text-muted-foreground";
                
                return (
                  <div
                    key={i}
                    className={`group relative rounded-lg border transition-all duration-300 hover:border-border hover:bg-muted/50 ${severityBg[scan.severity]} ${severityColor[scan.severity].split(" ").pop()}`}
                  >
                    {/* Status indicator line */}
                    <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-lg ${
                      scan.severity === "critical" ? "bg-red-500" :
                      scan.severity === "high" ? "bg-orange-500" :
                      scan.severity === "medium" ? "bg-yellow-500" :
                      "bg-green-500"
                    }`} />

                    <div className="pl-4 pr-4 py-4 flex items-center justify-between group-hover:translate-x-1 transition-transform">
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <div className="flex-shrink-0">
                          <FileSearch className="w-5 h-5 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-mono text-sm font-semibold text-foreground truncate">
                            {scan.name}
                          </p>
                          <div className="flex items-center gap-2 mt-1 flex-wrap">
                            <Badge 
                              className={`${severityColor[scan.severity]} border text-xs font-mono`}
                              variant="outline"
                            >
                              {scan.severity.toUpperCase()}
                            </Badge>
                            <span className="text-xs text-muted-foreground font-mono">
                              {scan.vulns} vulnerabilities
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 flex-shrink-0 ml-4">
                        {/* Risk Score */}
                        <div className="text-right">
                          <div className="text-lg font-bold text-foreground">
                            {scan.risk || (scan.vulns * 20)}
                          </div>
                          <div className="text-xs text-muted-foreground font-mono">RISK</div>
                        </div>

                        {/* Status */}
                        <div className="flex flex-col items-center gap-1">
                          <StatusIcon className={`w-4 h-4 ${statusColor}`} />
                          <span className="text-xs text-muted-foreground font-mono">
                            {scan.time}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <button className="w-full mt-4 px-4 py-3 rounded-lg border border-border/50 bg-muted/50 text-muted-foreground hover:bg-muted transition-colors text-sm font-mono uppercase tracking-wide">
              View All Scans →
            </button>
          </CardContent>
        </Card>

        {/* Footer Stats */}
        <div className="grid gap-4 sm:grid-cols-3 pt-4">
          <div className="border-l-2 border-cyan-400/50 pl-4 py-2">
            <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">Last Update</p>
            <p className="text-lg font-semibold text-foreground">{lastScanTime}</p>
          </div>
          <div className="border-l-2 border-green-400/50 pl-4 py-2">
            <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">Resolved Issues</p>
            <p className="text-lg font-semibold text-foreground">{resolvedCount} of {totalScans}</p>
          </div>
          <div className="border-l-2 border-orange-400/50 pl-4 py-2">
            <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">Total Contracts</p>
            <p className="text-lg font-semibold text-foreground">{totalScans}</p>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes pulse-subtle {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.8; }
        }
        
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-5px); }
        }

        .animate-pulse {
          animation: pulse-subtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        .bg-grid-pattern {
          background-image: 
            linear-gradient(rgba(71, 85, 105, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(71, 85, 105, 0.1) 1px, transparent 1px);
          background-size: 40px 40px;
        }
      `}</style>
    </div>
  );
};

export default Dashboard;