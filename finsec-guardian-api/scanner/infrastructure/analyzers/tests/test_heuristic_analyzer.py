from __future__ import annotations

import pytest

from scanner.domain.entities.finding import Finding
from scanner.domain.enums import (
    AnalyzerType,
    Confidence,
    RiskLevel,
    Severity,
)
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.infrastructure.analyzers.heuristic_analyzer import (
    HeuristicAnalyzer,
)


def make_request(
    source_code: str,
    *,
    contract_name: str = "TestContract",
    filename: str = "TestContract.sol",
) -> AnalysisRequest:
    return AnalysisRequest(
        source_code=source_code,
        contract_name=contract_name,
        source_filename=filename,
        solidity_version="0.8.20",
    )


@pytest.fixture
def analyzer() -> HeuristicAnalyzer:
    return HeuristicAnalyzer()


class TestHeuristicAnalyzer:

    @pytest.mark.asyncio
    async def test_analyze_returns_domain_findings(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            mapping(address => uint256) balances;

            function setBalance(
                address account,
                uint256 amount
            ) external {
                balances[account] = amount;
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        assert isinstance(findings, tuple)
        assert findings
        assert all(
            isinstance(finding, Finding)
            for finding in findings
        )

    @pytest.mark.asyncio
    async def test_unguarded_setter_is_critical(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            address public owner;

            function setOwner(
                address newOwner
            ) external {
                owner = newOwner;
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        finding = next(
            finding
            for finding in findings
            if finding.title.startswith(
                "Unrestricted setter:"
            )
        )

        assert finding.severity is Severity.CRITICAL
        assert finding.risk_level is RiskLevel.CRITICAL
        assert finding.confidence is Confidence.HIGH
        assert finding.analyzer is AnalyzerType.HEURISTIC
        assert finding.swc_id == "SWC-105"

    @pytest.mark.asyncio
    async def test_unguarded_mapping_write_is_high(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            mapping(address => uint256) balances;

            function updateBalance(
                address account,
                uint256 amount
            ) external {
                balances[account] = amount;
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        finding = next(
            finding
            for finding in findings
            if finding.title.startswith(
                "Missing access control:"
            )
        )

        assert finding.severity is Severity.HIGH
        assert finding.risk_level is RiskLevel.HIGH
        assert finding.confidence is Confidence.HIGH
        assert finding.swc_id == "SWC-105"

    @pytest.mark.asyncio
    async def test_guarded_state_mutation_is_not_reported(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            mapping(address => uint256) balances;
            address public owner;

            modifier onlyOwner() {
                require(msg.sender == owner);
                _;
            }

            function updateBalance(
                address account,
                uint256 amount
            ) external onlyOwner {
                balances[account] = amount;
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        state_findings = [
            finding
            for finding in findings
            if finding.swc_id == "SWC-105"
            and (
                "access control" in finding.title.lower()
                or "setter" in finding.title.lower()
            )
        ]

        assert state_findings == []

    @pytest.mark.asyncio
    async def test_missing_address_validation_is_reported(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            mapping(address => uint256) balances;

            function updateUser(
                address account
            ) external {
                balances[account] = 1;
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        finding = next(
            finding
            for finding in findings
            if finding.title.startswith(
                "Missing input validation"
            )
        )

        assert finding.severity is Severity.MEDIUM
        assert finding.risk_level is RiskLevel.MEDIUM
        assert finding.confidence is Confidence.MEDIUM
        assert finding.swc_id is None

    @pytest.mark.asyncio
    async def test_validated_address_is_not_reported(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            mapping(address => uint256) balances;

            function updateUser(
                address account
            ) external {
                require(account != address(0));
                balances[account] = 1;
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        validation_findings = [
            finding
            for finding in findings
            if finding.title.startswith(
                "Missing input validation"
            )
        ]

        assert validation_findings == []

    @pytest.mark.asyncio
    async def test_unguarded_ether_send_is_high(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            function withdraw(
                uint256 amount
            ) external {
                payable(msg.sender).transfer(amount);
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        finding = next(
            finding
            for finding in findings
            if finding.title.startswith(
                "Unprotected Ether withdrawal:"
            )
        )

        assert finding.severity is Severity.HIGH
        assert finding.risk_level is RiskLevel.HIGH
        assert finding.confidence is Confidence.HIGH
        assert finding.swc_id == "SWC-105"

    @pytest.mark.asyncio
    async def test_full_balance_ether_send_is_critical(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            function emergencyWithdraw() external {
                payable(msg.sender).transfer(
                    address(this).balance
                );
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        finding = next(
            finding
            for finding in findings
            if finding.title.startswith(
                "Unprotected Ether withdrawal:"
            )
        )

        assert finding.severity is Severity.CRITICAL
        assert finding.risk_level is RiskLevel.CRITICAL
        assert finding.confidence is Confidence.HIGH

    @pytest.mark.asyncio
    async def test_unguarded_sender_call_is_dos_risk(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            function withdraw() external {
                (bool success, ) = msg.sender.call{
                    value: address(this).balance
                }("");
                require(success);
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        finding = next(
            finding
            for finding in findings
            if finding.swc_id == "SWC-113"
        )

        assert finding.severity is Severity.MEDIUM
        assert finding.risk_level is RiskLevel.MEDIUM
        assert finding.confidence is Confidence.MEDIUM

    @pytest.mark.asyncio
    async def test_pull_payment_pattern_is_not_reported_as_dos(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            mapping(address => uint256) pendingWithdrawals;

            function withdraw() external {
                uint256 amount =
                    pendingWithdrawals[msg.sender];

                pendingWithdrawals[msg.sender] = 0;

                (bool success, ) = msg.sender.call{
                    value: amount
                }("");

                require(success);
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        dos_findings = [
            finding
            for finding in findings
            if finding.swc_id == "SWC-113"
        ]

        assert dos_findings == []

    @pytest.mark.asyncio
    async def test_view_function_is_not_reported(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            mapping(address => uint256) balances;

            function getBalance(
                address account
            ) external view returns (uint256) {
                return balances[account];
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        assert findings == ()

    @pytest.mark.asyncio
    async def test_constructor_is_not_reported(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            address public owner;

            constructor(
                address initialOwner
            ) {
                owner = initialOwner;
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        assert findings == ()

    @pytest.mark.asyncio
    async def test_finding_location_uses_request_filename(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            address public owner;

            function setOwner(
                address newOwner
            ) external {
                owner = newOwner;
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(
                source,
                filename="contracts/TestContract.sol",
            ),
        )

        assert findings

        assert all(
            finding.location.filename
            == "contracts/TestContract.sol"
            for finding in findings
        )

    @pytest.mark.asyncio
    async def test_fingerprints_are_deterministic(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            mapping(address => uint256) balances;

            function updateBalance(
                address account,
                uint256 amount
            ) external {
                balances[account] = amount;
            }
        }
        """

        request = make_request(source)

        first = await analyzer.analyze(request)
        second = await analyzer.analyze(request)

        assert [
            finding.fingerprint
            for finding in first
        ] == [
            finding.fingerprint
            for finding in second
        ]

    @pytest.mark.asyncio
    async def test_fingerprints_are_valid_sha256_values(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            mapping(address => uint256) balances;

            function updateBalance(
                address account,
                uint256 amount
            ) external {
                balances[account] = amount;
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        assert findings

        for finding in findings:
            assert len(finding.fingerprint) == 64
            assert finding.fingerprint.islower()
            assert all(
                character in "0123456789abcdef"
                for character in finding.fingerprint
            )

    @pytest.mark.asyncio
    async def test_invalid_request_is_rejected(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        with pytest.raises(
            DomainValidationError,
            match="request must be an AnalysisRequest",
        ):
            await analyzer.analyze(
                None,  # type: ignore[arg-type]
            )

    @pytest.mark.asyncio
    async def test_analyzer_marks_findings_as_heuristic(
        self,
        analyzer: HeuristicAnalyzer,
    ) -> None:
        source = """
        pragma solidity ^0.8.20;

        contract TestContract {
            mapping(address => uint256) balances;

            function updateBalance(
                address account,
                uint256 amount
            ) external {
                balances[account] = amount;
            }
        }
        """

        findings = await analyzer.analyze(
            make_request(source),
        )

        assert findings

        assert all(
            finding.analyzer is AnalyzerType.HEURISTIC
            for finding in findings
        )