# T16-only seal recovery operator

Prepared 2026-09-27 Eastern Time. Prospective packet; no Git delivery, admission,
lease claim, or scientific dispatch has occurred through this operator.

This copies the reviewed lease-recovery operator with a narrow change: only T16,
a separate pristine `EvolveSWDB_t16_seal_recovery_runtime_20260927_a1` checkout,
the new `t16-seal-recovery` plan, and the fresh
`bfs-seal-recovery-linux-20260927-a1.final.json` proof group. The shared admission
helper remains pinned to its previously reviewed SHA. It invokes the existing
batch supervisor with canonical Python and explicit `-s -B`; no evaluator or
cleanup implementation is duplicated.

Runtime `PIN`, template commit, full runtime manifest hash and fresh proof reference
are deliberately unset. `setup` rejects both T15 and an unpinned runtime before any
host inspection or file access. Root must review the diff and tests, then pin the
immutable export, build its complete manifest, retain a fresh helper comparison and
seal the actual proof reference before Git export/admission. The helper files and
resource limits are unchanged.

The original T16 hard end remains 20:16:17.225985 ET. Admission must still allow a
whole 21,600-second series plus 30-second cleanup by 14:15:47.225985 ET. The existing
cost reader charges every prior reservation and the fresh 600-second / 2-GiB proof
allowance. Preparation cannot resume an existing ID; launch cannot retry an existing
raw root. No T15 allowance, deadline extension, or budget reset is provided.
