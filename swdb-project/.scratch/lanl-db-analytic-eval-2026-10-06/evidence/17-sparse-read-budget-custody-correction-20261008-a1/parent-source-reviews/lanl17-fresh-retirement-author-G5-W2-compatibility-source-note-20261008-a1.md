# Fresh RETIRE author: adjacent change requirements

2026-10-08 ET. Source-only analysis; no source changes, imports, tests, operational
calls, SSH or project writes. Successful new DEFAULT artifacts and their actual
pins remain unknown. The failed default-a1 is historical custody only.

Sources (all under `/private/tmp`):

- `lanl17_author_fresh_sparse_retirement_parent_request_20261008_a1_r1.py`
  (A): 31,092 B; SHA `1cf61753ea21c291a91600aff41072b39c77cfd3be907ccf31d539f53a41cbf0`.
- `lanl17_author_corrected_sparse_default_parent_request_20261008_a3.py`
  (D): 13,846 B; SHA `ceab5f0c9ad06c17b820ef3f9668220bd5614d314e15b056cf86bd3b52ce5740`.
- `lanl17-fresh-sparse-capacity-query-20261008-a4.py` (Q): 5,629 B;
  SHA `6fdef6305ae33ca5ab290eda2947e055920985252830a7e909a77a20316fdd78`.
- `lanl_sparse_retire_consumed_source_guard_20261008_a1_r5.py` (G):
  180,887 B; SHA `d75baaf9dbe7192b02812cab525ccd6c50c81fd312d67cbfae7b9c8fdf955301`.
- `lanl17_detach_library_preserving_sparse_administration_20261008_a1_r2.py`
  (W): 24,114 B; SHA `e16f1afa5a427d452504e7a759a7562dcc05a98014e2b4ece1663db6755d39ec`.

## Required adjacent changes to A

1. **Selected source and publisher pins.** A:25–27/223–227/325 still bind
   G2 `4956…`/166,145 and W1 `1127…`/24,115. Replace their selected bindings
   with G/W above, including parent acceptance and every source-size check.
   A:27/449–450 also uses publisher SHA `72527…`, while D:10/91 specifies the
   same future basename `lanl17-publish-sparse-parent-originals-20261008-a3.py`
   at 16,126 B/SHA `5e667fa8ca26ece4825631e5d51feca490f3e154688a38399518bf9c237df2d9`.
   Bind the actually selected publisher; do not retain the conflicting old SHA
   or infer its current remote availability. Preserve fixed scientific PRIMARY
   `5e12…`, native/PAM pins and all numerical/scientific limits.

2. **Genuine DEFAULT lineage.** A:29–37/177–205/292–302/407–421 fix failed
   control default-a1, its decoded folder and original request/plan/review a2
   pins. The next author must consume the corrected DEFAULT request created by
   D (chosen local request path ends `a3.json`) and the actual successful
   default-a3 originals, guard attempt a3 and source-derived receipt-a3.
   Actual request/plan/review byte sizes, SHA, True identities, decoded folder,
   nine-original custody and parent acceptance must come from their genuine
   publication/collection. No old a1 success substitution or guessed pins.
   A fresh RETIRE attempt a4 uses its distinct control/output and freshly dated
   plan; W:161–162 refuses the same guard attempt. It inherits the original
   DEFAULT plan as evidence, not as a stale execution plan.

3. **Metadata-first facts.** A:271–275 currently requires regular bytes true
   and a digest for `tracked_mode_blob_source_inventory_sha256`; G:1692–1696
   instead requires false and null. Keep detached clean/tracked count/stat
   inventory/source/C/F6/RAW/alias/lease checks (A:269–290), but require the
   corrected false/null facts. Full row byte/Git/library proof is still a
   mandatory fresh pre-action G check, not a DEFAULT fact.

4. **Historical custody validation.** A currently verifies the full original
   True receipt and counters (253–267), but no new historical-custody fields.
   Require the G:1697–1713 contract: format v1, fresh DEFAULT bytes true,
   inherited files zero, exact sorted historical projection digest and complete
   ordered witness list; each vector is precisely path/bytes/SHA/stat/bool
   reference_hits and matches the original plan. Bind original review's exact
   configuration digest/backlinks and original W source in protected pins
   (G:1643–1663), plus aware chronology/300-second DEFAULT start relation
   (1664–1670). Preserve all eleven compared coverage fields (1687–1691).
   Do not duplicate the 345 vectors in review metadata; the authentic receipt
   already carries them. The parent acceptance must remain explicit and bind
   source, all original file hashes/identities and the accepted ordered subset.

5. **Fresh four-copy capacity input.** Q:21 pins both historical G2/W1 and
   selected G5/W2 copies; Q:23–28 supplies fresh lease/reserved-path/statvfs
   observations, never capacity admission. A:350–354 should require the exact
   four distinct copy routes and preserve old copies while matching selected
   G/W path/bytes/SHA/full stat to corrected DEFAULT protected pins (D:65–75,
   90–100). Maintain the 120-second freshness, original Q/T/64-MiB planning
   allowance and conditional sixteen-row minimum decision/refusal. No automatic
   new subset or claimed recovery from source estimates.

6. **Preserve and qualify DEFAULT-only prose.** Start from the corrected
   request, preserving its historical proof scope and protected-prefix lists.
   D:86 says that *this DEFAULT request* authorizes no retirement inheritance.
   A:54–55 excludes `selection_reason` from MUTABLE, so a deliberate narrow
   allowance/append is needed if the new RETIRE request qualifies that clause
   as creation-time history and states its separate accepted DEFAULT binding.
   Review facts `actual_default_only=False` and
   `successful_default_original_bindings` are the new authority input; neither
   constitutes an observed retirement. Preserve old failed receipts/reviews,
   selected-source courier and all appended protection roots.

7. **Honest source-budget statements.** Use D:87's corrected source-estimate
   fields: DEFAULT major body core 14,381,124,025 B and conditional RETIRE core
   after accepted prior reuse 14,702,545,997 B. Its old counter estimates are
   explicitly renamed obsolete/old. A:427–438 must describe original accepted
   DEFAULT counters as historical observations and the 153 eligible hashes as
   prior full-byte proof plus current full-stat continuity. Fresh two RAW
   passes, source physical/Git checks and each row's full pre-action body check
   remain debits. These numbers exclude remaining role/admin/index/proc/plan
   work and are not upper bounds, predicted duration, fit or capacity admission.
   All 16-GiB/400k/2M/3600s/256-KiB limits stay exact.

## What the existing binding does and does not supply

A:306–314 already returns G-compatible keys: pinned status/stdout, original
receipt bytes/SHA/stat/True identity/policy, original DEFAULT plan file+identity
and old review pin. All nine originals are separately protected by A:449–463.
With genuine new values and the checks above, G independently reopens those
originals, authenticates seals/review/source/projections, then seeds only the
eligible history map; W's boolean is insufficient by itself.

The decoded custody supplies **original remote stats**, not fresh current
remote history identities. Q supplies current source-copy stats only. A's local
read checks describe local copies only. G:1584–1591/1708–1717 independently
checks current eligible file identity, then rechecks at every use and stability
boundary. Do not claim that author/decoder/Q has refreshed all historical
remote stats. Fresh RAW/PRIMARY/candidate proof checks remain independent.

No presently successful DEFAULT, actual receipt seal, publication pin,
retirement authority or storage clearance is established by this note.
