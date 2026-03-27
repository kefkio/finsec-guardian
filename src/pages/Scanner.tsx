import { useState } from "react";
import { Search, Upload, AlertTriangle, CheckCircle, XCircle, Code2, Play } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";

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

interface Finding {
  id: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  line: number;
  description: string;
  recommendation: string;
  category: string;
}

const mockFindings: Finding[] = [
  {
    id: "SWC-107",
    severity: "critical",
    title: "Reentrancy Vulnerability",
    line: 17,
    description:
      "The withdraw() function sends ETH via a low-level call before updating the sender's balance. An attacker can re-enter the function before the balance is set to zero.",
    recommendation:
      "Apply the Checks-Effects-Interactions pattern. Update balances[msg.sender] = 0 before the external call.",
    category: "Reentrancy",
  },
  {
    id: "SWC-105",
    severity: "critical",
    title: "Missing Access Control",
    line: 24,
    description:
      "emergencyWithdraw() has no access control modifier. Any address can drain all funds from the contract.",
    recommendation:
      "Add an onlyOwner modifier or use OpenZeppelin's Ownable contract to restrict access.",
    category: "Access Control",
  },
  {
    id: "SWC-103",
    severity: "medium",
    title: "Floating Pragma",
    line: 2,
    description:
      "The contract uses ^0.8.0 which allows compilation with any 0.8.x compiler. Different compiler versions may introduce subtle bugs.",
    recommendation: "Lock the pragma to a specific version, e.g., pragma solidity 0.8.19;",
    category: "Best Practice",
  },
  {
    id: "GAS-01",
    severity: "low",
    title: "Unchecked Return Value Pattern",
    line: 19,
    description:
      "Using low-level call with manual success check. Consider using OpenZeppelin's Address.sendValue for safer transfers.",
    recommendation:
      "Use Address.sendValue(payable(msg.sender), balance) from OpenZeppelin for cleaner error handling.",
    category: "Gas Optimization",
  },
  {
    id: "INFO-01",
    severity: "info",
    title: "Missing Events",
    line: 8,
    description: "deposit() and withdraw() functions do not emit events. This makes it harder to track contract activity off-chain.",
    recommendation: "Add event emissions for Deposit and Withdrawal actions.",
    category: "Best Practice",
  },
];

const severityStyles: Record<string, { badge: string; border: string }> = {
  critical: { badge: "bg-destructive text-destructive-foreground", border: "border-l-destructive" },
  high: { badge: "bg-warning text-warning-foreground", border: "border-l-warning" },
  medium: { badge: "bg-info text-info-foreground", border: "border-l-info" },
  low: { badge: "bg-success text-success-foreground", border: "border-l-success" },
  info: { badge: "bg-muted text-muted-foreground", border: "border-l-muted-foreground" },
};

const Scanner = () => {
  const [code, setCode] = useState(sampleContract);
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [scanned, setScanned] = useState(false);

  const handleScan = () => {
    setScanning(true);
    setFindings([]);
    setProgress(0);
    setScanned(false);

    const steps = [10, 25, 40, 55, 70, 85, 95, 100];
    steps.forEach((step, i) => {
      setTimeout(() => {
        setProgress(step);
        if (step === 100) {
          setScanning(false);
          setFindings(mockFindings);
          setScanned(true);
        }
      }, (i + 1) * 400);
    });
  };

  const criticalCount = findings.filter((f) => f.severity === "critical").length;
  const highCount = findings.filter((f) => f.severity === "high").length;

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
        {/* Code Input */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Code2 className="h-4 w-4" /> Solidity Source
              </CardTitle>
              <Button variant="outline" size="sm" className="font-mono text-xs" onClick={() => setCode(sampleContract)}>
                Load Example
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <Textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
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

        {/* Findings */}
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
                {/* Summary */}
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
                    {findings.filter((f) => f.severity === "medium").length} Medium
                  </Badge>
                  <Badge className="bg-success text-success-foreground font-mono">
                    {findings.filter((f) => f.severity === "low").length} Low
                  </Badge>
                </div>

                {/* Finding Cards */}
                <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
                  {findings.map((finding) => (
                    <div
                      key={finding.id}
                      className={`rounded-md border border-border bg-secondary/20 p-3 border-l-4 ${severityStyles[finding.severity].border}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <Badge className={severityStyles[finding.severity].badge} variant="secondary">
                            {finding.severity}
                          </Badge>
                          <span className="text-xs font-mono text-muted-foreground">{finding.id}</span>
                        </div>
                        <span className="text-xs font-mono text-muted-foreground">Line {finding.line}</span>
                      </div>
                      <h4 className="text-sm font-semibold mt-1">{finding.title}</h4>
                      <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                        {finding.description}
                      </p>
                      <div className="mt-2 rounded bg-primary/5 border border-primary/20 p-2">
                        <p className="text-xs font-mono text-primary">
                          ✓ {finding.recommendation}
                        </p>
                      </div>
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
