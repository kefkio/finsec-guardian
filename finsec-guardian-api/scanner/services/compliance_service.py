"""Layer 5 — Standards Compliance Analysis Service.

Checks Solidity contracts against ERC token standards:
    - ERC-20:   Transfer, Approve, Allowance interface + events
    - ERC-721:  ownerOf, safeTransferFrom, ERC165 supportsInterface
    - ERC-1155: balanceOf, balanceOfBatch, safeBatchTransferFrom
    - Interface validation: missing functions, wrong signatures, missing events
"""

import logging
import re

logger = logging.getLogger(__name__)


class ComplianceService:
    """Layer 5: ERC standards compliance and interface validation."""

    # Each standard defines required function signatures and events.
    # Format: { "standard": { "functions": [...], "events": [...] } }
    _ERC_STANDARDS: dict[str, dict] = {
        "ERC20": {
            "functions": [
                r"function\s+totalSupply\s*\(",
                r"function\s+balanceOf\s*\(",
                r"function\s+transfer\s*\(",
                r"function\s+transferFrom\s*\(",
                r"function\s+approve\s*\(",
                r"function\s+allowance\s*\(",
            ],
            "events": [
                r"event\s+Transfer\s*\(",
                r"event\s+Approval\s*\(",
            ],
        },
        "ERC721": {
            "functions": [
                r"function\s+balanceOf\s*\(",
                r"function\s+ownerOf\s*\(",
                r"function\s+safeTransferFrom\s*\(",
                r"function\s+transferFrom\s*\(",
                r"function\s+approve\s*\(",
                r"function\s+setApprovalForAll\s*\(",
                r"function\s+getApproved\s*\(",
                r"function\s+isApprovedForAll\s*\(",
            ],
            "events": [
                r"event\s+Transfer\s*\(",
                r"event\s+Approval\s*\(",
                r"event\s+ApprovalForAll\s*\(",
            ],
        },
        "ERC1155": {
            "functions": [
                r"function\s+balanceOf\s*\(",
                r"function\s+balanceOfBatch\s*\(",
                r"function\s+setApprovalForAll\s*\(",
                r"function\s+isApprovedForAll\s*\(",
                r"function\s+safeTransferFrom\s*\(",
                r"function\s+safeBatchTransferFrom\s*\(",
            ],
            "events": [
                r"event\s+TransferSingle\s*\(",
                r"event\s+TransferBatch\s*\(",
                r"event\s+ApprovalForAll\s*\(",
                r"event\s+URI\s*\(",
            ],
        },
    }

    def run_analysis(self, source_code: str, **_kwargs) -> dict:
        """
        Detect which ERC standard(s) the contract targets and check compliance.

        Returns:
            {
                "success": bool,
                "findings": list[dict],
                "error": str | None,
            }
        """
        findings: list[dict] = []

        detected_standards = self._detect_standards(source_code)

        for standard in detected_standards:
            spec = self._ERC_STANDARDS.get(standard)
            if not spec:
                continue
            findings.extend(self._check_standard(source_code, standard, spec))

        return {"success": True, "findings": findings, "error": None}

    # -----------------------------------------------------------------
    # Detection & checks — TODO: implement
    # -----------------------------------------------------------------

    def _detect_standards(self, source: str) -> list[str]:
        """Infer which ERC standard(s) the contract intends to implement."""
        # TODO: Implement heuristic detection (inheritance, import names,
        #       interface declarations, comment hints).
        raise NotImplementedError("Layer 5: _detect_standards")

    def _check_standard(
        self, source: str, standard: str, spec: dict
    ) -> list[dict]:
        """Validate source against a specific ERC standard's requirements."""
        # TODO: Check each required function/event signature against source.
        #       Generate a finding for each missing or malformed member.
        raise NotImplementedError("Layer 5: _check_standard")

    # -----------------------------------------------------------------
    # Finding builder (consistent shape across all layers)
    # -----------------------------------------------------------------

    @staticmethod
    def _make(
        *,
        title: str,
        severity: str,
        description: str,
        recommendation: str = "",
        swc_id: str = "",
        line_number: int | None = None,
        confidence: int = 75,
    ) -> dict:
        return {
            "swc_id": swc_id,
            "title": title,
            "severity": severity,
            "description": description,
            "recommendation": recommendation,
            "line_number": line_number,
            "confidence": confidence,
            "tags": ["compliance", "erc-check"],
            "metadata": {"tool": "compliance-engine", "layer": 5},
        }
