# 75 — Certify native a8's best: a TDStep frontier-staging contract, promotion and team re-evaluation

Created: 2026-10-05 11:40 ET (from ticket 56's a8 result; Yan-Ru: "certify it", 2026-10-05)
Updated: 2026-10-05 19:20 ET (addendum: native certify 1.5 record and re-promotion citing it); 2026-10-05 18:30 ET (addendum: review attribution and re-promotion, spec review C1, C3); 2026-10-05 17:20 ET (tracker hygiene, code review: Blocked by line); 2026-10-05 16:55 ET (legacy-lease audit, code review S13); 2026-10-05 15:00 ET (resolved); 2026-10-05 12:25 ET (decisions revised after the independent review, before any
certification record or run)
**Type:** slice
**Status:** resolved
**Blocked by:** 56, 76
**Spec:** `../spec.md`; [design decisions](../extensa-design-2026-10-03.md) D9; ADR 0007, 0008, 0010;
[15](15-library-tiers-and-entry-promotion.md), [43](43-promote-bc-contract.md), [48](48-mode-tags-and-team-boundary.md),
[51](51-seed-extensa-families.md), [56](56-native-campaign-target.md), [70](70-certification-isolation.md),
[72](72-native-upstream-two-level-trials.md)

**What to build:** native campaign a8's uncertified uniform best `extensa-native-bfs-20261005-a8.it1.kronecker.a0`
(artifact `7acca955…`; 1.457 [1.450, 1.472] against the fork scalar TDStep under `ci_width.v2`) becomes a
certified candidate artifact of a new rewrite contract. The contract is certified on the exact a8 tree,
independently reviewed, promoted to shared, and the candidate artifact is promoted and re-evaluated once under a
team protocol for its workload class (ticket 48).

Every decision here is **agent-decided under Yan-Ru's 2026-10-05 delegation ("certify it"); revisable.**

## The a8 best patch (analysis)

The provider patch (`provider.patch`, sha256 `be754a79…`, from the a8 campaign store on mbit10, read only) applies
with `git apply --recount` to snapshot `bfs-dx100-scalar-only-20260929-a1.source` and reproduces artifact
`7acca955…` byte for byte. Its clean `-p1` form is `library/native/bfs-tdstep-frontier-staging.patch`. It changes
only the body of `TDStep` in `benchmarks/gapbs/src/bfs.cc`:

1. **Frontier staging** (`frontier_staging`). The worksharing loop runs over batches of 16 window positions
   (`schedule(static)`). Per batch it copies the frontier vertex IDs into `staged_vertices[16]`, then gathers
   `offsets[u]` and `offsets[u + 1]` into `staged_begin[16]` and `staged_end[16]` (both copies under `omp simd`).
   The edge loop of each lane reads the staged vertex and bounds. This is the `gather_stream` reference
   semantics of `operation.gather_staging_executor` (ticket 51) with one row of `staged_count` lanes, written
   inline; the executor is not called, so the contract cites its reference semantics and does not depend on the
   (experimental) executor.
   - Legality: every window position is staged and expanded exactly once, including the final partial batch
     (`staged_count = min(remaining, 16)`); each lane expands the row of the vertex it claims with; the staging
     sources (frontier window, row offsets, neighbor array) are not written during the step, so a staged copy
     cannot go stale and the staging loops carry no cross-iteration dependence.
2. **Post-claim store elimination** (`post_claim_store_elimination`). `parent[v] = u` after a successful
   `compare_and_swap(parent[v], curr_val, u)` is removed. It is redundant if (sufficient, not necessary):
   - (i) it follows the successful claim on the same lvalue with the same value `u`, with no reassignment between;
   - (ii) the claim writes `new_val` on success as one atomic read-modify-write (`platform_atomics.h`:
     `__sync_bool_compare_and_swap`, a full barrier);
   - (iii) per location, within the step the only writes to `parent[v]` are claims on `parent[v]` with a negative
     expected value and (in the original) the winning thread's own store of the same value; claimed values are
     vertex IDs of at least 0, so the claimed state is absorbing and no other value can intervene;
   - (iv) the plain store orders nothing (no release or flush semantics); `parent[v]` reaches later steps through
     the claim and the implicit barrier and flush at the end of the OpenMP parallel region.
   Under (i)–(iv) the store writes the value the location already holds. The argument is relative to the
   original program under GCC's de facto model (aligned 32-bit plain loads and stores are single-copy atomic; none
   invented): the plain read `curr_val = parent[v]` races with other threads' claims in both programs (undefined
   in ISO C++11). The rewrite removes one such race (the plain store) and adds none.
