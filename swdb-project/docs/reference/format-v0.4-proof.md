# Proof records (`kind: proof`)

Created: 2026-10-14 (Eastern Time), Probata proof of concept ticket 04 (the proof record tracer).
Updated: 2026-10-14 ET, ticket 11: batches, skips, the failure-class vocabulary, the method-version pin
([format-v0.4-method-version.md](format-v0.4-method-version.md)); 2026-10-14 02:15 ET, ticket 10: the
replay-label and `tools` fields, no level fields, and the versioned level rule
([format-v0.4-level-rule.md](format-v0.4-level-rule.md)); 2026-10-14 02:26 ET: failure class
`spurious_counterexample` and its tie to `unreplayed_counterexample` (Yan-Ru's decision of 02:25 ET);
2026-10-14 02:57 ET, ticket 12: the job block's
one field list and its checks, run fields (`run_index`, `provider_pin`) on proof records and proposals,
repair lineage on proposals ([Run fields and repair lineage](#run-fields-and-repair-lineage-ticket-12));
2026-10-14 ET, ticket 13: `swdb repair <proof record>` writes repair lineage ([format-v0.4-repair.md](format-v0.4-repair.md)).
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
| The job block | `job` ([below](#the-job-block-ticket-12)); `swdb.proof._job` | nobody adds a field outside ticket 12; 57 fills it on mbit10 |
| Run fields, repair lineage | `run_index`, `provider_pin` (proof, proposal); `repair_lineage` (proposal) | 13 writes repair lineage ([format-v0.4-repair.md](format-v0.4-repair.md)); 37 writes run fields on its proof records |
| SQLite tables | `swdb_proofs`, `swdb_proof_pins`, `swdb_proof_assumptions`, `swdb_proof_bounds`, `swdb_proof_jobs`, `swdb_run_fields`, `swdb_repair_lineage` | [database.md](database.md#proof-tables) |

## `swdb prove`

```
swdb prove --candidate <candidate> --function <name> --adapter scripted --script <file> [--script <file> ...] \
           --runs-dir <folder outside the repo> [--contract <id>] [--batch <id>] [--position <n>] [--id <id>] \
           [--run-index <1-3>] [--provider-kind codex|claude --provider-model <m> --provider-effort <e>]
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
- **Run fields** (ticket 12, S10): `--run-index` and the three `--provider-*` options put `run_index` and
  `provider_pin` on every record of the batch. A provider pin needs all three (exit 2 otherwise). A
  bounded job with no provider call passes none.

## The adapter interface

An adapter is a class in `ADAPTERS` with a `name` and `run(job) -> Verdict`.

- **In, `Job`:** `unit` (a `ProofUnit`: candidate, function, tree path, tree sha256, contract,
  contract sha256), `summaries` (pins `{id, sha256, proof_record}`; empty in this tracer),
  `scratch` (a folder the adapter may use; deleted after the job; never named by the record) and
  `log` (the log file the adapter appends to; kept as evidence).
- **Out, `Verdict`:** `verdict` (`proven`, `refuted`, `not_proven`), `bounds`, `assumptions`, and
  `counterexample` (refuted only) or `failure_class` (not proven only), plus
  `unreplayed_counterexample` (with failure class `spurious_counterexample` only, and always with it; below),
  `tools`, and `peak_rss_bytes` (ticket 12: the peak the adapter's RSS watchdog read for the job's
  process tree; else `swdb prove` measures it). A verdict that breaks these rules raises
  `AdapterError`, and nothing is written.
- **Scripted adapter (`--adapter scripted`):** reads `verdict`, `bounds`, `assumptions`,
  `counterexample`, `failure_class`, `unreplayed_counterexample`, `tools` and `peak_rss_bytes` from the YAML `--script` file. Its records are
  `contract_fixture` evidence, never evidence about real code.

## The record

| Field | Meaning |
|---|---|
| `subject` | `{kind: candidate_proof_unit, candidate, function}`; any other kind (vocabulary `proof_subject_kinds`) has `{kind, id}` and an optional `part`, a value of vocabulary `proof_part_names` whose `subject_kind` is the subject's kind (ticket 10; a new part is added there first) |
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
| `job` | required: the job block ([below](#the-job-block-ticket-12)); ticket 12 owns and validates this one list |
| `run_index`, `provider_pin` | optional (ticket 12, S10): [run fields](#run-fields-and-repair-lineage-ticket-12); present when a provider call took part (proof hinting) or the job belongs to a repeated run |
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

## The job block (ticket 12)

Ticket 12 owns this one field list: 04 writes it, 57 fills it on mbit10, and neither adds a field (a
new field is added in ticket 12 first). Every field is required, measured or read from the run; the
schema refuses a missing field, an unknown one, a negative time, load or peak RSS, and position 0.

| Field | Meaning |
|---|---|
| `adapter` | the verifier adapter's name (`scripted` for contract fixtures), so a scripted record shows as such |
| `host` | `mac` on the Mac, else the host's short name (`mbit10`); Mac and mbit10 numbers never mix |
| `worker_core` | the one core the job was pinned to, or `unpinned` (macOS pins nothing; 57 pins on mbit10). `null`: written before ticket 12 |
| `wall_seconds` | the job's wall time (seconds, >= 0) |
| `cpu_seconds` | the job's CPU time: own process plus waited children (seconds, >= 0) |
| `batch_load` | `{start, end}`: the host's 1-minute load average when the job starts (`start`) and ends (`end`), each >= 0. A bare number: written before ticket 12 (start only) |
| `peak_rss_bytes` | largest resident set size of the job's whole process tree (solver and JVM children included): what the 8 GB RSS watchdog per worker reads (O9). An adapter reports it in `Verdict.peak_rss_bytes`; else `swdb prove` reads `getrusage` |
| `batch` | the batch ID the jobs of one `swdb prove` call share |
| `position` | the job's position in the batch (>= 1); 57 checks interleaving from `batch` and `position` |

A skip record has the same block, with zero times. Proof time is a cost metric, never a speed claim
(map decision 23 item 6).

## Run fields and repair lineage (ticket 12)

The same two run fields go on proposals and proof records (one schema rule each, `envelope.schema.json`
`$defs`), because a proof-hint run has no proposal (S10). Both are optional: absent means the record is
not part of a repeated LLM configuration (map decision 23 item 5 repeats only those).

| Field | Meaning |
|---|---|
| `run_index` | 1, 2 or 3: which of the three independent runs |
| `provider_pin` | `{kind, model, effort}`, all three required; `kind` is `codex` or `claude`. For example `{kind: codex, model: gpt-5.6-sol, effort: xhigh}` |

A proposal that counterexample-guided repair (ticket 13) makes carries `repair_lineage`:

| Field | Meaning |
|---|---|
| `refuted_candidate` | the refuted candidate artifact (must exist) |
| `counterexample_record` | the proof record that holds the counterexample (must exist) |
| `round` | the repair round, a positive integer (the 5-round cap is the repair loop's budget, not a schema rule) |
| `reverted_repair` | required boolean: the deterministic contract-match check's flag. A reverted repair may compete and never counts as a repair |

`swdb validate` also checks (`swdb.proof.validate_proposal`) that the counterexample record is refuted
with its counterexample inline (an `unreplayed_counterexample` on a not-proven record never qualifies)
and that its subject is the named refuted candidate artifact's proof unit. Proposals and proof records
written before ticket 12 carry none of these fields and stay valid.

## The level on read (`swdb candidate-level`)

Ticket 10 replaced the tracer rule with the versioned level rule: see
[format-v0.4-level-rule.md](format-v0.4-level-rule.md). Nothing writes a level to any record.
