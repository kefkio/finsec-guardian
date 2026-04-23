"""Orchestrator — coordinates analyzers, normalizer, and persistence.

Pipeline: Analyzers → Orchestrator → Normalizer → Persistence → API

Layers:
  Layer 1 — Source-code analyzers (Slither, Mythril, Echidna, Heuristic)
  Layer 2 — On-chain intelligence (Etherscan: fetcher → analyzer → reputation)
  Layer 3 — Normalisation (merge findings + on-chain data)
  Layer 4 — Risk scoring (findings + on-chain reputation adjustment)
  Layer 5 — Persistence
"""

import logging
import re

from django.conf import settings

from .analyzers.slither import SlitherAnalyzer, SlitherError
from .analyzers.mythril import MythrilAnalyzer, MythrilError
from .analyzers.echidna import EchidnaAnalyzer, EchidnaError
from .analyzers.heuristic import HeuristicAnalyzer
from .normalizer import FindingNormalizer
from .persistence import ScanPersistence
from .risk_scorer import RiskScorer

logger = logging.getLogger(__name__)

# Ethereum address pattern — used to detect contract addresses in input.
_ETH_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


class ScanOrchestrator:
    """Single entry-point for running a full scan pipeline.

    Coordinates:
        1. Slither static analysis
        2. Mythril symbolic execution (optional, graceful degradation)
        3. Echidna property-based fuzzing (optional, graceful degradation)
        4. Heuristic regex analysis
        5. Etherscan on-chain intelligence (optional, when contract_address provided)
        6. Normalisation of raw outputs + on-chain enrichment
        7. Risk scoring (findings + on-chain reputation adjustment)
        8. Persistence of findings (for job-based scans)
    """

    def __init__(self):
        self.slither = SlitherAnalyzer()
        self.mythril = MythrilAnalyzer()
        self.echidna = EchidnaAnalyzer()
        self.heuristic = HeuristicAnalyzer()
        self.normalizer = FindingNormalizer()
        self.persistence = ScanPersistence()
        self.risk_scorer = RiskScorer()

    # ------------------------------------------------------------------
    # Etherscan layer (lazy-loaded — only instantiated when needed)
    # ------------------------------------------------------------------

    def _get_etherscan_components(self):
        """Import and instantiate Etherscan layer components on demand.

        Returns (fetcher, analyzer, reputation_scorer) or None if the
        Etherscan API key is not configured.
        """
        api_key = getattr(settings, "ETHERSCAN_API_KEY", "")
        if not api_key:
            return None

        from .etherscan.client import EtherscanClient, EtherscanError  # noqa: PLC0415
        from .etherscan.fetcher import EtherscanFetcher  # noqa: PLC0415
        from .etherscan.analyzer import EtherscanAnalyzer  # noqa: PLC0415
        from .etherscan.reputation import ReputationScorer  # noqa: PLC0415

        try:
            client = EtherscanClient()
            return EtherscanFetcher(client), EtherscanAnalyzer(), ReputationScorer()
        except EtherscanError as exc:
            logger.warning("Etherscan layer disabled: %s", exc)
            return None

    def _run_etherscan_layer(self, contract_address: str) -> dict | None:
        """Run the full Etherscan pipeline for a contract address.

        Returns the normalised ``onchain_data`` dict, or None on failure.
        """
        components = self._get_etherscan_components()
        if not components:
            return None

        fetcher, analyzer, reputation_scorer = components

        try:
            contract_data = fetcher.fetch(contract_address)
            insights = analyzer.analyze(contract_data)
            reputation = reputation_scorer.score(insights)
            onchain_data = self.normalizer.normalize_onchain(insights, reputation)
            return onchain_data
        except Exception as exc:  # noqa: BLE001
            logger.warning("Etherscan layer failed for %s: %s", contract_address, exc)
            return None

    # ------------------------------------------------------------------
    # Public: ad-hoc scan (no database)
    # ------------------------------------------------------------------

    def run_scan(
        self,
        source_code: str,
        contract_name: str | None = None,
        mythril_timeout: int = 60,
        echidna_timeout: int | None = None,
        contract_address: str | None = None,
    ) -> dict:
        """Run Slither + Mythril + Echidna + Heuristic + (Etherscan) and return merged findings.

        Parameters
        ----------
        source_code:
            Solidity source code to analyse.
        contract_name:
            Optional contract name hint.
        mythril_timeout:
            Maximum seconds for Mythril analysis.
        echidna_timeout:
            Maximum seconds for Echidna fuzzing.
        contract_address:
            Optional ``0x``-prefixed Ethereum address.  When provided, the
            Etherscan on-chain intelligence layer runs in parallel with the
            source-code analyzers to enrich findings with real-world data.

        Returns::

            {
                "success": bool,
                "findings": list[dict],
                "slither_findings": list,
                "mythril_findings": list,
                "echidna_findings": list,
                "heuristic_findings": list,
                "mythril_available": bool,
                "echidna_available": bool,
                "raw_output": dict,
                "error": str | None,
                "stderr": str,
                "risk_assessment": dict,
                "onchain_data": dict | None,
            }
        """
        # --- Slither -------------------------------------------------------
        slither_result = self.slither.analyze(source_code, contract_name)
        slither_findings = self.normalizer.normalize(slither_result)
        self.normalizer.tag_findings(slither_findings, "slither")

        # --- Mythril (optional) --------------------------------------------
        mythril_findings: list[dict] = []
        mythril_available = True
        mythril_error: str | None = None

        try:
            mythril_result = self.mythril.analyze(
                source_code, contract_name, timeout=mythril_timeout,
            )
            mythril_findings = self.normalizer.normalize(mythril_result)
            self.normalizer.tag_findings(mythril_findings, "mythril")
        except MythrilError as exc:
            mythril_available = False
            mythril_error = str(exc)
            logger.warning("Mythril unavailable: %s", exc)
        except Exception as exc:  # noqa: BLE001
            mythril_error = str(exc)
            logger.warning("Mythril analysis failed: %s", exc)

        # --- Echidna (optional) --------------------------------------------
        echidna_findings: list[dict] = []
        echidna_available = True
        echidna_error: str | None = None

        try:
            echidna_result = self.echidna.analyze(
                source_code, contract_name, timeout=echidna_timeout,
            )
            echidna_findings = self.normalizer.normalize(echidna_result)
            self.normalizer.tag_findings(echidna_findings, "echidna")
        except EchidnaError as exc:
            echidna_available = False
            echidna_error = str(exc)
            logger.warning("Echidna unavailable: %s", exc)
        except Exception as exc:  # noqa: BLE001
            echidna_error = str(exc)
            logger.warning("Echidna analysis failed: %s", exc)

        all_findings = slither_findings + mythril_findings + echidna_findings

        # --- Heuristic (always runs — lightweight regex analysis) ----------
        heuristic_result = self.heuristic.analyze(source_code, contract_name)
        heuristic_findings = self.normalizer.normalize(heuristic_result)
        self.normalizer.tag_findings(heuristic_findings, "heuristic")
        all_findings += heuristic_findings

        # --- Etherscan on-chain layer (separate from analyzers) -----------
        onchain_data: dict | None = None
        etherscan_available = False

        if contract_address and _ETH_ADDR_RE.match(contract_address):
            onchain_data = self._run_etherscan_layer(contract_address)
            etherscan_available = onchain_data is not None

            # Enrich static findings with on-chain context.
            if onchain_data:
                from .etherscan.analyzer import OnChainInsights  # noqa: PLC0415
                # We re-run the analyzer inline to get the insights object
                # for enrichment (the normalized dict doesn't carry it).
                self.normalizer.enrich_findings_with_onchain(
                    all_findings,
                    self._build_insights_from_onchain_data(onchain_data),
                )

        risk_assessment = self.risk_scorer.compute(all_findings, onchain_data=onchain_data)

        return {
            "success": slither_result.success,
            "findings": all_findings,
            "slither_findings": slither_findings,
            "mythril_findings": mythril_findings,
            "echidna_findings": echidna_findings,
            "heuristic_findings": heuristic_findings,
            "mythril_available": mythril_available,
            "echidna_available": echidna_available,
            "etherscan_available": etherscan_available,
            "raw_output": slither_result.raw_output,
            "error": slither_result.error or mythril_error or echidna_error,
            "stderr": slither_result.stderr,
            "risk_assessment": risk_assessment,
            "onchain_data": onchain_data,
        }

    @staticmethod
    def _build_insights_from_onchain_data(onchain_data: dict):
        """Reconstruct a minimal OnChainInsights from the normalised dict.

        Only the fields needed by ``enrich_findings_with_onchain`` are set.
        """
        from .etherscan.analyzer import OnChainInsights  # noqa: PLC0415

        return OnChainInsights(
            address=onchain_data.get("address", ""),
            suspicious_patterns=onchain_data.get("suspicious_patterns", []),
            tx_count=onchain_data.get("tx_count", 0),
        )

    # ------------------------------------------------------------------
    # Public: job-based scan (with persistence)
    # ------------------------------------------------------------------

    def run_scan_job(self, job_id: int) -> None:
        """Full lifecycle analysis for a persisted ScanJob.

        1. Mark job as 'analyzing'.
        2. Run Slither.
        3. Run Mythril (optional).
        4. Run Echidna (optional).
        5. Run Heuristic.
        6. Run Etherscan on-chain layer (optional, when contract_address set).
        7. Normalise all findings + on-chain enrichment.
        8. Persist findings.
        9. Risk score (with on-chain adjustment).
        10. Update summary counts and mark 'complete' (or 'failed').
        """
        from scanner.models import ScanJob  # noqa: PLC0415

        try:
            job = ScanJob.objects.get(id=job_id)
        except ScanJob.DoesNotExist:
            logger.error("run_scan_job: ScanJob %s not found", job_id)
            return

        self.persistence.mark_analyzing(job)

        # --- Slither -------------------------------------------------------
        try:
            slither_result = self.slither.analyze(job.source_code, job.contract_name)
        except SlitherError as exc:
            logger.error("Slither failed for ScanJob %s: %s", job_id, exc)
            self.persistence.mark_failed(job, str(exc))
            return

        slither_findings = self.normalizer.normalize(slither_result)
        self.normalizer.tag_findings(slither_findings, "slither")

        self.persistence.update_progress(job, 40)

        # --- Mythril (optional) --------------------------------------------
        mythril_timeout = getattr(settings, "MYTHRIL_TIMEOUT", 60)
        mythril_findings: list[dict] = []
        mythril_available = True
        mythril_error: str | None = None

        try:
            mythril_result = self.mythril.analyze(
                job.source_code, job.contract_name, timeout=mythril_timeout,
            )
            mythril_findings = self.normalizer.normalize(mythril_result)
            self.normalizer.tag_findings(mythril_findings, "mythril")
        except MythrilError as exc:
            mythril_available = False
            mythril_error = str(exc)
            logger.warning("Mythril unavailable for ScanJob %s: %s", job_id, exc)
        except Exception as exc:  # noqa: BLE001
            mythril_error = str(exc)
            logger.warning("Mythril failed for ScanJob %s: %s", job_id, exc)

        self.persistence.update_progress(job, 60)

        # --- Echidna (optional) --------------------------------------------
        echidna_timeout = getattr(settings, "ECHIDNA_TIMEOUT", 120)
        echidna_findings: list[dict] = []
        echidna_available = True
        echidna_error: str | None = None

        try:
            echidna_result = self.echidna.analyze(
                job.source_code, job.contract_name, timeout=echidna_timeout,
            )
            echidna_findings = self.normalizer.normalize(echidna_result)
            self.normalizer.tag_findings(echidna_findings, "echidna")
        except EchidnaError as exc:
            echidna_available = False
            echidna_error = str(exc)
            logger.warning("Echidna unavailable for ScanJob %s: %s", job_id, exc)
        except Exception as exc:  # noqa: BLE001
            echidna_error = str(exc)
            logger.warning("Echidna failed for ScanJob %s: %s", job_id, exc)

        all_findings = slither_findings + mythril_findings + echidna_findings

        # --- Heuristic (always runs — lightweight regex analysis) ----------
        heuristic_result = self.heuristic.analyze(job.source_code, job.contract_name)
        heuristic_findings = self.normalizer.normalize(heuristic_result)
        self.normalizer.tag_findings(heuristic_findings, "heuristic")
        all_findings += heuristic_findings

        self.persistence.update_progress(job, 75)

        # --- Etherscan on-chain layer (separate from analyzers) -----------
        onchain_data: dict | None = None
        etherscan_available = False
        contract_address = getattr(job, "contract_address", "") or ""

        if contract_address and _ETH_ADDR_RE.match(contract_address):
            onchain_data = self._run_etherscan_layer(contract_address)
            etherscan_available = onchain_data is not None

            if onchain_data:
                self.normalizer.enrich_findings_with_onchain(
                    all_findings,
                    self._build_insights_from_onchain_data(onchain_data),
                )

        self.persistence.update_progress(job, 85)

        # --- Persist -------------------------------------------------------
        self.persistence.persist_findings(job, all_findings)

        risk_assessment = self.risk_scorer.compute(all_findings, onchain_data=onchain_data)

        self.persistence.mark_complete(job, metadata={
            "slither_stderr": slither_result.stderr[:2000],
            "mythril_available": mythril_available,
            "mythril_error": mythril_error,
            "echidna_available": echidna_available,
            "echidna_error": echidna_error,
            "etherscan_available": etherscan_available,
            "slither_finding_count": len(slither_findings),
            "mythril_finding_count": len(mythril_findings),
            "echidna_finding_count": len(echidna_findings),
            "heuristic_finding_count": len(heuristic_findings),
            "onchain_data": onchain_data,
        }, risk_assessment=risk_assessment)

        logger.info(
            "ScanJob %s complete: %d Slither + %d Mythril + %d Echidna + %d Heuristic = %d total. "
            "Etherscan: %s.",
            job_id,
            len(slither_findings),
            len(mythril_findings),
            len(echidna_findings),
            len(heuristic_findings),
            job.total_findings,
            "available" if etherscan_available else "skipped",
        )
