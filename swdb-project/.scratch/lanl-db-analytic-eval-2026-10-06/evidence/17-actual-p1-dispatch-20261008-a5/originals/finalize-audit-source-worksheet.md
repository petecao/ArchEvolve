# Ticket 17 a5 FINALIZE, full-record index and accepted-input worksheet

Prepared 2026-10-08 ET. SOURCE-ONLY / NOT EXECUTED. This worksheet supplies routes and retained source pins, not new observations, an index request, an accepted-input specification or scientific admission. Assumption: reuse the original reviewed controls unchanged; only the actual a5 routes replace earlier prospective routes. Every `ACTUAL_*` or `FRESH_*` value below is still an explicit future parent input. Never execute a template with placeholders or infer those inputs from artifact existence.

## Fixed actual identities and routes

| Alias | Exact value |
| --- | --- |
| R | `5e12a9796432654d88def24ecea617d16ca605b2` |
| R_TREE | `1ab2c8ab147251391a4af75e637114bdd5b0ff27` |
| C | `f893fed400347ed23d92e917d8bde21b75e5375d` |
| F6, 185 unchanged Python modules | `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3` |
| S | `/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5` |
| RAW | `/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5` |
| M2 | `RAW/manifest.json` |
| M2 bytes / file SHA | `292401` / `b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1` |
| M2 original ensure_ascii=true seal | `66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7` |
| PREP | `/data/yanruj/EvolveSWDB_runs/lanl17-metadata-prepare-20261007-a5` |
| FINALIZE_CONTROL, must be fresh | `/data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a5` |
| EF worktree / commit | `/data1/yanruj/ArchEvolve-lanl17-freeze-evidence-20261007-a5` / `44652dd359e352480065f0c6281730dd61523ea6` |
| EF branch | `codex/lanl17-freeze-evidence-20261007-a5` |
| Policy ID | `extensa-gem5-bfs-20261006-p1.agreement.5bae2f42d9078864` |
| Policy identity | `5bae2f42d9078864caad73e81a16007edb6458f0b101628ded04a7ef3aedbf7d` |
| Frozen UTC | `2026-10-08T16:05:25.347884+00:00` |
| Account | Linux `mbit10`, UID/EUID `114316761`, user `yanruj` |

`RAW`, `S` and other aliases denote the literal absolute strings above in command arrays; they are not environment overrides. EF tree, actual ER commit/tree/additions, report ID and all completed campaign/index input facts remain unsupplied here. PREP originals are locally decoded under `/private/tmp/lanl17-prepare-completion-decoded-originals-20261008-a1`; their `decoded-parent-summary.json` pins every retained local/remote original. This worksheet adds no independent remote verification.

The four actual **Store** roots are exactly:

| CID | Actual records root |
| --- | --- |
| `extensa-gem5-bfs-20261006-p1` | `/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/campaign-runs/extensa/extensa-gem5-bfs-20261006-p1/records` |
| `extensa-gem5-bfs-20261006-p2` | `/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/campaign-runs/extensa/extensa-gem5-bfs-20261006-p2/records` |
| `extensa-gem5-bfs-20261006-p3` | `/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/campaign-runs/extensa/extensa-gem5-bfs-20261006-p3/records` |
| `extensa-gem5-bfs-20261006-p4` | `/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/campaign-runs/extensa/extensa-gem5-bfs-20261006-p4/records` |

For containment, use their four campaign roots without the final `/records`. The initial `RAW/catalogs/CID/records` team catalogs are not the completed campaign Stores.

## Retained native and control source pins

Native pins below are dated originals from `/private/tmp/lanl17-pre-dispatch-host-capture-20261008-a1/host-original.json`, observed 2026-10-08T16:34:14Z. Recheck live executable/source identity, ownership, regular/nonsymlink routes, GNU behavior, host/account, clean R/F6 and lane state before future invocation. The file contains original stat metadata. A dated byte pin does not establish current ownership or clearance.

