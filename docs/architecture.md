# Architecture — V0

CaseOps separates documentary truth from operational context.

```text
Document evidence ──────┐
                        ├──> Parcel State Engine ──> State / Blocker / Next Action
Workflow context ───────┘
```

## Documentary truth

Documentary state is computed from final, verified evidence.

A draft closeout memo is intentionally **not** equivalent to a final closeout memo.

## Operational context

Operational state may depend on:

- current workflow stage;
- hold status;
- latest meaningful workflow comment;
- approval status.

A case can therefore be documentary `COMPLETE` while operationally `PENDING_APPROVAL`.

## Data quality

CaseOps detects stale workflow state. Example:

```text
Verified Title Policy = true
Workflow stage = Missing Title Policy
```

The engine preserves documentary truth and raises a data-quality issue instead of overwriting evidence.
