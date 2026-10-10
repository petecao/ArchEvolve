# 02 — First working v1: sources and the 5 source-code tables

Created: 2026-10-09
**Type:** slice
**Status:** wontfix
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** a v1 crosswalk document beside v0 that validates. It declares a list of
sources (the overview deck, slides 8–9, and the `DB_current_work` slide) and maps the five
source-code tables from the slide: `kernels`, `source_files`, `executables`, `definitions`,
`data_structures`. Identifiers are the slide's exact tokens (spec appendix); every row is
`unverified` and names its source. `kernels.slug` maps to the kernel ID; `definitions` and
`data_structures` are `no_counterpart` with a note naming them as contract anchors.

Source input: ask Yan-Ru for the `DB_current_work` PowerPoint path and record its SHA-256 (do not
copy the file into the repo). If Yan-Ru has no file, use the screenshot hash in the spec and say so
in the source note.

- [ ] The v1 document validates with `validate --crosswalk`
- [ ] The v0 document still validates
- [ ] A row citing a source `id` that is not declared is refused
- [ ] `status: verified` is refused in v1
- [ ] An invented research record kind is refused
- [ ] All five source-code tables appear with the slide's exact identifiers

## Comments

Superseded 2026-10-09 ET by [the LANL-shaped database spec](../../lanl-shaped-db-2026-10-09/spec.md): Yan-Ru wants the research database migrated to LANL's shape, not a mapping document.
