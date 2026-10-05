# 77 — Library-operation certification 1.1: record verdicts, blinded driver faults, attributed controls

Created: 2026-10-05 13:31 ET (from the open item of ticket 76)
Updated: 2026-10-05 17:20 ET (tracker hygiene, code review: Blocked by line); 2026-10-05 14:21 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** 76
**Spec:** `../spec.md` (certification command); [49](49-port-extensa-machinery.md), [50](50-library-operation-tracer.md), [51](51-seed-extensa-families.md), [70](70-certification-isolation.md), [76](76-attributed-blinded-certification.md)

**What to build:** give library-operation certification (`swdb certify ENTRY --profile P`) the
guarantees of certify 1.3/1.4. Agent-decided under Yan-Ru's delegation ("continue working");
revisable.

## Problem (ticket 76 open item)

Library-operation certification (command 1.0) certifies agent-synthesized Extensa library
operations (pack, bin, relabel, regroup, gather staging, and `swdb synthesize` output):

- a control's abort is classified from a printed line (`SWDB_PRESERVATION_FAIL:frame_violation`,
  `swdb/extensa/synthesis/certify.py` `classify_abort`);
- the frame check and the output file are produced inside the candidate's process, after code the
  candidate controls, so the candidate can skip them (write its own output, exit early);
- nothing shows that the post-call checks run in the candidate's own binary, and nothing hides
  from the candidate which kind of run it is in.

## Acceptance

- [x] Verdicts only from harness-owned records: a trusted driver records the frame check and the
  output; Python compares the output with the plain C++ reference out of the candidate's control.
- [x] Driver-fault controls run in the candidate's own binary, delivered by a blinded plan, in
  random order with the positive runs.
- [x] A control counts as rejected only by its own named check, attributed.
- [x] A static scan of candidate source refuses harness or fault symbols and I/O or process
  primitives.
- [x] Command 1.0 stays selectable; old certificates keep their meaning.
- [x] Adversarial tests (fake-print abort, control detection) pass 1.0 and fail 1.1.
- [x] Every experimental-tier library operation (tickets 50/51) re-certified under 1.1; results
  recorded.

## Answer

Resolved 2026-10-05 14:21 ET by the agent. Agent-decided under Yan-Ru's delegation ("continue
working"); revisable.

**Decision: library-operation certify command 1.1, the default for `swdb certify ENTRY --profile
P`; 1.0 unchanged and selectable** (`certify_entry(..., version='1.0')`, CLI
`--command-version 1.0`). 1.0 records keep their meaning. `--command-version 1.3/1.4` with
`--profile` is refused, and 1.0/1.1 without it. Code (commit 9490d57):
`swdb/library_operation_blinding.py`, `library/library_operations/certification/v1_1/`
(`record.cc`, `driver.cc`), `swdb/library_operations.py` (`certify_entry` dispatch,
`_certify_1_0`), `swdb/certification.py` (CLI choices).

1. **Record verdicts.** A trusted driver per family is compiled apart from the candidate. It keeps
   the run templates' arguments, inputs, canary and frame check. It calls the adapter's
   `extern "C"` entry, then writes `frame ok|violation <array> <byte> <count>` and
   `result <bytes> <hex>` to a record pipe that Python drains, followed by `end`.
   - Python compares the output with the reference output byte for byte.
   - A run without `end`, with the wrong nonce, with a line out of sequence, or with a nonzero
     exit has no named check: it is `runtime_abort` or `record_invalid`.
   - Stdout and stderr are logged and never parsed. `classify_abort` is used only by 1.0.
2. **Reference first.** The reference is built and run on every case before any candidate or
   control object is compiled. Its outputs stay in memory, and its binary and case folders are
   deleted.
3. **Blinded driver faults.** Two certifier controls run per build in the candidate's own binary:
   `driver.input_write` (frame_violation) and `driver.output_perturb` (differential_mismatch). The
   trusted driver flips one input bit or one output bit after the call.
   - The fault arrives in a 60-byte plan. `record.o` is linked first and drains the plan before any
     candidate initializer runs.
   - Positive cases, driver faults and the entry's mutation controls run in one `SystemRandom`
     order, each in a uniformly named fresh case folder.
   - Mutation controls are whole-body replacements, so their binaries hold no candidate code
     (`separate_binary_without_candidate`).
