# 36 — Proof setup check and verdict reading

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 11, 21, 27
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-hint loop": Three checks; "Verifier lineup and order": one summary source, failure classes; "What a proven verdict asserts": harness `assume`s; "Records and levels": method-version file; "Testing Decisions", seam 1; user stories 15, 21, 30, 31, 33; S1, S3, S7); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (items 7, 10), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) (item 4), [09](../../formal-verification-2026-10-09/issues/09-what-proven-asserts.md) (item 10), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (items 3, 10)
**Time estimate:** about 3 days

**What to build:** Two frozen, versioned checks inside `swdb prove`, so a proof cannot pass by
changing its own setup or by a misread report. Before every verifier run, the **proof setup check**
confirms the inputs and settings are the frozen ones: only summary-generated `assume`s; the
generator-made hazard probes present; every clause has a proof placement; the hashes of contract,
summaries, lowering and run plan; the frozen WP flags; and a run that matches the method-version
file. A pass goes into the proof record; a fail stops the batch. After the run, **verdict
reading** uses WP's per-property report from that fresh run: every goal, lemma, call-site
precondition and termination goal must be Valid, every smoke test must pass, and no `Extern` may
appear outside the contracts of summaries and `maa_*` calls (both readings are design S7). It
never trusts the consolidated `[ Valid ]` or a cache. Smoke tests void a vacuous proof. Each check
is tested with its negative controls.

## Acceptance

- [ ] **Always first.** `swdb prove` runs the proof setup check before every verifier run it makes,
      bounded runs included (scripted-adapter control: a non-summary `assume` on a SAW job is
      refused). On a pass, the proof record carries the result and the check's version. On a fail,
      no verifier runs and `swdb prove` stops the batch, naming the failing rule (assumption below).
- [ ] **`assume`s.** Only `assume`s a summary generates pass (map 11 item 4). Controls: the 08
      prototype's harness `assume` (`parent[v] >= -1`, which real callers violate); a hand-added
      `assume` in the C lowering. Both refused.
- [ ] **Hazard probes and placements.** Controls: a fixture unit with one generated hazard probe
      deleted; a probe supplied as a hint instead of by the generator; a clause with no proof
      placement. Each refused.
- [ ] **Hashes.** The check records the hashes of contract, summaries, lowering and run plan, and
      each must match the hash pinned for the job. Changing any one after the job is planned →
      refused.
- [ ] **Frozen flags.** Each control refused: `-wp-cache update` and `-wp-cache offline` (only
      `-wp-cache none` passes); an existing WP session in the working folder (not a fresh session); a
      Frama-C warning key moved off its default (for example `ghost:bad-use`, or `annot-error` below
      abort, which drops ill-formed annotations, research 13 Q7); a machdep other than
      x86_64; any WP environment variable set (`FRAMAC_WP_CACHE`, `FRAMAC_WP_CACHEDIR`,
      `FRAMAC_WP_SCRIPT`).
- [ ] **Method-version match.** A tool, solver or flag that differs from the method-version file
      is refused. On a pass, the record names the method version's ID and hash.
- [ ] **Per-property reading.** No fact-file control reads as proven, though WP prints its target
      `[ Valid ]`. A goal resting on an unproven lemma, on a failed call-site precondition, or on a
      callee whose termination fails reads "not proven" with the failing goal's class. A goal resting
      on an `admit` or an `axiom` (an unexpected `Extern`) stops the batch. `Extern` on a summary's
      or a `maa_*` call's contract is accepted, each one an assumption entry (S7). The consolidated
      status is never read.
- [ ] **Doctored cache.** The tampered cache entry from map ticket 13's facts (a false goal edited to
      `valid`) cannot make a goal Valid: the verdict comes only from the loop's own fresh run.
- [ ] **Smoke tests.** Every smoke test must pass (S7: a smoke goal WP proves Valid signals dead
      code). A failed smoke test voids the proof with failure class "vacuous pass". Controls:
      contradictory preconditions; contradictory loop invariants.
- [ ] **Failure classes.** A "not proven" reading carries the class the WP adapter (21) gave each
      unproven goal, or "vacuous pass" for a failed smoke test. Timeout and unknown are marked for
      the proof-hint loop (37 routes them). Any not-Valid property with no class stops the batch.

## Notes

- **Not in this ticket:** 35 — Hint records, merger and proof hint check (hint-borne escape
  hatches); 37 — The proof-hint loop (when smoke tests run on the final hint set, minimization,
  rounds); 11 — Method-version file and failure classes (the file and the class list this ticket
  reads); 27 — Proof semantics for the BFS read-offload calls (generates the hazard probes this
  check looks for); 21 — C lowering and WP adapter (A2 tracer) (the WP run itself and its per-goal
  failure classes); 10 — Level rule (what a verdict does to the level).
- Controls come from the seven WP fact files of map ticket 13 (report statuses, tactic scripts,
  smoke tests, other constructs, and the flag cases in the others), listed in
  [research 13](../../formal-verification-2026-10-09/research/13-wp-hint-facts.md).
- **`Extern` and smoke goals (design S7).** WP prints the contracts of summaries and `maa_*` calls
  (body-less) as `Extern`, so "no `Extern`" means none outside those contracts, each of which is an
  assumption entry. "Every smoke goal Valid" means every smoke test passed (`passed: true`); a smoke
  goal WP proves Valid signals dead code (research 13, Q6 and Q7). Any other `Extern` has no failure
  class, so it stops the batch (26 item 10).
- **Flag for Yan-Ru:** S7 accepts `Extern` only on those contracts. If a once-proven logic-library
  lemma reaches WP admitted, it falls outside S7 and stops the batch. Raise it before working
  around it.
