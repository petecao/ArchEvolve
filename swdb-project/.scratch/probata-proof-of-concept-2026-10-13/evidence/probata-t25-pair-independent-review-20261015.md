# Ticket25 pair workflow independent review

Created: 2026-10-16 00:01 ET.

**PASS for the reviewed production change and prospective profile, conditional on the pinned source/control closure below. Actual proof acceptance remains pending.** No tests, compiler/native executions, version probes, theorem provers, SSH or source mutations were performed by this reviewer.

## Production behavior and source identity

The only production-module change is bounded_std_initialization.py. The original std_models.py, c_lowering.py and wp_adapter.py are byte-identical to the integration base. Pair copy construction now requires one checked initialized local pair source of the exact same modeled type. Pair assignment requires both operands to retain checked local pair origins of the same type. The policy does not turn unknown pointer/reference storage into initialized objects. Local ownership uses AST declaration IDs and the existing prefix table, not names alone. Self-assignment is allowed; reference/address escape paths remain conservatively refused by the surrounding checker. Uninitialized constructor and field-write inputs remain refused.

The change is an initializedness admission extension, not a proof of pair values or of arbitrary C++ std::pair implementations. Original modeled member contracts and bodies remain the subjects of the future WP checks. Native finite value agreement supplies a distinct, bounded source/lowering sanity check.

c_lowering.identity includes bounded_initialization.identity, which includes bounded_std_initialization.py bytes. The public changed-runtime control copies the runtime, mutates the real policy module, starts the CLI from that copied runtime, and uses the original frozen method/library. The refusal occurs before the parser stand-in marker can be created. This closes the relevant translator identity boundary; it does not supply a model proof. The earlier wrong-cwd diagnostic is explicitly excluded.

## Controls and independence

The positive public lowering controls compare C++ and generated C against direct expected values over the input grid; they do not merely assert generated syntax or replay the implementation's internal predicates. Three functions cover default values, deep value copies/field independence, and self-assignment. Seventy-five finite checks include repeated default-return checks; no formal C++ equivalence is claimed. ASan/UBSan execution is retained by the implementer, not rerun here.

Unknown pair pointer copy/assignment and uninitialized scalar constructor/field inputs exercise conservative refusals. Missing current member proofs refuse the public caller before a parser stand-in runs. Four model subjects independently reach a deliberately failing parser stand-in, retain not_proven/parse_error records and the correct body hashes, and retain the RTE/initializedness/smoke flags. Such records cannot satisfy the actual profile's proven dependency checks. The wrong-field function has the defined witness x=2,y=5, producing17 against required11, independent of an unbounded verifier's inability to refute it.

The reviewer found one executable boundary defect in the initial ff2984ad packet: the runner rejected output only inside swdb-project, accepting sibling paths within the full source checkout. Runtime a1ee0cf1 corrects the guard to the resolved monorepo checkout root before mkdir. A public CLI control uses a miniature checkout and a sibling output path, asserts rejection and absence of output creation. The reviewer also requested exact safe/wrong caller subjects and fixture method/evidence assertions; these are now explicit. The implementer additionally fixes the adapter cap at8GiB and checks the reported cap in every actual record. The production policy did not change during these review repairs.

## Prospective actual profile

Collection gates the actual test solely on explicit SWDB_PAIR_ACTUAL=1; the pair test module performs no tool/version discovery during collection. Tool discovery, version matching and actual source/frontend checks occur through the ordinary proof adapter when a job executes. The coordinator must still publish/freeze the exact source, perform actual host/tool admission and supply the external whole-process-tree RSS/time watchdog and verifier lease. The profile script is not that watchdog.

The actual profile requires six distinct retained records: four original int/int pair c_model subjects, one safe library_summary caller and one wrong-field library_summary caller. All six must have contract_fixture evidence, method.pair-workflow-fixture and reported8GiB cap. Each model must be proven with nonempty all-valid goals and an exact original model-body hash. The safe caller must be proven and pin exactly the four model IDs, exact body hashes and the actual freshly retained proof-record IDs. The wrong caller must retain unknown/timeout, at least one ordinary open goal, and no failed smoke. The normal adapter's complete property/goal/setup checks continue to decide provenance and verdicts; no parser stand-in or manually manufactured proven dependency is used.

The fixture requires x,y within[-1000,1000], so the stated linear arithmetic result is within the defined int range. Both safe and wrong functions use the same unchanged postcondition text; the negative changes the selected function, not its desired result. This is pair fixture coverage, not ticket25 completion, a new frozen research method or vector workflow acceptance.

