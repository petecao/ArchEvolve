# Ticket25 cold typecheck audit and full-replay v4 entry review

Date: 2026-10-15 ET. Verdict: PASS for the actual standalone syntax/typecheck evidence and PASS for static admission of the exact full42 replay v4 entry/JSON. No blocking finding. Full WP capability outcomes remain pending.

The reviewer used read-only SSH Python file/JSON reads and hashing, Git object/status queries, plus local AST/text/JSON/hash comparisons. No compiler, formal tool, prover, test, evaluation launch or source edit was performed. Only these external immutable receipts were created.

## Actual syntax/type gate

Raw root:/data/yanruj/EvolveSWDB_runs/probata-reviewed-c5216796-t25-theory-typecheck-alpha-v1. Compact:/private/tmp/probata-t25-typecheck-cold-audit-v1-9d8ca764-20261015.json, SHA1d59130b53ff4fe71cf208feb0db988e897fa302cfcaf10debb2431de256bfdf.

Independently rehashed70 physical references:9 selected executables,2 WP artifacts, config, staged theory and57 declared stdlib files; zero mismatches. Independently checked all8 raw artifact hashes/sizes against the compact. Remote launch's exact nine-element command canonical JSON hash0558ae67d233ab8e3aef7e40ec304c0e62bb431f69dc4ab30d0f41a61ff46c35 equals the reviewed type-only command after placeholder substitution. Embedded entry SHAef6d6fdce6e316066a94fa5306929bf82dface72de1667aa7227f4412a30aca4 matches the reviewed entry.

Independent remote Git queries confirm old bootstrapc5216796dde05680acd237a97d4f0c7b3788e605 is currently clean, staged theory equals the new9d8ca764 Git body, blob8b3c2bf3f4c831b1e28499ffafad78c196819ec5 and content SHA5186c27f5a7a339352e3f62dc3a0d3efb1c7bd12f8a456cc61b0d7a52566638d. The profile retains distinct bootstrap/theory identities and the expected stdlib tree digest520d9875983b41da80b89d7809cff4c76370e8445f8b49147f1423cfb7404c31.

Pinned Why31.8.2 prove --type-only exited0 in0.067665800s, peakRSS32890880 bytes, no timeout/OOM. Whole guarded command exited0 in0.651877777s, peakRSS62087168 bytes, no timeout/OOM. The only log diagnostic is the unused dummy variable warning. Profile records no WP/solver launch and zero model-body proof records. Retained lane receipt reports node0 generation584 ended2026-10-16T02:51:21Z; this historical receipt is not a current lane reservation claim.

Budget provenance correction: actual launch.json uses whole timeout600 seconds and8GiB/one worker; actual socket wrapper uses720 seconds. These supersede the earlier proposed300/420 values for this run. Both actual resource limits were respected; inner typecheck budget remains60 seconds/8GiB. The review records actual values rather than retroactively claiming the earlier proposal was used.

## Full42 replay v4 entry

Entry:/private/tmp/probata-t25-capability-entry-v4-20261015.py SHA862d3844a4768902b920d66e51889b2d019ca54f2924faf3d0b274cfc314b434. Command:/private/tmp/probata-t25-capability-command-v4-9d8ca764-20261015.json SHA12062ef5a25e422dbb8eacbc264e4ad51f79d7f6ee831dc09005bfa2bd3a12dc.

AST parses; the command embeds the whole entry exactly. Both files equal reviewed v2 with the single expected source SHA024db66c replaced by9d8ca7645546ce3b282b2a51005392ceb78ff609. Every other argv element, physical tool/plugin pin, package binding check, ambient WP refusal, canonical42 precheck, output policy and final experiment argument remains unchanged. The exact9d8 source has separately passed the alpha-only review and preserves the repaired initial-stage library flag and all42 mapped targets. The replay still requires its own clean exact9d8 checkout; the oldc521 bootstrap's successful standalone typecheck is not substituted for that source gate.

Root owns fresh live lane/serialized admission and outer9000/9120-second,8GiB,one-worker guards. This entry does not itself implement those outer guards. A standalone typecheck pass does not prove actual WP import compatibility, source-to-VC mapping adequacy, generated ordinary/RTE/init/smoke goals, nonvacuity, actual resolved import/task-hypothesis closure or full ticket25 body correctness. Those remain pending; no c_model certification or production adoption is claimed.
