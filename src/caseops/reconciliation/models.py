from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class SourceSystem(str, Enum):
    DRIVE = "DRIVE"
    MONDAY = "MONDAY"
    SPREADSHEET = "SPREADSHEET"
    EMAIL = "EMAIL"
    COURT_RECORD = "COURT_RECORD"


class EvidenceType(str, Enum):
    RECORDED_JUDGMENT = "RECORDED_JUDGMENT"
    RECORDED_RELEASE = "RECORDED_RELEASE"
    PROOF_OF_DEPOSIT = "PROOF_OF_DEPOSIT"
    TITLE_POLICY = "TITLE_POLICY"
    FINAL_INVOICE = "FINAL_INVOICE"
    CLOSEOUT_MEMO = "CLOSEOUT_MEMO"


class EvidenceState(str, Enum):
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"
    DRAFT = "DRAFT"
    PRESENT = "PRESENT"
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"


class Authority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReconciliationIssue(str, Enum):
    WORKFLOW_STAGE_STALE = "WORKFLOW_STAGE_STALE"
    SECONDARY_SOURCE_STALE = "SECONDARY_SOURCE_STALE"
    DOCUMENT_MISMATCH = "DOCUMENT_MISMATCH"
    UNVERIFIED_DOCUMENT = "UNVERIFIED_DOCUMENT"
    SOURCE_DISAGREEMENT = "SOURCE_DISAGREEMENT"


@dataclass(frozen=True)
class EvidenceObservation:
    evidence_type: EvidenceType
    source: SourceSystem
    state: EvidenceState
    authority: Authority
    note: str = ""


@dataclass(frozen=True)
class ReconciliationResult:
    evidence_type: EvidenceType
    canonical_state: EvidenceState
    accepted: bool
    issues: Tuple[ReconciliationIssue, ...]
    next_action: str
    explanation: str
