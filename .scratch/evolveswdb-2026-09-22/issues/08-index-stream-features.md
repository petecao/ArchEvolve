# 08 — Index-stream features

Created: 2026-09-22
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 07
**Spec:** `../spec.md`

**What to build:** Profiles report exactly how an implementation's indices behave
(repeats, reuse distance, sequential runs, degree skew), computed from the index arrays
in the order the implementation visits them. No counters are needed.

- [ ] A small C++ tool, built against gapbs's own graph builder, regenerates the input's graph and walks the index array in visit order. It builds serially on the Mac and on mbit10.
- [ ] It reports the duplicate ratio, a log2-bucketed reuse-distance histogram, the fraction of sequential index steps, and the degree skew, all computed exactly.
- [ ] A tiny fixture graph with hand-computed values checks every feature.
- [ ] `swdb profile` includes these features as metrics, naming the tool, and fills the input's edge count with a measured value.

## Comments
