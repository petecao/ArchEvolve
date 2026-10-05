# Typed library and content-bound certification

Created: 2026-10-03 ET
Updated: 2026-10-04 ET (control observed checks and clause comparison)

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
