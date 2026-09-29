# 04 — Repairs keep their provider; usage limits don't consume repairs

Created: 2026-09-29
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** A repair always uses the kind, model, and effort of the proposal's first attempt. A
ChatGPT usage-limit error is recorded as `provider_unavailable` instead of a failed rewrite.
The new time caps apply.

## Acceptance

- [x] `swdb repair` with a different kind, model, or effort than the first attempt is refused; with the same one it proceeds.
- [x] A fixture that reports a usage-limit error produces the outcome `provider_unavailable`; the repair count is unchanged and the proposal can be retried.
- [x] Per-call time is capped at 1800 s with a 1200 s default; the total stays capped at 3600 s.

## Answer

Updated: 2026-09-29.

Repairs match the first actual provider's resolved kind, model and effort before starting
an attempt. A supplied-patch proposal establishes that identity at its first provider repair.
Historical real receipts without pins remain valid and reusable, but cannot be repaired
because matching an unknown historical model/effort cannot be established. Usage-limit
errors produce `provider_unavailable` and a nonzero CLI exit without consuming a repair;
time spent is retained. `swdb repair <proposal-id>` retries an unavailable initial session,
which has no evaluation yet. Repeated quota errors retain separate raw folders and attempts.
Forbidden audited actions take precedence over a simultaneous usage-limit error.

Per-call time defaults to 1200 s and caps at 1800 s; total provider time caps at 3600 s.
Each attempt records its actual selected configuration; later repair options do not overwrite
that evidence with the earlier configuration.

Validation: all **13** public provider-pin tests passed; the targeted quota/default-kind
checks passed **3/3**, including a successful initial retry and an evaluation-triggered retry
that consumes one repair only after the provider becomes available. The provider-kind change
is refused without adding an attempt. Existing bounded rewrite/repair checks passed in the
**73-test** legacy suite.

Context: `swdb/workflow.py`, `swdb/cli.py`, `swdb/rewrite.py`, `tests/test_provider_pins.py`.
