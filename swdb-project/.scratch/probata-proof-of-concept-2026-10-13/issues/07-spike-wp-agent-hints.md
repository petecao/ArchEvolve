# 07 — Spike (c): WP with agent hints

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan", A1 row (c); "Proof-hint loop"; "Verifier lineup and order", unbounded verifier; "Providers and machines"); decisions: [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md), [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** about 3 days, inside the 2-week box

**What to build:** The spike's test of the unbounded half. WP must prove one read-offload proof
unit at threads = 1 against the BFS unit postcondition, with proof hints written by Codex, within 60
minutes. The unit is one `TDStep` call with Peter's read offload, the contract's reference instance.
The C lowering tool does not exist yet (21), so WP reads a hand-made C stand-in for it. Throwaway
ACSL contracts stand in for the DX100 calls' summaries. Failing within the box is a stop condition
for 09 — Spike verdict.

## Acceptance

- [ ] The hand-made C stand-in keeps the unit's C++ names (map
      [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) item 3), has a
      hazard check at each tile-pointer read (map
      [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md) item 3), and
      reaches the DX100 calls only through throwaway ACSL contracts. Scope: threads = 1; every data
      dimension symbolic; `TILE_SIZE` a symbolic constant (map
      [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) item 2).
- [ ] WP runs once with no hints; its unproven goals are recorded with their failure class
      (timeout or unknown).
- [ ] One counted run starts with no hints and ends with every goal proven within 60 minutes wall
      time, WP time and Codex calls included. Recorded: rounds, Codex calls, tokens, and solver and
      time per goal.
- [ ] Every hint is one of map [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md)
      item 5's allowed kinds. None of its rejected kinds appears (`admit` in any form, `axiom`,
      recursive or inductive definitions, contracts, ghost functions, ...). Erasing the hints leaves
      the stand-in unchanged, checked by diff. Provenance is recorded per hint: every hint in the
      counted run comes from Codex, none from the implementing agent.
- [ ] The verdict is read from WP's per-property report of a fresh run (`-wp-cache none`, fresh
      session, default warning levels, x86_64 machdep, no WP environment variables). Every goal,
      lemma, call-site precondition and termination goal is Valid. No `Extern` outside the
      contracts of summaries and `maa_*` calls (WP prints those body-less contracts as `Extern`);
      each such contract is an assumption entry (map 13 item 7; design S7). The consolidated
      `[ Valid ]` line is never used.
- [ ] Every smoke test passed on the final hinted unit: no reachable `\false`. A smoke goal WP
      proves Valid signals dead code, so it fails the test (design S7).
- [ ] Negative control: the same hints on a copy of the stand-in with its covering wait removed
      leave the hazard check not proven. WP reports "not proven", never "refuted" (map
      [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md)).
- [ ] WP uses the solver portfolio Alt-Ergo, Z3 and CVC5. A goal counts when any one proves it; the
      solver is recorded per goal (map [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md)
      item 8).
- [ ] Codex sees map 13 item 6's workspace, minus what does not exist yet: the stand-in (read
      only), the unit's C++ code, the unit postcondition, the ACSL summaries, the failing goals with
      kind and failure class, and earlier rejected hints. It never sees tests, negative controls,
      the evaluator, workload inputs or other candidate artifacts. The provider pin is recorded.
- [ ] The Answer states "pass" or "fail", with evidence paths and sha256.

## Notes

- **Not in this ticket:** 21 — C lowering and WP adapter (A2 tracer) (the real lowering); 27 —
  Proof semantics for the BFS read-offload calls and 30 — Reference definitions, per-call summaries
  and new intrinsic versions (the real ACSL summaries); 31 —
  Five-gate drafting and the new bfs_read_offload version (formal halves); 34 — proof_hinting role
  and workspace; 35 — Hint records, merger and proof hint check; 36 — Proof setup check and verdict
  reading; 37 — The proof-hint loop (seeds, minimization, budgets); 39 — BFS unit proven unbounded at
  one thread; A3 exit; 45 — Per-thread lowering (symbolic thread count).
- **Throwaway.** Nothing here becomes A2 or A3 code.
- Assumption (not decided in the map): the 60 minutes count as map 13 item 11 counts its budget:
  loop wall time including verifier time, for one run that starts with no hints. Earlier runs may
  fix the stand-in and the summaries, never pre-seed hints. Map 13's other starting values (10
  rounds, WP 30 s per solver) apply and are recorded.
- Assumption (not decided in the map): "proven" here means the unit postcondition plus the hazard
  checks. Formal halves (A) do not exist until 31.
- Assumption (not decided in the map): Codex is called directly, with the design's pin
  (`gpt-5.6-sol`, effort `xhigh`), since the `proof_hinting` role arrives with 34.
- **Why 03 blocks this ticket:** Codex runs on the Mac under the scoped ADR 0006 exception that 03 —
  New verifiers on the Mac records. Confinement follows design O3's default until Yan-Ru rules:
  Codex's own sandbox over the frozen workspace; the role builds nothing (map 13 item 13). 03
  records that default in the exception.
- Assumption (not decided in the map): these direct Codex calls count as `proof_hinting` work under
  that exception, though the role itself arrives with 34.
- Assumption (not decided in the map): "the box" is A1's 2-week box. A counted run that has not
  passed when the box ends is a fail for 09.
- Assumption (not decided in the map): verdicts go in this ticket's Answer, not as `proof` records.
  Spike code lives in this effort's `prototype/` folder; logs and per-goal reports go to a Mac runs
  folder outside the repo, host `mac` (map 26 item 5). If 05 has not yet recorded that folder, record
  its path, size budget and readers before the first run (LR-06).
- **Risks:**
  - WP must run outside the agent sandbox. Inside it, the Why3 server socket is blocked and WP
    reports `[Failure]` (map 11 and 13 research).
  - A hand-edited WP cache once made a false goal `[ Valid ]` (map 13). Never read a cache.
  - WP turns recursive definitions into unchecked axioms; one proved a false postcondition (map
    13). That is why the vocabulary bans them.
- **Mac rules:** one real verifier job at a time, under the ~8 GB RSS watchdog. Keep at least 50 GB
  free. The counted run may take 60 minutes, so schedule the 30-minute heartbeat first (LR-07).
