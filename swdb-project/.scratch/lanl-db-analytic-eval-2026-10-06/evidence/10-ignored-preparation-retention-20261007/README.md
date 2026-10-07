# Retained ticket 10 ignored preparation — 2026-10-07

These two JSONs are historical local preparation snapshots, retained byte for byte before eventual managed-worktree archival. Both still say `state: prepared` and `provider_launched: false`; this retention is not a new provider run, execution receipt, acceptance or result. The source ignored files and their earlier temporary copies remain untouched.

The original inventory was captured at 2026-10-07T09:41:39.012438+00:00 and is copied verbatim as `original-unsealed-inventory.json`. It has no original identity seal. The new manifest pins its exact bytes and canonical JSON digest without modifying or retroactively sealing that historical inventory. The new manifest also pins both original ignored source paths and earlier retained copy paths, file sizes/SHA-256s and preserved preparation labels.

`ticket10-compatible-preparation-receipt-a1.json` is 12,643 bytes with SHA-256 `4a0a53660222552a9e164114a5e09d5471a6ff0e135be310ba23dad4116aa16e`. `ticket10-compatible-preparation-a1/plan.json` is 12,642 bytes with SHA-256 `141190de4102be58bd86fd905d2af3c1f4ff563f5c48f41984da3f1c513d6404`. Their original serialization and distinct trailing bytes are preserved.

The first SHA is already retained as the `prepare.stdout` file pin in the separate actual successful postfill custody `../10-estimation-role-postfill-custody-mbit10-20261006-a2.json`. That historical remote success remains separate from these local preparation objects; no state is promoted or rewritten by this archive.

The archive is based on checkpoint `f35cf2760d936a3e72dd230672a6be0ca7341894` in the owned ticket 17 branch. Only this five-file retention folder is added. Issues, map, progress, canonical records, source C/F6, library, controls and other archives remain unchanged. No test, Store, provider, native measurement, remote action, worktree archive or cleanup was performed for this retention. Parent review and separate merge approval remain pending.
