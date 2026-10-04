# 64 — Range-loop convention, register operands and named-check campaign feedback

Created: 2026-10-04 ET (by ticket 57 a6 and ticket 58 a3)
Updated: 2026-10-04 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** —
**Spec:** `../spec.md`

**What to build:** A rewrite provider in an Extensa campaign is told the range-loop
continuation convention and which operands are register handles. When certification fails, the
feedback names the failing check and states what it enforces.

## Finding

- Ticket 57 a6 (`records/campaign_summaries/extensa-gem5-bfs-20261004-a6.summary.yaml`): every
  applied contract edit set the range loop's `last_i` register to -1 and failed the strict layer's
  `range_bounds` check. The feedback said only "Certification failed a named check."
- Ticket 58 a3: all 9 samples passed plain values where DX100 takes register handles (stream
  bounds, range-loop stride), following Peter v1.1, which types those operands `int32_t`.

## Acceptance

- [x] The convention is checked against the authoritative sources, and the provider's workspace
  states it and the register-handle operands. No certified semantics change.
- [x] Campaign feedback and the repair workspace name the failing strict-layer check and its
  precondition. They never include run output or reference code.
- [x] Tests.

## Answer

Resolved 2026-10-04 ET by the agent. Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

**Convention (verified).** A range-loop batch starts with `last_i_reg = 0` and `last_j_reg = -1`.
`last_i` is the next row index into the bound tiles; `last_j = -1` means "row not started". Every
source agrees:
- Peter v1.1 §3.3 preconditions (`docs/bfs-intrinsics-spec-yanru.md` at `0b56895`, line 121).
- The authors' functional model `apps/dx100/benchmarks/API/MAA_functional.hpp` line 734
  ("for each tile of i, set last_i_reg to 0 and last_j_reg to -1").
- The strict layer `library/dx100/strict/MAA_functional.hpp` line 127 (`range_bounds`:
  equal bound-tile sizes, stride > 0, `0 <= last_i <= size`).
- The certified ticket 20 lowering use (`library/dx100/bfs_read_offload.inc` line 33).

**What was wrong in the entry.** `library/intrinsics/dxc_range_loop.yaml` gives only the
signature (`int last_i_reg, int last_j_reg, ... int stride_reg ...`). It does not say that these
are register handles set by `__dxc_const_i32`, and it gives no initial values. Peter's §5 template
writes `dxc_reg_t last_i = 0;` and passes stride `1` as a value, which reads like plain values.

**Decision: a non-normative usage note, not an entry edit.** The intrinsic entry's content hash is
pinned by every receipt that depends on it. A one-line caveat edit, tried on a scratch copy,
demotes `intrinsic.dxc_range_loop`, its lowering and `contract.bfs_read_offload` from
shared/evaluated_on_target to experimental/draft. Only a new promotion review by Yan-Ru restores
that tier. So the entries are unchanged, and the usage notes live beside them:
- `library/intrinsics/notes/dxc_range_loop.md`: operand kinds, the 0/-1 convention, the
  "until the output tile is empty" loop, and what `range_bounds` enforces, with sources.
- `library/intrinsics/notes/dxc_stream_load.md` and `dxc_const_i32.md`: `*_reg` operands are
  register handles whose values are set by `__dxc_const_i32`, never plain values (ticket 58).
- `Library` loads only `*.yaml`, so the notes are not entries. They are outside every content
  hash and outside the certification source digest, which covers `library/dx100/` only.
- `swdb/campaign.py` `_workspace` ships each used intrinsic's note as
  `library/intrinsics/notes/<name>.md`. `rewrite_prompt` states the register-handle rule and the
  0/-1 start in one sentence.
- Proposed for the next promotion review (open): copy the note's two rules into the entry's
  `caveats`.

**Named-check feedback.** New `swdb/certification_feedback.py`:
- `TargetAdapter.certify` (`swdb/campaign_targets.py`) reports a failed strict-layer matrix cell
  as `strict_layer_assertion:<check>`, for example `strict_layer_assertion:range_bounds`. The name
  comes from the run's own `SWDB_STRICT_ASSERT:<check>` line. Certification records and verdicts
  are unchanged.
- The campaign's rejection text (feedback reason `certification_failed`) gives each check with a
  fixed public message, for example: "range_bounds: __dxc_range_loop needs bound tiles of equal
  size, stride register > 0 and 0 <= last_i register <= bound-tile size; each batch starts with
  last_i_reg = 0 and last_j_reg = -1, set by __dxc_const_i32". It then counts the controls that
  were not rejected. It stays within the D8 closed feedback (at most 400 characters, no advice
  words, no outcome claims).
- The repair workspace's `CERTIFICATION.json` gains `messages` (`[{check, message}]`).
- The strict layer prints only the check name, not the operand value. So the message states the
  precondition ("0 <= last_i"), not the observed "-1". Printing values would change the strict
  layer, which is certification source, so it was not done.

**Verification (Mac).** `tests/test_certification_feedback.py` (27 tests):
- the check name is read from the assertion line;
- every strict message is valid closed feedback;
- every check named in the strict layer and the lowering header has a message;
- the adapter reports `strict_layer_assertion:range_bounds`;
- the notes are outside the entries and free of the authors' accelerated code names;
- a fixture gem5 campaign's rejection text, repair `CERTIFICATION.json`, iteration-2
  `FEEDBACK.json` and rewrite workspace carry the check, the convention and the notes, and no
  run output.

Regression suites:
- 27 passed in `tests/test_extensa_targets.py` and `tests/test_extensa_campaign.py`.
- Also passed: budgets (9), selection (12), boundary (16) and intrinsics (10).
- `swdb validate` reports all records valid.
- `test_library_submit.py::test_actual_dx100_submit_reproduces_the_certified_tree` fails. It
  expects status `certified`, but the entry has been `evaluated_on_target` since tickets 28/45.
  The failure does not involve the notes or the feedback.
- `test_provider_workspace.py` did not finish within this session's 15-minute cap.

**Follow-up (2026-10-04 ET, from campaign a7).** If the matrix passes and only controls survive,
the feedback now names those controls ("Negative controls not rejected (1): forged_frontier.").
Before, it gave only a count. Commit `4d94e47`; this fix was not in a7's checkout. Ticket 57 a7
used the rest of this ticket. No edit set `last_i` to -1, and both classes reached a certified
gem5 candidate.
