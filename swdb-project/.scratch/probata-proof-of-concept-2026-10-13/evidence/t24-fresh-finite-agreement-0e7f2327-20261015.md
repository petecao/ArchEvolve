# Fresh original finite agreement at 0e7f2327

2026-10-15 ET. **All 18 case classifications completed: 17 agree on defined inputs and the allocation seed is UB-only.** The fresh run records 112,589 equal defined input comparisons at published source `0e7f232762e4555aa9435a3a3622923fad8ee928`. This is finite observed native C++/ordinary-C agreement under ticket 22's accepted profile; it is not a formal C++ equivalence theorem, WP checking-view agreement, device semantics theorem or new proof verdict.

| Original group | Safe defined comparisons | Seeded defined comparisons | Known seeded UB exclusions |
| --- | ---: | ---: | ---: |
| classes | 16,658 | 16,658 | 0 |
| templates | 25 | 25 | 0 |
| new_array | 500 | 0 | 500 |
| std_models | 8,360 | 6,658 | 1,702 |
| omp | 19,783 | 19,783 | 0 |
| atomics | 125 | 125 | 0 |
| floats | 11,909 | 11,909 | 0 |
| dxc_summary | 3 | 3 | 0 |
| maa_summary | 35 | 30 | 5 |

The 47,164 original precondition exclusions remain separate from 2,207 known UB exclusions. Those UB cases are the original allocation seed's `buf[n]` write, the standard-copy seed's `a-1` formation at n = 0, and the maa seed's signed n+1 overflow at INT_MAX. Excluded inputs remain represented in the requested domains. The allocation seed has zero defined comparisons and is never labeled agreeing on defined inputs. No runtime sanitizer UB or one-sided sanitizer asymmetry was observed on executed inputs.

The committed `prototype/t24-finite-agreement.py` is byte-identical to the accepted e48a302e engine (SHA-256 `7948aefc4b5d9afbd07e65b90282630dd209edf0aba07f9c553efe7fa37a3f8e`). It used the unchanged ticket 22 domain generator/seed 22 and original preconditions, source-specific UB classification, real original C++ TU plus shared harness, generated ordinary C plus shared harness, and actual fixture dependency bodies. Native language modes stay GNU C11 and GNU C++17, with the accepted ASan/UBSan and -fwrapv policy. Known original overflow is explicitly excluded despite -fwrapv. No new planted-control execution is claimed; the existing accepted engine controls remain separately pinned historical evidence.

A new clean producer checkout was created at the exact published freeze, separate from earlier accepted float/native paths. All 8,550 tracked swdb-project source files match before/after; source-after HEAD stays 0e7f and its status is empty. Fresh runtime provenance is complete: selected executable/frontend, matching libclang and 1,982 standard/resource headers are hashed; no unavailable fallback is accepted. The Mac aggregate lowering identity is `077947cb193890b2a229be0d19200c01194558c563feb40239532dabb7307c9f`. Host-specific aggregate identity is retained as such, without relabeling remote identities. Link-time SDK stubs and physical libraries are hashed by the engine; dyld-cache runtime bytes are not independently hashed.

One sequential worker ran under a whole-worker 8 GiB RSS watchdog and 900 s deadline, including compiler/provenance bootstrap and native descendants. The trusted outer monitor is excluded from that measured tree. It exited 0 in 60.570 s with peak 1,310,572,544 B, no timeout/OOM. Raw output was monitored against 2 GiB (not a filesystem quota); retained output was approximately 349 MB and the monitor did not trip. No formal verifier or remote job ran. The existing other Mac verifier slot was preserved.

Agreement manifest: `/private/tmp/probata-agreement-0e7f2327-20261015/native/agreement.json`, SHA-256 `0d037c05a4e8ffebea483750dafd3c40fddf5d4aec861f77802bcaf14bc28303`. Engine self-audit rehashes 15,771 physical references with zero errors. Independent ticket27 review rehashed all 15,771 references (1,366 unique physical files) plus all 8,550 whole-source manifest files, reconstructed source/seed/contracts/draw order/seed22 oracle/preconditions/UB classifications/raw remapping/defined streams, and independently computed all 112,589 defined original-source observations. No discrepancies were found. [Independent receipt](t24-fresh-finite-independent-review-t27-20261015.json) is committed at `88d5581aae0e6d1a891ff311300b9a5c9e0085e6`, SHA-256 `e24797cda795fea9f46aa7e6f54380bea46d071cf412667d17d6f0fa7c7e08b5`.

[Compact receipt](t24-fresh-finite-agreement-0e7f2327-20261015.json) retains all 18 row counts/classifications, artifact/source/runtime/tool/launcher pins and resources. Raw originals remain outside Git at `/private/tmp/probata-agreement-0e7f2327-20261015/`. Producer checkout `/Users/yanrujhou/.codex/worktrees/probata-t24-agreement-0e7f/ArchEvolve` stays clean through current/final readers; the coordinator owns later recoverable cleanup. This receipt is prepared in a separate docs checkout. Ticket 24 remains claimed; actual WP pairs, current dependencies and other acceptance limbs stay separate.
