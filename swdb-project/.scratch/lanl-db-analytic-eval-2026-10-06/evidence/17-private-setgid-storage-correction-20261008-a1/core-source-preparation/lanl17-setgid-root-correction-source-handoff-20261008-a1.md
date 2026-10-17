# Demonstrated inherited directory-SGID root correction — source-only handoff

2026-10-08 ET. Every selected target and all fifteen synthetic test bodies remain NOT RUN. No imports, guard/helper/main invocations, SSH, Git mutations, project edits, source mode changes, storage admission or observer-success claim occurred. Existing originals remain byte-exact. This packet changes neither walk entry behavior nor finite limits.

## Exact source and derivation pins

| Original/selected source or complete derivation | Bytes | SHA256 |
|---|---:|---|
| lanl_consumed_detached_source_guard_r4_20261008_r3.py | 88521 | `96e033426d492fab3be2a07757ab1e89665a7a67d0f06d3941f274b1214dd294` |
| lanl17_acquire_passive_consumed_source_metadata_20261008_a1_r5.py | 58755 | `50ad9bf511f90429a040bf5c25cc9a4bd15b12cb28419ad414d586269e5cdc99` |
| lanl_consumed_detached_source_guard_r5_20261008_a1.py | 88872 | `a84dc9ca7ccd20e6485cc8e9a2007b3b982fad9c5ae19dacbb1f164d664748cb` |
| lanl17_acquire_passive_consumed_source_metadata_20261008_a1_r6.py | 58750 | `488fb42df44d338204b5cff58b10e7f0ff9c7feaee6490b33ba94201ba4f7665` |
| lanl17-setgid-guard-complete-original-derivation-20261008-a1.diff | 963 | `ae3daf3478ecdda42b726efcbbc4e68fea4c2ce5be66658730b407b2530227f9` |
| lanl17-setgid-observer-complete-original-derivation-20261008-a1.diff | 881 | `4313e908f3b9be609d9f57911c409f748cc5a3f04edaf265605bbf2720d45c09` |
| lanl17_setgid_root_virtual_path_regression_source_20261008_a1.py | 9064 | `1ff994f06bcfb26423137aea89cc415ffcb9e6facacb5dcd4f32fe9b73994e93` |

All files above are in `/private/tmp`. The separate unsealed static comparison is `/private/tmp/lanl17-setgid-root-correction-static-source-comparison-20261008-a1.json`, 3328 B, SHA256 `235b04095abcd3494ec1d42f8370d5490a9e2dc4de1975f95a7638b01c4997d9`. It records parse/comparison results, not target/runtime test evidence.

## Exact policy and change boundary

G5 replaces only the final special-bit condition inside `Guard.path`. Existing canonical path/type/owner/nonredirect/auth/writable-ancestor checks run first. Directory SGID is permitted only with explicit `directory=True`, literal BASE in the canonical path's parents, the existing verified private BASE0700 gate, mode special bits exactly02000, GID equal to verified BASE GID, and device equal to verified BASE device. UID114 ownership is the unchanged preceding gate. GID/device are read from the existing fixed privacy identity produced by `check_private_root`; no new caller-supplied identity or fabricated clearance is introduced. The observed BASE values are GID0/device2097, but the source preserves the original checked-root identity mechanism and existing end checks.

Regular-file SGID, SUID/sticky and combined bits cannot use this exception. PRIMARY's previous broad `special` bypass no longer waives special bits: mode0 passes, modeSGID must satisfy the same checked BASE identity, SUID/sticky fails. Its existing writable-bit handling remains unchanged. `Guard.walk`, all other guard methods, shared exact account-service helper, ROWS/RECEIPTS/FUTURE_SOURCE_HASHES/LIMITS and every other top-level AST node are unchanged. This correction does not exempt RAW or any path denied by the original credential policy.

O6 changes exactly R3/R3_BYTES/R3_SHA to the new G5 private route:
`/data1/yanruj/lanl-storage-admin-selected-source-20261008-a4/lanl_consumed_detached_source_guard_r5_20261008_a1.py`.
That prospective route is not claimed staged or available. It replaces the old binding to unchanged G552 under PRIMARY. All observer definitions, including its custom PRIMARY walk, remain exact. The observer still invokes only the reviewed guard's passive definitions/API; source-copy/mode checks and actual observer execution are parent-owned future steps. No module/table monkeypatch is introduced.

## Isolated virtual-path harness for parent review

The harness reads exact originalG96/newG5 local bytes, parses their ASTs, and—only when parent explicitly authorizes the future batch—lifts four original route assignments, original Refused/require/inside/stamp definitions and exactly Guard.check_private_root/private_ancestor/path. It never executes any target top-level import, constructor, main, action, filesystem walk or Git/SSH operation. The target paths and stat facts are an in-memory VirtualPath registry; only the two reviewed source files themselves are read from local storage.

Fifteen test bodies cover accepted SGID EV/model/baseline directories; PRIMARY normal/SGID acceptance and SUID/sticky combinations refused; SGID regular file refused; SUID/sticky/foreign GID/device/owner/symlink/nonprivateBASE/outsideBASE refusals; private-root identity mutation and credential denial. One body demonstrates the originalG96 refusal for the same virtual EV2777 fixture. This is the relevant expected RED/changed GREEN comparison, presently unexecuted. The baseline source remains unchanged; no prior writer/observer/guard suites are repeated.

Exact prospective harness argv, subject to parent full source/argv review and one separately recorded authorization:
`/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3 /private/tmp/lanl17_setgid_root_virtual_path_regression_source_20261008_a1.py`

No actual inputs, process visibility, byte coverage or capacity can be inferred from a future synthetic pass. The separate identified CPU T1 raw preservation routes and any bounded original IR/JSON metadata reads are outside this patch; no observer-root widening or cap increase is included.
