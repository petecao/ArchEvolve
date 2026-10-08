# Detached exact E administration R1 — independent source review

Source-only review on 2026-10-08. The selected wrapper, its complete derivation and handoff, and the original native observation were read in full. Local standard-library metadata/AST/diff comparison checked the packet; no target module was imported, compiled, lifted or called. No test, SSH, Git/worktree mutation, source copy, guard inspection, cleanup or removal ran. Selection for actual use remains pending the one bounded-read correction below.

## Original packet pins

| Original | Bytes | SHA256 |
| --- | ---: | --- |
| `/private/tmp/lanl14_detach_exact_E_cleanup_administration_20261008_a1_r1.py` | 18113 | `252c9735c034b3a305235dbcf95dd461a837e5d70dd031c7198ec7ac95cfeb24` |
| `/private/tmp/lanl14_detach_exact_E_cleanup_administration_20261008_a1.py` | 17278 | `645778f9e819f75e2b8414b93c0370635259d1d12bdb986a351a6a8794876c75` |
| `/private/tmp/lanl14-detached-exact-E-administration-r1-complete-draft-derivation-20261008.diff` | 3564 | `8f033c72e519903c45f0b6fb1d83596baa3528a9733b4c3b3f41910443d59454` |
| `/private/tmp/lanl14-detached-exact-E-administration-source-handoff-20261008-a1-r1.md` | 10172 | `4360d630ecf9c70c6b748b69630475a3487fbe2d0073c1ebe4e4b5e39fe16d3c` |
| `/private/tmp/lanl-detached-administration-native-pin-original-20261008-a1.json` | 1794 | `aee82e2b7d4ba8a50a55927f3cf8278918702e52b8d0067999b9564ced6c6694` |

The native observation is an original unsealed document. No original was changed or resealed. Its five literal native path/size/SHA entries agree with the wrapper NATIVE table. The unchanged guard is 22209 bytes/SHA `5a227cb9d68f638a5475e054bef6b4b85b1d477e857f18de04b54bf4097d160e`; the fixed original parent semantic review is 3258 bytes/SHA `fcf92eee1c4b8bdfaed979dc8bedab004c6c4b7e2b1410c7614bc92d60349f4a`.

The full unified derivation regenerates byte-exact from draft to R1. Only existing `inspect_prior` and `worker` definitions change; all other definitions, top-level imports, assignments and constants remain exact.

## Concrete finding requiring correction

In `process(pid)` the initial stat read, status read, and final stat read use `Path.read_bytes()` before testing their length against 16384/32768/16384. Those predicates bound accepted data, but do not bound the actual read/allocation. This conflicts with the declared finite read interface used for ancestry and transport polling.

A distinct minimal derivative should read at most cap+1 at each of those three sites, reject excess before parsing, and preserve the current stat/status/stat identity anchors and exception behavior. The existing native/source `file_bytes` loop already bounds reads at the read point. No permission adjustment, role exemption, production guard change or new test is required by this finding. The original draft/R1 and their NOTRUN chronology should remain unchanged. Parent and ticket03 were notified before any archival or use.

## Remaining reviewed behavior

No other concrete blocker was found in this complete source review. The following statements describe source behavior, not measured runtime success:

- The launcher binds its current account sshd ancestor and the root-owned sshd parent by public PID/start/PPID/name/UID facts, without a hardcoded transient PID or protected-reference exemption. A detached worker must be outside that original ancestry and observes the original account transport absent or its PID reused with a different start within 60 seconds. Missing or inaccessible relevant public identity fails closed. New or unrelated processes remain subject to the unchanged guard's checks.
- Fixed native byte/stat checks, private nonsymlink source routes outside PRIMARY/E/R/C, own source hash, guard hash and review hash are checked before launch and around the selected operation. The isolated tmux server has a fresh private socket/config; it does not modify an existing session, HOME or source permissions. Configurations, private streams and status use exclusive private originals. No auth environment or protected SSH contents are collected.
- The worker makes one unchanged invocation: native GNU timeout with TERM, KILL-after 60s, cap 660s, then native Python `-B` and the exact guard plus explicit expected primary and original service-review arguments. Removal is appended only for the explicit remove request. It does not retry, kill other consumers, waive leases/references, use sudo, or remove a broader path.
- Removal requires pinned original successful default status and stdout under the same private control prefix, same selected source/guard/review/primary, child exit zero, removed=false and no error_class. These originals are reread after detachment, immediately before the action. A failed or changed inspection cannot qualify. The inherited parent's explicit invocation review is a custody boundary, not a newly invented human approval gate.
- Original child exit status is retained; a nonzero child remains failure. Source/configuration or stream postflight errors are recorded and cannot become a reusable successful inspection. A launch failure does not claim no child started. A worker timeout does not claim completed cleanup or process disappearance.

The client 15s, original-transport 60s, GNU 660s/KILL60 and worker wait 735s limits are finite administrative allowances, not proven durations or hard bounds for every filesystem operation. The handoff's later collection timing is prospective. Starting another inspection SSH session while the strict guard runs can cause an honest refusal; no live SSH exception was added. Default success, separate removal clearance, actual host/capacity, reference completeness and scientific admission have not been established by this review.
