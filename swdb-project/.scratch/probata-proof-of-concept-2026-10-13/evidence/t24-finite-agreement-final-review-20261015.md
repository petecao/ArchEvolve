# Ticket24 original finite agreement: independent final audit

Created: 2026-10-15 ET. **Accepted for the separate finite native C++/ordinary-C
agreement limb at frozen `e48a302e0081ce46d8c2f865568951913833d276`.**
No blocking artifact or outcome discrepancy was found. This closes the reviewed
finite-agreement profile, not the rest of ticket24 and not formal C++ equivalence.
No compiler, native binary, verifier, provider, test or remote job was launched
for this audit; retained files and original source definitions were read only.

Manifest: `/private/tmp/probata-agreement-full-e48a302e/native/agreement.json`,
SHA256 `d7a15403a8a2dd7f3100563db2fd101d1f1d93905f26213af83641a8ae85f557`.
Reviewed worktree `/private/tmp/probata-t24-agreement` still has that exact HEAD
and empty `git status --porcelain` at audit completion.

## Independently verified results

| Original group | Safe defined | Seeded defined | Known seeded UB exclusions |
|---|---:|---:|---:|
| classes |16,658|16,658|0|
| templates |25|25|0|
| new_array |500|0|500: original i<=n writes buf[n]|
| std_models |8,360|6,658|1,702: n==0 forms a-1|
| omp |19,783|19,783|0|
| atomics |125|125|0|
| floats |11,909|11,909|0|
| dxc_summary |3|3|0|
| maa_summary |35|30|5: n==INT_MAX, seeded n+1 overflow|

All18 rows are present in the expected original group/case order:17
`agree_on_defined_inputs`, one `excluded_undefined_only`. **112,589 defined
comparisons** agree. The **2,207 known UB exclusions** above stay separate from
**47,164 precondition-excluded** requests. There were zero retained runtime
sanitizer-index entries, sanitizer diagnostics or C/C++ UB asymmetries in this
full profile. Excluding UB before execution is not evidence that it executed
safely; the allocation seed supplies no numeric agreement on legal positive n.

Independent recursive physical audit rehashed **15,768 declared references across
1,363 unique resolved files: zero missing/hash errors**. Repeated references are
counted. The manifest itself was independently hashed as above. Artifacts include
generated inputs, contracts, harnesses, domains, binaries, raw/comparison/defined
outputs, runtime sources, compiler/configuration, physical headers and link inputs.

Cold reconstruction also checked:

1. Original safe TU equals the exact concatenation of pinned `GROUP_FILES`; seeded
   TU equals the exact current shared `SEEDED_BUGS` replacements, including dxc+4.
   Every C++ native input ends with that unchanged full TU and its retained common
   harness. dxc/maa C input contains exact real fixture `summary_impls.cc` bodies;
   C++ contains those same bodies. No summary stubs were substituted.
2. Every original contract was reconstructed from its pinned source definition;
   native normalization matches exactly, limited to equivalent atomics `*p/*e`
   to `p[0]/e[0]` lvalues. Each domain was independently rebuilt with the accepted22
   choices, Cartesian ordering or deterministic seed22 sample, recorded capacities
   and input draw order. All oracle lines and sampled labels match.
3. Original precondition feasibility and all three source-specific UB classifiers
   were independently evaluated for every requested input. Counts, excluded indexes
   and exact reasons match. Raw output maps to its original active oracle indexes;
   comparison/defined streams and their selection/hashes match on both sides.
4. Original fixture computations and returned/buffer poststates were independently
   interpreted for **all112,589 defined comparisons**, with zero mismatch. This
   includes class constructor/destructor effects, Ring arithmetic, copy/swap outputs,
   one-thread OpenMP, the full atomic/CAS update sequence, float32 weight conversion
   and binary64 `.17g` observations, corrected dxc+4 values/failing postcondition,
   and maa's actual no-op fixture callees. This is a retained-output semantic audit,
   not new execution or a general proof of either compiler.
5. Source freeze, full matrix completeness and all classification labels match.
   Resources record exit0,47.511s guarded wall,894,910,464bytes peak RSS and no
   timeout/OOM. Independently counted retained output:387files,347,299,523bytes,
   within the2,147,483,648byte budget. Resource observations were read from the
   original run, not remeasured by rerunning it.

The prospective template pilot and shared C-only mismatch/one-sided-UB/tamper/
UB-only controls were separately admitted in
`/private/tmp/probata-t24-agreement-pilot-review.md/.json`; no successful native
job was repeated here.

## Accepted boundary and remaining gaps

This is the accepted22 **finite native differential subcheck** on the original
ticket24 fixture profile. It uses original C++ and ordinary lowering with actual
fixture callees; integer native flags retain `-fwrapv`, floats use recorded native
IEEE observations, OpenMP is one-thread. Feasible finite samples do not establish
universal C++/C equality, symbolic-N concurrency or an unbounded allocation model.
The all-UB allocation seed is an explicitly excluded control, not an agreed
defined-output row. Additional allocation bug units are not silently credited
because their source appears in the combined TU.

Actual safe/seeded WP records, mandatory RTE/initializedness/smoke, model/summary
proof dependencies, unsupported-construct controls and source-to-WP-view relations
remain separate ticket24 acceptance requirements. Ordinary native agreement does
not execute or prove terminal-release/member/conditional WP transformations, and
no formal proof record should be synthesized from this report. Native device-call
fixtures exercise declared stand-ins, not gem5 or tickets27/28 semantics.

Link-time libraries/SDK stubs are physically pinned; dyld-cache runtime bytes remain
explicitly unverified. This does not provide unrestricted production standard-library
or allocator admission. Historical results must retain the frozen source/runtime
pins; future runtime changes require affected replay rather than relabeling these
results as current-source acceptance.

Compact independent audit: `/private/tmp/probata-t24-agreement-final-review.json`.
Its cold read-only reconstruction script is
`/private/tmp/probata-t24-agreement-cold-audit.py`.
