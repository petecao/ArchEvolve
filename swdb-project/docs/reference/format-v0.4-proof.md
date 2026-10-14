# Proof records (`kind: proof`)

Created: 2026-10-14 (Eastern Time), Probata proof of concept ticket 04 (the proof record tracer).
Updated: 2026-10-14 ET, ticket 11: batches, skips, the failure-class vocabulary, the method-version pin
([format-v0.4-method-version.md](format-v0.4-method-version.md)); 2026-10-14 02:15 ET, ticket 10: the
replay-label and `tools` fields, no level fields, and the versioned level rule
([format-v0.4-level-rule.md](format-v0.4-level-rule.md)); 2026-10-14 02:26 ET: failure class
`spurious_counterexample` and its tie to `unreplayed_counterexample` (Yan-Ru's decision of 02:25 ET).
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
| Failure classes and skip reasons | `vocab/proof_failure_classes.yaml`; `swdb.proof.listed(vocabs, role)` | 21, 22, 46, 47 map tool failures to classes and build the handlers |
| The method-version pin | `swdb.method_version`: `current`, `pin`, `pin_problem` | 10 (level rule), 14 and 16 (budgets), 36 (setup check) |
| The route field | `route` | 61 fills `bounded_direct`; 62 fills `route_1`, `route_3` and makes it required |
| The level on read | `swdb.level_rule` ([format-v0.4-level-rule.md](format-v0.4-level-rule.md)) | a new rule is a new `level_rule.VERSION` |
| The replay label | `replay_label` | 60 fills it and makes it required on refuted records; a new value is added in 10 first |
| Tools used (S14) | `tools`; `Verdict.tools` | 21, 22 fill it for every real verifier and solver |
| SQLite tables | `swdb_proofs`, `swdb_proof_pins`, `swdb_proof_assumptions`, `swdb_proof_bounds` | [database.md](database.md#proof-tables) |

## `swdb prove`

```
swdb prove --candidate <candidate> --function <name> --adapter scripted --script <file> [--script <file> ...] \
           --runs-dir <folder outside the repo> [--contract <id>] [--batch <id>] [--position <n>] [--id <id>]
swdb prove ... --skip <skip reason>          # run no verifier; record one skip
```

- **A batch** is the list of proof jobs one `swdb prove` call runs (ticket 11): one job per `--script`,
  in order, positions `--position`, `--position + 1`, ...; all share one `batch` ID. Each job's record
  is written when the job ends.
- **An unlisted failure class stops the batch.** When an adapter reports a failure class that is not a
  `failure_class` value of vocabulary `proof_failure_classes`, `swdb prove` writes no record for that
  job, starts no later job, and exits 1 with a message naming the class and the adapter log's path.
  Records of earlier jobs stay.
- **A skip** (`--skip <reason>`, a `skip_reason` value of the same vocabulary) runs no verifier and
  writes one record with `skip_reason` and no verdict, bounds, assumption set or adapter log. A skip
  skips only the steps that need the missing piece (O7); the level rule ignores skip records.
- **The method version:** `swdb prove` pins the current method version (the highest `sequence` in
  `library/methods/` beside the records folder) and refuses to run (exit 1) when there is none.

- `--contract` defaults to the one contract the candidate artifact's counting certification
  records name; it must be in the library beside the records folder.
- `--runs-dir` must be outside the repository checkout (exit 2 otherwise). The job writes
  `<runs-dir>/<record id>/adapter.log` and uses `<runs-dir>/<record id>/scratch/`, which is
  deleted when the job ends, whatever the verdict.
- Output (`--format yaml|json`): `{record, path}` for a one-job batch, else `{batch, jobs: [{record, path}, ...]}`. Exit 0 for every verdict: the job ran and its
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
  `counterexample` (refuted only) or `failure_class` (not proven only), plus
  `unreplayed_counterexample` (with failure class `spurious_counterexample` only, and always with it; below). A verdict that breaks
  these rules raises `AdapterError`, and nothing is written.
- **Scripted adapter (`--adapter scripted`):** reads `verdict`, `bounds`, `assumptions`,
  `counterexample`, `failure_class` and `unreplayed_counterexample` from the YAML `--script` file. Its records are
  `contract_fixture` evidence, never evidence about real code.

## The record

| Field | Meaning |
|---|---|
| `subject` | `{kind: candidate_proof_unit, candidate, function}`; any other kind (vocabulary `proof_subject_kinds`) has `{kind, id}` and an optional `part` |
| `route` | optional; `route_1`, `route_3` or `bounded_direct`; only on a candidate proof unit |
| `verdict` | `proven`, `refuted` or `not_proven`; absent on a skip record |
| `skip_reason` | a skip record only: why no verifier ran (vocabulary `proof_failure_classes`, role `skip_reason`): `no_contract_proof`, `no_minimum_bounds`, `outside_cpp_subset` |
| `counterexample` | refuted only, required: the counterexample, inline |
| `failure_class` | not proven only, required: a value of vocabulary `proof_failure_classes` whose role is `failure_class` (thirteen classes; each entry has its `handler`). `spurious_counterexample`: the verifier reported a counterexample that does not replay concretely on the compiled code, so the refutation comes from the tool or the spec encoding, not the program; never sent to repair (handler: fix the encoding, add the case to the regression corpus, rerun) |
| `replay_label` | refuted only, optional (ticket 10 owns it; 60 fills it and makes it required): `reproduced`, `proof_semantics_only`, `not_reproduced` or `undefined_behavior` (O6: "undefined behavior (no strict-layer replay)"; the refutation counts). Any other value, or a label on a record that is not refuted (a skip included), fails `swdb validate` |
| `tools` | optional (ticket 10, S14): the verifiers and solvers the job used, each the reference ID of a `trusted_tool` entry in the assumption set; `swdb validate` names any tool without one. Adapters report it in `Verdict.tools`; the scripted adapter reads `tools` from its script |
| `level`, `level_rule` | never present: a proof record holds no level and never pins the level rule (26 item 9); `swdb validate` refuses either |
| `unreplayed_counterexample` | not proven only; required when `failure_class` is `spurious_counterexample` and refused under any other class or verdict: the counterexample the verifier reported that did not replay concretely on the compiled code. It is a tool or encoding failure, never a refutation, and never reaches repair (input from ticket 05's SAW spike; class decided by Yan-Ru 2026-10-14 02:25 ET; the replay itself is built by the adapter tickets 22, 46, 47) |
| `pins` | the content-hash set, all ten kinds required (below) |
| `bounds` | `{dimension: positive integer or "unbounded"}`; `threads` required; absent on a skip record |
| `assumptions` | absent on a skip record; otherwise list of `{kind, reference: {id, sha256}, sentence}` (`reference` and a non-empty `sentence` required); kind from vocabulary `proof_assumption_kinds` (seven kinds) |
| `job` | `adapter`, `host` (`mac` on the Mac), `worker_core` (null unless pinned to one core), `wall_seconds`, `cpu_seconds`, `batch_load` (1-minute load average at start), `peak_rss_bytes`, `batch`, `position`; ticket 12 owns and validates this list |
| `evidence` | absent on a skip record; otherwise `adapter_log`: `{path, sha256}` of the adapter log in the runs folder (absolute path) |
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
| `method_version` | the current method version's ID and file sha256 (ticket 11). `swdb validate` rejects a pin naming no file in `library/methods/` or whose sha256 does not match the file; a `not_applicable` pin (records written before ticket 11) still passes |
| `summaries` | `[]` (list of `{id, sha256, proof_record}`; `proof_record` is the proof record of the summary) |
| `minimum_bounds` | not applicable (ticket 33) |
| `predecessor_snapshot` | not applicable (ticket 62) |
| `build_constants` | `[]` (list of `{name, value}`) |

## The level on read (`swdb candidate-level`)

Ticket 10 replaced the tracer rule with the versioned level rule: see
[format-v0.4-level-rule.md](format-v0.4-level-rule.md). Nothing writes a level to any record.
