import { useQuery } from "@tanstack/react-query";
import { scannerApi } from "@/lib/api";
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
  critical: "bg-red-950/40",
  high: "bg-orange-950/40",
  medium: "bg-yellow-950/40",
  low: "bg-green-950/40",
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

function StatCard({ label, value, change, icon: Icon, trend, bgGradient }) {
  const isPositive = change?.startsWith("+") || trend === "up";
  const TrendIcon = trend === "up" ? TrendingUp : TrendingDown;
  
  return (
    <Card className="relative overflow-hidden border-slate-700/50 bg-slate-900/50 backdrop-blur-xl hover:bg-slate-900/70 transition-all duration-300 group">
      <div className={`absolute inset-0 ${bgGradient} opacity-0 group-hover:opacity-10 transition-opacity`} />
      <CardContent className="relative p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-2">
              {label}
            </p>
            <p className="text-3xl font-bold bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent">
              {value}
            </p>
            {change && (
              <div className="flex items-center gap-1 mt-2">
                <TrendIcon className={`w-3 h-3 ${isPositive ? "text-red-400" : "text-green-400"}`} />
                <span className={`text-xs font-mono ${isPositive ? "text-red-400" : "text-green-400"}`}>
                  {change}
                </span>
                <span className="text-xs text-slate-500">from last week</span>
              </div>
            )}
          </div>
          <div className="rounded-lg bg-gradient-to-br from-slate-700/50 to-slate-800/50 p-3 group-hover:from-slate-700 group-hover:to-slate-800 transition-colors">
            <Icon className="w-5 h-5 text-slate-300" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

const Dashboard = () => {
  const { data: scansData } = useQuery({
    queryKey: ['scans'],
    queryFn: scannerApi.getScans,
    staleTime: 5000,
  });

  const rawScans = Array.isArray(scansData) ? scansData : (scansData?.results || []);
  const recentScans = rawScans.length > 0
    ? rawScans.slice(0, 5).map(scan => ({
        name: scan.contract_name || 'Unnamed',
        vulns: scan.finding_count ?? 0,
        severity: scan.finding_count >= 2 ? "critical" : scan.finding_count >= 1 ? "high" : "low",
        time: relativeTime(scan.created_at),
      }))
    : staticRecentScans;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 md:p-8">
      {/* Animated background grid */}
      <div className="fixed inset-0 pointer-events-none opacity-10">
        <div className="absolute inset-0 bg-grid-pattern" />
      </div>

      <div className="relative z-10 space-y-8">
        {/* Header */}
        <div className="space-y-2 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-400 to-cyan-400 animate-pulse" />
            <span className="text-xs font-mono text-slate-400">SECURITY OPERATIONS CENTER</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-slate-100 via-blue-200 to-cyan-200 bg-clip-text text-transparent">
            Smart Contract Security Dashboard
          </h1>
          <p className="text-sm text-slate-400 font-mono mt-2">
            Real-time threat detection and vulnerability analysis
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard 
            label="Total Scans" 
            value="142" 
            change="+12%" 
            icon={FileSearch}
            trend="up"
            bgGradient="bg-gradient-to-br from-blue-500 to-blue-600"
          />
          <StatCard 
            label="Critical Vulns" 
            value="23" 
            change="-8%" 
            icon={AlertTriangle}
            trend="down"
            bgGradient="bg-gradient-to-br from-red-500 to-red-600"
          />
          <StatCard 
            label="Active Threats" 
            value="7" 
            change="+2" 
            icon={AlertCircle}
            trend="up"
            bgGradient="bg-gradient-to-br from-orange-500 to-orange-600"
          />
          <StatCard 
            label="Risk Score" 
            value="72" 
            change="-5%" 
            icon={Shield}
            trend="down"
            bgGradient="bg-gradient-to-br from-yellow-500 to-yellow-600"
          />
        </div>

        {/* Main Analytics Grid */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Scan Activity Chart */}
          <Card className="lg:col-span-2 border-slate-700/50 bg-slate-900/50 backdrop-blur-xl overflow-hidden">
            <CardHeader className="border-b border-slate-700/50 pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-mono uppercase tracking-widest text-slate-300 mb-1">
                    Scan Activity & Vulnerability Trend
                  </CardTitle>
                  <p className="text-xs text-slate-500">7-day historical analysis</p>
                </div>
                <div className="flex gap-2">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-cyan-400" />
                    <span className="text-xs text-slate-400">Scans</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-red-400" />
                    <span className="text-xs text-slate-400">Vulns Found</span>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={scanHistory}>
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
                      background: "rgba(15, 23, 42, 0.95)",
                      border: "1px solid rgba(71, 85, 105, 0.5)",
                      borderRadius: "0.75rem",
                      fontFamily: "JetBrains Mono",
                      fontSize: "12px",
                      boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)",
                    }}
                    cursor={{ fill: "rgba(100, 116, 139, 0.1)" }}
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
          <Card className="border-slate-700/50 bg-slate-900/50 backdrop-blur-xl">
            <CardHeader className="border-b border-slate-700/50 pb-4">
              <CardTitle className="text-sm font-mono uppercase tracking-widest text-slate-300">
                Threat Classification
              </CardTitle>
              <p className="text-xs text-slate-500 mt-1">Vulnerability types identified</p>
            </CardHeader>
            <CardContent className="p-6">
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={vulnDistribution}
                    dataKey="value"
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={65}
                    strokeWidth={2}
                    stroke="rgba(15, 23, 42, 0.8)"
                  >
                    {vulnDistribution.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-4">
                {vulnDistribution.map(item => (
                  <div key={item.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: item.color }} />
                      <span className="text-slate-400 font-mono">{item.name}</span>
                    </div>
                    <span className="text-slate-300 font-semibold">{item.value}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Risk Matrix */}
        <Card className="border-slate-700/50 bg-slate-900/50 backdrop-blur-xl">
          <CardHeader className="border-b border-slate-700/50 pb-4">
            <CardTitle className="text-sm font-mono uppercase tracking-widest text-slate-300">
              Risk Assessment Matrix
            </CardTitle>
            <p className="text-xs text-slate-500 mt-1">Severity vs. Frequency analysis</p>
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
                    background: "rgba(15, 23, 42, 0.95)",
                    border: "1px solid rgba(71, 85, 105, 0.5)",
                    borderRadius: "0.75rem",
                    fontFamily: "JetBrains Mono",
                    fontSize: "12px",
                  }}
                  cursor={{ fill: "rgba(100, 116, 139, 0.1)" }}
                  formatter={(value) => `${value.severity}: ${value.count} issues`}
                />
                <Scatter name="Critical" data={[severityMatrix[0]]} fill={severityMatrix[0].color} shape="circle" />
                <Scatter name="High" data={[severityMatrix[1]]} fill={severityMatrix[1].color} />
                <Scatter name="Medium" data={[severityMatrix[2]]} fill={severityMatrix[2].color} />
                <Scatter name="Low" data={[severityMatrix[3]]} fill={severityMatrix[3].color} />
              </ScatterChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Recent Scans Table */}
        <Card className="border-slate-700/50 bg-slate-900/50 backdrop-blur-xl">
          <CardHeader className="border-b border-slate-700/50 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-mono uppercase tracking-widest text-slate-300">
                  Recent Security Scans
                </CardTitle>
                <p className="text-xs text-slate-500 mt-1">Latest contract analysis results</p>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Clock className="w-4 h-4" />
                Live Updates
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-3">
              {recentScans.map((scan, i) => {
                const StatusIcon = statusConfig[scan.status]?.icon || Activity;
                const statusColor = statusConfig[scan.status]?.color || "text-slate-400";
                
                return (
                  <div
                    key={i}
                    className={`group relative rounded-lg border transition-all duration-300 hover:border-slate-500/50 hover:bg-slate-800/50 ${severityBg[scan.severity]} ${severityColor[scan.severity].split(" ").pop()}`}
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
                          <FileSearch className="w-5 h-5 text-slate-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-mono text-sm font-semibold text-slate-100 truncate">
                            {scan.name}
                          </p>
                          <div className="flex items-center gap-2 mt-1 flex-wrap">
                            <Badge 
                              className={`${severityColor[scan.severity]} border text-xs font-mono`}
                              variant="outline"
                            >
                              {scan.severity.toUpperCase()}
                            </Badge>
                            <span className="text-xs text-slate-500 font-mono">
                              {scan.vulns} vulnerabilities
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 flex-shrink-0 ml-4">
                        {/* Risk Score */}
                        <div className="text-right">
                          <div className="text-lg font-bold text-slate-100">
                            {scan.risk || (scan.vulns * 20)}
                          </div>
                          <div className="text-xs text-slate-500 font-mono">RISK</div>
                        </div>

                        {/* Status */}
                        <div className="flex flex-col items-center gap-1">
                          <StatusIcon className={`w-4 h-4 ${statusColor}`} />
                          <span className="text-xs text-slate-500 font-mono">
                            {scan.time}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <button className="w-full mt-4 px-4 py-3 rounded-lg border border-slate-700/50 bg-slate-800/50 text-slate-300 hover:bg-slate-800 transition-colors text-sm font-mono uppercase tracking-wide">
              View All Scans →
            </button>
          </CardContent>
        </Card>

        {/* Footer Stats */}
        <div className="grid gap-4 md:grid-cols-3 pt-4">
          <div className="border-l-2 border-cyan-400/50 pl-4 py-2">
            <p className="text-xs text-slate-500 font-mono uppercase tracking-widest mb-1">Last Update</p>
            <p className="text-lg font-semibold text-slate-100">2 minutes ago</p>
          </div>
          <div className="border-l-2 border-green-400/50 pl-4 py-2">
            <p className="text-xs text-slate-500 font-mono uppercase tracking-widest mb-1">Resolved Issues</p>
            <p className="text-lg font-semibold text-slate-100">28 of 142</p>
          </div>
          <div className="border-l-2 border-orange-400/50 pl-4 py-2">
            <p className="text-xs text-slate-500 font-mono uppercase tracking-widest mb-1">Active Contracts</p>
            <p className="text-lg font-semibold text-slate-100">45</p>
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