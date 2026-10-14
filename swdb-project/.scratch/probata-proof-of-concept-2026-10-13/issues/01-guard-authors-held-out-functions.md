# 01 — Guard blocks the authors' held-out functions

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Modules", table "Loop, modes and guards", row "Provider guard and workspaces"; "Testing Decisions", seam 4; "Proof-of-concept plan", A0 row and exit check; "Found while cutting the build tickets", O2 and O5; user story 77); decisions: [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md) (item 6), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) (items 2, 5)
**Time estimate:** about 2 hours

**What to build:** The provider guard keeps the DX100 authors' accelerated code out of agent-role
inputs by function name. Today it names `TDStepMAA` and `DOBFSMAA` (BFS) plus two names that exist
nowhere (`TDStepMAA2`, `BCMAA`), and it misses the held-out kernels' functions. After this ticket it
also names `PBFSMAA` (BC), `PageRankPullMAA` (PR) and `DeltaStepMAA` (SSSP) (names decided in map
18, item 6), plus `BrandesMaa`, BC's DX100 driver, which calls `PBFSMAA` (design spec O2 default).
The two dead names are gone. An agent-role input whose text names a listed function is refused
before a provider call opens. A test through the provider workspace and guard seam shows it. This
is the first build item of stage A0, and it must land before any held-out proposal.

## Acceptance

- [ ] Through the provider workspace and guard seam: an agent-role input whose text names
      `PBFSMAA` is refused with the existing authors'-code refusal, before any provider call opens.
      The same holds for `PageRankPullMAA` and `DeltaStepMAA`. Each name has its own case, so
      dropping any one name fails a test.
- [ ] `BrandesMaa` is refused too, with its own case (O2 default; see Notes). If Yan-Ru reverses
      O2, drop that case and the name.
- [ ] `TDStepMAA` and `DOBFSMAA` stay refused, each with its own case. Today only `TDStepMAA` has
      one; add the `DOBFSMAA` case.
- [ ] `TDStepMAA2` and `BCMAA` are off the guard's list. They name nothing in the authors' code, so
      no test needs them.
- [ ] The refusal fires for a name inside a source file and inside a JSON input.
- [ ] Negative controls: the baseline names stay allowed. Inputs naming `PBFS`, `Brandes`,
      `PageRankPullGS`, `DeltaStep`, `TDStep` and `DOBFS` (the fork's non-DX100 functions) pass the
      guard, so held-out proposals can still see their baselines.
- [ ] Every existing test that exercises the guard (provider guard, provider workspace, role-input
      and certification-feedback tests) passes unchanged, run with at most 2 test workers.

## Notes

- **Not in this ticket:** 34 — proof_hinting role and workspace (its narrow exception: the authors'
  code is shown only when it is the candidate artifact; hint records never reach a rewriting
  workspace). In the [evaluation tickets](../../probata-evaluation-2026-10-13/issues/): evaluation
  02 — BC held-out contract and contract proof, evaluation 03 — PR held-out contract and contract
  proof, evaluation 04 — SSSP held-out contract and contract proof (drafted with the authors' code
  hidden); evaluation 05 — LLM candidate populations (the held-out proposals this guard protects);
  evaluation 06 — Authors' code and seeded faults (the authors' code as a subject; its repairs use
  O5's narrow exception: in the evaluation only, the rewriting role may see the authors' code when
  it is the refuted candidate artifact under repair, never in a campaign).
- **A0 exit:** the design spec's A0 check is this ticket's guard test plus the smoke verdicts of
  03 — New verifiers on the Mac.
- **Order:** merged on `yanrujhou_main` before any held-out proposal (map 18 item 6). It also blocks
  31 — Five-gate drafting and the new bfs_read_offload version, whose drafting workspace must hold
  none of the guarded functions. The evaluation tickets wait for proof-of-concept 59 anyway; this
  ticket makes sure the guard is not the gap.
- **Default O2** (design spec; applies until Yan-Ru rules): the guard names `BrandesMaa`. BC's
  authors' code has this second DX100 function (the DX100 Brandes driver; it has its own `maa_*`
  calls and calls `PBFSMAA`). The existing BC scalar-only snapshot already removes it beside
  `PBFSMAA`. The design's list (map 18 item 6; spec "Modules") omits it, but user story 77 asks the
  guard to name every authors' DX100 function.
- Assumption (not decided in the map): baseline-only source snapshots for PR and SSSP proposals are
  made by the evaluation tickets that generate held-out proposals, not here. ADR 0006 asks for such
  a snapshot whenever a source file mixes the baseline with the authors' code. BFS and BC already
  have scalar-only snapshots; PR and SSSP have none. This ticket only makes the guard refuse the
  names.
- Risk: an existing record whose text still holds one of the newly listed names is now refused if
  handed to an agent role. Report any workflow that breaks; never exempt it.
- Side finding (no ticket opened): the 2026-10-03 BC proposal's candidate record and its BC
  scalar-only source snapshot name `PBFSMAA` and `BrandesMaa` in their list of removed functions;
  the 2026-10-06 BC generality source snapshot keeps both functions. Each is refused if handed to an
  agent role.
- Known limit, not fixed here: the guard matches names, so code copied under another name would
  pass. The design fixes a name list (map 18 item 6). Report any sign of copying instead of widening the
  guard silently.
