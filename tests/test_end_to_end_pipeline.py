from caseops.orchestration import evaluate_from_reconciliation
from caseops.reconciliation.engine import reconcile_document
from caseops.reconciliation.models import (
    Authority,
    EvidenceObservation,
    EvidenceState,
    EvidenceType,
    SourceSystem,
)
from caseops.rules.parcel_state import (
    BlockerCode,
    DocumentaryState,
    OperationalState,
)


def drive_observation(evidence_type, state):
    return EvidenceObservation(
        evidence_type=evidence_type,
        source=SourceSystem.DRIVE,
        state=state,
        authority=Authority.HIGH,
    )


def test_end_to_end_missing_title_policy_while_case_is_on_hold():
    results = {
        EvidenceType.RECORDED_JUDGMENT: reconcile_document(
            EvidenceType.RECORDED_JUDGMENT,
            [drive_observation(EvidenceType.RECORDED_JUDGMENT, EvidenceState.VERIFIED)],
        ),
        EvidenceType.RECORDED_RELEASE: reconcile_document(
            EvidenceType.RECORDED_RELEASE,
            [drive_observation(EvidenceType.RECORDED_RELEASE, EvidenceState.VERIFIED)],
        ),
        EvidenceType.PROOF_OF_DEPOSIT: reconcile_document(
            EvidenceType.PROOF_OF_DEPOSIT,
            [drive_observation(EvidenceType.PROOF_OF_DEPOSIT, EvidenceState.VERIFIED)],
        ),
        EvidenceType.TITLE_POLICY: reconcile_document(
            EvidenceType.TITLE_POLICY,
            [
                drive_observation(EvidenceType.TITLE_POLICY, EvidenceState.MISSING),
                EvidenceObservation(
                    evidence_type=EvidenceType.TITLE_POLICY,
                    source=SourceSystem.MONDAY,
                    state=EvidenceState.MISSING,
                    authority=Authority.MEDIUM,
                ),
            ],
            workflow_stage="Missing Title Policy",
        ),
        EvidenceType.FINAL_INVOICE: reconcile_document(
            EvidenceType.FINAL_INVOICE,
            [drive_observation(EvidenceType.FINAL_INVOICE, EvidenceState.MISSING)],
        ),
        EvidenceType.CLOSEOUT_MEMO: reconcile_document(
            EvidenceType.CLOSEOUT_MEMO,
            [drive_observation(EvidenceType.CLOSEOUT_MEMO, EvidenceState.DRAFT)],
        ),
    }

    title_policy_result = results[EvidenceType.TITLE_POLICY]

    assert title_policy_result.canonical_state == EvidenceState.MISSING
    assert title_policy_result.accepted is False
    assert title_policy_result.next_action == "FOLLOW_UP_TITLE_POLICY"

    decision = evaluate_from_reconciliation(
        results,
        monday_stage="Missing Title Policy",
        monday_case_status="On hold",
        latest_comment="Hold reminders until further notice.",
    )

    assert decision.documentary_state == DocumentaryState.INCOMPLETE
    assert decision.operational_state == OperationalState.ON_HOLD
    assert decision.documentary_blocker == BlockerCode.TITLE_POLICY_MISSING
    assert decision.operational_blocker == BlockerCode.ON_HOLD
    assert decision.blocker == BlockerCode.ON_HOLD
    assert decision.next_action == "CONFIRM_HOLD_STATUS"
