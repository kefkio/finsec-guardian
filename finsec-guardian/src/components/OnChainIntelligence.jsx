import { useState, useMemo } from "react";
import {
  Activity, Users, AlertTriangle, TrendingUp, Globe, Clock,
  ChevronDown, ChevronRight, ExternalLink, Shield, Zap,
  ArrowUpRight, ArrowDownRight, Hash,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

/* ---------- helpers ---------- */
function fmtEth(val) {
  if (val == null) return "0";
  return Number(val).toLocaleString(undefined, { maximumFractionDigits: 4 });
}

function fmtNum(val) {
  if (val == null) return "0";
  return Number(val).toLocaleString();
}

function fmtDate(ts) {
  if (!ts) return "—";
  try { return new Date(ts * 1000).toLocaleDateString(); } catch { return "—"; }
}

function pct(a, b) {
  if (!b) return 0;
  return Math.round((a / b) * 100);
}

// Common method selectors → human labels
const METHOD_LABELS = {
  "0xa9059cbb": "transfer()",
  "0x095ea7b3": "approve()",
  "0x23b872dd": "transferFrom()",
  "0x3ccfd60b": "withdraw()",
  "0x2e1a7d4d": "withdraw(uint256)",
  "0xd0e30db0": "deposit()",
  "0x70a08231": "balanceOf()",
  "0x18160ddd": "totalSupply()",
  "0x": "(fallback)",
};

function methodLabel(methodId) {
  return METHOD_LABELS[methodId] || methodId || "unknown";
}

/* ---------- sub-components ---------- */

function StatCard({ icon: Icon, label, value, sub, color = "text-foreground" }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-secondary/30 border border-border/50">
      <div className="h-9 w-9 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
        <Icon className="h-4 w-4 text-primary" />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">{label}</p>
        <p className={`text-lg font-bold font-mono ${color}`}>{value}</p>
        {sub && <p className="text-[10px] font-mono text-muted-foreground">{sub}</p>}
      </div>
    </div>
  );
}

