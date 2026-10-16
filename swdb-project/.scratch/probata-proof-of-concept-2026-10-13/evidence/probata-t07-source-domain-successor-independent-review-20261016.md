# Ticket07 source-domain successor independent review

Created: 2026-10-16 00:20 ET. **PASS static review of the exact two-file freeze.** This does not authorize a component, a counted run or a proof-success claim. Root owns source commits and actual admissions.

Reviewed checkout `/private/tmp/probata-resume-t07-source-domains`, base `13225a825aa1be9882d9031787ebf939991c0cb0`. Exact gapbs_models.h SHA-256 `62c482f54d2ed6771d0f91bbff5c807226ee2b9f5d53c9a2047f4dc63424bfd2`; tdstep_standin.c `3cee3cb2062bbd07d7f1c42b769d967ae739824ef0cf5cc97ff7a534fc12a9b6`. Physical hashes match. Removing comments/whitespace leaves the C token text in both files identical to that base; this is a lexical preservation check, not an independent C++ lowering theorem. The original algorithm, executable helpers, postconditions on TDStep, and C++ proof unit have not been changed by this repair.

## Findings closed

| Boundary | Static result |
|---|---|
| Named queue registration accessors | Full-storage beginp/endp restored. Exact modified DX100 e4fc4af header distinguishes them from active-window begin/end. The earlier window native oracle remains excluded; no missing-definition assumption is needed. |
| Pointer subtraction and live spans | Copy and pvector domains now require common allocation base, live endpoints, ordering and a pre-subtraction offset representability bound. Destination spans/read-write ranges are explicit. These remove the identified reliance on comparability alone. Installed WP handling remains a component question. |
| Input initializedness | Queue/buffer metadata and accessed pvector/Graph fields use precise initializedness clauses; TD input arrays and occupied queue prefix are explicit; atomic reads and copy source are initialized. No whole-struct-padding premise is introduced. |
| Opaque update initializedness | Primitive CAS/fetch and their wrappers now publish initialized pointer outputs; std_copy publishes its written range; flush and flushed push export their copied shared range. These are legitimate effects of the source operations, not assumed desired BFS properties. |
| Allocation/lifetime scope | Exactly one thread-zero buffer lifetime, no escape, overlapping live construction or repeated destruction is explicit. This remains a restricted fixed-storage stand-in, without general freshness/dangling-pointer/allocator claims. |

The output initializedness repair matters: installed WP MemLoader.ml598–613 can havoc both values and initialization for assigned pointer-memory locations/ranges. MemVar preserves monotonic initialization on only some direct-value paths. Explicit postconditions avoid depending on a favorable internal memory classification. They have not been solver-validated here.

The capacity premise is caller history: capacity equals symbolic num_nodes and all previously occupied slots contain distinct valid already-visited vertices. It does not assume that TDStep reaches every relevant vertex, sets the right parent, enqueues new vertices or preserves output uniqueness. Those remain proof obligations. Natural DOBFS construction and first-discovery insertion support the premise; a complete caller proof across direction switches is still absent and must not be claimed.

No further concrete source-contract falsity or desired-result premise was found in this freeze. The standard-copy and pointer helpers deliberately restrict their public domains to live nonnull array spans; this is not a claim to support every C++ iterator program. The device summaries remain unchanged throwaway assumptions. This review does not certify their C++/gem5 equivalence or all TDStep RTE obligations.

`-wp-no-filter-init` disables aggressive filtering of initialization hypotheses (wp_parameters.ml479–483); it is not initialization instrumentation. Existing counted modes still lack `-wp-rte`. Any stricter helper component below is separately scoped and cannot retroactively upgrade run26 or another earlier source/method.

## Finite no-hint helper/RTE component plan

This plan is inert. Root must bind the exact source/tool/runtime identities, enforce the Mac actual-verifier slot, live preflight, fresh outside-checkout output, one worker,8GiB sampled process-tree cap and whole-job timeout before any execution.

