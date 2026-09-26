"""Public capability/proposal checks; no fixture establishes acceleration. Updated 2026-09-25."""

import copy
import difflib
import hashlib
import json

import pytest
import yaml

from conftest import REPO, run_swdb


TARGET = "dx100-e4fc4af-4c"
REVISION = "e4fc4afdf894f295442cef3604667a469fab8e62"


def output(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def leaf(operation="dx100.mmio.v1.indirect-store-vector.i32", **extra):
    return {"operation": operation, "interface": "dx100-mmio",
            "interface_version": "1.0-e4fc4af", "model_revision": REVISION, **extra}


def source_only_target(records):
    """Keep source-only contract cases independent of actual lab build progress."""
    records.copy_repo()
    target = records.read(f"hardware_targets/{TARGET}.yaml")
    target['backend'].update(readiness='source_supported', build_evidence=[])
    target['execution_host'] = None
    records.write(f"hardware_targets/{TARGET}.yaml", target)
    return target


def test_public_capabilities_distinguish_source_from_executable(records):
    source_only_target(records)
    data = output(records.swdb("capabilities", TARGET, "--format", "json"))
    assert data["target"]["backend"]["readiness"] == "source_supported"
    assert data["target"]["backend"]["build_evidence"] == []
    assert data["target"]["execution_host"] is None
    ops = {op["id"]: op for op in data["operations"]}
    scatter = ops["dx100.mmio.v1.indirect-store-vector.i32"]
    assert scatter["semantics"]["returns_old_value"]["value"] is True
    assert scatter["semantics"]["cpu_atomic"]["state"] == "unknown"
    for op in ops.values():
        assert op["implementation_evidence"][0]["sha256"]
        for evidence in op["declaration_evidence"]:
            path = REPO / "apps/dx100" / evidence["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == evidence["sha256"]
    assert output(records.swdb("capabilities", TARGET, "--format", "json")) == data
    assert records.swdb("capabilities", "unknown-target").returncode == 1


@pytest.fixture
def proposal_case(records, tmp_path):
    source_only_target(records)
    runs = tmp_path / "runs"
    source = output(records.swdb("source-snapshot", "gapbs-bfs-do", "--id", "source",
                                 "--runs-dir", runs, "--format", "json"))
    output(records.swdb("fixture-package", "source", "--id", "package", "--format", "json"))
    before = (REPO / "apps/gapbs/src/bfs.cc").read_text()
    after = "// Capability contract fixture; source edit only.\n" + before
    patch = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                       fromfile="a/src/bfs.cc", tofile="b/src/bfs.cc"))
    request = {"message_version": "1.0", "id": "proposal", "profile_package": "package",
               "implementation": "gapbs-bfs-do", "source_snapshot": "source",
               "regions": [source["regions"][0]["id"]],
               "source_sha256": source["artifact"]["sha256"], "intent": "Add an explanatory source comment.",
               "producer": {"name": "capability-fixture", "role": "hw", "test_client": True},
               "constraints": {"editable_files": ["src/bfs.cc"], "preserve_correctness": True, "preserve_roi": True},
               "payload": {"kind": "patch", "content": patch}, "hardware_target": TARGET,
               "required_operations": [leaf()]}

    def submit(change=None):
        current = copy.deepcopy(request)
        if change:
            change(current)
        path = tmp_path / "proposal.yaml"
        path.write_text(yaml.safe_dump(current))
        command = records.swdb("submit", path, "--runs-dir", runs, "--format", "json")
        assert command.returncode in {0, 1}, command.stderr
        result = json.loads(command.stdout)
        retrieved = output(records.swdb("get", "proposal", "--format", "json"))
        assert retrieved == result
        return result
    return submit


def test_supported_sequence_creates_candidate_without_executable_claim(proposal_case):
    def change(request):
        request["required_operations"] = [{"wrapper": "parent-scatter", "requires": [
            leaf(semantics={"returns_old_value": True, "masked": True})]}]
    result = proposal_case(change)
    assert result["outcome"]["state"] == "candidate_created"
    assert result["candidate"]


@pytest.mark.parametrize("kind,reason", [
    ("unknown", "unsupported"), ("version", "conflicting"),
    ("model", "conflicting"), ("unknown-semantic", "unsupported or unknown"),
    ("value", "conflicts"), ("bool-int", "conflicts"),
    ("wrapper", "unsupported"), ("empty-wrapper", "nonempty"),
    ("executable", "no identified executable"), ("target", "exact hardware_target"),
    ("alternate-backend", "unresolved implementing backend"),
])
def test_requirements_fail_durably_before_candidate_creation(proposal_case, records, kind, reason):
    def change(request):
        op = request["required_operations"][0]
        if kind == "unknown":
            op["operation"] = "invented-cas"
        elif kind == "version":
            op["interface_version"] = "9.0"
        elif kind == "model":
            op["model_revision"] = "0" * 40
        elif kind == "unknown-semantic":
            op["semantics"] = {"cpu_atomic": True}
        elif kind == "value":
            op["semantics"] = {"returns_old_value": False}
        elif kind == "bool-int":
            op["semantics"] = {"returns_old_value": 1}
        elif kind == "wrapper":
            request["required_operations"] = [{"wrapper": "declared-cas", "requires": [leaf("invented-cas")]}]
        elif kind == "empty-wrapper":
            request["required_operations"] = [{"wrapper": "declared-cas", "requires": []}]
        elif kind == "executable":
            request["require_executable_backend"] = True
        elif kind == "target":
            request.pop("hardware_target")
        elif kind == "alternate-backend":
            target = records.read(f"hardware_targets/{TARGET}.yaml")
            target["backend"]["id"] = "unimplemented-alternate-model"
            records.write(f"hardware_targets/{TARGET}.yaml", target)
    result = proposal_case(change)
    assert result["outcome"]["state"] == "unresolved"
    assert result["outcome"]["stage"] == "capabilities"
    assert reason in result["outcome"]["reason"]
    assert "candidate" not in result


def test_built_target_requires_build_receipt_and_real_operation_references(records, tmp_path):
    target = source_only_target(records)
    target["backend"]["readiness"] = "built"
    path = tmp_path / "target.yaml"
    path.write_text(yaml.safe_dump(target))
    result = run_swdb("validate", "--records", records.path)
    assert result.returncode == 0, result.stderr
    records.write(f"hardware_targets/{TARGET}.yaml", target)
    result = records.validate()
    assert result.returncode != 0 and "build_evidence" in result.stdout + result.stderr
    target["backend"]["readiness"] = "source_supported"
    target["operations"] = ["unregistered-generated-wrapper"]
    records.write(f"hardware_targets/{TARGET}.yaml", target)
    result = records.validate()
    assert result.returncode != 0 and "does not exist" in result.stdout + result.stderr
