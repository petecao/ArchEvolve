# Workflow record format 0.4

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

Format 0.4 adds source ownership and workflow records. Existing 0.2 and 0.3 records
retain their meaning; see [source identity](bfs-source-identity.md). The envelope's
`schema_version` versions database records. Independent `message_version: "1.0"`
versions the provisional ensemble handoff. YAML remains authoritative; the SQLite
`records` table carries every new kind for retrieval after an index rebuild.

## Shared workflow fields

`producer` has `name`, `role` (`sw`, `hw`, `operator`, or `worker`), and the explicit
Boolean `test_client`. A fixture producer is not a live collaborator integration.
All records retain the ordinary envelope dates, provenance, draft/review status,
and stable identity. The internal operator creates metadata; its `agent_run`
provenance does not certify its contents as measured.

An `artifact` contains its absolute external `path`, aggregate `sha256`, and sorted
`files` manifest. Each file has relative `path`, `sha256`, `bytes`, and `executable`
mode. The aggregate hashes the canonical JSON manifest, including paths and modes.
Source snapshots reject symlinks; generated build/cache directories are excluded.
Artifact availability and hash agreement are checked before rewriting or execution.

## Source snapshots and profile packages

A `source_snapshot` records `implementation`, `application`, source `revision`,
`artifact`, source/build/evaluator `context`, declared `regions`, and `protections`. It preserves the
application snapshot before candidate edits. Protections record canonical verifier
text, complete harness files, and simulator ROI calls. Only evaluator-owned code
determines the correctness and timing contract; a proposal cannot waive protections.

A `profile_package` names its `implementation`, `source_snapshot`, and exact
workload/target/ROI `context`. `completeness` is `fixture`, `incomplete`, or `complete`.
It contains `regions`, `dynamic_memory`, `constraints`, collection `evidence`, and
explicit incompleteness `reasons`. `fixture-package` creates a contract fixture with
no execution, correctness, dynamic profiling, or performance evidence. A complete
package requires the later discovery and collector checks; fixture creation cannot
produce one.

## Proposals and candidate artifacts

`submit` accepts a request with `message_version`, `id`, `producer`,
`profile_package`, `source_snapshot`, `implementation`, exact `source_sha256`,
selected `intent`, exact target `regions`, `constraints`, `payload`, and `required_operations`. `payload`
contains `kind` and `content`; the first route accepts an actual unified patch.
`constraints.editable_files` bounds all direct and supporting edits;
`preserve_correctness` and `preserve_roi` must both be true. Every requested
capability must resolve against its declared target/interface before materialization.

A persisted `proposal` retains the original `request`, `payload_sha256`, `outcome`,
`attempts`, and `raw_artifacts`. An outcome has `state`, current `stage`, and `reason`.
States distinguish `submitted`, `rejected`, `unresolved`, `candidate_created`, and
`failed`. Source/package references and `candidate` are attached only after they
resolve. Invalid references in the original request remain available as rejected
input; they are not turned into successful cross-record references.

Each attempt records its `number`, `stage`, `state`, and available failure reason.
The running stage is persisted before starting a child operation. An interrupted
caller can therefore leave an explicit running stage; retrieval never interprets
that state as completion. Original IDs cannot be resubmitted to replace old evidence.

A `candidate` names its `proposal`, `source_snapshot`, originating `implementation`,
new `artifact`, retained `diff`, and `diff_sha256`. Its `state` distinguishes
`unverified`, `incomplete`, `incorrect`, and `checked`; patch creation uses
`unverified`. `context` and `protections` retain evaluator inputs. A later repair may
name a `parent_candidate`; ancestry does not select the performance comparator.

`get ID --chain` retrieves connected workflow records from a freshly regenerated
index. The writer commits metadata before index generation; an indexing failure is
reported with the durable record ID, never as successful submission.

## Public contract example

```sh
python3 -m swdb source-snapshot gapbs-bfs-do --id source-1 --runs-dir /external/runs
python3 -m swdb fixture-package source-1 --id package-1
python3 -m swdb submit proposal.yaml --runs-dir /external/runs
python3 -m swdb get proposal-1 --chain
```

These commands illustrate the contract. Fixture packages and source edits alone
are not acceptance evidence for the real BFS or DX100 campaign.
