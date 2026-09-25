# 07 — Discover BFS loops and rediscover changed hot regions

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 06
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution hold:** Publishing this ticket does not authorize implementation, builds, installations, benchmark/simulator runs, or remote execution. Wait for explicit user authorization.

## What to build

Extend public hotspot discovery from functions to loops inside BFS and its helpers, and demonstrate that reprofiling a real changed BFS candidate finds expensive work absent from the baseline catalog. Associate observations with current source, including changed or split/fused regions, without copying stale baseline region properties. Region timing is diagnostic evidence with declared scope; it does not independently establish an overall BFS gain.

## Scope and spec references

This slice completes the discovery behavior in AC02–AC03 and contributes AC13 through D03–D05 and D11. The native proposal/evaluation path is already available through ticket 06's prerequisites. A manually added region annotation must not be required to make the changed-code case discoverable.

## Acceptance criteria

- [ ] A public native BFS profiling query discovers and ranks attributable loops within BFS functions and helpers without mandatory manual loop annotations.
- [ ] Loop output identifies the current source/binary, containing function and source context, contribution metric, units, and whether timing is per invocation or accumulated across the BFS execution.
- [ ] Inclusive/exclusive attribution and unresolved work remain explicit across nested functions and loops, without double-counting their reported contributions.
- [ ] A real BFS candidate introduces expensive work in a helper or loop absent from the baseline catalog; after the normal candidate/evaluation path, reprofiling discovers, locates, and ranks that work without a person first adding it to the catalog.
- [ ] Reprofiled observations reference the candidate artifact rather than the baseline. Removed or changed regions do not retain unsupported baseline timing, access-pattern, or semantic assertions.
- [ ] Changed, split, or fused regions have explicit correspondence when one can be established; an unresolved correspondence cannot be used to manufacture a region speedup.
- [ ] Fresh-process queries recover both baseline and candidate rankings and the available correspondence, including differences between BFS-level and region-level observations.
- [ ] Collection failure or incomplete source attribution remains a retained partial outcome. Diagnostic runs performed before protocol freeze do not become candidate gain claims.

## Verification

Use the public patch-to-candidate, native evaluation, profiling, and retrieval path with actual changed BFS/helper code after authorization. The new-region discovery example must execute real code; canned profiler output alone cannot satisfy it. External fixtures may cover nested accounting and failed source mapping. Check observable output and artifacts, not private collector calls or internal module layout.

## Dependencies and boundaries

Ticket 06 supplies function attribution and source context; its prerequisite chain already supplies patch candidates and native evaluation. Natural-language or annotated-source workers are not required for this discovery demonstration. Memory observations and complete package acceptance arrive separately. General program extraction, full traces, and proof of every bottleneck cause remain outside this slice.
