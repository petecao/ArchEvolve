# 08 — Spike (d): sums over reals

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 03:15 ET (resolved); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan", A1 row (d) and "Two efforts, split at the freeze"; "Modules", logic library; "Verifier lineup and order", floats as reals; "Further Notes", risk table); decisions: [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** about 3 days, inside the 2-week box

**What to build:** The spike's test of real-valued sums: the riskiest proof for the held-out PR and
BC kernels, done without touching them. Throwaway ACSL definitions give a range sum and a filtered
sum by an offsets array. WP then proves the sum library's three lemmas: additivity, regrouping a
flat edge range by owner vertex, and permutation of a finite sum. Last, WP proves one unit of a
synthetic CSR pull-sum fixture, written for this test, over real arithmetic. Never a PR unit: PR is
held out.

## Acceptance

- [ ] Throwaway logic definitions of a range sum and a filtered sum by an offsets array (map
      [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) item 4). Each is
      non-recursive or primitive recursive on a non-negative integer argument (map
      [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) item 2). No
      axioms.
- [ ] WP 33.0 with `-wp-model +real` proves each lemma: additivity; regrouping a flat edge range by
      owner vertex; permutation of a finite sum. Induction goes through `Wp.induction` scripts,
      saved and replayed on a fresh run (map
      [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) item 7). Per lemma:
      solver, time and script recorded.
- [ ] `\false` check: WP cannot prove `\false` from the definitions and lemmas alone (map 16 item 9).
- [ ] A synthetic CSR pull-sum fixture in C: each vertex's output is a sum of `float` inputs over
      its in-edge range. Its unit postcondition states each output as a range sum, in map 24 item
      2's form. Sizes are symbolic; threads = 1.
- [ ] WP proves the fixture's unit against that postcondition, using the lemmas. In the
      per-property report of a fresh run (`-wp-cache none`), every goal is Valid and every smoke
      test passed (a smoke goal WP proves Valid signals dead code). No `Extern` outside the
      contracts of summaries and `maa_*` calls, each an assumption entry (design S7).
- [ ] Negative control: a seeded-bug copy of the fixture (one edge range off by one), with the same
      hints, is not proven. WP reports "not proven", never "refuted".
- [ ] Every hint is one of map [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md)
      item 5's allowed kinds. Recursive definitions appear only in the throwaway logic file.
      Provenance is recorded per hint.
- [ ] Rounding is listed as a platform-choice assumption entry (map
      [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) item 4).
- [ ] Nothing in the fixture comes from the fork's PR or BC code or the authors' DX100 code. The
      Answer says what the fixture was written from.
- [ ] The Answer gives "pass" or "fail" per lemma and for the unit, with times, evidence paths and
      sha256.

## Notes

- **Not in this ticket:** 26 — Logic and sum libraries (the real, versioned sum library); 38 —
  Calibration on the public C suites; 40 — Bucketed-relaxation fixture (SSSP's risk); 09 — Spike
  verdict; evaluation 03 — PR held-out contract and contract proof and evaluation 02 — BC held-out
  contract and contract proof ([evaluation tickets](../../probata-evaluation-2026-10-13/issues/);
  the first PR and BC proofs, after the freeze).
- **Throwaway.** Nothing here becomes the sum library of 26.
- **Held-out rule:** BC, PR and SSSP are never proven or used for calibration before the freeze
  (59 — Method-version review and freeze; map
  [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md) items 5 and
  7).
- Assumption (not decided in the map): the fixture's unit is one flat loop over the edge range, the
  flattening case map 24 item 4 names, so the regrouping lemma is used. A nested per-vertex loop
  alone would leave that risk open.
- Assumption (not decided in the map): (d) has no time bar. Per-goal times are recorded, and goals
  that need more than map 13 item 11's starting 30 s per solver are listed for 09.
- A failed (d) is not one of the stop rule's two conditions (map
  [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) item 3). The
  design's risk table says "re-plan", so 09 hands it to Yan-Ru.
