# 77 — Library-operation certification 1.1: record verdicts, blinded driver faults, attributed controls

Created: 2026-10-05 13:31 ET (from the open item of ticket 76)
**Type:** slice
**Status:** claimed
**Blocked by:** —
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

- [ ] Verdicts only from harness-owned records: a trusted driver records the frame check and the
  output; Python compares the output with the plain C++ reference out of the candidate's control.
- [ ] Driver-fault controls run in the candidate's own binary, delivered by a blinded plan, in
  random order with the positive runs.
- [ ] A control counts as rejected only by its own named check, attributed.
- [ ] A static scan of candidate source refuses harness or fault symbols and I/O or process
  primitives.
- [ ] Command 1.0 stays selectable; old certificates keep their meaning.
- [ ] Adversarial tests (fake-print abort, control detection) pass 1.0 and fail 1.1.
- [ ] Every experimental-tier library operation (tickets 50/51) re-certified under 1.1; results
  recorded.
