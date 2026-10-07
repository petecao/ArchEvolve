# Ticket 14 lifecycle supervisor draft — independent source review

2026-10-07 ET. Full source and complete fa703 derivation read; original 31e cleanup and frozen bcc9 `stop_group` boundaries rechecked. No target import, main, fixture, test, SSH, staging, Git mutation, project edit, or actual input inspection occurred. Earlier f339 descendant-boundary note remains unchanged.

## Finding requiring the planned distinct R1

Draft lines 124–131 validate the supplied `action`, but `immutable(context)` checks `SOURCES[context.action]`. Receipt lines 170–175 describe `SOURCES[action]`. An internal API/fixture caller could supply a different admitted action and mislabel the selected source and allowance. Production `main` lines 190–192 supplies the same action to both. Require exact `action == context.action` before launch/receipt. Parent identified the same boundary and selected a separate one-guard R1; that revision is not reviewed by this draft note.

No additional concrete production blocker found in the reviewed draft.

## Lifecycle and custody assessment

- Lines 136–146 install interruption handling, enable the subreaper **before** launch, and start the complete selected exporter/reader in a new session. Early internal Git failure now returns to this enclosing supervisor; it no longer depends on an outer GNU deadline eventually firing.
- Lines 155–166 always run cleanup after return, timeout, interruption, launch error, or other exception. Original `stop_group(child, grace_seconds=15)` runs even after a returned leader, and the original 31e descendant/adopted-orphan cleanup still runs if `stop_group` raises. Cleanup errors, surviving processes, or changed source bytes prevent supervision success.
- Original 31e lines 485–531 scope termination to this subreaper's same-UID descendants/adopted orphans, with process start-time rechecks. Frozen `stop_group` sends group TERM and KILL even after the leader has returned. Thus both same-group leftovers and a reparented session-escaped child have a source-supported cleanup route; an unrelated sibling is outside that ancestry scope. Actual Linux survival/cleanup is still untested here.
- Lines 148, 163, 167 and 171 preserve a child return of 7 in `returned_child_exit`, `child_exit` and `supervisor_exit`; its state is `child_failed`, not success. Timeouts/signals and cleanup failures remain explicit in the receipt. No scientific result is admitted by any child return code.
- CLI actions are only exporter/reader. The child uses the explicit pinned native Python, `-B`, and selected 928/690 source. `fixture=True` exists only in the internal API, has no CLI flag, and does not bypass context/source checks. The source/native paths, module count/F6, selected bytes and supervisor self pin are checked before and after supervision.
- Fresh output is under the fixed raw roots, with nonsymlink owned parent 0700, fresh directory 0700 and exclusive original streams/JSON 0600. The returned receipt is capped at 16384 bytes and excludes original argv, environment and stdout/stderr content. Exact cleanup data remains private in unsealed `cleanup.json`, byte-pinned by the sealed lifecycle receipt. The new receipt explicitly declares `canonical_ensure_ascii: false`; it must retain that original policy.
- The imported 31e module has no top-level campaign/provider invocation; the supervisor invokes only its cleanup function. Selected 928/690 and their original validation/codec/scientific formulas are not rewritten by this derivation.

## Explicit limits

The 18000/14400-second allowances bound `child.wait`, not all preflight, source hashing, cleanup and receipt publication. The cleanup wait allowances are 15+5 and 15+5 seconds plus enumeration/work overhead; no actual total duration is proved. Any future external hard-kill margin and original outer status must be retained separately. Native interpreter path/SHA, cwd, project/input arguments, private output parent and host/process facts are supplied and checked only at a future parent-owned invocation. The pinned Python is the supervisor and selected-control interpreter; unchanged 928's nested validator still uses its original `python3` resolution and environment. No broader interpreter/runtime claim is inferred.

## Exact source pins

| Source | Bytes | SHA-256 |
|---|---:|---|
| `/private/tmp/lanl14_export_reader_administrative_supervisor_20261007_a1.py` | 14471 | `8cad3bc1986de0ae160535d71fbea580deddaf400658753ffe1dfdee76374837` |
| `/private/tmp/lanl14-export-reader-supervisor-complete-derivation-20261007-a1.diff` | 18702 | `e2d98fbe1101ea2604d03f318f6edd81aae1af75c869bbcbb9356e41fbb93e0e` |
| Original `/private/tmp/lanl17_metadata_supervisor_cleanup60_a4.py` | 8014 | `fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0` |
| Original `/private/tmp/lanl17_parent_helpers.py` | — | `31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec` |
| Frozen `swdb-project/swdb/processes.py` | — | `bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289` |
| Selected exporter | — | `928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e` |
| Selected reader | — | `6909c422990a071b1a8d08c634c1c086f0218c5851d38996b6f4798759499570` |

C185/F6: `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3`. Source review provides no runtime or report acceptance evidence.
