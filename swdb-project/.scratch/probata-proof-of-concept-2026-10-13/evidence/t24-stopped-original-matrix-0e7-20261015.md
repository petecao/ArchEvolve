# Ticket24 stopped original matrix: final retained audit, 2026-10-15 ET

The exact `0e7f232762e4555aa9435a3a3622923fad8ee928` actual matrix stopped at the original std safe caller. **Seven rows met their individual acceptance rules; the original std safe caller did not.** The full matrix is incomplete and unsuccessful. This receipt preserves the accepted float pair and five model dependencies while retaining the caller contract gap. It does not claim that subsequent groups ran.

| Original row | Ordinary Valid / open | Smoke Valid / open | Initialization goals | Result |
|---|---:|---:|---:|---|
| floats safe | 48 / 0 | 5 / 0 | 12 | proven |
| floats seeded | 47 / 1 | 1 / 4 | 12 | not proven; invariant establishment timeout |
| model std_min_int | 5 / 0 | 2 / 0 | 0 | proven |
| model std_max_int | 5 / 0 | 2 / 0 | 0 | proven |
| model std_swap_int | 13 / 0 | 1 / 0 | 3 | proven |
| model std_copy_int | 36 / 0 | 7 / 0 | 7 | proven within checked range-qualified body scope |
| model std_max_long | 5 / 0 | 2 / 0 | 0 | proven |
| std_models original safe | 46 / 1 | 13 / 0 | 5 | not proven; pointer-formation timeout |

The float seed retains failure class `vacuous_pass` and the attributable ordinary open goal `typed_real_swdb_float_unit_loop_invariant_2_established`; its four failed smoke checks remain in the receipt. They are not counted as Valid. The safe float proof retains all 12 initialization obligations after the two ordinary initialized-field loop invariants were added. The earlier historical float failure remains separate.

The failed original std caller is record `proof.wp24-safe.candidate-1.20261015t214040z.c309a2c9`, physical SHA-256 `e03a86746f27c7815aeb4b3765fb3d84da21e1079f8170b4f1a21ae881b6a194`. Its sole ordinary open goal is `typed_real_swdb_std_unit_assert_swdb_pointer_formation_1` (timeout). The original contract pin remains `contract.fixture_wp24_std_models` / `13fd0509e48eb0d9f45e8e6edc9a0fd5a4fec66d45f3e3cc525ee072b09c57d9`. Setup and actual verifier launch passed; all mandatory RTE, initialization, cache-disabled, x86_64 and smoke flags remained present. No counterexample was produced by this timeout.

The caller pins exactly these five physical model records, whose hashes/code contracts/method pins were checked:

- `proof.model.std_min_int.20261015t212915z.949d8187`
- `proof.model.std_max_int.20261015t213126z.f8b8689c`
- `proof.model.std_swap_int.20261015t213339z.c0ed4542`
- `proof.model.std_copy_int.20261015t213547z.ea97bd04`
- `proof.model.std_max_long.20261015t213829z.89f04fca`

The `std_copy_int` certificate `standard-range-model-certificate-1` / `900ad4ea61e5b4ac45c7efa1b5aa652b320a7c3668dc1e313f3de512b71f8b4a` covers the unchanged body/ACSL under explicit typed same-array live-range conditions. Its input premise additions and removed body operations are empty. Its caller still must establish origin, ordering, destination capacity and lifetime; this model success does not license unrestricted opaque pointers. The failed caller's range-check certificate binds that exact model record and qualification. Ordinary public dependency eligibility remains mandatory for reuse.

The immutable producer `audit-0eb6ac0f167be373b462ccfd7b35342d020aa0b8c40254d0ca56da2f818bb9d4.py` verifies 1,003 source/Git blob files, eight physical records, 76 evidence instances and 276 artifact-file instances (with setup hashes checked separately) with zero integrity errors. It reports the caller acceptance error separately. The retained full snapshot is [t24-current-std-frontier-0e7f2327-20261015.json](t24-current-std-frontier-0e7f2327-20261015.json), SHA-256 `faf684b643563fae216e2a4ae85b4070f1dc70a34bc6687f8a43808de4102f67`, freshly matched against the unchanged remote producer output. The accompanying compact JSON pins the records, dependencies, qualification, original contract and completion receipts without modifying any prior artifact.

The exact launch-environment translator aggregate is `b1ddaa111bec5d19843b69fd7571530859acb1382947d96692894bfc29b0b993`; the full snapshot retains driver, parser, standard/resource-header tree and command-wrapper component identities. The method pin is `ac4fe5ea50ebb15eddc88e239cb340d9fca41306df41e0cdda8432c9d0d88c5c`. Generated C++ caller products pin `kept-names.3`; standalone original C model subjects have no generated C++ name mapping. No default-reader fallback identity replaces the exact launch identity.

Node0 generation572 ended at `2026-10-15T21:43:14Z`, exit1. Inner whole-worker monitoring recorded 1,803.321 seconds, peak959,057,920 bytes; outer monitoring recorded 1,805.691 seconds, peak1,010,438,144 bytes. Neither recorded OOM or watchdog timeout. The source-after receipt confirms exact clean0e7. This receipt records the ended lease and retained resource/source checks; it makes no independent process-cleanup claim beyond the coordinator's separate lane management.

The diagnostic correction is documented in [t24-std-object-domain-20261015.md](t24-std-object-domain-20261015.md). Null+0, live-base empty, live-one-past empty and nonempty native controls agree under ASan+UBSan; an intentional bad read fails under UBSan. Quiet dangling/nonobject executions are excluded from agreement, and live zero-size allocation is a native-supported/unsupported-readable-proxy distinction, not classified UB. Native controls establish no WP verdict or exhaustive agreement. The distinct qualified contract's actual safe/seeded pair is pending; a future qualified success cannot be relabeled as original-contract success.

The original std seed, atomics, maa summaries, DXC summary, templates/Ring, classes, OpenMP, allocation pair and dedicated allocation/lifetime controls did not run after this stop. Their historical records are retained at their original freezes. They remain fresh actual acceptance work. Ticket24 stays claimed.
