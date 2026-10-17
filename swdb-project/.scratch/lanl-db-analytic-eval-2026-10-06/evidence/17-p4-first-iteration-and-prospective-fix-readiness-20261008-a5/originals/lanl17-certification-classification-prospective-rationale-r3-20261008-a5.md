# Prospective certification classification R3 — 2026-10-08 ET

SOURCE ONLY / UNAPPLIED / NOTRUN. Selected unified diff `/private/tmp/lanl17-certification-classification-prospective-r3-20261008-a5.diff`, 23678 B, SHA256 `d8d44eb826470f0331e5aabcc882fbdb226e23a010ca94b7888a3535d5b0910d`. It proposes changes to the same10 existing files as R2; no repository source, frozen R5e12/F6, record, evidence, original campaign history or remote artifact has changed. Target/control modules were not imported; no tests, compiler, provider, CLI, remote action or scientific repair ran. This is a prospective source draft for application only after original custody/FINALIZE guards finish and final review authorizes implementation.

R2 exact diff19214/SHA806ba772e15220c8d7620bf281eaf1a52b1a1c8e981bc74be5604bb71664887f and its rationale remain unchanged. Independent findings are retained in `/private/tmp/lanl17-certification-classification-prospective-r2-peer-findings-r1-20261008-a5.md`. R3 incorporates all three concrete findings, preserving the rest of R2 behavior and boundaries.

## Confirmed source problem and narrow mapping

Frozen TargetAdapter.certify catches every certification Failure/UsageError as candidate failed feedback. That conflates expected authored scope/header/harness/mutation-site refusal with unavailable compiler, failed trusted evaluator build, invalid library/profile and trusted snapshot/source drift. Infrastructure can then enter repair/plateau accounting. Retained certification_aborted digests do not reveal actual exception classes/messages, so no actual campaign rejection is reclassified by this draft.

R2 introduced explicit CandidateRefusal categories with original standalone Failure/UsageError bases preserved. Pure authored-source checks receive narrow typing; trusted compiler/build/input/configuration/materialization errors remain ordinary operational exceptions. The adapter catches CandidateRefusal first for expected failed-check feedback, then raises the existing campaign Stop(infrastructure_failure) for operational certification errors. Stop traverses the existing interrupted_iteration/provider-call bookkeeping, avoiding completed-iteration/plateau/repair advancement. Candidate compiler/build nonzero matrix verdicts remain ordinary persisted negative outcomes; this draft does not promote them to infrastructure automatically.

R3 corrections:

1. **Shared native1.4/1.5 frontier guard:** original certification_native.py481–482 rejects missing/ambiguous protected logging anchor or BFSVerifier with bare Failure. R3 changes only this explicit authored-source raise to common.CandidateFailure. Its default public check remains certification_aborted. Trusted profile, driver, graph, original snapshot and protected metadata validation remain operational. The native1.3 instrumentation/scope checks already typed by R2 remain unchanged.
2. **Blinded trusted control instrumentation:** restore the shared `instrument(text)` lambda to its original unwrapped plugin call. Wrap only the positive authored `instrument(source)` call with common.candidate_check. The same lambda used for generated legality-control text stays operational; a trusted transform that removes an anchor cannot become candidate repair feedback. Positive candidate instrument failures remain expected refusals. This mirrors the existing1.3 positive/control distinction without altering control construction/evaluation.
3. **Trusted certification I/O:** add OSError to the adapter's operational certification catch, after CandidateRefusal. FileNotFoundError/PermissionError and related trusted driver/source/object/log failures now reach the same Stop boundary and preserve interrupted rows/provider calls. No blanket Exception/BaseException catch, subprocess redesign, generic candidate exception heuristic or source-history reinterpretation is introduced.

Missing normative knob configuration stays Failure/infrastructure, despite its legacy mutation-site words. Authored missing worksharing/schedule/mutation sites remain explicit candidate refusal. CLI exit categories for CandidateFailure and CandidateUsageError still inherit exit1/exit2 respectively; explicit failed check names replace exception-text classification.

## Proposed meaningful regressions

All proposed tests remain in existing tests/test_extensa_targets.py; none ran. Total newly proposed parametrized cases18: operational4, expected candidate feedback3, authored-source check/category1, native frontier8, positive/control instrumentation2.

- Four campaign-level operational cases exercise real unavailable-compiler discovery, trusted evaluator Build.evaluator refusal with an injected nonzero compile result, invalid-library UsageError and trusted-driver FileNotFoundError. Assert infrastructure stop, no completed iterations/plateau/repair/evaluation, and an actual interrupted row with retained provider-call history.
- Three adapter expected refusal cases assert failed candidate output with exact public scope/harness/site checks, preserving candidate repair semantics and CLI inheritance. A direct source-check test exercises actual mutation-site, harness and schedule guards, while missing normative knob metadata remains operational.
- Eight native guard cases use the actual certify_native_v14 shared production function for version1.4/1.5, with missing/duplicate frontier anchor and missing/duplicate BFSVerifier. Only graph generation/staging preludes are mocked; no build/compiler is needed before the real guard. Assert CandidateFailure/certification_aborted rather than infrastructure.
- Two blinded cases traverse the actual positive/control construction path with a fixture build and mocked graph/legality metadata. The instrumenter refuses either positive authored input or a trusted generated-control source. Assert positive errors are CandidateRefusal; trusted-control errors remain Failure and not CandidateRefusal, with exact visited inputs. No graph body/compiler/evaluator runtime is used for this guard regression.

After authorized application to current source, first run the relevant focused classification cases, then the existing target and certification scope/isolation/blinding/native/process/legality suites appropriate to the changed boundaries. Resolve real API/behavior failures before broad review. Suggested focused command from swdb-project:

```text
python3 -m pytest -q tests/test_extensa_targets.py -k 'certification_infrastructure or expected_candidate_certificate or authored_source_refusals or native_authored_frontier or blinded_instrumentation_distinguishes'
```

The broader candidate/native certification suites can require GNU OpenMP or native hardware/toolchain; preserve truthful skip/environment limitations and run the required remote checks only under separate actual source/evaluation custody. Tests do not repair or establish the original research evidence.

## Static preparation evidence and remaining gate

The local source-draft builder reconstructed every R2 changed file from original `git show R:path` bytes, verified every hunk context/removal line, applied only the three described source corrections and corresponding tests in memory, generated a fresh full R-based unified diff and AST-parsed all10 complete proposed files. It used read-only Git source retrieval and stdlib source/file operations only. No reconstructed target source was imported/executed or written into the repository. The builder is retained at `/private/tmp/lanl17-build-certification-classification-prospective-r3-20261008-a5.py` for byte-preserving review.

Root and independent peer source review of R3 remain required. Original R2 and peer notes remain authoritative historical preparation; no retrospective claim is made that they had these corrections. Actual campaign causes remain unproven, all original stop/release/report/index/audit results stay faithful to frozenR, and final Standards+Spec review plus actual implementation/testing remain future work.