| Native path | Bytes | SHA-256 |
| --- | ---: | --- |
| `/usr/bin/bash` | 1446024 | `bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1` |
| `/usr/bin/python3.12` | 8020928 | `e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f` |
| `/usr/bin/timeout` | 39880 | `12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52` |
| `/usr/bin/sha256sum` | 39336 | `4d2db56c867e5324e0084c9e897f6360d37517de77ac96f2bd31494223d69a60` |
| `/usr/bin/wc` | 55824 | `9005273a966c875547a4317288bdd92e7b2aa49ad86bc9978121242106405e6b` |
| `/usr/bin/mkdir` | 76296 | `430c3f949d7d328cd835722f5bbddeac0956fbdfbbb6a197e0abb1def3ed27e2` |
| `/usr/bin/git` | 4019024 | `06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb` |

`/usr/bin/python3` is the original symlink to native `/usr/bin/python3.12`; the explicit direct control interpreter is the canonical latter path. Account HOME is `/home/yanruj`, public CODEX_HOME is `/data1/yanruj/.codex`. Preserve both. If a fresh login lacks the task marker, restore `SWDB_LANL17_ORIGINAL_CODEX_HOME` only after current CODEX_HOME matches the pinned route, refusing any nonempty conflicting marker. State marker restoration truthfully; do not claim it preexisted, read auth bodies or edit authentication.

| Alias and exact staged path | Bytes | SHA-256 |
| --- | ---: | --- |
| GUARD9c `/data1/yanruj/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py` | 14577 | `9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6` |
| HELPER28 `/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py` | 38195 | `28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414` |
| SUPERVISORfa `/data1/yanruj/lanl17-metadata-supervisor-cleanup60-20261007-a4.py` | 8014 | `fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0` |
| INVENTORY76 `/data1/yanruj/lanl17-input-author-source-20261007-a1/passive_inventory.py` | 29653 | `76b86959ceca7a162a34b7a2d1e633ee9523d0b9cc7f629e9fbeeb4e101aa176` |
| AUTHORa2 `/data1/yanruj/lanl17-input-author-source-20261007-a1/index_request_author.py` | 38266 | `a2e69aef10deb6186ac49401516ffba9a165b2f3cc94c8001646b6ac9a5b701d` |
| WRITER7a `/data1/yanruj/lanl17-index-source-20261007-a1/writer.py` | 33445 | `7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b` |
| ENVELOPE1ee `/data1/yanruj/lanl17-index-privacy-source-20261007-a1/envelope.py` | 38790 | `1ee5ffbdf1ef322cfd5bfec4b6e402c29d23c776e855f01d25208ebbece0fcfc` |
| OUTER59 `/data1/yanruj/lanl17-index-private-outer-source-20261007-a1/outer_capture.py` | 34658 | `59c06dd5ea606414827a85d6e27f4aff1bc381827624590b2449415198399544` |
| BOOTSTRAP0d `/data1/yanruj/lanl17-index-private-outer-source-20261007-a1/bootstrap.sh` | 6549 | `0d1eb650d1bcb1a9f491d5fb790f083e371875ddd20fe0bf1f42d5fce05a9217` |
| SPEC339 `/data1/yanruj/lanl17-custody-source-20261007-a3/spec-writer.py` | 11868 | `339ea0dc1abb6778f0f016e9c03f2b29c5f1916154b668f5416747b2768a9231` |
| ASSEMBLERde `/data1/yanruj/lanl17-custody-source-20261007-a3/assembler.py` | 33584 | `de669e4c0928876f9d033f6d9c1fc820ab3a1eb915aba20c5b6755b9866d7e6a` |
| AUDITOR6a `/data1/yanruj/lanl17-custody-source-20261007-a3/auditor.py` | 115130 | `6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da` |
| COLLECTORb08 `/data1/yanruj/lanl17-custody-source-20261007-a2r1/collector.py` | 24818 | `b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c` |
| CAPTURE32 `/data1/yanruj/lanl17-custody-source-20261007-a3/capture-producer.py` | 46165 | `32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6` |

PLAN = `S/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-selected-trajectory-controls-20261007-a2r1s1/lanl17-r1s1-future-actual-input-construction-plan-20261007.md`, 11817 B, SHA `e3420b334ce05f7268699b0079987d1d2afc98fe5cb5503e6069a89038b59170`.

