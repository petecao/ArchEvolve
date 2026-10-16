# Qualified017 WP import and generation-only passive audit

Created: 2026-10-16 ET. Status: prospective independent review of a completed
actual generation run. No actual rerun, solver invocation, model-body proof,
original-v2 contract proof or generic-caller acceptance is claimed.

The retained actual producer is
`/private/tmp/probata-t25-mac-qualified-generation-v1-01771a83-20261016`.
Root ran exact entry v3 (`ce792616c5b5cba4ce84e0f385251155211609b86547b9bb1420eae38e9417fc`)
with exact expected v3 (`866a8a3900722d86ae390e7f0e91cdb6e6b9d02524303e51777f7bc9008e7493`).
The immutable source was01771a839893975bba389ee0adcbec2aecdb88ac, recorded as an
ancestor of published integration2bf4a386423a3a427871fe10d15f8c1a6b6e1e29.
The component staged all310 exact Git package blobs and reconstructed all20
canonical grow targets; only `grow.entry.int_projection` was selected for this
separate feasibility component. Its packet digest is
`b5dbe9939b460efa5503b1cbba8a891f5cdb940a8d44835f3fd04da307a74b3f`.

The actual guard ended03:45:36 EDT with exit1 after7.153422s and peak207.421875MiB.
There was no watchdog kill, timeout, inspection event/failure or unconfirmed
child. Frama-C completed import and actual Why3 task construction. The executed
entry then refused a legitimate empty-ID IPModule metadata row. The original
`result.json`, exit1 and error remain unchanged. No generation result is being
rewritten as a successful entry execution.

The separate reader successor v4 recognizes exactly one source-bound module
metadata row: empty property identity, `kind=other`, line0, empty emitter,
no function/origin/dependencies, `extern=false`, `generated_smoke_failure=false`,
and the exact whitespace-normalized description `module heap_reallocation::Heap`.
It requires precisely that row and the selected global check lemma. The kernel's
selected `Property.ml` explains this shape: line493 prints `module@ name`,
line1090 gives IPModule no naming parts, and lines1365–1367 construct IPModule
for the imported source module. This is not a general empty-identity exception.
The reader normalizes formatting whitespace for the exact check-lemma description;
it does not accept additional tokens or arbitrary properties.

Pure retained-schema RED reproduced1 failure with12 hostile-input controls
already refusing. GREEN passed13/13 in0.15s (guard0.303323s,47.94MB). Controls
reject absent/duplicate/wrong/extern/dependent/misclassified module rows, unrelated
empty identities, externally assumed or dependent/wrong-description lemmas,
duplicate goals and a solver Valid result. No tool executable was invoked.

The final separate passive audit is
`/private/tmp/probata-t25-qualified-generation-passive-audit-v3-01771a83-20261016/audit.json`,
SHA256 `f9e67bde785f12d007aec1ad826762c441e709303fd877ae907d7f931bd2dd4f`.
It reports723 checks,1376 physical files and zero errors. It verifies exact producer
output membership and hashes, all310 source blobs, all20 independent canonical
packets, selected packet/theory, native-reader source, configuration/sentinel,
selected compiled packages and native-load closure. The57-file Why3 standard
library,30 WP support files and93 drivers remain exact. Trusted host OS dyld
shared-cache dependencies retain their explicit runtime boundary.

All actual evidence is retained: one ordinary goal with `passed=false` and empty
results, both production property rows, native verdict `none`/zero prover success,
CSV header only, and three complete normalized snapshots. The latter are emitted
by the three command stages, are byte-identical after framing, and each retains
only the exact source check lemma. There is no smoke goal for this global lemma;
no caller reachability or nonvacuity proof is inferred.

Two warning headers are present, both exactly `unused variable dummy` at the
selected theory's line25/characters18–23, during import and task compilation.
Both the exact path/location and theory digest are bound. There is no free-form
warning waiver. The original complete multiline diagnostic log is retained.

The printed Why3 theory contains precisely the source definitions `P_t25_fields`,
`P_t25_repr`, `P_t25v3_repr` and one unproved `wp_goal`. It contains no explicit
project axiom, lemma, constant or val. The `Heap::int_values` alias is actually
resolved to the unbounded functional type `int -> int`. The source variable map
is h→heap, values→t, r→i4, o→i3, b→i, bo→i1, s→i5, c→i2. The complete emitted goal
matches the original projection statement under that renaming, including its
bounded-int source-image premise and receiver/buffer-distinct-or-zero condition.
No desired projection conclusion was imported as a project assumption.

The transitive source import inventory is retained in `import-source-closure.json`.
It covers30 modules and56 source proposition declarations with full module text,
dependency edges and clone declarations/substitutions. Direct configured/emitted
imports are Bool, Int, ComputerDivision, Abs, RealInfix, Qed, Map, the project Heap
and Why3 BuiltIn. Heap has zero axioms or lemmas; its functions and predicates are
uniform definitions. The arithmetic/order, conversion, map and Qed declarations
belong to the explicitly pinned selected standard foundation. The56 count is a
source declaration inventory, **not** a count of flattened instantiated Why3
Task hypotheses; no independent proof of the standard library is asserted.
The BuiltIn typed core and selected standard/tool implementations remain part of
the declared trusted computing base.

`-wp-gen` is the decisive no-solver boundary: selected `ProverWhy3.ml` constructs
`task_of_wpo`, then returns `VCS.no_result` before `prover_task` or `automated`.
The fresh configuration has only the CVC5 selector with the pinned Python
sentinel command; actual solver binaries are absent from that command. Why3
autodetection is disabled. The sentinel's exclusive marker is absent and its
script/config digests remain exact. Printed generation output is not a physical
solver task-file claim or a formal proof.

Passive auditors v1/v2 remain preserved at distinct paths. V1 exposed a source
comment-token handling limitation; v2 correctly retained output but rejected the
three legitimate normalized snapshots as a single-snapshot expectation. V3
retains and checks all three snapshots. These are cold-reader corrections, not
changes to any original source, generated task, proof input or actual run.

The next acceptance step is a separately reviewed fresh whole public20-target
qualified-grow proof through the normal adapter/reader/deadline/persistence route.
It remains separate from original-v2 growth and source-derived caller discharge.