- Assumption (not decided in the map): (d) passes only on WP proofs, as the A1 row says. The
  lifting-lemma fallback to Rocq (map 11 item 7) is not tried here; if WP fails, 09 reports it.
- Assumption (not decided in the map): hints may come from the implementing agent or from Codex.
  The spike is throwaway agent-written work (map 27 item 3), and the sum library is a once-proven
  method part, which need not be fully automatic (map
  [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md) item 8 lets
  Yan-Ru assist under the same hint rules). Unlike (c), (d) does not test agent hints.
- Assumption (not decided in the map): verdicts go in this ticket's Answer, not as `proof` records.
  Spike code lives in this effort's `prototype/` folder; logs and per-goal reports go to a Mac runs
  folder outside the repo, host `mac` (map 26 item 5). If 05 has not yet recorded that folder, record
  its path, size budget and readers before the first run (LR-06).
- **Risks:**
  - WP proved no induction lemma on its own; Alt-Ergo, Z3 and CVC5 all timed out. With
    `Wp.induction`, one of three subgoals was never attempted, cause unresolved (map 11 research).
  - No Rocq in the `framac-33` switch.
  - WP must run outside the agent sandbox: inside it, the Why3 server socket is blocked and WP
    reports `[Failure]`.
- **Mac rules:** one real verifier job at a time, under the ~8 GB RSS watchdog. Keep at least 50 GB
  free.

## Answer

2026-10-14 03:15 ET. **Spike (d): pass.** WP 33.0 (`-wp-model +real`) proves all three sum
lemmas and the CSR pull-sum unit on fresh runs. The seeded bug is not proven, and no solver
proves `\false`. Every number here is a **Mac result**, not a paper number. Wall time: about
2.5 hours, well inside the box.

**Verdicts for 09** (fresh replay at 03:07 ET: `-wp-cache none`, a new session holding only the
saved scripts):

| Item | Verdict | Solver | Time | Script |
|---|---|---|---|---|
| Additivity (`ADDITIVITY`; helper `ADD_N`) | pass | Z3 (`ADD_N`: Qed + Alt-Ergo) | 0.01 s (0.01 s) | `ADD_N`: `Wp.induction` on `n`, 3/3 |
| Regrouping by owner vertex (`REGROUP_OWNER`; helper `REGROUP_OWNER_N`) | pass | Alt-Ergo | 0.01 s (0.22 s) | `REGROUP_OWNER_N`: `Wp.induction` on `n`, 3/3 |
| Regrouping, total form (`REGROUP_TOTAL`) | pass | Alt-Ergo | 13.0 s (0.7 s on the unit run) | `Wp.induction` on `n`, 3/3 |
| Permutation (`PERMUTATION`; 9 helpers) | pass | Alt-Ergo | 0.01 s (helpers ≤ 0.18 s) | `Wp.lemma` instance of `PERM_ROWS_R`; 7 helpers by `Wp.induction`, 3/3 each |
| CSR pull-sum unit (`csr_pull_sum`) | pass | Alt-Ergo (Qed for the rest) | `UNIT` 0.11 s; slowest goal 0.72 s (`PARTIAL` preserved); stage 31 s wall, 1.2 GB peak | none (loop hints only) |
| Negative control (`-DSEEDED_BUG`) | pass: not proven | — | `PARTIAL` preserved: `Timeout` on all three solvers; `UNIT` `[ Partial ]` | — |
| `\false` check | pass: not proven | Alt-Ergo `Timeout` 30 s; CVC5 `Unknown` 0.8 s; Z3 `Timeout` 8 s (see below) | — | — |

No goal needed more than map 13 item 11's starting 30 s per solver. The slowest is
`REGROUP_TOTAL` (13 s, Alt-Ergo), and it varies from run to run.

**Acceptance, item by item:**

