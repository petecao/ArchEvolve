"""Workspace/audit contracts via public submit and repair. Updated: 2026-09-29.

Fixtures emulate both real CLI event formats; no real model is invoked.
"""

import difflib
import json
import shlex
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
(root / "build/received-stdin.txt").write_text(sys.stdin.read())
(root / "build/received-argv.json").write_text(json.dumps(sys.argv[2:]))
(root / "build/start-visible.json").write_text(json.dumps(sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())))
if plan.get("require_large_annotation"):
    proposal = json.loads((root / ".swdb-context/proposal.json").read_text())
    annotated = proposal["payload"]["content"]["files"]["src/bfs.cc"]
    assert len(annotated.encode()) > 128*1024 and "Requested rewrite: alpha 14" in annotated
    (root / "build/context-read.json").write_text(json.dumps({"annotation_bytes":len(annotated.encode())}))
    if kind == "codex":
        print(json.dumps({"type":"item.completed", "item":{"type":"command_execution", "command":"python local context read .swdb-context/proposal.json", "exit_code":0}}), flush=True)
    else:
        print(json.dumps({"type":"assistant", "message":{"content":[{"type":"tool_use", "name":"Read", "input":{"file_path":".swdb-context/proposal.json"}}]}}), flush=True)
if plan.get("require_repair_context"):
    repair = json.loads((root / ".swdb-context/repair.json").read_text())
    diagnostic_bytes = sum(len(log["text"].encode()) for log in repair["logs"])
    assert repair["outcome"]["stage"] == "build" and diagnostic_bytes >= 32000
    (root / "build/repair-read.json").write_text(json.dumps({"diagnostic_bytes":diagnostic_bytes}))
    if kind == "codex":
        print(json.dumps({"type":"item.completed", "item":{"type":"command_execution", "command":"python local context read .swdb-context/repair.json", "exit_code":0}}), flush=True)
    else:
        print(json.dumps({"type":"assistant", "message":{"content":[{"type":"tool_use", "name":"Read", "input":{"file_path":".swdb-context/repair.json"}}]}}), flush=True)
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
    value = action.get("value")
    if isinstance(value, str):
        value = value.replace("__WORKSPACE_ROOT__", str(root))
    if kind == "codex":
        if action["type"] == "command":
            item = {"type":"command_execution", "command":value, "exit_code":0}
        elif action["type"] == "file":
            item = {"type":"file_change", "changes":[{"path":action["value"], "kind":"update"}]}
        else:
            item = {"type":action["type"]}
        print(json.dumps({"type":"item.completed", "item":item}), flush=True)
    else:
        name = "Bash" if action["type"] == "command" else "Read" if action["type"] == "file" else action["type"]
        inputs = {"command":value} if name == "Bash" else {"file_path":action.get("value", ".")}
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
    provider_prompt = argv[-1] if workspace_provider.kind == "codex" else (root / "build/received-stdin.txt").read_text()
    assert "Use direct editing tools for source changes" in provider_prompt
    assert "literal command and file operands" in provider_prompt
    assert "inline interpreters" in provider_prompt and "regex-based code transformations" in provider_prompt


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


@pytest.mark.parametrize("shell,flags", [("sh", "-c"), ("bash", "-lc"), ("zsh", "-xec"),
                                         ("dash", "-uc"), ("ksh", "-lc")])
@pytest.mark.parametrize("body,code", [
    ("cat ../outside/secret.yaml", "external_file_access"),
    ("cat /etc/passwd", "external_file_access"),
    ("curl https://example.com/source.cc", "network_command"),
    ("cat $CODEX_HOME/auth.json", "login_file_access"),
])
def test_shell_wrapped_actions_fail_public_submit(proposal_setup, workspace_provider, shell, flags, body, code):
    result, proposal = submit(proposal_setup, workspace_provider,
        actions=[{"type": "command", "value": f"/usr/bin/{shell} {flags} {shlex.quote(body)}"}])
    assert result.returncode == 1 and proposal["outcome"]["state"] == "failed"
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert not audit["passed"] and code in {v["code"] for v in audit["violations"]}
    assert "candidate" not in proposal and Path(audit["raw_log"]["path"]).is_file()


