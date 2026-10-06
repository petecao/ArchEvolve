# 69 — Profiling role schema against the providers' strict mode

Created: 2026-10-04 21:15 ET (by the final code review, 2026-10-04, P3 `swdb/annotation.py:21`)
Updated: 2026-10-05 17:20 ET (tracker hygiene, code review: Blocked by line); 2026-10-04 21:15 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`; [code review](../code-review-2026-10-04.md), [36](36-annotate-and-score.md)

**What to build:** the profiling role's output schema is checked against the same strict-mode
rules as the other role schemas (`4e2a68b`), including its `minLength`, `minItems` and `minimum`
keywords, and is fixed if needed.

## Acceptance

- [x] `minLength`, `minItems` and `minimum` are verified against the strict mode that the profiling
  role actually runs under.
- [x] The schema is fixed if needed. The existing all-roles test covers it.

## Answer

Resolved 2026-10-04 21:15 ET by the agent. Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

**Verdict: no schema change is needed for the provider this role runs on (Codex).** The evidence is
from real sessions, not from documentation:
- **Refused.** Annotation a2 (2026-10-03) was refused 400:
  `invalid_json_schema: uniqueItems is not permitted for index_provenance`
  ([failure summary](../evaluation/annotation-a1-a2-failure-summary.json)). So the API does reject an
  unsupported keyword. The Codex transport (`provider_adapters._codex_transport_schema`) has omitted
  `uniqueItems` since then. Local validation keeps it.
- **Accepted.** Annotation a3 (completed 2026-10-03 09:08 ET, codex-cli 0.153.0, gpt-5.6-sol, xhigh)
  sent wire schema sha256 `3928d885d99918a2…`
  ([operator audit](../evaluation/annotation-a3/annotation-a3.operator-audit.json)). The session
  completed with all seven predictions. That schema contains `minLength`, `minItems`, `minimum` and
  a type-less `enum`.
- **Same bytes today.** Today's profiling wire schema has the same sha256, so the keywords were
  accepted on exactly these bytes.

**What changed (the check, not the schema).**
- `swdb/provider_roles.py` `strict_problems` now also checks keywords:
  - `STRICT_ACCEPTED_KEYWORDS`: the shape keywords plus `enum`, `minItems`, `minLength` and `minimum`;
  - `STRICT_REFUSED_KEYWORDS`: `uniqueItems`;
  - any other keyword is reported as not verified.
- `wire_schema(schema, kind)` gives the schema as the provider receives it.
- `tests/test_provider_role_schemas.py`:
  - every production role's Codex wire schema passes, keywords included (8 roles);
  - the profiling wire schema still has the accepted a3 sha256, and its semantic schema fails only
    on `uniqueItems`, so a schema change voids the evidence and the test asks for a new check;
  - an unverified keyword (`maxLength`) and a refused one are both named.
- 11 passed; with `test_statement_annotation.py` 35, and `test_provider_pins.py` + `test_provider_login.py` 44 passed.

**Open (not verified).** The Claude adapter passes the semantic schema unchanged
(`--json-schema`), including `uniqueItems`. The profiling role has never run on Claude, so its
keyword support is unverified. Run one real Claude profiling session before using that path.
