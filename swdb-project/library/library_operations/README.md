# Library operations

Created: 2026-10-03 ET. Updated: 2026-10-03 ET (tickets 49–51); 2026-10-05 ET (ticket 77).

Normative library-operation entries belong here. Each operation pins its implementation
(`location`, `code_sha256`), its plain C++ reference semantics, its differential-test
driver and input set, and names every intrinsic it uses. A body is plain C++ and never
calls a hardware interface: `swdb validate` rejects a body that includes a DX100 header or
calls a `maa_*` function.

- `*.yaml` + `*.hh`: entries seeded from Extensa (MemAcc `af3d6d7f7a69`), experimental tier.
- `reference/`: plain C++ reference semantics (`swdb_ref::`), original SWDB code.
- `drivers/`: two-binary differential templates ported from Extensa's synthesis drivers.
- `controls/`: negative controls, one mutated copy of a body each.
- `synthesized/`: entries written by `swdb synthesize` (only after they certify).
- `certification/v1_1/`: the trusted record object and differential-test driver of certify
  command 1.1 (ticket 77). The driver records the frame check and the output on a pipe the
  harness reads; driver faults arrive in a blinded run plan.

Certify with `swdb certify ENTRY --profile PROFILE` (profiles in `library/profiles/`). The
default is command 1.1; `--command-version 1.0` runs the earlier two-binary harness, whose
records keep their meaning.
Provenance of every ported file: `swdb/extensa/PROVENANCE.md`.
