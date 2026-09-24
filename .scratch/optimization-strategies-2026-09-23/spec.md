# Spec: Optimization strategies and intrinsics

- Created: 2026-09-23
- Updated: 2026-09-23
- Status: ready-for-agent
- Owner: Yan-Ru Jhou
- Glossary: `CONTEXT.md` (Optimization strategy, Strategy effect, Intrinsic; update kind
  `prefetch`). Decisions: ADR 0001 (kernel identity), ADR 0002 (YAML master copy),
  ADR 0003 (access pattern as chain of steps), ADR 0004 (strategy identity).
- Source: grilling session of 2026-09-23 (Q1–Q16, all recommendations accepted) and the
  spec review of the same day (version rule, intrinsic IDs).

## Problem Statement

The Software Database records what each kernel computes, how each implementation
touches memory, and what profiling measured. It does not record the reusable techniques
that change that behavior, such as packing, software prefetch, SIMD gather, vertex
reordering, and loop tiling, nor the intrinsics that code calls to apply them.

So the SW Ensemble Agent, asked to improve a kernel, has nowhere to look up:

- which techniques are legal for a given access pattern, and which facts are still
  unknown before it can tell;
- what a technique changes about the access pattern, the loop, or the input;
- what a technique or an intrinsic needs from the ISA, and whether a machine has it;
- which implementations already apply a technique, and whether their profiles beat the
  baseline.

An optimized implementation today can only say "derived from X" in prose. Nobody can ask
the database "every kernel with a software-prefetch version" or "strategies legal for
this gather". A strategy is not an implementation: packing is not code for any one
kernel and has no correctness check of its own.

## Solution

Two new record kinds, links from implementations to them, CPU flags on machine records,
and new queries, all through the existing `swdb` command line and the existing
YAML-in-git records (ADR 0002).

- **Optimization strategy** records hold no code. Each states its target type (access
  pattern, loop, or input), its strategy effect (a set of typed changes), its
  parameters, its preconditions, the benefits sources report, and its sources. Its
  identity is its target type plus its effect (ADR 0004).
- **Intrinsic** records describe one ISA instruction wrapper: its exact C name, ISA
  family and extensions, header, memory kind and address shape, element width and
  lanes, and a reference.
- **Implementations** may list, in order, the strategies they apply (with target and
  parameters) and the intrinsics they call. Their required ISA is derived from those
  intrinsics and checked against the build flags and the machine.
- **Machines** list the CPU's ISA flags, captured read-only.
- **Queries:** strategy legality for one access pattern, one loop, or an
  implementation's input; access patterns a strategy could apply to; a kernel's
  implementations that apply a strategy, next to their baselines' profiles.

## User Stories

### Recording strategies

