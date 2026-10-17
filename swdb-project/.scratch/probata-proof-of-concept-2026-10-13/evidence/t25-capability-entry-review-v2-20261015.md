# Ticket25 capability entry v2 independent inert review

Date: 2026-10-15 ET. Verdict: PASS for coordinator admission of the capability experiment; no blocking finding in the reviewed entry/command pair. This receipt does not approve any proof result or create a c_model record.

Reviewed only Python AST/text, parsed command/metadata JSON, local source text, Git diff and file digests. No entry invocation, formal-tool query, compiler, prover, test or remote operation was performed by this reviewer. The coordinator owns actual execution, live lane admission and outer process-tree guards.

## Exact reviewed inputs

- Entry: /private/tmp/probata-t25-capability-entry-v2-20261015.py; SHA-256 f765e6e70bea6b1471ada303386cc9d1a332eb3db03c23b3b97c5624cb73f33d.
- Command: /private/tmp/probata-t25-capability-command-v2-024db66c-20261015.json; SHA-256 2210a246b49f94e6988a371cdf0bc1d3f526ab28a6f30d417a321e1306261b62.
- Metadata snapshot: /private/tmp/probata-t25-remote-tool-path-metadata-20261015.json; SHA-256 c1f18660c983164aeb4637c790f3fdb04e06d5ab577d0e85cf1b796e0b5f5166. Only selected_tool_metadata was used to validate tool/plugin pins; other snapshot fields are not a live-state assertion.
- Expected execution source: 024db66c9ec4da43901f6662771a389b4567b334. Current local worktree HEAD is 2f1ab7ce56d1b738506fb327d9c2ff25304abbf0; Git diff confirms the four reviewed capability prototype files are unchanged from 024db66c. The entry deliberately refuses any actual execution checkout whose HEAD differs from the expected SHA or is dirty.

## Findings

1. The nine-element command array embeds the entire reviewed entry text byte for byte. It selects the pinned absolute opam binary, switch framac-33 and absolute Python interpreter, with {SOURCE}/swdb-project and {OUTPUT} as explicit positional arguments. No shell parsing is introduced by this array.
2. The entry resolves paths, refuses raw output inside the checkout and requires an existing coordinator raw root before source preparation. Source/cleanliness checks precede canonical preparation. The prepared manifest is checked and counted as exactly 42 packets: 41 global check lemmas (37 expected positive, four expected negative) and one numeric kernel. Canonical preparation/checking performs no formal-tool discovery. The same prepared input is rechecked before the reviewed experiment receives --input.
3. The ambient guard examines environment key presence, not truthiness: every FRAMAC_WP* name is refused even with an empty value. It writes names only to its receipt and does not dump the environment. This matches the production proof_setup._environment rule. All JSON receipt suffix literals are a single LF character, not literal backslash-n text.
4. All nine selected executable resolved paths and SHA-256 values exactly match selected_tool_metadata; both unique WP artifact digests also match. Every path/digest check precedes the first version/package query. SWDB_FRAMA_C and SWDB_OCAMLFIND are set to verified absolute paths before actual experiment discovery and fresh reader compilation.
5. All queried OCaml package directories must exist, resolve within the selected switch's lib directory and exit successfully; frama-c-wp.core additionally must resolve to the parent directory of the exact pinned native wp.cmxs. Bindings are retained and any mismatch refuses before fresh-reader compilation or the experiment. Version/package probes have explicit 30-second limits. Explicit configured Why3 paths, when set, must exist and are hashed without an environment dump.
6. The final invocation keeps the reviewed experiment source SHA gate, canonical inputs, declared stdlib directory, dedicated capability output, 10-second per-prover budget and 180-second per-leaf public timeout. The reviewed experiment retains the shared verifier lock, serial isolated targets, mandatory RTE/init/smoke/cache policy, fresh report reader and exact result-matching policy. Global lemma zero-smoke behavior and the separately required nonempty passing numeric smoke remain distinct.
7. The command JSON itself does not enforce root's outer 9000-second experiment / 9120-second wrapper, 8 GiB process-tree and one-worker admission controls. Those remain coordinator obligations. The declared budget covers 42*180 = 7560 seconds of serial leaves plus discovery, package/version probes, reader compilation and cleanup; no measured execution claim is made here.

## Claim boundaries

The outer opam exec environment bootstrap necessarily runs before the embedded Python checks; “before selected-tool execution” in the canonical receipt means before the entry's version/package/compiler/verifier probes, not before that bootstrap. Its exact executable path is already specified in the command and its digest is rechecked by the entry. Source Git checks and pure Python preparation also necessarily precede those probes.

This is a bounded capability admission. Actual WP33 syntax acceptance, actual resolved Why3/import/driver closure, generated task hypotheses and dependency audit, all generated ordinary/RTE/init/smoke results, tool resource receipts, and useful first-pair capability outcome remain pending. Declared stdlib existence/hashes and executable/plugin pins do not by themselves establish task assumption equivalence or formal success. No full ticket25 body proof, generic caller composition or production adoption is claimed. v1 files remain preserved and are superseded for admission by the reviewed immutable v2 files.
