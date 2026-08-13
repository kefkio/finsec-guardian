from __future__ import annotations

import asyncio

from scanner.domain.entities.scan import Scan
from scanner.domain.entities.smart_contract import SmartContract
from scanner.domain.ports.analyzer import AnalyzerPort
from scanner.domain.ports.scan_repository import ScanRepository
from scanner.domain.value_objects.analysis_request import AnalysisRequest


class ScanPipeline:
    """
    Application service coordinating one V2 security scan.

    Analyzer execution is asynchronous. Repository operations are
    synchronous and therefore execute in worker threads so Django ORM
    access never occurs directly inside the async event loop.
    """

    def __init__(
        self,
        analyzer: AnalyzerPort,
        repository: ScanRepository,
    ) -> None:
        self._analyzer = analyzer
        self._repository = repository

    async def execute(
        self,
        request: AnalysisRequest,
    ) -> Scan:
        """
        Execute a scan from creation through persistence.
        """
        self._validate_request(request)

        scan = Scan(
            smart_contract=SmartContract(
                filename=request.source_filename,
                contract_name=request.contract_name,
                source_code=request.source_code,
                compiler_version=request.solidity_version,
            )
        )

        scan.queue()

        await asyncio.to_thread(
            self._repository.save,
            scan,
        )

        try:
            scan.start()

            await asyncio.to_thread(
                self._repository.update,
                scan,
            )

            findings = await self._analyzer.analyze(
                request,
            )

            scan.merge_findings(
                list(findings),
            )

            scan.complete()

            await asyncio.to_thread(
                self._repository.update,
                scan,
            )

            return scan

        except Exception:
            scan.fail()

            await asyncio.to_thread(
                self._repository.update,
                scan,
            )

            raise

    @staticmethod
    def _validate_request(
        request: AnalysisRequest,
    ) -> None:
        if not isinstance(request, AnalysisRequest):
            raise TypeError(
                "request must be an AnalysisRequest."
            )