1. **Definitions.** `range_sum` and `filtered_sum` (by an offsets array) are non-recursive wrappers
   of `sum_n` and `fsum_n`. Every recursive definition (`sum_n`, `fsum_n`, `vsum_n`, `row_n`,
   `col_n`, `rows_n`, `cols_n`) is primitive recursive on its last argument: `n <= 0 ? 0.0 :
   f(..., n - 1) + ...`. There is no `axiom`, `admit`, `axiomatic` or `inductive`. WP still
   translates each recursive definition into a definitional axiom (research 13, Q2), and the
   `\false` check (item 3) is the guard for that.
2. **Lemmas.** 17/17 goals Valid. 11 scripts were generated by `\wp::strategy` hints under
   `-wp-prover tip` (`run.sh gen`, 01:58 ET) and saved to `prototype/08-sums-over-reals/scripts/`.
   They were then replayed with `-wp-prover script,alt-ergo,z3,cvc5`, and the log shows
   "Script: 11 (Tactics 11)". Per-lemma solver and time: table above and
   `lemmas/verdicts.txt`.
3. **`\false` check.** Two goals, run apart: lemma `FALSE_FROM_LEMMAS` (all 17 lemmas in its
   context) and function goal `FALSE_FROM_CONTEXT` (every global lemma is a hypothesis). The
   printed Why3 tasks hold all 7 definitional axioms and all 17 lemmas (24 entries). Results:
   Alt-Ergo `Timeout` (30 s); CVC5 `Unknown` (0.8 s). Z3 at 30 s passed the 8 GB watchdog
   after about 18 s (killed, no verdict; out of memory, not a proof). Rerun at 8 s: `Timeout`,
   peak 2.1 GB. One prover per job (`-wp-par 1`). At `-wp-par 4` the job passed the watchdog in
   29 s.
4. **Fixture.** `csr_pull_sum.c`: `y[v] = sum_{j in [off[v], off[v+1])} x[nbr[j]]` over `float`.
   Sizes `n`, `nx` and `off[n]` are symbolic; one thread. It is one flat `while` loop over the
   edge range, whose step either advances the owner vertex or adds edge `j`. Postcondition
   `UNIT` is in map 24 item 2's form:
   `\forall u; 0 <= u < n ==> y[u] == range_sum{Pre}(x, nbr, off[u], off[u+1])`.
5. **Unit proof.** Fresh run with `-wp-rte -wp-smoke-tests`: 61 goals. All 17 lemmas, all 38
   unit goals (`UNIT`, invariants, RTE, assigns, variants) are Valid, and all 6 smoke tests
   passed (none proved). The per-property report shows "50 Completely validated / 50 Total",
   with no `Extern`, `Partial` or `-`. The unit has no summaries and no `maa_*` calls, so it
   has no `Extern` at all. The final step uses `REGROUP_OWNER`, and the step that adds an edge
   unfolds `fsum_n`.
6. **Negative control.** Same file and hints, with `-DSEEDED_BUG`: the owner test `j >=
   off[v+1]` becomes `j > off[v+1]`, so each edge range is one edge too long. WP reports
   `[Timeout]` on `PARTIAL` preserved and `[ Partial ] Post-condition 'UNIT'`. No verdict is
   "invalid".
7. **Hints, with provenance.** All hints come from the agent (the Claude Code subagent for
   ticket 08). There are no seeds and no Codex hints. Every hint is an allowed kind in map 13
   item 5:
   - `\wp::strategy` and `\wp::proof` tactic hints: `Leaf`, plus `Ind_add`, `Ind_own`,
     `Ind_tot`, `Ind_row`, `Ind_col`, `Ind_cols` and `Ind_rows` (`Wp.induction`), plus `Link`
     (`Wp.lemma`).
   - Lemmas proven in the same run: the 13 helpers.
   - Non-recursive definitions: `term`, `pick`, `col_val`, `clip_lo`, `clip_hi`.
   - In the fixture: loop invariants (6), `loop assigns` (2), and integer `loop variant`s (2).

   The recursive definitions are logic-file content, not hints. They appear only in
   `sum_logic.h`.
