# 13 — gapbs cc, cc_sv

Created: 2026-09-22
**Type:** slice
**Status:** claimed
**Blocked by:** 11
**Spec:** `../spec.md`

**What to build:** The database covers the gapbs connected-components kernels,
exercising the pointer-chase address shape.

- [ ] For cc (Afforest) and cc_sv (Shiloach-Vishkin): kernel records with verifier-based correctness checks, and baseline implementation records with access-pattern chains and semantics with basis.
- [ ] The iterated compress loop (`comp[n] = comp[comp[n]]` until fixed) is a pointer chase. The single lookup in the link step is a single-valued indirect step on the same array.
- [ ] Profiles on mbit10 for the four pilot inputs validate, and a view is generated for each pair.

## Comments
