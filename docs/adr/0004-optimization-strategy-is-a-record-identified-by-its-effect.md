# An optimization strategy is its own record, identified by its target and effect

Date: 2026-09-23

Optimization strategies (packing, software prefetch, SIMD gather, vertex reordering,
tiling) and intrinsics are their own record kinds, not implementations: a strategy holds
no code, never runs, and applies to many kernels, while an implementation is code for one
kernel that passes its correctness check (ADR 0001). A strategy is identified by its
target type (access pattern, loop, or input) plus its effect, a set of typed changes
(reshape, add pattern, hint, widen, reorder, restructure loop); distances and tile sizes
are parameters, not new strategies. An implementation that uses a strategy is still an
implementation (`origin: derived`) and names the strategies it applies, in order, and the
intrinsics it calls; its required ISA is derived from those intrinsics.

## Considered Options

- **Strategies as implementations:** packing is not code for any one kernel and has no
  correctness check of its own.
- **Identity by published name:** names collide and diverge across papers, and the
  SW Ensemble Agent cannot search by name for what fits a given access pattern.
- **Effect as pattern class before and after only:** software prefetch and SIMD gather
  leave the pattern class unchanged, so both would look like doing nothing.
- **Intrinsics folded into strategies:** one intrinsic serves many strategies and carries
  facts a strategy lacks (ISA extension, lanes, memory behavior).

## Consequences

- Update kinds gain `prefetch`, so prefetches in real code can be recorded as access
  patterns.
- A strategy's legality for a pattern is `legal`, `illegal`, or `undetermined`; unknown
  semantic values never count as false.
- A strategy stores only reported benefit (`basis: reported`); measured benefit is
  computed from an implementation's profiles against its `derived_from` baseline's.
- Machine records at format 0.3 must list CPU flags so the ISA check can run; `swdb profile`
  refuses ISA-dependent code on a machine that lists none.
