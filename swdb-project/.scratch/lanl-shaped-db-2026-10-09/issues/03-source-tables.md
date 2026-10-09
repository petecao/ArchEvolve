# 03 — Source tables: source_files, executables, definitions, data_structures

Created: 2026-10-09
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02
**Spec:** `../spec.md`

**What to build:** the build fills four LANL tables with the slide's columns:
`source_files` (`kernel_id`, `path`, `language`) from source snapshot files and implementation
code paths; `executables` (`kernel_id`, `name`, `kind`, `path`) from each built program an
implementation record names; `definitions` (`source_file_id`, `name`, `kind` = `function`) from the
functions implementations and statements name; `data_structures` (`kernel_id`, `name`, `kind`) from
the arrays access-pattern steps name. Only what records name; no inference. Each row has its
origin. Can run in parallel with 04 and 05.

About 3 h.

- [ ] All four tables have exactly the slide's columns plus `id`
- [ ] A fixture implementation's code file, build, function and arrays each appear once in the right table
- [ ] `language` is NULL when the application does not state it
- [ ] Every new row has a `swdb_row_origins` entry; foreign-key and separability checks stay clean
