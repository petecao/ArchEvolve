# Lessons from agent sessions

Updated: 2026-10-12 ET. Applies to SWDB work when the named trigger occurs.
These are reviewable lessons, not permanent additions to the scientific spec.
Rationale, review dates and retirement evidence live in the
[lesson register](../../swdb-project/docs/agents/learned-rule-register.md).

## LR-01 — Ticket completion

Before implementation, identify the deliverable and its actual acceptance criteria.
A report may finish with a supported negative result. Finish everything the criteria
need inside the ticket, including stale tests, fixture fixes and verification it
uncovers. Record side findings in the ticket's answer; open a new ticket only when
Yan-Ru asks for one.

## LR-02 — Scaling a numerical study

Before scaling a numerical agreement study, demonstrate one real, prospectively
recorded estimate/outcome pair admitted by the current study's auditor. Follow
the current spec and execution guards; record missing premises as unknown.

## LR-03 — Component tests

Verify the selected interpreter and required tools (including pytest-xdist) before a
costly test run. Use the existing record-closure helper for component fixtures,
preserving their validation and assertions. Use the full catalog only when catalog
integration is the thing being tested. After a run with mass failures, reproduce
one failing test alone and name the cause before any rerun.

## LR-04 — Repeated mechanical mistakes

Inspect existing checks first. Turn repeated syntactic, binding or file-location
mistakes into deterministic checks; verify the check runs in the normal workflow.
Keep judgement calls in reviewer guidance.

## LR-05 — Session state

Keep one short current-state section in the effort's resume document: checkpoint,
blocker and next action. Read ticket files for current statuses. Link to historical
evidence instead of copying it into every tracker or automation prompt.

## LR-06 — Generated output

Before large output, record its destination mount, storage budget and remaining
readers, including output a tool writes outside its declared temp folder. Follow the host's storage rules. After the last reader, remove only
authorized disposable output with verified identity, size/hash and no-use evidence.
Retain original bodies while future verification needs their contents.

## LR-07 — Long-running jobs

Size parallel workers to the memory the job may use (Mac: check `memory_pressure`;
mbit10 lane: at most 6 test workers). Write results incrementally (`--report-log`)
so a timeout or kill keeps them. For any job or ticket set expected to run past
30 minutes, schedule a heartbeat before starting it and post a status table to
Yan-Ru every 30 minutes, unprompted, until the work ends. Each table shows every
running item with its progress, change since the last report, health, and ETA.
Check progress from outside the runner; a counter that has not moved since the
last report is a finding, and the report says what is being done about it. If a
heartbeat was missed, the next report states the gap.
