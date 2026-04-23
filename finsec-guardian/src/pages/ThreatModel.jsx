import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { threatsApi } from "@/lib/api";
import { Shield, ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

/* =========================
   Constants
========================= */
const RISK_LEVELS = {
  HIGH: 80,
  MEDIUM: 60,
  LOW: 40,
};

/* =========================
   Helpers (outside component)
========================= */
const getRiskColor = (score = 0) => {
  if (score >= RISK_LEVELS.HIGH) return "text-destructive";
  if (score >= RISK_LEVELS.MEDIUM) return "text-warning";
  if (score >= RISK_LEVELS.LOW) return "text-info";
  return "text-success";
};

const normalizeThreats = (raw) => {
  const data = raw?.results || raw || [];
  return data.map((t) => ({
    ...t,
    name: t.title,
    riskScore: t.risk_score || 0,
  }));
};

/* =========================
   Reusable Components
========================= */
const StatsCard = ({ label, value, className }) => (
  <Card className="border-border bg-card">
    <CardContent className="p-4">
      <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <p className={`text-3xl font-bold mt-1 ${className}`}>
        {value}
      </p>
    </CardContent>
  </Card>
);

const ThreatCard = ({ threat }) => {
  const [expanded, setExpanded] = useState(false);

  // Lazy fetch: only fetch full detail when card is expanded
  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["threat-detail", threat.id],
    queryFn: () => threatsApi.getThreat(threat.id),
    enabled: expanded && !!threat.id,
    staleTime: 60000,
  });

  const fullThreat = detail || threat;

  return (
    <Card
      className="border-border bg-card overflow-hidden cursor-pointer select-none"
      onClick={() => setExpanded(e => !e)}
    >
      <CardContent className="p-0">
        <div className="flex flex-col lg:flex-row">
        
          {/* Risk Score */}
          <div
            className="flex flex-col items-center justify-center p-6 lg:w-32 bg-secondary/30 border-b lg:border-b-0 lg:border-r border-border"
            role="status"
            aria-label={`Risk score ${threat.riskScore}`}
          >
            <p className={`text-3xl font-bold font-mono ${getRiskColor(threat.riskScore)}`}>
              {threat.riskScore}
            </p>
            <p className="text-[10px] font-mono text-muted-foreground uppercase mt-1">
              Risk
            </p>
          </div>

          {/* Details */}
          <div className="flex-1 p-5 space-y-3">
          
            {/* Header */}
            <div className="flex items-start justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                {expanded
                  ? <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
                  : <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />}
                <h3 className="font-semibold text-sm">{threat.name}</h3>
              </div>
              {threat.category && (
                <span className="font-mono text-xs border border-border rounded px-2 py-0.5">
                  {threat.category}
                </span>
              )}
            </div>

            {/* Description */}
            <p className="text-xs text-muted-foreground leading-relaxed">
              {threat.description}
            </p>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-4">
            
              {/* Likelihood */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-mono text-muted-foreground">
                  <span>Likelihood</span>
                  <span>{threat.likelihood}%</span>
                </div>
                <Progress
                  value={threat.likelihood}
                  className="h-1.5"
                  role="progressbar"
                  aria-label="Likelihood"
                />
              </div>

              {/* Impact */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-mono text-muted-foreground">
                  <span>Impact</span>
                  <span>{threat.impact}%</span>
                </div>
                <Progress
                  value={threat.impact}
                  className="h-1.5"
                  role="progressbar"
                  aria-label="Impact"
                />
              </div>
            </div>

            {/* Mitigation (always visible if present) */}
            {threat.mitigation && (
              <div className="space-y-1">
                <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                  Mitigations
                </p>
                <div className="flex items-center gap-2 text-xs text-primary font-mono">
                  <Shield className="h-3 w-3 shrink-0" />
                  {threat.mitigation}
                </div>
              </div>
            )}

            {/* Expanded Detail (lazy-fetched) */}
            {expanded && (
              <div className="border-t border-border/50 pt-3 mt-2 space-y-2" onClick={e => e.stopPropagation()}>
                {detailLoading && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
                    <Loader2 className="h-3 w-3 animate-spin" /> Loading details...
                  </div>
                )}
                {!detailLoading && fullThreat && (
                  <div className="space-y-2 text-xs font-mono">
                    <div className="grid grid-cols-2 gap-3 text-muted-foreground">
                      <div>
                        <span className="text-foreground/60">Created: </span>
                        {fullThreat.created_at ? new Date(fullThreat.created_at).toLocaleString() : "—"}
                      </div>
                      <div>
                        <span className="text-foreground/60">Updated: </span>
                        {fullThreat.updated_at ? new Date(fullThreat.updated_at).toLocaleString() : "—"}
                      </div>
                      <div>
                        <span className="text-foreground/60">Category: </span>
                        {fullThreat.category || "—"}
                      </div>
                      <div>
                        <span className="text-foreground/60">Risk Score: </span>
                        <span className={getRiskColor(fullThreat.risk_score || threat.riskScore)}>
                          {fullThreat.risk_score ?? threat.riskScore}
                        </span>
                      </div>
                    </div>
                    {fullThreat.description && fullThreat.description !== threat.description && (
                      <div>
                        <p className="text-foreground/60 mb-1">Full Description:</p>
                        <p className="text-muted-foreground leading-relaxed">{fullThreat.description}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/* =========================
   Skeleton Loader
========================= */
const SkeletonCard = () => (
  <Card className="border-border bg-card animate-pulse">
    <CardContent className="p-5 h-32" />
  </Card>
);

/* =========================
   Main Component
========================= */
const ThreatModel = () => {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["threats"],
    queryFn: threatsApi.getThreats,
  });

  const threats = useMemo(() => normalizeThreats(data), [data]);

  const avgRisk = useMemo(() => {
    if (!threats.length) return 0;
    return Math.round(
      threats.reduce((sum, t) => sum + t.riskScore, 0) / threats.length
    );
  }, [threats]);

  const highRiskCount = useMemo(() => {
    return threats.filter(t => t.riskScore >= RISK_LEVELS.HIGH).length;
  }, [threats]);

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Threat <span className="text-gradient-primary">Model</span>
        </h1>
        <p className="text-sm text-muted-foreground font-mono mt-1">
          STRIDE-based threat analysis for DeFi protocols
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <StatsCard label="Total Threats" value={threats.length} className="text-destructive" />
        <StatsCard label="Avg Risk Score" value={avgRisk} className={getRiskColor(avgRisk)} />
        <StatsCard label="High Risk" value={highRiskCount} className="text-warning" />
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="text-center py-16 text-destructive font-mono text-sm">
          Failed to load threats. Check API connection.
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && threats.length === 0 && (
        <div className="text-center py-16 text-muted-foreground font-mono text-sm">
          No threats detected. System looks clean.
        </div>
      )}

      {/* Data */}
      {!isLoading && !isError && threats.length > 0 && (
        <div className="space-y-4">
          {threats.map((t) => (
            <ThreatCard key={t.id} threat={t} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ThreatModel;