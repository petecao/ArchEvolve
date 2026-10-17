# Ticket 10 ignored generated input retention

Dated 2026-10-07 ET. This archive retains three existing local ignored research inputs byte for byte. It does not rerun preparation, inference, evaluation or tests. Ticket 10 remains resolved; this is custody metadata rather than new scientific evidence.

The original preparation plan and receipt already reside in [the earlier retention archive](../10-ignored-preparation-retention-20261007/README.md), whose manifest identity is `281c951ce2e3f889deae2ed5ff8e40755783463775b9ccb15002345c67164852`. Their original file hashes are `141190de4102be58bd86fd905d2af3c1f4ff563f5c48f41984da3f1c513d6404` and `4a0a53660222552a9e164114a5e09d5471a6ff0e135be310ba23dad4116aa16e`. They are referenced here without duplicate copies. That historical plan remains `prepared` with `provider_launched=false`; this statement describes that preparation, separately from ticket 10's later archived actual inference.

The three input files complete the plan's exact `input_sha256s` set and its 101,164-byte input total:

| Original input | Bytes | Exact file SHA-256 |
|---|---:|---|
| characterization.json | 99,178 | `77d7e4101368ab29252695e4f8c6cdd52629f3dbe0d9be858862d5096b89ec00` |
| parameters.json | 1,750 | `b16f04ce73ad69fb25695e571ecff181129ae167bff9be236c0c1dbb1e600ebb` |
| profile.json | 236 | `0430c35f7a4c0d96f6c71db73f07810e55a19edd6053084d042767871ae9843a` |

Source-only inspection of `swdb/estimation_parameters.py` and its closed wire contract, plus passive JSON inspection, found sanitized structural projections: hashed research identities, scoped logical count/shape facts, recognized numerical parameter facts and closed profile kinds. The characterization contains five trial projections; parameters retain original known/inferred and unknown facts. These files contain no prompt/provider/authentication streams, credentials, source code, evaluator output, elapsed timing records or remote raw run artifacts. They do not establish new measurement, inference, accuracy or acceptance.

Each input's exact bytes equal the generator's original compact canonical serialization (sorted keys, ASCII escaping, finite numbers), and the resulting file SHA matches the original plan's input digest. The parameters' target hash and unknown array also match the original plan. No generator, contract validator, source import, Store, provider or scientific command was executed for this retention.

`original-unsealed-inventory.json` is the parent's exact original 3,271-byte five-file copy inventory, with `sealed=false` and no identity field. Its original `source_bodies_parsed_or_run=false` describes the earlier copy phase; the later passive inspection described above does not rewrite that historical statement. The new manifest seals this archive's byte-retention metadata only, without retroactively sealing the inventory or changing any original preparation file. Original ignored files and parent temporary copies remain unchanged. No worktree archival or cleanup was performed.

The incoming archive is based on integration `0bf8dc77a190a136e363e665b35c5158e958f316`; the scientific source checkpoint `f893fed400347ed23d92e917d8bde21b75e5375d` and estimator bundle `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3` remain unchanged. Apart from a dated pointer appended to ticket 10, no earlier tracked file, ticket status, map, progress, production source or canonical record is changed.
