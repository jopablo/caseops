from caseops.orchestration import build_parcel_evidence, evaluate_from_reconciliation
from caseops.reconciliation.models import (
    EvidenceState,
    EvidenceType,
    ReconciliationResult,
)
from caseops.rules.parcel_state import (
    BlockerCode,
    DocumentaryState,
    OperationalState,
)


def result(
    evidence_type,
    *,
    state=EvidenceState.VERIFIED,
    accepted=True,
    next_action="NONE",
):
    return ReconciliationResult(
        evidence_type=evidence_type,
        canonical_state=state,
        accepted=accepted,
        issues=(),
        next_action=next_action,
        explanation="synthetic test result",
    )


def verified_closeout_results():
    return {
        EvidenceType.RECORDED_JUDGMENT: result(EvidenceType.RECORDED_JUDGMENT),
        EvidenceType.RECORDED_RELEASE: result(EvidenceType.RECORDED_RELEASE),
        EvidenceType.PROOF_OF_DEPOSIT: result(EvidenceType.PROOF_OF_DEPOSIT),
        EvidenceType.TITLE_POLICY: result(EvidenceType.TITLE_POLICY),
        EvidenceType.FINAL_INVOICE: result(EvidenceType.FINAL_INVOICE),
        EvidenceType.CLOSEOUT_MEMO: result(EvidenceType.CLOSEOUT_MEMO),
    }


def test_only_verified_accepted_evidence_becomes_true():
    results = verified_closeout_results()
    results[EvidenceType.TITLE_POLICY] = result(
        EvidenceType.TITLE_POLICY,
        state=EvidenceState.PRESENT,
        accepted=False,
        next_action="VERIFY_DOCUMENT",
    )

    evidence = build_parcel_evidence(results)

    assert evidence.recorded_judgment is True
    assert evidence.title_policy is False


def test_invalid_title_policy_does_not_reach_state_engine_as_true():
    results = verified_closeout_results()
    results[EvidenceType.TITLE_POLICY] = result(
        EvidenceType.TITLE_POLICY,
        state=EvidenceState.INVALID,
        accepted=False,
        next_action="REVIEW_DOCUMENT",
    )

    decision = evaluate_from_reconciliation(
        results,
        monday_stage="Missing Title Policy",
        monday_case_status="Active",
    )

    assert decision.documentary_state == DocumentaryState.INCOMPLETE
    assert decision.operational_state == OperationalState.AWAITING_TITLE_POLICY
    assert decision.blocker == BlockerCode.TITLE_POLICY_MISSING


def test_verified_title_policy_can_progress_to_pending_approval():
    decision = evaluate_from_reconciliation(
        verified_closeout_results(),
        monday_stage="Closed",
        monday_case_status="Active",
        latest_comment="Final approval pending.",
    )

    assert decision.documentary_state == DocumentaryState.COMPLETE
    assert decision.operational_state == OperationalState.PENDING_APPROVAL
    assert decision.blocker == BlockerCode.APPROVAL_PENDING
    assert decision.next_action == "AWAIT_APPROVAL"


def test_present_unverified_title_policy_does_not_count_as_verified():
    results = verified_closeout_results()
    results[EvidenceType.TITLE_POLICY] = result(
        EvidenceType.TITLE_POLICY,
        state=EvidenceState.PRESENT,
        accepted=False,
        next_action="VERIFY_DOCUMENT",
    )

    decision = evaluate_from_reconciliation(
        results,
        monday_stage="Missing Title Policy",
        monday_case_status="Active",
    )

    assert decision.documentary_state == DocumentaryState.INCOMPLETE
    assert decision.operational_state == OperationalState.AWAITING_TITLE_POLICY
