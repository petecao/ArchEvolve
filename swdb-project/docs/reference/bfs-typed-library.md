# Typed library and content-bound certification

Created: 2026-10-03 ET
Updated: 2026-10-05 ET (ticket 75 native-CPU certification, command 1.4); 2026-10-04 ET (control observed checks and clause comparison; ticket 70 certification isolation)

The `library/` folder holds normative YAML and buildable C++ outside the record store.
`swdb validate` checks entry shapes, clause discharge modes, pinned files and the
ported Extensa predicate grammar. Only stated formal labels are supported. The
ported grammar and vendored Lark 1.3.1 carry provenance and licenses inside
`swdb/_vendor/`; the port needs no MemAcc installation or additional Python dependency.
Yan-Ru authorized using Apache-2.0 WITH LLVM-exception while Peter's confirmation is pending.

Intrinsic records may carry `interface: {id, version}`, `hardware_operations` and
`library_entry` with `id`, `path` and `content_sha256`. With this form, ISA family, extensions
and header are optional; source-code provenance is required. The profile package
lists accelerator intrinsics with `machine_support: not_applicable`: machine ISA
flags do not establish accelerator build support. Existing ISA records retain their requirements.

An `offload` strategy effect carries `steps` (positions in the matched access chain)
and `hardware_operations` (operation record IDs). Only access-pattern targets allow
this effect. Legality checks every selected step and reports the contract's unchecked
conditions separately. The `dx100_read_offload` strategy leaves CPU arbitration intact.

`swdb certify ENTRY_ID --runs-dir DIR` runs strict functional builds and differential
checks. Candidate certification adds `--snapshot ID --patch FILE` or `--candidate ID`;
`--calibrate` runs the T17-fixed authors' calibration outside provider workspaces.
The matrix uses tile sizes 16,384 and 1,024 and four threads. A control is rejected
only after successful compilation and a named semantic check failure; invalid controls
and surviving controls block certification. Functional-model evidence is simulated
pre-check evidence, not gem5 correctness or performance.
Lowering certification compiles its pinned `location`, `differential_test` and intrinsic
reference semantics, using the declared input set and build definitions. Unsupported
driver seams, input sets or matrix overrides fail before producing a receipt.

Certification records bind `entry` (`id`, `content_sha256`), `dependencies`
(sorted ID/content hashes for the complete referenced entry closure), optional `candidate`
(contract ID, contract hash and tree hash), `command` (`version`, `sources_sha256`),
`host`, `matrix`, `negative_controls`, `verdict`, `evidence_basis`, `evidence_kind` and
`created_at`. Positive cells and negative controls keep their build/run commands,
outputs and reasons. The certification command is the producer of this evidence.

Added 2026-10-04 ET (final code review): each negative-control run also records its
`graph` and `observed_checks` (every check the run failed, not only the first reason). A
control that expects named checks is rejected only by one of them. A candidate certification
records `clause_controls`: per contract clause, its `clause`, `control`, the clause's named
`check`, `source` (`contract`, or `plugin` for a control the kernel plug-in adds to a
clause), the run's `observed_checks`, `matched` and `enforceable` (false for a check name no
run can report). An enforceable mismatch fails the verdict.

Added 2026-10-04 ET (ticket 70, command version 1.3): candidate certification is isolated.
- No candidate verdict is read from stdout or stderr. Each run writes evaluator records to a
  descriptor the harness opened (`library/dx100/certification/record.cc`). The records hold the
  strict-layer check names, each frontier window, the vector returned to an evaluator-owned
  `main` (`*_driver.inc`) and the witness counters.
- Every check is computed from those records out of process. Each run keeps `record` and
  `record_sha256`; each cell and control keeps `named_checks`, `observed_checks` and
  `result_check`.
- The candidate is compiled once per tile size with a forced prelude (`candidate_prelude.hpp`)
  whose library seams call `seams.cc`. Faults are compiled only into that separate object. Cells
  and controls record `candidate_object_sha256` and `seam_object_sha256`. Library-fault controls
  share the positive object and record `fault.delivery: separate_object`.
