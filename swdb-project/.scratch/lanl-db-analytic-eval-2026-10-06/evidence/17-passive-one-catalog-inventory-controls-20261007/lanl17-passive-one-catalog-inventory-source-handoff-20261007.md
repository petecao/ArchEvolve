# Passive ONE-catalog inventory supplier: source-only handoff

Prepared 2026-10-07 ET. Target source, main, imports and test bodies **NOT RUN**. No actual inventory, request, summary descriptor, output root or scientific input was constructed. Ticket14 and its unchanged approved nine-export reader remain independent.

The selected controls lack this supplier. Original7a `approved_inventory` (255–275) consumes the complete sorted list of exact `{path,bytes,sha256,stat}` rows; its `scan_catalog` (234–252) produces stat7 only, and custody line566 repeats the supplied list. R1 request author (447–453, 561, 608–612) copies/validates the supplied inventory and summary binding. Original28d `inventory` (132–134) returns relative path→file SHA only; `finalize` (596–611) obtains the summary through Store but emits no stat7 inventory or this exact summary descriptor. Originalb08 `invocation_inventory` (143–160) observes invocation files, not the full public catalog. Checklist453 (29, 50–53) consumes these inputs. This absence was reported to the parent before creating this separate source.

Selected new source: `/private/tmp/lanl17_read_passive_one_catalog_inventory_20261007.py`; 29,653 bytes; SHA256 `76b86959ceca7a162a34b7a2d1e633ee9523d0b9cc7f629e9fbeeb4e101aa176`. This is a separate passive metadata producer, not an index writer, request author, validator or admission gate. Original7a/author/28d/b08/6a/F6 are unmodified.

## Exact output and remaining parent facts

Future execution creates one fresh 0700 directory with one 0600 **UNSEALED** `catalog-inventory.json`, format `swdb.lanl17-passive-one-catalog-inventory.v1`. There is no top-level `identity_sha256`. The stdout receipt contains only the new file pin, canonical-true payload digest, reader source pin, record count, selected summary route, and false index/scientific execution flag. No YAML bodies, raw logs, provider output, prompt/auth material, addresses or streams are serialized.

`catalog_inventory` is sorted by relative public path and contains every eligible public `.yaml`/`.yml` file in exactly one original M2-routed `records` folder. Each row has `path`, exact current byte count, file SHA256 and exact original stat7 `{dev,ino,mode,uid,size,mtime_ns,ctime_ns}`. `catalog_inventory_sha256` uses original7a whole-object canonical policy: sorted keys, separators comma/colon, ensure_ascii=true, allow_nan=false. `context` and `limits` match the original7a/R1 input shapes; they are observed current metadata or explicitly supplied future finite allowances, not parent approval.

The mandatory `--summary-selection` has two explicit choices:

- `present`: requires `--summary-relative-path` with the exact known original public relative path. Only that selected summary YAML is parsed; its ID must be the original campaign ID plus `.summary`, kind `campaign_summary`, mode `extensa`, campaign exact, and `swdb_commit` exact actualR. Emits the exact original7a present `summary_binding={state,path,id,record_sha256}` and original file/digest pin.
- `parent-binding-required`: forbids `--summary-relative-path`, parses no YAML and leaves `summary_binding`/`summary_original_pin` null. Its descriptor says that the parent binding remains required, index-wide ID absence was not checked and no absence attestation was generated. This route permits passive inventory for an interrupted catalog without fabricating `parent_observed_absence:true`. Parent must independently provide the exact absence binding after real observation; unchanged7a later checks that ID is absent from the complete parsed index.

Even present mode does not establish index-wide uniqueness. Original7a still performs that check. Missing named present summary refuses, rather than switching to absence or guessing a filename. The reader does not provide original validation argv/exit/stdout/stderr or their provenance, continuity since that validation, stopped-process/exclusive-snapshot observations, normal/substantive completion, publication/selection/trajectory or D30 admission. Those are required explicit parent facts for the original request author/writer, never defaults. The finite scan only rechecks byte/stat continuity during this reader's own invocation.

## Source, path, identity and privacy contract

