"""Workspace/audit contracts via public submit and repair. Updated: 2026-09-29.

Fixtures emulate both real CLI event formats; no real model is invoked.
"""

import difflib
import json
import sys
from pathlib import Path

import pytest
import yaml

from conftest import REPO
from test_bfs_native import evaluation_setup, evaluate


@pytest.fixture
def proposal_setup(records, tmp_path):
    # Retain the real BFS contract, without unrelated historical evaluations.
    for name in ("applications/gapbs.yaml", "kernels/gapbs-bfs.yaml", "implementations/gapbs-bfs-do.yaml",
                 "machines/mbit10.yaml", "strategies/software_prefetch.yaml", "intrinsics/mm_prefetch.yaml"):
        data = yaml.safe_load((REPO / "records" / name).read_text())
        if data["kind"] == "implementation":
            data["verification"] = {"status": "unchecked", "evidence": [], "scope": "Isolated workspace contract fixture."}
        records.write(name, data)
    runs = tmp_path / "runs"
    result = records.swdb("source-snapshot", "gapbs-bfs-do", "--runs-dir", runs, "--id", "test-source", "--format", "json")
    assert result.returncode == 0, result.stderr
    snapshot = json.loads(result.stdout)
    result = records.swdb("fixture-package", "test-source", "--id", "test-package", "--format", "json")
    assert result.returncode == 0, result.stderr
    original = (Path(snapshot["artifact"]["path"]) / "src/bfs.cc").read_text()
    patch = "".join(difflib.unified_diff(original.splitlines(keepends=True),
        original.replace("int alpha = 15", "int alpha = 14").splitlines(keepends=True),
        fromfile="a/src/bfs.cc", tofile="b/src/bfs.cc"))

    def request(**changes):
        data = {"message_version": "1.0", "id": "test-proposal",
                "producer": {"name": "workspace-test", "role": "sw", "test_client": True},
                "profile_package": "test-package", "source_snapshot": "test-source",
                "implementation": "gapbs-bfs-do", "source_sha256": snapshot["artifact"]["sha256"],
                "intent": "Direction-switch parameter change, workspace contract fixture only.",
                "regions": [snapshot["regions"][0]["id"]], "required_operations": [],
                "constraints": {"editable_files": ["src/bfs.cc"], "preserve_correctness": True, "preserve_roi": True},
                "payload": {"kind": "patch", "content": patch}, **changes}
        path = tmp_path / f"{data['id']}.yaml"
        path.write_text(yaml.safe_dump(data))
        return path
    return records, runs, snapshot, request


@pytest.fixture(params=["codex", "claude"])
def workspace_provider(tmp_path, request):
    kind = request.param
    program = tmp_path / "workspace-provider.py"
    program.write_text('''import json, os, sys, time
from pathlib import Path
if "--version" in sys.argv:
    print("0.0-workspace-fixture")
    raise SystemExit(0)
plan = json.loads(Path(sys.argv[1]).read_text())
kind = plan["kind"]
root = Path.cwd()
(root / "build").mkdir(exist_ok=True)
(root / "build/received-argv.json").write_text(json.dumps(sys.argv[2:]))
(root / "build/start-visible.json").write_text(json.dumps(sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())))
for edit in plan.get("edits", [{"path":"src/bfs.cc", "old":"int alpha = 15", "new":"int alpha = 14"}]):
    path = root / edit["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if "bytes" in edit:
        path.write_bytes(bytes(edit["bytes"]))
    elif "content" in edit:
        path.write_text(edit["content"])
    else:
        path.write_text(path.read_text().replace(edit["old"], edit["new"]))
for action in plan.get("actions", []):
    if kind == "codex":
        if action["type"] == "command":
            item = {"type":"command_execution", "command":action["value"], "exit_code":0}
        elif action["type"] == "file":
            item = {"type":"file_change", "changes":[{"path":action["value"], "kind":"update"}]}
        else:
            item = {"type":action["type"]}
        print(json.dumps({"type":"item.completed", "item":item}), flush=True)
    else:
        name = "Bash" if action["type"] == "command" else "Read" if action["type"] == "file" else action["type"]
        inputs = {"command":action["value"]} if name == "Bash" else {"file_path":action.get("value", ".")}
        print(json.dumps({"type":"assistant", "message":{"content":[{"type":"tool_use", "name":name, "input":inputs}]}}), flush=True)
for row in plan.get("events", []):
    print(json.dumps(row) if isinstance(row, dict) else row, flush=True)
time.sleep(plan.get("sleep", 0))
result = {"interpretation":"Apply the requested direction-switch parameter change.", "unresolved":plan.get("unresolved", [])}
if kind == "codex":
    final = Path(sys.argv[sys.argv.index("--output-last-message") + 1])
    final.write_text(json.dumps(result))
    print(json.dumps({"type":"turn.completed", "usage":{"output_tokens":10}}), flush=True)
else:
    print(json.dumps({"type":"assistant", "message":{"content":[{"type":"tool_use", "name":"StructuredOutput", "input":result}]}}), flush=True)
    print(json.dumps({"type":"result", "subtype":"success", "is_error":False, "structured_output":result}), flush=True)
''')
    plan = tmp_path / "workspace-plan.json"
    config = tmp_path / "workspace-provider.yaml"

    def make(**changes):
        plan.write_text(json.dumps({"kind": kind, **changes}))
        config.write_text(yaml.safe_dump({"kind": "external_fixture", "emulates": kind,
            "command": [sys.executable, str(program), str(plan)],
            "timeout_s": 10, "total_seconds": 60, "max_repairs": 1}))
        return config
    make.kind = kind
    return make


