# Ticket 14 export/reader descendant boundary — source review

2026-10-07 ET. Read-only source review of the unchanged selected controls. No import, main, test, native/provider command, SSH, staging, Git mutation, or actual invocation occurred. Parent's prospective GNU limits are export 18000 seconds and reader 14400 seconds, TERM followed by KILL after 60 seconds. These limits have no measured duration proof; validation and codec limits remain 3600 seconds.

## Conclusion

The selected call graph supports direct GNU group termination for the outer-deadline path. Its sole explicitly detached child is exported catalogue validation, which has the existing group and subreaper cleanup. Later Git calls and the reader's Git calls do not request a new session.

This is not a complete descendant-cleanup guarantee for an earlier internal Git timeout or other early parent exit. `subprocess.check_output(..., timeout=120)` owns its immediate Git process, not a process group. If a Git-created transport/helper remains after that process is killed, the uncaught failure can end the monitored Python process before GNU's outer deadline; the later outer group KILL is then not an assured cleanup step. This is a source-level unguarded failure branch, **not evidence that any descendant actually survived**. No selected control modification or new wrapper is proposed in this review.

## Exact boundaries

- Exporter 928 lines 242–254: enables Linux subreaper; handles TERM/INT/HUP during validation; starts `python3 -m swdb validate` with `start_new_session=True`; waits 3600 seconds; finally ignores those signals, calls `stop_group(child, grace_seconds=15)`, then requires original 31e `cleanup_owned()` to return no survivors. `processes.py` lines 7–29 performs group TERM, up to 15 seconds of leader wait, group KILL and up to 5 seconds of wait. Original 31e lines 485–531 enumerates this subreaper's same-UID descendants/adopted orphans with start-time identity, then TERM/15 seconds and KILL/5 seconds. The nominal wait allowances sum to 40 seconds; process enumeration and other work add time, so this is not a measured wall-time bound.
- The exporter does not restore its handlers after line 253. Its subsequent Python work and exec'd Git processes inherit ignored TERM/INT/HUP. A later outer timeout therefore relies on the 60-second KILL step for that original GNU group. This does not create a new session by itself.
- Exporter lines 207 and 276 call e79's checked source/manifest paths; e79 lines 150–154 call b797's Git-backed source and authoritative-wrapper checks. They do not invoke e79's `dispatch()` or `run()` or b797's counted `run_case()`.
- b797 lines 37–39 implement `h.git()` through synchronous `check_output` with a 120-second timeout and no `start_new_session`. Its wrapper check lines 50–54 performs Git fetch/show/rev-parse. Exporter lines 234–237 also perform bounded branch checks and worktree creation. Lines 281–287 perform add, diff, commit, optional push and final source checks after the validation cleanup block. There is no final `cleanup_owned()` enclosing these Git stages or the earlier pre-validation Git stages.
- Reader 690 line 249 uses synchronous Git with timeout 120 and no new session. Its main performs selected-file parsing, hashing, read-only binding/reuse/protocol checks and in-process codec work. It invokes no evaluator, provider, compiler, Store/full validator or e79/count runner. It has no process-group or descendant cleanup block. Its local Git failure boundary has the same immediate-child ownership limit; the selected source does not establish an actual escaping helper.
- GNU group conclusions assume the parent's eventual direct GNU invocation, without `--foreground` or an intervening session-detaching launcher. Actual executable paths, transport/configuration, signals, argv/environment and process visibility remain future host facts. Source review cannot establish actual survivors or successful cleanup.

## Byte pins

| Original source | SHA-256 |
|---|---|
| `/private/tmp/lanl14-actual-export-reader-invocation-source-review-20261007-a1.md` | `32cba5a87a408a017aaa99fc3049ce0ff8ddc55bac8e2426428ab46e03008223` |
| `/private/tmp/lanl14_final_export_lossless_gzip_20261007_a1.py` | `928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e` |
| `/private/tmp/lanl14_final_export_catalog_caps_a4.py` | `bf5add9eb35daa5402a0359f6ace5c542a289f9b60b14cbd00aa763097a9645d` |
| `/private/tmp/lanl14_readonly_nine_export_admission_lossless_gzip_20261007_a1.py` | `6909c422990a071b1a8d08c634c1c086f0218c5851d38996b6f4798759499570` |
| `/private/tmp/lanl14_final_reports_catalog_caps_a5.py` | `e79e4b2e295f07967a1f4f67e7501c35d9d402101330ac9347f98cfb282bf63a` |
| `/private/tmp/lanl14_count_dispatch.py` | `b797a19f0d80a1a91b852a360c19e59beba4fa082ce88c38cbec029670e7deda` |
| `/private/tmp/lanl17_parent_helpers.py` | `31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec` |
| Owned ticket11 `swdb-project/swdb/processes.py` | `bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289` |

Selected exporter/reader and original bf5 are already byte-retained in `swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-lossless-report-export-controls-20261007-a1/`; e79 is retained in `14-report-kill-margin-controls-20261007-a5/`; original 31e in `11-native-controls-20261007/`. This note adds no execution or actual admission facts.
