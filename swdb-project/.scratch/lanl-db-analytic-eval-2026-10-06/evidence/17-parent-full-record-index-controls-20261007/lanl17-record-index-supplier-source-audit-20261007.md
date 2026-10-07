# Actual17 full-record-index supplier audit — 2026-10-07 ET

Source-only preparation. No actual inputs, imports, Store, validation, campaign, native, provider, SSH or tests ran. No future revision, export or outcome is assigned.

The inspected selected controls and scientific C public code do **not** emit the exact full record index required by the capture producer. The original per-campaign validation files **do** have a supplier. This is an index metadata gap, not a missing validation invocation.

## Exact suppliers and consumers

- Scientific C `f893fed400347ed23d92e917d8bde21b75e5375d`, `swdb-project/swdb/store.py:104`: `Store.index()` returns `id -> kind`. It supplies neither original file SHA nor whole-record digest. `validate.py` consumes this internal map, and `cli.py` prints `OK: <count> record(s) valid` or problems/FAILED with its exit status. The public validate command emits no full hash index.
- Original `/private/tmp/lanl17_parent_helpers_cleanup60_a4.py`, SHA `28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414`: `run_cli` retains exact `<name>.argv.json`, `.stdout`, `.stderr`, and, after the child returns, `.exit-code.txt`. `finalize` invokes `validate-<cid>` against `M2.raw/campaign-runs/extensa/<cid>/records`. Thus the original files are `M2.raw/validate-<cid>.{argv.json,stdout,stderr,exit-code.txt}`. A timeout may lack the exit file; absence must remain pending. Its `validate-final-export` files validate `M2.raw/base/records`, which cannot substitute for the campaign store. Its `inventory` is relative-path -> file SHA, not the required record identity map.
- Original `/private/tmp/lanl17_compact_attempt_custody_a2r1_20261007.py`, SHA `b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c`: collector custody contains safe state/ledger/invocation projections, not the full record index or a catalogue validation invocation.
- `/private/tmp/lanl17_parent_capture_projection_producer_a3_20261007.py`, SHA `32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6`, lines 275–278: `record_index(inputs)` consumes an original unsealed JSON mapping whose every row has exactly `kind`, `sha256`, `record_sha256`. `trajectory` also requires the original validation exit/stdout/stderr; `interrupted_bodies` requires the validation exit and selected closure. These are consumers, not suppliers. The full index descriptor needs the actual separate writer source pin.
- `/private/tmp/lanl17_selected_record_trajectory_auditor_a2r1s1_20261007.py`, SHA `6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da`: selected closure/trajectory/interrupted checks compare index semantics and exact selected body hashes and require prior full-validation exit 0. It does not create the index.

A scoped source search of `swdb-project/swdb`, `swdb-project/scripts` and LANL `/private/tmp/*.py` found no existing emitter of this exact three-field full index. This finding is confined to the inspected selected/public suppliers; it is not a claim about every filesystem file.

## Minimal honest separate writer contract

Use a distinct reviewed **parent metadata writer**, with its own original source/policy pin, to generate a bare, unsealed `id -> {kind, sha256, record_sha256}` JSON map. Do not label it a 28d output or embed a format/seal key in the map. Preserve the original validation exit/stdout/stderr as unsealed originals with their actual 28d/public-CLI provenance.

Require explicit parent-approved M2/source/R/F6/account/campaign bindings; the exact real `.yaml`/`.yml` inventory with original bytes/SHA; the original campaign summary and validation argv/exit/stdout/stderr pins; and an explicit quiescent, unchanged validated-snapshot attestation. Original validation stdout alone does not bind a later catalog snapshot. If snapshot continuity is unavailable, leave construction pending.

Read every catalogue body using the exact C/6a duplicate-key refusal and timestamp-as-string policy. Hash the same returned file bytes that are parsed; compute each whole-record digest with the original public `ensure_ascii=True`, sorted compact JSON convention. Refuse duplicate IDs, unreadable/nonmapping bodies, omitted/extra inventory paths, changed inode/content, or nonfinite/unsupported values. Reinventory and recheck original sources before success. Do not run Store, build SQLite or repeat full validation.

Create separate metadata custody that pins the bare index file SHA/semantic digest, original inventory and validation files, writer/source identities and the **inherited** validation/quiescence boundary. It must not claim independently repeated catalogue validation, normal trajectories, or numeric agreement. Fresh output stays outside source/raw/campaign paths, with explicit ownership, nonsymlink and bounded runtime guards. A separately reviewed source-read bound may exceed the compact index limit; that does not change any selected consumer or scientific budget.

The release builder was rechecked byte-for-byte: it uses `dispatch.attempt` and the stopped receipt's `dispatch_sha256`; it does not read `stopped.attempt`. No release compatibility fix is needed.
