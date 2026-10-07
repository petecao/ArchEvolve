# Prospective parent full-record-index writer — 2026-10-07 ET

**Preparation only. The writer, its main, the isolated tests and all fixtures have NOT RUN.** No actual request, catalog, index, inventory, future R, account UID or output path is assigned. Scientific C/F6 and all approved controls remain unchanged. Only source reading, syntax/AST inspection and preparation metadata hashing occurred.

The preceding supplier audit is `/private/tmp/lanl17-record-index-supplier-source-audit-20261007.md` (SHA `acff77a27f43920e635d367c8f9c06243b855ab45013f4c746bb8409580f7237`). Original28d emits per-campaign public validation argv/exit/stdout/stderr, but not the consumer's full three-field record index. This distinct writer supplies **parent-generated metadata**, with inherited prior validation; it must never be described as an original28d output or an independent full-validation run.

## Prepared sources and existing contracts

- Writer `/private/tmp/lanl17_write_parent_full_record_index_20261007.py`, SHA `7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b`.
- Isolated test **source** `/private/tmp/lanl17_parent_full_record_index_isolated_test_source_20261007.py`; its exact SHA is in the accompanying preparation packet. It pins the writer above, lifts only closed named original Assign/function/class/loader AST nodes, and contains eight synthetic cases. No `ast.literal_eval` is used for multiplied size constants. No full writer, Store, SWDB, collector or auditor module is imported.
- Consumer producer32bead, selected auditor6a91, collectorb08 and helper28d are original pinned sources. No consumer/output format is altered. Original spec writer339ea and assemblerde669 stay exact.
- Scientific C is `f893fed400347ed23d92e917d8bde21b75e5375d`; F6 is `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3` over exactly185 C Python module bytes.

## Future explicit request contract

A future original unsealed JSON request must have **exactly** `format`, `context`, `originals`, `catalog_inventory`, `summary_binding`, `limits`, `parent_review`, `output_directory`. Format is `swdb.lanl17-parent-record-index-request.v1`. Duplicate/nonfinite JSON values refuse. The external full request SHA, parent review digest and request-author source SHA are mandatory CLI parameters. This verifies declared parent review and bytes, not human identity or independently observed quiescence.

`context` has exactly:

- `source_C`, `estimator_sha256` fixed above; `final_R: {commit, tree}` with explicit full actual Git hashes.
- `account: {host, platform, uid, user}`: actual execution must be Linux `mbit10`, real/effective UID equal the explicitly reviewed UID, and `pwd` account `yanruj`. No UID or host is inferred from a path.
- `campaign` exactly one of the four approved `extensa-gem5-bfs-20261006-p1..p4` names.
- `source_path`, `project`, `records_directory`, `manifest_identity_sha256`: source and project must resolve to exact original M2.source and M2.source/swdb-project. Records resolve to original M2.raw/campaign-runs/extensa/campaign/records. Symlink components refuse. Existing original M2.raw must be owned and under `/data/yanruj`.

`originals` has exactly `manifest_M2`, `helper_source`, `auditor_source`, `collector_source`, `validation_argv`, `validation_exit`, `validation_stdout`, `validation_stderr`. All file descriptors have exact `{path, bytes, sha256}`. The original M2 descriptor additionally has its original `identity_sha256` and explicit `canonical_ensure_ascii:true`. Selected source bytes must match original28d/6a91/b08. Only M2 gains seal verification; original validation files stay unsealed.

Validation paths must be original `M2.raw/validate-campaign.{argv.json,exit-code.txt,stdout,stderr}`. The exact original argv must be `python3 -m swdb validate --records <exact campaign records directory>`. Exit must be0, stdout exactly the public C success line, stderr empty, and its validated record count must match the complete approved inventory. The final base-export validation is not substituted. Missing files, nonzero, timeouts or changed bytes refuse rather than invent success.

`catalog_inventory` is an explicit sorted list, one row per eligible public `.yaml`/`.yml` body: exactly `{path, bytes, sha256, stat}`. `path` is the exact relative public catalog path. `stat` is exactly `{dev, ino, mode, uid, size, mtime_ns, ctime_ns}`, from the parent-approved real unchanged snapshot. Every eligible body is included; no selected-closure-only index. Hidden paths follow C discovery exclusion; symlink redirects refuse. Duplicate paths/IDs/keys, omitted/extra files and changed contents/inodes refuse.

