# Resumed-main launcher V7: independent review

Date: 2026-10-16 ET. Reviewer: `caller_assess`.

**PASS for the V6-to-V7 launcher change and exact initialized-pair source/control binding. No blocking finding.** Root still owns fresh remote admission, execution and settlement.

| Reviewed input | SHA-256 |
|---|---|
| `prototype/resume-root-20261016/launch_reviewed_main_v6.py` | `67082813f7f87e47582259fda191cbd1035a6da3f517f939eaa8906fb4ca9ca7` |
| `prototype/resume-root-20261016/launch_reviewed_main_v7.py` | `e54ee1f4b159505b4f9c41d847404ec7adcb345f8158430862851005194243c8` |
| `prototype/resume-root-20261016/t28-initialized-pair-2baf-source-review-v7.json` | `ae80ed43b55efb20f19c86c9057880eaf477b2f3a37f6d6372606f49f966e89a` |
| `prototype/resume-root-20261016/t28-initialized-pair-argv-v1.json` | `4eebac5b2ce8295a0dec20d3b857557e642be60e1cc5561ec0b79f0d165da2c9` |

The complete textual delta adds only base64 transport, an optional reviewed raw-output root and optional pinned control-file staging. Raw roots must be canonical direct children of `/data/yanruj/EvolveSWDB_runs`, use the fixed resumed-run prefix and include the selected commit prefix. Remote creation remains fresh (`exist_ok=False`) and refuses a symlink. No existing output is overwritten.

Control names exclude traversal/separators, are unique, and their aggregate is limited to one MiB. Local bytes/length/hash are checked before transport; remote base64 decoding validates and rechecks them before exclusive creation under the new output's `control/`, then rehashes the physical file. Source worktrees are untouched by staging.

The reviewed initialized-pair command names exactly those staged entry/policy paths under the explicit raw root. The 20,760-byte entry matches `615f6c867a29101e1dee2072893fea212f6c2843c77f6bbd3d18538fc891300a`; the 84,621-byte policy matches `574e8fba725e65cb8113795b784e7869005801cb2dc4dc5cd5adc21c2b3ed7f0`. Its independent source-review receipt physically matches its declared hash. Git confirms the complete production delta from `c978393b119a3614229a37f0f2c8ca2a097c750b` to `2baf722fdaa6cba24b859eae3172a6f597417d72` contains exactly the declared two vector reserve-application files, with matching content hashes.

Source ancestry/clean detached checkout, reviewed socket/host-lock wrapper hashes, selected/legacy lease checks, sanitized direct `env -i` dispatch, 8 GiB worker wrapper and disk floors remain unchanged. Timeout behavior is unchanged: accepted `seconds` is 60–21600; worker launch records that value; socket dispatch uses GNU `timeout(seconds+120)` with TERM and 60-second kill grace. Source/metadata preflight and the initiating SSH call themselves retain V6's existing unbounded waits; this change adds none and does not claim a whole-launch timeout.

Both launcher ASTs and their literal remote program bodies parse. Review used local source/metadata reads, read-only Git and standard-library hashing/AST only. No launcher, runtime import, compiler/native helper, test, verifier, solver or SSH execution occurred. This PASS establishes no actual run, live capacity, lane ownership, proof result or ticket acceptance.