1. As the database owner, I want each optimization strategy in its own YAML record with the common envelope, so that it is read, diffed, and reviewed like every other record.
2. As the database owner, I want a strategy to state one target type — access pattern, loop, or input — so that it is clear what the strategy acts on.
3. As the database owner, I want a strategy's effect recorded as a set of typed changes (reshape, add pattern, hint, widen, reorder, restructure loop), so that effects are comparable, not prose.
4. As the database owner, I want a reshape change to name the step it changes and the address shape before and after, so that "indirect becomes stream" is stated exactly.
5. As the database owner, I want an add-pattern change to state the pattern class of the access pattern the strategy adds, so that the cost of a packing pass is visible.
6. As the database owner, I want a hint change to name which step is accessed early, so that software prefetch is distinguishable from doing nothing.
7. As the database owner, I want a widen change to state lanes per access, as a number or a parameter name, so that SIMD gather is distinguishable from a scalar gather.
8. As the database owner, I want a reorder change to name the input properties it changes, using the existing input-property and index-locality vocabularies, so that vertex reordering is described in terms the profiles measure.
9. As the database owner, I want a restructure-loop change to name a loop restructure from a vocabulary (tile, interchange, split, fuse), so that loop strategies are comparable.
10. As the database owner, I want numbers such as prefetch distance, tile size, and lanes declared as named parameters of a strategy, so that different values never create new strategies.
11. As the database owner, I want a new strategy rejected when its target type and effect set equal an existing strategy's, naming the existing one, so that duplicates cannot accumulate.
12. As the database owner, I want strategy preconditions written with the existing address shapes and semantic fields, so that legality is computed from facts the access patterns already record.
13. As the database owner, I want validation to fail when a precondition names a semantic field or value that does not exist, so that typos never make a strategy look legal.
14. As the database owner, I want a prose list of preconditions the tool cannot check, so that conditions outside the model are still written down.
15. As the database owner, I want each reported benefit condition written in terms of profile metrics, input properties, or machine cache sizes, with `basis: reported` and a source, so that claims from papers are marked as claims.
16. As the database owner, I want validation to fail when a reported benefit has no source or a basis other than reported, so that no measured-looking number enters a strategy.
17. As the database owner, I want a strategy to list intrinsics commonly used to apply it, as suggestions, so that an agent knows where to start.
18. As the database owner, I want every strategy to cite at least one source, so that each technique is traceable to the literature or a person.

### Recording intrinsics

19. As the database owner, I want each intrinsic in its own record, so that its facts are stated once and shared by every strategy and implementation that uses it.
20. As the database owner, I want an intrinsic's ID to be its C name without leading underscores, and its exact C name in its own field, so that IDs follow the existing ID rule and the name stays exact.
21. As the database owner, I want an intrinsic to name its ISA family and the ISA extensions it needs, as `lscpu` flag names, so that support is a direct match against machine records.
22. As the database owner, I want an intrinsic to state its memory kind (gather, scatter, masked load, masked store, prefetch, non-temporal store, load, store) and the address shape it performs, so that its memory behavior matches the access-pattern model.
23. As the database owner, I want an intrinsic to state element width and lane count, so that widen effects can be checked against it.
24. As the database owner, I want an intrinsic to cite a vendor reference, so that its facts are checkable.
25. As the database owner, I want ISA families, extensions, and memory kinds kept in vocabularies, so that Arm NEON/SVE or RISC-V V can be added later without a schema change.

### Linking implementations

26. As the database owner, I want an implementation to list, in the order applied, the strategies it applies, each with its target and parameter values, so that combined strategies are recorded faithfully.
27. As the database owner, I want validation to fail when an applied strategy's target is not a loop or access-pattern ID in the same implementation, or does not match the strategy's target type, so that links never dangle.
28. As the database owner, I want validation to fail when an applied strategy gives a parameter the strategy does not declare, so that parameter names stay consistent.
29. As the database owner, I want an implementation to list the intrinsics its code calls, so that its ISA needs are known.
30. As the database owner, I want an implementation's required ISA derived from its intrinsics, not written by hand, so that it cannot drift from the code.
31. As the database owner, I want validation to fail when an implementation's build flags do not enable its required ISA, and to report a `-march` value it cannot interpret rather than guess, so that a build never silently lacks an extension.
32. As the database owner, I want existing implementation records to stay valid without edits, so that adding strategies costs nothing for records that do not use them.

### Machines

33. As the database owner, I want `swdb capture-machine` to store the CPU's ISA flags, so that the database knows what each machine can execute.
34. As the database owner, I want machine records that declare the new format version to be required to list CPU flags, while older records stay valid, so that the change stays a minor version under the format's versioning rule.
35. As the database owner, I want mbit10's machine record recaptured with its flags, so that ISA checks run on the only lab host.
36. As the database owner, I want `swdb profile` to refuse an implementation whose required ISA the machine's flags lack, or whose machine lists no flags, before any host check, build, or run, so that no profile runs code the machine may not execute and unknown support is never treated as support.

### Querying (SW Ensemble Agent)