8. **Assumption entries** (map 26 item 4):
   - Kind *platform choice*: float rounding. `-wp-model +real` reads `float` arithmetic as real
     arithmetic, with no rounding and no overflow. So `UNIT` holds only under this reading. Even
     the RTE guard `is_nan_or_infinite` is closed by Qed only because of it.
   - Kind *trusted tool*: Frama-C 33.0, WP, Why3 1.8.2, Alt-Ergo 2.6.4, Z3 5.1.0 and CVC5 1.2.1.
9. **Origin.** The fixture and the logic were written from scratch, from this ticket's text and
   map 24 items 2 and 4 (statements only). I read no file of the fork's PR or BC code and none
   of the authors' DX100 code. `pr.cc` lines cited in map 24 were not opened.
10. **Pass/fail, times, evidence:** see the table above and the evidence list below.

**Findings for 09, 26 and 37 (the cause is named for each):**
- **The `Wp.induction` "never attempted" subgoal (map 11 research risk).** It is reproduced and
  its cause named. With `base` 0 and a hypothesis `0 <= n`, the "Induction (inf)" child is never
  sent to a prover, and Qed does not close it. The lemma then stays unknown at 2/3 subgoals,
  under both `tip` and script replay. Base −1 makes the child vacuous, and Qed closes it. Logs:
  `dev/exp/e1*.log`, `dev/exp/e2.log`, `dev/exp/e3*.log`.
- **Typing premises block lemma reuse.** For every `int` memory read at the top of a lemma
  statement, WP adds an `is_sint32` premise. Inside another lemma's proof, the read value has no
  typing fact, so the lemma cannot fire. `PERM_ROWS` and `PERM_COLS` timed out on all three
  solvers until the reads moved into non-recursive wrapper definitions. Ticket 26's library
  needs this rule.
- **Trigger gap.** No solver proved `PERMUTATION` from its proven helpers: the goal has no
  `cols_n` term to trigger them. One `Wp.lemma` instantiation hint (`Link`) fixed it. Ticket 26
  and the proof-hinting role (34/37) should expect `Wp.lemma` hints, not only `Wp.induction`.
- **Unproven lemma = hypothesis (research 13 Q4, seen live).** In a first `\false`-check
  layout, the lemma `FALSE_FROM_LEMMAS` (Qed: `false`) sat in the same file as the function
  goal. The function goal became Valid in 0.01 s. The verdict reading must keep requiring every
  lemma Valid in the same run. Log: `dev/false_try2_samefile/`.
- **Z3 memory.** `-wp-memlimit` (default 1000 MB) did not hold Z3 on macOS: 8.8–9.2 GB within
  about 20 s on the `\false` goals. The watchdog is what bounds it. A portfolio run of a
  hard negative goal on the Mac needs `-wp-par 1` or a shorter Z3 timeout.
- **Permutation form.** Assumption: a permutation is given with its inverse,
  `is_perm(p, q, n)` (`p` and `q` are mutually inverse maps of `[0, n)`). The form with
  injectivity only (pigeonhole) and the form with `\exists` for surjectivity both failed to
  instantiate. 26 decides the library form.

**Assumptions** (not decided in the map):
- The test seams are the ticket's acceptance items, read from WP's per-goal JSON and the
  per-property report by `check_verdicts.py` (7 pytest cases). They were not confirmed
  separately, because this is an autonomous ticket run.
- "Regrouping a flat edge range by owner vertex" is taken in two forms: the per-owner form
  `REGROUP_OWNER` (used by the unit) and the total form `REGROUP_TOTAL`. Both are proven.
- The `\false` check accepts a solver killed by the memory watchdog as "not proven". It is
  backed by a clean `Timeout` from the same solver at 8 s.

