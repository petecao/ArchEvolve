"""Every production role output schema passes the providers' strict structured-output check.

Created: 2026-10-04 ET (final code review). Ticket 57's campaign a1 lost its provider calls
to a free-form `knobs` object; the synthesis role's free-form `entry` had the same defect.
"""

import pytest

from swdb import annotation, campaign, provider_roles  # noqa: F401  (annotation registers "profiling")


def production_roles():
    roles = dict(provider_roles.ROLES)
    roles.update({"extensa_" + name: role for name, role in campaign._roles().items()})
    return roles


@pytest.mark.parametrize("name", sorted(production_roles()))
def test_role_output_schema_is_strict(name):
    assert provider_roles.strict_problems(production_roles()[name].output_schema) == []


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
