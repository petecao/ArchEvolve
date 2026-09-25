# 09 — Retrieve actionable profile packages and bidirectional strategy matches

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 07, 08
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution hold:** Publishing this ticket does not authorize implementation, builds, installations, benchmark/simulator runs, or remote execution. Wait for explicit user authorization.

## What to build

Assemble the preceding execution, discovery, source-context, and dynamic-memory evidence into a versioned profile package that an ensemble can retrieve and reference in a proposal. Support both finding applicable strategies for identified regions and finding stored implementations/regions relevant to strategy requirements. The package supplies evidence and constraints; it does not select the ensemble's strategy or promise a gain.

## Scope and spec references

This slice contributes AC01–AC05, AC07, and AC20 through D01–D06 and D14–D15. It turns earlier partial outputs into the complete profile-package contract where required evidence exists. Existing fixture packages used by route tests remain identifiable as fixtures; their use did not make this ticket a prerequisite for those earlier slices.

## Acceptance criteria

- [ ] A public request for an exact implementation/source, graph and traversal sources, target/configuration, threads, and ROI returns a stable, versioned package whose evidence belongs to that requested context.
- [ ] A complete package contains automatically discovered function/loop rankings, timing scope and attribution coverage, actual dynamic memory observations, source/build context, correctness/edit constraints, and applicable strategy/hardware information with explicit unknowns.
- [ ] A package with missing required timing or dynamic-memory evidence is returned as incomplete or unavailable with reasons; source-only facts or an entirely unavailable dynamic metric set cannot qualify it as complete.
- [ ] The package provides selected-region source plus necessary callers/helpers, types/headers, and access to the full buildable application snapshot. Source associations reflect current candidate code and preserve unresolved correspondence honestly.
- [ ] Forward lookup returns strategy records relevant to an implementation/profile/region with checked legality conditions, unresolved conditions, and reported benefit distinguished from measured outcomes.
- [ ] Reverse lookup from strategy requirements/effect returns relevant stored implementations and regions, distinguishing static applicability from matches backed by compatible profiling evidence.
- [ ] Unknown semantic facts or hardware support are not treated as satisfied requirements, and neither query direction guarantees performance or silently substitutes another workload or source.
- [ ] A package can be referenced by the established public patch workflow, and later result retrieval recovers that exact input package and its evidence. Regenerating the query index preserves these links.

## Verification

Use public profile/query, strategy lookup, proposal submission, and fresh-process result retrieval. Exercise real BFS discovery and dynamic observations from the prerequisite capabilities after authorization, plus isolated contract cases for stale identity, missing evidence, unknown legality, and both lookup directions. Compare returned behavior and artifact links rather than private joins. This package is our provisional contract, not proof of live Peter/Josh integration or performance gain.

## Dependencies and boundaries

Ticket 07 supplies loop discovery and changed-source associations; ticket 08 supplies actual memory observations. Their prerequisite chain supplies native execution and patch submission. DX100-specific operations and backend readiness may still be explicitly unavailable until later slices; that does not block native packages. Do not require live agents, a particular transport, full traces, or a general-purpose optimization selector.
