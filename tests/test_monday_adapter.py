from caseops.adapters.monday import adapt_monday_item
from caseops.reconciliation.models import (
    Authority,
    EvidenceState,
    EvidenceType,
    SourceSystem,
)


def synthetic_item(*, item_id, name, stage, case_status, group):
    return {
        "id": item_id,
        "name": name,
        "url": f"https://example.test/items/{item_id}",
        "column_values": {
            "status": stage,
            "color_mm442gwk": case_status,
            "text_mm2mttm5": "CASE-001",
            "text_mm2dy085": "Synthetic Client",
            "text_mm2ddd74": "",
            "text_mm2dkhs5": "",
            "link_mm57dd7p": "",
        },
        "group": {
            "id": "synthetic-group",
            "title": group,
        },
    }


def test_missing_title_policy_stage_becomes_source_observation():
    context = adapt_monday_item(
        synthetic_item(
            item_id="1001",
            name="Synthetic Parcel A",
            stage="7. Missing Title Policy",
            case_status="Active",
            group="Active cases",
        ),
        updates=[
            {
                "id": "u1",
                "text_body": "Only the title policy remains pending.",
                "created_at": "2026-05-28T14:17:48.000Z",
            }
        ],
    )

    assert context.stage == "7. Missing Title Policy"
    assert context.case_status == "Active"
    assert context.latest_comment == "Only the title policy remains pending."

    assert len(context.evidence_observations) == 1
    observation = context.evidence_observations[0]

    assert observation.evidence_type == EvidenceType.TITLE_POLICY
    assert observation.source == SourceSystem.MONDAY
    assert observation.state == EvidenceState.MISSING
    assert observation.authority == Authority.MEDIUM


def test_latest_comment_is_selected_by_timestamp():
    context = adapt_monday_item(
        synthetic_item(
            item_id="1002",
            name="Synthetic Parcel B",
            stage="7. Missing Title Policy",
            case_status="On hold",
            group="Cases on hold",
        ),
        updates=[
            {
                "id": "older",
                "text_body": "Only the title policy remains pending.",
                "created_at": "2026-05-28T14:19:03.000Z",
            },
            {
                "id": "newer",
                "text_body": "HOLD REMINDERS. NOTE FROM APPROVER.",
                "created_at": "2026-07-01T21:49:28.000Z",
            },
        ],
    )

    assert context.case_status == "On hold"
    assert context.group == "Cases on hold"
    assert context.latest_comment == "HOLD REMINDERS. NOTE FROM APPROVER."
    assert context.latest_comment_at == "2026-07-01T21:49:28.000Z"


def test_adapter_does_not_infer_document_truth_from_closed_stage():
    context = adapt_monday_item(
        synthetic_item(
            item_id="1003",
            name="Synthetic Parcel C",
            stage="8. Closed",
            case_status="Active",
            group="Active cases",
        )
    )

    # Monday operational state is preserved, but no documentary evidence
    # is fabricated from the fact that the workflow stage says Closed.
    assert context.stage == "8. Closed"
    assert context.case_status == "Active"
    assert context.evidence_observations == ()


def test_empty_updates_do_not_break_adapter():
    context = adapt_monday_item(
        synthetic_item(
            item_id="1004",
            name="Synthetic Parcel D",
            stage="6. Closing & Release",
            case_status="Active",
            group="Active cases",
        ),
        updates=[],
    )

    assert context.latest_comment == ""
    assert context.latest_comment_at == ""
