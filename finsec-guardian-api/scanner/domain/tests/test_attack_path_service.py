from scanner.domain.entities import Finding
from scanner.domain.enums import AnalyzerType, Confidence, RiskLevel, Severity
from scanner.domain.services.attack_path_service import AttackPathService
from scanner.domain.value_objects.source_location import SourceLocation
from scanner.domain.value_objects.vulnerability_signature import VulnerabilitySignature


def _build_finding(title: str, line: int) -> Finding:
    return Finding(
        title=title,
        description=f"Description for {title}",
        recommendation="Patch the issue",
        severity=Severity.HIGH,
        confidence=Confidence.MEDIUM,
        risk_level=RiskLevel.HIGH,
        analyzer=AnalyzerType.SLITHER,
        location=SourceLocation(filename="contracts/Token.sol", line=line),
        signature=VulnerabilitySignature("a" * 64),
    )


def test_attack_path_service_discovers_correlated_attack_path() -> None:
    findings = (
        _build_finding("Unprotected ownership change", 10),
        _build_finding("Missing access control", 12),
    )

    attack_paths = AttackPathService.discover(findings)

    assert len(attack_paths) == 1
    path = attack_paths[0]
    assert path.findings_count == 2
    assert path.entry_finding_id in path.finding_ids
    assert path.impact_finding_id in path.finding_ids
    assert path.reasoning
    assert path.score >= 0.0
    assert 0.0 <= path.confidence <= 1.0
