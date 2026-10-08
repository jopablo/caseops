import json
from pathlib import Path

from caseops.rules.parcel_state import (
    BlockerCode,
    DataQualityIssue,
    DocumentaryState,
    OperationalState,
    ParcelEvidence,
    evaluate_parcel,
)


DATA = Path(__file__).parents[1] / "data" / "synthetic" / "inspiration_cases.json"


def load_cases():
    return json.loads(DATA.read_text())


def build_evidence(case):
    return ParcelEvidence(
        recorded_judgment=case["recorded_judgment"],
        recorded_release=case["recorded_release"],
        proof_of_deposit=case["proof_of_deposit"],
        title_policy=case["title_policy"],
        final_invoice_pdf=case["final_invoice_pdf"],
        closeout_memo_pdf=case["closeout_memo_pdf"],
        monday_stage=case["monday_stage"],
        monday_case_status=case["monday_case_status"],
        latest_comment=case["latest_comment"],
    )


def test_complete_cases_can_be_document_complete_but_pending_approval():
    for case in [load_cases()[0], load_cases()[1], load_cases()[3], load_cases()[5]]:
        decision = evaluate_parcel(build_evidence(case))
        assert decision.documentary_state == DocumentaryState.COMPLETE
        assert decision.operational_state == OperationalState.PENDING_APPROVAL
        assert decision.blocker == BlockerCode.APPROVAL_PENDING
        assert decision.next_action == "AWAIT_APPROVAL"


def test_missing_title_policy_blocks_closeout():
    case = load_cases()[2]
    decision = evaluate_parcel(build_evidence(case))

    assert decision.documentary_state == DocumentaryState.INCOMPLETE
    assert decision.operational_state == OperationalState.AWAITING_TITLE_POLICY
    assert decision.blocker == BlockerCode.TITLE_POLICY_MISSING
    assert decision.next_action == "FOLLOW_UP_TITLE_POLICY"


def test_title_policy_received_while_on_hold_does_not_auto_close():
    case = load_cases()[4]
    decision = evaluate_parcel(build_evidence(case))

    assert decision.documentary_state == DocumentaryState.READY_FOR_CLOSEOUT
    assert decision.operational_state == OperationalState.ON_HOLD
    assert decision.blocker == BlockerCode.ON_HOLD
    assert decision.next_action == "CONFIRM_HOLD_STATUS"
    assert DataQualityIssue.MONDAY_STAGE_STALE in decision.data_quality_issues


def test_draft_closeout_does_not_count_as_final_closeout():
    evidence = ParcelEvidence(
        recorded_judgment=True,
        recorded_release=True,
        proof_of_deposit=True,
        title_policy=True,
        final_invoice_pdf=False,
        closeout_memo_pdf=False,
        monday_stage="Closing",
        monday_case_status="Active",
        latest_comment="",
    )

    decision = evaluate_parcel(evidence)

    assert decision.documentary_state == DocumentaryState.READY_FOR_CLOSEOUT
    assert decision.operational_state == OperationalState.ACTIVE
    assert decision.next_action == "FINALIZE_CLOSEOUT_PACKAGE"
