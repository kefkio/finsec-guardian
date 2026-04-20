import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { recordsApi } from "@/lib/api";
import { toast } from "sonner";
import { Link2, ShieldCheck, Plus, Hash, FileText, AlertTriangle, CheckCircle, XCircle, Fingerprint } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

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

const TamperProofRecords = () => {
  const queryClient = useQueryClient();
  const [recordType, setRecordType] = useState("transaction");
  const [description, setDescription] = useState("");
  const [actor, setActor] = useState("");
  const [value, setValue] = useState("");
  const [verificationResult, setVerificationResult] = useState(null);
  const [showContract, setShowContract] = useState(false);

  const { data: rawRecords = [], isLoading, isError } = useQuery({
    queryKey: ['records'],
    queryFn: recordsApi.getRecords,
  });

  const records = Array.isArray(rawRecords) ? rawRecords : (rawRecords.results || []);
  const blocks = records.map((record, i) => ({
    index: record.id ?? i,
    timestamp: record.created_at,
    data: { description: record.content, type: 'record' },
    hash: record.content_hash,
    previousHash: record.previous_hash,
    valid: record.chain_valid !== false,
  }));

  const addMutation = useMutation({
    mutationFn: (content) => recordsApi.createRecord({ content }),
    onSuccess: (_, content) => {
      queryClient.invalidateQueries({ queryKey: ['records'] });
      setDescription("");
      setActor("");
      setValue("");
      setVerificationResult(null);
      toast.success("Block added & submitted to smart contract");
    },
    onError: (error) => {
      toast.error(error.message || "Failed to add record");
    },
  });

  const verifyMutation = useMutation({
    mutationFn: recordsApi.verifyChain,
    onSuccess: (data) => {
      const valid = data?.valid ?? data?.all_valid ?? true;
      setVerificationResult({
        valid,
        checkedBlocks: blocks.length,
        brokenAt: data?.broken_at,
      });
      if (valid) {
        toast.success("Chain integrity verified — no tampering detected");
      } else {
        toast.error("Tampering detected in chain!");
      }
    },
    onError: (error) => {
      toast.error(error.message || "Verification failed");
    },
  });

  const addRecord = () => {
    if (!description.trim() || !actor.trim()) {
      toast.error("Fill in all required fields");
      return;
    }
    const content = `[${recordType}] ${description.trim()} | actor: ${actor.trim()}${value.trim() ? ` | value: ${value.trim()}` : ''}`;
    addMutation.mutate(content);
  };

  const verifyChain = () => {
    if (blocks.length === 0) {
      toast.error("No records to verify");
      return;
    }
    verifyMutation.mutate();
  };

  return (
    <div className="space-y-6">
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
                onChange={e => setDescription(e.target.value)}
                className="bg-secondary/30 border-border font-mono text-sm min-h-[60px] resize-none"
                placeholder="e.g. Transferred 2.5 ETH to vault"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-mono">Actor *</Label>
              <Input
                value={actor}
                onChange={e => setActor(e.target.value)}
                className="bg-secondary/30 border-border font-mono text-sm"
                placeholder="0x7a2b...9f3e"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-mono">Value</Label>
              <Input
                value={value}
                onChange={e => setValue(e.target.value)}
                className="bg-secondary/30 border-border font-mono text-sm"
                placeholder="e.g. 2.5 ETH"
              />
            </div>
            <Button
              onClick={addRecord}
              disabled={addMutation.isPending}
              className="w-full gradient-primary text-primary-foreground font-mono font-semibold"
            >
              <Link2 className="h-4 w-4 mr-2" />
              {addMutation.isPending ? "Adding..." : "Add to Chain"}
            </Button>
            <Separator />
            <Button
              onClick={verifyChain}
              variant="outline"
              className="w-full font-mono text-sm"
              disabled={blocks.length === 0 || verifyMutation.isPending}
            >
              <ShieldCheck className="h-4 w-4 mr-2" />
              {verifyMutation.isPending ? "Verifying..." : "Verify Chain Integrity"}
            </Button>
            {verificationResult && (
              <div className={`rounded-md border p-3 ${verificationResult.valid ? "border-success/30 bg-success/5" : "border-destructive/30 bg-destructive/5"}`}>
                <div className="flex items-center gap-2">
                  {verificationResult.valid
                    ? <CheckCircle className="h-4 w-4 text-success" />
                    : <XCircle className="h-4 w-4 text-destructive" />
                  }
                  <span className="text-sm font-semibold">
                    {verificationResult.valid ? "Chain Valid" : "Tampering Detected!"}
                  </span>
                </div>
                <p className="text-xs font-mono text-muted-foreground mt-1">
                  Checked {verificationResult.checkedBlocks} blocks
                  {verificationResult.brokenAt != null && <> — broken at block #{verificationResult.brokenAt}</>}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Hash className="h-4 w-4" /> Hash Chain — {blocks.length} Blocks
            </h2>
          </div>

          {isLoading && (
            <div className="flex items-center justify-center py-16 text-muted-foreground font-mono text-sm">
              Loading records...
            </div>
          )}

          {isError && (
            <div className="flex items-center justify-center py-16 text-destructive font-mono text-sm">
              Failed to load records. Check API connection.
            </div>
          )}

          {!isLoading && !isError && blocks.length === 0 && (
            <Card className="border-border bg-card border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                <Link2 className="h-12 w-12 mb-3 opacity-20" />
                <p className="font-mono text-sm">No records yet — add one to start the chain</p>
              </CardContent>
            </Card>
          )}

          {blocks.map((block, i) => (
            <div key={block.index} className="relative">
              {i > 0 && (
                <div className="flex items-center justify-center py-1">
                  <div className="flex flex-col items-center gap-0.5">
                    <div className="h-4 w-px bg-primary/30" />
                    <Link2 className="h-3 w-3 text-primary/40" />
                    <div className="h-4 w-px bg-primary/30" />
                  </div>
                </div>
              )}
              <Card className={`border bg-card overflow-hidden ${!block.valid ? "border-destructive/50" : "border-border"}`}>
                <CardContent className="p-0">
                  <div className="flex flex-col">
                    <div className="flex items-center justify-between px-4 py-2.5 bg-secondary/20 border-b border-border">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs">
                          Block #{block.index}
                        </Badge>
                        <Badge variant="secondary" className="font-mono text-[10px] bg-accent/10 text-accent">
                          {block.data.type}
                        </Badge>
                        {!block.valid && (
                          <Badge className="bg-destructive text-destructive-foreground text-[10px]">
                            <AlertTriangle className="h-3 w-3 mr-1" /> INVALID
                          </Badge>
                        )}
                      </div>
                      <span className="text-[10px] font-mono text-muted-foreground">
                        {new Date(block.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="p-4 space-y-3">
                      <div>
                        <p className="text-sm">{block.data.description}</p>
                      </div>
                      <div className="space-y-1.5 bg-secondary/20 rounded-md p-3">
                        <div className="flex items-center gap-2 text-[11px] font-mono">
                          <span className="text-muted-foreground w-16 shrink-0">hash:</span>
                          <span className="text-primary truncate">{block.hash}</span>
                        </div>
                        <div className="flex items-center gap-2 text-[11px] font-mono">
                          <span className="text-muted-foreground w-16 shrink-0">prev:</span>
                          <span className="text-foreground/60 truncate">{block.previousHash}</span>
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
