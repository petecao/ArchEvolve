# Public abstract memory traces — 2026-10-16 ET

**Source and an exact two-file integration proposal are ready. No public proof,
compiler, native, verifier or remote execution occurred in this preparation.**

1. `cases/` contains 25 fixed-order synthetic C++ callers with bodyless scalar
   ghost-query declarations. They exercise same-thread CPU hazards, another
   thread's successful/failed CAS and history values, preissue visibility,
   cross-thread region stalls, ownership, both tile halves and logical ready
   answers. These are explicit abstract model witnesses. No actual header call,
   source CPU operation, pointer, hardware schedule or refinement is certified.
2. `trace_fixture.py` emits the closed model and an isolated fixture-library
   builder. Two initialized abstract cells denote distinct physical lines;
   region IDs equal cell IDs by construction. There are four physical tiles,
   at most two issued commands and one later CPU write per unfinished gather.
   Four independently drawn, initialized harness cells supply four fresh choice
   bits; each used history/ready choice increments the index once. Exhaustion is
   a fatal `swdb.ghost_capacity` check. The model never consumes an undeclared
   extra native oracle value or silently reuses a choice. It has no polling
   termination/fairness or real interleaving claim.
3. `integration.patch` proposes changes only to `bounded_initialization.py` and
   `cbmc_adapter.py`; production is untouched. It freezes the complete canonical
   entry, exact four component hashes, constants, all ten query prototypes and
   `requires false` WP contracts. Every real interface declaration remains
   explicitly unsupported. Source imports reuse existing full-TU bodyless
   signature checks. The legacy hash policy, pointer domains, real-source
   certificates and default record wording keep their existing behavior.
   Exact trace records use abstract scope wording and omit the inapplicable
   at-issue/Rocq/pointer-ABI claims. Inherited physical trust entries are marked
   retained and unused; scope/domain/history assumptions are owned, immutable
   and recorded. WP has no usable query axiom.
4. `test_pure.py` passes 12 preparation/reference controls, including all 25
   expected traces over eight choice vectors. `test_policy_proposal.py` passes
   ten controls executing only the proposed hash gate against explicit
   stand-ins. These checks do not execute the generated C/C++, source parser or
   public proof path. The legacy policy and verdict fallback ASTs match their
   originals. One initial reference-domain test expected a region
   failure before establishing tile ownership; that test was corrected. No
   model/verifier success is inferred from either Python suite.
5. Root must review the final `integration-base.json`, recheck physical bases,
   integrate the two-file patch, and admit exact compiler/runtime/guard bytes
   before execution. `test_public_actual.py` is prospective, has exactly 25
   cases and fails before tool use without explicit root admission. An accepted
   run requires JUnit `tests=25`, zero failures/errors/skips, raw property and
   replay evidence, and a cold audit. Native agreement must have no capacity
   failures; positive traces must reach return. Refutations remain abstract
   model refutations. This bridge cannot close per-call/body/hardware/current
   0.2 or whole ticket 28 acceptance.

Preparation commands (standard library only, from this directory):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 trace_fixture.py
PYTHONDONTWRITEBYTECODE=1 python3 prepare_cases.py
PYTHONDONTWRITEBYTECODE=1 python3 propose_integration.py
PYTHONDONTWRITEBYTECODE=1 python3 test_pure.py
PYTHONDONTWRITEBYTECODE=1 python3 test_policy_proposal.py
```

`propose_integration.py` reads and hashes physical production files and refuses
an unexpected base. It writes only proposed copies and a unified diff here; it
does not apply the diff. The recorded bases matched `HEAD` when checked. No
installation, commit, branch, shared tracker update or held-out source read is
part of this slice.

The builder refuses the installed library path. It deletes only the copied 0.1
YAML from its disposable fixture library, since that YAML's validation would
otherwise read a kernel inventory. The installed readable 0.1 is untouched.

Postintegration control repair — 2026-10-16 ET: the old-AST comparisons now read
`base-source/` snapshots from exact `f918f5d52035fd99499280a0a8058efd0ed4ef55`,
verified against `integration-base.json` hashes. They no longer treat live
production as the old baseline after root's approved integration. Original
preintegration logs remain unchanged; the affected ten proposal and seven Linux
controls pass again in separate postintegration/normalization logs. The inert
trace entry now carries the exact parent-reviewed initialized V3 alias
normalizer before absolute preflight and project import. This author still made
no production edits or actual compiler/native/verifier/remote calls.
