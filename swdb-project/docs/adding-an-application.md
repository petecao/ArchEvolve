# Adding records

Updated: 2026-09-28 (Eastern Time).

[Guide](README.md) · [Application field checklist](reference/adding-an-application.md)
· [Strategy field checklist](reference/adding-a-strategy.md)

Start from a similar record in `records/`. Use the [0.3 field reference](reference/format-v0.3.md)
for catalog records and the [0.4 additions](reference/format-v0.4.md) for explicit
source ownership and workflow records. The schemas and vocabularies define
accepted fields and values; older 0.2/0.3 records retain their original meaning.

## Application → kernel → implementation → input

1. **Pin the application source.** Record its URL, full commit, license, language,
   build command, and flags. For a small source copy (about 10 MB or less), keep
   the unchanged files in `apps/NAME/` with a dated `PROVENANCE.md`. For larger
   sources, provide a pinned fetch/checksum procedure and leave `local_path: null`.
2. **Define the kernel's correctness check.** State what it computes, the verifier,
   pass criterion, tolerance, command, and pass regex. Name its baseline
   implementation. Write the kernel and baseline together before validation
   because they reference one another.
3. **Describe each implementation's actual code.** Include exact source excerpts,
   build/run templates, relevant loops, and access patterns. A baseline refers to
   application source; derived code lives beside its record with a SHA-256.
   In format 0.4, name the implementation's application, source baseline,
   evaluator, and scoped verification. Its source ancestor and comparison
   baseline have different purposes.
4. **Describe the input.** Choose a generator or a file with a hash. Supply every
   input-property symbol used by array-size and trip-count formulas. An unknown
   value is `{value: null, basis: unknown}`.
5. **Validate and inspect.** Run the commands below, then collect measurements
   through the [profiling procedure](mbit10-profiling.md). Profile records are
   produced by the tool. Keep additions draft until human review.

```sh
python3 -m swdb validate
python3 -m swdb view IMPLEMENTATION INPUT MACHINE
python3 -m swdb add new-record.yaml --agent
```

Use `--agent` for agent-authored additions; it records agent provenance and draft
status. `add` validates before writing to the canonical record location and
rebuilding the index. To assemble mutually dependent records, place them together
in a working records directory and validate the whole set.

## Describe memory without guessing

One access pattern represents one memory-access expression. Its ordered steps
identify arrays and address shapes, ending at the target array; its update kind
records the mechanism used by the code. For example, a min operation implemented
by a CAS retry loop is `compare_and_swap`, with the min effect explained in a note.

Record all seven semantics with their basis: duplicate target indices, index
modification, loop-carried dependencies, shared targets between threads, required
atomic updates, ordering, and numerical requirements. Read-only sharing still
counts as shared targets. Unknown facts must remain unknown.

Use vocabulary-defined property symbols and supported arithmetic in size
formulas. If a size depends on runtime data that the model cannot express, use
`null` and explain why. Repeated references to the same array must agree on type,
size, and layout. State aliases so footprints do not double-count memory.
Application, kernel, and implementation records need their own source-code
provenance. Each `evidence_refs` value names provenance in that same record.

## Add a strategy or intrinsic

A strategy is identified by its **target plus typed effect**. Check existing
records before adding one; tile sizes and distances are parameters. Choose the
target (`access_pattern`, `loop`, or `input`) and effects such as reshape, add
pattern, hint, widen, reorder, or restructure loop.

Put checkable preconditions in the shape, update-kind, and semantic requirements;
put the rest in `unchecked`. Cite sources. `benefits_when` contains only reported
benefits; measured outcomes belong to implementation profiles. Unknown semantics
and unchecked requirements need attention before execution.

For an intrinsic, cite the vendor reference and record its exact C name, ISA
extensions, header, element width, lanes, and memory behavior. Its ID removes the
C name's leading underscores. Add missing vocabulary entries with definitions.
Add intrinsics before strategies that reference them.

```sh
python3 -m swdb sql "select id, target, json_extract(json, '$.effect') from strategies"
python3 -m swdb add my-strategy.yaml --agent
python3 -m swdb find --strategy STRATEGY_ID
```

Never reuse an ID for a replacement. Keep the old record deprecated and point to
the new one. For implementation work, use the repository's local
[tracker conventions](agents/issue-tracker.md).
