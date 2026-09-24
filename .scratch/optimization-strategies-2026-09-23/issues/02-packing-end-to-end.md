# 02 — Packing, end to end

Created: 2026-09-23
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** the SW Ensemble Agent can ask which access-pattern strategies are
legal for one access pattern, and where one strategy could apply, with `packing` as the
first real strategy (ADR 0004).

- [ ] The strategy record kind: target (access_pattern for now), effect with the `reshape` and `add_pattern` kinds, parameters, preconditions (`requires_shapes`, `requires_semantics`, `unchecked`), `benefits_when` (`basis: reported` plus a provenance ref), and at least one source.
- [ ] Rules, each with a passing and a failing fixture: effect items match their kind's shape; precondition fields and values exist; benefit items are reported and sourced; a duplicate strategy (same target and effect set, parameters ignored) fails and names the existing one.
- [ ] `swdb add` and `swdb add --agent` write strategies to their canonical folder (draft and `agent_run` for agents).
- [ ] The `packing` seed record, with its source verified before citing (spec Further Notes). Unverifiable claims are left out.
- [ ] `swdb build` includes strategies. `swdb strategies --pattern <impl>/<pattern>` returns each access-pattern strategy with `outcome` (legal / illegal / undetermined), `reasons`, `unknown_fields`, `check_by_hand` and `benefits_when`, as YAML or JSON.
- [ ] `swdb find --strategy <id>` returns the access patterns where it is legal or undetermined (illegal ones are left out).
- [ ] Tests cover all three outcomes, including a semantic value with basis unknown. The new fields and the query are documented in the v0.3 format doc and the query doc.

## Comments