@pytest.mark.parametrize("body", [
    "$COMMAND",
    'cat "$UNKNOWN_PATH"',
    '$(cat ../outside/secret.yaml)',
    'eval "cat ../outside/secret.yaml"',
    'bash --rcfile ../outside/shellrc -c "printf harmless"',
    "env -S " + shlex.quote("bash -lc 'cat ../outside/secret.yaml'"),
    "f(){ bash -lc 'cat ../outside/secret.yaml'; }; f",
    "{ bash -lc 'cat ../outside/secret.yaml'; }",
    "2>/dev/null bash -lc 'cat ../outside/secret.yaml'",
])
def test_dynamic_shell_body_fails_closed(proposal_setup, workspace_provider, body):
    result, proposal = submit(proposal_setup, workspace_provider,
        actions=[{"type": "command", "value": f"/usr/bin/bash -lc {shlex.quote(body)}"}])
    assert result.returncode == 1
    violations = proposal["attempts"][0]["provider"]["audit"]["violations"]
    assert "unparsed_command" in {v["code"] for v in violations}
    assert "candidate" not in proposal


@pytest.mark.parametrize("prefix", ["cd src && ", "\n\n", "printf ok;\n", "printf ok &&\n"])
def test_nested_shell_preserves_known_cwd(proposal_setup, workspace_provider, prefix):
    body = prefix + "/usr/bin/dash -ec " + shlex.quote("cat ../../outside/secret.yaml")
    result, proposal = submit(proposal_setup, workspace_provider,
        actions=[{"type": "command", "value": "/usr/bin/bash -lc " + shlex.quote(body)}])
    assert result.returncode == 1
    assert "external_file_access" in {v["code"] for v in proposal["attempts"][0]["provider"]["audit"]["violations"]}


@pytest.mark.parametrize("body", [
    "cd src && /usr/bin/dash -ec " + shlex.quote("c++ -c bfs.cc -o ../build/bfs.o >/dev/null"),
    "printf '%s\\n' 'cat ../outside/secret.yaml' >/dev/null\n"
    "c++ -c src/bfs.cc -o build/bfs.o",
    "mkdir -p build && c++ -c src/bfs.cc -o build/bfs.o\n"
    "build/probe\nprobe_status=$?\nprintf 'probe status: %s\\n' \"$probe_status\"\n"
    'test "$probe_status" -eq 1',
])
def test_shell_wrapped_compile_and_status_pass(proposal_setup, workspace_provider, body):
    output = {"type": "item.completed", "item": {"type": "command_execution",
        "command": "/usr/bin/bash -lc " + shlex.quote(body),
        "aggregated_output": "cat ../outside/secret.yaml\ncurl https://example.com\ncat $CODEX_HOME/auth.json",
        "exit_code": 0}}
    actions = [] if workspace_provider.kind == "codex" else [{"type": "command", "value": output["item"]["command"]}]
    events = [output] if workspace_provider.kind == "codex" else [{"type": "user", "message": {"content": [
        {"type": "tool_result", "content": output["item"]["aggregated_output"]}]}}]
    result, proposal = submit(proposal_setup, workspace_provider, actions=actions, events=events,
        edits=[{"path": "src/bfs.cc", "old": "int alpha = 15", "new": "int alpha = 14"},
               {"path": "build/bfs.o", "bytes": [127, 69, 76, 70, 0]},
               {"path": "build/probe", "bytes": [127, 69, 76, 70, 0]}])
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert audit["passed"] and audit["commands"] == 1 and proposal["candidate"]


@pytest.mark.parametrize("value", [
    'cat "$UNKNOWN_PATH"',
    'eval "cat ../outside/secret.yaml"',
    'python -c "print(open(\'/etc/passwd\').read())"',
    'python -c "from pathlib import Path; print(Path(chr(47)+chr(101)+chr(116)+chr(99)+chr(47)+chr(112)+chr(97)+chr(115)+chr(115)+chr(119)+chr(100)).read_text())"',
    'node -e "require(\'fs\').readFileSync(\'/etc/passwd\')"',
    'perl -e "open(my $f, \'/etc/passwd\'); print <$f>"',
    'ruby -e "puts File.read(\'/etc/passwd\')"',
    'php -r "echo file_get_contents(\'/etc/passwd\');"',
])
def test_direct_dynamic_or_inline_command_fails_closed(proposal_setup, workspace_provider, value):
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert result.returncode == 1 and not audit["passed"]
    assert "unparsed_command" in {v["code"] for v in audit["violations"]}
    assert "candidate" not in proposal and Path(audit["raw_log"]["path"]).is_file()


