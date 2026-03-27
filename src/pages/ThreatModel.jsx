import { useQuery } from "@tanstack/react-query";
import { threatsApi } from "@/lib/api";
import { Shield } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

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
  const { data: rawThreats = [], isLoading, isError } = useQuery({
    queryKey: ['threats'],
    queryFn: threatsApi.getThreats,
  });

  const threats = (Array.isArray(rawThreats) ? rawThreats : (rawThreats.results || [])).map(t => ({
    ...t,
    name: t.title,
    riskScore: t.risk_score,
  }));

  const avgRisk = threats.length
    ? Math.round(threats.reduce((sum, t) => sum + (t.riskScore || 0), 0) / threats.length)
    : 0;

  const highRiskCount = threats.filter(t => (t.riskScore || 0) >= 80).length;

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

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">Total Threats</p>
            <p className="text-3xl font-bold text-destructive mt-1">{threats.length}</p>
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
            <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">High Risk</p>
            <p className="text-3xl font-bold text-warning mt-1">{highRiskCount}</p>
          </CardContent>
        </Card>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-16 text-muted-foreground font-mono text-sm">
          Loading threats...
        </div>
      )}

      {isError && (
        <div className="flex items-center justify-center py-16 text-destructive font-mono text-sm">
          Failed to load threats. Check API connection.
        </div>
      )}

      {!isLoading && !isError && (
        <div className="space-y-4">
          {threats.map(threat => (
            <Card key={threat.id} className="border-border bg-card overflow-hidden">
              <CardContent className="p-0">
                <div className="flex flex-col lg:flex-row">
                  <div className="flex flex-col items-center justify-center p-6 lg:w-32 bg-secondary/30 border-b lg:border-b-0 lg:border-r border-border">
                    <p className={`text-3xl font-bold font-mono ${riskColor(threat.riskScore)}`}>
                      {threat.riskScore}
                    </p>
                    <p className="text-[10px] font-mono text-muted-foreground uppercase mt-1">Risk</p>
                  </div>
                  <div className="flex-1 p-5 space-y-3">
                    <div className="flex items-start justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-sm">{threat.name}</h3>
                      </div>
                      <div className="flex items-center gap-2">
                        {threat.category && (
                          <span className="font-mono text-xs border border-border rounded px-2 py-0.5">
                            {threat.category}
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{threat.description}</p>
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
                    {threat.mitigation && (
                      <div className="space-y-1">
                        <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Mitigations</p>
                        <div className="flex items-center gap-2 text-xs text-primary font-mono">
                          <Shield className="h-3 w-3 shrink-0" />
                          {threat.mitigation}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default ThreatModel;
