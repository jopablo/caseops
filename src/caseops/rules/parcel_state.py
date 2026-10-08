from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


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


class DataQualityIssue(str, Enum):
    MONDAY_STAGE_STALE = "MONDAY_STAGE_STALE"


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
    blocker: BlockerCode
    next_action: str
    data_quality_issues: Tuple[DataQualityIssue, ...] = ()


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def evaluate_documentary_state(e: ParcelEvidence) -> DocumentaryState:
    prerequisites = (
        e.recorded_judgment
        and e.recorded_release
        and e.proof_of_deposit
    )

    if not prerequisites or not e.title_policy:
        return DocumentaryState.INCOMPLETE

    if e.final_invoice_pdf and e.closeout_memo_pdf:
        return DocumentaryState.COMPLETE

    return DocumentaryState.READY_FOR_CLOSEOUT


def evaluate_parcel(e: ParcelEvidence) -> ParcelDecision:
    documentary_state = evaluate_documentary_state(e)

    stage = _normalize(e.monday_stage)
    case_status = _normalize(e.monday_case_status)
    comment = _normalize(e.latest_comment)

    issues = []

    if e.title_policy and "missing title policy" in stage:
        issues.append(DataQualityIssue.MONDAY_STAGE_STALE)

    if "hold" in case_status or "hold" in comment:
        return ParcelDecision(
            documentary_state=documentary_state,
            operational_state=OperationalState.ON_HOLD,
            blocker=BlockerCode.ON_HOLD,
            next_action="CONFIRM_HOLD_STATUS",
            data_quality_issues=tuple(issues),
        )

    if not e.title_policy:
        return ParcelDecision(
            documentary_state=documentary_state,
            operational_state=OperationalState.AWAITING_TITLE_POLICY,
            blocker=BlockerCode.TITLE_POLICY_MISSING,
            next_action="FOLLOW_UP_TITLE_POLICY",
            data_quality_issues=tuple(issues),
        )

    if "approval" in comment and "pending" in comment:
        return ParcelDecision(
            documentary_state=documentary_state,
            operational_state=OperationalState.PENDING_APPROVAL,
            blocker=BlockerCode.APPROVAL_PENDING,
            next_action="AWAIT_APPROVAL",
            data_quality_issues=tuple(issues),
        )

    if documentary_state == DocumentaryState.COMPLETE and "closed" in stage:
        return ParcelDecision(
            documentary_state=documentary_state,
            operational_state=OperationalState.CLOSED,
            blocker=BlockerCode.NONE,
            next_action="NONE",
            data_quality_issues=tuple(issues),
        )

    if documentary_state == DocumentaryState.READY_FOR_CLOSEOUT:
        return ParcelDecision(
            documentary_state=documentary_state,
            operational_state=OperationalState.ACTIVE,
            blocker=BlockerCode.NONE,
            next_action="FINALIZE_CLOSEOUT_PACKAGE",
            data_quality_issues=tuple(issues),
        )

    return ParcelDecision(
        documentary_state=documentary_state,
        operational_state=OperationalState.ACTIVE,
        blocker=BlockerCode.DOCUMENT_MISSING,
        next_action="REVIEW_MISSING_DOCUMENTS",
        data_quality_issues=tuple(issues),
    )
