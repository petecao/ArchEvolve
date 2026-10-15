# Method19 preparation

Created: 2026-10-15 ET. Status: implementation prepared; independent review pending. **No counted run launched.**

`--staged-induction` is a prospective search policy. It keeps the exact four source/model files from reviewed `996bd62c`, the provider design pin, all-goal acceptance, and `-wp-no-filter-init`. It requires a fresh output directory, fresh no-hint baseline, mechanical frame seeds, 60 counted minutes, and an eight-minute final reserve. Development overrides, reused baselines and alternative debt/unit-first policies are refused.

One fresh provider conversation receives three equal search intervals after baseline and seeds: local/CAS/history/queue bridges; saved-pre-issue-cursor consumption induction; recovery. Tool responses report the current interval. Early-return calls resume that same conversation; a missing resumable conversation stops the run. The implementing agent supplies no concrete hints, prior hints, audit counterstates, tests or finite projections to the provider.

`best.json` remains the authoritative checked incumbent. `debt.json` holds a separate candidate with at most eight additional **total** open goals, including unit goals. A stage gets 300 counted seconds and four repair proposals; invalid/rejected proposals consume repairs, and diagnostics/checks consume clock. Edits and phase changes never reset its original age. New stages cannot enter the recovery interval. Promotion requires recovering the captured incumbent's total open-goal count before its deadlines. Expiry, exhaustion, context change or run completion rolls back. Temporary hints never become final hints without promotion.

The clock includes sleep: `mach_continuous_time` with a checked timebase on Darwin, `CLOCK_BOOTTIME` on Linux. Unsupported clocks fail closed. Driver, MCP tools and the scoped `counted_verifier.py` serialize the same implementation/timebase. Untagged or mismatched wait settlement earns no excluded time. Wall timestamps remain only for human logs, compatible queue tickets and stale-owner age; they do not determine counted durations.

The scoped runner leaves the external runner unchanged. It uses the shared queue and atomic lease protocol, accounts for occupied slots when selecting the oldest waiters, defaults to 8 GiB RSS, and bounds queue and active waits. Signals set a stop flag; cleanup confirms the tracked child tree stopped before releasing its own lease. Unconfirmed cleanup quarantines that lease with a live sentinel instead of freeing it. Existing external peers retain their own ordering policy.

Only an authoritative zero-open incumbent triggers the fresh full-function, cache-none replay with all smoke enabled. Late completion cannot count as proven. The covering-wait negative control remains a separate mandatory ticket acceptance check after a proven incumbent; `summary.proven` alone is insufficient for ticket closure. This prototype lacks production `-wp-rte/-rte-initialized @all`, so it makes no production UB/initializedness claim.

Validation: 110 prototype controls passed, including the private-lock RSS/timeout/signal/FIFO runner tests. A reproduced FIFO overtaking race was fixed before the final union. No solver or provider was launched by the controls. [Preparation evidence](../../evidence/t07-method19-preparation.json) pins reports, exact historical inputs, the seven ported paths, policy/runner sources and tests. Root or an independent agent must review clock accounting, rollback, process cleanup and pins before launch.

## Independent review fixes — 2026-10-15 ET

Review of `8af8956b` found an exited-root cleanup gap: with no initial ancestry sample, a same-group child could remain alive while cleanup returned success. The deterministic Python-only regression reproduces it. The runner now inventories and stops its original owned group even after root exit, checks birth/group identity, and refuses to target a reused/unobserved live root PID. If ancestry was never sampled, draining that group does **not** certify unseen escaped children stopped: cleanup remains unconfirmed and its lease stays quarantined.

Method19 also requires completed baseline, seed, candidate and final reports. Process failures, timeouts/RSS kills, unconfirmed cleanup, empty unit inventories, missing/partial JSON and truncated property reports fail closed. Seeds cannot publish `best.json` or launch the provider after such a failure. Scheduled-goal counts and property totals check completeness only; individual proof statuses still determine open goals. Ordinary unknown/timeout goals from a completed exit0 run are valid open obligations, not process failures.

The revised union passes **137 controls**. [Review-fix evidence](../../evidence/t07-method19-review-fixes.json) supersedes preparation-source pins at `8af8956b`; the original evidence remains historical. Independent re-review is pending. No counted run launched.