- **Harness `assume`s, stricter rule kept.** Map 09 item 10 also let a harness `assume` stand when it
  is proven at every real call or listed as a reduction. The later map 11 item 4 allows only
  `assume`s a summary generates. This check follows map 11 item 4.
- Assumption (not decided in the map): the reading compares the goals WP generated with the goals
  it reports, so a goal left out as never tried counts as not proven. Research 13 Q5:
  `-wp-prover none` or `script` drops untried goals from the report.
- Assumption (not decided in the map): no single WP output has everything. Research 13 Q4: the JSON
  goal report lacks admit and axiom data; the CSV report leaves out lemmas and axioms. The reading
  combines outputs from the same run; the choice is tested against the report-status, tactic-script
  and smoke-test fact files.
- The mapping from WP's per-goal outcomes to failure classes belongs to 21 — C lowering and WP
  adapter (A2 tracer), as 11 assigns it. This ticket only reads it and adds "vacuous pass".
- Assumption (not decided in the map): a failed proof setup check matches no failure class, so it
  stops the batch until root-caused and writes no proof record, as 11 does for an unlisted class
  (map 26 item 10: a failure outside the list stops the batch).
- Assumption (not decided in the map): on a bounded-verifier run the setup check covers the same
  items except the WP flags; that tool's frozen flags come from the method-version file.

## Implementation checkpoint — 2026-10-15 ET

Implemented the universal setup preflight, per-invocation generated-input check,
and fresh WP property reader in `swdb/proof_setup.py` and `swdb/proof_report.ml`.
The WP, CBMC, crux-llvm and whole-function CBMC adapters call the generated-input
check immediately before their verifier process. A real successful verdict without
that check is refused by `swdb prove`. Schemas and
`docs/reference/format-v0.4-proof-setup.md` describe both attestations; production
execution methods must pin each check's version and content hash. Historical
fixture methods remain fixture evidence.

The reader enumerates generated Wpo obligations, actual individual prover results,
property dependencies and user include closure. Automatically proved obligations
omitted from WP JSON require direct valid results; omitted untried obligations stay
not proven. No consolidated Valid summary establishes proof. Unexpected Externs
stop the batch; exact pinned summary, C-model and DX100 contract Externs become
individual assumption entries. Failed smoke tests invalidate the result while
retaining each original goal and failure class. Lemmas are never filtered out to
make a target pass.

Assumption resolved with the project coordinator: bounded harness restrictions
are reconstructed from pinned bounds and the formal unit's declared preconditions.
They are explicit input-domain restrictions, distinct from summary postconditions.
An undeclared `parent[v] >= -1` restriction is still refused. A unit's own Ignored
preconditions describe its conditional theorem; failed call-site preconditions
remain proof obligations. Neither check discharges lifting obligations at callers.

Validation before the final semantics ghost-state hardening: 48 setup/documentation
controls passed in 149.65 s, including 13 real Frama-C fact controls and the actual
doctor-cache experiment; two additional production version/hash controls passed;
three direct CBMC/baseline/chain controls passed; all 15 existing WP adapter cases
passed (safe and seeded-bug pair, then the other 13). Logs are local under
`/private/tmp/probata-t36-{verified,method-controls,bounded,wp-verified}.jsonl`.
The packaged wheel also contains byte-identical Python/ML check assets.

A subsequent cross-ticket review found that Frama-C permits ghost hints to mutate
the trusted semantics ghost model. The setup guard now restricts semantics-job ghost
hints to fresh scalar witnesses and the checked `dx_store_bound` witness; direct
model writes, pointer/indexed writes, shadowing, calls, mutation expressions and
macro expansion fail closed before hint goal generation and before final WP.
Non-semantics hint behavior is unchanged. The dedicated public CLI adversarial and
accepted-witness controls passed: **12 passed in 95.52 s**, using the final checker
identity below. The macro control first reproduced an accepted hint containing a
model-state mutation; the guarded run refuses it before any WP process. The log is
`/private/tmp/probata-t36-ghost-final.jsonl`. Ticket 27's prover-free hint-generation
fix is integrated; the final WP portfolio remains unchanged.

Both `proof_setup_check` and `verdict_reading` have version `1` and content hash
`7a303ac2a9714010ea42f29964e81b62b7ae6a9bca0fb21318deb76974e6b9cc`.
Integration was merged before handoff; no source changes followed the final guard
validation. The earlier real fact controls exercised the same report reader; the
subsequent checker changes only added the semantics hint guard.

Status remains `claimed`: ticket 27's final real WP semantics acceptance is still a
required dependency. This checkpoint does not assert that all ticket-27 units have
passed, that Rocq composition is proved, or that a production campaign is proven.

### Follow-up ghost expression guard — 2026-10-15 03:14 ET

A public CLI negative control reproduced a shift-assignment bypass:
`dx_store_bound = (dx_count >>= 31)` passed the old expression check and mutated
trusted model state. The expression grammar now explicitly refuses both shift
assignments and trigraph introducers (`??`), including line-spliced shift operators.
Ordinary relational comparisons remain admitted. The right-shift control failed
before the fix; the full final focus suite passed **16 tests in 205.88 s**.
Logs: `/private/tmp/probata-ghost-shift-{red2,green}.{log,jsonl}`.
Both check identities are now version `1`, sha256
`5f5b3e343880fe65990a3aa47b335415cb2fee9cfa6e74fa8ceb7f80f9afe71f`.
The production composition record in ticket 42 pins this exact checker through
immutable `method.probata-draft-2`. Earlier checker identities above are historical.
Ticket 27's remaining acceptance and CPU-memory admission work still block resolution.
