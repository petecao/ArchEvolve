# Probata closeout code review

Reviewed: 2026-10-15 ET. Baseline `150930b4be39526e6eeefd881987dba1c6d6e4d3`;
frozen tip `53471f7f942d2c1ae7456d4fd08b776777006447`.
Command: `git diff BASE...TIP`. The two axes ran in parallel, read-only subagents.
[Commit list](closeout-review-commits-20261015.txt). No reviewer launched a solver,
provider or remote evaluation. Coordinator integration controls are separate.

## Standards

One minor documentation issue; no confirmed must-fix standards violation.

- **P3: stale admission description.** `swdb/cbmc_translator.py:1079` says
  “production adapters and runtime-check refuse these jobs.” Checked CBMC
  entry-window admission exists at `cbmc_adapter.py:247-257`. Describe unchecked
  route refusal and independent source certificates required for admission.

Possible duplicated AST helpers and source-view bookkeeping are heuristic
observations only. Their accepted grammars and content-hash boundaries differ;
no speculative consolidation is requested. The recovery helper preserves tracked
and untracked source, verifies the pushed archive tag, and emits review-only
cleanup commands with expected-tip leases. Actual pruning still requires fresh
use checks. Refresh resume, release unfinished claims, and stop the heartbeat.
[Full standards notes](closeout-standards-review-20261015.md).

## Spec

No new actionable defect found in the inspected runtime changes.

- **07:** Acceptance requires “every goal proven within 60 minutes” and final smoke /
  covering-wait controls (ticket07:29–47). Method19 is unproven; method20 unlaunched.
- **24/25:** “One fixture per construct group” requires actual safe/seeded outcomes
  (ticket24:15); “every [member] contract” requires its body proof (ticket25:15–19).
  Narrow class/copy/owner/pipeline results leave declared construct, receiver-origin
  and allocation-lifetime work open.
- **27/36:** The complete agreement/capacity matrix (ticket27:16–23), immutable setup,
  fresh per-property reading and final freeze (ticket36:11–21,35–59) remain open.

No unsolicited scope or held-out-kernel implementation was identified. Inspected
source-view sequencing, pointer domains, imported-summary binding, header provenance,
member lifetimes, fresh verdict reader and diagnostic-only probing retain their
conservative refusals. No actual false proof was reproduced or claimed.

Inherited hardening observation: WP setup trusts method flags for `-wp-rte` rather
than independently requiring it. This predates the baseline; current actual methods
include it. Record a mandatory review item under36 before final method freeze;
no production-safety claim is justified by method20's prototype flags.

Standards: 1 minor finding. Spec: 0 new defects, with known partial acceptance and one
inherited freeze-review item. Both axes require preserving open ticket boundaries.

## Disposition

One implementation subagent handles the stale comment, explicit inherited freeze
check, five claim releases and tracker refresh. No new feature or solver campaign
is authorized by this closeout. Final source/fix commits and validation are recorded
in the closeout completion metadata and handoff; historical proof pins stay exact.
