from __future__ import annotations

from collections.abc import Mapping

from caseops.reconciliation.models import (
    EvidenceState,
    EvidenceType,
    ReconciliationResult,
)
from caseops.rules.parcel_state import ParcelDecision, ParcelEvidence, evaluate_parcel


def _accepted(
    results: Mapping[EvidenceType, ReconciliationResult],
    evidence_type: EvidenceType,
) -> bool:
    result = results.get(evidence_type)
    if result is None:
        return False

    return (
        result.accepted
        and result.canonical_state == EvidenceState.VERIFIED
    )


def build_parcel_evidence(
    results: Mapping[EvidenceType, ReconciliationResult],
    *,
    monday_stage: str = "",
    monday_case_status: str = "",
    latest_comment: str = "",
) -> ParcelEvidence:
    return ParcelEvidence(
        recorded_judgment=_accepted(
            results,
            EvidenceType.RECORDED_JUDGMENT,
        ),
        recorded_release=_accepted(
            results,
            EvidenceType.RECORDED_RELEASE,
        ),
        proof_of_deposit=_accepted(
            results,
            EvidenceType.PROOF_OF_DEPOSIT,
        ),
        title_policy=_accepted(
            results,
            EvidenceType.TITLE_POLICY,
        ),
        final_invoice_pdf=_accepted(
            results,
            EvidenceType.FINAL_INVOICE,
        ),
        closeout_memo_pdf=_accepted(
            results,
            EvidenceType.CLOSEOUT_MEMO,
        ),
        monday_stage=monday_stage,
        monday_case_status=monday_case_status,
        latest_comment=latest_comment,
    )


def evaluate_from_reconciliation(
    results: Mapping[EvidenceType, ReconciliationResult],
    *,
    monday_stage: str = "",
    monday_case_status: str = "",
    latest_comment: str = "",
) -> ParcelDecision:
    evidence = build_parcel_evidence(
        results,
        monday_stage=monday_stage,
        monday_case_status=monday_case_status,
        latest_comment=latest_comment,
    )
    return evaluate_parcel(evidence)
