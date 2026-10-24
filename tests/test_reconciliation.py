from caseops.reconciliation.engine import reconcile_document
from caseops.reconciliation.models import (
    Authority,
    EvidenceObservation,
    EvidenceState,
    EvidenceType,
    ReconciliationIssue,
    SourceSystem,
)


def title_policy_observation(source, state, authority=Authority.HIGH):
    return EvidenceObservation(
        evidence_type=EvidenceType.TITLE_POLICY,
        source=source,
        state=state,
        authority=authority,
    )


def test_verified_drive_document_overrides_stale_workflow_stage():
    result = reconcile_document(
        EvidenceType.TITLE_POLICY,
        [
            title_policy_observation(SourceSystem.DRIVE, EvidenceState.VERIFIED),
            title_policy_observation(
                SourceSystem.MONDAY,
                EvidenceState.MISSING,
                Authority.MEDIUM,
            ),
        ],
        workflow_stage="Missing Title Policy",
    )

    assert result.canonical_state == EvidenceState.VERIFIED
    assert result.accepted is True
    assert ReconciliationIssue.WORKFLOW_STAGE_STALE in result.issues


def test_wrong_parcel_document_is_not_accepted():
    result = reconcile_document(
        EvidenceType.TITLE_POLICY,
        [
            title_policy_observation(
                SourceSystem.DRIVE,
                EvidenceState.INVALID,
            )
        ],
        workflow_stage="Missing Title Policy",
    )

    assert result.canonical_state == EvidenceState.INVALID
    assert result.accepted is False
    assert ReconciliationIssue.DOCUMENT_MISMATCH in result.issues
    assert result.next_action == "REVIEW_DOCUMENT"


def test_present_but_unverified_document_requires_validation():
    result = reconcile_document(
        EvidenceType.TITLE_POLICY,
        [
            title_policy_observation(
                SourceSystem.DRIVE,
                EvidenceState.PRESENT,
            )
        ],
    )

    assert result.canonical_state == EvidenceState.PRESENT
    assert result.accepted is False
    assert ReconciliationIssue.UNVERIFIED_DOCUMENT in result.issues
    assert result.next_action == "VERIFY_DOCUMENT"


def test_spreadsheet_cannot_override_verified_drive_evidence():
    result = reconcile_document(
        EvidenceType.TITLE_POLICY,
        [
            title_policy_observation(SourceSystem.DRIVE, EvidenceState.VERIFIED),
            title_policy_observation(
                SourceSystem.SPREADSHEET,
                EvidenceState.MISSING,
                Authority.LOW,
            ),
        ],
    )

    assert result.canonical_state == EvidenceState.VERIFIED
    assert ReconciliationIssue.SECONDARY_SOURCE_STALE in result.issues


def test_draft_closeout_memo_is_not_final_evidence():
    result = reconcile_document(
        EvidenceType.CLOSEOUT_MEMO,
        [
            EvidenceObservation(
                evidence_type=EvidenceType.CLOSEOUT_MEMO,
                source=SourceSystem.DRIVE,
                state=EvidenceState.DRAFT,
                authority=Authority.HIGH,
            )
        ],
    )

    assert result.canonical_state == EvidenceState.DRAFT
    assert result.accepted is False
    assert result.next_action == "FINALIZE_DOCUMENT"