@pytest.mark.parametrize("value", [
    "awk 'BEGIN {getline line < \"/etc/passwd\"; print line}'",
    "gawk 'BEGIN {getline line < \"/etc/passwd\"; print line}'",
    "sed -e 'r /etc/passwd' src/bfs.cc",
    "sed -n '1p; r /etc/passwd' src/bfs.cc",
    "sed -n '1p\nr /etc/passwd' src/bfs.cc",
    "sed -ni '1p' src/bfs.cc",
    "find src -exec sh -c 'cat /etc/passwd' sh {} +",
    "find src -execdir sh -c 'cat /etc/passwd' sh {} +",
    "find src -ok sh -c 'cat /etc/passwd' sh {} +",
    "find src -okdir sh -c 'cat /etc/passwd' sh {} +",
    "printf src/bfs.cc | xargs sh -c 'cat /etc/passwd'",
    "/usr/bin/time c++ -I/etc -c src/bfs.cc -o build/bfs.o",
    "ccache c++ -I/etc -c src/bfs.cc -o build/bfs.o",
    "busybox sh -c 'cat /etc/passwd'",
    "git -c include.path=/etc/passwd diff -- src/bfs.cc",
    "tar -T/etc/passwd -cf build/probe.tar",
    "CPATH=/etc c++ -c src/bfs.cc -o build/bfs.o",
    "BASH_ENV=/etc/passwd bash -c 'true'",
    "env PATH=/data1/other-repo c++ -c src/bfs.cc -o build/bfs.o",
    "export CPATH=/etc; c++ -c src/bfs.cc -o build/bfs.o",
    "wc --files0-from=src/bfs.cc",
    "grep -vf/etc/passwd src/bfs.cc",
    "GIT_EXTERNAL_DIFF='cat /etc/passwd' git diff -- src/bfs.cc",
    "tar -cTf /etc/passwd build/probe.tar src/bfs.cc",
    "tar cTf /etc/passwd build/probe.tar src/bfs.cc",
])
def test_opaque_utility_or_delegation_fails_public_submit(proposal_setup, workspace_provider, value):
    # Scripted actions exercise the admission contract, not actual outside reads.
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert result.returncode == 1 and proposal["outcome"]["state"] == "failed" and not audit["passed"]
    assert "unparsed_command" in {v["code"] for v in audit["violations"]}
    assert "candidate" not in proposal and Path(audit["raw_log"]["path"]).is_file()
    assert proposal["outcome"]["reason"].startswith("provider audit failed")


@pytest.mark.parametrize("value", [
    "grep --file=/etc/passwd src/bfs.cc",
    "rg --file=/etc/passwd src/bfs.cc",
    "grep -f/etc/passwd src/bfs.cc",
    "wc --files0-from=/etc/passwd",
    "/usr/bin/env sh -c 'cat /etc/passwd'",
    "/data1/other-repo/env sh -c 'true'",
    "git -C/etc diff -- src/bfs.cc",
    "git --git-dir=/etc diff -- src/bfs.cc",
])
def test_literal_utility_file_operands_fail_public_submit(proposal_setup, workspace_provider, value):
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert result.returncode == 1 and not audit["passed"] and "candidate" not in proposal
    assert "external_file_access" in {v["code"] for v in audit["violations"]}
    assert Path(audit["raw_log"]["path"]).is_file()


@pytest.mark.parametrize("value", [
    "sed -n '70,105p' src/bfs.cc",
    "sed -n -e '80,96p' src/bfs.cc",
    "/usr/bin/bash -lc " + shlex.quote("sed -n '70,105p' src/bfs.cc"),
    "find src -type f -name '*.cc' -print",
    "grep -F --file=src/bfs.cc src/bfs.cc",
    "rg -F -f src/bfs.cc src/bfs.cc",
    "/usr/bin/env -i OMP_NUM_THREADS=2 /usr/bin/c++ -Isrc -c src/bfs.cc -o build/bfs.o",
    "/usr/bin/env bash -c 'cat src/bfs.cc'",
    "git diff -- src/bfs.cc",
])
def test_literal_utility_read_and_build_pass_public_submit(proposal_setup, workspace_provider, value):
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}])
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert audit["passed"] and not audit["violations"] and proposal["candidate"]
    candidate = json.loads(proposal_setup[0].swdb("get", proposal["candidate"], "--format", "json").stdout)
    assert "int alpha = 14" in (Path(candidate["artifact"]["path"]) / "src/bfs.cc").read_text()


