# 63 — Experimental enabling contracts and the shared-contracts rule

Created: 2026-10-13 23:15 ET
Updated: 2026-10-14 11:00 ET (resolved, Answer); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 18, 19
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof routes" (a new experimental enabling contract for any input; route 1 for its results); "ArchEvolve mode" (shared contracts only; one rewrite proposal per rewrite; promotion); "Modules", table "Loop, modes and guards" (implementation records); "Verifier lineup and order" (skip reasons); "Testing Decisions", seams 1, 3 and 4; O7, O10); decisions: [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) items 5, 6, 8 and Later changes; [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) item 3; [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) items 1, 5; [ADR 0007](../../../docs/adr/0007-typed-library.md) (ArchEvolve mode accepts only shared certified entries)
**Time estimate:** about 2 days

**What to build:** Any input code, even when no catalog entry fits. In Extensa mode the rewriting role
may then write a new **experimental enabling contract** beside its patch (17 item 5): an experimental
library entry that only reshapes, usable only in Extensa mode until promotion. A certified result of
it is a derived implementation (19), proven by route 1 against the kernel's unit postcondition like
any other; no relational template is needed, since route 2 is not built (24 item 3). ArchEvolve mode
keeps the shared-contracts rule: it refuses any contract that is not shared, at every rewrite of a
chain, and a derived implementation enters the main database only through promotion (17 item 8).
Tested through `swdb campaign --fixture` and ArchEvolve mode's proposal path.

## Acceptance

- [x] **The rewriting role writes one.** In a fixture campaign, a scripted rewrite response carries a
  new enabling contract and a patch that applies it. The loop adds the contract to the library, where
  it reads as experimental (no review) with entry status draft. `swdb validate` and `swdb build`
  accept it.
- [x] **Enabling only.** Negative controls, each refused before certification: a contract whose
  strategy effects include an offload; a contract that fails library validation.
- [x] **Extensa mode only.** A campaign whose allowed library tiers exclude experimental entries
  refuses the new contract (negative control); one that allows them accepts it.
- [x] **Certified result, derived implementation.** The result is certified alone against its
  predecessor's snapshot, in the native family like any enabling rewrite. Once certified, it is a
  derived implementation whose contract lineage names the experimental contract (ID, version, content
  hash). Control: a result that fails certification makes no derived implementation.
- [x] **Built on, then proven by route 1.** A later iteration starts from that derived implementation
  and applies an offloading contract that names no required enabling contracts (see the gap in Notes).
  `swdb prove` (scripted adapter) proves the derived implementation by route 1 against the kernel's
  unit postcondition; the record pins the experimental contract's hash. Nothing requires a contract
  proof, minimum bounds or template of the experimental contract: skip reason "no contract proof"
  skips only the contract seeds and the bounded rung, and route-1 WP still runs (O7).
- [x] **ArchEvolve mode refuses it.** An ArchEvolve-mode rewrite proposal that names the experimental
  contract is refused at submit. Control: once a promotion review makes it shared and it is certified,
  the same proposal is accepted.
- [x] **Every rewrite of a chain.** In ArchEvolve mode each rewrite is one rewrite proposal. Fixture
  chain: the first proposal names a shared enabling contract and is accepted; the second names a
  non-shared contract and is refused. A proposal whose target is a derived implementation with a
  non-shared contract in its lineage is refused too.
- [x] **Main database only through promotion.** After an ArchEvolve-mode chain, its derived
  implementations stay in the research database. The handoff and every team-store write name only the
  final candidate artifact; none carries a derived implementation.
- [x] Fixture records carry `contract_fixture` evidence. Tests use the scripted adapter and a scripted
  provider; full-suite runs on the Mac use at most 2 test workers.

## Notes

- **Not in this ticket:**
  - 19 — Derived implementations: the record, contract lineage, per-rewrite links and the iteration
    start this ticket reuses.
  - 52 — Split the bundled read offload: the check of an offload-only contract's required enabling
    contracts against the lineage, and the pattern-class check on each derived implementation (17
    item 5). Both apply to experimental enabling contracts unchanged.
  - 62 — Route choice and predecessor proofs in the campaign: when, inside a campaign, the derived
    implementation's route-1 proof runs.
  - 53 — Chained vs direct vs bundled; A5 exit: route 1 on derived implementations.
  - 31 — Five-gate drafting and the new bfs_read_offload version: any formal half the new contract
    carries passes the five gates before promotion.
  - 18 — ArchEvolve mode level and handoff block; 12 — Proposal and promotion fields: the handoff and
    the promotion review this ticket relies on.
  - 55 — End-to-end fixture campaign with real verifiers waits on this ticket.
  - Promoting a derived implementation into the main database: no path exists (ADR 0014), and none is
    built here.
