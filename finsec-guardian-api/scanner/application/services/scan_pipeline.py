from __future__ import annotations

import asyncio
from collections.abc import Sequence

from scanner.domain.entities.scan import Scan
from scanner.domain.entities.smart_contract import SmartContract
from scanner.domain.ports.analyzer import AnalyzerPort
from scanner.domain.ports.scan_repository import ScanRepository
from scanner.domain.value_objects.analysis_request import AnalysisRequest


class ScanPipeline:
    """
    Application service coordinating a V2 security scan.

    The pipeline is responsible for:
        - creating the Scan aggregate
        - progressing the scan lifecycle
        - executing the configured analyzers
        - merging analyzer findings into the aggregate
        - persisting lifecycle transitions

    Analyzer execution is asynchronous.

    Repository operations are synchronous, so they are executed through
    asyncio.to_thread() to keep synchronous Django ORM access outside the
    event-loop thread.
    """

    def __init__(
        self,
        analyzers: Sequence[AnalyzerPort],
        repository: ScanRepository,
    ) -> None:
        if not analyzers:
            raise ValueError(
                "At least one analyzer must be configured."
            )

        for analyzer in analyzers:
            if not isinstance(analyzer, AnalyzerPort):
                raise TypeError(
                    "All analyzers must implement AnalyzerPort."
                )

        self._analyzers = tuple(analyzers)
        self._repository = repository

    async def execute(
        self,
        request: AnalysisRequest,
    ) -> Scan:
        """
        Execute the complete scan lifecycle.

        Lifecycle:

            PENDING
              ↓
            QUEUED
              ↓
            RUNNING
              ↓
        analyzer 1
              ↓
        analyzer 2
              ↓
            findings merged
              ↓
          COMPLETED

        If any analyzer raises an exception, the aggregate transitions
        to FAILED and the exception is re-raised.
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

            for analyzer in self._analyzers:
                findings = await analyzer.analyze(
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

    @property
    def analyzers(self) -> tuple[AnalyzerPort, ...]:
        """
        Return the configured analyzers as an immutable tuple.
        """
        return self._analyzers

    @staticmethod
    def _validate_request(
        request: AnalysisRequest,
    ) -> None:
        if not isinstance(request, AnalysisRequest):
            raise TypeError(
                "request must be an AnalysisRequest."
            )