def test_direct_workspace_script_compile_and_status_pass(proposal_setup, workspace_provider):
    value = "c++ -c src/bfs.cc -o build/bfs.o\npython3 -I -E build/synthetic.py\nbuild/probe\n"
    value += 'probe_status=$?\nprintf "status: %s\\n" "$probe_status"\ntest "$probe_status" -eq 1'
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}],
        edits=[{"path": "src/bfs.cc", "old": "int alpha = 15", "new": "int alpha = 14"},
               {"path": "build/probe", "bytes": [127, 69, 76, 70, 0]}])
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    assert proposal["attempts"][0]["provider"]["audit"]["passed"] and proposal["candidate"]


@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize("report", ['echo "exit=$?"', 'printf "%s\\n" "status=$?"'])
def test_literal_exit_status_report_passes_public_submit(proposal_setup, workspace_provider, wrapped, report):
    body = "mkdir -p build && g++ src/bfs.cc -o build/probe && ./build/probe; " + report
    value = "/usr/bin/bash -lc " + shlex.quote(body) if wrapped else body
    result, proposal = submit(proposal_setup, workspace_provider,
        actions=[{"type": "command", "value": value}],
        edits=[{"path": "src/bfs.cc", "old": "int alpha = 15", "new": "int alpha = 14"},
               {"path": "build/probe", "bytes": [127, 69, 76, 70, 0]}])
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert audit["passed"] and not audit["violations"] and Path(audit["raw_log"]["path"]).is_file()
    assert proposal["candidate"] and proposal["provider"]["audit"]["passed"]


@pytest.mark.parametrize("value", [
    'echo "exit=$(cat ../outside/secret.yaml)"',
    'printf "%s\\n" "status=$(cat ../outside/secret.yaml)"',
    'echo "$?/../secret"',
    'printf "%s\\n" "status=$?/../secret"',
    'echo "$?*"',
    'printf "%s\\n" "status=$?*"',
    'echo "exit=$UNKNOWN"',
    'printf "%s\\n" "status=${UNKNOWN}"',
    'echo "exit=$?~"',
    'printf "%s\\n" "status=$?\\fragment"',
    'echo "exit=$?`cat ../outside/secret.yaml`"',
    'printf "%s\\n" "status=$?${UNKNOWN}"',
    'test "exit=$?" -eq 1',
])
def test_unsafe_exit_status_report_fails_public_submit(proposal_setup, workspace_provider, value):
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}])
    assert result.returncode == 1 and proposal["outcome"]["state"] == "failed"
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert not audit["passed"] and "unparsed_command" in {v["code"] for v in audit["violations"]}
    assert "candidate" not in proposal and Path(audit["raw_log"]["path"]).is_file()


@pytest.mark.parametrize("wrapped", [False, True])
def test_external_executable_fails_public_submit(proposal_setup, workspace_provider, wrapped):
    value = "/data1/other-repo/evaluator"
    if wrapped:
        value = "/usr/bin/bash -lc " + shlex.quote(value)
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert result.returncode == 1 and not audit["passed"] and "candidate" not in proposal
    assert "external_file_access" in {v["code"] for v in audit["violations"]}


@pytest.mark.parametrize("operand", ["-I/data1/other-repo", "-I ../outside", "-L/data1/other-repo",
    "-include../outside/verifier.h", "-include ../outside/verifier.h", "-imacros../outside/verifier.h",
    "-isystem/data1/other-repo", "-iquote ../outside", "-idirafter../outside", "-isysroot/data1/other-repo",
    "--sysroot=/data1/other-repo", "--sysroot ../outside", "-o../outside/file", "-o ../outside/file"])
def test_compiler_external_operand_fails_public_submit(proposal_setup, workspace_provider, operand):
    value = "/usr/bin/c++ " + operand + " src/bfs.cc"
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert result.returncode == 1 and not audit["passed"] and "candidate" not in proposal
    assert "external_file_access" in {v["code"] for v in audit["violations"]}


