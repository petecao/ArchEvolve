"""Crosswalk validation through the public validate command. Created 2026-10-06 ET."""

import json

from conftest import run_swdb


def draft_crosswalk():
    return {
        "schema_version": "0.1",
        "crosswalk_version": 0,
        "id": "lanl-main-crosswalk-v0",
        "date": "2026-10-06",
        "source_deck": {
            "filename": "ArchEvolve-project-overview.pdf",
            "date": "2026-10-06",
            "sha256": "0" * 64,
        },
        "rows": [{
            "table_label": "Kernel information",
            "table_identifier": None,
            "field_label": None,
            "field_identifier": None,
            "disposition": "proposed",
            "research": [{"record_kind": "kernel", "field": None}],
            "status": "unverified",
            "source_slide": 8,
            "note": "A label from the slide; the SQL schema has not been seen.",
        }],
        "separable_extension": [{
            "concept": "optimization strategies",
            "research": [{"record_kind": "strategy", "field": None}],
            "status": "unverified",
            "source_slide": 8,
            "note": "No counterpart is visible in the slide.",
        }],
    }


def validate_crosswalk(records, tmp_path, document):
    path = tmp_path / "crosswalk.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return run_swdb("validate", "--records", records.path, "--crosswalk", path)


def test_crosswalk_cannot_claim_verified_mapping(records, tmp_path):
    document = draft_crosswalk()
    document["rows"][0]["status"] = "verified"
    result = validate_crosswalk(records, tmp_path, document)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "rows[0].status" in result.stderr
    assert "unverified" in result.stderr


def test_crosswalk_requires_the_slide_for_every_mapping(records, tmp_path):
    document = draft_crosswalk()
    document["rows"][0]["source_slide"] = 7
    result = validate_crosswalk(records, tmp_path, document)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "rows[0].source_slide" in result.stderr


def test_crosswalk_refuses_an_unknown_format_version(records, tmp_path):
    document = draft_crosswalk()
    document["schema_version"] = "999.0"
    result = validate_crosswalk(records, tmp_path, document)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "schema_version" in result.stderr


def test_extension_concepts_cannot_claim_verified_absence(records, tmp_path):
    document = draft_crosswalk()
    document["separable_extension"][0]["status"] = "verified"
    result = validate_crosswalk(records, tmp_path, document)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "separable_extension[0].status" in result.stderr


def test_crosswalk_requires_an_explicit_mapping_destination(records, tmp_path):
    document = draft_crosswalk()
    document["rows"][0].pop("research")
    result = validate_crosswalk(records, tmp_path, document)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "research" in result.stderr


def test_slide_crosswalk_v0_validates_as_a_standalone_document(records):
    from conftest import REPO

    result = run_swdb("validate", "--records", records.path, "--crosswalk",
                      REPO / "docs/compatibility/lanl-crosswalk-v0.yaml")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "crosswalk valid" in result.stdout


def test_crosswalk_refuses_an_invented_research_record_kind(records, tmp_path):
    document = draft_crosswalk()
    document["rows"][0]["research"][0]["record_kind"] = "invented_kind"
    result = validate_crosswalk(records, tmp_path, document)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "record_kind" in result.stderr


def test_crosswalk_record_kinds_match_the_store():
    # 2026-10-09 ET: the kind enum was a 2026-10-06 snapshot; record kinds added later
    # could not be named. It must track the store's kinds.
    from conftest import REPO
    from swdb.store import PLURAL
    schema = json.loads((REPO / "schemas/compatibility/main_crosswalk.schema.json").read_text())
    assert set(schema["$defs"]["target"]["properties"]["record_kind"]["enum"]) == set(PLURAL)


def _schema_has_field(schema, root, parts):
    """Whether a dotted record field path exists in a JSON schema (through $ref, combinators, items)."""
    if not parts:
        return True
    if "$ref" in schema:
        target = root
        for key in schema["$ref"].removeprefix("#/").split("/"):
            target = target[key]
        return _schema_has_field(target, root, parts)
    child = schema.get("properties", {}).get(parts[0])
    if isinstance(child, dict) and _schema_has_field(child, root, parts[1:]):
        return True
    options = [option for key in ("allOf", "anyOf", "oneOf") for option in schema.get(key, [])]
    if isinstance(schema.get("items"), dict):
        options.append(schema["items"])
    return any(_schema_has_field(option, root, parts) for option in options)


def test_every_crosswalk_field_exists_in_its_record_schema():
    from conftest import REPO
    from swdb import yamlio
    crosswalk = yamlio.load(REPO / "docs/compatibility/lanl-crosswalk-v0.yaml")
    targets = [target for row in crosswalk["rows"] + crosswalk["separable_extension"] for target in row["research"]]
    missing = []
    for target in targets:
        if target["field"] is None:
            continue
        schema = json.loads((REPO / "schemas" / f"{target['record_kind']}.schema.json").read_text())
        if not _schema_has_field(schema, schema, target["field"].split(".")):
            missing.append(f"{target['record_kind']}.{target['field']}")
    assert not missing, missing
    kernel = json.loads((REPO / "schemas/kernel.schema.json").read_text())
    assert not _schema_has_field(kernel, kernel, ["no_such_field"])
