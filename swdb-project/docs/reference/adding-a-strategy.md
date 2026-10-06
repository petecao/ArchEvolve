# Adding an optimization strategy or an intrinsic

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-23

A procedure for a collaborator (or the SW Ensemble Agent) who wants to record a new
technique or a new intrinsic. The full field reference is [format-v0.3.md](format-v0.3.md),
sections 11 and 12. The words are in [GLOSSARY.md](../../GLOSSARY.md), and the identity rule is
[ADR 0004](../adr/0004-optimization-strategy-is-a-record-identified-by-its-effect.md).

## A strategy

1. **Find the sources first.** Every strategy cites at least one paper, person, or vendor
   reference. Read the source and note what it says about the technique, what it requires,
   and when it helps. A claim you cannot find in the source is left out, not paraphrased.
2. **Check for a duplicate.** A strategy is its target plus its effect. List the existing
   ones with `swdb sql "select id, target, json_extract(json, '$.effect') from strategies"`.
   If one has the same target and the same effect items, it is the same strategy. Link to
   it (or improve it) instead of adding a second record. Different distances, tile sizes, or
   lane counts are parameters of one strategy, not new strategies.
3. **Pick the target.** `access_pattern` if it changes one memory-access expression,
   `loop` if it restructures a loop nest, `input` if it changes the data (such as the
   vertex order).
4. **Write the effect as typed changes.** Use `reshape` (a step's address shape changes),
   `add_pattern` (a new pass such as packing, stated as its pattern class), `hint` (a step
   is accessed early), `widen` (several accesses per instruction), `reorder` (input
   properties change), or `restructure_loop` (tile, interchange, split, fuse). Steps count
   from 0, and -1 is the target step. Put numbers in `parameters`.
5. **Write the preconditions.** Put what the tool can check in `requires_shapes`,
   `requires_update_kinds`, and `requires_semantics` (the seven semantic facts). Put
   everything else in `unchecked`, in words. Unknown values make a result `undetermined`,
   never legal. Input strategies have prose preconditions only.
6. **Write the reported benefit** (optional). Each `benefits_when` item is a condition in
   terms of profile metrics, input properties, or cache sizes (`l1d_bytes`, `l2_bytes`,
   `llc_bytes`), with `basis: reported` and `source` naming the provenance entry that
   reports it. Measured benefit never goes here: it comes from profiles of implementations
   that apply the strategy.
7. **Name common intrinsics** (optional) in `common_intrinsics`. Each must be an existing
   intrinsic record, so add missing intrinsics first (below).
8. **Add it:** `swdb add my-strategy.yaml` (an agent adds `--agent`, which marks the record
   draft with an `agent_run` provenance entry). The whole folder is validated first and
   nothing is written on any error. A duplicate is rejected with the existing strategy's
   ID.
9. **Try it:** `swdb find --strategy <id>` (for an access-pattern strategy) lists where it
   could apply. `swdb strategies --pattern <impl>/<pattern>`, `--loop <impl>/<loop>`, or
   `--input <impl>` shows the outcome for one target.

## An intrinsic

1. Look it up in the vendor's reference (for x86, the Intel Intrinsics Guide) and note the
   exact C name, the CPUID flag(s), the header, the element width, the lane count, and what
   memory it touches.
2. The ID is the C name without its leading underscores (`_mm512_i32gather_ps` becomes
   `mm512_i32gather_ps`), and `name` keeps the exact C name.
3. Name the ISA extensions as `lscpu` prints them (`avx512f`, `sse`, `sse4_1`); add a
   missing one to `vocab/isa_extensions.yaml`. A new ISA family (Arm, RISC-V) is a new
   value in `vocab/isa_families.yaml`.
4. Set `memory_kind` and `address_shape`. `address_shape` is the shape the instruction
   itself forms (a gather's indices are `single_valued_indirect`), or null when it takes
   one address the caller computed or touches no memory.
5. Cite the vendor reference as a provenance entry of kind `vendor_reference` with its URI,
   then `swdb add` it.
