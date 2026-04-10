import { useQuery } from "@tanstack/react-query";
import { auditApi } from "@/lib/api";
import { Search } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useState } from "react";

const severityStyles = {
  info: "bg-info/10 text-info border-info/20",
  warning: "bg-warning/10 text-warning border-warning/20",
  critical: "bg-destructive/10 text-destructive border-destructive/20"
};

const AuditLog = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ['audit-events'],
    queryFn: auditApi.getEvents,
  });

  const rawEntries = data?.results || data || [];
  const entries = rawEntries.map(e => ({
    ...e,
    action: e.event_type || e.action,
    details: e.message || e.details,
    ip: e.ip_address || e.ip,
  }));

  const filtered = entries.filter(e =>
    (e.action || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (e.actor || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (e.details || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Audit <span className="text-gradient-primary">Log</span>
        </h1>
        <p className="text-sm text-muted-foreground font-mono mt-1">
          Tamper-evident security event log with forensic detail
        </p>
      </div>

      <div className="relative w-full max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search events..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          className="pl-10 font-mono text-sm bg-secondary/30 border-border"
        />
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-16 text-muted-foreground font-mono text-sm">
          Loading audit events...
        </div>
      )}

      {isError && (
        <div className="flex items-center justify-center py-16 text-destructive font-mono text-sm">
          Failed to load audit events. Check API connection.
        </div>
      )}

      {!isLoading && !isError && (
        <div className="relative">
          <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />
          <div className="space-y-4">
            {filtered.map(entry => (
              <div key={entry.id} className="relative pl-14">
                <div
                  className={`absolute left-[18px] top-4 h-3 w-3 rounded-full border-2 border-background ${
                    entry.severity === "critical" ? "bg-destructive" :
                    entry.severity === "warning" ? "bg-warning" : "bg-info"
                  }`}
                />
                <Card className="border-border bg-card">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between flex-wrap gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant="outline"
                            className={`font-mono text-[10px] ${severityStyles[entry.severity] || severityStyles.info}`}
                          >
                            {(entry.severity || 'info').toUpperCase()}
                          </Badge>
                          <span className="font-mono text-sm font-semibold">{entry.action}</span>
                        </div>
                        <p className="text-xs text-muted-foreground leading-relaxed">{entry.details}</p>
                      </div>
                      <span className="text-xs font-mono text-muted-foreground whitespace-nowrap">
                        {entry.timestamp}
                      </span>
                    </div>
                    <div className="flex gap-4 mt-2 text-[11px] font-mono text-muted-foreground">
                      <span><span className="text-foreground/60">actor:</span> {entry.actor}</span>
                      <span><span className="text-foreground/60">resource:</span> {entry.resource}</span>
                      <span><span className="text-foreground/60">ip:</span> {entry.ip}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLog;
