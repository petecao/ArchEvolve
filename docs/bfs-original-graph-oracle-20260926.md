# Independent original-graph verification

Created: 2026-09-26 (Eastern Time)

Generated complete-call candidate wrappers now use adapter
`dx100.complete_call.v2` and the `swdb.bfs.original-adjacency.v1` contract. The
previous wrapper checked the returned parent array with `BFSVerifier` over the
same mutable `Graph` passed to the candidate. A candidate that replaced all
neighbors with self-loops could make the original path 0–1–2 appear disconnected
and obtain PASS for `[0,-1,-1]`. The protected verifier source did not prevent
its input from changing. A compiled regression using the actual upstream
source and unchanged `BFSVerifier` reproduced this false PASS before the fix.

Before checkpoint creation and the complete-call ROI, the trusted wrapper
reads the serialized file named by the evaluator's exact `-f` argument and
captures the exact `-r` source. Its own SG32/SG64 little-endian reader retains
private outgoing CSR arrays, independently of candidate `Builder`, `Graph`,
headers, and accessors. Registered-workload execution already verifies the
serialized bytes against the canonical adjacency and rehashes the original
representation and any `.sg` loader alias. That existing path/hash/command
binding establishes which original graph the oracle loads; the guest does not
invent a second canonical identity. Registration validates inverse adjacency
and symmetry; the guest oracle checks full file length and normalized outgoing
CSR, and uses only outgoing edges for BFS truth.

After the same complete-call ROI ends, an independent O(V+E) traversal validates
the exact returned parent buffer. It requires the original vertex count,
bounded parent IDs, the source pointing to itself, correct reachability,
original parent edges, and shortest-path depths. The candidate may mutate its
own graph and still pass if its returned tree is valid for the original graph.
No candidate graph accessor or `BFSVerifier` supplies post-execution truth.
This is an ordinary C++ correctness contract, not a sandbox against arbitrary
undefined behavior or intentional corruption of unrelated process memory.

The parser bounds extra oracle allocation before graph-sized allocation:

`8*(V+1) + 4*E + 9*V + 65,536 <= 2,147,483,648 bytes`.

These terms are 64-bit offsets, 32-bit neighbors, 32-bit depth and fixed BFS
queue arrays, one byte per vertex for parent-edge membership, and a small-object
reserve. Every oracle and checker array is allocated before the ROI, with no
growing BFS queue. Malformed counts, offsets, neighbors, lengths, missing source
arguments, and over-budget graphs fail before checkpoint creation. The modeled
guest remains 16 GB. Allocation/preloading can affect caches and memory use, so
this wrapper is a new treatment; it cannot reuse an older frozen wrapper
identity or checkpoint.

`context.graph_verification` and
`context.instrumentation.graph_verification` carry the same stable mapping:
`contract`, `input_format`, `byte_order`, `adjacency`, `maximum_extra_bytes`,
`preload`, `verification`, and `allocation`. These fields explicitly place graph
preloading and checker work outside the ROI. `context.verifier_source` identifies
the generated trusted wrapper with its exact `path`, `sha256`, `symbol`, and
`bounds_check`. `context.protected_bfs_verifier` preserves the separately
protected source verifier reference. The shared standalone
`graph_verification_contract(application)` factory selects `gapbs.sg64` for
upstream GAPBS and `gapbs.sg32` for DX100.

Execution rejects legacy complete-call builds lacking the new adapter, exact
contract, or wrapper verifier identity before checkpoint/restore. The v2
completed-witness validator also requires the contract and its frozen
instrumentation identity. The generic comparison/coverage verifier gate applies
this requirement to both v1 and v2 DX100 complete-call verdicts and independently
checks every actual hashed aggregate component. Existing records and raw
outcomes remain unchanged and retrievable. The unchanged pinned author primary and author-ROI diagnostic
keep their original traversal/verifier treatment; the latter explicitly selects
`trusted_graph=False` and is permitted only for unchanged author source.

Validation uses locally compiled C++ wrappers with explicit no-op m5 stubs,
the real upstream BFS source/protected verifier, and hand-constructed SG32/64
inputs. The SG32 fixture changes only the upstream loader's offset typedef to
exercise that representation. These tests establish wrapper semantics and
failure boundaries; they are not DX100 execution or performance evidence.
