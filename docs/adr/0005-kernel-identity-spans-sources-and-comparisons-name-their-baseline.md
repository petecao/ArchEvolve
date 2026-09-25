# Kernel identity spans sources, and comparisons name their baseline

Date: 2026-09-25
Status: accepted design; implementation pending separate authorization

Upstream GAPBS and DX100 BFS realize one computation and correctness check, so they
share a kernel identity while each implementation retains its exact application
source, baseline, and evaluation context. We chose this over separate
application-specific kernel identities so one BFS query can retrieve both without
duplicating their semantic identity. A performance comparison names its baseline
implementation and evaluation evidence explicitly; source ancestry identifies the
code rewritten and does not implicitly select the comparator.

## Consequences

- Extends ADR 0001 across application sources without changing its computation and
  correctness criterion. Source locations, build context, and executable check
  bindings must resolve to the actual implementation's source and target.
- Supersedes the ADR 0004 consequence that computes measured benefit implicitly
  against `derived_from`. A comparison may select that ancestor, a source baseline,
  or an author reference, but must identify the comparator and comparison protocol.
- The current single-application kernel schema and inherited application resolution
  do not implement this design. Record layout, migration, and evaluator bindings
  remain to be designed; this ADR authorizes no code changes or execution.
