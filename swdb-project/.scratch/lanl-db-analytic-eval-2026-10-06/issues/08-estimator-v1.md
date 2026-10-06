# 08 — Estimator v1: mechanism models, per-region report and the estimate protocol

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03, 06
**Spec:** `../spec.md`
**Time estimate:** 1–2 days

**What to build:** Mechanism models (each one hardware behavior: reorder-window row counting, cache fit, fetch queue, tile staging, offload setup, compute throughput, requests in flight) composed per target description into per-region bounds; the estimate is the largest bound plus overhead, summed over regions with the serial remainder (D21). Emit the per-region report and freeze estimate protocols (estimator version and target-description sha256).

## Acceptance

- [ ] Unit tests on synthetic regions with known bounds.
- [ ] Report names the limiting bound per region from `vocab/bottleneck_classes.yaml`, adding values for limits it lacks (accelerator throughput, offload overhead) through the vocabulary's normal change process.
- [ ] No kernel-specific or target-specific code: a new kernel or target needs only records and a description (D22).
- [ ] An `unknown` parameter makes the bound that needs it `unknown`, never zero.
- [ ] Estimates carry basis `estimated`; estimate protocols freeze like other protocols.