3. Not a transformation: the edge index changes from `int` to `SGOffset`, but `SGOffset` is `int32_t` in the DX100
   fork (`graph.h` line 90), so no type changes.

## Decisions

- **Contract** `contract.bfs_tdstep_frontier_staging` (`library/rewrite_contracts/bfs_tdstep_frontier_staging.yaml`),
  experimental origin the a8 campaign and candidate. Pattern key in ticket 55 chain form: frontier stream; offsets
  through the frontier; neighbors through the offsets (ranged); parent compare-and-swap at the end of the chain.
  Strategies `packing` and `loop_tiling` (the staging); the store elimination has no strategy effect (noted).
  Clauses S1 (coverage), S2 (lane correspondence, formal half: the `gather_stream` reference pin), S3 (frame),
  C1 (claim and push stay at the seams), C2 (store elimination, (i)–(iv)); preservation obligations
  `frontier_size_equality` and `once_enqueue`; correctness check BFSVerifier. Knob `frontier_batch`, default 16,
  range 1–4096, bound to S1.
- **Native-CPU certification profile** (`library/profiles/native_bfs_tdstep.yaml`, certify command 1.4,
  `swdb/certification_native.py`): builds `-O3` (the frozen native flags) and `-O1 -g`, threads 1 and 4, the five
  certification graphs, source 0 (pinned; `--sources` cannot override it); ticket 70's isolation (one candidate
  object per build, evaluator `main`, records on a harness descriptor, faults only in
  `library/native/certification/seams.cc`, harness scan); before any build, certify checks the rewrite scope (every
  byte outside the TDStep definition unchanged, the region exactly one function definition with the snapshot's
  signature) and the scan refuses authored preprocessor directives other than `#pragma omp` (the seam macros
  exist only in certification builds); execution witness: claims and pushes through the seams.
- **Negative controls**, each a fault in the separately compiled seam object that the candidate's translation
  unit cannot see, from source 0 on the two-level graph (except `partial_batch_dropped`):

  | Control | Emulates | Clause | Named check |
  |---|---|---|---|
  | `claim_without_write` | the first successful claim leaves `parent[v]` unchanged (C2 (ii) false) | C2 | `verifier` |
  | `partial_batch_dropped` | in every step with more than 16 window positions, the final partial batch is never expanded (graph `staging-tail-17`: one full batch plus a one-vertex tail with a unique leaf) | S1, `frontier_size_equality` | `frontier_size_equality` |
  | `stale_row_offset` | in the first step, vertex u is expanded over vertex u + 1's row while claiming as u | S2 | `verifier` |
  | `forged_frontier` | the first push of the run is pushed twice | C1, `once_enqueue` | `duplicate_frontier` |

  - `claim_without_write` and `forged_frontier` act inside seams the candidate calls; a candidate that bypasses a
    seam leaves the control alive. `claim_without_write` also discriminates: a variant that keeps the post-claim
    store survives it (test).
  - The two staging controls act on the step's inputs at the evaluator's frontier hook (inserted before DOBFS's
    protected print, outside the rewritten function). They show that the checks catch each bug class whatever the
    candidate; they say nothing about how a candidate stages. For a candidate, S1 and S2 are discharged by the 20
    positive cells, and tests show that real spellings of both bugs fail those cells.
  - S3 (frame) has no local test: discharge `assumed`, owned by the promotion reviewer per candidate (for a8, the
    review read it from code). C1's spelling is also checked by the reviewer per candidate.
- **Binding to the a8 candidate.** `swdb certify --snapshot … --patch … --candidate-record FILE` reads the a8
  candidate record in place and binds only if its source snapshot matches and its artifact sha256 equals the
  patched tree's; the certification's `candidate.id` is then the a8 candidate.

## Pre-registration: team re-evaluation (written before any run)

