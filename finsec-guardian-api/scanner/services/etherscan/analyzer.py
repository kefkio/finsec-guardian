"""Etherscan behavioral analyzer — derives security insights from on-chain data.

This is a *separate analytical layer* from the static/symbolic/fuzz analyzers.
Those operate on source code; this one operates on live blockchain activity
(transactions, token flows, event logs) fetched via the Etherscan API.

The insights produced here enrich vulnerability findings with real-world
context.  For example, a reentrancy vulnerability detected by Slither
becomes far more critical when the contract has processed thousands of
high-value transactions with abnormal repeated calls to ``withdraw()``.

Design:
  - Input: ``ContractData`` from the fetcher layer.
  - Output: ``OnChainInsights`` dataclass consumed by the normalizer and
    risk scorer.
  - Never modifies or depends on analyzer results — enrichment is handled
    downstream by the orchestrator.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .fetcher import ContractData

logger = logging.getLogger(__name__)

# Wei → Ether conversion factor.
_WEI_PER_ETH = 10**18

# Threshold above which a single transaction is "high-value".
_HIGH_VALUE_THRESHOLD_ETH = 10.0

# Number of calls from the same sender within a short window considered
# "repeated" (potential bot / exploit pattern).
_REPEATED_CALL_THRESHOLD = 10


@dataclass
class OnChainInsights:
    """Aggregated behavioral insights for a contract address."""

    address: str = ""

    # Transaction statistics
    tx_count: int = 0
    unique_callers: int = 0
    unique_receivers: int = 0
    failed_tx_count: int = 0
    failure_rate: float = 0.0  # 0.0 – 1.0

    # Value flow
    total_value_eth: float = 0.0
    high_value_tx_count: int = 0
    high_value_flows: list[dict] = field(default_factory=list)  # top N txs

    # Behavioral patterns
    repeated_callers: dict[str, int] = field(default_factory=dict)  # addr → count
    suspicious_patterns: list[str] = field(default_factory=list)
    top_methods: list[tuple[str, int]] = field(default_factory=list)  # (methodId, count)

    # Token activity
    token_transfer_count: int = 0
    unique_tokens: int = 0

    # Event log stats
    event_log_count: int = 0

    # Contract age
    first_tx_timestamp: int | None = None
    last_tx_timestamp: int | None = None
    contract_age_days: int = 0

    # Warnings from fetch layer
    warnings: list[str] = field(default_factory=list)


class EtherscanAnalyzer:
    """Derives ``OnChainInsights`` from raw ``ContractData``.

    This class does *not* inherit from the source-code ``AnalyzerBase``.
    It is a distinct analytical layer that runs in parallel to the
    static/symbolic analyzers and feeds into the risk scorer separately.
    """

    def analyze(self, contract_data: ContractData) -> OnChainInsights:
        """Run all on-chain analyses and return aggregated insights."""
        insights = OnChainInsights(
            address=contract_data.address,
            warnings=list(contract_data.warnings),
        )

        txs = contract_data.transactions
        if txs:
            self._analyze_transactions(txs, insights)
            self._detect_suspicious_patterns(txs, insights)

        if contract_data.token_transfers:
            self._analyze_token_transfers(contract_data.token_transfers, insights)

        insights.event_log_count = len(contract_data.event_logs)

        return insights

    # ------------------------------------------------------------------
    # Transaction analysis
    # ------------------------------------------------------------------

    def _analyze_transactions(
        self, txs: list[dict], insights: OnChainInsights,
    ) -> None:
        insights.tx_count = len(txs)

        senders: set[str] = set()
        receivers: set[str] = set()
        sender_counts: Counter[str] = Counter()
        method_counts: Counter[str] = Counter()
        failed = 0
        total_value_wei = 0
        high_value_txs: list[dict] = []

        for tx in txs:
            sender = (tx.get("from") or "").lower()
            receiver = (tx.get("to") or "").lower()
            senders.add(sender)
            receivers.add(receiver)
            sender_counts[sender] += 1

            # Method signature (first 10 chars of input, e.g. 0xa9059cbb)
            method_id = (tx.get("input") or "")[:10]
            if method_id and method_id != "0x":
                method_counts[method_id] += 1

            # Transaction success/failure
            is_error = tx.get("isError", "0")
            if str(is_error) == "1":
                failed += 1

            # Value
            try:
                value_wei = int(tx.get("value", 0))
            except (ValueError, TypeError):
                value_wei = 0
            total_value_wei += value_wei
            value_eth = value_wei / _WEI_PER_ETH

            if value_eth >= _HIGH_VALUE_THRESHOLD_ETH:
                high_value_txs.append({
                    "hash": tx.get("hash", ""),
                    "from": sender,
                    "to": receiver,
                    "value_eth": round(value_eth, 4),
                    "timestamp": tx.get("timeStamp", ""),
                })

            # Timestamps
            try:
                ts = int(tx.get("timeStamp", 0))
            except (ValueError, TypeError):
                ts = 0

            if ts:
                if insights.first_tx_timestamp is None or ts < insights.first_tx_timestamp:
                    insights.first_tx_timestamp = ts
                if insights.last_tx_timestamp is None or ts > insights.last_tx_timestamp:
                    insights.last_tx_timestamp = ts

        insights.unique_callers = len(senders)
        insights.unique_receivers = len(receivers)
        insights.failed_tx_count = failed
        insights.failure_rate = round(failed / len(txs), 4) if txs else 0.0
        insights.total_value_eth = round(total_value_wei / _WEI_PER_ETH, 4)
        insights.high_value_tx_count = len(high_value_txs)
        # Keep only top 20 high-value transactions.
        insights.high_value_flows = sorted(
            high_value_txs, key=lambda t: t["value_eth"], reverse=True,
        )[:20]

        # Repeated callers — addresses calling > threshold times.
        insights.repeated_callers = {
            addr: count
            for addr, count in sender_counts.most_common(50)
            if count >= _REPEATED_CALL_THRESHOLD
        }

        # Top method signatures
        insights.top_methods = method_counts.most_common(10)

        # Contract age
        if insights.first_tx_timestamp:
            try:
                first_dt = datetime.fromtimestamp(
                    insights.first_tx_timestamp, tz=timezone.utc,
                )
                now = datetime.now(tz=timezone.utc)
                insights.contract_age_days = max(0, (now - first_dt).days)
            except (OSError, ValueError):
                pass

    # ------------------------------------------------------------------
    # Suspicious pattern detection
    # ------------------------------------------------------------------

    def _detect_suspicious_patterns(
        self, txs: list[dict], insights: OnChainInsights,
    ) -> None:
        """Flag behavioural anomalies in the transaction history."""

        # 1. High failure rate
        if insights.failure_rate > 0.3 and insights.tx_count > 50:
            insights.suspicious_patterns.append(
                f"High failure rate ({insights.failure_rate:.0%}) across "
                f"{insights.tx_count} transactions — possible exploit attempts."
            )

        # 2. Repeated callers (potential bot / flashloan attack pattern)
        for addr, count in insights.repeated_callers.items():
            if count >= 50:
                insights.suspicious_patterns.append(
                    f"Address {addr[:10]}…{addr[-4:]} made {count} calls — "
                    "possible automated exploit or bot activity."
                )

        # 3. Abnormal withdraw-like calls
        # Method IDs for common withdraw patterns.
        _WITHDRAW_SIGS = {"0x3ccfd60b", "0x2e1a7d4d", "0x51cff8d9"}
        withdraw_count = sum(
            1 for tx in txs
            if (tx.get("input") or "")[:10] in _WITHDRAW_SIGS
        )
        if withdraw_count > 20:
            insights.suspicious_patterns.append(
                f"Abnormal withdraw activity: {withdraw_count} withdraw-like "
                "calls detected — cross-reference with reentrancy findings."
            )

        # 4. Large single-value outflows
        for flow in insights.high_value_flows[:5]:
            if flow["value_eth"] >= 100:
                insights.suspicious_patterns.append(
                    f"Large outflow of {flow['value_eth']} ETH in tx "
                    f"{flow['hash'][:12]}… — verify authorization controls."
                )

        # 5. Contract with many unknown callers (exposure surface)
        if insights.unique_callers > 500:
            insights.suspicious_patterns.append(
                f"High exposure: {insights.unique_callers} unique callers "
                "interact with this contract."
            )

    # ------------------------------------------------------------------
    # Token transfer analysis
    # ------------------------------------------------------------------

    def _analyze_token_transfers(
        self, transfers: list[dict], insights: OnChainInsights,
    ) -> None:
        insights.token_transfer_count = len(transfers)
        token_addresses: set[str] = set()
        for t in transfers:
            addr = (t.get("contractAddress") or "").lower()
            if addr:
                token_addresses.add(addr)
        insights.unique_tokens = len(token_addresses)
