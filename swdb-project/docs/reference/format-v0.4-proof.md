# Proof records (`kind: proof`)

Created: 2026-10-14 (Eastern Time), Probata proof of concept ticket 04 (the proof record tracer).
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/04-proof-record-tracer.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Records and levels"), map ticket 26,
[ADR 0016](../adr/0016-proof-records-never-change-level-computed-on-read.md).

**In one line:** `swdb prove` runs one proof job on one candidate artifact's proof unit and
writes one `proof` record that never changes; `swdb candidate-level` reads the proven level from
the records whose pins still match.

## What later tickets build on

| Piece | Where | Who widens it |
|---|---|---|
| The record kind and its schema | `schemas/proof.schema.json`, `records/proofs/<id>.yaml` | 10, 11, 12, 13, 60 add fields |
| The adapter interface | `swdb/proof.py`: `ProofUnit`, `Job`, `Verdict`, `ADAPTERS` | 21 (WP), 22 (SAW) add adapters |
| The route field | `route` | 61 fills `bounded_direct`; 62 fills `route_1`, `route_3` and makes it required |
| The level on read | `swdb.proof.proven_level`, `swdb.proof.counts` | 10 adds every pin kind and the level rule |
| SQLite tables | `swdb_proofs`, `swdb_proof_pins`, `swdb_proof_assumptions`, `swdb_proof_bounds` | [database.md](database.md#proof-tables) |

## `swdb prove`

```
swdb prove --candidate <candidate> --function <name> --adapter scripted --script <file> \
           --runs-dir <folder outside the repo> [--contract <id>] [--batch <id>] [--position <n>] [--id <id>]
```

- `--contract` defaults to the one contract the candidate artifact's counting certification
  records name; it must be in the library beside the records folder.
- `--runs-dir` must be outside the repository checkout (exit 2 otherwise). The job writes
  `<runs-dir>/<record id>/adapter.log` and uses `<runs-dir>/<record id>/scratch/`, which is
  deleted when the job ends, whatever the verdict.
- Output (`--format yaml|json`): `{record, path}`. Exit 0 for every verdict: the job ran and its
  record was written. Each run writes a new record with a new ID; a record is never replaced
  (the record writer refuses).
- Records written in an Extensa campaign get its `mode` and `campaign` tags, as `swdb add` does.

## The adapter interface

An adapter is a class in `ADAPTERS` with a `name` and `run(job) -> Verdict`.

- **In, `Job`:** `unit` (a `ProofUnit`: candidate, function, tree path, tree sha256, contract,
  contract sha256), `summaries` (pins `{id, sha256, proof_record}`; empty in this tracer),
  `scratch` (a folder the adapter may use; deleted after the job; never named by the record) and
  `log` (the log file the adapter appends to; kept as evidence).
- **Out, `Verdict`:** `verdict` (`proven`, `refuted`, `not_proven`), `bounds`, `assumptions`, and
  `counterexample` (refuted only) or `failure_class` (not proven only). A verdict that breaks
  these rules raises `AdapterError`, and nothing is written.
- **Scripted adapter (`--adapter scripted`):** reads `verdict`, `bounds`, `assumptions`,
  `counterexample` and `failure_class` from the YAML `--script` file. Its records are
  `contract_fixture` evidence, never evidence about real code.

## The record

| Field | Meaning |
|---|---|
| `subject` | `{kind: candidate_proof_unit, candidate, function}`; any other kind (vocabulary `proof_subject_kinds`) has `{kind, id}` and an optional `part` |
| `route` | optional; `route_1`, `route_3` or `bounded_direct`; only on a candidate proof unit |
| `verdict` | `proven`, `refuted` or `not_proven` |
| `counterexample` | refuted only, required: the counterexample, inline |
| `failure_class` | not proven only, required (presence only until ticket 11's vocabulary) |
| `pins` | the content-hash set, all ten kinds required (below) |
| `bounds` | `{dimension: positive integer or "unbounded"}`; `threads` required |
| `assumptions` | list of `{kind, reference: {id, sha256}, sentence}` (`reference` and a non-empty `sentence` required); kind from vocabulary `proof_assumption_kinds` (seven kinds) |
| `job` | `adapter`, `host` (`mac` on the Mac), `worker_core` (null unless pinned to one core), `wall_seconds`, `cpu_seconds`, `batch_load` (1-minute load average at start), `peak_rss_bytes`, `batch`, `position`; ticket 12 owns and validates this list |
| `evidence` | `adapter_log`: `{path, sha256}` of the adapter log in the runs folder (absolute path) |
| `evidence_kind` | `contract_fixture` |

### Pins

Single pins are `{id, sha256}` (the `baseline_function` pin adds `function`) or
`{not_applicable: <sentence>}` (`not_applicable` holds why); a pin that does not apply yet is written, never left out.

| Kind | What `swdb prove` writes today |
|---|---|
| `code` | candidate artifact ID and its tree sha256 (`artifact.sha256`) |
| `contract` | contract ID and its current library content sha256 |
| `baseline_function` | the candidate's source snapshot ID, the function, and the snapshot tree sha256 |
| `reference_semantics` | not applicable (ticket 30) |
| `proof_semantics` | not applicable (ticket 27) |
| `method_version` | not applicable (ticket 11) |
| `summaries` | `[]` (list of `{id, sha256, proof_record}`; `proof_record` is the proof record of the summary) |
| `minimum_bounds` | not applicable (ticket 33) |
| `predecessor_snapshot` | not applicable (ticket 62) |
| `build_constants` | `[]` (list of `{name, value}`) |

## The level on read (`swdb candidate-level`)

New output fields beside the existing ones (`certifications`, `counted`, `mode`, `campaign`,
`promotion`, `stale`):

- `level`: the proven level when a proof record counts, else the certification level.
  Values: `proven_unbounded`, `proven_within_bounds`, `certified`, `uncertified`, `rejected`.
- `certification_level`: what certification alone gives.
- `proven`: null, or `{level, bounds, records}`: the best counting level, the bounds of its first
  record by ID, and every counting record at that level.
- `proof_records`: every proof record of the candidate artifact's proof units.

A record counts only when the candidate artifact is certified, its verdict is `proven`, its
`code` pin equals the candidate's tree sha256, and its `contract` pin equals the contract's current
content sha256 in the library beside the records (a contract the library does not know never
counts). `proven_unbounded` needs every bound dimension, `threads` included, unbounded. Nothing
writes a level to any record. Ticket 10 replaces this tracer rule with the versioned level rule.
