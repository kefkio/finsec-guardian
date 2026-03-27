import { useState, useCallback } from "react";
import {
  Link2,
  ShieldCheck,
  ShieldAlert,
  Plus,
  Hash,
  FileText,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Fingerprint,
  RefreshCw,
  Pencil,
} from "lucide-react";
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
async function sha256(message: string): Promise<string> {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

// --- Types ---
interface Block {
  index: number;
  timestamp: string;
  data: RecordData;
  previousHash: string;
  hash: string;
  nonce: number;
  valid: boolean;
  contractTx: string;
}

interface RecordData {
  type: string;
  description: string;
  actor: string;
  value: string;
}

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
  const [chain, setChain] = useState<Block[]>([]);
  const [recordType, setRecordType] = useState("transaction");
  const [description, setDescription] = useState("");
  const [actor, setActor] = useState("");
  const [value, setValue] = useState("");
  const [verificationResult, setVerificationResult] = useState<null | {
    valid: boolean;
    checkedBlocks: number;
    brokenAt?: number;
  }>(null);
  const [showContract, setShowContract] = useState(false);

  // Generate a fake tx hash
  const fakeTxHash = () =>
    "0x" +
    Array.from(crypto.getRandomValues(new Uint8Array(32)))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");

  const addRecord = useCallback(async () => {
    if (!description.trim() || !actor.trim()) {
      toast.error("Fill in all required fields");
      return;
    }

    const data: RecordData = {
      type: recordType,
      description: description.trim(),
      actor: actor.trim(),
      value: value.trim(),
    };

    const index = chain.length;
    const timestamp = new Date().toISOString();
    const previousHash = index === 0 ? "0".repeat(64) : chain[index - 1].hash;
    const nonce = Math.floor(Math.random() * 100000);

    const blockContent = `${index}${timestamp}${JSON.stringify(data)}${previousHash}${nonce}`;
    const hash = await sha256(blockContent);

    const newBlock: Block = {
      index,
      timestamp,
      data,
      previousHash,
      hash,
      nonce,
      valid: true,
      contractTx: fakeTxHash(),
    };

    setChain((prev) => [...prev, newBlock]);
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
    let brokenAt: number | undefined;

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

    setVerificationResult({ valid, checkedBlocks: chain.length, brokenAt });

    if (valid) {
      toast.success("Chain integrity verified — no tampering detected");
    } else {
      toast.error(`Tampering detected at block #${brokenAt}!`);
    }
  }, [chain]);

  // Simulate tampering (modify a block's data without updating hash)
  const simulateTamper = useCallback(
    (index: number) => {
      setChain((prev) =>
        prev.map((block, i) =>
          i === index
            ? {
                ...block,
                data: {
                  ...block.data,
                  description: block.data.description + " [TAMPERED]",
                  value: "999999",
                },
                valid: false,
              }
            : block
        )
      );
      setVerificationResult(null);
      toast.warning(`Block #${index} data was tampered with! Run verification to detect.`);
    },
    []
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Tamper-Proof <span className="text-gradient-primary">Records</span>
          </h1>
          <p className="text-sm text-muted-foreground font-mono mt-1">
            SHA-256 hash chain with simulated Solidity smart contract anchoring
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowContract(!showContract)}
          className="font-mono text-xs"
        >
          <FileText className="h-3 w-3 mr-1" />
          {showContract ? "Hide" : "Show"} Smart Contract
        </Button>
      </div>

      {/* Smart Contract Display */}
      {showContract && (
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Fingerprint className="h-4 w-4" /> AuditLedger.sol
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs font-mono bg-secondary/30 rounded-md p-4 overflow-x-auto leading-relaxed text-primary/90 max-h-[300px] overflow-y-auto">
              {SOLIDITY_CONTRACT}
            </pre>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Add Record Form */}
        <Card className="border-border bg-card lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Plus className="h-4 w-4" /> New Record
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs font-mono">Record Type</Label>
              <Select value={recordType} onValueChange={setRecordType}>
                <SelectTrigger className="bg-secondary/30 border-border font-mono text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="transaction">Transaction</SelectItem>
                  <SelectItem value="audit_event">Audit Event</SelectItem>
                  <SelectItem value="contract_deploy">Contract Deploy</SelectItem>
                  <SelectItem value="access_change">Access Change</SelectItem>
                  <SelectItem value="config_update">Config Update</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-mono">Description *</Label>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="bg-secondary/30 border-border font-mono text-sm min-h-[60px] resize-none"
                placeholder="e.g. Transferred 2.5 ETH to vault"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-mono">Actor *</Label>
              <Input
                value={actor}
                onChange={(e) => setActor(e.target.value)}
                className="bg-secondary/30 border-border font-mono text-sm"
                placeholder="0x7a2b...9f3e"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-mono">Value</Label>
              <Input
                value={value}
                onChange={(e) => setValue(e.target.value)}
                className="bg-secondary/30 border-border font-mono text-sm"
                placeholder="e.g. 2.5 ETH"
              />
            </div>

            <Button
              onClick={addRecord}
              className="w-full gradient-primary text-primary-foreground font-mono font-semibold"
            >
              <Link2 className="h-4 w-4 mr-2" /> Add to Chain
            </Button>

            <Separator />

            {/* Verification */}
            <Button
              onClick={verifyChain}
              variant="outline"
              className="w-full font-mono text-sm"
              disabled={chain.length === 0}
            >
              <ShieldCheck className="h-4 w-4 mr-2" /> Verify Chain Integrity
            </Button>

            {verificationResult && (
              <div
                className={`rounded-md border p-3 ${
                  verificationResult.valid
                    ? "border-success/30 bg-success/5"
                    : "border-destructive/30 bg-destructive/5"
                }`}
              >
                <div className="flex items-center gap-2">
                  {verificationResult.valid ? (
                    <CheckCircle className="h-4 w-4 text-success" />
                  ) : (
                    <XCircle className="h-4 w-4 text-destructive" />
                  )}
                  <span className="text-sm font-semibold">
                    {verificationResult.valid ? "Chain Valid" : "Tampering Detected!"}
                  </span>
                </div>
                <p className="text-xs font-mono text-muted-foreground mt-1">
                  Checked {verificationResult.checkedBlocks} blocks
                  {verificationResult.brokenAt !== undefined && (
                    <> — broken at block #{verificationResult.brokenAt}</>
                  )}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Chain Visualization */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Hash className="h-4 w-4" /> Hash Chain — {chain.length} Blocks
            </h2>
            {chain.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setChain([]);
                  setVerificationResult(null);
                }}
                className="text-xs font-mono text-muted-foreground"
              >
                <RefreshCw className="h-3 w-3 mr-1" /> Reset
              </Button>
            )}
          </div>

          {chain.length === 0 && (
            <Card className="border-border bg-card border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                <Link2 className="h-12 w-12 mb-3 opacity-20" />
                <p className="font-mono text-sm">No records yet — add one to start the chain</p>
              </CardContent>
            </Card>
          )}

          {chain.map((block, i) => (
            <div key={block.index} className="relative">
              {/* Chain link connector */}
              {i > 0 && (
                <div className="flex items-center justify-center py-1">
                  <div className="flex flex-col items-center gap-0.5">
                    <div className="h-4 w-px bg-primary/30" />
                    <Link2 className="h-3 w-3 text-primary/40" />
                    <div className="h-4 w-px bg-primary/30" />
                  </div>
                </div>
              )}

              <Card
                className={`border bg-card overflow-hidden ${
                  !block.valid
                    ? "border-destructive/50 glow-danger"
                    : verificationResult?.brokenAt === i
                    ? "border-destructive/50 glow-danger"
                    : "border-border"
                }`}
              >
                <CardContent className="p-0">
                  <div className="flex flex-col">
                    {/* Block header */}
                    <div className="flex items-center justify-between px-4 py-2.5 bg-secondary/20 border-b border-border">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs">
                          Block #{block.index}
                        </Badge>
                        <Badge
                          variant="secondary"
                          className="font-mono text-[10px] bg-accent/10 text-accent"
                        >
                          {block.data.type}
                        </Badge>
                        {!block.valid && (
                          <Badge className="bg-destructive text-destructive-foreground text-[10px]">
                            <AlertTriangle className="h-3 w-3 mr-1" /> TAMPERED
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono text-muted-foreground">
                          {new Date(block.timestamp).toLocaleTimeString()}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                          onClick={() => simulateTamper(block.index)}
                          title="Simulate tampering"
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    {/* Block body */}
                    <div className="p-4 space-y-3">
                      {/* Data */}
                      <div>
                        <p className="text-sm">{block.data.description}</p>
                        <div className="flex gap-4 mt-1 text-[11px] font-mono text-muted-foreground">
                          <span>
                            <span className="text-foreground/50">actor:</span> {block.data.actor}
                          </span>
                          {block.data.value && (
                            <span>
                              <span className="text-foreground/50">value:</span> {block.data.value}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Hashes */}
                      <div className="space-y-1.5 bg-secondary/20 rounded-md p-3">
                        <div className="flex items-center gap-2 text-[11px] font-mono">
                          <span className="text-muted-foreground w-16 shrink-0">hash:</span>
                          <span className="text-primary truncate">{block.hash}</span>
                        </div>
                        <div className="flex items-center gap-2 text-[11px] font-mono">
                          <span className="text-muted-foreground w-16 shrink-0">prev:</span>
                          <span className="text-foreground/60 truncate">{block.previousHash}</span>
                        </div>
                        <div className="flex items-center gap-2 text-[11px] font-mono">
                          <span className="text-muted-foreground w-16 shrink-0">nonce:</span>
                          <span className="text-foreground/60">{block.nonce}</span>
                        </div>
                        <div className="flex items-center gap-2 text-[11px] font-mono">
                          <span className="text-muted-foreground w-16 shrink-0">tx:</span>
                          <span className="text-accent truncate">{block.contractTx}</span>
                        </div>
                      </div>
                    </div>
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

export default TamperProofRecords;