- **Gap for Yan-Ru (not decided in the map):** an offload-only contract names its required enabling
  contracts by ID, and enabling contracts never list what they enable (17 item 5). So no existing
  offload-only contract can require a brand-new experimental enabling contract, and 52's lineage check
  would block that chain. The new contract's result can then feed only an offloading contract that
  names no required enabling contracts, or a new offload-only contract that names it, which nothing
  lets the rewriting role write today. The fixture uses the first; this ticket decides nothing.
- Assumption (not decided in the map): "no fitting catalog entry" is not checked by code. Whether a
  catalog entry fits the offload the rewriting role aims at is a judgment; the rewrite workspace lists
  the catalog's enabling contracts, and Yan-Ru judges at promotion.
- Assumption (not decided in the map): the new contract travels in the rewrite response beside the
  patch, in the smallest shape that works. The call is a rewriting call, in the rewriting total. The
  campaign's existing synthesis calls (D7) stay as they are; the map gives this job to the rewriting
  role.
- Assumption (not decided in the map): this path accepts only a contract that offloads nothing (19's
  reading of "enabling"). Other ways Extensa mode makes experimental entries are unchanged.
- Assumption (not decided in the map): the new contract gets no contract proof in this effort. 17 item
  5's template proof fell with route 2 (24 item 3), and an enabling contract states no unit
  postcondition and records why (design O10, default until Yan-Ru rules: 24 item 2's drafting rule
  governs kernel contracts; route 1 proves an enabling contract's results). So, per O7, its results skip contract seeds and the bounded rung,
  and route-1 WP runs.
- Assumption (not decided in the map): a new contract is accepted only when the campaign's allowed
  library tiers include experimental entries; the campaign file already lists them.
- Assumption (not decided in the map): an ArchEvolve-mode proposal whose target is a derived
  implementation with a non-shared contract in its lineage is refused, or the shared-contracts rule
  could be bypassed through the predecessor.
- Assumption (not decided in the map): "only through promotion" is tested as "no ArchEvolve-mode output
  carries a derived implementation". SWDB contributes to the main database only through that
  database's own ingest inputs (ADR 0014), and no producer exists yet.
- ArchEvolve mode already refuses, at submit, library entries that are not shared and certified (ADR
  0007). This ticket confirms that covers enabling contracts and every rewrite of a chain, and extends
  it only where a test fails.
- Generality: per kernel and contract; nothing BFS-specific. Contract fixtures only; no held-out kernel
  (BC, PR, SSSP).

## Answer

2026-10-14 11:00 ET. Built test-first on branch `probata-poc/t63`. Every box is met with contract fixtures,
the scripted verifier adapter and a scripted provider; two caveats are listed under the boxes they touch. Interface:
[`docs/reference/format-v0.4-derived.md`](../../../docs/reference/format-v0.4-derived.md) (section "Experimental
enabling contracts and the shared-contracts rule").

**What exists now**

- **`swdb/experimental_contracts.py`**: `admit` (Extensa mode: tier, shape, certified alone, new ID, enabling,
  library validation; writes `library/rewrite_contracts/<id>.yaml` with `provenance.origin` =
  `{kind: extensa_rewriting, campaign, iteration}`), `shared_problem`, `lineage_problem`, `target_gate`.
- **Campaign loop** (`swdb/campaign.py`): campaign file `library.new_enabling_contracts: true` adds
  `new_contract` (string or null, required) to the rewrite role's schema and `NEW_CONTRACT.json` to the
  workspace; the loop admits it once per answer (iteration row `new_contract`: added, or refused with the
  reason, which rejects every class's candidate artifact `provider_output_invalid` before certification). An
  added contract joins the campaign's contracts (workspace `contracts/`, tier check; exempt from the
  site-finder applied check, which cannot name it).
- **`swdb.derived`**: `enabling_problem(entry, stores)` (why an entry, in a library or not, is not enabling);
  `root_implementation(store, id)`.
- **ArchEvolve mode**: `swdb submit` calls `target_gate` after `proposal_gate` (a derived target whose lineage
  holds a contract that is not shared and certified, at the lineage's content hash, is refused);
  `archevolve_proof.certified_contracts` refuses a candidate artifact certified under such a contract or built
  on such a lineage (both proof steps); the `evaluation_result` handoff names the chain's root implementation in
  `software_hardware_pair.implementation`.
- `tests/testkit/library_promotion.py`: execution-certification test double plus the real `swdb promote`.

**Tests:** `tests/test_experimental_enabling_contracts.py`, 9 tests (writes one; offload / invalid / bundled
refused; tiers; certified result is a derived implementation, built on with the read offload, route-1 WP with
gate skips; failed certification makes none; ArchEvolve refusal and promotion control; chain of proposals;
proof path refusal and control; handoff names no derived implementation). Stale tests fixed:
`tests/test_archevolve_proof_path.py` seed now promotes its two contracts (ticket 18's tests certified
proposals under an unreviewed contract, which the proof path now refuses). Runs (one worker, no xdist,
`-m "not whole_store"`, under `/tmp/claude/probata-runs/t63/`, no verifier job): group A
`test_experimental_enabling_contracts`, `test_format_doc`, `test_archevolve_proof_path`, `test_library_submit`,
`test_proposals`, `test_provider_role_schemas`, `test_bfs_package_handoff`, `test_functional_evaluation`,
`test_typed_library`: 164 passed, 1 skipped, 11.8 min (`ra.jsonl`, sha256
`d0c5d162257d0621823594157a0b0f3b79a77458bb11865e56f4c00b89c9af29`). Group B `test_derived_implementations`, `test_bounded_gate_campaign`, `test_wp_phase_campaign`,
`test_campaign_certification_links`, `test_extensa_campaign`, `test_iteration_ladder_campaign`: 57 passed, 35.4 min
(`rb.jsonl`, sha256 `890be36ecec04b75cd2fb70d42c2209cd676e83f557fd9a3417ff8aa236ef614`).

**Caveats**

- Box "Built on, then proven by route 1": the WP phase's record (`swdb prove`, scripted) is route-1 WP of the
  candidate proof unit (stages `["wp"]`, no seeds, contract pin = the experimental contract's hash); its
  `route` field stays empty, since tickets 61/62 fill it (so `swdb_rewrite_links.proof_route` reads `none yet`).
- Box "Main database only through promotion": the native evaluator refuses a candidate artifact whose
  implementation is a derived implementation ("native evaluator requires an application-backed candidate", at
  `source_resolution`), so an ArchEvolve chain's final candidate artifact cannot be measured yet. The test renders
  the handoff of that failed evaluation record. In ArchEvolve mode the records store that certifies is the one
  store, so "team-store writes" is tested as: derived implementations stay in that store and the handoff names
  none.
- The promotion control needs an execution certification (review validation requires `evidence_kind:
  execution`), so it uses a synthetic execution-envelope test double (as `test_library_submit` does) and the
  real `swdb promote`. Every campaign and proposal certification is `contract_fixture`.

**Assumptions** (beyond the ticket's own):

- Assumption: `new_contract` is offered only in campaigns whose file sets `library.new_enabling_contracts`
  (as `start` only with `derived_starts`), so other campaigns' role schema is unchanged; such a campaign whose
  tiers exclude experimental still runs and refuses each new contract.
- Assumption: the loop sets `provenance.origin` itself (campaign, iteration) and keeps the rest of the role's
  provenance; it writes into the campaign's `--library` root, as synthesis (D7) does.
- Assumption: "certified alone" is enforced: an answer carrying a new contract must name exactly that contract.
- Assumption: re-sending an existing ID is refused (name the contract instead); an identical resend in the same
  iteration (resume) is reused.
- Assumption: library validation of the new entry is the library's own checks against the team store, filtered
  to that entry's file (the whole library has unrelated errors against a campaign store, ticket 19).
- Assumption: ArchEvolve-mode `swdb certify` still certifies a candidate under a non-shared contract and its
  hook still records the derived implementation (certification precedes review); the shared-contracts rule
  then bites at the next proposal (`target_gate`) and at the proof path.
- Assumption: the handoff names the chain's root implementation (origin `derived_from` followed back), since
  the main database knows no derived implementation before promotion.

**Side findings**

- Native evaluation of a candidate artifact built on a derived implementation is not supported (above); 55 and
  any ArchEvolve chain end-to-end need it.
- A new contract's ID is never offered to the site finder (query mode): the loop exempts it from the applied
  check; 52's pattern-class check is the guard there.

