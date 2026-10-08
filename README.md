# CaseOps

**CaseOps** is a portfolio project that models operational case readiness from fragmented evidence.

The public repository uses **synthetic data only**. It contains no client names, owner names, legal documents, internal identifiers, private links, or confidential case data.

## Goal

Answer four questions for each case:

1. What is the documentary state?
2. What is the operational state?
3. What is blocking progress?
4. What should happen next?

## V0 scope

The first version focuses on a synthetic property-case workflow inspired by a real legal-operations process.

### Documentary state

- `INCOMPLETE`
- `READY_FOR_CLOSEOUT`
- `COMPLETE`

### Operational state

- `AWAITING_TITLE_POLICY`
- `ON_HOLD`
- `PENDING_APPROVAL`
- `ACTIVE`
- `CLOSED`

## Source hierarchy

1. Document evidence is authoritative for document existence/state.
2. Workflow comments/statuses are authoritative for current operational context.
3. Spreadsheets are secondary context and may be stale.
4. Draft documents do not count as final evidence.

## Run tests

```bash
python -m pytest
```

## Current milestone

V0 implements a deterministic parcel-state engine and tests six synthetic scenarios derived from patterns observed in a real operational workflow.