- **Team protocol** `bfs-native-scale22-ci-team-20261005` (untagged, ArchEvolve mode): the settings of a8's frozen
  `fork_scalar_tdstep` protocol exactly (evaluator v3, compiled verifier v2, 20 paired repetitions, 1 thread,
  `-O3` native flags, `native_paired.v1`, circular block bootstrap with blocks of 4, 2000 resamples, seed 20260925,
  gate `relative_ci_width.v1` at most 0.05, minimum speedup 1.05), both scale-22 workloads, lane node 1. No
  current team protocol covers scale 22 or the CI-width rule; this one is new.
- **Stores.** The a8 candidate and proposal records are imported byte for byte from the a8 campaign store into
  `records/` (still tagged `mode: extensa`, so team commands refuse them until the re-evaluation exists). The
  certification (Mac, `--candidate-record`), the library review and the candidate review go to the same team store;
  the protocol, promotion and re-evaluation records are written on mbit10 in a worktree of that commit and come
  back by git bundle.
- **Promotion** (ticket 48): `swdb promote extensa-native-bfs-20261005-a8.it1.kronecker.a0 --protocol <team>
  --workload-class uniform_random`, which derives the uniform-only team protocol and records the review.
- **Blocks** (mbit10 node 1 through `socket_lane.sh`, isolated as a8: the node 0 and legacy leases released at the
  start and end of each block, recorded with load and users; raw output under `/data1/yanruj/EvolveSWDB_runs/`
  by the 20 GB rule):
  1. A/A: the fork scalar TDStep baseline against itself under the derived protocol.
  2. Only if the A/A width is at most 0.05 and its interval lies inside (1/1.05, 1.05): the certified candidate
     against the fork scalar TDStep under the derived protocol. This comparison is the team re-evaluation.
- **Verdict** (speed rule `ci_width.v2` per comparison): `inconclusive` if the relative CI width exceeds 0.05;
  else `gain` if and only if the lower bound is strictly above 1.05; else `no_gain` (`regression` if the upper
  bound is below 1). An A/A failure is reported as `baseline_unstable` and the candidate block is not run.
  Upstream DO-BFS is not re-timed (a8 reported 0.141).
- **One run; the result is reported whatever it shows; no rerun chosen by outcome.** An
  `infrastructure_failure` before the first block completes may be fixed and restarted once.

## Comments

- 2026-10-05 11:40 ET: claimed by the agent (ticket 75; 74 is reserved for a concurrent guard fix).
- 2026-10-05 12:30 ET: independent review (PROMOTE AFTER FIXES) addressed; [review](../frontier-staging-contract-review-2026-10-05.md). Certification `certification.b7954f4d…` certified (20/20, 8/8); contract promoted to shared (`review.contract.bfs_tdstep_frontier_staging.a8452cbb68ab`). The re-evaluation pre-registration above is committed before any mbit10 action.
- 2026-10-05 13:40 ET: ticket 76 (certify 1.4, blinded and attributed) reached `yanrujhou_main` during this ticket.
  As the coordinator asked, the branch merged it, the native path was ported to 1.4, the tree was certified
  under both versions, and the contract was promoted again only after 1.4 certified.

## Answer

Resolved 2026-10-05 15:00 ET by the agent. Agent-decided, agent-reviewed and promoted under Yan-Ru's 2026-10-05 delegation;
revisable. Not pushed.

**Contract** `contract.bfs_tdstep_frontier_staging` (content `f0919f00…`): tier **shared**, status **certified**.
- Clauses: S1 coverage, S2 lane correspondence (formal half: the `gather_stream` reference pin), S3 frame (assumed
  and owned by the reviewer per candidate), C1 claim and push at the seams, C2 post-claim store elimination with
  preconditions (i)–(iv).
- Preservation obligations: `frontier_size_equality` and `once_enqueue`. Correctness check: BFSVerifier.
- Knob `frontier_batch`: default 16, range 1–4096.

**Controls** (each a seam fault the candidate cannot see; two builds each):

| Control | Clause | Named check | 1.3 | 1.4 (attribution) |
|---|---|---|---|---|
| `claim_without_write` | C2 | `verifier` | rejected | rejected (`lost_claim_left_unset`) |
| `partial_batch_dropped` | S1, `frontier_size_equality` | `frontier_size_equality` | rejected | rejected (`missing_child_of_hidden_vertex`) |
| `stale_row_offset` | S2 | `verifier` | rejected | rejected (`parent_without_edge_from_stale_vertex`) |
| `forged_frontier` | C1, `once_enqueue` | `duplicate_frontier` | rejected | rejected (`duplicate_is_forged_push`) |

