# Derived implementations and rewrite links (format 0.4 addition)

Created: 2026-10-14 (Eastern Time), Probata proof of concept ticket 19. Updated: 2026-10-14 ET, ticket 18
(ArchEvolve mode records one at `swdb certify`); 2026-10-14 ET, ticket 63 (experimental enabling contracts,
the shared-contracts rule; section at the end).
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/19-derived-implementations.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Proof routes", "Loop, modes and guards"), map
decision 17 items 5-8, 24 item 3, 26 item 2; ADR 0005 (the root baseline stays the comparator) and
ADR 0016 (records never change; what still holds is computed on read). Code: `swdb/derived.py`.

**In one line:** a certified enabling rewrite's result becomes an implementation record with
`origin.kind: derived`; it carries its contract lineage and its rewrite links, and from then on
proposals, the site finder and Extensa iterations use it like any implementation.

## What later tickets build on

| Piece | Where | Who widens it |
|---|---|---|
| Implementation fields | `contract_lineage`, `rewrite_links` (below) | 52 checks a lineage against an offload-only contract's required list and checks pattern classes |
| Enabling test | `swdb.derived.is_enabling`, `enabling_problem` (no strategy effect of kind `offload`) | 63 added experimental enabling contracts (below) |
| Iteration start | campaign file `derived_starts`; rewrite role `start` | 62 chooses routes; real targets (56, 57) still build only from their base snapshot |
| Links on read | `swdb.derived.link_rows`; tables in [database.md](database.md#derived-implementation-tables) | 10 (dependent candidate artifacts drop to certified), 62 (route per rewrite) |

## When one is written

A candidate artifact whose every contract is an enabling contract (no strategy effect of kind
`offload`; strategy records the store lacks make a contract not enabling) and that passes
certification is recorded, in the same store, as derived implementation `<candidate>.derived`
with its own source snapshot `<candidate>.derived.source` (the candidate artifact's tree). No new
command: the Extensa campaign loop writes it right after certification. A rejected or uncertified
result, or one with an offloading contract, writes none. The campaign summary entry names it in
`derived_implementation` (or says why not in `derived_note`).

**ArchEvolve mode** (ticket 18, 2026-10-14 ET): `swdb certify <contract> --candidate <candidate>` on a rewrite
proposal's candidate artifact (not an Extensa campaign's) records it the same way, in the store that certified
it (the research database; nothing reaches the main database before promotion), one contract per proposal,
with the candidate artifact's source snapshot as the predecessor snapshot. Its output adds
`derived_implementation`, or `derived_note` with why none (an offloading contract, a failed certification, a
refused record). The certification stands either way (`swdb.archevolve_proof.record_derived`).

## Implementation fields

- `origin.kind: derived`, `origin.derived_from`: the predecessor (the baseline implementation or a
  derived implementation).
- `code`: one `root: records` file, `implementations/<id>/<path>`, the kernel file of the result
  (byte copy, `sha256`). `swdb source-snapshot` refuses a records-root implementation; its snapshot
  is the one written with it.
- `loops`, `access_patterns`: the predecessor's (without code lines or agent claims) until the
  profiling agent annotates the derived implementation.
- `applies`: the predecessor's entries, then each contract's strategies in order. A target the
  annotation must name is `unresolved`, and so is a declared parameter with no knob of the same name;
  `swdb validate` accepts `unresolved` only on a derived implementation.
- `application`, `source_baseline`, `comparison_baseline`, `evaluator`, `build`, `run`: the
  predecessor's, so `source_baseline` stays the root baseline. `verification.status: unchecked`.
- `contract_lineage`: the rewrite contracts applied since the baseline implementation, in order,
  each `{contract, version, content_sha256}`. `version` is null while rewrite contracts carry none
  (ticket 20 adds versions); the content hash names the exact entry.
- `rewrite_links`: this rewrite's link, one per contract in contract order, each with `contract`,
  `contract_sha256`, `predecessor_snapshot` (`id`, `sha256`), `result` (`candidate`, `snapshot`,
  `sha256`) and `certification` (the record ticket 02 links for that contract).

`swdb validate` refuses: a lineage that is not the predecessor's lineage followed by this rewrite's
contracts (a skipped, added or reordered rewrite); with a library, a lineage contract the library
does not hold; a link whose certification covers another contract, certifies another candidate
artifact, is not certified, or whose candidate artifact was built on a snapshot other than the
link's predecessor snapshot; a predecessor snapshot that is not the predecessor's; lineage or links
on a non-derived implementation.

## Candidate artifacts built on a derived implementation

A candidate artifact built on a derived implementation names it in `predecessor`
(`implementation`, and the `snapshot` `id` and `sha256` it was built on); its `source_snapshot` is
that snapshot. It is certified against that snapshot, one contract per run, and (fixture cell
`root_baseline_correctness`, `command.start`) also runs the kernel's correctness check against the
root baseline. Its speed is compared against the campaign's baseline roles, never its predecessor.

## Links on read (`swdb build`)

Each link of a derived implementation, and each certified certification of a candidate artifact
built on one, is a row of `swdb_rewrite_links`. A link matches while its predecessor snapshot hash,
its contract's content hash (when the library is known) and its result hash are current and every
earlier link of its chain matches; otherwise `reason` says which changed. Changing a predecessor's
snapshot reopens that rewrite and every later one; no record is rewritten. The proof route is the
`route` of a proof record whose subject is the result candidate artifact and whose contract pin is
the link's contract (the first by ID that names one), else `none yet`.

## Extensa campaigns

- Campaign file `derived_starts`: the derived implementations an iteration may start from (an ID may
  name one this campaign records in an earlier iteration).
- With `derived_starts`, the rewrite role answers `start` (one of them, or null for the base source)
  and the workspace holds `STARTS.json` and each usable start's kernel file under `starts/<id>/`.
  A start that is not listed, not a derived implementation, of another kernel, or not certified (a
  link's certification missing, failed or no longer counting) rejects the class's candidate artifact
  (`provider_output_invalid`); a patch that does not apply to the start's snapshot rejects it
  (`build_failed`).
- Contract-fixture file `base_snapshot`: the team-store source snapshot fixture candidate artifacts
  are built from. With it, a fixture candidate artifact is a real tree (the start's tree with the
  patch applied). Without it, fixture campaigns behave as before and record no derived
  implementation.
- Real targets (native, gem5) still build every candidate artifact from their scalar-only snapshot
  and refuse a `start`; they record a derived implementation for a certified enabling result, with
  that snapshot as the predecessor snapshot.

## Experimental enabling contracts and the shared-contracts rule (ticket 63)

Code: `swdb/experimental_contracts.py`. Design: map spec "Proof routes" and "ArchEvolve mode"; decision 17
items 5, 6, 8; ADR 0007.

**Extensa mode: the rewriting role may write one.**

- Campaign file `library` field `new_enabling_contracts` (true) turns it on. The rewrite role then answers
  `new_contract` (the YAML text of one rewrite-contract entry, or null), and the workspace holds
  `NEW_CONTRACT.json` (when and how to write one). Other campaigns' role schema is unchanged.
- The loop adds it to the campaign's library (`--library`), file `rewrite_contracts/<id without contract.>.yaml`,
  with `provenance.origin` set to `{kind: extensa_rewriting, campaign, iteration}`. It reads as tier
  experimental (no review), entry status draft. From then on it is one of the campaign's contracts.
- Refused before certification (the class's candidate artifact is rejected `provider_output_invalid`, the
  library unchanged), in this order: the campaign's `allowed_tiers` lack `experimental`; not a
  rewrite-contract mapping; the patch does not apply it alone (each rewrite is certified alone); its ID is
  already in the library; a strategy effect offloads, or the team store lacks a strategy record; library
  validation of that entry fails.
- The iteration row names the outcome: `new_contract: {contract, state: added, content_sha256, path}` or
  `{state: refused, reason}`.
- A certified result is a derived implementation like any enabling rewrite; its lineage names the new
  contract's ID and content hash. The contract has no contract proof: the bounded gate skips both rungs
  (`no_contract_proof`), the WP phase runs route-1 WP without contract seeds.

**ArchEvolve mode: shared contracts only, at every rewrite of a chain.**

- `swdb submit`: a library section naming a contract that is not shared and certified is refused (ADR 0007,
  `swdb.library.proposal_gate`, unchanged). New: a proposal whose `implementation` is a derived
  implementation with any lineage contract that is not shared and certified (with the lineage's content
  hash) is refused too (`target_gate`).
- `swdb prove --proof-path`: `archevolve_proof.certified_contracts` refuses a candidate artifact certified
  under a contract that is not shared and certified, or built on such a lineage.
- The `evaluation_result` handoff's `software_hardware_pair.implementation` names the implementation the
  rewrite chain started from (`swdb.derived.root_implementation`), never a derived implementation; derived
  implementations stay in the store that certified them until promotion (not built).