CONTRACT = same directory `/lanl17-auditor-a2r1s1-accepted-input-contract-20261007.md`, 5288 B, SHA `192eb5d1c2b461f9d42b3532a934c8dc107bb193f29fabbb5ba2dec94acd2978`.

## 1. FINALIZE through unchanged guard9c, supervisorfa and helper28

Prerequisites: every actual attempt stopped with original receipts; actual campaign Stores/summaries exist; both socket lanes and legacy lease are released; clean exact S=R and F6 unchanged. A summary is not proof of normal terminal substantive completion. Preserve failed/partial attempts and control directories. This action creates the fresh metadata control directory and may publish the pure report export; it does not create a full record index.

**Phase-specific project route:** FINALIZE requires `S/swdb-project` (guard9c lines 130–131). PREPARE's C cleanup project is not accepted here. Original cleanup/supervisor proof paths and a4 control filenames remain unchanged.

```text
/usr/bin/timeout --signal=TERM --kill-after=60s 78300s
  /usr/bin/python3.12 GUARD9c
  --action finalize --final-source-sha R
  --project S/swdb-project --control FINALIZE_CONTROL
  --guard-sha256 9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6
  --cleanup-proof /data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json
  --cleanup-proof-identity 18e58a44476709cc7520f9760ac94161cd67248e39ff662fbfb16378855d7ca1
  --supervisor-proof /data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-20261007-a4/receipt.json
  --supervisor-proof-identity ea9751eef12bc519be0c4159813e29fa5aa378693c6a31caea137599c5db744b
  -- --manifest M2
```

The immediate parent must be this direct GNU78300/K60 envelope, not an intervening Python wrapper. Guard emits GNU78120/K60 → unchanged supervisor `--timeout-s 78000` → helper `finalize --manifest M2`. Preserve published startup/environment contract and original seal policies: guard/supervisor false; helper true. Capture private stdout/stderr from before interpreter startup through finite parent custody; do not return raw diagnostics or infer remote termination from local transport cleanup.

Helper28 validates each exact Store with public `python3 -m swdb validate --records <STORE>` (3600 s), producing `RAW/validate-CID.{argv.json,exit-code.txt,stdout,stderr}`. It exports named nonrejected candidates with public `campaign-export RAW/configs/CID.yaml --records RAW/base/records --runs-root RAW/campaign-runs --format json --candidate <each actual selected ID>` (6000 s). It runs `agreement-report --policy <policy ID> --records RAW/base/records --mode extensa --campaign p1 --format json` plus four `--campaign-records <STORE>` (14400 s), then validates the final base export (3600 s). Expected scope remains zero eligible numeric pairs, unsupported, `do_not_switch_to_flow_b`, unchanged timing-only selection and four observed campaigns. Actual result, ER/report identity, logs, supervisor/preregistration originals and cleanup must be checked after execution; expected scope is not a measured outcome. Original compact report format is `swdb.lanl17-actual-agreement-compact.v1`; `RAW/final-export.json` describes the future export.

## 2. Four separate full-record indexes

Use one catalog per CID, the exact Stores above. Original helper validation plus **honest current quiescence/exclusive ownership and unchanged catalog continuity** must precede authoring. Bind original validator source/argv/exit/stdout/stderr and the full original inventory; a zero exit by itself is insufficient. Never substitute a selected closure or initial team catalog. Index publication is metadata custody, not validation or trajectory admission.

Passive inventory template (explicit deadlines remain future values):

```text
/usr/bin/python3.12 -B INVENTORY76
  --manifest M2 --manifest-bytes 292401
  --manifest-sha256 b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1
  --manifest-identity-sha256 66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7
  --source-sha R --source-tree R_TREE --campaign ACTUAL_CID
  --index-writer-source WRITER7a --index-writer-source-sha256 7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b
  --reader-sha256 76b86959ceca7a162a34b7a2d1e633ee9523d0b9cc7f629e9fbeeb4e101aa176
  --account-user yanruj --account-uid 114316761
  --metadata-deadline-seconds ACTUAL_READER_SECONDS
  --writer-metadata-deadline-seconds ACTUAL_WRITER_SECONDS
  --output-directory FRESH_INVENTORY_OUT
  --summary-selection present --summary-relative-path ACTUAL_SUMMARY_RELATIVE_PATH
```