4. **Attribution.**
   - A driver fault counts only when the single changed byte (count 1) or the single differing
     element is the one it flipped, and the positive run of that case passed.
   - A mutation control counts only when its expected check comes from records on a case whose
     positive run passed, in every build; then the mutation is the only code that differs.
5. **Scan.** The body, the candidate template and every control mutation are scanned before any
   build. The scan uses certify 1.4's set plus initializer and exit hooks, printing and
   self-location primitives. A finding fails the certification (cell `scan/harness`). The 1.0
   token and include checks still apply.

**Adversarial results (Mac, clang++ sanitized, g++-16 OpenMP; relabel entry).** Evidence:
[`evaluation/library-operation-certification-2026-10-05.json`](../evaluation/library-operation-certification-2026-10-05.json).

| Attack | 1.0 | 1.1 | 1.1, scan disabled |
|---|---|---|---|
| `fake_print_control`: the agent-authored aliasing_write control has no write; it prints `SWDB_PRESERVATION_FAIL:frame_violation` and exits 3 | **certified** | failed (`harness_scan`) | failed: aliasing_write `invalid` (runtime_abort, no frame record) |
| `plan_detecting_bypass`: the body writes its input, looks for a run plan on descriptors and in the environment, and when it finds none writes `cand.bin` itself, prints the done line and `_Exit(0)` before the frame check | **certified** (its detector saw "none" in 16 runs) | failed (`harness_scan`) | failed: both matrix cells `record_invalid`, every control `invalid`; the detector saw "none" in all 48 candidate-binary runs |

Without `record.o`, the same detector reads the plan and names the fault (test), so the "none"
comes from the blinding.

Tests: `tests/test_library_operation_blinding.py`, 20 cases. They cover both attacks under 1.0,
1.1 and 1.1 without the scan; the detector control; one blinded binary, reference first, random
order and distinct nonces; attributed controls; 1.0 still selectable; CLI version refusal; the
record judge and attribution on synthetic records; and the scan. Changed 1.0-era tests in
`test_extensa_library_operations.py`:
- the pack controls test ignores driver faults;
- the probe test uses `<build>/candidate_bin`;
- the mid-run pin test runs under both versions.

Suites (Mac): library-operation blinding, Extensa (7 files), library index, submit and typed
library, kernel plug-ins, feedback: 285 passed. Two failed in that run and pass alone and on the
committed tree (51 passed); the likely cause, not confirmed, is files the agent edited during that
run. Certification
blinding, isolation, controls, legality, typed and BC: 228 passed.

**Re-certification (1.1 at 9490d57, clean tree, sources_sha256 d9cb73db…, Mac, scratch stores, not
committed).**

| Entry | Certification | Matrix | Controls rejected, attributed | Runs |
|---|---|---|---|---|
| `operation.pack_executor` | `certification.c7b599e6118d4cb1bf8c7f096f2e4f2b` | 2/2 + probe | 5/5 | 144 |
| `operation.update_binning_executor` | `certification.438d272cfab344349f734ef165441776` | 2/2 | 5/5 | 96 |
| `operation.vertex_relabel_executor` | `certification.e39e01687ea44504a9d5483365b7ac60` | 2/2 | 5/5 | 96 |
| `operation.regroup_executor` | `certification.4f8600252dd44243aad96cbc5ba73508` | 2/2 | 5/5 | 96 |
| `operation.gather_staging_executor` | `certification.07bf697c7d2f4bf5a5e22d78f6728506` | 2/2 | 5/5 | 96 |

All five are `certified`, and every driver-fault run is attributed. Each takes 9–12 s. No
synthesized entry is in the library, so there was nothing more to re-certify.

**Residuals.**
- **R1, in-process (as ticket 76).** Candidate code shares the address space with the driver and
  the record object. Descriptor scanning or pointer arithmetic can reach the record pipe or the
  plan state; the scan refuses the names only. *Closure:* run the candidate in a process with no
  evaluator descriptor, with buffers in shared memory and a syscall filter.
- **Transient input writes.** A write that the candidate undoes before it returns is not seen by
  the frame check, as in 1.0. *Closure:* map the inputs read-only during the call.
- **The probe cell is unchanged from 1.0.** Its verdict file is written by trusted probe code in
  the candidate's process. Its predicates bind only the adapter's operands.
