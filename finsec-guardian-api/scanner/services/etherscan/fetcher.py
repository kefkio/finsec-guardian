"""Etherscan data fetcher — aggregates raw on-chain data for a contract.

Combines source code, ABI, transactions, token transfers, and event logs
into a single ``ContractData`` bundle that downstream components consume.

This is the *data-collection* layer; interpretation happens in
``analyzer.py`` and ``reputation.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .client import EtherscanClient, EtherscanError

logger = logging.getLogger(__name__)


@dataclass
class ContractData:
    """Everything we know about a contract from Etherscan."""

    address: str = ""
    # Source metadata
    contract_name: str = ""
    source_code: str = ""
    abi: list[dict] = field(default_factory=list)
    compiler_version: str = ""
    is_verified: bool = False
    # Transaction data
    transactions: list[dict] = field(default_factory=list)
    token_transfers: list[dict] = field(default_factory=list)
    event_logs: list[dict] = field(default_factory=list)
    # Fetch errors (non-fatal)
    warnings: list[str] = field(default_factory=list)


class EtherscanFetcher:
    """High-level facade that collects all data for a contract address.

    Usage::

        fetcher = EtherscanFetcher()
        data = fetcher.fetch("0x1234…abcd")
        # data.source_code, data.transactions, etc.
    """

    def __init__(self, client: EtherscanClient | None = None) -> None:
        self.client = client or EtherscanClient()

    def fetch(self, address: str, *, tx_limit: int = 1000) -> ContractData:
        """Fetch all available data for *address*.

        Individual API calls degrade gracefully — a failure to fetch
        transactions does not prevent source-code retrieval.

        Parameters
        ----------
        address:
            ``0x``-prefixed Ethereum address.
        tx_limit:
            Maximum number of transactions to retrieve (default 1 000).
        """
        data = ContractData(address=address)

        # --- Source code / ABI -------------------------------------------
        try:
            src = self.client.get_source_code(address)
            data.source_code = src.get("SourceCode", "")
            data.contract_name = src.get("ContractName", "")
            data.compiler_version = src.get("CompilerVersion", "")
            data.is_verified = bool(data.source_code)
        except EtherscanError as exc:
            data.warnings.append(f"Source code fetch failed: {exc}")
            logger.warning("Etherscan source code fetch failed for %s: %s", address, exc)

        try:
            data.abi = self.client.get_abi(address)
        except EtherscanError as exc:
            data.warnings.append(f"ABI fetch failed: {exc}")

        # --- Transactions ------------------------------------------------
        try:
            data.transactions = self.client.get_transactions(
                address, offset=tx_limit
            )
        except EtherscanError as exc:
            data.warnings.append(f"Transaction fetch failed: {exc}")
            logger.warning("Etherscan tx fetch failed for %s: %s", address, exc)

        # --- Token transfers ---------------------------------------------
        try:
            data.token_transfers = self.client.get_token_transfers(
                address, offset=tx_limit
            )
        except EtherscanError as exc:
            data.warnings.append(f"Token transfer fetch failed: {exc}")

        # --- Event logs --------------------------------------------------
        try:
            data.event_logs = self.client.get_logs(address)
        except EtherscanError as exc:
            data.warnings.append(f"Event log fetch failed: {exc}")

        logger.info(
            "Etherscan fetch for %s: verified=%s, txs=%d, token_txs=%d, logs=%d",
            address,
            data.is_verified,
            len(data.transactions),
            len(data.token_transfers),
            len(data.event_logs),
        )
        return data