function TxActivityChart({ data }) {
  /* Simple ASCII-style bar chart based on top_methods */
  const methods = data.top_methods || [];
  if (!methods.length) return <p className="text-xs font-mono text-muted-foreground">No function call data available.</p>;

  const maxCount = Math.max(...methods.map(m => m.count), 1);

  return (
    <div className="space-y-2">
      {methods.map((m, i) => {
        const w = pct(m.count, maxCount);
        return (
          <div key={i} className="flex items-center gap-2">
            <span className="w-32 text-xs font-mono text-muted-foreground truncate shrink-0"
              title={m.method_id}>{methodLabel(m.method_id)}</span>
            <div className="flex-1 bg-secondary/40 rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${w}%` }}
              />
            </div>
            <span className="w-12 text-xs font-mono text-right text-foreground shrink-0">
              {fmtNum(m.count)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function InteractionGraph({ data }) {
  const callers = Object.entries(data.repeated_callers || {}).slice(0, 8);
  if (!callers.length)
    return <p className="text-xs font-mono text-muted-foreground">No repeated callers detected.</p>;

  const maxCalls = Math.max(...callers.map(([, c]) => c), 1);

  return (
    <div className="space-y-2">
      {callers.map(([addr, count]) => {
        const w = pct(count, maxCalls);
        const short = `${addr.slice(0, 8)}…${addr.slice(-4)}`;
        return (
          <div key={addr} className="flex items-center gap-2">
            <span
              className="w-28 text-xs font-mono text-muted-foreground truncate shrink-0 cursor-pointer hover:text-primary"
              title={addr}
              onClick={() => window.open(`https://etherscan.io/address/${addr}`, "_blank", "noopener")}
            >
              {short}
            </span>
            <div className="flex-1 bg-secondary/40 rounded-full h-2">
              <div
                className="bg-orange-500 h-2 rounded-full transition-all"
                style={{ width: `${w}%` }}
              />
            </div>
            <span className="w-12 text-xs font-mono text-right text-foreground shrink-0">
              {fmtNum(count)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function HighValueTable({ flows }) {
  if (!flows || !flows.length)
    return <p className="text-xs font-mono text-muted-foreground">No high-value transactions detected.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-border/50 text-muted-foreground">
            <th className="text-left py-1.5 px-2">Tx Hash</th>
            <th className="text-left py-1.5 px-2">From</th>
            <th className="text-right py-1.5 px-2">Value (ETH)</th>
            <th className="text-right py-1.5 px-2">Date</th>
          </tr>
        </thead>
        <tbody>
          {flows.slice(0, 10).map((f, i) => (
            <tr key={i} className="border-b border-border/30 hover:bg-secondary/20">
              <td className="py-1.5 px-2">
                <a
                  href={`https://etherscan.io/tx/${f.hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline flex items-center gap-1"
                >
                  {f.hash ? `${f.hash.slice(0, 10)}…` : "—"}
                  <ExternalLink className="h-3 w-3" />
                </a>
              </td>
              <td className="py-1.5 px-2 text-muted-foreground">
                {f.from ? `${f.from.slice(0, 8)}…${f.from.slice(-4)}` : "—"}
              </td>
              <td className="py-1.5 px-2 text-right text-yellow-400 font-semibold">
                {fmtEth(f.value_eth)}
              </td>
              <td className="py-1.5 px-2 text-right text-muted-foreground">
                {fmtDate(f.timestamp)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SuspiciousPatterns({ patterns }) {
  if (!patterns || !patterns.length) return null;

  return (
    <div className="space-y-2">
      {patterns.map((p, i) => (
        <div key={i} className="flex items-start gap-2 p-2 rounded bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
          <p className="text-xs font-mono text-red-300 leading-relaxed">{p}</p>
        </div>
      ))}
    </div>
  );
}

function ReputationBadge({ reputation }) {
  if (!reputation) return null;
  const score = reputation.score ?? 50;
  let color = "text-muted-foreground";
  if (score >= 80) color = "text-green-400";
  else if (score >= 60) color = "text-lime-400";
  else if (score >= 40) color = "text-yellow-400";
  else if (score >= 20) color = "text-orange-400";
  else color = "text-red-400";

  return (
    <div className="flex items-center gap-3">
      <div className="flex flex-col items-center">
        <p className={`text-3xl font-bold font-mono ${color}`}>{score}</p>
        <p className="text-[10px] font-mono text-muted-foreground">/ 100</p>
      </div>
      <div>
        <Badge variant="outline" className={`${color} border-current text-xs`}>
          {reputation.verdict || "UNKNOWN"}
        </Badge>
        {reputation.risk_adjustment != null && (
          <p className="text-[10px] font-mono text-muted-foreground mt-1">
            Risk adj: {reputation.risk_adjustment > 0 ? "+" : ""}{reputation.risk_adjustment}
          </p>
        )}
      </div>
    </div>
  );
}

/* ---------- MAIN COMPONENT ---------- */

export default function OnChainIntelligence({ data, contractAddress }) {
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    activity: true,
    interactions: false,
    highValue: false,
    patterns: true,
    logs: false,
  });

  const toggle = (key) =>
    setExpandedSections((s) => ({ ...s, [key]: !s[key] }));

  if (!data) {
    return (
      <Card className="border-border bg-card/50 border-l-4 border-l-muted-foreground/30">
        <CardContent className="p-6 text-center">
          <Globe className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm font-mono text-muted-foreground">
            No on-chain data available.
          </p>
          <p className="text-xs font-mono text-muted-foreground/60 mt-1">
            Provide a contract address when creating a scan to enable on-chain intelligence.
          </p>
        </CardContent>
      </Card>
    );
  }

  const addr = data.address || contractAddress || "";
  const addrShort = addr ? `${addr.slice(0, 8)}…${addr.slice(-4)}` : "—";
  const rep = data.reputation;
  const susCount = (data.suspicious_patterns || []).length;

  const sections = [
    {
      key: "overview",
      title: "Contract Overview",
      icon: Globe,
      badge: rep ? `Rep: ${rep.score}` : null,
      content: (
        <div className="space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
              <Hash className="h-3 w-3" />
              <a
                href={`https://etherscan.io/address/${addr}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline flex items-center gap-1"
              >
                {addr || "—"} <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            {rep && <ReputationBadge reputation={rep} />}
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            <StatCard icon={Activity} label="Transactions" value={fmtNum(data.tx_count)}
              sub={`${fmtNum(data.failed_tx_count)} failed (${(data.failure_rate * 100).toFixed(1)}%)`} />
            <StatCard icon={Users} label="Unique Callers" value={fmtNum(data.unique_callers)} />
            <StatCard icon={TrendingUp} label="Total Value" value={`${fmtEth(data.total_value_eth)} ETH`}
              sub={`${fmtNum(data.high_value_tx_count)} high-value txs`} />
            <StatCard icon={Clock} label="Contract Age" value={`${fmtNum(data.contract_age_days)} days`}
              sub={data.first_tx_timestamp ? `Since ${fmtDate(data.first_tx_timestamp)}` : null} />
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2 rounded bg-secondary/30 border border-border/50">
              <p className="text-[10px] font-mono text-muted-foreground">Tokens</p>
              <p className="text-sm font-bold font-mono">{fmtNum(data.unique_tokens)}</p>
              <p className="text-[10px] font-mono text-muted-foreground">{fmtNum(data.token_transfer_count)} transfers</p>
            </div>
            <div className="p-2 rounded bg-secondary/30 border border-border/50">
              <p className="text-[10px] font-mono text-muted-foreground">Events</p>
              <p className="text-sm font-bold font-mono">{fmtNum(data.event_log_count)}</p>
              <p className="text-[10px] font-mono text-muted-foreground">log entries</p>
            </div>
            <div className="p-2 rounded bg-secondary/30 border border-border/50">
              <p className="text-[10px] font-mono text-muted-foreground">Receivers</p>
              <p className="text-sm font-bold font-mono">{fmtNum(data.unique_receivers)}</p>
              <p className="text-[10px] font-mono text-muted-foreground">unique addrs</p>
            </div>
          </div>
        </div>
      ),
    },
    {
      key: "activity",
      title: "Function Call Distribution",
      icon: Zap,
      badge: data.top_methods?.length ? `${data.top_methods.length} methods` : null,
      content: <TxActivityChart data={data} />,
    },
    {
      key: "interactions",
      title: "Interaction Graph",
      icon: Users,
      badge: Object.keys(data.repeated_callers || {}).length
        ? `${Object.keys(data.repeated_callers).length} repeated`
        : null,
      content: <InteractionGraph data={data} />,
    },
    {
      key: "highValue",
      title: "High-Value Transactions",
      icon: TrendingUp,
      badge: data.high_value_tx_count ? `${data.high_value_tx_count} txs` : null,
      content: <HighValueTable flows={data.high_value_flows} />,
    },
    {
      key: "patterns",
      title: "Suspicious Patterns",
      icon: AlertTriangle,
      badge: susCount > 0 ? `${susCount} alerts` : null,
      badgeColor: susCount > 0 ? "bg-red-500/20 text-red-400 border-red-500/30" : null,
      content: susCount > 0
        ? <SuspiciousPatterns patterns={data.suspicious_patterns} />
        : <p className="text-xs font-mono text-green-400">No suspicious patterns detected.</p>,
    },
  ];

  return (
    <Card className="border-border bg-card/50 border-l-4 border-l-primary/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Globe className="h-4 w-4" /> On-Chain Intelligence
          {addr && (
            <Badge variant="outline" className="font-mono text-[10px] ml-auto">
              {addrShort}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {data.warnings && data.warnings.length > 0 && (
          <div className="p-2 rounded bg-yellow-500/10 border border-yellow-500/20 text-xs font-mono text-yellow-400">
            {data.warnings.join(" | ")}
          </div>
        )}
        {sections.map((sec) => (
          <div key={sec.key} className="border border-border/50 rounded-lg overflow-hidden">
            <button
              className="w-full flex items-center justify-between p-3 hover:bg-secondary/20 transition-colors text-left"
              onClick={() => toggle(sec.key)}
            >
              <div className="flex items-center gap-2">
                <sec.icon className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-mono font-semibold uppercase tracking-wider">
                  {sec.title}
                </span>
                {sec.badge && (
                  <Badge
                    variant="outline"
                    className={`text-[10px] font-mono ${sec.badgeColor || ""}`}
                  >
                    {sec.badge}
                  </Badge>
                )}
              </div>
              {expandedSections[sec.key]
                ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
                : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
            </button>
            {expandedSections[sec.key] && (
              <div className="p-3 border-t border-border/30">
                {sec.content}
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
