import { useState } from "react";
import { Search, AlertTriangle, Code2, Play } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
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
const mockFindings = [{
  id: "SWC-107",
  severity: "critical",
  title: "Reentrancy Vulnerability",
  line: 17,
  description: "The withdraw() function sends ETH via a low-level call before updating the sender's balance. An attacker can re-enter the function before the balance is set to zero.",
  recommendation: "Apply the Checks-Effects-Interactions pattern. Update balances[msg.sender] = 0 before the external call.",
  category: "Reentrancy"
}, {
  id: "SWC-105",
  severity: "critical",
  title: "Missing Access Control",
  line: 24,
  description: "emergencyWithdraw() has no access control modifier. Any address can drain all funds from the contract.",
  recommendation: "Add an onlyOwner modifier or use OpenZeppelin's Ownable contract to restrict access.",
  category: "Access Control"
}, {
  id: "SWC-103",
  severity: "medium",
  title: "Floating Pragma",
  line: 2,
  description: "The contract uses ^0.8.0 which allows compilation with any 0.8.x compiler. Different compiler versions may introduce subtle bugs.",
  recommendation: "Lock the pragma to a specific version, e.g., pragma solidity 0.8.19;",
  category: "Best Practice"
}, {
  id: "GAS-01",
  severity: "low",
  title: "Unchecked Return Value Pattern",
  line: 19,
  description: "Using low-level call with manual success check. Consider using OpenZeppelin's Address.sendValue for safer transfers.",
  recommendation: "Use Address.sendValue(payable(msg.sender), balance) from OpenZeppelin for cleaner error handling.",
  category: "Gas Optimization"
}, {
  id: "INFO-01",
  severity: "info",
  title: "Missing Events",
  line: 8,
  description: "deposit() and withdraw() functions do not emit events. This makes it harder to track contract activity off-chain.",
  recommendation: "Add event emissions for Deposit and Withdrawal actions.",
  category: "Best Practice"
}];
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
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [findings, setFindings] = useState([]);
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
  const criticalCount = findings.filter(f => f.severity === "critical").length;
  const highCount = findings.filter(f => f.severity === "high").length;
  return /*#__PURE__*/_jsxs("div", {
    className: "space-y-6",
    children: [/*#__PURE__*/_jsxs("div", {
      children: [/*#__PURE__*/_jsxs("h1", {
        className: "text-2xl font-bold tracking-tight",
        children: ["Contract ", /*#__PURE__*/_jsx("span", {
          className: "text-gradient-primary",
          children: "Scanner"
        })]
      }), /*#__PURE__*/_jsx("p", {
        className: "text-sm text-muted-foreground font-mono mt-1",
        children: "Static analysis for Solidity smart contracts \u2014 OWASP SWC Registry"
      })]
    }), /*#__PURE__*/_jsxs("div", {
      className: "grid gap-6 lg:grid-cols-2",
      children: [/*#__PURE__*/_jsxs(Card, {
        className: "border-border bg-card",
        children: [/*#__PURE__*/_jsx(CardHeader, {
          className: "pb-2",
          children: /*#__PURE__*/_jsxs("div", {
            className: "flex items-center justify-between",
            children: [/*#__PURE__*/_jsxs(CardTitle, {
              className: "text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2",
              children: [/*#__PURE__*/_jsx(Code2, {
                className: "h-4 w-4"
              }), " Solidity Source"]
            }), /*#__PURE__*/_jsx(Button, {
              variant: "outline",
              size: "sm",
              className: "font-mono text-xs",
              onClick: () => setCode(sampleContract),
              children: "Load Example"
            })]
          })
        }), /*#__PURE__*/_jsxs(CardContent, {
          children: [/*#__PURE__*/_jsx(Textarea, {
            value: code,
            onChange: e => setCode(e.target.value),
            className: "min-h-[400px] font-mono text-xs bg-secondary/30 border-border resize-none leading-relaxed",
            placeholder: "// Paste your Solidity contract here..."
          }), /*#__PURE__*/_jsx(Button, {
            onClick: handleScan,
            disabled: scanning || !code.trim(),
            className: "mt-4 w-full gradient-primary text-primary-foreground font-mono font-semibold",
            children: scanning ? /*#__PURE__*/_jsx(_Fragment, {
              children: "Scanning..."
            }) : /*#__PURE__*/_jsxs(_Fragment, {
              children: [/*#__PURE__*/_jsx(Play, {
                className: "h-4 w-4 mr-2"
              }), " Run Security Analysis"]
            })
          }), scanning && /*#__PURE__*/_jsxs("div", {
            className: "mt-3 space-y-1",
            children: [/*#__PURE__*/_jsx(Progress, {
              value: progress,
              className: "h-1.5"
            }), /*#__PURE__*/_jsxs("p", {
              className: "text-xs font-mono text-muted-foreground",
              children: ["Analyzing patterns... ", progress, "%"]
            })]
          })]
        })]
      }), /*#__PURE__*/_jsxs(Card, {
        className: "border-border bg-card",
        children: [/*#__PURE__*/_jsx(CardHeader, {
          className: "pb-2",
          children: /*#__PURE__*/_jsxs(CardTitle, {
            className: "text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2",
            children: [/*#__PURE__*/_jsx(AlertTriangle, {
              className: "h-4 w-4"
            }), " Findings", scanned && /*#__PURE__*/_jsxs(Badge, {
              variant: "secondary",
              className: "ml-2 font-mono",
              children: [findings.length, " issues"]
            })]
          })
        }), /*#__PURE__*/_jsxs(CardContent, {
          children: [!scanned && !scanning && /*#__PURE__*/_jsxs("div", {
            className: "flex flex-col items-center justify-center h-[400px] text-muted-foreground",
            children: [/*#__PURE__*/_jsx(Search, {
              className: "h-12 w-12 mb-3 opacity-30"
            }), /*#__PURE__*/_jsx("p", {
              className: "font-mono text-sm",
              children: "Paste a contract and run the scanner"
            })]
          }), scanned && /*#__PURE__*/_jsxs("div", {
            className: "space-y-4",
            children: [/*#__PURE__*/_jsxs("div", {
              className: "flex gap-2 flex-wrap",
              children: [criticalCount > 0 && /*#__PURE__*/_jsxs(Badge, {
                className: "bg-destructive text-destructive-foreground font-mono",
                children: [criticalCount, " Critical"]
              }), highCount > 0 && /*#__PURE__*/_jsxs(Badge, {
                className: "bg-warning text-warning-foreground font-mono",
                children: [highCount, " High"]
              }), /*#__PURE__*/_jsxs(Badge, {
                className: "bg-info text-info-foreground font-mono",
                children: [findings.filter(f => f.severity === "medium").length, " Medium"]
              }), /*#__PURE__*/_jsxs(Badge, {
                className: "bg-success text-success-foreground font-mono",
                children: [findings.filter(f => f.severity === "low").length, " Low"]
              })]
            }), /*#__PURE__*/_jsx("div", {
              className: "space-y-3 max-h-[360px] overflow-y-auto pr-1",
              children: findings.map(finding => /*#__PURE__*/_jsxs("div", {
                className: `rounded-md border border-border bg-secondary/20 p-3 border-l-4 ${severityStyles[finding.severity].border}`,
                children: [/*#__PURE__*/_jsxs("div", {
                  className: "flex items-center justify-between mb-1",
                  children: [/*#__PURE__*/_jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [/*#__PURE__*/_jsx(Badge, {
                      className: severityStyles[finding.severity].badge,
                      variant: "secondary",
                      children: finding.severity
                    }), /*#__PURE__*/_jsx("span", {
                      className: "text-xs font-mono text-muted-foreground",
                      children: finding.id
                    })]
                  }), /*#__PURE__*/_jsxs("span", {
                    className: "text-xs font-mono text-muted-foreground",
                    children: ["Line ", finding.line]
                  })]
                }), /*#__PURE__*/_jsx("h4", {
                  className: "text-sm font-semibold mt-1",
                  children: finding.title
                }), /*#__PURE__*/_jsx("p", {
                  className: "text-xs text-muted-foreground mt-1 leading-relaxed",
                  children: finding.description
                }), /*#__PURE__*/_jsx("div", {
                  className: "mt-2 rounded bg-primary/5 border border-primary/20 p-2",
                  children: /*#__PURE__*/_jsxs("p", {
                    className: "text-xs font-mono text-primary",
                    children: ["\u2713 ", finding.recommendation]
                  })
                })]
              }, finding.id))
            })]
          })]
        })]
      })]
    })]
  });
};
export default Scanner;