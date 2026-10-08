from __future__ import annotations

from collections.abc import Iterable

from .models import (
    EvidenceObservation,
    EvidenceState,
    EvidenceType,
    ReconciliationIssue,
    ReconciliationResult,
    SourceSystem,
)


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def reconcile_document(
    evidence_type: EvidenceType,
    observations: Iterable[EvidenceObservation],
    *,
    workflow_stage: str = "",
) -> ReconciliationResult:
    observations = [o for o in observations if o.evidence_type == evidence_type]
    drive = [o for o in observations if o.source == SourceSystem.DRIVE]
    issues: list[ReconciliationIssue] = []

    # Drive is the documentary source of truth, but presence alone is not enough:
    # the document must be validated before CaseOps accepts it as evidence.
    if any(o.state == EvidenceState.VERIFIED for o in drive):
        canonical_state = EvidenceState.VERIFIED
        accepted = True
        next_action = "NONE"
        explanation = "Verified documentary evidence exists in Drive."

    elif any(o.state == EvidenceState.INVALID for o in drive):
        canonical_state = EvidenceState.INVALID
        accepted = False
        issues.append(ReconciliationIssue.DOCUMENT_MISMATCH)
        next_action = "REVIEW_DOCUMENT"
        explanation = (
            "A candidate document exists in Drive but failed validation "
            "(for example, it belongs to a different parcel)."
        )

    elif any(o.state == EvidenceState.PRESENT for o in drive):
        canonical_state = EvidenceState.PRESENT
        accepted = False
        issues.append(ReconciliationIssue.UNVERIFIED_DOCUMENT)
        next_action = "VERIFY_DOCUMENT"
        explanation = "A document is present in Drive but has not been verified."

    elif any(o.state == EvidenceState.DRAFT for o in drive):
        canonical_state = EvidenceState.DRAFT
        accepted = False
        next_action = "FINALIZE_DOCUMENT"
        explanation = "Only a draft exists in Drive; drafts are not final evidence."

    elif any(o.state == EvidenceState.MISSING for o in drive):
        canonical_state = EvidenceState.MISSING
        accepted = False
        next_action = (
            "FOLLOW_UP_TITLE_POLICY"
            if evidence_type == EvidenceType.TITLE_POLICY
            else "LOCATE_OR_CREATE_DOCUMENT"
        )
        explanation = "The required document is not present in the documentary source of truth."

    else:
        canonical_state = EvidenceState.UNKNOWN
        accepted = False
        next_action = "CHECK_DRIVE"
        explanation = "No authoritative Drive observation has been recorded."

    normalized_stage = _normalize(workflow_stage)

    if (
        evidence_type == EvidenceType.TITLE_POLICY
        and accepted
        and "missing title policy" in normalized_stage
    ):
        issues.append(ReconciliationIssue.WORKFLOW_STAGE_STALE)

    # Secondary sources can add context, but they cannot override documentary truth.
    for observation in observations:
        if observation.source == SourceSystem.SPREADSHEET:
            if (
                canonical_state == EvidenceState.VERIFIED
                and observation.state == EvidenceState.MISSING
                and ReconciliationIssue.SECONDARY_SOURCE_STALE not in issues
            ):
                issues.append(ReconciliationIssue.SECONDARY_SOURCE_STALE)

        if observation.source == SourceSystem.MONDAY:
            if (
                canonical_state == EvidenceState.VERIFIED
                and observation.state == EvidenceState.MISSING
                and ReconciliationIssue.WORKFLOW_STAGE_STALE not in issues
            ):
                issues.append(ReconciliationIssue.WORKFLOW_STAGE_STALE)

        if (
            canonical_state in {EvidenceState.MISSING, EvidenceState.INVALID}
            and observation.state == EvidenceState.VERIFIED
            and observation.source != SourceSystem.DRIVE
            and ReconciliationIssue.SOURCE_DISAGREEMENT not in issues
        ):
            issues.append(ReconciliationIssue.SOURCE_DISAGREEMENT)

    return ReconciliationResult(
        evidence_type=evidence_type,
        canonical_state=canonical_state,
        accepted=accepted,
        issues=tuple(issues),
        next_action=next_action,
        explanation=explanation,
    )