Use the original alternative `--summary-selection parent-binding-required` without a summary-relative-path only when that is the truthful selected state. It does not invent the missing parent summary binding. Inventory records every eligible original YAML path/bytes/stat `{dev,ino,mode,uid,size,mtime_ns,ctime_ns}`. Index limits remain 128 MiB/file, 2 GiB unique one-catalog bytes, 16384 records, 8 MiB metadata and explicit writer deadline 60–3600 s; no timeout widening.

The future unsealed author specification has exactly `format, context, originals, catalog_inventory, summary_binding, limits, writer_parent_review, writer_output_directory, controls, author_review, output_directory`. Parent supplies and reviews actual originals/observations before this command:

```text
/usr/bin/python3.12 -B AUTHORa2
  --specification ACTUAL_INDEX_AUTHOR_SPEC
  --specification-sha256 ACTUAL_INDEX_AUTHOR_SPEC_FILE_SHA
  --parent-review-sha256 ACTUAL_AUTHOR_REVIEW_DIGEST
  --author-sha256 a2e69aef10deb6186ac49401516ffba9a165b2f3cc94c8001646b6ac9a5b701d
  --metadata-deadline-seconds ACTUAL_AUTHOR_SECONDS
  --output-directory FRESH_INDEX_AUTHOR_OUT
```

Read exact returned `index-request.json` bytes and its whole-file SHA plus separate author custody; no invented original request seal. The selected original author is a2, writer is 7a, and bootstrap is 0d1eb650. **“0d56” means this bootstrap's 56-argument script vector, not a SHA prefix.**

Launch prefix is `/usr/bin/bash --noprofile --norc BOOTSTRAP0d`. Its exact 56 script arguments, in order, follow. Resolve named pins to literal values from the tables; future values remain unsupplied:

| Positions | Exact argument(s), in order |
| --- | --- |
| 1–2 | `FRESH_BOOTSTRAP_LOGS`, `ACTUAL_WRITER_SECONDS` |
| 3–7 | `/usr/bin/python3.12`, `/usr/bin/timeout`, `/usr/bin/sha256sum`, `/usr/bin/wc`, `/usr/bin/mkdir` |
| 8–10 | `OUTER59`, `S`, `RAW` |
| 11–13 | `FRESH_WRITER_OUT`, `FRESH_INNER_LOGS`, `FRESH_OUTER_LOGS` |
| 14–16 | `M2`, `b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1`, `59c06dd5ea606414827a85d6e27f4aff1bc381827624590b2449415198399544` |
| 17–20 | SHA256SUM SHA `4d2db56c867e5324e0084c9e897f6360d37517de77ac96f2bd31494223d69a60`, WC SHA `9005273a966c875547a4317288bdd92e7b2aa49ad86bc9978121242106405e6b`, MKDIR SHA `430c3f949d7d328cd835722f5bbddeac0956fbdfbbb6a197e0abb1def3ed27e2`, BOOTSTRAP SHA `0d1eb650d1bcb1a9f491d5fb790f083e371875ddd20fe0bf1f42d5fce05a9217` |
| 21–22 | `--request`, `ACTUAL_INDEX_REQUEST` |
| 23–24 | `--request-sha256`, `ACTUAL_INDEX_REQUEST_FILE_SHA` |
| 25–26 | `--request-author-source`, `AUTHORa2` |
| 27–28 | `--request-author-source-sha256`, `a2e69aef10deb6186ac49401516ffba9a165b2f3cc94c8001646b6ac9a5b701d` |
| 29–30 | `--parent-review-sha256`, `ACTUAL_WRITER_PARENT_REVIEW_DIGEST` |
| 31–32 | `--output-directory`, `FRESH_WRITER_OUT` |
| 33–34 | `--log-directory`, `FRESH_INNER_LOGS` |
| 35–36 | `--envelope-sha256`, `1ee5ffbdf1ef322cfd5bfec4b6e402c29d23c776e855f01d25208ebbece0fcfc` |
| 37–38 | `--cleanup-helper-source`, `HELPER28` |
| 39–40 | `--python-executable`, `/usr/bin/python3.12` |
| 41–42 | `--python-executable-sha256`, `e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f` |
| 43–44 | `--timeout-executable`, `/usr/bin/timeout` |
| 45–46 | `--timeout-executable-sha256`, `12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52` |
| 47–48 | `--timeout-family`, `GNU` |
| 49–50 | `--envelope-source`, `ENVELOPE1ee` |
| 51–52 | `--outer-log-directory`, `FRESH_OUTER_LOGS` |
| 53–54 | `--capture-source-sha256`, `59c06dd5ea606414827a85d6e27f4aff1bc381827624590b2449415198399544` |
| 55–56 | `--parent-reviewed-argv-sha256`, `ACTUAL_DIRECT_GNU_ENVELOPE_ARGV_DIGEST` |

