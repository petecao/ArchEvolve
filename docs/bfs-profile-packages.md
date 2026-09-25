# BFS profile packages and strategy lookup

Date: 2026-09-25

Ticket 09 assembles evidence through `profile-package REQUEST`. The request names
an exact `evaluation`, optional `region_profile`, `implementation`, and `context`:
`source_sha256`, `canonical_graph_sha256`, ordered `sources`, `target`,
`target_configuration`, `threads`, and `roi`. A mismatch is rejected; omitted or
unavailable discovery and dynamic observations produce an incomplete package with
reasons. Execution fixtures remain labeled fixtures and cannot establish gains.

Packages use independent message version 1.0 and record format 0.4. Their
`package_version`, `requested_id`, and `identity_sha256` identify a retained
assembly. A new request creates a new version rather than overwriting an earlier
package. Evidence references and content identities survive index regeneration.

The package's source snapshot identifies the current evaluated candidate, including
the full buildable application. Selected regions retain exact source text and
hashed byte extents, callers/helpers, and header/type source access. Unknown source
correspondence remains explicit. An ensemble can use that snapshot and package in
the established patch proposal workflow to rewrite the code that was profiled.

The package's `strategies` retain applicability checks; `hardware` retains target
interfaces and explicit unknown support. Collector `discovery`, `artifacts`,
`executions`, and changed-source `correspondence` remain attached to their exact
evidence. Timing ranks retain inclusive/exclusive scope and discovery coverage. Memory
observations retain their collector, basis, scope, and diagnostic execution.
Diagnostic timing and simulated cache behavior do not replace primary native ROI
timing. A complete package needs discovered function and loop timing, primary ROI
timing, and at least one actual available dynamic-memory
observation. Partial attribution is explicitly reported even when these required
evidence categories exist. Correctness status is exposed independently: a complete
unverified simulated collection cannot promote an implementation or establish gain.

`profile-strategies PACKAGE [--region ID]` returns forward matches.
`strategy-regions STRATEGY [--package PACKAGE]` returns stored static applicability
and compatible package-backed regions separately. Known contradictions are illegal;
missing semantics and unchecked hardware requirements are unresolved. A rewritten
source does not inherit baseline semantic facts merely because line numbers or
function names match. Reported benefits remain literature statements, separate
from measured profile outcomes. Neither direction selects a strategy or promises
performance.
