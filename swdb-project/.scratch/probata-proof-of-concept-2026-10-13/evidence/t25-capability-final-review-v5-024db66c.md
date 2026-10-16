# Heap capability gate: final frozen independent review v5

2026-10-15 ET. Reviewed clean commit `024db66c9ec4da43901f6662771a389b4567b334` in `/private/tmp/probata-resume-t25`, integrated base `f439edf03d9369c51c5658abe1961af75a52e45f`. No test, compiler, typechecker, WP, Why3, prover, CBMC, provider or remote execution; no repository edits. This supersedes the open findings in the preserved mapping/runner reviews for this exact frozen candidate.

## Verdict: passed for root-owned first formal capability admission

No remaining blocking source/VC/runner finding identified within the declared exact int count/value constructor/destructor capability scope. Production swdb and original lowering fixtures have zero diff from the integrated base. This is setup approval, not successful formal admission, a completed member-body record or ticket25 closure.

## Semantic mapping and witnesses

The fixed reviewed model/module/source hashes, closed12-event map, receiver/store/init/field/value/frame/loop/numeric/lifetime targets and source-derived omitted-store/wrong-release controls remain intact. Available allocator outputs now include alignment, live-range separation and live-base uniqueness; well_formed includes that same uniqueness for zero-extent identities. Constructor loop state carries well_formed and the allocator-output relation at entry. Zero-size and address-reuse controls use legal well-formed allocation outputs. Unbounded issued identities retain dead history, without a fixed pool or machine epoch.

The new Heap.empty is a concrete generic heap definition, not an axiom. The two new feasibility targets are unconditional constructive statements, not implications with potentially contradictory hypotheses. The constructor witness provides a 24-byte receiver block at address8 and an available positive allocation at64. The destructor witness t25_sample performs the explicit one-element allocation/fill/final-size trace, giving receiver identity1 and initialized data identity2 with size/capacity1. These terms show feasible entries but do not restrict any main universally quantified incoming heap. No desired constructor/destructor result is imported as a trusted proposition. All source targets remain separate check lemmas with no previous/future source lemma assumptions.

The constructor still permits an initially uninitialized receiver and overwrites only its fields. It does not release any previously pointed-to buffer; t25_frame preserves other pre-existing live object metadata/contents/init. The destructor still permits receiver/buffer overlap within one identity; it releases the selected entire identity, can invalidate receiver storage and every escaped alias, leaves field values/aliases unrewritten, and does not promise vector_valid afterward. No receiver/buffer separation or desired postcondition premise was added. Generic caller composition, byte/cast/partial-write memory and other element types remain unsupported.

The frozen inventory is42 packets:41 global check-lemma packets (37 prospective positive,4 expected ordinary negatives) plus one numeric C kernel. Actual kernel RTE/init/contract/smoke goals must be counted separately; packet count is not actual WP goal count. Global check lemmas naturally need not generate smoke. Constructive premise witnesses are explicit mathematical nonvacuity controls, not fabricated generated smoke. The numeric kernel requires a nonempty actual smoke inventory with every smoke passing.

## Runner findings resolved

- matches_result is shared by the real and synthetic paths. Every lemma row requires exactly one matching named global property, nonempty ordinary goals all owned by that property, direct classified reader results, and every generated smoke Valid. Expected-negative rows accept only selected-target unknown/timeout, rejecting UNCLASSIFIED report-integrity errors, unrelated open goals, Valid intended targets, vacuous passes and unsupported outcomes. Unknown/timeout is never labeled a refutation.
- Numeric positives require all selected ordinary goals Valid, reader proven with no failure class and actual nonempty passing smoke. No general zero-smoke waiver applies.
- Actual output is rejected under the checkout before source/tool probing. Exact SHA and full source cleanliness precede formal discovery and are rechecked between leaves and afterward. Immutable packet/input checks and exclusive fresh job/report directories remain.
- Explicit timeout/OOM booleans and nonzero command exits prevent result matching, independently of report contents. The real watchdog receives the declared leaf timeout unchanged and an8GiB cap. Shared verifier_lock covers formal discovery, fresh report-module compilation and serial leaves; root retains outer process-tree/time/lane ownership.
- Commands retain RTE, initializedness, no init filter, smoke, cache none, x86_64, explicit prover/timeout, par1 and named target/kernel selection. Fresh inventory plus JSON/CSV reader retains every generated global/ordinary/smoke goal. Raw normalized input, task files, resource results and source/reader/module pins are retained. No c_model record or certification level is created.

## Evidence and budget checked

Rehashed29 retained local pins covering the prototype sources, test source, preserved reviews and six control runs: zero mismatches. The composed preparation log reports21 passed/0 skipped in3.83s, guarded wall4.2832655s, peakRSS121274368 bytes, exit0, no OOM/timeout. Intentional RED controls and unsuccessful implementation checks are separately labeled and preserved rather than relabeled as formal failures. These are Python preparation/policy controls plus a bounded sleep timeout, not formal-tool success. This reviewer did not rerun them.

The README correctly budgets42×180=7560s of possible leaf time, at least8100s whole guard plus wrapper margin, one8GiB worker and a separately monitored raw-output budget (expected under1GiB, explicitly unmeasured). Source and command plans remain frozen for root's independent toolchain admission.

## Mandatory next gate

Actual WP33 import/type syntax, tool/library resolution, all42 packet results and the numeric complete inventory remain pending. Declared physical Why3 stdlib hashes do not establish actual resolution. Independently audit the resolved definition/proposition closure and every emitted task hypothesis; uniform int.Int algebra and reviewed heap/translation definitions are explicit TCB components, while source-specific desired results must never be hidden imported assumptions. Check dependency closure and preserve missing/failed/filtered targets as nonacceptance. A zero exit or all_result_expectations_matched cannot close the gate while import_task_audit_pending remains true. No external compiler-correctness theorem is required by the accepted TCB policy. Public member-model integration and every later ticket25 acceptance limb remain open.

Frozen component SHA-256 pins:

- `experiment.py`: `26486209a7618b59349021af1e48a019c31e91d9828d1e64a77439bf264e285e`
- `heap_bridge.mlw`: `44cd626d07a93d105be791bff82fa201b525e09523a8f6598b92312a6a0b1eac`
- `source_vcs.py`: `5b6353263114ea31bf7ee9408b81a356b10ba1206ee4f21167c67d7d96f1a362`
- `packets.py`: `3299b9eb5f24d37228d26c18dc8a795c812b2410384899d680657d86fbdcead5`
