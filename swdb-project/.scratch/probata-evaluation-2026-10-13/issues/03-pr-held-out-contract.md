# 03 — PR held-out contract and contract proof

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": held-out contracts, RQ3, cut order; "Proven once vs per candidate"; "What a proven verdict asserts"; "Bounds": PR's iteration count; "Formal-half language and the C++ subset": the five gates; "Verifier lineup and order": floats as reals; "Concurrency": shared-action kinds; S1: the proof command); decisions: [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md), [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [20](../../formal-verification-2026-10-09/issues/20-dx100-pr-reset-check.md), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) (items 4-5), [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) (offload-only contracts)
**Time estimate:** about 2-3 weeks of agent work
**Cut order:** 3

**What to build:** As for BC (02), but for PR. Once 01 gives PR a correctness check, an agent (Codex)
drafts PR's output relation and one offload-only rewrite contract, blind to the authors' DX100 code,
from the baseline `PageRankPullGS` and the intrinsic specification. The unit postcondition is a set
of sums over CSR ranges over real arithmetic: next contributions, scores and error. The iteration
count is a bound dimension, expected to need at least 2. Every drafted formal half passes the five
gates. The agent then builds the contract proof and derives the minimum bounds. Yan-Ru approves at
promotion. Agent time and Yan-Ru's review hours are recorded for RQ3. PR is cut third in the
evaluation's cut order.

## Acceptance

- [ ] **Blind drafting:** every drafting call's provider workspace hash list shows no authors' DX100
      function and no file outside 02's input list. The provider workspace and guard test refuses an
      input that names `PageRankPullMAA`.
- [ ] PR's output relation is recorded beside 01's PR correctness check. The contract and its formal
      halves pass `swdb validate` and `swdb build`.
- [ ] The contract is offload-only: it keeps its predecessor's thread split and loop order
      (`PageRankPullGS` itself, or the derived implementation the enabling contracts it names
      produce) and names any required enabling contracts in order (ID and version range). It states
      its unit relation, its bound dimensions (thread count and iteration count among them) and, per
      interface array of the proof unit, its shared-action kinds and whether its reads are history
      reads. Every kind is in the method version's fixed set. Sharing classes stay per candidate
      (map ticket 16 item 4).
- [ ] The unit postcondition is in the method's ACSL subset: next contributions, scores and error as
      sums over CSR ranges, over real arithmetic, written with the method's sum library (range sum,
      filtered sum by an offsets array, and its three lemmas). PR's own definitions are drafted here.
      Rounding appears as a platform-choice assumption entry. Every clause names a proof placement.
- [ ] Every drafted formal half passes the five gates. Gate 4 runs the runtime form on every certify
      run of the reference instance, under 01's PR check at its fixed iteration count. Each rejection
      is recorded with its gate.
- [ ] `swdb prove` writes one proof record per contract-proof part, each with its content-hash set:
      the unit postcondition on the reference instance with its two lemmas; the order-independence
      lemma; the lifting lemma for PR; each formal-visible negative control refuted; the
      minimum-bounds derivation per rung. No formal-visible control proves.
- [ ] The minimum-bounds derivation keeps bounded inputs away from the fixed point (else the loop
      exits after iteration 1, ticket 20) and records the derived iteration-count minimum. Yan-Ru
      sees that value at promotion beside the expected "at least 2".
- [ ] The lifting lemma is machine-checked (WP with replayed `Wp.induction` scripts; Rocq as the
      fallback), or stays an assumption entry of kind "written proof" and the report says so.
- [ ] Yan-Ru approves the contract, the output relation, the formal halves and the minimum bounds at
      promotion; the review cites the proof record IDs. RQ3 inputs are recorded as in 02 (agent wall
      time, provider calls, tokens, review hours, time on PR's own definitions). The final hint sets
      are kept as seeds.
- [ ] The contract-proof records that count come from mbit10, inside a socket lane.

## Notes

- **Not in this ticket:** 01 — Correctness checks and certification drivers for PR and SSSP; 02 — BC
  held-out contract and contract proof; 04 — SSSP held-out contract and contract proof; 05 — LLM
  candidate populations; 06 — Authors' code and seeded faults (the authors' PR, refuted then
  repaired); 08 — RQ3: what a contract buys (the sum library's one-time cost is reported there, not
  here).
- 02's notes on who proves, soundness, the reference instance, drafting inputs and machines apply
  here unchanged.
- Assumption (not decided in the map): "blind" also hides ticket 20's finding from the drafting
  agent, since it describes the authors' code. The contract's negative controls are its own.
- **Risk:** if none of the drafted controls needs a second iteration, the script derives an
  iteration minimum of 1. At 1 iteration the authors' defect class cannot be seen (ticket 20). The
  map does not settle this case: ticket 20 passes on "a minimum of 2", ticket 19 item 1 derives
  every minimum from the controls, and the design spec says only "expected to need at least 2".
  Report it to Yan-Ru at promotion; do not add a control taken from ticket 20's finding.
- **Risk:** WP on real-valued sums at PR's sizes was tested only on a synthetic CSR pull-sum fixture
  ([proof-of-concept 08 — Spike (d): sums over reals](../../probata-proof-of-concept-2026-10-13/issues/08-spike-sums-over-reals.md)).
  If PR's unit does not prove, re-plan with Yan-Ru.
- **Risk:** SAW's float mode may stay unconfirmed. The bounded rung follows the recorded outcome of
  the SAW float-mode check in
  [proof-of-concept 23 — C-stub translator, fallbacks and check mode](../../probata-proof-of-concept-2026-10-13/issues/23-stub-translator-fallbacks-check-mode.md):
  SAW if it passed, else crux-llvm `-f real` (verifier lineup).
- **Risk:** a needed shared-action kind outside the fixed five makes a new method version (02's
  risk). Stop and ask Yan-Ru.
- **Cut order:** if PR is cut, its share of 05-09 goes with it (effort spec).
- Internal findings about the authors' code are never sent to the authors or the team without
  Yan-Ru.
