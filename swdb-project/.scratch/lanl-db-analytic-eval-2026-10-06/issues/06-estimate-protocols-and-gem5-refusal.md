# 06 — Estimate protocols and the gem5 refusal

Created: 2026-10-06
**Type:** slice
**Status:** resolved
**Blocked by:** 04
**Spec:** `../spec.md`
**Time estimate:** 3–4 h

**What to build:** Estimate protocols freeze the estimator version and the target description's hash like other frozen protocols. Team protocols and ArchEvolve-mode commands refuse a gem5 target, a gem5-derived record, or an estimator calibrated with gem5 data, naming ADR 0013 and the offending record (D3, D10). Extensa mode is untouched.

## Acceptance

- [x] A test per refusal case.
- [x] Existing ArchEvolve-mode gem5 records still validate, as history.
- [x] Extensa gem5 campaign tests still pass.

## Answer

Resolved 2026-10-06 ET on `codex/lanl-ticket06`. Implementation `c3633cf`, followed by
merge `9ccf710` of integration `bf8ed26`; the implementation worktree was clean at
that tested source tip. All changes are inside `swdb-project/`.

- **Frozen estimate protocols:** `swdb/estimate_protocol.py` adds `settings.mode:
  estimated` to the existing public `freeze-protocol` seam. A freeze pins the version,
  portable SWDB Python bundle digest, complete target-description snapshot/hash,
  recursive target/calibration/source-configuration record hashes, input record
  identities, optional source record identities, counted ROI, threads, and optional
  exact per-input run arguments. Application evidence requires frozen arguments.
  The full persisted protocol ID is required by `estimate`.
- **Execution binding:** estimate verifies that the current implementation bundle,
  target, input, subject/candidate source identity, ROI, threads and arguments match
  the freeze. It records `protocol_sha256` and `estimator_sha256`. Non-fixture
  evidence invokes ticket05's `analytic_binding.verify_binding`; an absent verifier
  refuses application evidence. Fixture state and `contract_fixture` evidence kind
  remain paired; changing only a label cannot promote them. Historical validation
  verifies the stored freeze and estimate identities without requiring the current
  source bundle to match an old implementation.
- **ADR 0013 boundary:** new public evidence operations recursively inspect request
  and record dependencies before dispatch/write. Tests cover gem5 targets, direct
  and transitive gem5 calibration records, research estimators, simulator execution
  hidden beneath source-evidence/notes/code fields, the real public `claim` command,
  and an explicit team override under an inherited Extensa campaign. Refusals name
  ADR 0013 and the offending record/dependency chain. A `code_reading` fact may cite
  a pinned simulator source/configuration record (D18), but labeling an execution
  record as source reading does not admit it.
- **Extensa:** inherited campaign mode and explicit `--mode extensa --campaign ID`
  retain the legacy simulator route. Explicit imports receive their immutable tags
  at creation. `--mode archevolve` restores the team policy even under the campaign
  environment. Existing simulator adapters and timing-selection rules were retained.
- **Portable interface/documentation:** [analytic format and commands](../../../docs/reference/format-v0.4-analytic.md),
  `schemas/protocol.schema.json`, `schemas/estimate.schema.json`,
  `swdb/archevolve.py`, and `swdb/bfs_protocol.py`. Whole-bundle pinning is deliberately
  conservative: future model/support-code changes require fresh protocols, while
  historical protocols remain valid.

Validation through the confirmed public seams:

| Check | Result |
|---|---|
| Final protocol/import/writer/format batch | 41 passed in 335.54 s: 24 protocol cases and 17 import/writer/documentation checks |
| Final public team-claim refusal | RED proved legacy gem5 evidence could enter a team claim; GREEN: 1 passed after correcting the actual command registration |
| Earlier LLVM + Extensa campaign/selection/target + format batch | 83 passed, 2 failed in 833.94 s; both failures were repaired and passed in the final focused batch (binding diagnostic order, isolated copied-bundle history assets) |
| Extra review repair batch | 4 passed: hidden execution dependency, explicit Extensa import tags, calibration mutation, changed-code execution refusal with historical validation |
| Existing historical record store | `OK: 553 record(s) valid`, including legacy ArchEvolve gem5 records |
| Source/whitespace consistency | `git diff --check` passed; integration merge occurred after test processes completed |

No SSH, push, simulator execution or mbit10 measurement was performed by this
implementer. Real application counts/estimates require ticket05's registered-source
adapter; measured target parameters belong to ticket07. Parent owns final integrated
code review and remote evaluation.
