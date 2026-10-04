# Fixed simulator recovery operator

Prepared 2026-09-27 Eastern Time. Both actual admissions are prepared; no batch was launched by this worker.

Status: runtime pinned to reviewed `6a493a0d489d8d1c76eba8c3431538d6412fd45a`. Separate pristine T15/T16 Git checkouts were created and verified at 2026-09-27 00:48 ET. The successful proof remains `8cbfee600f23416a8e9578fa8d3ce3f0e19fced8` and is carried separately as `linux_proof_runtime`. T15 and T16 admissions were prepared at 00:54:54.327820 ET and 00:55:23.313196 ET, respectively, then independently reopened by the preparer at 00:56:39.998480 ET. The complete installed helper subtree and both scripts were freshly verified against tracked origin/yanrujhou_main `67980a7016358858a5f8c77f9aca1213ddf90210` at 2026-09-27 00:52:46 ET; the helper checkout was not updated. Configurations pin this observation and original helper hashes.

Create separate pristine same-commit Git clones at `/data1/yanruj/EvolveSWDB_t15_supervision_recovery_runtime_20260927_a1` and `/data1/yanruj/EvolveSWDB_t16_supervision_recovery_runtime_20260927_a1`. Each batch writes its own records. Raw outputs and sibling dispatch directories use the exact new plan IDs under `/data/yanruj/EvolveSWDB_runs`. No records, proofs, raw logs, or binaries are rewritten or copied from earlier executions.

The operator reuses the exact reviewed proof-group `guard`, `free_lane`, `capacity`, `environment`, and exclusive-write helpers through a SHA-pinned sibling Git recipe. Both recipes and their fixed manifests must be delivered in the same Git operational packet. The new configuration must pin the replacement runtime's complete clean checkout manifest; fresh helper comparison; helper/hostlock bytes; Python bytes; and a prospectively selected free socket node. Its runtime and commit must match the operator's fixed values. A stale helper comparison cannot authorize a new launch: obtain and retain the current upstream/subtree comparison immediately before sealing the configuration.

Invoke preparation with isolated, bytecode-disabled Python and a bounded read-only process: `python3.12 -I -B operator.py prepare t15 /absolute/sealed-config.json` (or `t16`). It reopens the exact complete group receipt SHA `6458aa125ade00c41b6bb150429cd39c2e9c757efb89e982f9888c4f141eb14e`, validates both proofs and supplemental evidence, all historical charged failures, source/build availability, original scientific prerequisites and protocols, then writes a fresh admission in the new dispatch directory. Preserve any preparation failure; do not treat missing admission as permission to launch.

After independent admission readback and scheduling the short provider/T17 prerequisites, run `launch.sh` in one named tmux pane with exact `OPERATOR`, `OPERATOR_SHA`, `CONFIG`, `CONFIG_SHA`, `KIND`, and `ADMISSION_SHA`. The wrapper captures the actual shell PID before its stat subprocess. The operator rechecks unchanged admission, recipe/config/runtime, all three leases, capacity and disk reserve, then executes the existing batch supervisor through the socket helper and GNU timeout. It does not introduce another process supervisor or claim a lease in advance.

The T15 original absolute end remains 2026-09-27 09:14:09.851819 ET and latest full-series start 03:13:39.851819 ET. T16 ends at 20:16:17.225985 ET, latest start 14:15:47.225985 ET. Effective end is the smaller of the original end and actual start plus the unchanged remaining nominal allowance. Remaining nominal seconds are 39,603 and 74,426; every series still requires 21,600 plus the same 30-second cleanup reserve. Existing failures and the entire successful 600-second/2-GiB proof reservation remain charged without refund. Idle preparation time is never restored. The launch refuses startup exceeding 25 seconds, leaving room for the batch's 30-second first-observation limit.

After exit, root must run the existing independent terminal reader and recount raw plus sibling dispatch output within the applicable original accounting rules. An outer exit alone does not establish successful evaluation or ticket acceptance.


## Actual preparation checkpoint — 2026-09-27 00:56 ET

The nine-file operational Git packet is `cd970388aa157601e2e6cbda17d956978f8015ff`,
sole parent `6a493a0d489d8d1c76eba8c3431538d6412fd45a`, on private branch
`codex/bfs-simulator-recovery-operator-20260927-a1`. Its pristine host checkout is
`/data1/yanruj/EvolveSWDB_simulator_operator_20260927_a1`. Subsequent local review
and preparation receipts document that packet; they are not additional host code.

Both bounded metadata preparations passed the actual retained failure-cost,
standard and supplemental proof, input/source/build, original-window and frozen
protocol checks. The proof runtime stays 8cb with its complete 157-file map; the
scientific reader runtime is 6a with canonical `/usr/bin/python3.12`. No cost or
original deadline was changed. Both scientific runtime checkouts remained clean
and neither had a launch receipt at final readback.

| Batch | Admission SHA-256 | Prospective lane | Launch condition |
|---|---|---|---|
| T15 | `3d723561db50c6ee8e595bd0931b37c9de7a109ed6eede81245bcea62b12875a` | node 1 | Root independent admission verification and fresh free-lane/capacity check |
| T16 | `10307df14096aab7b5745661404f35b9a262b3b122ae86c0285d085510c0b057` | node 0 | External user must release node 0; no lane reservation |

The launch wrapper is the packet's `operator-recipes/simulator-recovery/launch.sh`,
SHA `6e495ceba7431f6b37d958dbd707bc985a35e7ef7f332c77acc26508a5bd9bed`.
The operator SHA is `58be86993f09a70b330bb214eb75e02a8af43584de66a48e53fb87396655797c`.
The T15 configuration SHA is `7f0260775627a0652d38b406fbab8aa601873a79141127c0c57f18bdb6db2910`;
the T16 configuration SHA is `c55ff2e24e130d8734f97950293ef9e9e4558abea768f9956a2000817b758493`.
Use absolute paths under the host packet checkout and the original wrapper's
explicit `OPERATOR`, `OPERATOR_SHA`, `CONFIG`, `CONFIG_SHA`, `KIND` and
`ADMISSION_SHA` inputs.

The first helper comparison mistakenly selected origin's default HEAD, which
lacks this host subtree, and rejected it. No helper checkout files were changed.
The corrected comparison uses the checkout's actual tracked `yanrujhou_main`
branch and verifies the entire subtree plus both script hashes. This is a
preparation-probe correction, not a scientific execution or evidence failure;
its classification is preserved in `helper-comparison-20260927.json`.

Local schedule/launcher controls passed four tests; independent operator review
passed six tests, including actual dry-launch clock clamping and a held-lane
negative. The new reader's actual old-proof compatibility and negative checks are
retained separately. These results admit preparation; they do not establish any
new simulator sample, qualified gain, or completed evaluation cell.
