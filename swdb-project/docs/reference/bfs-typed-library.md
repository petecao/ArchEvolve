# Typed library and content-bound certification

Created: 2026-10-03 ET
Updated: 2026-10-09 ET (current defaults, procedure fingerprints, and campaign failure handling)
Updated: 2026-10-05 ET (certification version tables, record identity fields, evidence basis); 2026-10-05 ET (ticket 75 native-CPU certification under command 1.3 and 1.4); 2026-10-04 ET (control observed checks and clause comparison; ticket 70 certification isolation)

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

Added 2026-10-05 ET (ticket 75, command versions 1.3 and 1.4): native-CPU candidate certification.
- A rewrite contract that pins `certification_profile` (format `swdb.native-candidate-profile.v1`,
  for example `library/profiles/native_bfs_tdstep.yaml`) is certified by
  `swdb/certification_native.py` instead of the DX100 matrix. The profile names the build
  configurations (the frozen native protocol's `-O3` flags and `-O1 -g`), thread counts, the five
  certification graphs plus any control-only graph (each also gets a positive cell), the rewrite
  scope (one function definition) and the controls.
- `--command-version 1.3` uses 1.3's isolation: one candidate object per build, an evaluator-owned
  `main`, records on a harness descriptor, one seam object per fault
  (`library/native/certification/seams.cc`), and an evaluator hook before DOBFS's protected frontier
  print that records each window and may apply one step-input fault.
- 1.4 uses ticket 76's mechanism (`library/native/certification/v1_4/`): one binary
  per build holding every fault, a blinded 43-byte run plan on a pipe, a random run order recorded
  in `profile.schedule`, record files named by the run's nonce, windows from the slide-window
  ledger, the seam witness on every positive cell, and a control rejected only when attributed to
  its fault (`lost_claim_left_unset`, `missing_child_of_hidden_vertex`,
  `parent_without_edge_from_stale_vertex`, `duplicate_is_forged_push`). The evaluator call inserted
  into DOBFS (outside the rewrite scope) only hands the row offsets to trusted code.
- The native seams are `compare_and_swap`, `QueueBuffer::push_back` (and, under 1.4,
  `SlidingQueue`); the execution witness is `witness claims=<c> pushes=<p>` (both above zero once
  BFS passes the source). A witness line of the other target's form makes a record invalid.
- Before any build, certify refuses a change outside the scope function, a scope region that is not
  exactly one function definition with the snapshot's signature, and (harness scan with
  `directives`) any authored preprocessor directive other than `#pragma omp` or the token `defined`:
  the seam macros exist only in certification builds, so a directive could tell them apart. Native
  profiles pin their sources (`--sources` is refused).
- Cells record `build`, `flags` and `threads`; the record carries `profile` (`id`, `path`, `sha256`,
  `target: native_cpu`, `target_scope`).
- `--candidate-record FILE` (with `--snapshot`/`--patch`) binds the run to an Extensa candidate
  record read in place: its source snapshot must match and its artifact sha256 must equal the
  patched tree's. The record's `candidate.id` is then that candidate, so `swdb candidate-level`
  derives its level from this certification.
- `certification.b7954f4df9dd4e228fb12437b845f190` was written before ticket 75 merged ticket 76;
  its command version reads 1.4 but it ran the 1.3-isolation native path (sources_sha256
  `06fe4cc5…`).

Added 2026-10-05 ET (certification code-review fixes): command versions belong to command
families, each with its own frozen version table (`swdb/certification_procedures.py`): candidate
artifacts on DX100 (1.3-1.6, default 1.6), native-CPU contracts (1.3-1.5, default 1.5), library operations
(1.0-1.2, default 1.2) and lowerings with calibration (1.1). An unknown version is refused. New certification
records add to `command`:
- `family` (`candidate`, `native`, `library_operation` or `lowering_calibration`), and for library
  operations `library_operation_version`, so a library-operation label is never read as a candidate
  label;
- `sources`, the per-version manifest (`path`, `sha256` of each file the version reads, plus its
  table-entry row), whose digest is `sources_sha256`; `kernel_sources`, the kernel plug-in and its
  result check, recorded beside it;
- `sources_match_version`, true when that digest equals the version's frozen digest;
- `code` (`git_commit`, `sources_differ_from_commit`).
`evidence_basis` is `measured` for native-CPU and library-operation runs (real code on the host CPU)
and `simulated` for functional-model runs (ADR 0008); earlier records say `simulated` on every path.
Older records carry none of these fields; `swdb.certification_procedures.classify` names the
procedure each one ran, including the labels that drifted (the native record above; DX100 1.4
records before 93a2a94, which named record files by cell).

## Handle a certification refusal at the right boundary

[Candidate checks](../../swdb/certification_common.py) mark authored-source refusals
explicitly. Scope violations keep `certification_aborted`; evaluator-symbol scans
keep `harness_scan`; missing candidate mutation sites keep
`negative_control_site:NAME`. Standalone commands retain their failure or usage
exit code. [Campaign certification](../../swdb/campaign_targets.py) can pass these
failed checks to bounded repair.

Compiler availability, trusted evaluator builds, invalid library/configuration,
and trusted-file I/O failures instead stop the campaign with
`infrastructure_failure`. The summary keeps `stop_detail` and
`interrupted_iteration`; no repair call or completed iteration/plateau increment
is created for that failure. A candidate compilation result remains part of the
certification matrix; it is distinct from failure to build the trusted evaluator.

The 2026-10-08 source change re-declared the frozen procedure digests in
[the version table](../../swdb/certification_procedures.py). Version labels alone
do not identify the executed code: compare `sources_sha256` and `kernel_sources`.
Historical receipts keep their recorded manifests. Functional evaluation requires
a certificate matching the current procedure; an older receipt is not refreshed
by keeping its version label.

## Inspect or promote an entry

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