@pytest.mark.parametrize("operand", ['-I"$UNKNOWN_ROOT"', '-o "$UNKNOWN_PATH"', '-I=src', '-L=src'])
def test_compiler_dynamic_operand_fails_closed(proposal_setup, workspace_provider, operand):
    result, proposal = submit(proposal_setup, workspace_provider,
        actions=[{"type": "command", "value": "c++ " + operand + " src/bfs.cc"}])
    assert result.returncode == 1 and "candidate" not in proposal
    assert "unparsed_command" in {v["code"] for v in proposal["attempts"][0]["provider"]["audit"]["violations"]}


@pytest.mark.parametrize("operand", [
    "-Wp,-include,/etc/passwd",
    "-Xpreprocessor -include -Xpreprocessor /etc/passwd",
    "-Xclang -include -Xclang /etc/passwd",
    "-Wl,@/etc/passwd",
    "@/etc/passwd",
    "@build/compiler.rsp",
    "-I @build/compiler.rsp",
    "-fplugin=/etc/passwd",
])
def test_compiler_forwarded_and_response_operands_fail_public_submit(proposal_setup, workspace_provider, operand):
    # A workspace response file can still introduce outside arguments; its final
    # contents do not prove the inputs at the time of the recorded invocation.
    result, proposal = submit(proposal_setup, workspace_provider,
        actions=[{"type": "command", "value": "c++ " + operand + " -c src/bfs.cc -o build/bfs.o"}])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert result.returncode == 1 and not audit["passed"] and "candidate" not in proposal
    assert "unparsed_command" in {v["code"] for v in audit["violations"]}
    assert Path(audit["raw_log"]["path"]).is_file()


@pytest.mark.parametrize("value", [
    "clang++ -fprofile-instr-use=/etc/passwd -c src/bfs.cc -o build/bfs.o",
    "c++ -fprofile-use=profile -c src/bfs.cc -o build/bfs.o",
    "clang++ -fprofile-instr-generate=build/profile -c src/bfs.cc -o build/bfs.o",
    "clang++ -fprofile-remapping-file=/etc/passwd -c src/bfs.cc -o build/bfs.o",
    "clang++ -mllvm -load=/etc/passwd -c src/bfs.cc -o build/bfs.o",
    "printf '#include </etc/passwd>' | clang++ -x c++ - -fsyntax-only",
    "tar --checkpoint=1 --checkpoint-action='exec=cat /etc/passwd' -cf build/probe.tar src/bfs.cc",
    "tar --use-compress-program=/data1/other-repo/tool -cf build/probe.tar src/bfs.cc",
    "rg --pre=/data1/other-repo/tool BFS src/bfs.cc",
    "rg --pre=build/tool BFS src/bfs.cc",
    "rg --ignore-file=/etc/passwd BFS src/bfs.cc",
    "RIPGREP_CONFIG_PATH=/etc/passwd rg BFS src/bfs.cc",
    "TAR_OPTIONS='--checkpoint-action=exec=cat /etc/passwd' tar -cf build/probe.tar src/bfs.cc",
    "CXXFLAGS='-fprofile-use=/etc' c++ -c src/bfs.cc -o build/bfs.o",
    "LLVM_PROFILE_FILE=/etc/profile build/probe",
    "sed -n '1p' src/bfs.cc >/dev/null -e 'r /etc/passwd'",
])
def test_unknown_compiler_or_utility_options_fail_public_submit(proposal_setup, workspace_provider, value):
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert result.returncode == 1 and not audit["passed"] and "candidate" not in proposal
    assert {v["code"] for v in audit["violations"]} & {"unparsed_command", "external_file_access"}
    assert Path(audit["raw_log"]["path"]).is_file() and proposal["outcome"]["reason"].startswith("provider audit failed")
    if value.startswith(("RIPGREP_CONFIG_PATH=", "TAR_OPTIONS=", "CXXFLAGS=", "LLVM_PROFILE_FILE=")):
        assert any("environment override" in v["reason"] for v in audit["violations"])


