# Lessons from agent sessions

Updated: 2026-10-16 ET. Applies when the named trigger occurs.
Rationale and retirement criteria live in the
[lesson register](../../swdb-project/docs/agents/learned-rule-register.md).

## LR-01 — Ticket completion and evidence

Identify the deliverable and acceptance criteria before work. Complete necessary
fixes and verification within that ticket. A negative result closes a report only
when its criteria allow it. Size evidence to the ticket type: a spike records each
verdict with its inputs, hashes and run folder; production code adds review and
retained evidence. Distinguish actual runs from offline checks. Record side
findings; create new tickets only at Yan-Ru's request.

## LR-02 — Scaling a numerical study

Before scaling a numerical agreement study, demonstrate one real, prospectively
recorded estimate/outcome pair admitted by its auditor. Preserve current admission
requirements; record missing premises as unknown.

## LR-03 — Test selection and preflight

Before costly tests, verify the selected interpreter, required tools and watchdog
access. Select explicit test profiles or node lists; use markers when available.
Use record-closure fixtures for components; reserve the full catalog for catalog
integration. Validate report readers and common assertions cheaply before real
verifier runs, preserving scientific acceptance criteria.

## LR-04 — Recurring errors, reruns and review

Inspect existing checks first. Extend deterministic checks for recurring mechanical
errors and wire them into the normal workflow. Keep judgment in reviewer guidance.
Before a broad rerun, isolate representative failures and identify their causes.
Review once per method version, before launch; a change outside the verdict path
is reviewed in its diff.

## LR-05 — Current state and pause

Ticket files are authoritative. Keep one current resume section of at most 30
lines: checkpoint, active owners/jobs, blocker and next action. Move history into
dated evidence files and link them. At pause, release unfinished claims, record
resume commands and stop the effort's heartbeat.

## LR-06 — Output lifecycle

Before large output, record its destination mount, storage budget and remaining
readers, including files written outside declared temp folders. Follow host
storage rules. Remove authorized disposable output only after verifying identity
and no remaining use. Retain source and raw evidence needed for audit or resumption.

## LR-07 — Guarded jobs and progress

Use a committed runner when available; otherwise record the exact guarded command.
Enforce shared verifier slots, RSS caps, timeouts and incremental structured results.
Size workers to memory: check Mac `memory_pressure`; use at most six test workers
per leased mbit10 lane. Before an effort exceeding 30 minutes, schedule a status
table every 30 minutes: item, progress, change, health and ETA (unknown if unmeasured).
Check logs and processes independently; investigate unexplained lack of progress
and report missed intervals.

## LR-08 — Minimal branches and worktrees

Default to zero new remote branches. When isolation requires one, use at most one
remote integration branch per active effort beyond `yanrujhou_main`. Keep ticket
and subagent branches local. Publish evaluation commits through `yanrujhou_main`
or that integration ref; evaluate exact SHAs in detached checkouts. Reuse suitable
idle worktrees. After merges into `yanrujhou_main` and at pause, apply the
[branch cleanup policy](miscellaneous.md), preserving recovery and active readers.
Run ticket work in its own worktree. In the shared primary checkout, commit only
your own paths and leave other sessions' uncommitted work and stash entries in place.

## LR-09 — Check the target first

Before proving, optimizing or measuring against a specification, contract, oracle
or stand-in, run it on concrete cases: every precondition satisfiable, every
postcondition true on known-good runs. Fix a refuted target first and flag the fix
to Yan-Ru for sign-off.

## LR-10 — Convergence checkpoint

Track the measured distance to the acceptance criterion for each attempt. After
three attempts without a step change, or a quarter of the time box, stop and send
Yan-Ru the trend, the premise most likely wrong, and two to four options with a
recommendation. Start a new method version only from a measured cause.
