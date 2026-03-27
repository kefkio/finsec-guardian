import { useState, useCallback } from "react";
import { Link2, ShieldCheck, Plus, Hash, FileText, AlertTriangle, CheckCircle, XCircle, Fingerprint, RefreshCw, Pencil } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

// --- Crypto helpers (browser-native SHA-256) ---
import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
async function sha256(message) {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

// --- Types ---

// Simulated Solidity contract ABI-like display
const SOLIDITY_CONTRACT = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract AuditLedger {
    struct Record {
        uint256 index;
        uint256 timestamp;
        bytes32 dataHash;
        bytes32 previousHash;
        address submitter;
    }

    Record[] public ledger;
    mapping(uint256 => bool) public verified;

    event RecordAdded(uint256 indexed index, bytes32 dataHash);
    event TamperDetected(uint256 indexed index);

    function addRecord(
        bytes32 _dataHash,
        bytes32 _previousHash
    ) external returns (uint256) {
        uint256 idx = ledger.length;
        ledger.push(Record({
            index: idx,
            timestamp: block.timestamp,
            dataHash: _dataHash,
            previousHash: _previousHash,
            submitter: msg.sender
        }));
        verified[idx] = true;
        emit RecordAdded(idx, _dataHash);
        return idx;
    }

    function verifyChain() external view returns (bool) {
        for (uint256 i = 1; i < ledger.length; i++) {
            if (ledger[i].previousHash !=
                keccak256(abi.encodePacked(
                    ledger[i-1].dataHash,
                    ledger[i-1].previousHash
                ))) {
                return false;
            }
        }
        return true;
    }
}`;

// --- Component ---
const TamperProofRecords = () => {
  const [chain, setChain] = useState([]);
  const [recordType, setRecordType] = useState("transaction");
  const [description, setDescription] = useState("");
  const [actor, setActor] = useState("");
  const [value, setValue] = useState("");
  const [verificationResult, setVerificationResult] = useState(null);
  const [showContract, setShowContract] = useState(false);

  // Generate a fake tx hash
  const fakeTxHash = () => "0x" + Array.from(crypto.getRandomValues(new Uint8Array(32))).map(b => b.toString(16).padStart(2, "0")).join("");
  const addRecord = useCallback(async () => {
    if (!description.trim() || !actor.trim()) {
      toast.error("Fill in all required fields");
      return;
    }
    const data = {
      type: recordType,
      description: description.trim(),
      actor: actor.trim(),
      value: value.trim()
    };
    const index = chain.length;
    const timestamp = new Date().toISOString();
    const previousHash = index === 0 ? "0".repeat(64) : chain[index - 1].hash;
    const nonce = Math.floor(Math.random() * 100000);
    const blockContent = `${index}${timestamp}${JSON.stringify(data)}${previousHash}${nonce}`;
    const hash = await sha256(blockContent);
    const newBlock = {
      index,
      timestamp,
      data,
      previousHash,
      hash,
      nonce,
      valid: true,
      contractTx: fakeTxHash()
    };
    setChain(prev => [...prev, newBlock]);
    setDescription("");
    setActor("");
    setValue("");
    setVerificationResult(null);
    toast.success(`Block #${index} added & submitted to smart contract`);
  }, [chain, recordType, description, actor, value]);

  // Verify entire chain
  const verifyChain = useCallback(async () => {
    if (chain.length === 0) {
      toast.error("No records to verify");
      return;
    }
    let valid = true;
    let brokenAt;
    for (let i = 0; i < chain.length; i++) {
      const block = chain[i];
      const expectedPrev = i === 0 ? "0".repeat(64) : chain[i - 1].hash;

      // Check previous hash linkage
      if (block.previousHash !== expectedPrev) {
        valid = false;
        brokenAt = i;
        break;
      }

      // Re-compute hash
      const blockContent = `${block.index}${block.timestamp}${JSON.stringify(block.data)}${block.previousHash}${block.nonce}`;
      const recomputed = await sha256(blockContent);
      if (recomputed !== block.hash) {
        valid = false;
        brokenAt = i;
        break;
      }
    }
    setVerificationResult({
      valid,
      checkedBlocks: chain.length,
      brokenAt
    });
    if (valid) {
      toast.success("Chain integrity verified — no tampering detected");
    } else {
      toast.error(`Tampering detected at block #${brokenAt}!`);
    }
  }, [chain]);

  // Simulate tampering (modify a block's data without updating hash)
  const simulateTamper = useCallback(index => {
    setChain(prev => prev.map((block, i) => i === index ? {
      ...block,
      data: {
        ...block.data,
        description: block.data.description + " [TAMPERED]",
        value: "999999"
      },
      valid: false
    } : block));
    setVerificationResult(null);
    toast.warning(`Block #${index} data was tampered with! Run verification to detect.`);
  }, []);
  return /*#__PURE__*/_jsxs("div", {
    className: "space-y-6",
    children: [/*#__PURE__*/_jsxs("div", {
      className: "flex items-start justify-between flex-wrap gap-4",
      children: [/*#__PURE__*/_jsxs("div", {
        children: [/*#__PURE__*/_jsxs("h1", {
          className: "text-2xl font-bold tracking-tight",
          children: ["Tamper-Proof ", /*#__PURE__*/_jsx("span", {
            className: "text-gradient-primary",
            children: "Records"
          })]
        }), /*#__PURE__*/_jsx("p", {
          className: "text-sm text-muted-foreground font-mono mt-1",
          children: "SHA-256 hash chain with simulated Solidity smart contract anchoring"
        })]
      }), /*#__PURE__*/_jsxs(Button, {
        variant: "outline",
        size: "sm",
        onClick: () => setShowContract(!showContract),
        className: "font-mono text-xs",
        children: [/*#__PURE__*/_jsx(FileText, {
          className: "h-3 w-3 mr-1"
        }), showContract ? "Hide" : "Show", " Smart Contract"]
      })]
    }), showContract && /*#__PURE__*/_jsxs(Card, {
      className: "border-border bg-card",
      children: [/*#__PURE__*/_jsx(CardHeader, {
        className: "pb-2",
        children: /*#__PURE__*/_jsxs(CardTitle, {
          className: "text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2",
          children: [/*#__PURE__*/_jsx(Fingerprint, {
            className: "h-4 w-4"
          }), " AuditLedger.sol"]
        })
      }), /*#__PURE__*/_jsx(CardContent, {
        children: /*#__PURE__*/_jsx("pre", {
          className: "text-xs font-mono bg-secondary/30 rounded-md p-4 overflow-x-auto leading-relaxed text-primary/90 max-h-[300px] overflow-y-auto",
          children: SOLIDITY_CONTRACT
        })
      })]
    }), /*#__PURE__*/_jsxs("div", {
      className: "grid gap-6 lg:grid-cols-3",
      children: [/*#__PURE__*/_jsxs(Card, {
        className: "border-border bg-card lg:col-span-1",
        children: [/*#__PURE__*/_jsx(CardHeader, {
          className: "pb-2",
          children: /*#__PURE__*/_jsxs(CardTitle, {
            className: "text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2",
            children: [/*#__PURE__*/_jsx(Plus, {
              className: "h-4 w-4"
            }), " New Record"]
          })
        }), /*#__PURE__*/_jsxs(CardContent, {
          className: "space-y-4",
          children: [/*#__PURE__*/_jsxs("div", {
            className: "space-y-2",
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-xs font-mono",
              children: "Record Type"
            }), /*#__PURE__*/_jsxs(Select, {
              value: recordType,
              onValueChange: setRecordType,
              children: [/*#__PURE__*/_jsx(SelectTrigger, {
                className: "bg-secondary/30 border-border font-mono text-sm",
                children: /*#__PURE__*/_jsx(SelectValue, {})
              }), /*#__PURE__*/_jsxs(SelectContent, {
                children: [/*#__PURE__*/_jsx(SelectItem, {
                  value: "transaction",
                  children: "Transaction"
                }), /*#__PURE__*/_jsx(SelectItem, {
                  value: "audit_event",
                  children: "Audit Event"
                }), /*#__PURE__*/_jsx(SelectItem, {
                  value: "contract_deploy",
                  children: "Contract Deploy"
                }), /*#__PURE__*/_jsx(SelectItem, {
                  value: "access_change",
                  children: "Access Change"
                }), /*#__PURE__*/_jsx(SelectItem, {
                  value: "config_update",
                  children: "Config Update"
                })]
              })]
            })]
          }), /*#__PURE__*/_jsxs("div", {
            className: "space-y-2",
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-xs font-mono",
              children: "Description *"
            }), /*#__PURE__*/_jsx(Textarea, {
              value: description,
              onChange: e => setDescription(e.target.value),
              className: "bg-secondary/30 border-border font-mono text-sm min-h-[60px] resize-none",
              placeholder: "e.g. Transferred 2.5 ETH to vault"
            })]
          }), /*#__PURE__*/_jsxs("div", {
            className: "space-y-2",
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-xs font-mono",
              children: "Actor *"
            }), /*#__PURE__*/_jsx(Input, {
              value: actor,
              onChange: e => setActor(e.target.value),
              className: "bg-secondary/30 border-border font-mono text-sm",
              placeholder: "0x7a2b...9f3e"
            })]
          }), /*#__PURE__*/_jsxs("div", {
            className: "space-y-2",
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-xs font-mono",
              children: "Value"
            }), /*#__PURE__*/_jsx(Input, {
              value: value,
              onChange: e => setValue(e.target.value),
              className: "bg-secondary/30 border-border font-mono text-sm",
              placeholder: "e.g. 2.5 ETH"
            })]
          }), /*#__PURE__*/_jsxs(Button, {
            onClick: addRecord,
            className: "w-full gradient-primary text-primary-foreground font-mono font-semibold",
            children: [/*#__PURE__*/_jsx(Link2, {
              className: "h-4 w-4 mr-2"
            }), " Add to Chain"]
          }), /*#__PURE__*/_jsx(Separator, {}), /*#__PURE__*/_jsxs(Button, {
            onClick: verifyChain,
            variant: "outline",
            className: "w-full font-mono text-sm",
            disabled: chain.length === 0,
            children: [/*#__PURE__*/_jsx(ShieldCheck, {
              className: "h-4 w-4 mr-2"
            }), " Verify Chain Integrity"]
          }), verificationResult && /*#__PURE__*/_jsxs("div", {
            className: `rounded-md border p-3 ${verificationResult.valid ? "border-success/30 bg-success/5" : "border-destructive/30 bg-destructive/5"}`,
            children: [/*#__PURE__*/_jsxs("div", {
              className: "flex items-center gap-2",
              children: [verificationResult.valid ? /*#__PURE__*/_jsx(CheckCircle, {
                className: "h-4 w-4 text-success"
              }) : /*#__PURE__*/_jsx(XCircle, {
                className: "h-4 w-4 text-destructive"
              }), /*#__PURE__*/_jsx("span", {
                className: "text-sm font-semibold",
                children: verificationResult.valid ? "Chain Valid" : "Tampering Detected!"
              })]
            }), /*#__PURE__*/_jsxs("p", {
              className: "text-xs font-mono text-muted-foreground mt-1",
              children: ["Checked ", verificationResult.checkedBlocks, " blocks", verificationResult.brokenAt !== undefined && /*#__PURE__*/_jsxs(_Fragment, {
                children: [" \u2014 broken at block #", verificationResult.brokenAt]
              })]
            })]
          })]
        })]
      }), /*#__PURE__*/_jsxs("div", {
        className: "lg:col-span-2 space-y-4",
        children: [/*#__PURE__*/_jsxs("div", {
          className: "flex items-center justify-between",
          children: [/*#__PURE__*/_jsxs("h2", {
            className: "text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2",
            children: [/*#__PURE__*/_jsx(Hash, {
              className: "h-4 w-4"
            }), " Hash Chain \u2014 ", chain.length, " Blocks"]
          }), chain.length > 0 && /*#__PURE__*/_jsxs(Button, {
            variant: "ghost",
            size: "sm",
            onClick: () => {
              setChain([]);
              setVerificationResult(null);
            },
            className: "text-xs font-mono text-muted-foreground",
            children: [/*#__PURE__*/_jsx(RefreshCw, {
              className: "h-3 w-3 mr-1"
            }), " Reset"]
          })]
        }), chain.length === 0 && /*#__PURE__*/_jsx(Card, {
          className: "border-border bg-card border-dashed",
          children: /*#__PURE__*/_jsxs(CardContent, {
            className: "flex flex-col items-center justify-center py-16 text-muted-foreground",
            children: [/*#__PURE__*/_jsx(Link2, {
              className: "h-12 w-12 mb-3 opacity-20"
            }), /*#__PURE__*/_jsx("p", {
              className: "font-mono text-sm",
              children: "No records yet \u2014 add one to start the chain"
            })]
          })
        }), chain.map((block, i) => /*#__PURE__*/_jsxs("div", {
          className: "relative",
          children: [i > 0 && /*#__PURE__*/_jsx("div", {
            className: "flex items-center justify-center py-1",
            children: /*#__PURE__*/_jsxs("div", {
              className: "flex flex-col items-center gap-0.5",
              children: [/*#__PURE__*/_jsx("div", {
                className: "h-4 w-px bg-primary/30"
              }), /*#__PURE__*/_jsx(Link2, {
                className: "h-3 w-3 text-primary/40"
              }), /*#__PURE__*/_jsx("div", {
                className: "h-4 w-px bg-primary/30"
              })]
            })
          }), /*#__PURE__*/_jsx(Card, {
            className: `border bg-card overflow-hidden ${!block.valid ? "border-destructive/50 glow-danger" : verificationResult?.brokenAt === i ? "border-destructive/50 glow-danger" : "border-border"}`,
            children: /*#__PURE__*/_jsx(CardContent, {
              className: "p-0",
              children: /*#__PURE__*/_jsxs("div", {
                className: "flex flex-col",
                children: [/*#__PURE__*/_jsxs("div", {
                  className: "flex items-center justify-between px-4 py-2.5 bg-secondary/20 border-b border-border",
                  children: [/*#__PURE__*/_jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [/*#__PURE__*/_jsxs(Badge, {
                      variant: "outline",
                      className: "font-mono text-xs",
                      children: ["Block #", block.index]
                    }), /*#__PURE__*/_jsx(Badge, {
                      variant: "secondary",
                      className: "font-mono text-[10px] bg-accent/10 text-accent",
                      children: block.data.type
                    }), !block.valid && /*#__PURE__*/_jsxs(Badge, {
                      className: "bg-destructive text-destructive-foreground text-[10px]",
                      children: [/*#__PURE__*/_jsx(AlertTriangle, {
                        className: "h-3 w-3 mr-1"
                      }), " TAMPERED"]
                    })]
                  }), /*#__PURE__*/_jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [/*#__PURE__*/_jsx("span", {
                      className: "text-[10px] font-mono text-muted-foreground",
                      children: new Date(block.timestamp).toLocaleTimeString()
                    }), /*#__PURE__*/_jsx(Button, {
                      variant: "ghost",
                      size: "sm",
                      className: "h-6 w-6 p-0 text-muted-foreground hover:text-destructive",
                      onClick: () => simulateTamper(block.index),
                      title: "Simulate tampering",
                      children: /*#__PURE__*/_jsx(Pencil, {
                        className: "h-3 w-3"
                      })
                    })]
                  })]
                }), /*#__PURE__*/_jsxs("div", {
                  className: "p-4 space-y-3",
                  children: [/*#__PURE__*/_jsxs("div", {
                    children: [/*#__PURE__*/_jsx("p", {
                      className: "text-sm",
                      children: block.data.description
                    }), /*#__PURE__*/_jsxs("div", {
                      className: "flex gap-4 mt-1 text-[11px] font-mono text-muted-foreground",
                      children: [/*#__PURE__*/_jsxs("span", {
                        children: [/*#__PURE__*/_jsx("span", {
                          className: "text-foreground/50",
                          children: "actor:"
                        }), " ", block.data.actor]
                      }), block.data.value && /*#__PURE__*/_jsxs("span", {
                        children: [/*#__PURE__*/_jsx("span", {
                          className: "text-foreground/50",
                          children: "value:"
                        }), " ", block.data.value]
                      })]
                    })]
                  }), /*#__PURE__*/_jsxs("div", {
                    className: "space-y-1.5 bg-secondary/20 rounded-md p-3",
                    children: [/*#__PURE__*/_jsxs("div", {
                      className: "flex items-center gap-2 text-[11px] font-mono",
                      children: [/*#__PURE__*/_jsx("span", {
                        className: "text-muted-foreground w-16 shrink-0",
                        children: "hash:"
                      }), /*#__PURE__*/_jsx("span", {
                        className: "text-primary truncate",
                        children: block.hash
                      })]
                    }), /*#__PURE__*/_jsxs("div", {
                      className: "flex items-center gap-2 text-[11px] font-mono",
                      children: [/*#__PURE__*/_jsx("span", {
                        className: "text-muted-foreground w-16 shrink-0",
                        children: "prev:"
                      }), /*#__PURE__*/_jsx("span", {
                        className: "text-foreground/60 truncate",
                        children: block.previousHash
                      })]
                    }), /*#__PURE__*/_jsxs("div", {
                      className: "flex items-center gap-2 text-[11px] font-mono",
                      children: [/*#__PURE__*/_jsx("span", {
                        className: "text-muted-foreground w-16 shrink-0",
                        children: "nonce:"
                      }), /*#__PURE__*/_jsx("span", {
                        className: "text-foreground/60",
                        children: block.nonce
                      })]
                    }), /*#__PURE__*/_jsxs("div", {
                      className: "flex items-center gap-2 text-[11px] font-mono",
                      children: [/*#__PURE__*/_jsx("span", {
                        className: "text-muted-foreground w-16 shrink-0",
                        children: "tx:"
                      }), /*#__PURE__*/_jsx("span", {
                        className: "text-accent truncate",
                        children: block.contractTx
                      })]
                    })]
                  })]
                })]
              })
            })
          })]
        }, block.index))]
      })]
    })]
  });
};
export default TamperProofRecords;