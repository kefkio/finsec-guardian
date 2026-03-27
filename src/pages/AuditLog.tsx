import { ScrollText, Filter, Search } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useState } from "react";

interface AuditEntry {
  id: string;
  timestamp: string;
  action: string;
  actor: string;
  resource: string;
  severity: "info" | "warning" | "critical";
  details: string;
  ip: string;
}

const auditEntries: AuditEntry[] = [
  {
    id: "EVT-001",
    timestamp: "2026-03-27 14:32:01",
    action: "SCAN_INITIATED",
    actor: "admin@defiguard.io",
    resource: "UniswapV3Pool.sol",
    severity: "info",
    details: "Full security scan initiated on uploaded contract",
    ip: "192.168.1.42",
  },
  {
    id: "EVT-002",
    timestamp: "2026-03-27 14:32:45",
    action: "CRITICAL_VULN_DETECTED",
    actor: "system",
    resource: "UniswapV3Pool.sol",
    severity: "critical",
    details: "Reentrancy vulnerability detected at line 47. SWC-107 triggered.",
    ip: "system",
  },
  {
    id: "EVT-003",
    timestamp: "2026-03-27 13:15:22",
    action: "USER_LOGIN",
    actor: "analyst@defiguard.io",
    resource: "auth/session",
    severity: "info",
    details: "Successful login via MFA (TOTP). Session ID: sess_a8f2e...",
    ip: "10.0.0.15",
  },
  {
    id: "EVT-004",
    timestamp: "2026-03-27 12:45:10",
    action: "FAILED_LOGIN_ATTEMPT",
    actor: "unknown",
    resource: "auth/login",
    severity: "warning",
    details: "3 failed login attempts from IP. Rate limit applied.",
    ip: "203.0.113.45",
  },
  {
    id: "EVT-005",
    timestamp: "2026-03-27 11:30:00",
    action: "THREAT_MODEL_UPDATED",
    actor: "admin@defiguard.io",
    resource: "threats/T-001",
    severity: "info",
    details: "Reentrancy threat risk score updated from 88 to 92 based on new exploit data.",
    ip: "192.168.1.42",
  },
  {
    id: "EVT-006",
    timestamp: "2026-03-27 10:20:33",
    action: "API_RATE_LIMIT_HIT",
    actor: "api-key:prod_3fa2b",
    resource: "api/v1/scan",
    severity: "warning",
    details: "Rate limit exceeded: 100 requests/min. Throttled for 60 seconds.",
    ip: "172.16.0.88",
  },
  {
    id: "EVT-007",
    timestamp: "2026-03-27 09:05:12",
    action: "PRIVILEGE_ESCALATION_ATTEMPT",
    actor: "user@defiguard.io",
    resource: "admin/settings",
    severity: "critical",
    details: "Unauthorized access attempt to admin panel. Request blocked by RBAC middleware.",
    ip: "10.0.0.22",
  },
  {
    id: "EVT-008",
    timestamp: "2026-03-27 08:00:00",
    action: "SYSTEM_BACKUP",
    actor: "system",
    resource: "database/backup",
    severity: "info",
    details: "Daily automated backup completed. Size: 2.4GB. Integrity hash verified.",
    ip: "system",
  },
];

const severityStyles: Record<string, string> = {
  info: "bg-info/10 text-info border-info/20",
  warning: "bg-warning/10 text-warning border-warning/20",
  critical: "bg-destructive/10 text-destructive border-destructive/20",
};

const AuditLog = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const filtered = auditEntries.filter(
    (e) =>
      e.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.actor.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.details.toLowerCase().includes(searchTerm.toLowerCase())
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

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search events..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 font-mono text-sm bg-secondary/30 border-border"
        />
      </div>

      {/* Timeline */}
      <div className="relative">
        <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />
        <div className="space-y-4">
          {filtered.map((entry) => (
            <div key={entry.id} className="relative pl-14">
              {/* Dot */}
              <div
                className={`absolute left-[18px] top-4 h-3 w-3 rounded-full border-2 border-background ${
                  entry.severity === "critical"
                    ? "bg-destructive"
                    : entry.severity === "warning"
                    ? "bg-warning"
                    : "bg-info"
                }`}
              />

              <Card className="border-border bg-card">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between flex-wrap gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={`font-mono text-[10px] ${severityStyles[entry.severity]}`}>
                          {entry.severity.toUpperCase()}
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
                    <span>
                      <span className="text-foreground/60">actor:</span> {entry.actor}
                    </span>
                    <span>
                      <span className="text-foreground/60">resource:</span> {entry.resource}
                    </span>
                    <span>
                      <span className="text-foreground/60">ip:</span> {entry.ip}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AuditLog;
