# O1 source provenance and candidate-literal review taxonomy

Date: 2026-10-08 (ET). Source-only local review; no observation, classification approval, coverage/admission, selection or cleanup is created.

O1 correction: the five `equivalence.source_sha256` / `compute_counts.<category>.source_sha256` leaves for `18505bf0e53496132ac3c4bf03881d804d6e0fd9dee51c5887fbda2190fd8393` identify exact retained Git source bytes, external to O1's runtime tree. `swdb-project/swdb/native/CpuWork.h` at both original calibration `97f5f196bd5e1c1405b2f24326e73761890f9930` and helper source `c1cd9077c58db5d093e1bc4c7545ab1899ec502b` is 1485B/blob `26f308a04e7570491931803c45c37fc0703d85dc` with that whole-byte SHA. They should be classified as retained-source provenance, not unresolved RAW-header preservation. Helper33 hashes the header beside supplied `--source`;34–35 requires prior source equality;80–85 uses that source and writes generated counting outputs to RAW. The actual absolute source argument remains unrecorded. Runtime `cda8f2db11996402bcb483bf98440eedc07feaa7` lacks this header. G96 1013–1027 requires a candidate-row HEAD for a physical source proof: neither distinct source commit may be substituted for O1's runtime HEAD. Keep O1 checkout and entire RAW protected; this correction grants no removal scope.

G96 966–988 allows candidate-literal metadata only through an exact per-file pin, `handling=historical_only_not_dereferenced`, and nonempty reviewed basis. Suitable source-specific bases, requiring parent's eventual review:

| Source class | Concrete review basis | What remains live or unresolved |
|---|---|---|
| Archived ordinary Python/Bash/Markdown controls | Exact bytes, original execution/disposition custody, and named reader/call sites establish an earlier command or source-review snapshot. A pathname embedded in archived source is history only when this exact source is not a queued/current invocation. | Current invocation/queue/aliases must independently exclude every selected route; `.py`/`.sh` suffix or age alone proves nothing. |
| Characterization YAML source/provenance | R15 saved `source.path` and region-binding locations remain exact history. `analytic_binding.py`159–234 ordinary verification resolves current registered application through `artifacts.source_root`; it does not dereference saved source.path/region locations. | `require_available=True`225–231 opens saved counted-output files. New execution or any custom literal-path reader requires an independent disjoint route. |
| Original compiler/projection argv | R14 original argv records a completed native projection; exact source/count/compiler hashes bind historical computation, not a future replay instruction. | Rebuilding/replaying that argv, queued compiler work, or mapped/FD references is an actual dependency. |
| Current aliases | G96 989–998 checks pending controls' bytes and explicit dereferenced paths, including strict resolved targets;1001–1010 separately pins future-source bytes. | Candidate-prefix targets, resolved symlinks or process references cannot be relabeled historical. Original RAW symlinks/references remain checked separately. |

The 2026-10-07 audit's zero literal hits across13 future sources is historical local evidence, not current alias or queue completeness. G96 explicitly inherits parent review at1030–1032; this note supplies bases only and sets no such fields.

Source pins:
- /private/tmp/lanl17-consumed-detached-source-reference-audit-20261007-r1.md: 19094B / SHA256 `1c95063ca5364d5bafa98f87fe745c1450811ffaae11c3b7673459f639e9d8d3`.
- /private/tmp/lanl_consumed_detached_source_guard_r4_20261008_r3.py: 88521B / SHA256 `96e033426d492fab3be2a07757ab1e89665a7a67d0f06d3941f274b1214dd294`.
