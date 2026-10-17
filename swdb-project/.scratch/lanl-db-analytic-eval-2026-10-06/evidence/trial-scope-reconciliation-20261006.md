Legacy registered trial scopes (2026-10-06 ET)

New producer counts consistently use `per_trial` for a trial's operations,
iterations, source access elements/bytes and call execution/size counts. Root
snapshot labels remain `per_run`; this correction does not change the native
observer, source work, ROI, count values or hardware-transaction interpretation.

Historical registered receipts are immutable. Estimation may copy an individually
sealed registered begin/reset/end trial window and infer its legacy source labels
as `per_trial`. The inference requires verified source/input/ROI/run binding,
ordered trial positions, whole-call wrapper and count payload seals, matching
region-local executed call sites/names/events/counts, complete nonempty call-bin
partitions and exact source access request partitions by update kind and width.
It preserves unknown shape dimensions and all values. Unsealed fixtures, arbitrary
scopes or mismatched site/bin/access partitions are left unchanged and existing
service-model coverage guards decide whether the estimate stays unknown.

The estimate's `extensions.legacy_trial_scope_reconciliations` retains original
characterization/payload/runtime hashes, trial position/ROI and per-site shape
proof hashes, with `basis: inferred`. The original characterization and receipt
remain byte-identical. Sensitivity scenarios use the same copied scopes and
original characterization identity; calibration transfer and error-band admission
still require their independent evidence. This is no count rerun, cost fill,
physical residency claim, functional/MMIO bridge or agreement-gate success.
