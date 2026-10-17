# 29 — Proof-semantics checks

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 23, 28
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("DX100 proof semantics" (agreement, semantics negative controls, values and timing split), "Records and levels" (method-part subjects), "Testing Decisions" (seam 1, method parts), S1, S2, S4); decisions: [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md), [14](../../formal-verification-2026-10-09/issues/14-dx100-wait-rule.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md)
**Time estimate:** about 4 days

**What to build:** A proof-semantics version earns trust before any proof on it counts. Per version, three checks, each a method-part proof record: (1) every rule that both the strict layer and the proof semantics model runs as a fixture scenario on both, with 0 differences, in the pattern of the strict wait-rule fixture, and the rules only the proof semantics has are listed; (2) the three generated summary forms (SAWScript specs, C stubs, ACSL) give the same verdict on every scenario (this ticket owns three-form agreement on the semantics scenarios); (3) the semantics negative controls get their required verdicts (4 must be refuted, 2 must prove), and a wrong verdict voids the version. Once for the effort, the reduction lemma that joins finish-at-issue values to hazard freedom gets its written proof and a bounded check on an asynchronous port. End to end: `swdb prove` on the method parts, for a named version, writes the records that later verdicts cite in their proof-semantics assumption entry. Last, it prepares the proof semantics' review packet for Yan-Ru's review at the freeze (59).

## Acceptance

- [ ] **Agreement, 0 differences.** Each rule both models has at least one fixture scenario. Each scenario runs on the strict layer (the current certify version) and on the proof semantics, with its build constants recorded. The method-part proof record shows 0 differences and pins the proof-semantics version and the certify version.
- [ ] **Every rule accounted for.** Each rule of the version maps to a scenario or to the "stricter than the strict layer" list. Negative control: a rule with neither fails the check. The list holds at least footprints, the timing-dependent `get_tile_ready` and the other-thread read rule (map 12 item 8), plus the region stall and the 8-byte tile pair, which the strict layer does not model today.
- [ ] **Agreement catches a planted difference.** Negative control: a mutated rule on one side (for example, the range-loop exception removed) gives at least one difference, named by scenario.
- [ ] **Three forms agree** (owned here; ticket 27 compares only SAW with WP, on its own fixtures). SAW on the SAWScript specs, the C-stub fallback on the C stubs, and WP on the ACSL give the same verdict on every scenario. Negative control: a planted translator fault (one form drops a hazard assertion) is caught.
- [ ] **Semantics controls, required verdicts** (map 12 item 9). Must be refuted: `TDStepMAA` with its wait deleted; the authors' wait under the old wait rule; a same-thread read of `parent` while its DX100 store is unfinished; another thread's read of a line a DX100 store has in flight. Must prove: the authors' wait under the gem5 rule; Peter's other-thread read pattern (DX100 gathers `parent` while another thread CASes it). Each is a method-part proof record.
- [ ] **A wrong verdict voids the version.** Negative control: a deliberately broken version (the unready-read assertion removed, so the wait-deleted control proves) is marked void by the run. Through `swdb candidate-level`, a fixture candidate artifact whose proof record pins the void version reads as certified.
- [ ] **Evidence travels.** Every proof record that pins a checked version cites the agreement, form and control records in its proof-semantics assumption entry.
- [ ] **Reduction lemma, written** (once; map 12 item 2). A written proof that hazard-free code gives the same values under every timing gem5 allows, with research 14's side conditions: one core's commands dispatch in program order but run out of order, made safe by the tile dispatch stall and the memory-region stall.
- [ ] **Reduction lemma, bounded check** (once). On an asynchronous port in which each command finishes at any point before its covering wait, every hazard-free scenario gives the finish-at-issue values (a method-part proof record). Negative control: a scenario with its wait deleted shows a value difference. Verdicts list the lemma as an assumption entry of kind reduction (map 12 item 2) until ticket 43's Rocq check.
- [ ] **Re-runnable.** One `swdb prove` run per method part repeats checks (1)-(3) for any named proof-semantics version.
- [ ] **Review packet for the freeze** (59). For the current proof-semantics version: its ID and content hash; every rule with its gem5 citation or its owner; the agreement, form and control record IDs; the "stricter than the strict layer" list; the reduction lemma's written proof and its bounded-check record. The agent hands it over; the review is Yan-Ru's, at the freeze.

## Notes

- **Not in this ticket:** 27 — Proof semantics for the BFS read-offload calls and 28 — Proof semantics for the remaining maa_* calls (the rules). 30 — Reference definitions, per-call summaries and new intrinsic versions. 33 — Minimum-bounds script and A2 exit (re-checks this ticket's form and control records at the exit; runs no new check). 43 — Rocq: DX100 reduction lemma. 59 — Method-version review and freeze (Yan-Ru's review of the packet). 51 — Strict-layer catch-up (adds the memory-timing rule to the strict layer; the "stricter" list shrinks then). 46 — CIVL adapter, 47 — GenMC adapter and agreement and 48 — Concurrency negative controls (real interleavings).
- Assumption (not decided in the map): "run on the proof semantics" means the bounded verifier on the scenario with the generated contracts, at concrete inputs. A difference is a different hazard verdict or a different value read.
- Assumption (not decided in the map): WP never refutes, so for WP "the same verdict" on a hazard scenario means "not proven", with the hazard assertion among the failing goals.
- Assumption (not decided in the map): the other-thread scenarios and the two other-thread controls run as sequential scenarios with two thread IDs in one fixed order, as in ticket 28. CIVL and GenMC run real interleavings in A4.
- Assumption (not decided in the map): "the authors' wait under the old wait rule" runs against a control semantics, a copy of the version with the old wait rule. It counts only as a control, never as a version.
- Assumption (not decided in the map): the reduction lemma's written proof follows the composition theorem's fallback pattern (map 15 item 8): Codex writes it, Codex reviews it adversarially, and Yan-Ru approves it with the proof semantics, from this ticket's review packet.
- Assumption (not decided in the map): how "void" is stored. This ticket picks the smallest form the level rule can read (a field in the control record), so the level rule needs no new concept.
- The unchecked lemma's assumption entry has kind "reduction" (map 12 item 2).
- Risk: the strict layer applies DX100 memory effects at the call, so the memory-timing rules stay on the "stricter" list until ticket 51. If 51 is cut (cut order 2), replays (60 — Strict-layer replay and whole-kernel reproduction) of refutations that use them stay "proof semantics only" (map 27 item 7).
- Mac: one real verifier job at a time under the ~8 GB RSS watchdog. Before the full scenario batch, record its output destination, size budget and readers (LR-06); if it runs past 30 minutes, post the 30-minute heartbeat (LR-07).
- Assumption (not decided in the map): the citation of this ticket's agreement, form and control records is resolved on read by proof-semantics version, never stored on a proof record. A record that pins a version whose checks do not exist yet reads "proof semantics unchecked" in its assumption entry and counts once the checks pass; a failed check voids the version (10).


### Retained agreement boundary — 2026-10-15 ET

An exact complete native-model finite case observes one-past of one automatic
array at the numerical address of an adjacent distinct array and answers the
footprint query true. ACSL additionally distinguishes the physical object. The
production query slice now requires a separately proved same-object domain; this
does not establish general agreement of the inherited native query and ACSL.
Retained source, output and independent review:
`prototype/27-proof-semantics/checks/query-address-boundary-20261015/`.
[Evidence](../evidence/wp-footprint-query-20261015.json). Account for this boundary
in the scenario/agreement matrix after28; no public false proof is claimed.
