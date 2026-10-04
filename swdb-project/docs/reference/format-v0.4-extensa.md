# Extensa-mode record fields (format 0.4 addition)

Created: 2026-10-03 (Eastern Time)
Updated: 2026-10-03 (Eastern Time)

Extensa mode (ADR 0009, ADR 0010; decisions in
`.scratch/typed-library-dx100-bfs-2026-10-03/extensa-design-2026-10-03.md`) adds optional
envelope fields and a candidate-artifact review. Everything here is additive: records
without these fields keep their ArchEvolve-mode meaning and revalidate unchanged.

## Mode tags (ticket 48)

Every record kind accepts two optional envelope fields:

- `mode`: the only value is `extensa`. Absent means ArchEvolve mode.
- `campaign`: the Extensa campaign ID, matching
  `extensa-(native|gem5)-bfs-YYYYMMDD-<letter><n>`. It is required when `mode` is present
  and forbidden otherwise.

The writer sets both only when a record is created. Rewriting an existing record to add,
remove or change either field is refused, and nothing is written. Tags are never
backfilled.

A candidate artifact never stores its certification level. `swdb candidate-level
CANDIDATE` derives it from certification records: `certified` (a certified record for
the candidate), `rejected` (any failed certification) or `uncertified` (none, for
example an edit that used no rewrite contract).

## Team boundary

`swdb compare-evaluations`, `swdb handoff-message` and `swdb bfs-coverage` refuse an
input whose record closure (every record reachable through ID references) holds an
Extensa-tagged record, naming that record. The exceptions:

- a tagged candidate artifact, or its tagged proposal or source snapshot, whose
  candidate is promoted by a candidate review, once a non-rejected comparison under the
  review's derived team protocol exists;
- the re-evaluation comparison itself (`compare-evaluations` under the derived
  protocol);
- a campaign's own comparisons, under an Extensa-tagged protocol, which accept only
  records of the same campaign.

Tagged evaluations, comparisons and protocols never enter team results. Coverage scans
skip refused records instead of failing.

## Candidate reviews

`swdb promote CANDIDATE --protocol TEAM_PROTOCOL --workload-class CLASS --output DIR`
records Yan-Ru's review of an Extensa candidate artifact. The review record has:

- `target_kind`: `candidate` (absent means `library_entry`, the ticket 15 review);
- `target`: the candidate ID and its artifact sha256;
- `evidence`: the candidate's certification records or its campaign summary (no
  `x-ref` restriction for candidate reviews; library reviews keep certification only);
- `origin`: `mode: extensa` and the `campaign`;
- `reevaluation`: the named current `team_protocol`, the derived `protocol` (frozen
  from the team protocol's settings with only the `workloads` of `workload_class`, the
  workload family), and the written evaluation `requests` (`id` and file `sha256`).
  Each request cites the campaign, candidate, review and team protocol under `origin`.

A failed (rejected) candidate artifact is never promoted.
