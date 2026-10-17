# 13 — gapbs cc, cc_sv

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 11
**Spec:** `../spec.md`

**What to build:** The database covers the gapbs connected-components kernels,
exercising the pointer-chase address shape.

- [x] For cc (Afforest) and cc_sv (Shiloach-Vishkin): kernel records with verifier-based correctness checks, and baseline implementation records with access-pattern chains and semantics with basis.
- [x] The iterated compress loop (`comp[n] = comp[comp[n]]` until fixed) is a pointer chase. The single lookup in the link step is a single-valued indirect step on the same array.
- [x] Profiles on mbit10 for the four pilot inputs validate, and a view is generated for each pair.

## Comments

## Answer

Resolved 2026-09-22.

- One kernel `gapbs-cc` (ADR 0001: cc.cc and cc_sv.cc use the same CCVerifier, byte for byte)
  with baseline `gapbs-cc-afforest` and `gapbs-cc-sv` (upstream_alternative, code stored next
  to its record). The ticket said "kernel records"; one kernel with two implementations is
  what ADR 0001 requires.
- The iterated compress (`comp[n] = comp[comp[n]]`) is `stream > pointer_chase`; the link
  step's lookup is `single_valued_indirect` on `comp`; Afforest's hook is `compare_and_swap`,
  SV's plain check-then-store hook is `arbitrary` (repaired by the next sweep).
- Profiles on mbit10 for the four pilot inputs: 8 profiles, all complete and valid, views
  generated. cc_sv's sweeps come from its "Shiloach-Vishkin took N iterations" line
  (`run.sweep_count_regex`): 2 at scale 16, 3 at scale 22. Scale 16 parallelism_bound
  (urand cc_sv compute_bound); scale 22 memory_bound (latency).
