import { useState, useEffect, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { scannerApi } from "@/lib/api";
import { Search, AlertTriangle, Code2, Play } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";

const TOOLS = [
  { value: 'slither', label: 'Slither', description: 'Static analysis (fast)' },
  { value: 'mythril', label: 'Mythril', description: 'Symbolic execution' },
  { value: 'echidna', label: 'Echidna', description: 'Fuzzing / properties' },
];

const sampleContract = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableVault {
    mapping(address => uint256) public balances;
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    // VULNERABLE: Reentrancy attack vector
    function withdraw() external {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "No balance");
        
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] = 0; // State update AFTER external call
    }
    
    // VULNERABLE: No access control
    function emergencyWithdraw() external {
        payable(msg.sender).transfer(address(this).balance);
    }
}`;

const severityStyles = {
  critical: {
    badge: "bg-destructive text-destructive-foreground",
    border: "border-l-destructive"
  },
  high: {
    badge: "bg-warning text-warning-foreground",
    border: "border-l-warning"
  },
  medium: {
    badge: "bg-info text-info-foreground",
    border: "border-l-info"
  },
  low: {
    badge: "bg-success text-success-foreground",
    border: "border-l-success"
  },
  info: {
    badge: "bg-muted text-muted-foreground",
    border: "border-l-muted-foreground"
  }
};

const Scanner = () => {
  const [code, setCode] = useState(sampleContract);
  const [tool, setTool] = useState('slither');
  const [progress, setProgress] = useState(0);
  const [findings, setFindings] = useState([]);
  const [scanned, setScanned] = useState(false);
  const progressIntervalRef = useRef(null);

  const mutation = useMutation({
    mutationFn: () => scannerApi.createScan({ source_code: code, contract_name: 'Unnamed', tool }),
    onSuccess: (data) => {
      const rawFindings = data.findings || [];
      setFindings(rawFindings.map(f => ({
        id: f.swc_id || String(f.id),
        line: f.line_number,
        severity: f.severity,
        title: f.title,
        description: f.description,
        recommendation: f.recommendation,
      })));
      setProgress(100);
      setScanned(true);
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    },
    onError: (error) => {
      toast.error(error.message || 'Scan failed');
      setProgress(0);
      setScanned(false);
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    },
  });

  const handleScan = () => {
    setFindings([]);
    setProgress(0);
    setScanned(false);

    let p = 0;
    progressIntervalRef.current = setInterval(() => {
      p = Math.min(p + Math.random() * 12 + 3, 90);
      setProgress(Math.floor(p));
    }, 350);

    mutation.mutate();
  };

  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);

  const scanning = mutation.isPending;
  const criticalCount = findings.filter(f => f.severity === "critical").length;
  const highCount = findings.filter(f => f.severity === "high").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Contract <span className="text-gradient-primary">Scanner</span>
        </h1>
        <p className="text-sm text-muted-foreground font-mono mt-1">
          Static analysis for Solidity smart contracts — OWASP SWC Registry
        </p>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Code2 className="h-4 w-4" /> Solidity Source
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs"
                onClick={() => setCode(sampleContract)}
              >
                Load Example
              </Button>
            </div>
            <div className="flex gap-2 pt-2">
              {TOOLS.map(t => (
                <button
                  key={t.value}
                  onClick={() => setTool(t.value)}
                  className={`flex-1 rounded border px-2 py-1.5 text-xs font-mono transition-colors ${
                    tool === t.value
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border text-muted-foreground hover:border-primary/50'
                  }`}
                >
                  <div className="font-semibold">{t.label}</div>
                  <div className="text-[10px] opacity-70">{t.description}</div>
                </button>
              ))}
            </div>
          </CardHeader>
          <CardContent>
            <Textarea
              value={code}
              onChange={e => setCode(e.target.value)}
              className="min-h-[400px] font-mono text-xs bg-secondary/30 border-border resize-none leading-relaxed"
              placeholder="// Paste your Solidity contract here..."
            />
            <Button
              onClick={handleScan}
              disabled={scanning || !code.trim()}
              className="mt-4 w-full gradient-primary text-primary-foreground font-mono font-semibold"
            >
              {scanning ? (
                <>Scanning...</>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" /> Run Security Analysis
                </>
              )}
            </Button>
            {scanning && (
              <div className="mt-3 space-y-1">
                <Progress value={progress} className="h-1.5" />
                <p className="text-xs font-mono text-muted-foreground">
                  Analyzing patterns... {progress}%
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" /> Findings
              {scanned && (
                <Badge variant="secondary" className="ml-2 font-mono">
                  {findings.length} issues
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!scanned && !scanning && (
              <div className="flex flex-col items-center justify-center h-[400px] text-muted-foreground">
                <Search className="h-12 w-12 mb-3 opacity-30" />
                <p className="font-mono text-sm">Paste a contract and run the scanner</p>
              </div>
            )}
            {scanned && (
              <div className="space-y-4">
                <div className="flex gap-2 flex-wrap">
                  {criticalCount > 0 && (
                    <Badge className="bg-destructive text-destructive-foreground font-mono">
                      {criticalCount} Critical
                    </Badge>
                  )}
                  {highCount > 0 && (
                    <Badge className="bg-warning text-warning-foreground font-mono">
                      {highCount} High
                    </Badge>
                  )}
                  <Badge className="bg-info text-info-foreground font-mono">
                    {findings.filter(f => f.severity === "medium").length} Medium
                  </Badge>
                  <Badge className="bg-success text-success-foreground font-mono">
                    {findings.filter(f => f.severity === "low").length} Low
                  </Badge>
                </div>
                <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
                  {findings.map(finding => (
                    <div
                      key={finding.id}
                      className={`rounded-md border border-border bg-secondary/20 p-3 border-l-4 ${(severityStyles[finding.severity] || severityStyles.info).border}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <Badge
                            className={(severityStyles[finding.severity] || severityStyles.info).badge}
                            variant="secondary"
                          >
                            {finding.severity}
                          </Badge>
                          <span className="text-xs font-mono text-muted-foreground">{finding.id}</span>
                        </div>
                        {finding.line != null && (
                          <span className="text-xs font-mono text-muted-foreground">Line {finding.line}</span>
                        )}
                      </div>
                      <h4 className="text-sm font-semibold mt-1">{finding.title}</h4>
                      <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{finding.description}</p>
                      {finding.recommendation && (
                        <div className="mt-2 rounded bg-primary/5 border border-primary/20 p-2">
                          <p className="text-xs font-mono text-primary">✓ {finding.recommendation}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Scanner;
