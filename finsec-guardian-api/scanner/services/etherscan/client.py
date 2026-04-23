"""Etherscan API client — thin wrapper around Etherscan's REST endpoints.

Handles authentication, rate-limiting (via configurable delay), and error
normalisation so callers never deal with raw HTTP responses.

Supports:
  - ``getsourcecode``  — verified source code + ABI
  - ``getabi``         — contract ABI only
  - ``txlist``         — normal transaction history
  - ``tokentx``        — ERC-20 token transfers
  - ``getlogs``        — event log retrieval

All public methods return parsed JSON dicts or raise ``EtherscanError``.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Ethereum address regex — 0x followed by exactly 40 hex chars.
_ETH_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Etherscan free tier: 5 calls/sec.  We insert a small sleep between calls.
_DEFAULT_RATE_LIMIT_DELAY = 0.22  # seconds


class EtherscanError(Exception):
    """Any Etherscan interaction failure (network, auth, rate-limit, …)."""


class EtherscanClient:
    """Low-level Etherscan REST API wrapper.

    Configuration is read from Django settings:
      - ``ETHERSCAN_API_KEY``  (required)
      - ``ETHERSCAN_BASE_URL`` (optional, defaults to mainnet)
      - ``ETHERSCAN_TIMEOUT``  (optional, default 30 s)
    """

    def __init__(self) -> None:
        self.api_key: str = getattr(settings, "ETHERSCAN_API_KEY", "")
        if not self.api_key:
            raise EtherscanError(
                "ETHERSCAN_API_KEY is not configured. "
                "Set it in config/settings.py or your .env file."
            )
        self.base_url: str = getattr(
            settings, "ETHERSCAN_BASE_URL", "https://api.etherscan.io/api"
        )
        self.timeout: int = getattr(settings, "ETHERSCAN_TIMEOUT", 30)
        self._last_request_time: float = 0.0

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_source_code(self, address: str) -> dict:
        """Fetch verified source code and compiler metadata for *address*."""
        self._validate_address(address)
        data = self._call(module="contract", action="getsourcecode", address=address)
        results = data.get("result", [])
        if not results or not isinstance(results, list):
            return {}
        return results[0]

    def get_abi(self, address: str) -> list[dict]:
        """Fetch the ABI for a verified contract at *address*.

        Returns the parsed ABI list, or an empty list when the contract
        is not verified.
        """
        import json as _json

        self._validate_address(address)
        data = self._call(module="contract", action="getabi", address=address)
        raw = data.get("result", "")
        if not raw or raw == "Contract source code not verified":
            return []
        try:
            return _json.loads(raw)
        except (ValueError, TypeError):
            return []

    def get_transactions(
        self,
        address: str,
        *,
        start_block: int = 0,
        end_block: int = 99999999,
        page: int = 1,
        offset: int = 1000,
        sort: str = "desc",
    ) -> list[dict]:
        """Return normal (external) transactions for *address*."""
        self._validate_address(address)
        data = self._call(
            module="account",
            action="txlist",
            address=address,
            startblock=start_block,
            endblock=end_block,
            page=page,
            offset=offset,
            sort=sort,
        )
        result = data.get("result", [])
        return result if isinstance(result, list) else []

    def get_token_transfers(
        self,
        address: str,
        *,
        start_block: int = 0,
        end_block: int = 99999999,
        page: int = 1,
        offset: int = 1000,
        sort: str = "desc",
    ) -> list[dict]:
        """Return ERC-20 token transfer events for *address*."""
        self._validate_address(address)
        data = self._call(
            module="account",
            action="tokentx",
            address=address,
            startblock=start_block,
            endblock=end_block,
            page=page,
            offset=offset,
            sort=sort,
        )
        result = data.get("result", [])
        return result if isinstance(result, list) else []

    def get_logs(
        self,
        address: str,
        *,
        from_block: int = 0,
        to_block: int = 99999999,
        topic0: str | None = None,
    ) -> list[dict]:
        """Return event logs emitted by *address*."""
        self._validate_address(address)
        params: dict[str, Any] = {
            "module": "logs",
            "action": "getLogs",
            "address": address,
            "fromBlock": from_block,
            "toBlock": to_block,
        }
        if topic0:
            params["topic0"] = topic0

        data = self._call(**params)
        result = data.get("result", [])
        return result if isinstance(result, list) else []

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _call(self, **params: Any) -> dict:
        """Execute a single Etherscan API request with rate-limiting."""
        self._rate_limit()
        params["apikey"] = self.api_key

        try:
            resp = requests.get(
                self.base_url, params=params, timeout=self.timeout
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise EtherscanError(f"Etherscan request failed: {exc}") from exc

        data = resp.json()
        status = data.get("status")
        message = data.get("message", "")

        # Etherscan returns status "0" with message "NOTOK" on errors.
        if status == "0" and "No transactions found" not in message:
            raise EtherscanError(
                f"Etherscan API error: {data.get('result', message)}"
            )

        return data

    def _rate_limit(self) -> None:
        """Enforce minimum delay between successive API calls."""
        elapsed = time.monotonic() - self._last_request_time
        delay = _DEFAULT_RATE_LIMIT_DELAY - elapsed
        if delay > 0:
            time.sleep(delay)
        self._last_request_time = time.monotonic()

    @staticmethod
    def _validate_address(address: str) -> None:
        if not _ETH_ADDR_RE.match(address):
            raise EtherscanError(
                f"Invalid Ethereum address: {address!r}. "
                "Expected 0x followed by 40 hex characters."
            )
