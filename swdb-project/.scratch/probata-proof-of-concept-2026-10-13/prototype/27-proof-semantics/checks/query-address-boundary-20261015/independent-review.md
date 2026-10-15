# Independent footprint-query review

Reviewed 2026-10-15 ET. Initial runtime `e3d21284bb9050b6299881f0c00c4acc52b2429d`; repaired runtime `4c860f39b93f1421e55d85e4b8d401dc20433fd8`; composition `8e37727424b72a2b0520e7ea14a95dc1e57b552b`. Read-only review and compiler/native controls only: no WP/CBMC/provider invocation, no root worktree edit, no claim of a public false proof. Exact immutable snapshots/manifests are `/private/tmp/probata-footprint-query-review-e3d21284/manifest.json` and `/private/tmp/probata-footprint-query-review-4c860f39/manifest.json` (the latter archives the complete relevant source/library/schema/vocabulary closure).

The repaired narrow slice is GREEN for actual safe-first validation. This is an independent source review, not proof of all inherited C-model/ACSL agreement or whole ticket acceptance.

## Blocking finding in the initial slice, now excluded

The native query's `uintptr_t` arithmetic (`library/proof_semantics/dx100_bfs/model.h:348-383`) can observe equal numerical addresses for one-past of one automatic array and the start of an adjacent distinct array. The ACSL `dx_in_footprint` predicate (`logic.acsl:96`) additionally distinguishes the address's physical memory-object base. Merely allowing one-past formation and granting the noescape exemption did not bind those two interpretations.

An executable finite control uses the exact complete `model_for(...).c_text`, `swdb_dx_init`, actual tile/register allocation, constants and a valid one-element stream load from the high-address array. Querying `low + 1` prints `adjacent=1 query=1 offset=4 live=1 count=1`; every model check passes. No ghost state is manually fabricated. Source/command/model hashes and output are in `complete-native-query-boundary.c/.json` under the initial snapshot directory. The smaller exact-query extraction is also retained. This demonstrates a model-agreement boundary, not an actual WP false theorem.

The repair adds a separately named ordinary `swdb_window_query_domain_*` assertion, requiring the tile bound and either an idle writer or a valid writer slot whose base shares the certified query root's physical memory object. Normal pointer-formation obligations still constrain the actual address to its independently certified entry window, including one-past. The new domain excludes the distinct-array finite case. Same-object one-past need not be rejected: the native and abstract comparisons then retain the same object/offset interpretation. No `requires`, assumption, validity or initializedness premise is inserted.

## Checked source and call boundary

`dx_array_domains.certify_query` pins the canonical query contract and audited ghost/state/C component hashes, exact imported `int(int,const int*)` binding and read-only/noescape model. The source cannot replace it with a body, namespace/template/static/attribute alias or pointer-reference API. Unknown/other pointer calls retain their existing refusal. Query arguments contain no calls, mutation, conditionals or volatile reads. The new query-domain placement additionally requires the call to be the entire value of one ordinary int initializer/return or a standalone call; a sibling state-changing call cannot invalidate the pre-call guard. The slot upper bound makes the guard's `dx_base[writer]` read explicit.

Origins are resolved after constructing the exact noescape call handles; only stable explicit int entry windows are admitted. A failed origin/domain row stays a refusal. The new query exemption does not excuse pointer formation, rebinding, casts or unrelated calls. Original NoOp qualification can no longer hide its underlying pointer operation from the independent formation inventory. The member/query composition preserves the removed member call exemptions, vector/standard handles and checker hashes. Contextual member origins do not acquire query acceptance because this query domain requires an entry-window origin.

## Ordered source reads and fresh replay

The nested query view captures the original plain int index read once, before address formation, for the exact bodyless query with literal tile. Its whole-statement pure grammar excludes mutation/conditional ordering, opaque/default calls and volatile reads. The independent AST comparison checks the exact original read and callee declarations; original local declaration scope/bindings, unedited bytes and dependency resolution remain checked. A changed captured root is refused. Original read validity/initialization and both numerical formation/access bounds remain ordinary obligations.

Query rows retain the fresh imported policy comparison. Entry-window/import rows trigger original source/definition replay, and `check_input` reconstructs the generated assertions immediately before launch. The helper and nested stages each recheck their original/effective source, certificate and exact entry-window binding; a self-hash alone is insufficient. No preexisting opaque-origin refusal or whole-function fallback is relaxed by this review.

## Independent finite controls

Using archived exact `4c860f39` code, six compiler controls pass in 0.659s: direct one-past and a stable constant-offset alias retain the separately named query-domain VC; missing domain, rebound source pointer, sibling query and conditional query refuse. Commands/results/source hashes: `/private/tmp/probata-footprint-query-review-4c860f39/check.py` and `checks.json`. The native adjacent-root domain is false while a same-root one-past domain is true in the corresponding finite object-identity cases. These finite checks do not establish universal correctness.

Two nonblocking descriptions should remain precise in later documentation: `base_addr` expresses the physical memory-object boundary, while typed same-array provenance comes independently from the entry-window/formation checks; and direct query certification accepts pure int tile expressions, whereas the nested-read view specifically requires a literal tile. Broader source-buffer/member roots, arbitrary query/model agreement and full class acceptance are not covered here. No source change was requested during the active composed-source stand-in.
