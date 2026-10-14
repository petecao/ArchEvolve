# 51 — Strict-layer catch-up

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 29
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Modules" (library content: strict layer, new certify version), "DX100 proof semantics", "Refutation, repair and bugs", "Proof-of-concept plan" (side tracks, cut order), "Out of Scope"; S4, O6); decisions: [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md) items 4, 8, 9, 10; [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) item 10; [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) items 4, 7; [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) item 11 and its later change
**Time estimate:** about 1 week
**Cut order:** 2

**What to build:** A new certify command version of the strict layer that knows the proof semantics'
memory-timing rule. Today the strict layer does DX100 memory reads and writes at issue, so it never
flags a CPU access that overlaps a command still in flight. The new version tracks each unfinished
command's memory footprint per element and applies the overlap rule, split by thread and by what DX100
does. Result: 60's replay step can label a refutation that rests on this rule "reproduced" instead
of "proof semantics only". Once the new version exists, 60's replay uses it, whatever the
certification default; that default may stay 1.7. Fixture scenarios show both rules agreeing with
the proof semantics. Certify 1.7 and every older version stay exactly as they are.

## Acceptance

- [ ] **New label, old versions untouched.** A new certify command version label exists in the DX100
  candidate family. Certify 1.7 is unchanged: its existing tests pass as before, and records certified
  under it still count (`swdb validate`, `swdb build` and `swdb candidate-level` on a 1.7 fixture give
  the same results as before this ticket).
- [ ] **Per-element footprints** (12 item 4: indirect, the addresses its index tile names; stream, its
  range). Under the new version, a same-thread CPU write to an address an unfinished indirect DX100 read
  names is flagged, and one to an address it does not name is not. The same pair holds for a stream
  command's range. After the covering wait, neither is flagged.
- [ ] **Overlap rule.** Each row has a fixture scenario with the required verdict under the new
  version:
  - same thread, either side writes: hazard;
  - other thread, DX100 only reads: allowed (the read is a history read);
  - other thread, DX100 writes: hazard.
- [ ] **Agreement with the proof semantics (fixtures show both rules).** The proof-semantics agreement
  check from 29 re-runs against the new version. Every footprint and other-thread-read scenario runs on
  both the strict layer and the proof semantics with 0 differences. Footprints and the other-thread read
  rule leave the "stricter than the strict layer" list (so does the region stall, if this version adds
  it; see Notes). The timing-dependent `get_tile_ready` and the 8-byte tile pair stay on it. The new
  agreement evidence is a proof record that names the new certify version.
- [ ] **Semantics negative controls on the strict layer.** Under the new version: a same-thread CPU
  read of `parent` while its DX100 store is unfinished is rejected; another thread's CPU read of a line
  a DX100 store has in flight is rejected; Peter's other-thread read pattern (DX100 gathers `parent`
  while another thread CASes it) is accepted. The same three also run under 1.7 and their results are
  recorded (expected: 1.7 accepts all three, since it does DX100 memory accesses at issue).
- [ ] **Replay labels through 60's replay step** (run by `swdb prove`). With the certification
  default still 1.7, a fixture refutation that uses a same-thread footprint hazard replays against
  the new version and is labeled "reproduced"; the record names the new version. Control: with the
  new version absent (1.7 the newest), the same replay is "proof semantics only" (citing the rule's
  gem5 source), since the rule is still on 1.7's "stricter" list. Negative control: a planted copy of
  the new version that claims the rule (off the "stricter" list) but ignores footprints makes the
  same replay "not reproduced", and the batch stops.
- [ ] **No 8-byte tile-pair rule.** A fixture with an 8-byte operand behaves exactly as under 1.7.
- [ ] **Mac rules.** At most one real verifier job at a time, under the ~8 GB RSS watchdog; full-suite
  test runs use at most 2 workers.

## Notes

- **Not in this ticket:**
  - 29 — Proof-semantics checks: builds the agreement fixtures and the semantics negative controls for
    the proof semantics itself. This ticket only re-runs them against the new certify version.
  - 27 — Proof semantics for the BFS read-offload calls; 28 — Proof semantics for the remaining
    `maa_*` calls: the proof-semantics rules themselves.
  - 60 — Strict-layer replay and whole-kernel reproduction: the replay step itself (13 item 10), its
    labels and the batch stop on "not reproduced". This ticket only adds the memory-timing rule that
    lets 60's replay label such refutations "reproduced".
  - 58 — Mac verdicts reproduced on mbit10: re-runs these replays on mbit10.
  - A plain C++ data race (46 — CIVL adapter): it is undefined behavior, not a strict-layer rule. Its
    refutation gets the replay label "undefined behavior (no strict-layer replay)" (design O6), which
    60 applies. This ticket covers only DX100 memory-timing refutations.
  - The 8-byte tile-pair rule (16 item 11): it stays in the proof semantics; the strict layer gets it
    only after the evaluation, because no evaluated kernel uses 8-byte tile data. No ticket in this
    effort.
- Assumption (not decided in the map): this ticket has no "Blocked by" edge to 60, because it can be
  cut and 60 cannot. 60 sits in A2, so its replay step should exist by the time this side track runs.
  If it does not, the replay-label criterion runs last, once 60 lands; this ticket never builds its
  own replay step.
- Assumption (not decided in the map): the new label is the next one in the DX100 candidate family
  (1.8, unless another version lands first).
- Assumption (not decided in the map): whether new certify runs default to the new version is Yan-Ru's
  call. This ticket adds it beside 1.7; the default stays 1.7 until Yan-Ru decides. Replay does not
  wait for that call: 60 replays against the newest certify version that models the failing rule,
  whatever the default. Reason to ask: under the new version, a candidate artifact with a
  same-thread footprint overlap fails certification, where today it certifies and is refuted only
  by proof (12 item 4).
- Assumption (not decided in the map): 12 item 4 also orders device against device by gem5's region
  stall ("the strict layer gets these rules later"). The new version includes that ordering if the
  strict layer does not model it yet. 29 puts it on the "stricter" list today; confirm in the code
  first.
- Assumption (not decided in the map): the strict layer runs code, so it must pick the value a DX100
  read returns while another thread writes the location. To replay a counterexample that relies on an
  older allowed value, 60's replay supplies that choice from the counterexample (any value the location
  held while the command ran, never older than stores made before issue).
- **Side track and cut:** beside A3–A4; it ends before the freeze. If cut (cut order 2), replays that
  use the rule stay "proof semantics only" (27 item 7), and 58's edge to this ticket drops.
