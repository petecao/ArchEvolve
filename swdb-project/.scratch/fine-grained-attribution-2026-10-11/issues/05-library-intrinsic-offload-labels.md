# 05: Library, intrinsic and offload labels

Created: 2026-10-11 15:14 ET
Updated: 2026-10-11 16:43 ET (resolved)
**Type:** task
**Status:** resolved
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F2; seam 1)
**Time estimate:** about 2–3 hours

**What to build:** Inside a rewrite site, `swdb attribute` labels executed typed-library operations as `library_call`, intrinsics as `intrinsic` and commands bound by the functional observation contract as `offload_command`, with precedence offload_command > intrinsic > library_call > agent_rewritten. libc and C++ standard library calls already in the baseline stay untouched.

## Acceptance

- [x] Fixture with an offload command and a library call in one site shows the precedence.
- [x] A baseline standard-library call outside any site stays untouched.
- [x] Per-origin seconds appear inside the rewritten group.

## Answer

Resolved 2026-10-11 16:43 ET on branch `fga/05-origin-labels`.

**Built** (all in `swdb attribute`; no estimator, protocol or prompt change)

- Regions **inside a rewrite site** are relabeled by what they execute, highest precedence first:
  `offload_command` > `intrinsic` > `library_call` > `agent_rewritten`. Regions outside every
  site are never relabeled, so baseline libc/C++ calls stay `untouched`.
- Signals (risks C7), read from the counted characterization only:
  - `offload_command`: `accelerator_calls[]` with a nonzero `execution_count` (named by `event`).
  - `intrinsic`: an executed `unmodeled_calls[]` entry (aggregate or any trial) named after a
    saved `intrinsic` record's C `name`, plain or as an Itanium source name (`<len><name>`).
  - `library_call`: an executed call naming a library operation's `location.symbol` the same
    way, or the region or one of its accesses located in the operation's `location.path`.
- New region field `evidence` (`[{origin, name}]`, every signal, precedence order) and reasons
  `offload_command_in_site`, `intrinsic_in_site`, `library_operation_in_site`.
- The `agent_rewritten` **group** keeps its name and holds every in-site region; it gains
  `origins`: four rows (per-trial sums, then medians) with seconds, shares and unknowns.
- Top-level `catalog`: `{kind, id, sha256}` of every intrinsic record / library operation that
  labeled a region; `swdb validate` re-checks intrinsic pins (library pins are replay-only,
  since `--library` may point outside the records folder).
- New option `--library` (default `library.default_root(records)`).
- SQLite: `swdb_attribution_origins`, appended inside the `swdb_attribution*` block of
  `swdb/db.py` (wraps `_insert_attribution`, does not edit it).
- Docs: `docs/reference/format-v0.4-attribution.md`, `docs/reference/database.md`; schema
  `schemas/attribution.schema.json`.

**Not detected yet (for later tickets)**

- ISA intrinsics already lowered to `llvm.*` calls (no catalog name to match).
- Inlined library code in a region whose own start line lies outside the source tree: it is
  `untouched`/`outside_source_tree` before the site check runs (ticket 04's inlining rule should
  route it into a site; the library-path signal then applies).

**Test command** (from `swdb-project/`): `python3 -m pytest -q tests/test_attribution.py`
(11 passed, about 37 s). `tests/test_format_doc.py` fails only on its two pre-existing non-attribution fields.

**Review fix (2026-10-11 22:10 ET, branch `fga/review-fixes`).**
- F34: `offload_command` needs a command the pinned description's functional observation
  contract names; an unbound executed command inside a site makes the region `unattributed`
  (`unbound_offload_command`).
- F33: a region's seconds inside unmodeled calls go to the `unattributed` group per trial; the
  region keeps the rest (new region field `unmodeled_calls`).
- `db.py`: the six chained `_Insert.attribution` reassignments are one ordered list
  (`_ATTRIBUTION_INSERTS`); `mixed` is stored as `int` everywhere.
