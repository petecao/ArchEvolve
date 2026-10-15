# Independent stopped-matrix review

Updated: 2026-10-15 ET. **GREEN for retained integrity and truthful incomplete reporting. Original std safe acceptance remains RED.** This audits the frozen `0e7f232762e4555aa9435a3a3622923fad8ee928` snapshot; it is not a new actual proof. Current production source at reviewed `dfa5402df2abbf12609f7adf02065c38241492d1` has no `swdb/` diff from that freeze.

## Verified physical evidence

Read-only SSH checks independently verified 1,003 physical source files against both SHA-256 manifest and frozen Git blob identity, eight YAML record hashes, 76 report/log instances, and 276 artifact-file instances. Artifact manifests were regenerated from physical contents. All setup/hash/method/naming flags, original source substitutions, current original clauses and consumed hints match. Pure offline replay of the strict WP reader against retained goal/property/inventory files reproduces all eight verdicts, failure classes and complete goal lists exactly. No compiler, solver, test or new evaluation ran; no raw artifact was copied locally.

The exact producer `0eb6ac0f167be373b462ccfd7b35342d020aa0b8c40254d0ca56da2f818bb9d4` and full snapshot `faf684b643563fae216e2a4ae85b4070f1dc70a34bc6687f8a43808de4102f67` physically match. Remote raw root: `/data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t24`.

| Row | Ordinary Valid / open | Smoke Valid / open | Initialization goals | Recorded verdict |
|---|---:|---:|---:|---|
| floats:safe | 48 / 0 | 5 / 0 | 12 | proven |
| floats:seeded | 47 / 1 | 1 / 4 | 12 | not_proven |
| model:std_min_int | 5 / 0 | 2 / 0 | 0 | proven |
| model:std_max_int | 5 / 0 | 2 / 0 | 0 | proven |
| model:std_swap_int | 13 / 0 | 1 / 0 | 3 | proven |
| model:std_copy_int | 36 / 0 | 7 / 0 | 7 | proven |
| model:std_max_long | 5 / 0 | 2 / 0 | 0 | proven |
| std_models:safe | 46 / 1 | 13 / 0 | 5 | not_proven |

The float seed remains `not_proven/vacuous_pass`: its attributable ordinary invariant-establishment goal timed out, and four smoke checks failed. None is relabeled Valid or a counterexample. The original std safe record remains `not_proven/timeout` with sole open goal `typed_real_swdb_std_unit_assert_swdb_pointer_formation_1`. Setup and actual launch passed, but the safe all-goal criterion did not.

## Records and dependencies

- `floats:safe`: `proof.wp24-safe.candidate-1.20261015t212324z.db377b81`; record SHA-256 `560c76e40561475712b300c34de4a5d24d11a6f2addb88b1b875bee4f36c69c3`.
- `floats:seeded`: `proof.wp24-bug.candidate-1.20261015t212559z.6233b2da`; record SHA-256 `dff628d92a3a8393857f223f2cb94c24a860cde56d1de527a15e9cd70d27b209`.
- `model:std_min_int`: `proof.model.std_min_int.20261015t212915z.949d8187`; record SHA-256 `7028e9105fdb92ecf8ba1bc1974f456a5084676cdfc1e08161b861978bd7523a`.
- `model:std_max_int`: `proof.model.std_max_int.20261015t213126z.f8b8689c`; record SHA-256 `714be0d2ec0f6017544af81a067c7a60ffafa6ae389109b313a161f73ede6707`.
- `model:std_swap_int`: `proof.model.std_swap_int.20261015t213339z.c0ed4542`; record SHA-256 `c06d6a934ae68fcb72e164c38444faa6b40868119e04d4d96673ce346d6a3b32`.
- `model:std_copy_int`: `proof.model.std_copy_int.20261015t213547z.ea97bd04`; record SHA-256 `ab86fab89802a166bad0263c5235b9b17f84552467a067af1da0fc3887940130`.
- `model:std_max_long`: `proof.model.std_max_long.20261015t213829z.89f04fca`; record SHA-256 `00e5e0404b786243aeba6426a2f8ae7d9bec37a14294ddd5460426d2b86d0037`.
- `std_models:safe`: `proof.wp24-safe.candidate-1.20261015t214040z.c309a2c9`; record SHA-256 `e03a86746f27c7815aeb4b3765fb3d84da21e1079f8170b4f1a21ae881b6a194`.

The failed std caller pins exactly the five fresh listed model records, matching each physical record hash, code/contract content and method. The copy qualification `standard-range-model-certificate-1/900ad4ea61e5b4ac45c7efa1b5aa652b320a7c3668dc1e313f3de512b71f8b4a` matches its physical report, setup, current checker and caller dependency. I independently reconstructed its checked view from the frozen unchanged body and ordinary guards; its hash matches. Added ACSL input premises and removed body operations remain empty. Typed live-range/origin/capacity obligations remain the caller's responsibility; this audit does not bypass ordinary public dependency eligibility.

The pinned launch runtime aggregate is `b1ddaa111bec5d19843b69fd7571530859acb1382947d96692894bfc29b0b993`; method `ac4fe5ea50ebb15eddc88e239cb340d9fca41306df41e0cdda8432c9d0d88c5c`; generated callers use `kept-names.3/64db66a1f89446ce264aa756c22db9672500f430f6b2c08605b5bdd5ae156ff4`. The wrapper, compiler driver, libclang and all 1,983 header files match the immutable producer's pinned components. The aggregate was reconstructed with those exact pinned runtime facts, without rediscovering a default environment. Standalone C model records need no generated C++ naming pin.

Mandatory RTE, unfiltered initializedness, `-rte-initialized @all`, cache none, x86_64, smoke, actual launch and 8 GiB cap checks pass for all eight rows. Node0 generation572's recorded lease ended exit1. Inner monitoring: 1,803.321 s, peak959,057,920 B; outer: 1,805.691 s, peak1,010,438,144 B, hash `e74297cdb1a2efae94aa2cd27017043a39cf2ce59cbcc0db38679986263217dd`. Neither reports OOM or watchdog timeout. Clean exact-source after-run receipt matches. No additional process-cleanup claim is made.

## Boundaries and draft check

The final compact JSON/MD projections, table, record IDs, goal counts, dependencies, qualification and resource values match the retained full snapshot. The earlier ambiguous count wording was corrected to artifact-file instances; setup hashes are checked separately. Reviewed final draft SHA-256: JSON `f4050ac553d7270d2d71635e67e73632d50f868e23905b7716190c973a59e84b`; Markdown `9274044e549316d6b3bd69f6b5cadbab43802ebf9cde732df5a18eb4463d755d`.

Forty-six native evidence file instances match physical local hashes. Defined-input controls have matching C/C++ outputs, the deliberate bad read exits -6 in both, and the zero-allocation/dangling/nonobject observations keep their diagnostic boundaries. No native output supplies a WP verdict or exhaustive agreement. Twelve qualification-profile source/log/JUnit/mutation-evidence instances match; the retained JUnit shows11 tests, zero errors/failures/skips. Those are compiler/parser/test-only controls, and qualified safe/seeded actual acceptance is pending.

Matrix complete=false and success=false remain correct. Original std seeded, atomics, maa/DXC summaries, Ring/templates, classes, OpenMP, allocation safe/seeded and lifetime controls did not run after this stop. Their historical results remain at their original freezes. No lifetime or whole-ticket completion is inferred.