A variant that keeps the post-claim store leaves `claim_without_write` alive (tests). Real spellings of both
staging bugs fail the positive cells. A raw-builtin claim fails `seam_witness` in every 1.4 cell.

**Certification of the exact a8 tree.** Tree `7acca955…`, bound to the a8 candidate by `--candidate-record`. The
harness scan has 0 findings, and the rewrite scope holds (one function definition, signature unchanged).

| Record | Command | Cells | Controls |
|---|---|---|---|
| `certification.f5b8f6a732714abfad544aaa65982438` | 1.3 | 22/22 | 8/8 rejected |
| `certification.7f15786592134bdabbc921f16c806ce1` | 1.4 | 22/22, one binary per build, seam witness clean | 8/8 rejected and attributed |
| `certification.b7954f4df9dd4e228fb12437b845f190` | "1.4" label, 1.3-isolation path, before the ticket 76 merge | 20/20 | 8/8 (earlier content `dcaf63ec…`) |

- Code: `swdb/certification_native.py`, `library/native/certification/` and `v1_4/`, and
  `library/profiles/native_bfs_tdstep.yaml`.
- The certification command stays version 1.4, with 1.3 selectable. Native contracts are routed by their
  `certification_profile` pin.
- `--candidate-record` was added.
- Tests: `tests/test_certification_native.py`, 27 cases. With the certification, blinding, isolation, typed-library,
  BC, Extensa and campaign-target suites: 333 passed.

**Reviews.** [Review file](../frontier-staging-contract-review-2026-10-05.md).
- The first review returned PROMOTE AFTER FIXES. It found four majors: the directive scan, the scope, the store
  plan and the controls' wording. All were fixed before the first certification.
- The second review covered the 1.4 port. It also returned PROMOTE AFTER FIXES: two blockings, two majors and
  minors. All were fixed, except that DX100 record file names still reveal the fault (left open).
- Promotion: `review.contract.bfs_tdstep_frontier_staging.92527fd3e03f` cites both certifications.
- `review.…a8452cbb68ab` (content `dcaf63ec…`) is history.

**Team re-evaluation (ticket 48; pre-registered above, commit 6e1fe61, before the run).**
- Team protocol `bfs-native-scale22-ci-team-20261005.9f1ed533a09ae832`. It is new, because no team protocol covered
  scale 22 or the CI-width rule.
- Candidate promotion `review.extensa-native-bfs-20261005-a8.it1.kronecker.a0.95a37f742399`. Derived protocol
  `…-reeval-uniform-random-bb0f642780c4.2e33442a1cf31c02`.
- Host: mbit10 node 1 through `socket_lane.sh` (Memacc 76cca35, equal to its origin), lease generation 527.
- Time: 12:30–14:51 ET (`16:30:44Z`–`18:51:39Z`). Load1 1.6–2.0, users `yanruj` only.
- The node 0 and legacy leases were released at the start and end of both blocks. Commit 6e1fe61 (worktree from a
  git bundle). Runs root `/data1/yanruj/EvolveSWDB_runs/t75-reeval-20261005` (0.24 GB). Lane exit 0.

| Class | Block | Ratio vs fork scalar TDStep [95% CI] | CI width / ratio | Verdict |
|---|---|---|---|---|
| uniform_random (uniform22) | A/A (fork vs fork) | 0.996 [0.989, 1.001] | 0.013 | passes (inside (0.952, 1.05)) |
| uniform_random (uniform22) | certified candidate | **1.454 [1.442, 1.464]** | 0.015 | **gain** |

- The result replicates a8's 1.457 and 1.450. "Single graph per class", measured.
- The comparison `t75-reeval-20261005.candidate.uniform_random.comparison` now admits the candidate to team results
  (`extensa_boundary.refusal` returns none).
- Upstream DO-BFS was not re-timed; a8 measured 0.141 against it, so the artifact is still about 7× slower than
  upstream.
- Evidence: [`evaluation/ticket75-certification-and-reevaluation-2026-10-05.json`](../evaluation/ticket75-certification-and-reevaluation-2026-10-05.json).
  The mbit10 records arrived by git bundle (commit d94ced9).

