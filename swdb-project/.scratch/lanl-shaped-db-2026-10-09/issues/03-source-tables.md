# 03 — Source tables: source_files, executables, definitions, data_structures

Created: 2026-10-09
**Type:** slice
**Status:** resolved
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

## Answer

Resolved 2026-10-11 21:55 ET on `lanl-shaped-db` (commit 9fdfb9d4, merge 1410435c).
Built in `swdb/lanl_sources.py`. `source_files`: implementation code files and statement sources
(`<application local_path>/<path>` or `records/<path>`) plus files source snapshots keep
(`<artifact.path>/<path>`), one row per kernel and path with one origin per mention; `language`
only for files a record names as code, else NULL. `executables`: one row per implementation
build, `name` = implementation ID (the stated build output, `bin/<impl id>`), `kind`/`path` NULL
because no record names the binary file. `definitions` (`kind` = `function`): implementation
`function` (in `code[0]`'s file), statement functions, `run.kernel_symbols`, snapshot function
regions; `source_file_id` NULL where no record states the file. `data_structures`: one row per
kernel and access-pattern array, `kind` = stated layout or NULL. Tests:
`tests/test_lanl_sources.py` (21 pass); all LANL tests on the integration tip: 67 pass.
