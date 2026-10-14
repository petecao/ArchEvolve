# Promotion review: ten DX100 MMIO lowerings and their intrinsics (re-pin)

Written 2026-10-13 23:06 ET by a Claude Code agent. Yan-Ru Jhou delegated the review in chat on
2026-10-13 ("review those promotion for me and then if they are ok, then promote them").
This review was checked at `yanrujhou_main` `eaf7538c`.

**Verdict: promote all 20 entries.** Their only change since the 2026-10-03 reviews is a
catalog hash pin, and every entry has a fresh passing certificate.

## What was reviewed

- **The 10 lowerings:** `lowering.dxc_{alu_scalar,const_i32,gather,range_loop,session_begin,stream_load,thread_context,tile_pointer,tile_size,wait}.dx100-mmio.1.0-e4fc4af`
- **The 10 intrinsics:** `intrinsic.dxc_*` with the same names.

All 20 currently report `tier: experimental` and `status: certified`. The library validates
with no issues.

## Why the old reviews are stale

- **The diff:** I compared all 20 entry files between the review commit `8959b4df`
  (2026-10-03) and `eaf7538c`. That is 40 lines changed, every one of them the same change:
  - `catalog.sha256` and `catalog_sha256`: `adf17f3e…` → `7adeb7f9…`
- **What the diff leaves alone:** each entry's operations, source pins, `discharge_mode`
  and lowering text.
- **The catalog side:** for design `dx100-artifact-e4fc4af`, the change from `adf17f3e`
  (`a8710cc2`) to `7adeb7f9` is additive only:
  - added: `internal_mechanisms`;
  - extended: `source_refs`.
  - Nothing the lowerings bind was edited or removed. The other catalog changes in that
    range (4849bcdc and earlier) touch other designs.

## Certification evidence (lowering procedure 1.2, Mac, functional model, no gem5)

| Lowering | Certificate | Matrix cells | Negative controls |
|---|---|---|---|
| dxc_alu_scalar | certification.fa4d4b18… | 2/2 passed | 2/2 rejected |
| dxc_const_i32 | certification.a8dd3d3c… | 2/2 | 4/4 |
| dxc_gather | certification.beba4c44… | 2/2 | 14/14 |
| dxc_range_loop | certification.62138b1b… | 2/2 | 6/6 |
| dxc_session_begin | certification.6ac1a59b… | 2/2 | 2/2 |
| dxc_stream_load | certification.b649a1a1… | 2/2 | 4/4 |
| dxc_thread_context | certification.c4bc96f5… | 2/2 | 4/4 |
| dxc_tile_pointer | certification.3305ce37… | 2/2 | 2/2 |
| dxc_tile_size | certification.04acbece… | 2/2 | 2/2 |
| dxc_wait | certification.a8b8316f… | 4/4 | 6/6 |

Every certificate has verdict `certified`, `evidence_basis: simulated`, and is current for its
entry's content hash (commit `9c7ebc2d`). Each intrinsic is promoted on its lowering's
certificate, which is how `swdb promote` works for intrinsics.

## Limits of this review

- **Evidence is simulated.** It comes from the strict-layer functional model. That is the
  same evidence basis as the 2026-10-03 reviews, not gem5 or hardware.
- **ADR 0013 stands.** The shared tier does not let gem5-backed records into ArchEvolve
  mode.
- **Recording.** The promotions are recorded with `performed_by: agent`, with Yan-Ru Jhou as
  `delegated_by`.
