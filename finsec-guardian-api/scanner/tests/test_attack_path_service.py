from __future__ import annotations

from uuid import uuid4

import pytest

from scanner.domain.enums import RiskLevel
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.attack_path import AttackPath


@pytest.fixture
def finding_ids():
    return tuple(uuid4() for _ in range(3))


@pytest.fixture
def attack_path(finding_ids):
    return AttackPath(
        identifier="AP-001",
        title="Reentrancy Attack Path",
        description="A correlated attack path involving multiple findings.",
        risk_level=RiskLevel.HIGH,
        finding_ids=finding_ids,
        entry_finding_id=finding_ids[0],
        impact_finding_id=finding_ids[-1],
        confidence=0.85,
        score=72.5,
        reasoning=(
            "External call may be exploitable.",
            "State mutation occurs after the call.",
        ),
    )


class TestAttackPathConstruction:
    def test_creates_valid_attack_path(self, attack_path, finding_ids):
        assert attack_path.identifier == "AP-001"
        assert attack_path.title == "Reentrancy Attack Path"
        assert attack_path.description.startswith("A correlated")
        assert attack_path.risk_level is RiskLevel.HIGH
        assert attack_path.finding_ids == finding_ids
        assert attack_path.entry_finding_id == finding_ids[0]
        assert attack_path.impact_finding_id == finding_ids[-1]
        assert attack_path.confidence == 0.85
        assert attack_path.score == 72.5

    def test_key_returns_identifier(self, attack_path):
        assert attack_path.key == attack_path.identifier


class TestAttackPathStringValidation:
    def test_strings_are_stripped(self, finding_ids):
        path = AttackPath(
            identifier="  AP-001  ",
            title="  Attack Path  ",
            description="  Description  ",
            risk_level=RiskLevel.HIGH,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.8,
            score=50,
        )

        assert path.identifier == "AP-001"
        assert path.title == "Attack Path"
        assert path.description == "Description"

    @pytest.mark.parametrize(
        "field",
        ["identifier", "title", "description"],
    )
    def test_empty_string_is_rejected(self, finding_ids, field):
        values = {
            "identifier": "AP-001",
            "title": "Attack Path",
            "description": "Description",
        }
        values[field] = "   "

        with pytest.raises(DomainValidationError):
            AttackPath(
                **values,
                risk_level=RiskLevel.HIGH,
                finding_ids=finding_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[1],
                confidence=0.8,
                score=50,
            )


class TestAttackPathFindingIds:
    def test_finding_ids_are_normalized_to_tuple(self, finding_ids):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.HIGH,
            finding_ids=list(finding_ids),
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.8,
            score=50,
        )

        assert isinstance(path.finding_ids, tuple)
        assert path.finding_ids == finding_ids

    def test_empty_finding_ids_are_rejected(self, finding_ids):
        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=(),
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[1],
                confidence=0.8,
                score=50,
            )

    def test_duplicate_finding_ids_are_rejected(self, finding_ids):
        duplicate_ids = (
            finding_ids[0],
            finding_ids[1],
            finding_ids[0],
        )

        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=duplicate_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[1],
                confidence=0.8,
                score=50,
            )

    def test_non_uuid_finding_id_is_rejected(self, finding_ids):
        invalid_ids = (
            finding_ids[0],
            "not-a-uuid",
        )

        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=invalid_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[0],
                confidence=0.8,
                score=50,
            )


class TestAttackPathEntryAndImpact:
    def test_entry_finding_must_exist_in_path(self, finding_ids):
        outside_id = uuid4()

        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=finding_ids,
                entry_finding_id=outside_id,
                impact_finding_id=finding_ids[1],
                confidence=0.8,
                score=50,
            )

    def test_impact_finding_must_exist_in_path(self, finding_ids):
        outside_id = uuid4()

        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=finding_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=outside_id,
                confidence=0.8,
                score=50,
            )

    def test_entry_and_impact_can_be_same_finding(self, finding_ids):
        path = AttackPath(
            identifier="AP-001",
            title="Single Finding Path",
            description="A single finding attack path.",
            risk_level=RiskLevel.MEDIUM,
            finding_ids=(finding_ids[0],),
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[0],
            confidence=0.8,
            score=20,
        )

        assert path.entry_finding_id == path.impact_finding_id


