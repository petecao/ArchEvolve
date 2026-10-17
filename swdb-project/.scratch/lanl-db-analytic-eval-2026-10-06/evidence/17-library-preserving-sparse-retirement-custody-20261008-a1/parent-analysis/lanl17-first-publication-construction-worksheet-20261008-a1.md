# First-publication construction worksheet — 2026-10-08 ET

SOURCE ONLY; not a request. Actual prepare/M2/EF/policy/publication facts remain pending. Parent alone harvests, reviews and executes after genuine prepare.

## Fixed source contract

Author: `/private/tmp/lanl17_author_first_publication_request_r1_20261007.py`, 28419 B, SHA `791f95b5f53c23740ce8b2bdd72fc8dcd625494a60f5399f30b5ed704347fb1a` (lines242–457). Selected R=`5e12a9796432654d88def24ecea617d16ca605b2`, tree=`1ab2c8ab147251391a4af75e637114bdd5b0ff27`; C=`f893fed400347ed23d92e917d8bde21b75e5375d`; F6=`f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3`. Original NOTRUN histories remain.

`controls`: eight exact `{path,bytes,sha256}` pins at reviewed routes:

| Name | B | SHA256 |
|---|---:|---|
| producer |46165|32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6|
| helper |38195|28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414|
| supervisor |8014|fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0|
| auditor |115130|6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da|
| collector |24818|b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c|
| source_plan |11817|e3420b334ce05f7268699b0079987d1d2afc98fe5cb5503e6069a89038b59170|
| field_checklist |13484|45313085d7d010be749f9b9aec7c9aadf0b5b8d1e7c385bfb9f79fd384cc6fe0|
| accepted_input_contract |5288|192eb5d1c2b461f9d42b3532a934c8dc107bb193f29fabbb5ba2dec94acd2978|

Plan `/private/tmp/lanl17-r1s1-future-actual-input-construction-plan-20261007.md`; producer32 source lines250–263/304–317/420–458.

## Harvest after genuine prepare

Chosen routes only: S=`/data1/yanruj/ArchEvolve-lanl17-source-20261007-a4`; RAW=`/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4`; CTRL=`/data/yanruj/EvolveSWDB_runs/lanl17-metadata-prepare-20261007-a4`. Existence/success pending.

`inputs`: exact four descriptors, each `{path,bytes,sha256,encoding,sealed,writer_source:{path,bytes,sha256}}`. Sealed descriptors additionally require `{identity_sha256,canonical_ensure_ascii,canonical_policy_sources:[exact writer pin]}`:

- `manifest_M2`: RAW/manifest.json, JSON sealed/True, writer exact helper control; original format `swdb.lanl17-parent-population.v1`.
- `prepare_supervisor`: CTRL/supervisor-receipt.json, JSON sealed/False, writer exact supervisor control; Require nonfixture prepare, child/supervisor0, child_returned, no timeout/signal/errors, subreaper true/survivors empty, calls/outcomes0. Processes SHA: exact author324 constant.
- `freeze_receipt`: actual EF file `swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-freeze-mbit10-20261007-a4.json`, JSON sealed/True, writer helper. Prospective EF checkout `/data1/yanruj/ArchEvolve-lanl17-freeze-evidence-20261007-a4`; actual commit/pins pending.
- `policy`: actual new YAML in RAW/base/records/agreement_policies, unsealed. Discover file/ID from original new-record inventory. Pin live writer: S/swdb-project/swdb/extensa_agreement.py:158–214 → workflow.persist. Policy body must equal freeze.public_policy.

Preserve bytes/True-vs-False policies. M2 equals nested sealed M1 plus freeze_export/new identity; M2.freeze_export.commit equals observed EF.

## Specification fields — values pending

Root exact: `format,context,observations,inputs,read_roots,final_R,controls,parent_review,output_directory`; format `swdb.lanl17-first-publication-request-author-spec.v1`. `final_R={commit,tree}` uses selected R/tree above.

Context exact: `source_commit,source_C,estimator_sha256,helper_sha256,source_path,manifest_identity_sha256,policy:{id,identity_sha256,frozen_at},account:{platform:"linux",host:"mbit10",uid:114316761,user:"yanruj"}`. M2 identity/policy facts pending.

Observations exact: `freeze_export_commit,completed_export_exit_code,application_outcomes_opened,frozen_live_files_verified,checked_utc`. Require actual published EF exit0/outcomes0/live verified true, not inferred from seals. checked_utc follows prepare ended_utc/freeze checked_utc/policy frozen_at; publication precedes dispatch/outcome.

`read_roots`: 1–16 distinct owned nonsymlink existing directories beneath `/data/yanruj/` or `/data1/yanruj/`; cover every input/writer/control pin. BASE itself fails slash-prefix qualification. Direct-BASE aliases need same-byte nested archived source routes for descriptors; verify availability and preserve original executed-alias custody.

Review exact: `basis,author_sha256,reviewed_spec_payload_sha256,actual_inputs_parent_approved,fixtures_or_replays_allowed,freeze_export_publication_parent_checked,reviewed_utc`. Basis=`explicit_parent_review_of_actual_publication_inputs_and_original_observations`; Booleans true/false/true require full actual review. True payload digest excludes parent_review; True CLI review digest covers review; spec SHA covers complete bytes. Review UTC: observations ≤ review ≤ invocation.

## Two separate future invocations

Author staged alias `/data1/yanruj/lanl17-input-author-source-20261007-a1/publication_author.py`:
`python3 <author> --specification <actual spec> --specification-sha256 <actual fileSHA> --parent-review-sha256 <actual True review digest> --author-sha256 <791 fullSHA> --output-directory <fresh reviewed external directory> --metadata-deadline-seconds <60..3600>`.

Author creates0700 directory/0600 publication-request.json + author-custody.json outside S/RAW/four campaign roots, beneath /data/yanruj. Review returned request separately.

Producer staged alias `/data1/yanruj/lanl17-custody-source-20261007-a3/capture-producer.py`:
`python3 <producer> --request <actual author request> --request-sha256 <actual returned fileSHA> --output <distinct fresh external file>`.

Producer outputs `swdb.lanl17-freeze-publication-custody.v1`, True/0600 fresh file in existing owned external parent outside S/RAW/four roots. No trajectory/D30/study admission. Parent reviews native/outer/private capture and routes.