**Open (for Yan-Ru).**
- The DX100 1.4 record file names reveal the fault through `/proc/self/fd`. Native runs now use nonce names.
- The DX100 1.3/1.4 scan still allows authored `#if` blocks, since the DX100 rewrites use them, so a candidate can
  test the seam macros there.
- The store elimination has no strategy effect in the vocabulary.
- Kronecker for this artifact stays `inconclusive` (a8). No team re-evaluation was run for that class.
- `source_digest` now includes `library/native/`, so DX100 `sources_sha256` values differ from ticket 76's
  `29f3bcab…`.

## Addendum 2026-10-05 16:55 ET: legacy-lease audit (code review S13)

The campaign adapter's isolation check ignored the legacy lease `mbit10-evaluation` (fixed in the code-review
branch). This ticket's re-evaluation did not use that check: `t75_reeval.py` on mbit10 tested the kernel locks of
the node 0 lease and the legacy lease (`Host.held`) at the start and end of both blocks, and every test found them
not held (`evaluation/ticket75-certification-and-reevaluation-2026-10-05.json`, `legacy_held: false`). The legacy
lease's metadata was last written 2026-09-12 00:49 ET (generation 77), so no `hostlock.sh` holder took it during
the run either. The isolation recorded here stands. Audit details: ticket 56's addendum of the same time.

## Addendum 2026-10-05 18:30 ET: review attribution and re-promotion (spec review C1, C3)

- **Attribution.** The contract reviews `review.contract.bfs_tdstep_frontier_staging.a8452cbb68ab` and
  `.92527fd3e03f` and the candidate review `review.extensa-native-bfs-20261005-a8.it1.kronecker.a0.95a37f742399`
  were performed by agents under Yan-Ru's 2026-10-05 delegation, but name Yan-Ru as reviewer with provenance
  `human_report`. They are unchanged; attribution corrections (`review.correction.<review>.*`, one each) state
  the agent review, the delegation and the review document, and the readers report them.
- **Stale evidence.** The candidate review cited `certification.b7954f4d…`, labeled 1.4 but run on the
  1.3-isolation path for contract content `dcaf63ec…`, not the current `f0919f00…`. Under the corrected rule (a
  promotion cites a passing certification of the current contract content with a named command version), that
  review no longer counts as the promotion. The candidate was promoted again through the attributed path
  (`--performed-by agent`): `review.extensa-native-bfs-20261005-a8.it1.kronecker.a0.1657514d8e7d` cites
  `certification.7f15786592134bdabbc921f16c806ce1` (1.4, content `f0919f00…`) and the a8 summary. It reuses the
  derived protocol `…-reeval-uniform-random-bb0f642780c4.2e33442a1cf31c02` and the request
  `reeval-9534c5107d8c-c1e45d3b` already run, so the re-evaluation comparison
  `t75-reeval-20261005.candidate.uniform_random.comparison` still admits the candidate. No run was repeated.
- Listed in the spec's "Awaiting ratification" section.

## Addendum 2026-10-05 19:20 ET: native certify 1.5 record; re-promotion cites it

After the certification fixes merged (fix B, `5a9583c`: per-family procedure tables; native-CPU contracts run
1.3–1.5, default 1.5), the exact a8 tree was certified again on the Mac under the current native command:
`certification.ac33f5548c154caba9adbf0e4abb8925`, command 1.5 (family `native`, sources match the frozen version,
commit `b156044`, no local changes), contract content `f0919f00…`, **certified**: 22/22 cells, 8/8 controls
rejected, evidence basis `measured`. It is bound to the a8 candidate by `--candidate-record`.

Under the derived-level rule (newest command version for the current contract content), this record is the one
that counts, so the 18:30 ET re-promotion (`…1657514d8e7d`, citing the 1.4 record) no longer counts as the
promotion. The candidate was promoted again through the attributed path: `review.extensa-native-bfs-20261005-a8.
it1.kronecker.a0.c12ddfdf5c1b` (performed by an agent under Yan-Ru's delegation) cites the 1.5 record and the a8
summary, reuses the derived protocol and the request `reeval-9534c5107d8c-c1e45d3b`, and the re-evaluation
comparison `t75-reeval-20261005.candidate.uniform_random.comparison` still admits the candidate. No run was
repeated on mbit10.

