"""Every production role output schema passes the providers' strict structured-output check.

Created: 2026-10-04 ET (final code review). Ticket 57's campaign a1 lost its provider calls
to a free-form `knobs` object; the synthesis role's free-form `entry` had the same defect.
Updated: 2026-10-04 ET (ticket 69: keywords checked on the wire schema).
"""

import pytest

from swdb import annotation, campaign, provider_roles  # noqa: F401  (annotation registers "profiling")


def production_roles():
    roles = dict(provider_roles.ROLES)
    roles.update({"extensa_" + name: role for name, role in campaign._roles().items()})
    return roles


@pytest.mark.parametrize("name", sorted(production_roles()))
def test_role_output_schema_is_strict(name):
    # Ticket 69 (2026-10-04 ET): the schema as Codex receives it, keywords included.
    assert provider_roles.strict_problems(provider_roles.wire_schema(production_roles()[name].output_schema)) == []


def test_profiling_wire_schema_is_the_one_strict_mode_accepted():
    """Ticket 69: minLength, minItems and minimum were accepted in a real strict session.

    Annotation a3 (2026-10-03 09:08 ET, codex-cli 0.153.0, gpt-5.6-sol) completed with this
    exact wire schema; annotation a2 was refused with "uniqueItems is not permitted". A change to
    the profiling schema voids that evidence, and this test then asks for a new check.
    """
    import hashlib
    import json
    from swdb import annotation
    semantic = annotation.OUTPUT_SCHEMA
    wire = provider_roles.wire_schema(semantic)
    assert hashlib.sha256(json.dumps(wire).encode()).hexdigest() == \
        "3928d885d99918a2dae55546682d1cdcde7e537a2455459a19a802659cc84796"
    assert provider_roles.strict_problems(wire) == []
    # The semantic schema keeps uniqueItems for local validation; strict mode refuses it.
    assert provider_roles.strict_problems(semantic) == [
        "$.statements[].index_provenance: keyword uniqueItems is refused by strict mode"]
    # Claude receives the semantic schema; its keyword support is not verified.
    assert provider_roles.wire_schema(semantic, "claude") is semantic


def test_strict_check_names_unverified_and_refused_keywords():
    schema = {"type": "object", "additionalProperties": False, "required": ["a", "b"],
              "properties": {"a": {"type": "string", "maxLength": 3, "minLength": 1},
                             "b": {"type": "array", "uniqueItems": True, "items": {"type": "integer", "minimum": 1}}}}
    assert provider_roles.strict_problems(schema) == [
        "$.a: keyword maxLength is not verified against strict mode",
        "$.b: keyword uniqueItems is refused by strict mode"]


def test_strict_check_names_free_form_and_open_objects():
    loose = {"type": "object", "additionalProperties": False, "required": ["entry", "rows"],
             "properties": {"entry": {"type": "object"},
                            "rows": {"type": "array", "items": {
                                "type": "object", "required": ["a"],
                                "properties": {"a": {"type": "string"}, "b": {"type": "string"}}}}}}
    problems = provider_roles.strict_problems(loose)
    assert "$.entry: object without additionalProperties: false" in problems
    assert "$.entry: free-form object without properties" in problems
    assert "$.rows[]: object without additionalProperties: false" in problems
    assert "$.rows[]: required must list every property" in problems