The runner binds eleven local source inputs as a scoped supplement to the coordinator's full manifest, creates a fresh output directory outside the full checkout and sends an absolute monotonic deadline to the selected test. Before each actual CLI call it checks remaining time, passes remaining-minus15s as the adapter budget and uses the remaining interval as the CLI timeout. The profile checks whole completion time and source hashes afterward. Compilation/setup/record writes still consume the coordinator's outer clock. These checks are not a hard realtime guarantee and do not replace the required external process-tree guard. Whole runtime, toolchain and remaining transitive dependency closure must still be bound by the coordinator before actual admission.

## Decision boundary

No unresolved blocker was found in the final reviewed scope. The source protocol, public controls and prospective runner are ready for integration after exact final-pin verification. No actual pair WP proof was run by this reviewer or represented by the retained preparation controls. Future acceptance requires the six actual records, complete per-goal/RTE/init/smoke output, exact runtime/tool identities, resource results and independent cold closure audit. Earlier actual evaluations retain their original source identities.


## Exact final closure

Clean final packet `592891abf6d679e895756a226169b371f45141ef`; immutable runtime `a1ee0cf1836bf31bd6508457434d0615fefce696`; integration diff base `ac899748caa6719b8c4c1cd54e220b64eb77a940`. The final commit changes documentation/evidence only. Six changed paths contain one production module, one runner, one test module, one fixture and two documentation/evidence files.

Retained final profile:13 passed/1 actual-only skipped in47.13s; guard47.542960999999195s, peak319,684,608 bytes, exit0, no OOM or timeout; source_unchanged=true. Independently reread14 JUnit cases,11 exact runtime Git/physical source pins,12 author-pinned final/prior raw artifacts and supporting controls. Metadata errors: []. No controls were rerun.

Complete exact source/evidence inventory: `/private/tmp/probata-t25-pair-independent-review-20261015.json`, SHA-256 `f6b7b2430d03f33972dad71910544397116eb5ffc3ea3092a51758dca7d85f34`.

| Source | SHA-256 |
|---|---|
| `scripts/probata_pair_profile.py` | `c80c0566fde1f0925c3332d09b75a87d6723990a5a6c4696fa653e8acd180ded` |
| `tests/test_pair_workflow.py` | `baa2882950feb9ccd5da6bbec973dc6735e66120ad5b6e835bf79b0680dacb24` |
| `tests/fixtures/proof/lowering/pair_only.cc` | `60452123141c7603c633c1128536ec1397173b459045bedeceb63fb0d4801569` |
| `swdb/bounded_std_initialization.py` | `480bf38b3333639c62d8f89aff129208abccdc63351d63cfa6b23d7cb3d84607` |
| `swdb/bounded_initialization.py` | `12885e27dc1cb62b6c89ed4c2b5728c350dc6b0a5781b09ab70ff058e83b287d` |
| `swdb/std_models.py` | `cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2` |
| `swdb/c_lowering.py` | `e10b33f4d310e3097eb84b34ed53e03daf4df690dcf0c8c160f38d907c91e08c` |
| `swdb/wp_adapter.py` | `aa03842938a19d22fe6c3fb466007cfa57544c55fddc3c19b1784b047271ee43` |
| `swdb/proof_setup.py` | `dad41c8714cd3bfa3cbc472c82e2130f639a04ece008d641eec47512d7098e11` |
| `library/methods/probata-draft-1.yaml` | `497aa683887094e3217945132134112469e028c2a50a7966838bbebf902d3ae5` |
| `tests/fixtures/proof/methods/contract-fixture-1.yaml` | `a7d5acd7f0f592e7955d2fb424e029330068b3ef29c3936e27519b7b7de92b29` |
| `.scratch/probata-proof-of-concept-2026-10-13/evidence/t25-pair-preparation-20261015.json` | `54971ca4e1c7bd94a7b86f96faba498fa5b594fe2cb1c2bbcca9ea7b79c15f8d` |
| `.scratch/probata-proof-of-concept-2026-10-13/prototype/25-pair-workflow.md` | `33d3fe3354b4e7864cd1081c44af5b831e1630af02e30f7f32b737bdb16cf773` |
| `swdb/proof.py` | `c1f0bb937ff43c6db9c20d04f79079d1568dc90e5faf121c45722ff735e45808` |
| `swdb/proof_semantics.py` | `2354b1be662a4a9fe4985110ce657c9a432b27f288639f661e13aa5bad5ea5b6` |
| `tests/conftest.py` | `f70dea4668fc1c2a2234b3bed4d8630734e8eec4f756fbb9be0e8d79a66b6a7a` |
