# Functional correctness with estimated speed

Updated: 2026-10-10 ET (code review of tickets 06/12: current-procedure certificate,
tests and team lineage); 2026-10-09 ET.

`evaluate-functional` combines an exact current strict-functional certification
with a frozen analytic estimate. The finite certification matrix includes the
kernel correctness check. Its scope is **functional-target correctness**; it
does not certify the physical hardware. The command starts no child process.

The retained execution certificate is reusable only when its candidate tree,
source snapshot, normative contract and dependency hashes, process-split
procedure, and kernel verifier match the current sources. A stale or incomplete
certificate yields an `incompatible` evaluation with correctness unverified.
An exact current certificate that failed a positive correctness check yields an
`incorrect` evaluation. Neither failure creates an estimate.

After a passing certificate, the command accepts the candidate's verified
`registered-functional.v1` whole-call counts, or an explicitly labeled contract
fixture. It estimates every trial before reporting the median whole-call time.
Missing rates, mechanisms, whole-call coverage or composition premises preserve
null seconds and ratio. The verdict stays `within_error` until a valid error
band exists; the estimate carries its ratio and band even when they are null.

## Request and commands

Use a fresh evaluation ID and a protocol frozen against the current estimator
bundle. Characterization and certification IDs name retained records. The
target description may be a record ID or a YAML/JSON file; its exact snapshot
is retained in the estimate. An optional `baseline` names a compatible retained
estimate; its hash is carried with the ratio.

```yaml
message_version: '1.0'
id: bfs.functional.evaluation.example
candidate: bfs-functional-read-offload-20261006-a1.proposal.candidate-1
certification: REPLACE_WITH_CURRENT_CERTIFICATION_ID
characterization: bfs.functional.kron-g16.t4.characterization.objects.a2
target_description: dx100-e4fc4af-functional-analytic-v1.t4
protocol: REPLACE_WITH_FRESH_FROZEN_PROTOCOL_ID
```

Use a current execution certificate for this exact candidate. The retained
`certification.23f81442358b4dcc8688140a394a1f08` is historical: candidate procedure 1.6,
whose source manifest predates the 2026-10-08 re-declaration. Since 2026-10-09 the default
candidate procedure is 1.7, so `evaluate-functional` refuses it (`incompatible`,
"certify again"). A fresh estimate protocol alone does not make that certificate reusable.
See the [procedure rules](bfs-typed-library.md#handle-a-certification-refusal-at-the-right-boundary).

**Tests (2026-10-10 ET):** `tests/test_functional_evaluation.py` runs on a copied record
closure. It checks the stale-certificate refusal and handoff under a no-child sentinel (the
sentinel proves it loaded and blocks `subprocess` and `os` spawn/exec/fork routes), the gem5
refusal before writes, and a known ratio (2.0) staying `within_error` on the DX100 functional
target. The positive path (complete evaluation, 1.1 handoff with that ratio) **skips until a
1.7 execution certificate of this candidate exists in `records/`**; none does yet.

```sh
python3 -m swdb evaluate-functional request.yaml --records /path/to/records --library /path/to/library --format json
python3 -m swdb handoff-message evaluation_result bfs.functional.evaluation.example --records /path/to/records --format json
python3 -m swdb validate --records /path/to/records
```

`--library` defaults to this checkout's normative `library/`, including when
records are copied to an external run directory. An absent or changed contract
never falls back to an empty catalog. Requests are bounded to 10 MiB; unknown
fields and reused IDs are refused. Team lineage recursively refuses gem5 and
Extensa campaign dependencies (including campaign summaries and nested `{id: ...}`
pins) before writes, naming every offending record. This command requires ArchEvolve
mode.

## Evaluation-result format 1.1

Only evaluations labeled `swdb.strict-functional-estimate.v1` render the additive
1.1 format. Existing native/simulator evaluations and other message kinds keep
1.0. Record schema 0.4 and request message version 1.0 are independent versions.

The 1.1 content adds `estimate` with the referenced estimate ID/hash, `basis`,
seconds, ratio, verdict, band, baseline and count/target/protocol/estimator pins.
It adds correctness `scope`, `hardware_correctness_claim: false` and the retained
certification ID/hash, procedure manifest, date and explicit reuse basis.
`roi_measurements.trials` is zero, and `performance_claim` is `none`.
An incomplete evaluation carries `estimate: null`.

Rendering and canonical validation verify the compact fields against their
referenced records and the candidate/input/target/protocol binding. Archived
records retain the procedure used at creation; a later source update does not
apply a new procedure retroactively. Changing the retained evidence or a cached
ratio is rejected. No handoff converts functional host timing to hardware speed.
