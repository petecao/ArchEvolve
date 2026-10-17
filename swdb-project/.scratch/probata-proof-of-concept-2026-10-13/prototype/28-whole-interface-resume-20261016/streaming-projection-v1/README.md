# One-stream original-TU projection proposal

2026-10-16 ET. Inert source preparation and synthetic controls only. No compiler,
remote job, actual AST, public proof or project import was used. Capture V7 and
all earlier source/statement/model packets remain unchanged.

A future controller can feed one complete unfiltered JSON observation from one
Clang parse of the original physical `.cpp` source to `project_stream`. It must
bind the original command, source/dependency/runtime before/after pins, exit code,
stderr, live resource guard and final retained manifest independently. EOF and a
hash do not establish compiler success. A preprocessed `.ii` buffer cannot supply
original `.cpp` byte offsets. Independently filtered dumps never join node IDs.

The prospective **input stream allowance is 512 MiB**, separate from retained
output. This is a proposed new root-admitted streaming profile, not an existing
V7 allowance or an authorized increase. The complete stream is counted, hashed
and parsed to EOF in 64 KiB reads; its full bytes are not retained by this module.
The existing **128 MiB per retained file and 256 MiB overall output limits remain**.
A prospective 96 MiB allocation for projection plus certificate leaves room for
other files inside that total. A future controller must allocate this pair quota
from its actual remaining allowance, retain the 1 MiB finalization reserve, and
keep its actual 165 s entry / 180 s guard / 4 GiB RSS limits. The standalone module
checks its allocated pair, not the complete future run directory. No budget or
runtime policy is changed by this proposal.

The tokenizer rejects malformed/truncated input, trailing or concatenated roots,
nonfinite/invalid numbers, malformed UTF-8 and escapes, duplicate object keys,
late selection metadata, reserved normalized/projection fields, unprofiled owned
AST edges, excessive depth/tokens/metadata/counts/work and over-budget output.
Structural IDs must be unique. Exact repeated canonical `*Type` nodes may share
an ID only when their kind and complete content Merkle fingerprint match.
Reference summaries are distinct from owned definitions; they cannot conceal
owned `inner` or `array_filler` edges.

Selection scans every owned node, including irrelevant scopes. It retains:

- The complete selected caller declaration/body and all its control/effects.
- Every API-name candidate and selected host-global/assertion declaration in
  every namespace/scope, so competing declarations cannot vanish in filtering.
- Every named typedef, type alias and enum with its complete owned subtree.
- Complete ancestor context, source locations and all definitions reached inside
  those selected subtrees. Any unresolved caller reference refuses.

The future concrete name set must include all 26 interface names, the 12 exact
host globals, the three source enums and applicable assertion declaration. The
preparation records that set from pinned source artifacts. The synthetic example
uses a smaller explicit set and is labeled accordingly. This profile does not
claim general C++ support: unknown caller AST families, heap/asm/statement
expressions, unknown direct calls, increment/decrement, volatile types and
selected macro API calls refuse. Exact assertion macro subtrees are retained;
the existing separate assertion/source statement checks still need a versioned
projected-input consumer. Supported node names alone do not prove scalar RTE,
argument sequencing, object lifetime or complete CPU/device routing.

Location normalization happens during the complete serialization traversal before
elision. Raw fields are retained, physical file/line elision is recorded, and
`presumedFile`/`presumedLine` never replace actual buffer identity. Every retained
node has a gap-free byte partition into raw gaps and its owned children, with
hashes and bounds. Elided subtree capsules carry raw bounds/hash, a canonical
content fingerprint, complete visited-node counts and zero matching-selection
counts. The certificate also retains the full named-declaration and node-ID
censuses and a complete-stream leading/root/trailing partition. All relevant
names, nested scopes, selected call/decl IDs and caller effect inventory come
from that single stream.

`verify_projection` is a separate passive structural reader. It verifies policy,
projection and receipt bindings, coverage, counts, selection propagation,
retained Merkle/ID links, competing-name retention, complete caller reference
closure and the allocated output quota. It cannot reconstruct or independently
reclassify discarded compiler bytes from hashes. The reviewed producer/parser,
normalizer, relevance classifier and compiler observations remain explicit TCB;
these certificates are not signed attestations or theorems. The retained RED
control initially tried to demand detection of an arbitrary changed ID inside a
fully discarded, nonselected subtree. That is unavailable from its raw hash.
The corrected control changes a retained API definition ID, which must and does
refuse. This limitation is stated, rather than turning a self-consistent digest
into evidence about discarded bytes.

The output root is `ProjectedOriginalTranslationUnitV1`, never
`TranslationUnitDecl`. A control extracts the exact old raw-TU parser and proves
it refuses this root. No helper changes the root kind back or feeds the partial
tree to an old consumer. Actual use requires a separately reviewed projection
consumer that understands capsules and preserves full-TU declaration/ABI,
source-body/default/substitution/provenance/global/statement gates. If required
closure or compiler metadata cannot fit this profile, the result refuses.

Work accounting bounds charged serialized metadata, partitions, retained trees
and census payloads while parsing. Fixed parser ceilings also bound depth, node,
ID and declaration counts. This is not a Python allocator/RSS theorem; actual RSS
must remain checked by the future unchanged 4 GiB guard. Actual compatibility,
throughput and retention size for the pinned Clang22 headers are unmeasured.

Thirteen synthetic no-child controls cover full-stream hashes, raw byte
partitions across seven-byte reads, nested/competing names, all named aliases and
enums, preserved assertion macros, duplicate IDs/keys, hidden AST ownership,
malformed/truncated streams, unmodeled caller effects, reference closure,
independent input/output/work limits, certificate mutations and old-reader
refusal. There is no production seam or actual source-call admission in this
packet; owned MMIO semantics remain the already permitted premise, with no new
hardware/body theorem requirement.
