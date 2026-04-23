import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { scannerApi } from "@/lib/api";
import {
  ArrowLeft, Shield, ShieldAlert, ShieldCheck, ShieldX,
  ChevronDown, ChevronRight, FileSearch, Clock, AlertTriangle,
  BarChart3, Loader2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import OnChainIntelligence from "@/components/OnChainIntelligence";

const SEV = {
  critical: { badge: "bg-red-600 text-white", border: "border-l-red-500", bar: "bg-red-500", icon: ShieldX, label: "Critical", order: 0 },
  high: { badge: "bg-orange-500 text-white", border: "border-l-orange-500", bar: "bg-orange-500", icon: ShieldAlert, label: "High", order: 1 },
  medium: { badge: "bg-yellow-500 text-black", border: "border-l-yellow-500", bar: "bg-yellow-500", icon: Shield, label: "Medium", order: 2 },
  low: { badge: "bg-blue-500 text-white", border: "border-l-blue-500", bar: "bg-blue-500", icon: ShieldCheck, label: "Low", order: 3 },
  info: { badge: "bg-muted text-muted-foreground", border: "border-l-muted-foreground", bar: "bg-muted-foreground", icon: Shield, label: "Info", order: 4 },
};

function riskGrade(score) {
  if (score >= 85) return { grade: "F", label: "Critical Risk", color: "text-red-400" };
  if (score >= 70) return { grade: "D", label: "High Risk", color: "text-orange-400" };
  if (score >= 50) return { grade: "C", label: "Medium Risk", color: "text-yellow-400" };
  if (score >= 25) return { grade: "B", label: "Low Risk", color: "text-lime-400" };
  return { grade: "A", label: "Minimal Risk", color: "text-green-400" };
}

function FindingCard({ finding }) {
  const [open, setOpen] = useState(false);
  const cfg = SEV[finding.severity] || SEV.info;

  return (
    <div
      className={`rounded border border-border bg-secondary/20 border-l-4 ${cfg.border} cursor-pointer select-none`}
      onClick={() => setOpen(o => !o)}
    >
      <div className="flex items-center justify-between p-3">
        <div className="flex items-center gap-2 min-w-0">
          <Badge className={`${cfg.badge} font-mono text-xs shrink-0`}>{cfg.label}</Badge>
          {finding.swc_id && (
            <span className="text-xs font-mono text-muted-foreground shrink-0">{finding.swc_id}</span>
          )}
          <span className="text-sm font-medium truncate">{finding.title}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          {finding.line_number != null && (
            <span className="text-xs font-mono text-muted-foreground">L{finding.line_number}</span>
          )}
          {open ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
        </div>
      </div>
      {open && (
        <div className="px-3 pb-3 space-y-2 border-t border-border/50 pt-2">
          {finding.description && (
            <p className="text-xs text-muted-foreground leading-relaxed">{finding.description}</p>
          )}
          {finding.recommendation && (
            <div className="rounded bg-primary/5 border border-primary/20 p-2">
              <p className="text-xs font-mono text-primary">
                <span className="font-bold">Fix: </span>{finding.recommendation}
              </p>
            </div>
          )}
          {finding.code_snippet && (
            <pre className="text-xs font-mono bg-secondary/30 rounded p-2 overflow-x-auto">{finding.code_snippet}</pre>
          )}
          <div className="flex gap-3 text-[11px] font-mono text-muted-foreground">
            {finding.confidence != null && <span>confidence: {finding.confidence}%</span>}
            {finding.impact_score != null && <span>impact: {finding.impact_score}/10</span>}
            <span>status: {finding.status || "new"}</span>
          </div>
        </div>
      )}
    </div>
  );
}

function SeverityBar({ label, count, total, cfg }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2">
      <span className="w-16 text-xs font-mono text-muted-foreground shrink-0">{label}</span>
      <div className="flex-1 bg-secondary/40 rounded-full h-1.5">
        <div className={`${cfg.bar} h-1.5 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-6 text-xs font-mono text-right text-foreground shrink-0">{count}</span>
    </div>
  );
}

const ScanDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // Lazy fetch: scan metadata
  const { data: scan, isLoading: scanLoading, isError: scanError } = useQuery({
    queryKey: ["scan", id],
    queryFn: () => scannerApi.getScan(id),
    enabled: !!id,
    staleTime: 30000,
  });

  // Lazy fetch: findings only when scan is loaded
  const { data: findingsData, isLoading: findingsLoading } = useQuery({
    queryKey: ["scan-findings", id],
    queryFn: () => scannerApi.getFindings(id),
    enabled: !!scan,
    staleTime: 60000,
  });

  // Lazy fetch: statistics only when scan is loaded
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ["scan-statistics", id],
    queryFn: () => scannerApi.getStatistics(id),
    enabled: !!scan,
    staleTime: 60000,
  });

  // Lazy fetch: risk assessment only when scan is loaded
  const { data: riskData, isLoading: riskLoading } = useQuery({
    queryKey: ["scan-risk", id],
    queryFn: () => scannerApi.getRisk(id),
    enabled: !!scan,
    staleTime: 60000,
  });

  // Lazy fetch: on-chain intelligence (only when scan has a contract_address)
  const { data: onchainData, isLoading: onchainLoading } = useQuery({
    queryKey: ["scan-onchain", id],
    queryFn: () => scannerApi.getOnChainData(id),
    enabled: !!scan && !!scan.contract_address,
    staleTime: 60000,
  });

  const findings = findingsData?.findings || [];
  const sortedFindings = [...findings].sort(
    (a, b) => (SEV[a.severity]?.order ?? 5) - (SEV[b.severity]?.order ?? 5)
  );
  const totalFindings = scan?.total_findings || findings.length;

  const score = riskData?.risk_score ?? scan?.risk_score ?? 0;
  const grade = riskGrade(score);

  if (scanLoading) {
    return (
      <div className="flex items-center justify-center py-32 text-muted-foreground font-mono text-sm gap-2">
        <Loader2 className="h-5 w-5 animate-spin" /> Loading scan details...
      </div>
    );
  }

  if (scanError || !scan) {
    return (
      <div className="space-y-4 py-16 text-center">
        <p className="text-destructive font-mono text-sm">Failed to load scan #{id}</p>
        <Button variant="outline" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4 mr-2" /> Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div className="space-y-1">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-2 -ml-2">
            <ArrowLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
            <FileSearch className="h-6 w-6 text-muted-foreground" />
            {scan.contract_name || "Unnamed Contract"}
          </h1>
          <div className="flex items-center gap-3 text-xs font-mono text-muted-foreground">
            <span>Scan #{scan.id}</span>
            <span>|</span>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {scan.created_at ? new Date(scan.created_at).toLocaleString() : "—"}
            </span>
            <span>|</span>
            <Badge variant="outline" className="font-mono text-xs">
              {scan.status?.toUpperCase() || "UNKNOWN"}
            </Badge>
            {scan.contract_address && (
              <>
                <span>|</span>
                <a
                  href={`https://etherscan.io/address/${scan.contract_address}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  {scan.contract_address.slice(0, 8)}…{scan.contract_address.slice(-4)}
                </a>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        {/* Risk Grade */}
        <Card className="border-border bg-card/50">
          <CardContent className="p-4 flex flex-col items-center justify-center">
            {riskLoading ? (
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            ) : (
              <>
                <p className={`text-4xl font-bold font-mono ${grade.color}`}>{grade.grade}</p>
                <p className="text-[10px] font-mono text-muted-foreground mt-1">{grade.label}</p>
                <p className="text-lg font-mono font-semibold mt-1">{score}/100</p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Severity counts */}
        {[
          { key: "critical_count", label: "Critical", color: "text-red-400" },
          { key: "high_count", label: "High", color: "text-orange-400" },
          { key: "medium_count", label: "Medium", color: "text-yellow-400" },
          { key: "low_count", label: "Low", color: "text-green-400" },
        ].map(({ key, label, color }) => (
          <Card key={key} className="border-border bg-card/50">
            <CardContent className="p-4">
              <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">{label}</p>
              <p className={`text-3xl font-bold mt-1 ${color}`}>{scan[key] ?? 0}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Statistics (lazy loaded) */}
      {statsLoading && (
        <Card className="border-border bg-card/50">
          <CardContent className="p-6 flex items-center gap-2 text-muted-foreground font-mono text-sm">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading statistics...
          </CardContent>
        </Card>
      )}
      {statsData && (
        <Card className="border-border bg-card/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <BarChart3 className="h-4 w-4" /> Scan Statistics
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {statsData.findings_summary && (
              <div className="space-y-2">
                {Object.entries(SEV).map(([sev, cfg]) => {
                  const count = sev === "critical" ? scan.critical_count
                    : sev === "high" ? scan.high_count
                    : sev === "medium" ? scan.medium_count
                    : sev === "low" ? scan.low_count
                    : scan.info_count || 0;
                  return (
                    <SeverityBar key={sev} label={cfg.label} count={count || 0} total={totalFindings} cfg={cfg} />
                  );
                })}
              </div>
            )}
            {statsData.risk_metrics && (
              <div className="grid grid-cols-2 gap-4 pt-2 border-t border-border/50 text-xs font-mono text-muted-foreground">
                {Object.entries(statsData.risk_metrics).map(([key, val]) => (
                  <div key={key}>
                    <span className="text-foreground/60">{key.replace(/_/g, " ")}: </span>
                    <span className="text-foreground">{typeof val === "number" ? val.toFixed(1) : String(val)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* On-Chain Intelligence Panel (lazy loaded) */}
      {scan.contract_address && (
        onchainLoading ? (
          <Card className="border-border bg-card/50">
            <CardContent className="p-6 flex items-center gap-2 text-muted-foreground font-mono text-sm">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading on-chain intelligence...
            </CardContent>
          </Card>
        ) : (
          <OnChainIntelligence data={onchainData} contractAddress={scan.contract_address} />
        )
      )}

      {/* Severity Distribution Bar */}
      <Card className="border-border bg-card/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" /> Severity Distribution
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {Object.entries(SEV).map(([sev, cfg]) => {
            const count = sev === "critical" ? scan.critical_count
              : sev === "high" ? scan.high_count
              : sev === "medium" ? scan.medium_count
              : sev === "low" ? scan.low_count
              : scan.info_count || 0;
            return <SeverityBar key={sev} label={cfg.label} count={count || 0} total={totalFindings} cfg={cfg} />;
          })}
        </CardContent>
      </Card>

      {/* Findings (lazy loaded) */}
      <Card className="border-border bg-card/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <Shield className="h-4 w-4" /> Findings ({totalFindings})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {findingsLoading && (
            <div className="flex items-center gap-2 py-8 justify-center text-muted-foreground font-mono text-sm">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading findings...
            </div>
          )}
          {!findingsLoading && sortedFindings.length === 0 && (
            <div className="text-center py-8 text-muted-foreground font-mono text-sm">
              No findings to display.
            </div>
          )}
          {sortedFindings.map((f) => (
            <FindingCard key={f.id} finding={f} />
          ))}
        </CardContent>
      </Card>
    </div>
  );
};

export default ScanDetail;