The final digest is canonical ensure_ascii=true JSON of this **direct GNU/envelope array**, preserving order and using only the first fourteen forwarded flag/value pairs (positions 21–48):

```text
[/usr/bin/timeout, --signal=TERM, --kill-after=60s, (ACTUAL_WRITER_SECONDS+420)s,
 /usr/bin/python3.12, -B, ENVELOPE1ee, <positions 21 through 48 exactly>]
```

It does not bind all 56 bootstrap arguments. Parent separately reviews the complete actual bootstrap vector, all routes/native pins/startup semantics and source bytes. All four output/log directories must be mutually disjoint, fresh/private, outside the whole S/RAW/four campaign boundaries. Verify trusted Bash, absent injected startup settings and Linux Bash `ulimit -f` units of 1024 B before executing. Preserve unchanged HOME/auth.

Bounds: writer own W; inner GNU W+120/K60; outer GNU W+420/K60 with wait+65 and pre/post 60 s alarms; bootstrap GNU W+720/K60; metadata utilities GNU30/K60. Diagnostic files 16 MiB; returned structured metadata 16 KiB. Return FD is closed in every external child; logs stay private remote originals. Zero transport/control exit is not validated-index admission. Require consistent known inner/outer original sealed receipts, cleanup and exact `record-index.json` whole-file pin. Bare index is unsealed `id -> {kind, sha256, record_sha256}`; writer custody inherits truthful original validation and parent observations. Repeat with fresh distinct paths for each CID.

## 3. Actual accepted-input specification, assembler and unchanged auditor

Parent first inventories actual originals: final11/final14 accepted dependency admissions and exports, EF/ER/additions, policy/report, PREP/FINALIZE originals, four full indexes, actual before/dispatch/stopped/release/after/corroboration chains, truthful blind publication/outcome order and normal terminal substantive iterations. Include any actual unclean-resume, missing-component refusal, named public candidate selection and interrupted/rejected selected body custody. No synthetic replacement, inferred acceptance or retrospectively fabricated observation.

The unsealed parent template has `format, writer, parent_review, documents, root, forbidden_output_roots`. It pins the original template-author source and every original file/size/SHA, original seals and explicit original canonical policy. Root fields are exactly `freeze_export, report_export, manifest_M2, policy_id, report_id, prepare_supervisor, finalize_supervisor, prepare_preregistration, finalize_preregistration, freeze_publication_custody, final_ticket11_acceptance, final_ticket14_acceptance, collector_source_pin, collector_account, selected_records, campaigns`. Exact `{"$original_document":"alias"}` references allow no pin overrides. Selected YAML bodies and unsealed public campaign exports gain no invented receipt seals. Input-specification writer family is `parent_input_specification`, canonical true, using its explicit control-source document alias as source and sole policy source. CAPTURE32 remains the separate eight-format parent-capture producer.

