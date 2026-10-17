# Actual p1 dispatch

Updated: 2026-10-08 12:54 ET.

**p1 attempt 1 is active on node0, native lease generation 511. No substantive iteration or normal completion is admitted yet.**

The original helper28 returned 0 after full frozen-input checks. Its original preregistration is 44,229 bytes, SHA256 `7e63d49398eb8f8e2f0d9332b84c1350276acd5b50b9287b2d0b694ec565a6b4`, identity `ee2d7bebe5a8003403a136b3fd8f62b1d72b743b6b47c1f8f97c4abb31ac53dd`. It binds p1/attempt1/node0, R/F6/M2/policy and unchanged limits: 8 iterations, plateau4, 24 lane-hours, 20 GB, public child87000s and outer88200s. Resume and baselines-only are false.

Actual dispatch-state custody from unchanged producer32 is 6,971 bytes, SHA256 `70c88da3004c1a5f7aecf262591d9518ce71b37e9815599e31f39f84fae2d190`, identity `f411703a5c44f6e9887ea511388fe35374c8d4b86256c8ffe8ad446bb29cf4fc`. It binds the original absent-state before receipt and the real dispatch receipt. Root owned the fresh campaign namespace throughout the interval; the launcher rechecked state absence before action.

The 12:51 ET read-only monitor matches p1's actual held node0 lease generation511 and owned live holder. Node1 and the legacy lease are released. There is no campaign state or completed iteration yet: the in-lane helper repeats frozen-source/input checks before starting the public campaign. Initial lane exit -1 is an active sentinel, not a failure.

| Campaign | Actual state | Next step |
|---|---|---|
| p1 | Active attempt1, node0/g511; 0 iterations | Monitor public startup and trajectory |
| p2 | Queued | Fresh capacity/lease admission after p1 release |
| p3 | Queued | Same frozen policy and independent custody |
| p4 | Queued | Same frozen policy and independent custody |

All four original full catalogs remain intact. Current/data headroom is below the unchanged44GiB concurrent floor; no second campaign is admitted. Keep the selected node from reuse until original stopped/final-lane/wrapper-exit/native-release observations, release32 and b08after custody are collected. A released metadata flag precedes native fd9 unlock; it is not sufficient alone. Never resume a stopped=true state.

Originals, source-only release worksheet and future FINALIZE/index/audit worksheet are hash-indexed here. Future inputs remain explicit; these worksheets execute nothing and grant no scientific admission. Raw output remains on mbit10. The 30-minute heartbeat is ACTIVE on the resumed chat and points to current progress/actual paths. Final report, strict audit, Standards/Spec review, fixes and ticket closure remain pending.
