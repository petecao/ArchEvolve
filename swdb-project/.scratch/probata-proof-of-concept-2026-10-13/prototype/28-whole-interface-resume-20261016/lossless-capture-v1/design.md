# Lossless original-TU capture successor design

2026-10-16 ET. Source proposal; root owns actual admission and execution. V7 and
its failed actual output remain unchanged. No reduced projection is used.

The compact root metadata records successful preprocessing followed by caller
AST return code -25, exactly 134,217,728 stdout bytes, and accepted=false. That
supports the retained-file cap diagnosis. The partial AST does not establish a
complete TU, source-call census, ABI observation or proof result. Local metadata
receipt: evidence/t28-compiler-capture-v7-failure-metadata-20261016.json, SHA-256
c021c6cd2de3e060fff3581ba3772869a9184d7e26481343d58a7a35432fe745.

Root has prospectively approved a separate **512 MiB expanded-byte limit**. The
existing **128 MiB retained-file / 256 MiB total / 1 MiB finalization reserve /
4 GiB RSS / 165 s entry / 180 s guard** limits remain. Expanded bytes stay in
bounded process memory; no expanded temporary file evades the retained-file cap.
Actual DOM parsing time and memory remain acceptance gates. An OOM, timeout,
expanded overflow, incomplete JSON or any old semantic refusal remains failure.

Only the caller-ast transport changes. The same original `.cpp` source and
complete, unfiltered Clang JSON stdout are observed in one invocation. Its argv,
source-coordinate space and ephemeral declaration-ID scope stay unchanged.
Preprocessing and both ABI phases retain their exact existing behavior. A parent
collector reads the caller stdout pipe in at most 64 KiB blocks using a
nonblocking selector, checks the same deadline and total-output allowance, and
feeds stdlib zlib's streaming compressor with fixed gzip framing (wbits=31,
level=1, method=8, memLevel=8, strategy=0). There is no external compressor. The
child's file-size limit still protects its regular dependency/stderr files;
the parent separately enforces the retained gzip cap before every write.

The collector counts and hashes every expanded byte before compression and every
compressed byte before publication. It requires full pipe EOF and actual zero
compiler exit, then finishes exactly one gzip member. On a bound, timeout or
exception it kills and waits for the same owned process group, retains bounded
failure artifacts, and never invokes the consumer. The existing dependency
membership, source/runtime/control/guard and finalization rechecks remain.
Stderr is retained with its exact command result. Recipe and command records label
the compressed artifact explicitly; no compressed digest is called a raw JSON
hash. Root-readable full AST evidence is the gzip artifact plus exact raw and
compressed SHA-256/counts.

After close, the artifact is physically rehashed and checked against its stream
receipt. The bounded decoder reads the exact artifact incrementally, accepts only
a single gzip member, drains unconsumed input using a nonzero `max_length`, and
bounds every emitted chunk and the total expanded count. It requires EOF, no
unused/trailing data, no additional member, exact compressed SHA/count and exact
expanded SHA/count. Truncated, corrupted, concatenated and over-expanding input
refuses. It does not use `decompress.flush(length)` as an output bound: the Python
API describes that length as an initial allocation, so only bounded `decompress`
calls supply expanded data. Complete original JSON bytes then reach the same
strict UTF-8/duplicate-key/full-TU parser and unchanged declaration/body/ABI logic.
The APIs are documented by [Python 3.12 zlib](https://docs.python.org/3.12/library/zlib.html)
and the [zlib manual](https://www.zlib.net/manual.html).

Two existing ingress-accounting conditions need a narrow, independently reviewed
adapter successor. `parse_json_roots` currently enforces the 128 MiB raw-file gate;
for the verified compressed caller ingress it must instead receive an explicit
512 MiB expanded bound, while ABI input retains its original 128 MiB bound.
`prepare_unit` currently counts expanded caller JSON toward retained disk bytes;
the successor must count the physically retained compressed artifact plus ABI and
source/probe bytes, while separately checking the expanded count. The complete
parser and downstream logic remain unchanged. No global reassignment of
STAGE_BYTES, root-kind substitution, filtered AST join or semantic gate bypass is
permitted. Exact source inverses and pure tests must show those narrow changes.

The selected V7 runtime already pins `/usr/bin/python3.12` (8,020,928 bytes,
e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f),
`libz.so.1.3` (113,000 bytes,
86200da370f20476a2507e9097a789b5ef97269b4ca8d5e164ad82dab9d99892),
its exact alias and the complete stdlib filesystem surface. That alone does not
identify the selected interpreter's zlib import origin. Root is obtaining a
bounded selected-Python `-I -B` observation. If zlib is built in, its built-in spec,
loader and lack of a file must be bound to the exact interpreter/native closure.
If it is an extension, its actual canonical physical path, alias chain and ELF
loader closure must be freshly pinned. No arbitrary selector or module fallback
is admitted. Compression code imports only already gated stdlib facilities;
zlib is loaded after its origin gate, and the exact module is supplied to the
helper. Existing startup-role observations remain in force; the additional zlib
binding is explicit rather than a fabricated old origin observation.

Before freezing a controller, its policy must bind that actual root origin receipt
and any added physical files. Before actual launch, independent review must cover
single-TU transport, strict decode, ingress-only adapter inverse, exact resource
and final-input behavior, closed import environment and root runtime binding.
Private compiler preparation remains separate from complete source/CPU/model
integration, public 0.2 proof and ticket acceptance. Owned MMIO semantics retain
the already permitted TCB; this design adds no hardware/body theorem requirement.

Root's selected-Python observation has now settled. Exact retained receipt:
`evidence/t28-selected-python-zlib-origin-observation-20261016.json`, SHA-256
bc53f66a5c159b43af8b3fbc69a0ec367c39197589e57fd8af505e5730ae4e3d.
It reports built-in zlib, no extension file, and the already pinned libz mapping.
The successor checks the actual BuiltinImporter identity and those same physical
interpreter/library bytes before and after capture. The receipt's prose says
“fixed20-byte” for a literal whose actual source length is 17; that original
receipt is preserved. Its caption is excluded from the live binding and does not
supply a count, limit or roundtrip criterion.

The authored V8 keeps the inherited 45-second maximum per compiler phase. Root
can assess actual throughput under that existing bound; compression does not
promise a faster producer. Eighteen no-child controls now cover codec bounds,
strict decoding, exact adapter/controller and JSON inverses, unchanged runtime
and resources, root origin/physical membership, one-TU argv, mocked collector
success/failure and complete synthetic source binding equal to the old adapter.
No Clang or actual controller main ran during preparation. The retained test RED
was missing fixture class initialization in that last synthetic composition;
only the test's setup/cleanup changed to repair it.