**Evidence** (host `mac`, runs folder `/tmp/claude/probata-runs/t08/`, 1.2 MB, budget 200 MB
recorded before the first run in `RUNS.txt`). Readers: 09 and the main session. Kept until 09
resolves. `SHA256SUMS` (sha256 `cafa5caa0c471f8dfcbf85ab44a98a8a6e8ce30e55db24115d79b8d9114ca40c`)
covers all 110 logs and reports. The folder `scratch/` named in source comments was renamed `dev/` after the runs (comments left unchanged, so the file hashes still match the runs). Key files:

| File | sha256 |
|---|---|
| `lemmas/wp_report.json` | `27fa02966c6ede81737b0016649bcebb3bc6d579452b571ca32c33043568f6e8` |
| `lemmas/frama-c.log` | `304c597ca2534a223f88e9f5b11de6943cace21f9868f71a4c74af2cc4a1867d` |
| `unit/wp_report.json` | `3555f8ea1e3ba9a59b3707b2dfb20bb87d5afe561bbd5af7f4168b0033f439d4` |
| `unit/frama-c.log` | `955359e724de919c81ebd6e1432d56b454062f13dbe58e2de5289dbb15eedf48` |
| `bug/wp_report.json` | `b668179b87fc326294f6252dbd0dc7649f051610a1b6d6695343d0ba34d3e7a9` |
| `bug/frama-c.log` | `857a617ddd10a3e508555bb21f5baf0a4b7b7a037ee960e153a53368db85529f` |
| `false/alt-ergo/false-lemma/wp_report.json` | `2d00a4b7661f08816ed4a047be813d3f9118fe8c69ff60f2c3f531864813c0ff` |
| `false/alt-ergo/false-fn/wp_report.json` | `31fd84e0f139a4c1cb24b3ca83da8fbaadb4ff41a296cb345cff9061a822926b` |
| `false/cvc5/false-lemma/wp_report.json` | `96a26a1bbe3348cfe437fffced0e9905d298d8910b2625f8da6837149b471c27` |
| `false/cvc5/false-fn/wp_report.json` | `23f9c5a317f321d8c81adafa375ad847ccf65b24f69b78dd16a29b1698686532` |
| `false/z3-t8/false-lemma/wp_report.json` | `ef76d4b4d551886b9cd1f6a929d277cdca2910b39ab1b2ce2b9c76414a638069` |
| `false/z3-t8/false-fn/wp_report.json` | `6b947c09b6956f47a338f392f2063fbe9783fa655c5013e8e60dff71f9204b9a` |
| `gen/frama-c.log` (script generation) | `5f5f49575b08f93803ff6d206d2613e01919b40c7ad9b3525a6d56633b0ba9bb` |

Code: [`../prototype/08-sums-over-reals/`](../prototype/08-sums-over-reals/), with `run.sh <stage>`
for the stages `gen`, `lemmas`, `unit`, `bug`, `false-lemma` and `false-fn`. Each stage runs
under `/tmp/claude/probata-tools/verifier_run.py`, outside the sandbox. sha256 of the files:

| File | sha256 |
|---|---|
| `sum_logic.h` | `998080f3764be943a29e9fde5d387100e4588a18e1361457b9ff95d95a9285a0` |
| `csr_pull_sum.c` | `4e6799cf053d736fc71fb8f8a81cd31e10560370dce79832291a24309eb4ea6d` |
| `false_check.c` | `d02a88c0fb2bb8195d2b778f78101e34eed379d9f9db7a27d3e24b0505fc015f` |
| `run.sh` | `82cacb73b74e92ae35d28058f25593609a3e11a8afd9eadf10eef446ba36f8ef` |
| `check_verdicts.py` | `5cb7faf95cb8fe5a81c287104b6f3df79257d834f7fb6e0129366f0fead32739` |
| `scripts/*.json` (11, concatenated in name order) | `8dcf82edddc98ed8ff5e386cd9fd4d34542bcef276d3a13575603698e028b25c` |
