from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DocumentaryState(str, Enum):
    INCOMPLETE = "INCOMPLETE"
    READY_FOR_CLOSEOUT = "READY_FOR_CLOSEOUT"
    COMPLETE = "COMPLETE"


class OperationalState(str, Enum):
    ACTIVE = "ACTIVE"
    AWAITING_TITLE_POLICY = "AWAITING_TITLE_POLICY"
    ON_HOLD = "ON_HOLD"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    CLOSED = "CLOSED"


class BlockerCode(str, Enum):
    NONE = "NONE"
    DOCUMENT_MISSING = "DOCUMENT_MISSING"
    TITLE_POLICY_MISSING = "TITLE_POLICY_MISSING"
    ON_HOLD = "ON_HOLD"
    APPROVAL_PENDING = "APPROVAL_PENDING"


@dataclass(frozen=True)
class ParcelEvidence:
    recorded_judgment: bool
    recorded_release: bool
    proof_of_deposit: bool
    title_policy: bool
    final_invoice_pdf: bool
    closeout_memo_pdf: bool
    monday_stage: str = ""
    monday_case_status: str = ""
    latest_comment: str = ""


@dataclass(frozen=True)
class ParcelDecision:
    documentary_state: DocumentaryState
    operational_state: OperationalState
    documentary_blocker: BlockerCode
    operational_blocker: BlockerCode
    blocker: BlockerCode
    next_action: str


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def evaluate_documentary_state(e: ParcelEvidence) -> DocumentaryState:
    prerequisites = e.recorded_judgment and e.recorded_release and e.proof_of_deposit

    if not prerequisites or not e.title_policy:
        return DocumentaryState.INCOMPLETE

    if e.final_invoice_pdf and e.closeout_memo_pdf:
        return DocumentaryState.COMPLETE

    return DocumentaryState.READY_FOR_CLOSEOUT


def _documentary_blocker(e: ParcelEvidence) -> BlockerCode:
    prerequisites = e.recorded_judgment and e.recorded_release and e.proof_of_deposit
    if not prerequisites:
        return BlockerCode.DOCUMENT_MISSING
    if not e.title_policy:
        return BlockerCode.TITLE_POLICY_MISSING
    return BlockerCode.NONE


def evaluate_parcel(e: ParcelEvidence) -> ParcelDecision:
    documentary_state = evaluate_documentary_state(e)
    documentary_blocker = _documentary_blocker(e)

    stage = _normalize(e.monday_stage)
    case_status = _normalize(e.monday_case_status)
    comment = _normalize(e.latest_comment)

    operational_state = OperationalState.ACTIVE
    operational_blocker = BlockerCode.NONE
    next_action = "REVIEW_MISSING_DOCUMENTS"

    if "hold" in case_status or "hold" in comment:
        operational_state = OperationalState.ON_HOLD
        operational_blocker = BlockerCode.ON_HOLD
        next_action = "CONFIRM_HOLD_STATUS"
    elif documentary_blocker == BlockerCode.TITLE_POLICY_MISSING:
        operational_state = OperationalState.AWAITING_TITLE_POLICY
        next_action = "FOLLOW_UP_TITLE_POLICY"
    elif "approval" in comment and "pending" in comment:
        operational_state = OperationalState.PENDING_APPROVAL
        operational_blocker = BlockerCode.APPROVAL_PENDING
        next_action = "AWAIT_APPROVAL"
    elif documentary_state == DocumentaryState.COMPLETE and "closed" in stage:
        operational_state = OperationalState.CLOSED
        next_action = "NONE"
    elif documentary_state == DocumentaryState.READY_FOR_CLOSEOUT:
        next_action = "FINALIZE_CLOSEOUT_PACKAGE"

    blocker = (
        operational_blocker
        if operational_blocker != BlockerCode.NONE
        else documentary_blocker
    )

    return ParcelDecision(
        documentary_state=documentary_state,
        operational_state=operational_state,
        documentary_blocker=documentary_blocker,
        operational_blocker=operational_blocker,
        blocker=blocker,
        next_action=next_action,
    )