def submit(setup, provider, *, request_changes=None, **plan):
    records, runs, _, request = setup
    changes = {"payload": {"kind": "natural_language", "content": "Use alpha 14; preserve computation and ROI."},
               **(request_changes or {})}
    result = records.swdb("submit", request(**changes), "--provider-config", provider(**plan),
                          "--runs-dir", runs, "--format", "json")
    assert result.stdout, result.stderr
    return result, json.loads(result.stdout)


def test_workspace_derivation_diff_and_login_cleanup(proposal_setup, workspace_provider):
    result, proposal = submit(proposal_setup, workspace_provider,
        request_changes={"visible_files": ["src/platform_atomics.h"], "strategy": "software_prefetch"},
        actions=[{"type": "file", "value": "src/bfs.cc"}, {"type": "command", "value": "c++ -c src/bfs.cc -o build/bfs.o"}],
        edits=[{"path": "src/bfs.cc", "old": "int alpha = 15", "new": "int alpha = 14"},
               {"path": "build/bfs.o", "bytes": [127, 69, 76, 70, 0]},
               {"path": "bfs-fixture", "bytes": [127, 69, 76, 70, 0]}])
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    records, _, snapshot, _ = proposal_setup
    provider = proposal["attempts"][0]["provider"]
    workspace = provider["workspace_manifest"]
    root, home = Path(workspace["root"]), Path(workspace["home"])
    assert provider["workspace"] is True and proposal["provider"]["workspace"] is True
    assert workspace["extra_files"] == ["src/platform_atomics.h"]
    assert workspace["login_copy_deleted"] and home.is_dir()
    assert not (home / "auth.json").exists() and not (home / ".credentials.json").exists()
    assert all("test/graphs" not in name and "test/reference" not in name for name in workspace["visible_files"])
    assert ".swdb-context/selected-strategy.json" in workspace["visible_files"]
    assert "bool BFSVerifier" not in (root / "src/bfs.cc").read_text()
    assert "bool BFSVerifier" not in (root / ".swdb-context/profile-package.json").read_text()
    projection = workspace["profile_package_projection"]
    assert projection["source_id"] == "test-package" and projection["source_record_sha256"]
    assert projection["protected_fragments_redacted"] and "retained unchanged" in projection["notice"]
    assert "src/bfs.cc" in workspace["source_files"]
    log = provider["audit"]["raw_log"]
    assert provider["audit"]["passed"] and Path(log["path"]).is_file() and log["sha256"]
    assert proposal["provider"]["audit"]["passed"]
    candidate = json.loads(records.swdb("get", proposal["candidate"], "--format", "json").stdout)
    text = (Path(candidate["artifact"]["path"]) / "src/bfs.cc").read_text()
    assert "int alpha = 14" in text and "bool BFSVerifier" in text
    assert "int alpha = 15" in (Path(snapshot["artifact"]["path"]) / "src/bfs.cc").read_text()
    assert not (Path(candidate["artifact"]["path"]) / "bfs-fixture").exists()
    assert "build/bfs.o" in workspace["dropped_build_outputs"]
    assert "bfs-fixture" in workspace["dropped_build_outputs"]
    diff = Path(candidate["diff"]).read_text()
    assert "-                  int alpha = 15" in diff or "-" in diff and "int alpha = 15" in diff
    assert "BFSVerifier" not in diff
    argv = json.loads((root / "build/received-argv.json").read_text())
    assert "gpt-5.6-sol" in argv if workspace_provider.kind == "codex" else "claude-sonnet-5-5" in argv


