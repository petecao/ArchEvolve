# Concrete cleanup review

Reviewed: 2026-10-03 08:35 ET. Reviewer: Codex root acting on Yan-Ru Jhou's behalf.

Authority: the user explicitly approved all current and future related project actions, including remote evaluations and pushes; see [standing approval](approval-2026-10-03.md). Root performed the exact listing review before approving and applying. This records delegated review, not a claim that Yan-Ru personally inspected the file list.

Listing on mbit10: `/data1/yanruj/EvolveSWDB_runs/typed-library-t32-failed-smoke-dry-run-20261003-3399d76720944650bca75ef2074c9703.json`. SHA-256: `feb871b74833f8a88822af1321baeeaa762ac37e79dacdd2537521d46661c636`.

Only the following two regular, owned files are approved, each referenced solely as raw output by the failed, unclaimed evaluation `bfs-dx100-smoke-20260925-a3`, with no checkpoint manifest or input reference. Fresh custody and hashes must still match immediately before apply.

| Exact path | Bytes | SHA-256 |
|---|---:|---|
| `/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/bfs-dx100-smoke-20260925-a3/checkpoint/cpt.2117142500/m5.cpt` | 361986 | `f335ddd7b5db4f4d741fefb3b415f8491f96eee55e567eee3e3b59c1c607ce20` |
| `/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/bfs-dx100-smoke-20260925-a3/checkpoint/cpt.2117142500/system.physmem.store0.pmem` | 17677212 | `903f6e87be7f977433c34a1ac1104c6332300d4fe1994495ad92de51e963c7f1` |

Nine compact files remain. The coverage run still recorded running, every shared checkpoint, symlink root, and every other historical file are excluded. This bounded cleanup satisfies ticket32 without treating name-only inventory as deletion eligibility. Actual deletion receipts and disk deltas will be recorded separately.

Actual apply finished2026-10-03 08:35 ET. Public CLI approval `prune-approval-5482d06e021343978cc76026faebc70f` records delegated authority explicitly. Intent `prune-intent-528e33cdab12488181709aac274e9094` and deletion `retention-0fdfef7b828d49238d9af06e8c1378d5` retain both exact identities. Both files are absent and all nine compact artifacts remain. Total removed bytes18,039,198; `/data` available bytes78,819,528,704 before and78,837,571,584 after (delta18,042,880). `/data1` changed46,456,999,936 to46,455,836,672 while metadata and other host activity occurred; that separate filesystem decrease is not attributed to this deletion. All431 remote records validate. [Machine receipt](evaluation/ticket32-cleanup-receipt.json) returns through Git; raw listing remains remote.