@pytest.mark.parametrize("value", [
    "g++ -O3 -std=gnu++17 -march=native -mtune=native -mavx2 -fopenmp -Wall -Werror=return-type "
    "-DTEST_VALUE=1 -UOLD_VALUE -I src -L build -c src/bfs.cc -o build/bfs.o",
    "clang++ -O2 -g -std=c++17 -x c++ -D TEST_VALUE=1 -MMD -MF build/bfs.d -MJ build/bfs.json "
    "-c src/bfs.cc --output=build/bfs.o",
    "c++ -O3 -std=c++17 -fno-omit-frame-pointer src/bfs.cc -Lbuild -lpthread -lm -o build/probe >/dev/null",
    "rg --no-config -nF -e BFS src/bfs.cc >/dev/null",
    "rg --file=src/bfs.cc --count src/bfs.cc",
    "sed -n '70,105p' >/dev/null src/bfs.cc",
])
def test_supported_compiler_and_search_options_pass_public_submit(proposal_setup, workspace_provider, value):
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}])
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert audit["passed"] and not audit["violations"] and proposal["candidate"]
    candidate = json.loads(proposal_setup[0].swdb("get", proposal["candidate"], "--format", "json").stdout)
    assert "int alpha = 14" in (Path(candidate["artifact"]["path"]) / "src/bfs.cc").read_text()


@pytest.mark.parametrize("value", [
    "/usr/bin/c++ -Isrc -obuild/probe src/bfs.cc && __WORKSPACE_ROOT__/build/probe",
    "cd src && /usr/bin/c++ -I . -o ../build/probe bfs.cc && ../build/probe",
])
def test_system_compiler_and_workspace_executable_pass(proposal_setup, workspace_provider, value):
    result, proposal = submit(proposal_setup, workspace_provider, actions=[{"type": "command", "value": value}],
        edits=[{"path": "src/bfs.cc", "old": "int alpha = 15", "new": "int alpha = 14"},
               {"path": "build/probe", "bytes": [127, 69, 76, 70, 0]}])
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    assert proposal["attempts"][0]["provider"]["audit"]["passed"] and proposal["candidate"]


