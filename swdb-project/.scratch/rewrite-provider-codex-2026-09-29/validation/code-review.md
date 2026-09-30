# Final code review — guarded rewrite providers and ArchEvolve handoff

Updated: 2026-09-29 23:20 ET
State: complete; both independent rechecks and final public CLI regression passed

The two independent axes reviewed the owned changes under `swdb-project/`.
The originating specs are [provider](../spec.md) and
[handoff](../../archevolve-handoff-2026-09-29/spec.md). Human-owned tickets 01/07
and Peter-dependent tickets 05/06 keep their original ownership.

Base: `65c84fde73b34935d515edfb43c3bc44d7a22153`.
Whole-diff review head: `40c5011da06035593e209b10ff1e1a0710520ae0`.
Repair recheck head: `8889e175d551b5270e8b2a59d1747eefe63c69e5`.

```sh
git diff 65c84fde73b34935d515edfb43c3bc44d7a22153...40c5011da06035593e209b10ff1e1a0710520ae0
git log 65c84fde73b34935d515edfb43c3bc44d7a22153..40c5011da06035593e209b10ff1e1a0710520ae0 --oneline
git diff 40c5011da06035593e209b10ff1e1a0710520ae0...8889e175d551b5270e8b2a59d1747eefe63c69e5
```

## Standards

Documented-standard violations: **0**. The initial review found one **P3 possible
Duplicated Code** judgement call: initial submission and unavailable-provider
retry repeated the first-candidate apply/check/verify/diff/hash/persist sequence.
The repair extracts [`_persist_initial_candidate`](../../../swdb/workflow.py)
and uses it from both callers. Candidate identity, producer, protections,
verification and persistence order are preserved; states and budgets remain in
the callers. Patch-only submission retains the original conditional code-change
check.

Independent recheck confirmed the finding resolved at `8889e175`, with no new
documented-standard violation or actionable Fowler-baseline smell. Verified
workflow blob: `4de3deb6703e6d5807fa4d7d58285ea6ad897671`.

**Standards: 1 original judgement call, 1 resolved, 0 remaining. Worst remaining: None.**

## Spec

No missing or partial agent-owned requirement, scope creep, or incorrectly
implemented requirement was found in the whole diff. The review checked pinned
providers and provenance, repair identity/refunds, workspace/diff collection,
guard/audit behavior, campaign/smoke wiring, scalar derivation and handoff.

Read-only identity checks confirmed seven TDStep statement bindings and eight
access patterns with valid steps, unchanged vendored source/protocol files,
and the frozen audit blob. T17 gains remain scoped to simulated author-code reuse,
source0 and one declared deterministic repetition. Claude's retained OAuth failure
is a permitted ticket10 outcome. Human/Peter prerequisites remain distinguished
from completed agent work.

Independent recheck of the helper extraction found no behavior/spec regression;
candidate scope, source verification, diff hashing and caller budgets/outcomes
remain unchanged.

**Spec: 0 findings. Worst: None.**

## Validation and evidence boundaries

| Check | Source | Result |
|---|---|---|
| Linux A10 complete workspace collection | `a7cca27`; node1 generation 490 | 443 passed, 1402.63s |
| Linux A11 final audit grammar | `3a73c6c`; node0 generation 429 | 216 passed, 695.71s; 6/6 expected retained-log decisions |
| Local final audit grammar | audit blob `62fe75f4` | 154 passed, 321.82s |
| Independent audit grammar | Same audit blob | 114 passed; 76 refusals and 38 admissions |
| Post-review workflow public CLI regression | `8889e175`; workflow blob `4de3deb` | 45 passed, 569 deselected, 673.40s; no failures or skips |
| Public catalog and closure documentation | Final staged closure | 352 records valid; 125 local Markdown links resolve; staged/unstaged whitespace checks pass |

The workflow selection exercises existing patch and both-provider submissions,
initial usage-limit retry, mismatch/refund behavior, full-file output, immutable
large contexts and repair. No implementation-mirroring tests were added.
The local ignored log and XML hashes are recorded in the evidence metadata.
Pytest's summary reports 673.40s; the XML suite time is 671.582s.

The full Mac regression had 2798 passes and 31 skips, began while the tree was
evolving, and is not a full exact-final-head validation. Focused and Linux checks
carry their own source identities. Re-auditing historical raw event logs is not
rerunning providers under the latest guard. Codex DX100 A1 stays refused by the
current parser; A2 is the current successful admission. Native DX100 A2 correctness
uses a tiny graph and source0/3/8 with one trial each, with no gain claim. Guard
residuals and narrow supervisor controls do not establish universal hostile-process
isolation or exhaustive program semantics. Raw output remains on mbit10.

Metadata, guard receipts, source identities and raw-artifact hashes are in
[guarded provider evidence](../../../docs/evidence/guarded-rewrite-providers-20260929-a1.yaml).

Standards: 0 remaining (1 resolved); Spec: 0. Worst remaining in each axis: None.