1. Stage a fresh translation unit containing only `#include "gapbs_models.h"`, with the exact frozen header and ordinary standard includes. Preserve **all19 header bodies**. This is a helper component; TDStep is not its subject. Record the exact include paths and machdep. No generated hint, previous candidate, provider state, test stub or prior proof result enters this TU.
2. In one admitted guarded invocation, parse that TU and generate the complete helper VC/RTE/smoke inventory with no prover. Parse the AST before resolving the explicit19-function `-rte-initialized` function set; use `-wp-rte`, x86_64, current complete report/exporter machinery and fresh/cache-none output. Do not use `-wp-fct`, `-wp-prop` or selective helper suppression. Verify the19-body inventory and unchanged source/header/report inputs. A120s cap is a prospective finite allowance, not a measured runtime estimate. Any parser failure, unsupported-predicate warning, missing/duplicate inventory, resource refusal or input mismatch stops the component.
3. If that gate passes, run a separate fresh full all-helper replay with Alt-Ergo/Z3/CVC5,30s per solver/goal, `-wp-par 1`, `-wp-rte`, the explicit same19-function initialization set after parsing, `-wp-no-filter-init`, smoke, cache none, default warning levels and no WP environment variables. No supplied hints, strategies, extra axioms, property filters, disabled bodies or unchecked cuts. A900s proof cap and approximately1100s outer whole-component cap are finite proposals; the coordinator must choose/freeze exact enforcement. Preserve solver/time/status per goal and the complete property report. Require all generated ordinary, contract, call-precondition, frame, RTE/init and termination obligations Valid, plus every generated smoke passing. The six exact bodyless summary functions below alone may account for expected Extern assumptions; every unexpected Extern/refusal fails. Do not require fabricated smoke goals for functions where Frama generates none, and do not waive any generated smoke or ordinary goal.

The19 bodies are: compare_and_swap, fetch_and_add_size_t, std_min_size_t, omp_get_thread_num, pvector_NodeID_operator_index, pvector_NodeID_data, pvector_NodeID_beginp, pvector_NodeID_endp, pvector_SGOffset_operator_index, pvector_SGOffset_data, pvector_SGOffset_beginp, pvector_SGOffset_endp, SlidingQueue_NodeID_beginp, SlidingQueue_NodeID_endp, SlidingQueue_NodeID_size, QueueBuffer_NodeID_QueueBuffer, QueueBuffer_NodeID_destroy, QueueBuffer_NodeID_flush, QueueBuffer_NodeID_push_back.

The exact bodyless assumption allowlist is: __sync_bool_compare_and_swap_NodeID, __atomic_load_n_NodeID, __sync_fetch_and_add_size_t, swdb_new_NodeID_array, swdb_delete_NodeID_array, std_copy_NodeID. This is an allowlist, not a requirement that every unused declaration produce an Extern line. Each actually relied-on external contract needs an attributed assumption entry.

Retain source/header/command/tool/OCaml/runtime pins, parse and generation logs, generated normalized C, complete goal/property inventory, setup and resource receipts, source-unchanged checks and independently bounded post-stop observations. Complete per-goal scheduling/report counts must agree; an empty or missing report cannot pass. A successful component establishes only the declared helper/ACSL/WP boundary. It supplies neither TDStep induction nor ticket07 acceptance.

A later counted proposal must update the historical source guards/prospective method to these new bytes, receive exact-byte review and start with a fresh Codex and empty hints. Preserve the original counted budget/final/negative gates unless separately specified by a reviewed prospective method. Do not rerun merely because this source review passed.

## Exact inventory

JSON: `/private/tmp/probata-t07-source-domain-successor-independent-review-20261016.json`, SHA-256 `e08a6e07a1e41a005f28fbcc349d972219d2ab0cd1c21a2ab73641dc9dbaad4a`. Reviewer ran no tests, compiler/native programs, version probes, theorem provers, providers, solvers or SSH. Only source and metadata were read; the JSON lists all exact read pins and the two lexical preservation comparisons.
