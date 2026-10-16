# Ticket25 initial-import stage repair and v3 entry review

Date: 2026-10-15 ET. Verdict: PASS for a fresh coordinator-admitted replay of frozen c5216796dde05680acd237a97d4f0c7b3788e605 with the exact v3 entry/command reviewed below. No blocking changed-byte finding. Actual replay/import success remains unvalidated.

Review method: read-only Git diff/status, source/JSON/log text, Python AST parsing and SHA-256 checks. No tests, entry invocation, compiler, formal tool, prover or remote operation was executed by this reviewer. Only these outside-repository immutable review receipts were created.

## Source and command change

The clean local HEAD is c5216796dde05680acd237a97d4f0c7b3788e605. Its seven-path change contains one runner line, an18-line compiler-free plan regression, preserved admission-review receipts, actual-failure compact evidence, preparation controls and ticket notes. Production swdb and original fixture paths have no change from integration2f1ab7ce.

The only runner change adds `-wp-library <inputs/theory>` before `wp_input.c` and the first `-then`. The same path remains in the later WP phase. Mandatory RTE, initializedness, smoke, cache-none, machine, named target, solver, timeout and report flags are unchanged. Result matching, reader generation, source gates, shared lock and resource policy are unchanged. This directly repairs the command's missing initial-stage library setting without changing a logical obligation. Whether this is sufficient for the installed WP import interface must be established by the actual replay.

The retained GREEN plan contains42 rows. Independently reading that plan and its manifest shows identical ID/goal/kind/expected tuples for all42; each row has exactly two identical library values, one before the initial input and one after the first `-then`. The three mapping files retain final v5 hashes:

- heap_bridge.mlw:44cd626d07a93d105be791bff82fa201b525e09523a8f6598b92312a6a0b1eac
- source_vcs.py:5b6353263114ea31bf7ee9408b81a356b10ba1206ee4f21167c67d7d96f1a362
- packets.py:3299b9eb5f24d37228d26c18dc8a795c812b2410384899d680657d86fbdcead5

The v3 external entry AST parses. It is exactly the previously reviewed v2 source with its single expected024db66c full SHA replaced by c5216796dde05680acd237a97d4f0c7b3788e605. The command embeds that entire source byte for byte; all other argv elements are unchanged. Thus tool/plugin pins, ambient WP refusal, OCaml package binding checks, canonical42 precheck, configuration observations, source cleanliness and prepared-input checks are unchanged. Exact v3 entry SHA:ab2b9d7610970bc26dbef56e1d03bd4226212ef904e40777c8368b9614c36bbc. Exact v3 command SHA:a9f3b606af3d6336faa8ee2777d016e1594d2c2b8901e66c2999f63448721315.

## Evidence and claim boundaries

All six local RED/GREEN command/log/resource pins rehash exactly; resource objects equal their retained JSON files. The RED log fails the new initial-stage assertion with the old argv. GREEN reports22 passed in5.69s; guard wall6.192492208s, peakRSS129384448 bytes, exit0, no OOM/timeout. These are compiler-free preparation/policy checks, not an actual import or proof success.

The committed first-actual-failure compact preserves exact024db66c as producer, all42 precheck counts,9 selected tools,2 plugin artifacts, successful versions/package bindings, absent ambient WP keys, and the first leaf's `Library Heap not found` / `no such type Heap::heap` parsing error. It correctly records exit1, incomplete/mismatched outcome and no goal inventory rather than accepting this as a semantic negative. The ticket remains open and states that fresh actual replay is required. The12 remote raw pins in that compact were inspected as recorded evidence only; this read-only local review did not fetch or independently rehash remote bytes, nor assert a current lane state.

The v2 admission review files committed here match the reviewer's original immutable receipt digests exactly. v1/v2 external files and actual024 failure are preserved. Outer opam bootstrap, coordinator lane admission,9000/9120-second whole-command guards,8GiB process-tree budget and one-worker policy retain the prior review's coordinator-owned boundary. This command JSON does not itself implement those outer guards.

Still pending: actual WP33 initial import/syntax acceptance, actual resolved library/driver/task hypothesis and dependency audit, all ordinary/RTE/init/smoke outcomes and complete resource receipts. No c_model record, generic caller composition, full ticket25 body proof or production adoption is claimed.