37. As the SW Ensemble Agent, I want to list every access-pattern strategy for one access pattern as legal, illegal, or undetermined, so that I know what to try.
38. As the SW Ensemble Agent, I want an undetermined result to name the semantic fields that are unknown, so that I know exactly what to find out first.
39. As the SW Ensemble Agent, I want prose preconditions always listed as "check by hand", so that I never mistake an unchecked strategy for a checked one.
40. As the SW Ensemble Agent, I want each strategy's reported benefit conditions shown next to its legality but never used to filter, so that I can rank candidates without paper claims hiding options.
41. As the SW Ensemble Agent, I want to find every access pattern a given strategy is legal or undetermined for, across kernels, so that I can spread a strategy that worked on one kernel.
42. As the SW Ensemble Agent, I want to check loop strategies against one loop, with every access pattern in that loop and its child loops required to meet the preconditions, so that tiling-like strategies are queryable too.
43. As the SW Ensemble Agent, I want to list input strategies for one implementation, with their prose conditions marked "check by hand", so that input-side techniques such as vertex reordering are not invisible.
44. As the SW Ensemble Agent, I want to list a kernel's implementations that apply a strategy, each paired with its `derived_from` baseline and the newest complete profile of both per input and machine, so that I can see whether the strategy helped.
45. As the SW Ensemble Agent, I want every query result as YAML or JSON, so that I parse results without scraping text.
46. As the SW Ensemble Agent, I want to add strategies and intrinsics with `swdb add --agent`, marked draft with an agent-run provenance entry, so that my additions go through the same validation as a person's and are visibly unreviewed.
47. As the SW Ensemble Agent, I want my duplicate strategy rejected with the existing strategy's ID, so that I can link to it instead.

### Documentation

48. As a collaborator, I want the format document to cover strategies, intrinsics, and the new implementation and machine fields, so that the written format matches what the tool enforces.
49. As a collaborator, I want a written procedure for adding a strategy or an intrinsic (sources, effect, preconditions, duplicate check), so that I can contribute without reading the code.
50. As a collaborator, I want the query documentation to describe the three new queries and their output, so that agents and people use them the same way.

## Implementation Decisions

### Modules