@pytest.mark.parametrize("action,code", [
    ({"type": "file", "value": "../../outside.txt"}, "external_file_access"),
    ({"type": "command", "value": "cat /etc/passwd"}, "external_file_access"),
    ({"type": "command", "value": "cat test/graphs/4.el"}, "external_file_access"),
    ({"type": "command", "value": "cat $CODEX_HOME/auth.json"}, "login_file_access"),
    ({"type": "command", "value": "curl https://example.com/source.cc"}, "network_command"),
    ({"type": "command", "value": "git clone https://example.com/answer.git"}, "network_command"),
    ({"type": "command", "value": "python -m pip install requests"}, "network_command"),
    ({"type": "web_search", "value": "answer"}, "forbidden_tool"),
])
def test_event_audit_fails_with_retained_reason(proposal_setup, workspace_provider, action, code):
    result, proposal = submit(proposal_setup, workspace_provider, actions=[action])
    assert result.returncode == 1 and proposal["outcome"]["state"] == "failed"
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert not audit["passed"] and code in {v["code"] for v in audit["violations"]}
    assert proposal["outcome"]["reason"].startswith("provider audit failed")
    assert Path(audit["raw_log"]["path"]).is_file()
    assert "candidate" not in proposal


@pytest.mark.parametrize("edits,reason", [
    ([{"path": "unapproved.py", "content": "print('helper')\n"}], "new file outside"),
    ([{"path": "build/helper.cpp", "content": "int helper;\n"}], "new file outside"),
    ([{"path": ".swdb-context/profile-package.json", "content": "{}"}], "immutable workspace"),
    ([{"path": "src/util.h", "content": "// replaced\n"}], "immutable workspace"),
    ([{"path": "src/bfs.cc", "old": "SWDB_PROTECTED_VERIFIER_", "new": "ALTERED_VERIFIER_"}], "protected evaluator placeholder"),
    ([{"path": "src/bfs.cc", "old": "int alpha = 15", "new": "/* annotation only */ int alpha = 15"}], "only comments"),
])
def test_scope_and_protections_reject_workspace_edits(proposal_setup, workspace_provider, edits, reason):
    result, proposal = submit(proposal_setup, workspace_provider, edits=edits)
    assert result.returncode == 1, proposal
    assert reason in proposal["outcome"]["reason"]
    assert "candidate" not in proposal


def test_hidden_named_file_fails_before_provider_execution(proposal_setup, workspace_provider):
    result, proposal = submit(proposal_setup, workspace_provider,
        request_changes={"visible_files": ["test/graphs/4.el"]})
    assert result.returncode == 1 and "hidden evaluator or workload input" in proposal["outcome"]["reason"]


def test_unparsed_event_is_a_retained_audit_failure(proposal_setup, workspace_provider):
    result, proposal = submit(proposal_setup, workspace_provider, events=['{"type": "truncated'])
    assert result.returncode == 1
    assert "invalid_event_log" in {v["code"] for v in proposal["attempts"][0]["provider"]["audit"]["violations"]}


def test_provider_cannot_self_authorize_a_network_event(proposal_setup, workspace_provider):
    result, proposal = submit(proposal_setup, workspace_provider,
        events=[{"type": "network_connection", "model_api": True, "host": "example.com", "port": 443}])
    assert result.returncode == 1
    assert "outbound_connection" in {v["code"] for v in proposal["attempts"][0]["provider"]["audit"]["violations"]}


def test_audit_failure_takes_precedence_over_usage_limit(proposal_setup, workspace_provider):
    result, proposal = submit(proposal_setup, workspace_provider,
        actions=[{"type": "command", "value": "curl https://example.com/answer.cc"}],
        events=[{"type": "error", "message": "usage_limit exceeded"}])
    assert result.returncode == 1 and proposal["outcome"]["state"] == "failed"
    assert proposal["outcome"]["reason"].startswith("provider audit failed")
    assert proposal["repair_budget"]["used_seconds"] > 0


