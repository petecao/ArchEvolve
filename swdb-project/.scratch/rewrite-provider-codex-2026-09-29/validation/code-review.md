# Final code review — guarded rewrite providers and ArchEvolve handoff

Updated: 2026-09-30 ET
State: complete; the 2026-09-30 spec re-review findings are repaired and validated on Linux (A12)

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

## Spec re-review (2026-09-30 ET)

A second, independent spec-axis review of `65c84fde..ec40b08`, split into four
areas (pins/records, command lines/guard, workspace/diff, audit/tests), found
issues the first review missed. The P1 and the P2 header and repair findings were
confirmed by direct reproduction before repair. Repairs are in `42526ad`.

| Sev | Finding | Outcome |
|---|---|---|
| P1 | Brace and glob shell operands skipped the audit: `cat {..,.}/provider-home/au?h.json` passed and read the login copy | Fixed: every operand is brace-expanded; wildcard roots stay in the workspace; `cd` targets are literal; Claude Glob braces expanded |
| P2 | DX100 required-operation headers (`gem5/m5ops.h`) never matched the snapshot's `include/gem5/m5ops.h`, so those proposals failed | Fixed: include-root suffix match; DX100 public test |
| P2 | A repair could cross between a real provider and a fixture emulating it | Fixed: classification must match |
| P2 | Codex tool commands could connect on 443 through io_uring or TCP Fast Open without a traced `connect()` | Fixed for Codex by seccomp; IP-level API matching recorded as residual risk |
| P2 | Network check was a short denylist (`pip3.12`, `npm i`, `npx`, `uvx`, `go mod download` passed) | Fixed: package managers refused outright; Python `-m` offline allowlist |
| P3 | Thread/memory caps polled, not kernel-enforced | Recorded in `limit_enforcement`; inner tool commands get `RLIMIT_AS` |
| P3 | Provider home had no size cap | Fixed: counted in the 5 GiB cap |
| P3 | Tool copies or hard links of the login survived cleanup | Fixed: removed and listed |
| P3 | Code-mode-host watchdog exemption could be spoofed by `exec` | Fixed: first observed instance only |
| P3 | A fixture could run an installed real CLI unguarded | Fixed: refused |
| P3 | Real login copied before the non-Linux refusal; spike copy ordering | Fixed |
| P3 | Editable patterns admitted build outputs | Fixed: build outputs classified first |
| P3 | Header fallback containment check was ineffective | Fixed |
| P3 | Empty or terminal-less logs passed; unknown Claude blocks ignored; missing log path not fail-closed | Fixed |
| P3 | Usage-limit scan could discard a successful session | Fixed: failed sessions only |
| P3 | Provider block mixed attempts | Fixed: replaced per attempt |
| P3 | Codex effort literal | Fixed: from the pin |
| P3 | Campaign could not reuse a candidate made after a usage-limit retry | Fixed |
| P3 | Extra files add nothing; prompt points to proposal file; "unknown" model shown by absence; default total 3600 s | Spec clarified (deliberate designs) |
| P3 | Repair mismatch tested only on retry; guard test via spike script | Test added for classification; public-submit guard tests already exist |
| P3 | Scope: SPARTA note in `view.py`, mbit10 per-run source hash, T17 scripts | No change: owned by other work and harmless |

Validation:

| Check | Source | Result |
|---|---|---|
| Mac workspace file | before final CLI-detection narrowing | 656 passed, 1502.68 s |
| Mac pins + campaign reuse | same | 49 passed, 479.05 s |
| Mac stream + pins after narrowing | `42526ad` tree | 27 passed, 453.63 s |
| Linux A12 guard/pins/workspace selection | `42526ad`; node0 generation 430; load 1.11 | 238 passed, 1672.04 s |
| Retained-log re-audit | same checkout | 6/6 decisions match; completed-mode passes for the three completed logs |
| Real Codex toy under the new seccomp filter | same lane job | Passed in 32.2 s; guard, supervisor filter and login deletion pass |

Hashes are in the `spec_rereview_validation` block of the
[guarded provider evidence](../../../docs/evidence/guarded-rewrite-providers-20260929-a1.yaml).
The real Claude CLI was not rerun (its OAuth login had expired at A2); the new
Claude-side changes are covered by fixtures and the inner-layer Linux tests.
