"""`swdb validate` on application records: each rule has a passing and a failing case."""

from conftest import FIXTURES, load_fixture, run_swdb


def assert_rejected(result, *fragments):
    assert result.returncode == 1, result.stdout + result.stderr
    for fragment in fragments:
        assert fragment in result.stderr, f"{fragment!r} not in stderr:\n{result.stderr}"


def test_repo_records_are_valid():
    result = run_swdb("validate")
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_valid_application_passes(records):
    records.write("applications/app.yaml", load_fixture("application.yaml"))
    result = records.validate()
    assert result.returncode == 0, result.stderr
    assert "OK: 1 record" in result.stdout


def test_empty_records_folder_passes(records):
    result = records.validate()
    assert result.returncode == 0, result.stderr
    assert "OK: 0 record" in result.stdout


def test_missing_records_folder_is_a_usage_error(tmp_path):
    result = run_swdb("validate", "--records", tmp_path / "nowhere")
    assert result.returncode == 2
    assert "not found" in result.stderr


def test_missing_required_field_fails(records):
    data = load_fixture("application.yaml")
    del data["source"]["commit"]
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "applications/app.yaml", "source.commit", "required")


def test_missing_top_level_field_fails(records):
    data = load_fixture("application.yaml")
    del data["license"]
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "applications/app.yaml", "license", "required")


def test_unknown_top_level_key_fails(records):
    data = load_fixture("application.yaml")
    data["colour"] = "red"
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "applications/app.yaml", "colour", "unknown key")


def test_unknown_nested_key_fails(records):
    data = load_fixture("application.yaml")
    data["source"]["branch"] = "main"
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "source.branch", "unknown key")


def test_unknown_keys_under_extensions_pass(records):
    data = load_fixture("application.yaml")
    data["extensions"] = {"trial_field": {"anything": [1, 2, 3]}}
    records.write("applications/app.yaml", data)
    assert records.validate().returncode == 0


def test_kind_outside_vocabulary_fails(records):
    data = load_fixture("application.yaml")
    data["kind"] = "applicaton"
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "kind", "not in vocabulary record_kinds")


def test_provenance_kind_outside_vocabulary_fails(records):
    data = load_fixture("application.yaml")
    data["provenance"][0]["kind"] = "rumor"
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "provenance[0].kind", "not in vocabulary provenance_kinds")


def test_domain_outside_vocabulary_fails(records):
    data = load_fixture("application.yaml")
    data["domain"] = "astrology"
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "domain", "not in vocabulary domains")


def test_short_commit_fails(records):
    data = load_fixture("application.yaml")
    data["source"]["commit"] = "0123abc"
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "source.commit")


def test_unsupported_schema_version_fails(records):
    data = load_fixture("application.yaml")
    data["schema_version"] = "9.0"
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "schema_version")


def test_bare_yaml_date_passes(records):
    # YAML would turn a bare 2026-09-22 into a date object; the tool keeps it as text.
    text = (FIXTURES / "application.yaml").read_text()
    assert "\ncreated: 2026-09-22\n" in text
    records.write_text("applications/app.yaml", text)
    assert records.validate().returncode == 0


def test_malformed_date_fails(records):
    data = load_fixture("application.yaml")
    data["created"] = "22-09-2026"
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "created")


def test_deprecated_record_must_name_replacement(records):
    data = load_fixture("application.yaml")
    data["status"] = "deprecated"
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "deprecated_by", "replacement")


def test_deprecated_record_with_replacement_passes(records):
    data = load_fixture("application.yaml")
    data["status"] = "deprecated"
    data["deprecated_by"] = "fixture-app-v2"
    records.write("applications/app.yaml", data)
    replacement = load_fixture("application.yaml")
    replacement["id"] = "fixture-app-v2"
    records.write("applications/app-v2.yaml", replacement)
    assert records.validate().returncode == 0


def test_deprecated_record_with_missing_replacement_fails(records):
    data = load_fixture("application.yaml")
    data["status"] = "deprecated"
    data["deprecated_by"] = "fixture-app-v2"
    records.write("applications/app.yaml", data)
    assert_rejected(records.validate(), "deprecated_by", "does not exist")


def test_malformed_yaml_fails(records):
    records.write_text("applications/app.yaml", "kind: [unclosed\n")
    assert_rejected(records.validate(), "applications/app.yaml", "not valid YAML")


def test_duplicate_yaml_key_fails(records):
    text = "kind: application\nkind: application\n"
    records.write_text("applications/app.yaml", text)
    assert_rejected(records.validate(), "applications/app.yaml", "duplicate key")


def test_non_mapping_record_fails(records):
    records.write_text("applications/app.yaml", "- a\n- b\n")
    assert_rejected(records.validate(), "applications/app.yaml", "mapping")


def test_every_bad_file_is_reported(records):
    first = load_fixture("application.yaml")
    del first["license"]
    second = load_fixture("application.yaml")
    second["id"] = "fixture-app-2"
    second["colour"] = "red"
    records.write("applications/a.yaml", first)
    records.write("applications/b.yaml", second)
    assert_rejected(records.validate(), "applications/a.yaml", "applications/b.yaml", "2 error(s) in 2 file(s)")
