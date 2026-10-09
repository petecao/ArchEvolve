# Prospective certification error classification — 2026-10-08 20:22 ET

UNAPPLIED / NOTRUN. This is a draft based on frozen R `5e12a9796432654d88def24ecea617d16ca605b2`. Source changes and tests wait for original R custody and FINALIZE guards, then parent approval of final review. No local repository source was changed, no tests or target imports executed, no remote access and no original scientific evidence repaired or reinterpreted.

Selected draft `/private/tmp/lanl17-certification-classification-prospective-r2-20261008-a5.diff`: 19214 B, SHA256 `806ba772e15220c8d7620bf281eaf1a52b1a1c8e981bc74be5604bb71664887f`. Original draft `/private/tmp/lanl17-certification-classification-prospective-20261008-a5.diff` preserved unchanged; R1 corrects the proposed test to use SearchLedger.to_state() (there is no .data property) and avoids a process-wide shutil.which monkeypatch. All drafts remain unapplied and untested.

## Intended behavior

Only explicit authored-source candidate refusals become failed candidate certificates/repair feedback. Operational, invalid frozen configuration and trusted source-integrity failures stop the campaign as infrastructure_failure, without repair calls or plateau/completed-iteration advancement. Using the existing campaign Stop preserves the interrupted iteration and its opened provider-call ledger; bare Failure would bypass that row-preservation block.

The draft adds CandidateRefusal and two concrete CLI-compatible subtypes to the existing certification_common module. CandidateFailure continues to be a cli.Failure (standalone exit1); CandidateUsageError continues to be a cli.UsageError (exit2). Each carries an explicit public failed-check name. The adapter catches this category first, preserving certification_aborted/harness_scan/negative_control_site:<site> only for candidate checks, and routes other Failure/UsageError to Stop(infrastructure_failure, bounded detail).

Explicit candidate-only boundaries:

- DX100/native authored rewrite scope, canonical candidate header and protected evaluator/ROI fields.
- Harness scan and conditional directive refusal; public text/check names retained.
- Negative-control mutation site absence/ambiguity; prior Failure subtype retained.
- Pure candidate instrumentation and native candidate function definition checks; trusted profile, snapshot definition and input pins remain outside these boundaries.

`candidate_check` is restricted by call sites to pure authored-source checks. It never surrounds certification itself, a compiler/build/link, graph generation, library/configuration validation, snapshot reconstruction or source freshness checks. Existing failed persisted certification verdicts are unchanged. No command flags, schemas, protocol budgets, scientific selection/pairing/verdict computations, records or library bytes change.

Ten proposed files: swdb-project/swdb/certification_common.py, swdb-project/swdb/campaign_targets.py, swdb-project/swdb/certification.py, swdb-project/swdb/certification_blinding.py, swdb-project/swdb/certification_faults.py, swdb-project/swdb/certification_isolation.py, swdb-project/swdb/certification_process.py, swdb-project/swdb/certification_native.py, swdb-project/tests/test_extensa_targets.py, swdb-project/swdb/certification_legality.py.

## Static review and remaining validation

All ten proposed complete Python files AST-parse; every original unified-diff context/removal line was checked against exact git-show R bytes before reconstruction. Source behavior was inspected, not executed. Existing APIs confirmed: SearchLedger.to_state(), Stop reason conversion and interrupted-iteration capture, candidate compatibility checks, Build.evaluator() trusted failure, and fixture run's configurable fake_certify global. No regression outcomes are claimed.

R2 additionally covers authored schedule-control site refusal at certification_legality.py:484. Its knob_control missing-declaration case at426 remains untyped Failure and infrastructure: there is no normative integer-range knob, rather than an absent authored site. Both public source strings remain unchanged. Proposed source-boundary tests assert this distinction. R1 and initial drafts remain unchanged/NOTUSED.

Proposed new tests (7 parameter instances):

1. End-to-end Gem5 fixture campaign (3 cases): actual compiler() with explicitly nonexistent selected executable; real trusted Build.evaluator() with deterministic injected failed compile result; invalid-library UsageError. Expect infrastructure_failure, no completed iterations/plateau advancement, interrupted iteration retaining provider calls, no repair calls and no timing job.
2. Adapter expected-refusal cases (3): authored scope, harness, negative-control site. Expect failed candidate certificate, exact public failed check, no infrastructure stop, original CLI subtype compatibility.
3. Actual negative-control-site, schedule-control and harness source-check functions produce the typed refusals/check names and keep standalone CLI categories.

After safe source application, run focused tests from swdb-project with its established Python environment:

```sh
python -m pytest -q tests/test_extensa_targets.py -k 'certification_infrastructure_stops or expected_candidate_certificate_refusals or authored_source_refusals or failed_certificate_with_nothing_named'
python -m pytest -q tests/test_extensa_targets.py tests/test_extensa_campaign.py tests/test_certification_native.py tests/test_certification_controls.py tests/test_certification_isolation.py tests/test_certification_blinding.py tests/test_certification_process.py tests/test_certification_legality.py
```

Confirm actual test filenames/environment before execution; this command worksheet is prospective. Broader checks only after focused results or review justify them. Tests can reveal additional candidate-only boundaries needing explicit typing; do not reintroduce a blanket catch or an exception-message allowlist. Native trusted snapshot/profile validation must remain operational, not candidate rejection.

## Evidence boundary

The confirmed source defect is independent of P1–P3 actual cause. Six retained final failed-check digests match ['certification_aborted']; their original exception text was excluded by compact projection. This draft does not claim those six failures were compiler/configuration failures, does not transform their plateau statuses, and cannot repair missing preceding pairing histories. Original R/M2/F6/controls and report/audit facts remain authoritative.
