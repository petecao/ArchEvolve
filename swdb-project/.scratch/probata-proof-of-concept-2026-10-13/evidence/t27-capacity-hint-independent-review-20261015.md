# Independent capacity-hint review — 2026-10-15 ET

**Accept for merge and actual capacity rerun; no blockers.** Reviewed exact commit `0e71d962b2c1a2f5e148264e14bfd486262873eb` in clean `/private/tmp/probata-resume-t27`. This is a justified ordinary induction hint, not a new source precondition or proof of repaired capacity acceptance.

The original `dxf_capacity` (`tests/fixtures/proof/dx100/fixture_units.cc:329–337`) initializes registers and only issues `maa_stream_load` inside its loop. The new invariant states that every in-range tile writer has `DX_STREAM_LOAD` kind. Its proof argument is concrete:

- Initially `dx_idle` sets every tile writer to -1 (`library/proof_semantics/dx100_bfs/logic.acsl:108–110`). The register setup's preserved-writer contract does not introduce writers, so the antecedent is false at loop entry.
- For the destination, stream-load `ensures dx_new_slot(DX_STREAM_LOAD,...)` (`dx100_bfs_0_1.yaml:466`) and `dx_new_slot` (`logic.acsl:196–202`) give the required kind directly.
- For another tile with an in-range post writer, `dx_kept` (`160–167`) preserves its writer index and invokes `dx_same_slot` (`147–148`), preserving that slot's kind. Equality plus the post index bounds establishes the old index bounds, so the incoming invariant applies. Dropped writers make the antecedent false. This handles reuse through the existing relation rather than assuming all old slots remain untouched.
- `DX_STREAM_LOAD=1` and `DX_STORE_VECTOR=5` (`state.h:5,9`) are distinct. The history fact supplies the no-store consequence needed by `dx_memory_clear_at` (`123–127`), including the quantified fallback selected at `DX_NT=40`. It does not grant capacity, pointer validity or initialization.

The hint is agent-authored `loop_invariant`, inserted in the existing loop hint list; it is not `requires`, an axiom or `assume`. The normal WP run must establish and preserve it. It remains possible that the next run times out; source inspection establishes a sound rationale, not solver success.

Independent static checks found the extracted old `_hints(...)` call AST identical to its predecessor. The acceptance-test AST is identical after only removing moved imports/locations and substituting the helper call. All existing memory-clear, count, initialization, register, frame and variant hints remain. The complete `swdb/`, `library/` and original fixture diff against `0e7f232762e4555aa9435a3a3622923fad8ee928` is empty. Runtime semantics, source, contracts, premise specialization and final WP32/WP33 assertions are unchanged.

The corpus entry identifies the historical two memory-domain timeouts and records the narrower compiler/merge replay boundary. The retained RED log fails specifically because the invariant is absent. GREEN and final corpus-driven GREEN each pass 1/1; the final test checks anchor placement, original stream call, agent provenance, retained old hints and exact annotation erasure. It does not run Frama-C or prove hint well-typedness/establishment/preservation; the actual run must supply those checks. All 15 local physical pins in the compact evidence rehash correctly, including the three command/log/resource triplets and six source/corpus/library files. Final GREEN guard: exit0, 0.869 seconds, peak173,113,344 bytes.

Historical remote failure is retained honestly: WP32 `not_proven/memory_domain`,45/47 ordinary Valid,11/11 smoke passed, two timeouts; WP33 and CBMC32/33 were unrun after maxfail. I inspected the existing producer audit JSON/script and its 13-reference/14-file audit result, but did **not** independently fetch or rehash remote raw artifacts. Six remote record/receipt pins are separately marked unverified-by-this-review in the hash manifest. This does not block a test-only hint repair; it limits the independent historical-artifact claim.

Remaining acceptance: actual WP32 must prove every old and new obligation; WP33 must remain `not_proven/ghost_capacity` without a counterexample; the original CBMC32/33 pair must run and agree. No compiler, verifier, test, provider, SSH or remote job was launched by this review. Live producer paths and ticket07 were untouched.

Hash manifest: `/private/tmp/probata-t27-capacity-hint-independent-review-20261015.json`, SHA256 `c2484fa67e80d0d6b39c8408f32fe0bd7751463ec4279facf170c588389ec217`.