- **Vocabularies:** new vocabularies `strategy_targets` (access_pattern, loop, input),
  `effect_kinds` (reshape, add_pattern, hint, widen, reorder, restructure_loop),
  `loop_restructures` (tile, interchange, split, fuse), `isa_families` (x86 now),
  `isa_extensions` (`lscpu` flag names, starting with those the seed intrinsics need),
  `intrinsic_memory_kinds` (gather, scatter, masked_load, masked_store, prefetch,
  non_temporal_store, load, store). `update_kinds` gains `prefetch` ("a non-binding early
  access that returns no data"). `record_kinds` gains `strategy` and `intrinsic`. All
  are additions, so the format version goes from 0.2 to 0.3 as a **minor** change.
- **Schemas:** new schemas for the strategy and intrinsic kinds. Implementation schema
  gains optional `applies` and `uses_intrinsics`. Machine schema gains optional
  `cpu.flags`. The envelope accepts `schema_version` "0.2" and "0.3". Only local
  `$defs` references (jsonschema 4.10, no cross-file `$ref`).
- **Record store and writer:** the two new kinds get canonical folders (strategies,
  intrinsics) so `swdb add` writes them like other kinds.
- **Cross-record rules:** the validator gains checks for effect shapes, precondition
  terms, duplicate strategies, applied-strategy targets and parameters, intrinsic
  references, required ISA versus build flags, and CPU flags on 0.3 machine records.
- **Machine capture:** parses the `Flags:` line already present in `lscpu` output into a
  sorted list.
- **SQLite build:** new tables for strategies, intrinsics, and applied strategies,
  generated from records like the rest (ADR 0002). Nothing in them is edited by hand.
- **Legality evaluator:** one function, shared by the two strategy queries, that takes a
  strategy and an access pattern and returns an outcome with reasons. It reuses the
  existing semantic columns and their "unknown is not false" handling.
- **Command line:** a new `strategies` command (with `--pattern`, `--loop`, or `--input`); `find` gains `--strategy`;
  `implementations` gains `--applies`. All support `--format yaml|json`.
- **Profile:** an ISA check placed with the other record-level checks, before the host
  check and before any build.

### Record shapes (contract)

- **Strategy:** envelope; `name`; `target` (a `strategy_targets` term); `effect` (a
  non-empty list, each item a `kind` from `effect_kinds` plus that kind's fields);
  `parameters` (name, meaning, unit or null); `preconditions` with `requires_shapes`,
  `requires_semantics` (field and value pairs), and `unchecked` (prose list);
  `benefits_when` (optional list: condition, `basis: reported`, provenance ref);
  `common_intrinsics` (optional list of intrinsic IDs); at least one provenance entry of
  a source kind.
- **Effect item fields by kind:** reshape: step position, shape before, shape after.
  add_pattern: the added pattern's address shapes and update kind. hint: step position.
  widen: lanes (number or parameter name). reorder: input properties changed.
  restructure_loop: a `loop_restructures` term.
- **Intrinsic:** envelope; `name` (exact C name); `isa_family`; `isa_extensions` (list);
  `header`; `memory_kind`; `address_shape` (or null for non-memory intrinsics);
  `element_bits`; `lanes`; a provenance entry citing the vendor reference.
- **Implementation additions:** `applies` is an ordered list of `{strategy, target,
  parameters}`. `target` is a loop or access-pattern ID in the same record, or `input`.
  `uses_intrinsics` is a list of intrinsic IDs.

### Rules

- **Duplicate strategy:** two strategies are duplicates when their targets are equal and
  their effect sets are equal, comparing each effect item's kind and fields and
  ignoring parameter names and values. The error names the existing strategy.
- **Legality:** `illegal` when any required shape is absent or any required semantic
  value is known and different. Otherwise `undetermined` when any required semantic
  value has basis unknown, naming the fields. Otherwise `legal`. The `unchecked` prose
  is listed with every outcome as "check by hand".
- **Required ISA:** the union of the extensions of the implementation's intrinsics. The
  build satisfies it when each extension is enabled by an explicit `-m<extension>` flag
  or by a `-march` value the tool knows includes it. An unknown `-march` value fails
  validation with a message naming it, instead of passing silently.
- **Machine flags:** optional at 0.2, required at 0.3. `swdb profile` refuses when the
  implementation needs an extension and the machine lists no flags or lacks it.
- **Composition:** `applies` order is the order applied. Targets refer to the final
  code. No conflict rules between strategies; the correctness check catches bad
  combinations.
- **Benefit:** strategies store only reported benefit. Measured benefit is derived at
  query time from an implementation's profiles against its `derived_from` baseline's.
- **Agent records:** strategies and intrinsics from agents are draft with agent-run
  provenance, exactly as for other kinds.

### Query output (contract)

- `strategies --pattern <implementation>/<pattern>`: one entry per access-pattern
  strategy with `strategy`, `outcome`, `reasons` (for illegal), `unknown_fields` (for
  undetermined), `check_by_hand`, and `benefits_when`.
- `strategies --loop <implementation>/<loop>`: the same entry shape for each loop
  strategy; a loop strategy is legal only when every access pattern in the loop and its
  child loops meets its preconditions, illegal when any known value contradicts, and
  undetermined otherwise, naming the pattern and field of each unknown.
- `strategies --input <implementation>`: the same entry shape for each input strategy;
  their preconditions are prose, so each is listed with `check_by_hand` filled.
- `find --strategy <id>`: one entry per access pattern with `implementation`,
  `pattern`, `outcome`, and `unknown_fields`; illegal patterns are left out.
- `implementations <kernel> --applies <id>`: one entry per implementation with its
  `applies` entry, `derived_from`, and per (input, machine) the newest complete profile
  ID of the implementation and of the baseline, or null when either is missing.

## Testing Decisions

- **One seam, the existing one:** every test runs `swdb` as a separate process against a
  temporary records folder, through the shared test helpers. No test imports modules to
  call internals. Tests assert on exit codes, stdout (parsed YAML or JSON), stderr
  messages, and files written.
- **Every validation rule gets one passing and one failing fixture:** each new vocabulary
  term use, each effect kind's shape, duplicate strategy, unknown precondition field,
  applied-strategy target (missing ID, wrong target type), undeclared parameter,
  missing intrinsic, required ISA versus build flags (explicit flag, known `-march`,
  unknown `-march`), machine at 0.3 without flags.
- **Legality:** tests cover legal, illegal (shape and semantic), and undetermined (a
  semantic value with basis unknown), plus prose conditions always shown; for loop
  strategies, one failing pattern in a child loop makes the loop illegal.
- **Versioning:** a test that every existing record in the repo still validates, and a
  0.2 machine record without flags still validates.
- **Profile refusal:** a fixture machine without `avx512f` and a fixture machine with no
  flags are both refused before the host check, so the test runs on the Mac.
- **Capture:** the saved mbit10 capture fixture already contains a `Flags:` line; the
  parse test asserts `avx512f` is in the parsed list. No new capture fixture is needed.
- **Format document per ticket:** the format-document coverage test fails whenever a
  schema field is undocumented, so each ticket documents its own fields; a first
  prefactor ticket makes the tool accept 0.3 and creates the v0.3 document.
- **Prior art:** validation-rule tests, `add` tests, database query tests, machine
  capture tests, profile refusal tests (the "refuses another host's machine" test), and
  the format-document coverage test, which must point at the new format document.

## Out of Scope

- Writing or profiling real implementations that apply a strategy (for example packed or
  prefetch PageRank). A later ticket.
- Conflict or ordering rules between strategies.
- Generating code from a strategy.
- Arm and RISC-V intrinsic records. The vocabularies leave room; none are recorded now.
- Predicting profitability beyond displaying reported benefit conditions.
- A server interface (HTTP or MCP). Agents keep using the command line.
- Any change to the workload view the HW Ensemble Agent reads.

## Further Notes

- **Seed records:** five strategies and two intrinsics. `packing` (access pattern;
  reshape plus add pattern), `software_prefetch` (access pattern; hint; parameter
  distance), `simd_gather` (access pattern; widen; parameter lanes; common intrinsic
  `mm512_i32gather_ps`), `vertex_reordering` (input; reorder), `loop_tiling` (loop;
  restructure loop tile; parameter tile size). Intrinsics `mm512_i32gather_ps`
  (`_mm512_i32gather_ps`, x86, avx512f, gather) and `mm_prefetch` (`_mm_prefetch`, x86,
  sse, prefetch). No new implementations.
- **Sources to verify before citing:** Goto and van de Geijn (ACM TOMS 2008) for
  packing; Ainsworth and Jones (CGO 2017) for indirect software prefetch; Wei et al.
  (SIGMOD 2016, Gorder) and Balaji and Lucia (IISWC 2018) for vertex reordering; Wolf and
  Lam (PLDI 1991) for tiling; the Intel Intrinsics Guide for the two intrinsics. A claim
  that cannot be verified is left out, not paraphrased.
- **mbit10:** Intel Xeon Gold 6326. The saved capture's flags include `avx512f`,
  `avx512vl`, `avx512bw`, `avx512dq`, and `avx512cd`. The recaptured record, not this
  note, is the fact of record.
- **Versioning:** making `cpu.flags` required for all machines would be a major change
  under the format's rule; requiring it only at 0.3 keeps this a minor release.
