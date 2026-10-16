# Initialized-u32 formal-pair preparation: independent source review

Date: 2026-10-16 ET. Reviewer: independent `prefix10_review` subagent.

**PASS for source preparation. No blocking implementation, integration or style
finding. No actual initialized-u32 proof or ticket acceptance follows.** This
review read source and immutable Git material, calculated SHA256 values and
parsed Python/embedded Python syntax using the standard library. It ran no
tests, project imports, launcher, compiler, native tools, verifier or SSH.

| Reviewed addition | SHA256 | Bytes |
|---|---|---:|
| `tests/test_dx100_initialized_register_actual.py` | `a9b5462a739040a187595b870d8f63d64021885a1ff19e77eb8ff8eb54224e25` | 4684 |
| `tests/testkit/dx100_initialized_register_outcomes.py` | `95f2841e63a5f4aee1ad28bb0fa7026ad9e0f0273cfd4033c366d86c9162a9a7` | 3451 |
| this directory's `run_initialized_register_acceptance.sh` | `982cf10fa9cdbd54e6bd3f7e55f90470778e1816c47bad99ffcef80a1f100895` | 6042 |

1. **The original partial source and frame remain intact.** The actual test
   calls the existing fixture with `actual=True` and exact expected711/1107;
   only the result postcondition changes between halves. Existing fixture,
   model/source policy, scripted source test, native producer and ordinary
   reader are unchanged from `c978393b119a3614229a37f0f2c8ca2a097c750b`.
   The test requires the distinct partial subject/method, exact semantics hash,
   empty added unit premises, conditional-normal-return policy and owned scope
   statement. It checks all three source call kinds, the original four complete
   assigns locations including `[0..1]`, both initialized7/11 calls, prewrite
   capacity requires and three partial termination clauses. It neither adopts
   current0.2 nor proves hardware/body correspondence or liveness.
2. **Actual execution and complete native health cannot be replaced by the
   named stand-ins.** `actual=True` uses the explicitly supplied actual lineup
   and inherited real-tool environment; the test requires no stand-in marker,
   actual verifier launch, source setup hash and hashes of all recorded reports.
   Mandatory RTE/initializedness/no-init-filter/smoke flags, cache-none,
   one-worker, 30-second and three-solver settings remain checked. No smoke
   timeout override is added; the Frama33 default still requires independent
   runtime-source binding at admission.
3. **The outcome helper preserves ordinary and smoke distinctions.** Every
   record goal has one unique native counterpart; duplicate, missing or unread
   goals refuse. Ordinary passes require an actual native `valid` observation;
   ordinary failed/error/invalid/computing outcomes and unattempted-only duties
   refuse. Every smoke must be passed with nonempty healthy raw nonvalid results
   using the same set as `proof_setup.read_wp_reports`: unknown, timeout,
   stepout or invalid. These smoke observations are operational health, not a
   direct Valid result or satisfiability proof. Positive711 requires proven and
   no open ordinary duty. Wrong1107 requires not_proven/unknown-or-timeout and
   exactly one open ensures; it grants no refutation. Complete property/DAG,
   Extern and exact failed-target source ownership remain with the normal
   source-pinned reader and independent final cold audit, as the helper states.
4. **The formal launcher rejects missing tests and skips.** It requires a full
   frozen SHA, clean checkout, source-disjoint fresh output, explicit interpreter,
   actual lineup and counted-verifier marker. Positive/negative/pair profiles
   select exact node IDs. JUnit census requires exact names/class/count, one
   suite, no errors/failures/skips anywhere and no source bytecode cache; final
   success additionally requires pytest exit0. A missing/renamed test, plugin
   selection anomaly, ordinary collection failure or skip-only run cannot pass
   this census. Pytest auto-discovery of the new actual test follows existing
   repository patterns; its default opt-in skip is not formal acceptance.
5. **Root admission and result closure are still required.** These three files
   are reviewed additions to baselinec978, not an admitted immutable producer.
   Freeze their exact reviewed bytes and recheck full source/runtime/input
   closure before dispatch. The launcher records identities but does not itself
   establish physical interpreter/library/solver admission, actual held lane
   and lock ownership, process-tree resource enforcement or output settlement;
   root owns those controls. It explicitly requests a one-worker8GiB/1200s
   guarded tree. Current-source actual positive/wrong records, all native
   tasks/hypotheses/CSV/Extern/source/runtime closure, resource settlement and
   independent cold decision remain pending. Ticket28's whole-interface,
   overlap/history/ownership/pair/visibility/version acceptance boxes stay open.

Relevant unchanged context SHA256 values: initialized model
`a568c08f6e8d928ecb46212b7120b29740d719c65ae7ae818b540bcf6790961f`,
initialized source policy
`c023a4a6298fab7a34f4213f888b6c0fb4fe5c405e5a53741942e3e2accb81cb`,
native `proof_report.ml`
`8b84bec6a12669d877205ec60d46d149f41fa921d08b6640161b4896b9c4df16`,
and ordinary `proof_setup.py`
`069dbc55b6ca8b12ea8b524027e2ca2b0922eb9e7be449c6f5725dbddbfe733f`.
