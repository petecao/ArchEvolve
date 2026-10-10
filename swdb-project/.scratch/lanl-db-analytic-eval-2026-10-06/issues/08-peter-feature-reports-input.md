# 08 — Peter's feature reports as an input

Created: 2026-10-06
**Type:** slice
**Status:** resolved
**Blocked by:** 05
**Spec:** `../spec.md`
**Time estimate:** 3–4 h

**What to build:** A reader imports Peter's feature reports into a characterization as one input source, with basis `reported`. The characterization's field names match his where they overlap (D20). Where his values and SWDB's counts differ, both are kept and the difference is flagged.

## Acceptance

- [x] His BFS sparse and fully connected reports (v1.2) import.
- [x] A table of overlapping fields is documented.
- [x] Conflicts are listed, never silently resolved.

Claimed: 2026-10-06 ET by Codex ticket 08 worker on `codex/lanl-ticket08`; base `8e2156a`. Public seams: import-feature-report, view and validate against a copied record store, extending the spec-confirmed characterization CLI seam. Report input is additional reported evidence; counted facts and receipts remain immutable.

## Answer

Resolved: 2026-10-06 ET.

`swdb import-feature-report` imports either supplied report into a new
characterization with basis `reported`. Literal Peter field names live under
`reported_inputs[].features`; existing native count fields remain compatible.
The [overlapping-field table and CLI](../../../docs/reference/feature-report-inputs.md)
document scope, input identities, omitted outcomes and unit handling.

Actual public CLI imports used a copied record store and the immutable native
`bfs.kron-g16.t4.characterization.a2` record (identity `063085ba4121fbbfff6734131fd6d33e1186fb22e80cac10a0895f534c19f813`).

| Report | Content / filename version | Native trials preserved | Explicit conflicts |
|---|---|---:|---:|
| BFS sparse v1.2 | 1.1 / 1.2 | 5 | 17 |
| BFS fully connected v1.2 | 1.1 / 1.2 | 5 | 13 |

Both imports preserve every native fact, verified binding, execution receipt and
original bytes. Duplicate destination IDs refuse with nothing written. The
copied store validates with **579 records**. Expanded derived count payloads stay
in the temporary copied store; the committed [compact acceptance receipt](../evidence/08-reported-input-imports-20261006.json)
pins commands, original/report/sanitized/native hashes, conflicts and preservation
checks. Its original import tool identities and final-source validation identities
have separate, explicit scopes.

Conflicts retain both facts and reasons: content versus filename versions;
TDStep/source/input/host versus the counted whole-trial scope; reported 4-byte
`VertexOffsets` versus the explicitly aliased 8-byte upstream catalog array;
structured/text methodology width contradictions; stale manifest notes; and
ambiguous KB/MB labels. Arrays without explicit aliases remain unmapped. Reported
logical capacity arithmetic does not become a measured working set or select a
unit. Source/access equivalence stays unresolved. Native missing costs and
whole-call unknowns are unchanged; no new performance evaluation or CPU agreement
is claimed.

The sanitizer recursively withholds PMU, timing/runtime, cycle, IPC/CPI and
performance outcomes, including nested/free-text outcomes. It preserves reported
index/locality statistics and the explicit lack of runtime thread-interleaving
observation. Validation rejects reintroduced outcomes even after hashes are
recomputed, and checks a stored parent's native facts and identity. Source reads
and hashes use the shared access boundary; changing source bytes during a read
refuses the import.

Verification: **15 public tests passed** (12 importer/validation cases and three
existing estimated-fact/frozen-protocol compatibility cases). Both the exact
import outputs (**579 records**) and canonical history (**584 records**) validate
under final bundle `51cdc13ce074fe6702714d1f19e3b0a2de364ce1d6c0d17d37251b91a6c9b242`.
The former estimated-fact test changed a now-frozen input; its corrected fixture
adds a separate unbound input and explicitly preserves the original pinned bytes.
Malformed/nonfinite/duplicate-key inputs refuse without partial records or parser
tracebacks. Historical bundle validation remains supported while execution after
a bundle change requires a new freeze. The final batch command is recorded in
the acceptance receipt.