- A harness scan refuses candidate-authored lines that name harness or fault symbols,
  `SWDB_STRICT` or `FUNC`, descriptor, environment, loader or process primitives, or text that
  imitates an evaluator line. The refusal is a usage error; campaigns report it as `harness_scan`.
- Records with command versions before 1.3 keep their meaning: stdout/stderr checks, and fault
  macros in the candidate's translation unit.

Added 2026-10-05 ET (ticket 75, command version 1.4): native-CPU candidate certification.
- A rewrite contract that pins `certification_profile` (format `swdb.native-candidate-profile.v1`,
  for example `library/profiles/native_bfs_tdstep.yaml`) is certified by
  `swdb/certification_native.py` instead of the DX100 matrix. The profile names the build
  configurations (the frozen native protocol's `-O3` flags and `-O1 -g`), thread counts, the five
  certification graphs, the rewrite scope (one function body) and the controls.
- Isolation is 1.3's: one candidate object per build, an evaluator-owned `main`, records on a
  harness descriptor, and faults only in `library/native/certification/seams.cc`. The native seams
  are `compare_and_swap`, `QueueBuffer::push_back` and an evaluator frontier hook inserted before
  DOBFS's protected frontier print, which records each window and may apply one step-input fault.
  The execution witness is `witness claims=<c> pushes=<p>` (both above zero once BFS passes the
  source).
- Before any build, certify refuses a change outside the scope function, a scope region that is not exactly
  one function definition with the snapshot's signature, and (harness scan with `directives`) any authored
  preprocessor directive other than `#pragma omp` or the token `defined`: the seam macros exist only in
  certification builds, so a directive could tell them apart. Native profiles pin their sources (`--sources`
  is refused) and a control may name its own graph (`staging-tail-17`). A witness line of the other target's
  form makes a record invalid.
  Cells record `build`, `flags` and `threads`; the record carries `profile` (`id`, `path`, `sha256`,
  `target: native_cpu`).
- `--candidate-record FILE` (with `--snapshot`/`--patch`) binds the run to an Extensa candidate
  record read in place: its source snapshot must match and its artifact sha256 must equal the
  patched tree's. The record's `candidate.id` is then that candidate, so `swdb candidate-level`
  derives its level from this certification.
- DX100 certification, lowering certification and calibration are unchanged; their records keep
  version 1.3 meaning.

`swdb get ENTRY_ID` prints normative content with derived tier and status. Review records
bind a `target` content hash to a `reviewer`, `reviewed_at` and passing certification
`evidence`. `swdb promote ENTRY_ID` records that review without editing the entry.
Changing normative YAML or the code pin requires fresh certification and review.
Dependency changes also invalidate the old receipt, even when its subject's hash
stays fixed. The producer checks those identities before and after execution.
Historical receipts without dependency pins remain readable; entries with
dependencies require fresh bound receipts before certification or promotion.
Only passing `evidence_kind: execution` certification grants certification or shared
admission; `contract_fixture` receipts grant neither. Shared review is assigned to
Yan-Ru Jhou (the `yanrujhou` alias is accepted and recorded with the canonical name).
An unrelated review cannot grant the shared tier. A completed target execution that
fails a required witness is refuted; an unfinished execution remains inconclusive.
A separate successful execution cannot conceal a current-pin refutation.

Rewrite proposal message 1.1 adds an optional `library` section with a `contract` pin,
`entries` pins and `shipped_files` (`path`, `sha256`, `lowerings`). Message 1.0 remains
accepted without this section. ArchEvolve submit checks every cited entry and contract
dependency is shared and certified for its exact hash. New files must be exactly the
shipped lowering files, and each must match its certified canonical header bytes.
Patch payloads use no rewrite provider. The submitted producer names the authoring session.

The proposed ADRs 0007–0011 describe library, evidence, mode and retention boundaries.
Human sends, promotion reviews and retroactive cleanup approvals remain explicit
tracker tasks; implementation does not invent those receipts.
