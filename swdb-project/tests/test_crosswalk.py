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