class TestAttackPathScoring:
    @pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
    def test_valid_confidence_values(self, finding_ids, confidence):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.HIGH,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=confidence,
            score=50,
        )

        assert path.confidence == confidence

    @pytest.mark.parametrize("confidence", [-0.01, 1.01])
    def test_invalid_confidence_range(self, finding_ids, confidence):
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
                score=50,
            )

    @pytest.mark.parametrize("score", [-1.0, -100])
    def test_negative_score_is_rejected(self, finding_ids, score):
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

    def test_score_is_unbounded_above(self, finding_ids):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.HIGH,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.8,
            score=250.0,
        )

        assert path.score == 250.0

    @pytest.mark.parametrize(
        "field,value",
        [
            ("confidence", "0.8"),
            ("confidence", None),
            ("score", "50"),
            ("score", None),
        ],
    )
    def test_numeric_fields_reject_invalid_types(
        self,
        finding_ids,
        field,
        value,
    ):
        values = {
            "confidence": 0.8,
            "score": 50.0,
        }
        values[field] = value

        with pytest.raises(DomainValidationError):
            AttackPath(
                identifier="AP-001",
                title="Attack Path",
                description="Description",
                risk_level=RiskLevel.HIGH,
                finding_ids=finding_ids,
                entry_finding_id=finding_ids[0],
                impact_finding_id=finding_ids[1],
                **values,
            )


class TestAttackPathReasoning:
    def test_reasoning_is_normalized_to_tuple(self, finding_ids):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.HIGH,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.8,
            score=50,
            reasoning=["Reason one", "Reason two"],
        )

        assert isinstance(path.reasoning, tuple)

    def test_empty_reasoning_is_allowed(self, finding_ids):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.HIGH,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.8,
            score=50,
        )

        assert path.reasoning == ()
        assert not path.has_reasoning

    def test_reasoning_rejects_empty_strings(self, finding_ids):
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
                score=50,
                reasoning=("Valid reason", "   "),
            )


class TestAttackPathRisk:
    @pytest.mark.parametrize(
        "risk_level",
        list(RiskLevel),
    )
    def test_risk_level_is_preserved(self, finding_ids, risk_level):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=risk_level,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.8,
            score=50,
        )

        assert path.risk_level is risk_level

    def test_high_risk_predicate(self, finding_ids):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.HIGH,
            finding_ids=finding_ids,
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[1],
            confidence=0.8,
            score=50,
        )

        assert path.is_high_risk


class TestAttackPathMetrics:
    def test_findings_count(self, attack_path):
        assert attack_path.findings_count == 3

    def test_step_count_matches_findings_count(self, attack_path):
        assert attack_path.step_count == attack_path.findings_count

    def test_single_stage(self, finding_ids):
        path = AttackPath(
            identifier="AP-001",
            title="Attack Path",
            description="Description",
            risk_level=RiskLevel.LOW,
            finding_ids=(finding_ids[0],),
            entry_finding_id=finding_ids[0],
            impact_finding_id=finding_ids[0],
            confidence=0.8,
            score=10,
        )

        assert path.is_single_stage
        assert not path.is_multi_stage

    def test_multi_stage(self, attack_path):
        assert attack_path.is_multi_stage
        assert attack_path.spans_multiple_findings

    def test_complex_path(self, attack_path):
        assert attack_path.is_complex

    def test_normalized_score(self, attack_path):
        assert attack_path.normalized_score == 72.5 / 3

    def test_confident_path(self, attack_path):
        assert attack_path.is_confident


class TestAttackPathImmutability:
    def test_cannot_modify_identifier(self, attack_path):
        with pytest.raises(AttributeError):
            attack_path.identifier = "AP-002"

    def test_cannot_modify_finding_ids(self, attack_path):
        with pytest.raises(AttributeError):
            attack_path.finding_ids = ()

    def test_finding_ids_are_immutable(self, attack_path):
        assert isinstance(attack_path.finding_ids, tuple)

    def test_reasoning_is_immutable(self, attack_path):
        assert isinstance(attack_path.reasoning, tuple)