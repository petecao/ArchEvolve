# Library operations

Created: 2026-10-03 ET. Updated: 2026-10-03 ET (tickets 49–51); 2026-10-05 ET (tickets 77, 78; code-review
fixes F4, F11).

Normative library-operation entries belong here. Each operation pins its implementation
(`location`, `code_sha256`), its plain C++ reference semantics, its differential-test
driver and input set, and names every intrinsic it uses. A body is plain C++ and never
calls a hardware interface: `swdb validate` rejects a body that includes a DX100 header or
calls a `maa_*` function.

- `*.yaml` + `*.hh`: entries seeded from Extensa (MemAcc `af3d6d7f7a69`), experimental tier.
- `reference/`: plain C++ reference semantics (`swdb_ref::`), original SWDB code.
- `drivers/`: two-binary differential templates ported from Extensa's synthesis drivers.
- `controls/`: negative controls, one copy of a body with one defect each. Each must stay a small edit
  of its body's current header (`tests/test_library_operation_controls.py`).
- `synthesized/`: entries written by `swdb synthesize` (only after they certify).
- `certification/v1_1/`: the trusted record object and differential-test driver of library-operation
  command 1.1 (ticket 77). The driver records the frame check and the output on a pipe the
  evaluator reads; driver faults arrive in a blinded run plan.
- `certification/v1_2/`: the evaluator, runner and call layout of command 1.2 (ticket 78): the call
  runs in a separate candidate process; the evaluator keeps the records, the plan and the input copies.

Certify with `swdb certify ENTRY --profile PROFILE` (profiles in `library/profiles/`). The
default is command 1.2; `--command-version 1.1` and `--command-version 1.0` (the earlier two-binary
harness ported from Extensa) stay selectable, and their records keep their meaning. Library-operation
command versions are their own family: library-operation 1.2 is not candidate-artifact certify 1.2.
The layout of every certification folder is in `library/dx100/certification/README.md`.
Provenance of every ported file: `swdb/extensa/PROVENANCE.md`.