@pytest.mark.parametrize("workspace_provider", ["claude"], indirect=True)
@pytest.mark.parametrize("inputs", [
    {"pattern": "/etc/*"},
    {"pattern": "../outside/*"},
    {"pattern": "../../*", "path": "src"},
    {"pattern": "*", "path": "/etc"},
    {"pattern": "$UNKNOWN_ROOT/*.h"},
    {"pattern": "~/*.h"},
    {"pattern": "src/*/../../*"},
    {"pattern": "src/**/*.h", "path": "../outside"},
])
def test_glob_effective_root_fails_public_submit(proposal_setup, workspace_provider, inputs):
    event = {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Glob", "input": inputs}]}}
    result, proposal = submit(proposal_setup, workspace_provider, events=[event])
    audit = proposal["attempts"][0]["provider"]["audit"]
    assert result.returncode == 1 and not audit["passed"] and "candidate" not in proposal
    assert "external_file_access" in {v["code"] for v in audit["violations"]}


@pytest.mark.parametrize("workspace_provider", ["claude"], indirect=True)
@pytest.mark.parametrize("inputs", [{"pattern": "src/**/*.h"}, {"pattern": "*.cc", "path": "src"},
                                    {"pattern": "**/*.h", "path": "."}])
def test_glob_workspace_wildcards_pass_public_submit(proposal_setup, workspace_provider, inputs):
    event = {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Glob", "input": inputs}]}}
    result, proposal = submit(proposal_setup, workspace_provider, events=[event])
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    assert proposal["attempts"][0]["provider"]["audit"]["passed"] and proposal["candidate"]


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


def test_large_annotations_use_immutable_context_and_compact_prompt(proposal_setup, workspace_provider):
    records, _, snapshot, _ = proposal_setup
    original = (Path(snapshot["artifact"]["path"]) / "src/bfs.cc").read_text()
    annotation = "/* Requested rewrite: alpha 14. Preserve all computation and ROI.\n" + (
        "Instruction context: retain graph traversal, parent updates, and direction switching.\n" * 2200) + "*/\n"
    annotated = annotation + original
    assert len(annotated.encode()) > 128 * 1024
    result, proposal = submit(proposal_setup, workspace_provider,
        request_changes={"payload": {"kind": "annotated_source", "content": {"files": {"src/bfs.cc": annotated}}}},
        require_large_annotation=True)
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    meta = proposal["attempts"][0]["provider"]
    manifest = meta["workspace_manifest"]
    root = Path(manifest["root"])
    visible_proposal = json.loads((root / ".swdb-context/proposal.json").read_text())
    contents = visible_proposal["payload"]["content"]["files"]["src/bfs.cc"]
    assert contents.startswith(annotation) and len(contents.encode()) > 128*1024
    assert json.loads((root / "build/context-read.json").read_text())["annotation_bytes"] == len(contents.encode())
    assert "bool BFSVerifier" not in contents and "SWDB_PROTECTED_VERIFIER_" in contents
    assert proposal["request"]["payload"]["content"]["files"]["src/bfs.cc"] == annotated
    argv = json.loads((root / "build/received-argv.json").read_text())
    stdin = (root / "build/received-stdin.txt").read_text()
    provider_prompt = argv[-1] if workspace_provider.kind == "codex" else stdin
    assert len(provider_prompt.encode()) < 8*1024 and annotation not in provider_prompt
    assert ".swdb-context/proposal.json" in provider_prompt and ".swdb-context/workspace-map.json" in provider_prompt
    if workspace_provider.kind == "codex":
        assert stdin == ""
    map_path = manifest["context_manifest"]["path"]
    assert map_path in manifest["immutable_files"] and map_path in manifest["visible_files"]
    visible_map = json.loads((root / map_path).read_text())
    assert visible_map["editable_files"] == ["src/bfs.cc"]
    candidate = json.loads(records.swdb("get", proposal["candidate"], "--format", "json").stdout)
    edited = (Path(candidate["artifact"]["path"]) / "src/bfs.cc").read_text()
    assert "int alpha = 14" in edited and "bool BFSVerifier" in edited and annotation not in edited
    assert ".swdb-context" not in {Path(item["path"]).parts[0] for item in candidate["artifact"]["files"]}


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
    records, runs, evaluation_request, base = evaluation_setup
    machine = records.read("machines/native-testhost.yaml")
    if machine["hostname"] == "mbit10":
        # The public evaluator verifies the inherited socket lease itself.
        machine["lane_required"] = True
        records.write("machines/native-testhost.yaml", machine)
    compiler = Path(yaml.safe_load(evaluation_request().read_text())["build"]["compiler"])
    body = compiler.read_text()
    failure = "if os.environ.get('SWDB_NATIVE_FIXTURE') == 'build_fail': sys.exit(7)"
    assert failure in body
    compiler.write_text(body.replace(failure,
        "if os.environ.get('SWDB_NATIVE_FIXTURE') == 'build_fail':\n"
        " print('fixture syntax error: ' + 'retained compiler diagnostic ' * 4000); sys.exit(7)"))
    result, failed = evaluate(evaluation_setup, mode="build_fail",
                              build_directory=str(runs / "repair-native-build"))
    assert result.returncode == 1, result.stderr
    assert failed["outcome"]["state"] == "failed" and failed["outcome"]["stage"] == "build", failed["outcome"]
    if machine["hostname"] == "mbit10":
        assert "verified: affinity" in failed["context"]["lane"]
    old = json.loads(records.swdb("get", base["candidate"], "--format", "json").stdout)
    config = workspace_provider(edits=[{"path": "src/bfs.cc", "old": "int alpha = 14", "new": "int alpha = 13"}],
                                actions=[{"type": "file", "value": "src/bfs.cc"}], require_repair_context=True)
    result = records.swdb("repair", failed["id"], "--provider-config", config, "--runs-dir", runs, "--format", "json")
    proposal = json.loads(result.stdout)
    assert result.returncode == 0, (result.stderr, proposal["outcome"])
    attempt = proposal["attempts"][-1]
    assert attempt["provider"]["audit"]["passed"] and attempt["parent_candidate"] == old["id"]
    manifest = attempt["provider"]["workspace_manifest"]
    repair_path = manifest["repair_context"]["path"]
    assert repair_path in manifest["immutable_files"] and repair_path in manifest["visible_files"]
    repair_context = json.loads((Path(manifest["root"]) / repair_path).read_text())
    assert repair_context["evaluation"] == failed["id"] and repair_context["outcome"]["stage"] == "build"
    diagnostic_bytes = sum(len(log["text"].encode()) for log in repair_context["logs"])
    assert diagnostic_bytes >= 32000
    assert json.loads((Path(manifest["root"]) / "build/repair-read.json").read_text())["diagnostic_bytes"] == diagnostic_bytes
    assert len((Path(manifest["root"]).parent / "prompt.txt").read_bytes()) < 8*1024
    candidate = json.loads(records.swdb("get", proposal["candidate"], "--format", "json").stdout)
    assert "int alpha = 13" in (Path(candidate["artifact"]["path"]) / "src/bfs.cc").read_text()
    assert "int alpha = 14" in (Path(old["artifact"]["path"]) / "src/bfs.cc").read_text()