```text
/usr/bin/python3.12 -B SPEC339
  --template ACTUAL_UNSEALED_PARENT_TEMPLATE --template-sha256 ACTUAL_TEMPLATE_FILE_SHA
  --template-author-source ACTUAL_ORIGINAL_TEMPLATE_AUTHOR
  --template-author-source-sha256 ACTUAL_TEMPLATE_AUTHOR_SHA
  --parent-review-sha256 ACTUAL_CANONICAL_TRUE_PARENT_REVIEW_OBJECT_DIGEST
  --assembler-source ASSEMBLERde --assembler-sha256 de669e4c0928876f9d033f6d9c1fc820ab3a1eb915aba20c5b6755b9866d7e6a
  --writer-source-alias ACTUAL_DECLARED_SPEC_WRITER_DOCUMENT_ALIAS
  --source-root S
  --campaign-root RAW/campaign-runs/extensa/extensa-gem5-bfs-20261006-p1
  --campaign-root RAW/campaign-runs/extensa/extensa-gem5-bfs-20261006-p2
  --campaign-root RAW/campaign-runs/extensa/extensa-gem5-bfs-20261006-p3
  --campaign-root RAW/campaign-runs/extensa/extensa-gem5-bfs-20261006-p4
  --metadata-deadline-seconds ACTUAL_SPEC_SECONDS_60_TO_120
  --output-directory FRESH_SPEC_OUT
```

Parent reviews the original two-file output, exact specification file SHA and true seal before assembler use:

```text
/usr/bin/python3.12 -B ASSEMBLERde
  --repository ACTUAL_CLEAN_R_CHECKOUT --final-r R --final-r-tree R_TREE
  --freeze-export 44652dd359e352480065f0c6281730dd61523ea6 --freeze-export-tree ACTUAL_EF_TREE
  --report-export ACTUAL_ER --report-export-tree ACTUAL_ER_TREE
  --spec FRESH_SPEC_OUT/input-specification.json
  --spec-sha256 ACTUAL_SPEC_FILE_SHA --spec-identity ACTUAL_SPEC_TRUE_SEAL
  --spec-canonical-ensure-ascii true
  --auditor-source AUDITOR6a --collector-source COLLECTORb08
  --plan-source PLAN --contract-source CONTRACT
  --collector-uid 114316761 --collector-user yanruj
  --metadata-deadline-seconds ACTUAL_ASSEMBLER_SECONDS_60_TO_3600
  --output-directory FRESH_ACCEPTED_OUT
```

Assembler bounds stay 32 MiB/original, 8 MiB specification/output, 512 MiB total originals, 4096 originals, depth40, 256 attempts/CID. Output must be fresh/private outside selected repository, M2 source, forbidden roots and four campaigns. It creates only `accepted-pins.json` and `construction-custody.json`; state `constructed_for_parent_review_not_auditor_admission`. Review the constructed exact bytes independently before the unchanged auditor's three-flag invocation:

```text
/usr/bin/python3.12 -B AUDITOR6a
  --repository ACTUAL_CLEAN_R_CHECKOUT
  --accepted-pins FRESH_ACCEPTED_OUT/accepted-pins.json
  --accepted-pins-sha256 ACTUAL_PARENT_ACCEPTED_FILE_SHA
```

Auditor code0 can establish `ready_for_parent_review` only after its actual trajectory/order checks; code2 remains incomplete/pending, code3 refused. The distinction between campaign completeness and numerical evidence remains: zero eligible paired forecasts cannot establish accuracy/D30, and no-switch/human decision scope remains unchanged.

## Source provenance and future boundary

This local worksheet was derived by text/source inspection only from retained handoffs: `17-original-index-writer-private-outer-capture-controls-20261007/*source-handoff*.md` (exact 56 mapping), `17-parent-index-request-author-controls-20261007-r1/*source-handoff*.md`, `17-passive-one-catalog-inventory-controls-20261007/*source-handoff*.md`, `17-future-input-controls-20261007-a3/{lanl17-accepted-pins-assembler-source-handoff-20261007.md,lanl17-parent-input-specification-writer-source-handoff-20261007.md}`; staged originals for index7a/envelope1ee/outer59/authora2 and reviewed input controls a3. All archive paths are under `swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/`.

No remote command, control import/main, test, catalog read, producer, index, selected reader or scientific auditor was invoked to create it. Future completed validation/quiescence observations, actual index requests/specifications, ER/tree/report and selected accepted-input originals remain parent-supplied. Existing seals/source pins and limits are unchanged.
