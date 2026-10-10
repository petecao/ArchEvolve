# 04 — First runnable version: estimate a streaming loop on the mbit10 CPU

Created: 2026-10-06
**Type:** slice
**Status:** resolved
**Blocked by:** 01
**Spec:** `../spec.md`
**Time estimate:** 1.5–2 days

**What to build:** From a tiny C++ fixture kernel with one streaming loop, `swdb characterize` produces a workload characterization (static facts from the LLVM pass, plus trip and access counts from one counted native run), and `swdb estimate` turns it, with a minimal mbit10 target description, into an estimate: seconds per region and in total, a per-region report naming the limiting bound, basis `estimated`. The slice includes the basis value, characterization v1, target description v1, the compute-throughput and streaming-bandwidth mechanism models, the estimate record (a new kind or an evaluation section: choose the smaller change and record why), the two commands and their tests.

## Acceptance

- [x] `estimated` validates wherever a basis is allowed; every existing record validates unchanged (D9).
- [x] Characterization v1 and target description v1 have schemas and documentation written for outside readers (D7, D11).
- [x] The fixture's characterization and estimate match hand-computed counts and bounds.
- [x] An unknown parameter makes the bound that needs it unknown, never zero.
- [x] Counts are taken at source level and record the host (D12).
- [x] Tests run through the commands on a copied record store and skip cleanly when LLVM 22 is missing.

## Comments

2026-10-06: Claimed by ticket04 implementer on `codex/lanl-ticket04`, based on integration commit `fb842a8`. Confirmed public seams are characterize/estimate commands on a copied record store and validate.

## Answer

Resolved 2026-10-06 ET on `codex/lanl-ticket04`; implementation commit `191fd8d`, followed by merge `9bb823f` of the current integration tip. The claim was rebased onto the amended `2c50e5f` base before implementation.

- **Formats and public commands:** [analytic format/reference](../../../docs/reference/format-v0.4-analytic.md), `schemas/workload_characterization.schema.json`, `schemas/target_description.schema.json`, `schemas/estimate.schema.json`, and `swdb/analytic.py`. `estimated` is in the shared basis vocabulary for generic facts/parameters. Execution-specific timing and certification fields retain their semantic restrictions; estimates have their own kind.
- **Smaller record change:** chose `kind: estimate`, because an execution evaluation requires timing/correctness stage receipts. A separate kind keeps estimates outside native/simulated comparison and selection while using the existing validating writer and generic record index.
- **Actual compiler/counting implementation:** LLVM 22 new-PM pass in `swdb/llvm/Characterize.cpp` uses LoopInfo, ScalarEvolution and debug locations. It retains optimized `-O3` facts separately and inserts native counters in normalized pre-vectorization/unrolling IR. `CountingRuntime.cpp` counts actual operations, elements, loop entries and call executions; it retains no address trace or timing. Host, source/input identities, flags, thread/ROI/run-argument identity and IR/binary/count hashes are recorded.
- **Hand check:** eight fixture iterations give sixteen floating-point operations, eight 4-byte reads and eight 4-byte writes. Artificial fixture rates of 16 FP operations/s and 32 useful bytes/s yield compute 1 s, streaming 2 s, and total 2.000000002 s including the tiny serial remainder. The 17-element vector-tail and zero-trip cases match their independent counts. These numbers are fixtures, not mbit10 measurements.
- **Unknowns and coverage:** a required unknown bound propagates to null region/total/ratio; known component bounds remain visible. Executed unmodeled calls carry actual counts and an unknown-cost bound. Arbitrary supplied source is explicitly fixture or unverified application binding; ticket 05 must establish registered-source/outlined-call coverage and ticket 06 the protocol binding.
- **Compiler portability:** shared LLVM distributions link libLLVM; static distributions load the pass against opt host symbols without a duplicate static registry. `--toolchain-flag` applies compiler/header selection to pass/source/runtime; `--run-library-path` records native link/RPATH/runtime search paths. Parent owns the mbit10 load check and measured target parameters.

Validation through confirmed public seams:

| Check | Result |
|---|---|
| Characterization/estimate + format/validation/writer/view regression batch | 101 passed, 1 existing environment-dependent skip; 102 collected, 564.98 s |
| Additional static-distribution public-toolchain regression | 1 passed; real LLVM pass and native counts behind missing-libLLVM proxy |
| Normal shared-distribution hand-estimate repeat after portability change | 1 passed |
| Missing LLVM run (before the extra static case was added) | 2 passed, 6 clean skips |
| Unchanged existing record store | `OK: 553 record(s) valid` |
| Additive format field documentation | 4 passed; repeated after integration merge |
| Whitespace/diff consistency | `git diff --check` passed |

Remote measurements, the full BFS adapter and frozen estimate protocols belong to the unblocked tickets 05–07. No SSH, push or mbit10 measurement was performed by this implementer.

2026-10-06 16:48 ET: parent verified the merged source on mbit10 with official LinuxLLVM22.1.8/static-opt exported-symbol loading. Native hand counts17iterations/34FP/17reads/17writes and artificial bounds2.125scompute/4.25sstream matched;555copied-store records validate. Node0g466,exit0,lease released. [Compact receipt](../evidence/llvm22-mbit10-smoke-20261006-a2.json); raw stays remote. This is contract-fixture plumbing evidence; the artificial rates are not CPU measurements. The priora1 preflight-only failure (missing governor control file) is retained separately.
