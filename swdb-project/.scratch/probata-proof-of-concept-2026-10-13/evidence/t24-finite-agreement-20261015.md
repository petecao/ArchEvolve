# Original fixture finite C++/C agreement

Updated: 2026-10-15 ET. Compiler-only evidence for ticket24's agreement limb.
Actual WP acceptance remains separate; this document creates no proof record.

The runner `../prototype/t24-finite-agreement.py` reuses ticket22's `_domain` and
`cbmc_translator.harness` against the exact original fixture clauses. It compares
the complete combined original C++ translation unit with each ordinary C lowering,
including real fixture summary implementation bodies. It never invokes the
bounded adapter, weakens its admission rules, substitutes a formal-summary stub,
or executes a WP checking view. Compiling the complete original translation unit
avoids the adapter cutter's inability to find synthesized C member names in C++.

The native harness normalizes scalar interface dereferences `*p` to `p[0]` because
the shared parser accepts indexing. Its separate, fully initialized, nonnull
positive-capacity primitive buffers make these the same lvalue. Both original
and normalized clauses are retained. Array capacities are explicit even for
pointer-only atomics/maa units; finite native extents are not symbolic minimum
bounds. The original size preconditions remain unchanged.

The domain enumerates ticket22's small value choices and size ranges until its
20,000-row limit, then uses its deterministic seed22 sampler. The report retains
every requested oracle input, original-precondition exclusions, actual defined
comparisons, and UB exclusions. IEEE/native floating output comparison does not
discharge WP's real-number rounding assumption. OpenMP/atomics run in the declared
one-thread meaning. Fixture DXC/maa bodies are stand-ins, not hardware semantics.

Known UB is visible, not repaired with stronger premises: the allocation seed
writes `buf[n]` for every legal positive n; the std seed forms `a-1` at legal n=0;
and the maa seed overflows at `INT_MAX`. These original-source inputs are recorded
but not executed or counted as agreement. Remaining native executions use ASan
and UBSan; their union of diagnosed UB rows is excluded. A one-sided sanitizer
observation rejects acceptance. Sanitizer silence is not a general UB theorem.

Each report binds the source, original/normalized contract, common harness,
domain, raw stdout/stderr segments, observed streams, defined output hashes,
compiler/link commands, compiler configuration, Python, native binaries, header
dependencies and physical link inputs. macOS SDK stubs and physical libraries are
hashed; dyld-cache runtime bytes are not independently hashed. The OS identity and
SystemVersion.plist are retained. No universal C++/C equivalence follows.

## Controls and pilot

The first CLI test was RED for the absent runner, then the original template
safe/seeded pair passed. A second RED caught an exclusion-accounting error:
contract-infeasible k extremes had been counted as UB. The corrected classifier
keeps those rows infeasible. The five CLI controls then passed in 34.40 seconds
under an 8 GiB RSS watchdog (peak 1,191,936,000 bytes, no OOM/timeout):

- Original template safe/seeded: each 25 defined comparisons, 24 precondition exclusions.
- C-only return error: named feasible `[-2,-2]` mismatch; batch stops before the next group.
- C-only null dereference: 25 one-sided UBSan failures, zero defined comparisons, rejected.
- Changed retained output: physical-file audit rejects the report.
- Original allocation seed: 500 known UB exclusions, 214 infeasible rows, zero defined comparisons; explicitly excluded, not agreed.

Raw controls: `/private/tmp/probata-agreement-controls-{red,green}/`. The frozen
prospective pilot at `e48a302e0081ce46d8c2f865568951913833d276` lives at
`/private/tmp/probata-agreement-pilot-e48a302e/`. The template pair completed in
9.79 watchdog seconds, peak 1,108,099,072 bytes, no OOM/timeout. Both rows have
25 defined comparisons, 24 precondition exclusions and zero UB. All 2,040 physical
references audited without mismatch. The report SHA-256 is
`1f1bb4e026f814cb277094248040afef3cbd44046c049e779ee0cd3b03ef65a1`.

## Full original fixture matrix

Independent source/pilot review admitted the frozen runner before scaling
(`/private/tmp/probata-t24-agreement-pilot-review.md`). The full profile then
completed at the same clean `e48a302e0081ce46d8c2f865568951913833d276`, serially
under an 8 GiB RSS cap, 2 GiB raw-output cap, and 900-second wall budget. The
prospective wall estimate was 120 seconds; observed watchdog wall was 47.51
seconds, peak RSS 894,910,464 bytes. Raw peak was 347,299,275 bytes; no output cap,
OOM or timeout tripped.

| Original group | Safe defined comparisons | Seeded defined comparisons | Seeded known UB exclusions | Domain sampled? |
|---|---:|---:|---:|---|
| classes | 16,658 | 16,658 | 0 | yes |
| templates | 25 | 25 | 0 | no |
| new_array | 500 | 0 | 500 | no |
| std_models | 8,360 | 6,658 | 1,702 | yes |
| omp | 19,783 | 19,783 | 0 | yes |
| atomics | 125 | 125 | 0 | no |
| floats | 11,909 | 11,909 | 0 | yes |
| dxc_summary | 3 | 3 | 0 | no |
| maa_summary | 35 | 30 | 5 | no |

**Counting unit:** 112,589 defined C/C++ input-comparison observations across 17
agreeing rows. These are not doubled language executions or unique sampled
inputs; the deterministic sampler can repeat draws. The eighteenth row is the
explicitly excluded, all-undefined allocation seed. No runtime sanitizer findings
or asymmetric sanitizer sets occurred. Original-precondition exclusions remain
separate in the per-row compact record and full requested domain.

All 15,768 declared physical-file references audited without mismatch. Raw files
remain under `/private/tmp/probata-agreement-full-e48a302e/`. Its
`native/agreement.json` SHA-256 is
`d7a15403a8a2dd7f3100563db2fd101d1f1d93905f26213af83641a8ae85f557`.
The compact record retains bounds, physical capacities, sampling flags and seed,
exclusion counts/reasons, source/contract/harness/domain/output pins, guards,
resources, reviewed pilot, controls and exact runtime tree.

The agreement freeze is separate from actual WP freezes `71771f09` and
`9b75f4a2`. Their production runtime bytes are identical; the old full seeded
artifact uses DXC +2, while this native matrix uses the corrected +4. No whole
seeded-artifact identity across profiles is asserted. Actual WP linkage must use
its relevant source, contract, callee and checker pins, audited by the WP owner.
Ordinary native agreement does not itself validate a member/terminal/conditional
WP source view, and an open WP goal is not a C++ counterexample.

The [independent full-profile review](t24-finite-agreement-final-review-20261015.md)
accepted this finite evidence: 15,768 references / 1,363 unique physical paths had
zero hash errors; all 112,589 defined observations were independently reconstructed
with zero return/buffer mismatches. It also reconstructed all 2,207 known UB and
47,164 original-precondition exclusions. No additional execution was needed.

The [compact record](t24-finite-agreement-20261015.json) preserves review hashes,
source/domain/output pins and resource metadata. Review Markdown and JSON are
retained beside it. The integration sync at `6ec49cf8` retains the complete native
freeze as an ancestor and changes none of its runtime, fixture, shared contract,
runner or CLI-control bytes. The accepted full nine-group run was not repeated.


