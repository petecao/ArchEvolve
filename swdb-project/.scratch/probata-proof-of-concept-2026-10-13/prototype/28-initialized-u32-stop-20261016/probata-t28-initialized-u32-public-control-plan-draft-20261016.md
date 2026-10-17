# Initialized-u32 public persistence profile draft — 2026-10-16 ET

This is inert design data for root review. Source `42db8833` is preserved with
two independent-review blockers: declared-root reference symlinks can be hidden
by `Library.resolve`, and the adapter does not yet bind the selected current
semantics ID/hash to its fixed unit-policy semantics pin. A reviewed successor
commit, exact physical/Git source manifest, and root-selected runtime pins are
required before admitting this profile. No author execution is requested.

The exact existing selector is
`tests/test_dx100_initialized_register.py::test_public_initialized_u32_has_ordinary_prewrite_capacity_and_original_partial_frame`.
Only that selector is proposed. Pytest session `fixture_host` sets the explicit
fixture host; per-test `checkout_records_unchanged` hashes checkout library and
records before/after. `tmp_path` supplies a fresh outside-checkout base. Test
imports `testkit.dx100_initialized_register` and `testkit.dx100_trust`; the former
uses `actual=False` and the unchanged closed source/model/header proposal.

The public fixture copies the catalog into a private temporary library, writes
the exact initialized source/state/model, three helper contracts and complete
26-name/27-declaration inventory, fixes the partial contract/method IDs, and
executes the ordinary `python -m swdb prove --summary <partial-contract> --adapter
wp --bounds '{"threads":1,"input_size":1}'` persistence route. Its named
Frama-C script prints version33.0, accepts non-WP typecheck calls, and touches a
marker then exits99 if `-wp` is requested. The named CBMC version script exits99
for non-version calls. The private Why3 configuration points prover commands
to `/usr/bin/false`; no real Frama-C/Why3/prover invocation is permitted by this
profile. The required result is an ordinary persisted `not_proven/tool_crash`
record after the explicit WP marker, preserving subject, owned TCB assumptions,
empty unit requires/ensures, original711 result, unchanged four-location frame,
ordinary capacity requires and initialized source bindings. It is no proof.

This profile does perform real compiler work. `c_lowering.locate/identity` uses
selected Clang22.1.8 discovery, matching libclang/header provenance and ordinary
source lowering. The new constructor issues original preprocessing, five
complete function/family AST requests and O2 LLVM, with exact source/SSA checks
and strict remaining active budget. `proof_setup.compile_report_module` also
executes the selected OCaml compiler through `SWDB_OCAMLFIND ... ocamlopt
-shared -linkall -package frama-c.kernel,frama-c-wp.core` and retains its scratch
module/source hashes under the existing setup rules. Root must pin/admit these
compiler/runtime/package commands explicitly; this profile must not be labeled
compiler-free, no-object, or actual formal verification. No generated caller,
sanitizer binary or native caller executable is run.

Proposed envelope: one coordinated B+c6 request,240s active/300s independent
outer watch,8GiB whole tree,one worker,256MiB planned retained raw budget,50GiB
free-space floor plus that budget. Pinned Python runs isolated without optimized
mode; `SWDB_CLANG` selects the already observed exact absolute driver. Root
selects a matching OCaml command/package closure before creating an executable
entry. Preserve counted/watch markers in child environments. The fixture's
private `standin-only.lock` is test data and does not replace the outer c6/B
admission. Ambient include/SDK/prover overrides must be rejected or explicitly
bound by root. Preserve timeout/failure logs and all resources/argv/outputs;
stop on first failure, with no retry or actual prover substitution.

Retain full generated source/preprocessing/AST/LLVM/module, private catalog,
record, WP input, command/log/JUnit and manifests outside the source checkout.
Only compact metadata may be published. Hash selected compiler/runtime/source
and all selected consumers before/after, record exactly which headers were
first observed after preprocessing, and retain all process-inspection events.
Root alone decides whether to dispatch after successor source review and fresh
capacity/lease/process/disk checks. A subsequent real parser/proof profile is a
separate admission and cannot be inferred from this stand-in result.
