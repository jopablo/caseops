from caseops.orchestration import evaluate_from_reconciliation
from caseops.reconciliation.engine import reconcile_document
from caseops.reconciliation.models import (
    Authority,
    EvidenceObservation,
    EvidenceState,
    EvidenceType,
    ReconciliationIssue,
    SourceSystem,
)
from caseops.rules.parcel_state import (
    BlockerCode,
    DocumentaryState,
    OperationalState,
)


def drive_verified(evidence_type):
    return EvidenceObservation(
        evidence_type=evidence_type,
        source=SourceSystem.DRIVE,
        state=EvidenceState.VERIFIED,
        authority=Authority.HIGH,
    )


def test_end_to_end_title_policy_arrived_but_case_is_on_hold():
    # Step 1: reconcile each documentary fact.
    results = {
        EvidenceType.RECORDED_JUDGMENT: reconcile_document(
            EvidenceType.RECORDED_JUDGMENT,
            [drive_verified(EvidenceType.RECORDED_JUDGMENT)],
        ),
        EvidenceType.RECORDED_RELEASE: reconcile_document(
            EvidenceType.RECORDED_RELEASE,
            [drive_verified(EvidenceType.RECORDED_RELEASE)],
        ),
        EvidenceType.PROOF_OF_DEPOSIT: reconcile_document(
            EvidenceType.PROOF_OF_DEPOSIT,
            [drive_verified(EvidenceType.PROOF_OF_DEPOSIT)],
        ),
        EvidenceType.TITLE_POLICY: reconcile_document(
            EvidenceType.TITLE_POLICY,
            [
                drive_verified(EvidenceType.TITLE_POLICY),
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
            [
                EvidenceObservation(
                    evidence_type=EvidenceType.FINAL_INVOICE,
                    source=SourceSystem.DRIVE,
                    state=EvidenceState.MISSING,
                    authority=Authority.HIGH,
                )
            ],
        ),
        EvidenceType.CLOSEOUT_MEMO: reconcile_document(
            EvidenceType.CLOSEOUT_MEMO,
            [
                EvidenceObservation(
                    evidence_type=EvidenceType.CLOSEOUT_MEMO,
                    source=SourceSystem.DRIVE,
                    state=EvidenceState.DRAFT,
                    authority=Authority.HIGH,
                )
            ],
        ),
    }

    # Step 2: verify reconciliation found the stale workflow stage.
    title_policy_result = results[EvidenceType.TITLE_POLICY]

    assert title_policy_result.canonical_state == EvidenceState.VERIFIED
    assert title_policy_result.accepted is True
    assert ReconciliationIssue.WORKFLOW_STAGE_STALE in title_policy_result.issues

    # Step 3: pass only accepted canonical evidence to the parcel-state engine.
    decision = evaluate_from_reconciliation(
        results,
        monday_stage="Missing Title Policy",
        monday_case_status="On hold",
        latest_comment="Hold reminders until further notice.",
    )

    # Step 4: assert the final CaseOps decision.
    assert decision.documentary_state == DocumentaryState.READY_FOR_CLOSEOUT
    assert decision.operational_state == OperationalState.ON_HOLD
    assert decision.blocker == BlockerCode.ON_HOLD
    assert decision.next_action == "CONFIRM_HOLD_STATUS"
