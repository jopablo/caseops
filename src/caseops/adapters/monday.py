from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Tuple

from caseops.reconciliation.models import (
    Authority,
    EvidenceObservation,
    EvidenceState,
    EvidenceType,
    SourceSystem,
)


# Board-specific details live here instead of leaking through the rest of CaseOps.
STAGE_COLUMN_ID = "status"
CASE_STATUS_COLUMN_ID = "color_mm442gwk"
CAUSE_COLUMN_ID = "text_mm2mttm5"
CLIENT_COLUMN_ID = "text_mm2dy085"
MATTER_COLUMN_ID = "text_mm2ddd74"
PARCEL_COLUMN_ID = "text_mm2dkhs5"
FOLDER_LINK_COLUMN_ID = "link_mm57dd7p"


@dataclass(frozen=True)
class MondayUpdate:
    update_id: str
    text: str
    created_at: str


@dataclass(frozen=True)
class MondayCaseContext:
    item_id: str
    item_name: str
    item_url: str
    stage: str
    case_status: str
    group: str
    cause: str
    client: str
    matter: str
    parcel: str
    folder_link: str
    latest_comment: str
    latest_comment_at: str
    evidence_observations: Tuple[EvidenceObservation, ...]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _latest_meaningful_update(updates: Iterable[dict[str, Any]]) -> MondayUpdate | None:
    candidates = []

    for update in updates:
        text = _text(update.get("text_body"))
        if not text:
            continue

        candidates.append(
            MondayUpdate(
                update_id=_text(update.get("id")),
                text=text,
                created_at=_text(update.get("created_at")),
            )
        )

    if not candidates:
        return None

    # ISO-8601 timestamps sort chronologically as strings when consistently formatted.
    return max(candidates, key=lambda update: update.created_at)


def _workflow_claims(stage: str) -> tuple[EvidenceObservation, ...]:
    normalized = " ".join(stage.lower().split())
    observations: list[EvidenceObservation] = []

    if "missing title policy" in normalized:
        observations.append(
            EvidenceObservation(
                evidence_type=EvidenceType.TITLE_POLICY,
                source=SourceSystem.MONDAY,
                state=EvidenceState.MISSING,
                authority=Authority.MEDIUM,
                note="Monday workflow stage explicitly claims the Title Policy is missing.",
            )
        )

    return tuple(observations)


def adapt_monday_item(
    item: dict[str, Any],
    updates: Iterable[dict[str, Any]] = (),
) -> MondayCaseContext:
    columns = item.get("column_values") or {}
    group = item.get("group") or {}
    latest = _latest_meaningful_update(updates)

    stage = _text(columns.get(STAGE_COLUMN_ID))

    return MondayCaseContext(
        item_id=_text(item.get("id")),
        item_name=_text(item.get("name")),
        item_url=_text(item.get("url")),
        stage=stage,
        case_status=_text(columns.get(CASE_STATUS_COLUMN_ID)),
        group=_text(group.get("title")),
        cause=_text(columns.get(CAUSE_COLUMN_ID)),
        client=_text(columns.get(CLIENT_COLUMN_ID)),
        matter=_text(columns.get(MATTER_COLUMN_ID)),
        parcel=_text(columns.get(PARCEL_COLUMN_ID)),
        folder_link=_text(columns.get(FOLDER_LINK_COLUMN_ID)),
        latest_comment=latest.text if latest else "",
        latest_comment_at=latest.created_at if latest else "",
        evidence_observations=_workflow_claims(stage),
    )
