from uuid import uuid4
from uuid import UUID, uuid4

import pytest

from scanner.domain.enums import RiskLevel
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.attack_path import AttackPath

def make_attack_path(
    *,
    risk_level: RiskLevel = RiskLevel.HIGH,
    finding_ids: tuple[UUID, ...] | None = None,
) -> AttackPath:
    if finding_ids is None:
        finding_ids = (
            uuid4(),
            uuid4(),
            uuid4(),
        )

    return AttackPath(
        identifier="AP-001",
        title="Attack Path",
        description="Test attack path",
        risk_level=risk_level,
        finding_ids=finding_ids,
        entry_finding_id=finding_ids[0],
        impact_finding_id=finding_ids[-1],
        confidence=0.8,
        score=50.0,
        reasoning=("Test reasoning",),
    )
@pytest.fixture
def finding_ids():
    return tuple(uuid4() for _ in range(3))


@pytest.fixture
def attack_path(finding_ids):
    return AttackPath(
        identifier="AP-001",
        title="Reentrancy Attack Path",
        description="A correlated sequence of findings indicating a potential attack path.",
        risk_level=RiskLevel.HIGH,
        finding_ids=finding_ids,
        entry_finding_id=finding_ids[0],
        impact_finding_id=finding_ids[2],
        confidence=0.85,
        score=75.0,
        reasoning=(
            "External call may be exploitable.",
            "State mutation occurs after the external interaction.",
        ),
    )


class TestAttackPathConstruction:

    def test_creates_valid_attack_path(self, attack_path, finding_ids):
        assert attack_path.identifier == "AP-001"
        assert attack_path.title == "Reentrancy Attack Path"
        assert attack_path.risk_level is RiskLevel.HIGH
        assert attack_path.finding_ids == finding_ids
        assert attack_path.entry_finding_id == finding_ids[0]
        assert attack_path.impact_finding_id == finding_ids[2]
        assert attack_path.confidence == 0.85
        assert attack_path.score == 75.0

    def test_strips_string_fields(self, finding_ids):
        path = AttackPath(
            identifier="  AP-001  ",
            title="  Attack Path  ",
            description="  Correlated findings  ",
            risk_level=RiskLevel.MEDIUM,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.80,
            score=50.0,
        )

        assert path.identifier == "AP-001"
        assert path.title == "Attack Path"
        assert path.description == "Correlated findings"


class TestAttackPathValidation:

    @pytest.mark.parametrize(
        "field,value",
        [
            ("identifier", ""),
            ("identifier", "   "),
            ("title", ""),
            ("title", "   "),
            ("description", ""),
            ("description", "   "),
        ],
    )
    def test_rejects_empty_string_fields(self, finding_ids, field, value):
        kwargs = dict(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.HIGH,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.8,
            score=50.0,
        )

        kwargs[field] = value

        with pytest.raises(DomainValidationError):
            AttackPath(**kwargs)

    def test_rejects_invalid_risk_level(self, finding_ids):
        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level="HIGH",  # Should be RiskLevel enum instance
                finding_ids=finding_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[1],
                confidence=0.8,
                score=50.0,
            )

    def test_rejects_empty_finding_ids(self):
        finding_id = uuid4()

        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=(),
                entry_finding_id=finding_id,
                impact_finding_id=finding_id,
                confidence=0.8,
                score=50.0,
            )

    def test_rejects_duplicate_finding_ids(self):
        finding_id = uuid4()
        another_id = uuid4()

        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=(finding_id, finding_id, another_id),
                entry_finding_id=finding_id,
                impact_finding_id=another_id,
                confidence=0.8,
                score=50.0,
            )

    def test_rejects_invalid_finding_id_type(self, finding_ids):
        # Fixed: ensured entry/impact IDs match the elements in invalid_ids
        invalid_ids = (finding_ids[0], "not-a-uuid")

        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=invalid_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[0],  # Fixed membership conflict
                confidence=0.8,
                score=50.0,
            )

    def test_rejects_entry_finding_id_not_in_finding_ids(self, finding_ids):
        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=finding_ids,
                entry_finding_id=uuid4(),  # ID not in finding_ids
                impact_finding_id=finding_ids[1],
                confidence=0.8,
                score=50.0,
            )

    def test_rejects_impact_finding_id_not_in_finding_ids(self, finding_ids):
        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=finding_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=uuid4(),  # ID not in finding_ids
                confidence=0.8,
                score=50.0,
            )


