# 12 — ArchEvolve-mode DX100 evaluation without gem5

Created: 2026-10-06
**Type:** slice
**Status:** resolved
**Blocked by:** 06, 09
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** An ArchEvolve-mode DX100 candidate artifact is built on the functional model's strict layer and passes the kernel's correctness check and certification (functional-target correctness, D8), then gets an estimate, a three-state verdict (D25), an evaluation record and an evaluation-result handoff message whose new version carries the estimate, basis, verdict and band.

## Acceptance

- [x] Functional-target correctness is labeled as such, never as correctness on the hardware target.
- [x] The verdict is `within_error` until a band exists, with the ratio shown.
- [x] The handoff format version is bumped and documented.
- [x] A test shows that no gem5 job starts anywhere in the path.

## Implementation custody

Updated: 2026-10-06 21:23 ET. Parent `/root` owns `codex/lanl-ticket12`, based on integrated `4eaf95a`. Public seams: functional ArchEvolve evaluation, evaluation-result handoff and canonical validation. User authorized autonomous interface decisions; preserve functional-target correctness and outcome-free team lineage.

## Public local gate

Updated: 2026-10-06 22:06 ET. The functional evaluation, handoff 1.1 and canonical validation seams pass six distinct public cases across the recorded gates. Cached estimate/certificate integrity, stale certification, recursive team refusal, absence of child processes and historical 1.0 document pins are covered. See `../evidence/12-public-functional-evaluation-proof.json`. Remote exact-artifact acceptance is still pending; the ticket remains claimed.

## Answer

Resolved: 2026-10-06 22:35 ET. The public `evaluate-functional` command retains exact current strict certification and source/count/protocol identities, produces an immutable estimated evaluation, and renders evaluation-result handoff version 1.1. Its correctness scope is finite **functional-target** testing; hardware correctness and performance gains are not claimed. Whole-call seconds, ratio and band are null while structural coverage remains unknown, and the verdict is `within_error`. Historical handoff 1.0 bytes and the default recursive team/gem5 refusal are preserved.

Exact-artifact mbit10 acceptance passed from clean immutable `bef54f9661d099dcf381538522bd4d9573d6fe0c`: both evaluation and handoff ran under a no-child sentinel, 620 copied records validated, all 619 prior files were preserved, and three new canonical records were exported through Git. Node 1 generation 538 exited 0 and released; no application performance timing or simulator/provider/compiler child ran. See [remote acceptance](../evidence/12-functional-evaluation-mbit10-20261006-a1.json) and [compact handoff](../evidence/12-functional-handoff-mbit10-20261006-a1.json).

The final coexistence gate after integrating ticket 16 passed three distinct public cases: two functional/certification-refusal cases in 90.74s and one paired-freeze/refusal case in the earlier gate. A copied zero-work fixture now removes dependent functional evaluation copies when it removes their historical estimate/count copies; original records are untouched. Full canonical validation passes **628 records**. All **888 protected prior blobs and 625 prior YAML records** are byte-identical to integrated `9a5057f`; the only canonical additions are the actual protocol, estimate and evaluation. See [final proof](../evidence/12-final-public-coexistence-proof-20261006.json) and [earlier public gates](../evidence/12-public-functional-evaluation-proof.json).
