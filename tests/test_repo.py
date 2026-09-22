"""Repository-level checks: copied drafts stay unchanged, dependencies stay minimal."""

import hashlib
import tomllib

from conftest import REPO


def test_hw_ensemble_copies_match_checksums():
    folder = REPO / "archevolve" / "hw_ensemble"
    lines = (folder / "SHA256SUMS").read_text().splitlines()
    assert lines, "SHA256SUMS is empty"
    for line in lines:
        digest, name = line.split(maxsplit=1)
        actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
        assert actual == digest, f"{name} changed since it was copied"


def test_dependencies_are_only_pyyaml_and_jsonschema():
    project = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]
    names = {dep.split(">")[0].split("=")[0].strip().lower() for dep in project["dependencies"]}
    assert names == {"pyyaml", "jsonschema"}
    assert project["requires-python"] == ">=3.12"