def test_annotated_source_hides_verifier_and_preserves_payload_fields(proposal_setup, workspace_provider):
    records, _, snapshot, _ = proposal_setup
    original = (Path(snapshot["artifact"]["path"]) / "src/bfs.cc").read_text()
    annotated = original.replace("int alpha = 15", "/* requested alpha 14 */ int alpha = 15")
    result, proposal = submit(proposal_setup, workspace_provider,
        request_changes={"payload": {"kind": "annotated_source", "content": {"files": {"src/bfs.cc": annotated}}}})
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    root = Path(proposal["attempts"][0]["provider"]["workspace_manifest"]["root"])
    visible = json.loads((root / ".swdb-context/proposal.json").read_text())
    assert "requested alpha 14" in visible["payload"]["content"]["files"]["src/bfs.cc"]
    assert "bool BFSVerifier" not in visible["payload"]["content"]["files"]["src/bfs.cc"]
    assert proposal["request"]["payload"]["content"]["files"]["src/bfs.cc"] == annotated
    candidate = json.loads(records.swdb("get", proposal["candidate"], "--format", "json").stdout)
    assert "bool BFSVerifier" in (Path(candidate["artifact"]["path"]) / "src/bfs.cc").read_text()


def test_annotated_source_cannot_expose_an_altered_verifier(proposal_setup, workspace_provider):
    _, _, snapshot, _ = proposal_setup
    original = (Path(snapshot["artifact"]["path"]) / "src/bfs.cc").read_text()
    result, proposal = submit(proposal_setup, workspace_provider,
        request_changes={"payload": {"kind": "annotated_source", "content": {"files": {
            "src/bfs.cc": original.replace("bool BFSVerifier", "bool AlteredVerifier")}}}})
    assert result.returncode == 1
    assert "annotated source changes a protected evaluator input" in proposal["outcome"]["reason"]


def test_structured_payload_field_names_are_preserved(proposal_setup, workspace_provider):
    content = {"evaluator": "Preserve the independent evaluator.", "parameter": {"alpha": 14}}
    result, proposal = submit(proposal_setup, workspace_provider,
        request_changes={"payload": {"kind": "structured_instructions", "content": content}})
    assert result.returncode == 0, proposal["outcome"]
    root = Path(proposal["attempts"][0]["provider"]["workspace_manifest"]["root"])
    assert json.loads((root / ".swdb-context/proposal.json").read_text())["payload"]["content"] == content


def test_timeout_keeps_audit_and_deletes_login_copy(proposal_setup, workspace_provider):
    config = workspace_provider(sleep=5, actions=[{"type": "command", "value": "cat $CODEX_HOME/auth.json"}])
    data = yaml.safe_load(config.read_text()); data["timeout_s"] = 1; config.write_text(yaml.safe_dump(data))
    records, runs, _, request = proposal_setup
    result = records.swdb("submit", request(payload={"kind": "natural_language", "content": "Use alpha 14."}),
                          "--provider-config", config, "--runs-dir", runs, "--format", "json")
    proposal = json.loads(result.stdout)
    assert result.returncode == 1
    provider = proposal["attempts"][0]["provider"]
    assert provider["state"] == "interrupted_or_timeout" and provider["host_wall_s"] >= 1
    assert provider["workspace_manifest"]["login_copy_deleted"] and not provider["audit"]["passed"]
    assert not list(Path(provider["workspace_manifest"]["home"]).glob("*auth*"))


def test_public_repair_uses_workspace_diff_and_audit(evaluation_setup, workspace_provider):
    records, runs, _, base = evaluation_setup
    result, failed = evaluate(evaluation_setup, mode="build_fail")
    assert result.returncode == 1
    old = json.loads(records.swdb("get", base["candidate"], "--format", "json").stdout)
    config = workspace_provider(edits=[{"path": "src/bfs.cc", "old": "int alpha = 14", "new": "int alpha = 13"}],
                                actions=[{"type": "file", "value": "src/bfs.cc"}])
    result = records.swdb("repair", failed["id"], "--provider-config", config, "--runs-dir", runs, "--format", "json")
    proposal = json.loads(result.stdout)
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    attempt = proposal["attempts"][-1]
    assert attempt["provider"]["audit"]["passed"] and attempt["parent_candidate"] == old["id"]
    candidate = json.loads(records.swdb("get", proposal["candidate"], "--format", "json").stdout)
    assert "int alpha = 13" in (Path(candidate["artifact"]["path"]) / "src/bfs.cc").read_text()
    assert "int alpha = 14" in (Path(old["artifact"]["path"]) / "src/bfs.cc").read_text()
