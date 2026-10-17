# Proof records never change; a candidate artifact's level is computed on read

Date: 2026-10-13 ET
Status: proposed (decided by Yan-Ru on 2026-10-13 in formal-verification ticket 26,
`.scratch/formal-verification-2026-10-09/issues/26-proof-records.md`)

Every proof job writes one `proof` record that is never edited afterward. The job may be a
bounded-verifier run, a proof-hint loop, a once-proven part (a summary, a contract-proof part or a
method part), or a whole-kernel reproduction. Each record pins its content-hash set. A record counts
only while every pinned hash still matches the current one.

A candidate artifact's certification level is never stored as truth. It is computed when read, as
the weakest level among the proof records that count and the proven parts they depend on.
Campaign summaries, handoffs and promotion reviews keep only dated snapshots of the level, each
naming the version of the level rule that computed it.

A changed hash "reopens" a result simply by making its records stop counting, as certifications
already work (`swdb/library.py:281-291`). No job rewrites evidence.

Proof data stays in the SWDB extension (`swdb_` tables, ADR 0015). LANL's `Validation_results`
holds one outcome per input; a proof covers all inputs or declared bounds.

## Considered Options

- **A proof section inside the certification record:** certification is a test run that ends
  before any proof starts, and WP runs after the campaign stops. Evidence would have to be
  rewritten.
- **One editable level record per candidate artifact:** once-proven parts have no candidate, and a
  stored level goes stale silently when a pinned hash changes.

## Consequences

- The level rule is code with its own version. It is outside the method version, because every
  proof record pins the method version: a rule change recomputes levels and must not void proofs.
- A paper result cites a frozen research-database commit (ADR 0014), so its levels can be
  recomputed exactly.