Source lines444–499 require explicit Linux mbit10 account/UID, one of the four exact CIDs, exact original M2 file bytes/SHA and canonical-true identity, M2 format/helper/R/F6/source-clean declarations, actual M2 raw/source routing, exact original7a source hash/size, actualR full40 commit/tree and independently checked clean185-module F6 source. No actual path is guessed: all four campaign roots derive from the pinned M2 raw root; the one catalog derives from the selected original CID. SourceC is fixed `f893fed400347ed23d92e917d8bde21b75e5375d`; F6 is fixed `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3`.

Original7a stat7, checked_path, record-relative discovery, returned-bytes, full catalog rescan/rehash, duplicate-key refusal, timestamp-as-string loader, finite plain values, sourceC/F6 inspection, fresh external output and exact seal policies are retained. Catalog hashes use bounded streaming returned bytes with exact before/after FD+path stat7; the selected summary is verified from returned bytes with its exact pin/stat before parsing. All symlink/UID/type/size/inode/hash drift refuses. Unique catalog size means the sum of the approved relative-file inventory, not cumulative rereads; the final pre-publication and pre-success custody passes intentionally reread originals under the same finite deadline.

The output must be fresh, external to exact M2 source/raw/all four campaign roots, under the owned mbit10 data prefixes, and have an owned nonsymlink parent. Own reader, original7a control, M2, catalog and source185/F6 are rechecked before publication and before success (533–553); partial outputs are retained on refusal. Only fixed local read-only Git commands inspect source, with network/prompt/optional-lock behavior disabled. New `git` differs from the original solely by `stderr=subprocess.DEVNULL`; bounded exception class plus message hash are returned, and raw YAML/parser/Git/argv/environment prose is not printed (564–570). Original7a remains immutable; its inherited Git stderr requires the already discussed reviewed outer remote-only capture for a future invocation.

## Unchanged finite bounds and future invocation interface

- Original7a catalog file cap:128MiB. Unique one-catalog cap:2GiB. Record cap:16,384. Metadata cap:8MiB. No selected consumer32MiB bound expands.
- Reader allowance and prospective writer allowance are both explicit integers60–3600 seconds; neither is a prediction of runtime or an experiment/provider budget. Reader uses a monotonic deadline plus SIGALRM. Its allowance is recorded separately from original7a-compatible `limits.metadata_deadline_seconds` (the explicitly chosen future writer allowance).
- All caller flags are mandatory except the summary path conditional on the selected route. Formal interface only, with no actual values/template assembled here:

```
python3 <reviewed-reader-source> \
  --manifest <exact-original-M2-manifest.json> \
  --manifest-bytes <explicit-original-bytes> \
  --manifest-sha256 <explicit-file-SHA256> \
  --manifest-identity-sha256 <explicit-original-true-policy-seal> \
  --source-sha <actual-R-full40> --source-tree <actual-R-tree-full40> \
  --campaign <one-exact-original-CID> \
  --index-writer-source <unchanged-original7a-source> \
  --index-writer-source-sha256 7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b \
  --reader-sha256 76b86959ceca7a162a34b7a2d1e633ee9523d0b9cc7f629e9fbeeb4e101aa176 \
  --account-user <explicit-parent-verified-account> --account-uid <explicit-parent-verified-UID> \
  --metadata-deadline-seconds <explicit-reader-60-to-3600> \
  --writer-metadata-deadline-seconds <explicit-future-writer-60-to-3600> \
  --output-directory <fresh-reviewed-external-directory> \
  --summary-selection <present-or-parent-binding-required>
```

Present mode also supplies `--summary-relative-path <exact-known-public-path>`; the other route must omit that flag. Parent may invoke only after real stopped/final-validation observations and full review of the explicit actual argument/pin packet, in its reviewed metadata wrapper. This source-only handoff authorizes no execution. Parent owns all remote dispatch, observations and transfer.

## Preparation evidence only

A stdlib source AST inspection verified 25 exact shared helper/class ASTs, 12 exact original constant assignment ASTs and both exact loader setup ASTs. The only changed shared helper is `git`, and removing its single stderr keyword exactly recovers original7a AST. `main` and the passive observation/publication helpers are new. There is exactly one YAML-load call in the entire source, in selected-present-summary handling. No original module/control was imported, no lifted helper executed and no synthetic test body ran. This is source preparation, not runtime proof. Companion preparation JSON pins this source, handoff and original contract suppliers; its seal is preparation metadata only.