`summary_binding` is explicit. Present summary: `{state:'present', path:<relative file>, id:<campaign.summary>, record_sha256:<original public digest>}`. It must be the exact indexed campaign_summary, mode extensa/source R/campaign match. Absent summary: `{state:'absent', id:<campaign.summary>, parent_observed_absence:true}`, and that ID must actually be absent from the full index. Neither branch declares a normal terminal campaign or substantive rewrite. There is no default summary or acceptance state.

`limits` has exactly `catalog_record_count`, `catalog_total_bytes` (both exact actual inventory values), `max_catalog_file_bytes` =134217728, `max_catalog_total_bytes` =2147483648, `max_output_metadata_bytes` =8388608, `metadata_deadline_seconds` (explicit60–3600). Maximum record count16384. The new128MiB/body and2GiB **unique inventory** source-read bounds accommodate the observed70,599,862-byte original record. They change no selected32/8MiB input limit, scientific900s collector deadline or approved control. Construction and final custody passes reread unchanged originals;2GiB is not claimed as cumulative I/O. Index, request and custody each remain within8MiB. Finite Linux metadata timer/checks and bounded local Git waits apply only to this writer; parent may add an external administrative timeout after review.

`parent_review` has exactly `basis`, `writer_sha256`, `reviewed_request_payload_sha256`, `actual_inputs_parent_approved`, `fixtures_or_replays_allowed`, `validated_snapshot`. Basis is `explicit_parent_review_of_real_quiescent_catalog_and_original_prior_full_validation`; explicit approved actual inputs=true, fixture/replay allowance=false; writer SHA is original prepared writer; payload digest is canonical-true digest of request excluding parent_review.

`validated_snapshot` has exactly `campaign`, `records_directory`, `catalog_inventory_sha256`, `validation_files_sha256`, `prior_validation_full_catalogue`, `catalog_unchanged_since_original_validation`, `all_campaign_processes_stopped`, `exclusive_snapshot_ownership_confirmed`, `observed_utc`. The four boolean observations must be explicitly true and honestly captured by the parent; they have no defaults. The inventory digest and map of four original validation file SHAs must match the request; UTC observation is explicit. Original stdout alone cannot prove snapshot continuity. If parent cannot establish it, construction remains pending.

The whole parent_review digest is externally pinned with `--parent-review-sha256`. The exact original request-author source is separately pinned; this writer does not silently appoint another control as that supplier.

## Outputs, custody and unchanged semantics

Future CLI (placeholders are not actual pins):

```text
python3 <reviewed-writer> --request <actual-original-request> --request-sha256 <actual-request-SHA> --request-author-source <actual-original-author-source> --request-author-source-sha256 <actual-author-SHA> --parent-review-sha256 <actual-reviewed-subdocument-digest> --output-directory <exact-reviewed-fresh-external-directory>
```

The parent-approved destination must be fresh, owned, nonsymlink, below `/data/yanruj` or `/data1/yanruj` and outside M2.source, entire M2.raw and all four campaign roots. The writer publishes `record-index.json` and separate `writer-custody.json`; it never edits originals/source/store. A failure after partial publication preserves that folder and returns refusal; it is not admitted success and must not be consumed.

The bare unsealed index is exactly `id -> {kind, sha256, record_sha256}`. `sha256` hashes the same returned bytes parsed; `record_sha256` is the full public record digest, sorted compact JSON with ensure_ascii=true/allow_nan=false, original timestamp-as-string and duplicate-key refusal. Unknown/nonfinite/cyclic/nonstring-key bodies refuse; no values or identities are normalized to fake supported facts.

Separate custody format is `swdb.lanl17-parent-record-index-writer-custody.v1`, sealed whole-object ensure_ascii=true. It pins all originals, reviewed request/source/R/M2/inventory/summary and index file/semantic hashes, plus explicit inherited parent snapshot facts. It declares actual_campaign_admission=false, index_is_original_28d_output=false, index_sealed=false, no SWDB/scientific actions and unchanged existing controls/bounds.

Before publication and before success, catalog content/stats are rechecked and re-inventoried, all originals are reread, exact clean R/C Git/module equality and live185-module F6 including ignored extra `.py` files are rechecked, and own source SHA is checked last. No full catalog schema/rule/reference validation or live process/lease observation is claimed by those byte guards.

## Isolated test source scope

Eight future synthetic cases cover independent whole-record digest/file SHA/date/Unicode policy, duplicate IDs, top/nested duplicate YAML keys, same-length changed returned bytes, inode swap during an open read, added/deleted inventory entries, source-change refusal before publication, and final source-change refusal before success after preserved partial publication. Only new synthetic sentinel files may change. Original approved controls/data never change. This packet makes **no RED/GREEN or runtime success claim**; execution requires separate parent source/hash review and authorization.