class TestAttackPathScoring:

    @pytest.mark.parametrize(
        "confidence",
        [-0.01, 1.01, "high", None],
    )
    def test_rejects_invalid_confidence(self, finding_ids, confidence):
        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=finding_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[1],
                confidence=confidence,
                score=50.0,
            )

    @pytest.mark.parametrize(
        "score",
        [-1.0, "high", None],
    )
    def test_rejects_invalid_score(self, finding_ids, score):
        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=finding_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[1],
                confidence=0.8,
                score=score,
            )

    def test_accepts_zero_confidence_and_score(self, finding_ids):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.LOW,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.0,
            score=0.0,
        )

        assert path.confidence == 0.0
        assert path.score == 0.0


class TestAttackPathCollections:

    def test_finding_ids_are_coerced_to_tuple(self, finding_ids):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.HIGH,
            finding_ids=list(finding_ids),
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.8,
            score=50.0,
        )

        assert isinstance(path.finding_ids, tuple)
        assert path.finding_ids == finding_ids

    def test_reasoning_is_coerced_to_tuple(self, finding_ids):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.HIGH,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.8,
            score=50.0,
            reasoning=[
                "  First reason  ",
                "Second reason",
            ],
        )

        assert isinstance(path.reasoning, tuple)
        assert path.reasoning == (
            "First reason",
            "Second reason",
        )

    def test_rejects_non_string_reasoning(self, finding_ids):
        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=finding_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[1],
                confidence=0.8,
                score=50.0,
                reasoning=("valid reason", 123),
            )

    def test_rejects_whitespace_reasoning(self, finding_ids):
        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=finding_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[1],
                confidence=0.8,
                score=50.0,
                reasoning=("   ",),
            )


class TestAttackPathImmutability:

    def test_attack_path_is_frozen(self, attack_path):
        with pytest.raises(AttributeError):
            attack_path.score = 100.0

    def test_finding_ids_are_immutable(self, attack_path):
        assert isinstance(attack_path.finding_ids, tuple)

    def test_reasoning_is_immutable(self, attack_path):
        assert isinstance(attack_path.reasoning, tuple)


class TestAttackPathDerivedProperties:

    def test_key_returns_identifier(self, attack_path):
        assert attack_path.key == attack_path.identifier

    def test_entry_point_returns_entry_finding(self, attack_path):
        assert attack_path.entry_point == attack_path.entry_finding_id

    def test_impact_point_returns_impact_finding(self, attack_path):
        assert attack_path.impact_point == attack_path.impact_finding_id

    def test_findings_count(self, attack_path):
        assert attack_path.findings_count == 3

    def test_step_count(self, attack_path):
        # Adjust expectation depending on whether step_count means nodes (3) or edges (2)
        assert attack_path.step_count == 3

    def test_multi_stage_path(self, attack_path):
        assert attack_path.spans_multiple_findings is True
        assert attack_path.is_single_stage is False
        assert attack_path.is_multi_stage is True

    def test_complex_path(self, attack_path):
        assert attack_path.is_complex is True

    def test_normalized_score(self, attack_path):
        assert attack_path.normalized_score == 25.0

    def test_severity_rank(self, attack_path):
        assert attack_path.severity_rank == RiskLevel.HIGH.weight

    def test_has_reasoning(self, attack_path):
        assert attack_path.has_reasoning is True

    def test_confidence_threshold(self, attack_path):
        assert attack_path.is_confident is True


class TestAttackPathRiskPredicates:
    @pytest.mark.parametrize(
        ("risk_level", "predicate"),
        [
            (RiskLevel.CRITICAL, "is_critical_risk"),
            (RiskLevel.HIGH, "is_high_risk"),
            (RiskLevel.MEDIUM, "is_medium_risk"),
            (RiskLevel.LOW, "is_low_risk"),
            (RiskLevel.VERY_LOW, "is_very_low_risk"),
        ],
    )
    def test_risk_predicate(
        self,
        risk_level: RiskLevel,
        predicate: str,
    ) -> None:
        attack_path = make_attack_path(
            risk_level=risk_level,
        )

        assert getattr(attack_path, predicate) is True