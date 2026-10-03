# 40 — BC on the native evaluator (code)

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 38
**Spec:** `../spec.md`

**What to build:** BC (kernel gapbs-bc) plugs into the native evaluator like BFS, tested with fixtures.

## Acceptance

- [ ] A DX100 BC implementation record and a scalar-only BC snapshot derivation (the authors' accelerated BC code removed) exist.
- [ ] Kronecker and uniform BC workloads can be registered; native evaluation uses BCVerifier; BC protocols freeze.
- [ ] Fixture tests pass; BFS behavior is unchanged.

## Comments
