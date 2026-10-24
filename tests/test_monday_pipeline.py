from caseops.adapters.monday import adapt_monday_item
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


def test_monday_adapter_can_feed_full_caseops_pipeline():
    item = {
        "id": "2001",
        "name": "Synthetic Parcel Hold Case",
        "url": "https://example.test/items/2001",
        "column_values": {
            "status": "7. Missing Title Policy",
            "color_mm442gwk": "On hold",
            "text_mm2mttm5": "CASE-002",
            "text_mm2dy085": "Synthetic Client",
            "text_mm2ddd74": "",
            "text_mm2dkhs5": "",
            "link_mm57dd7p": "",
        },
        "group": {
            "id": "hold-group",
            "title": "Cases on hold",
        },
    }

    updates = [
        {
            "id": "u1",
            "text_body": "Only the title policy remains pending.",
            "created_at": "2026-05-28T14:19:03.000Z",
        },
        {
            "id": "u2",
            "text_body": "HOLD REMINDERS. NOTE FROM APPROVER.",
            "created_at": "2026-07-01T21:49:28.000Z",
        },
    ]

    monday = adapt_monday_item(item, updates)

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
                *monday.evidence_observations,
            ],
            workflow_stage=monday.stage,
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

    title_policy = results[EvidenceType.TITLE_POLICY]

    assert title_policy.canonical_state == EvidenceState.MISSING
    assert title_policy.accepted is False

    decision = evaluate_from_reconciliation(
        results,
        monday_stage=monday.stage,
        monday_case_status=monday.case_status,
        latest_comment=monday.latest_comment,
    )

    assert decision.documentary_state == DocumentaryState.INCOMPLETE
    assert decision.operational_state == OperationalState.ON_HOLD
    assert decision.documentary_blocker == BlockerCode.TITLE_POLICY_MISSING
    assert decision.operational_blocker == BlockerCode.ON_HOLD
    assert decision.blocker == BlockerCode.ON_HOLD
    assert decision.next_action == "CONFIRM_HOLD_STATUS"
