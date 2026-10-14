"""The proof_hinting agent role and its guarded workspace (Probata proof of concept, ticket 34).

Created: 2026-10-14 ET. Seams: the provider launcher (`provider_roles.run` with role `proof_hinting`), the
role's workspace (`workspace.json` against the visible tree), the frozen wrapper (an MCP stdio server and
its command line) and the rewriting workspace's guard. A scripted provider (an `external_fixture` that
emulates Codex), a stand-in `frama-c` and a scripted proof hint check stand in; no real provider or
verifier runs.
"""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES
from swdb import artifacts, provider_roles, proof_hinting, rewrite, verifier_lock
from swdb.cli import Failure

HERE = FIXTURES / "proof_hinting"
FUNCTION = "f"
LOWERING = """#include <stdint.h>
int f(int n) {
  /* swdb-anchor f.contract */
  /* swdb-anchor f.entry */
  int i = 0;
  /* swdb-anchor f.loop1.head */
  while (i < n) {
    i++;
  }
  return i;
}
"""
ANCHORS = {"function": FUNCTION, "anchors": [{"id": "f.contract", "kind": "contract"}, {"id": "f.entry", "kind": "entry"},
                                             {"id": "f.loop1.head", "kind": "loop_head"}]}
UNIT = "int f(int n) {\n  int i = 0;\n  while (i < n) i++;\n  return i;\n}\n"
UNIT_PATH = "src/unit.cc"
HINT = {"anchor": "f.loop1.head", "kind": "loop invariant", "text": "0 <= i <= n;"}
GOALS = [{"goal": "typed_f_loop_invariant_preserved", "property": "f_ensures", "kind": "postcondition",
          "failure_class": "timeout"}]
REJECTED = [{"hint": {"anchor": "f.entry", "kind": "assert", "text": "admit;"}, "rule": "vocabulary"}]
BLAMED = [{"hint": {"anchor": "f.loop1.head", "kind": "loop invariant", "text": "i < n;"},
           "reason": "made goal typed_f_assigns time out"}]
SEEDS = [{"anchor": "f.loop1.head", "kind": "loop invariant", "text": "0 <= i;", "source": "contract proof"}]


def candidate(**overrides):
    data = {"id": "candidate.unit-1", "files": {UNIT_PATH: hashlib.sha256(UNIT.encode()).hexdigest()},
            "authors_function": None}
    data.update(overrides)
    return proof_hinting.Candidate(**data)


def files(**overrides):
    parts = dict(function=FUNCTION, lowering=LOWERING, anchors=ANCHORS, proof_unit_path=UNIT_PATH,
                 proof_unit_text=UNIT, formal_halves="requires n >= 0;\nensures \\result == n;\n",
                 unit_postcondition="ensures \\result == n;\n", summaries={"dxc_wait": "/*@ assigns \\nothing; */\n"},
                 goals=GOALS, rejected=REJECTED, blamed=BLAMED, seeds=SEEDS)
    parts.update(overrides)
    return proof_hinting.workspace_files(**parts)


@pytest.fixture
def plan(tmp_path, monkeypatch):
    """The wrapper plan, a stand-in frama-c and a private verifier lock."""
    wp_log = tmp_path / "frama-c-calls.jsonl"
    monkeypatch.setenv("SWDB_FRAMA_C", f"{sys.executable} {HERE / 'stub_framac.py'} {wp_log}")
    monkeypatch.setenv("SWDB_VERIFIER_LOCK", str(tmp_path / "locks" / "verifier.lock"))
    built = proof_hinting.wrapper_plan(base=LOWERING, method_flags=["-wp", "-wp-cache", "none", "-wp-model", "+real"],
                                       seconds_per_solver=30, check=(HERE / "scripted_check.py", "check"))
    built.wp_log = wp_log
    return built


class Provider:
    def __init__(self, root):
        self.root = root
        self.log = root / "provider-argv.jsonl"
        self.replies = root / "mcp-replies.json"

    def config(self, mode="hints", **extra):
        plan = {"mode": mode, "log": str(self.log), "replies": str(self.replies), "server": proof_hinting.SERVER,
                "hints": [HINT], **extra}
        path = self.root / f"plan-{mode}-{len(list(self.root.glob('plan-*')))}.json"
        path.write_text(json.dumps(plan))
        config = self.root / f"{path.stem}.yaml"
        config.write_text(yaml.safe_dump({"kind": "external_fixture", "emulates": "codex",
                                          "command": [sys.executable, str(HERE / "provider.py"), str(path)],
                                          "timeout_s": 60, "total_seconds": 120}))
        return rewrite.configuration(config)

    def runs(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []


@pytest.fixture
def provider(tmp_path):
    return Provider(tmp_path)


def run(provider, plan, folder, mode="hints", inputs=None, cand=None, **extra):
    return provider_roles.run("proof_hinting", proof_hinting.Inputs(inputs or files(), cand or candidate(), plan),
                              None, provider.config(mode, **extra), folder)


# --- launch ------------------------------------------------------------------------------------------

def test_a_scripted_provider_runs_the_role_end_to_end_and_the_hint_set_records_the_provider_kind(provider, plan, tmp_path):
    hint_set, metadata = run(provider, plan, tmp_path / "call")
    assert [{k: h[k] for k in ("anchor", "kind", "text")} for h in hint_set["hints"]] == [HINT]
    assert hint_set["provider"]["kind"] == "external_fixture" and hint_set["provider"]["resolved_kind"] == "codex"
    assert hint_set["provider"]["model"] == "gpt-5.6-sol" and hint_set["provider"]["effort"] == "xhigh"
    assert all(h["provenance"] == {"by": "proof_hinting_agent", "provider_kind": "codex"} for h in hint_set["hints"])
    assert metadata["role"] == "proof_hinting" and metadata["audit"]["passed"]
    assert len(provider.runs()) == 1


def test_codex_at_its_pin_is_the_default_provider():
    config = proof_hinting.default_config(command="/bin/echo")
    assert config["kind"] == "codex" and (config["model"], config["effort"]) == ("gpt-5.6-sol", "xhigh")


# --- the visible set -----------------------------------------------------------------------------------

def test_the_visible_tree_is_exactly_the_files_hashed_in_workspace_json(provider, plan, tmp_path):
    _hint_set, metadata = run(provider, plan, tmp_path / "call")
    manifest = json.loads((tmp_path / "call" / "workspace.json").read_text())
    root = Path(manifest["root"])
    tree = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}
    assert tree == manifest["visible_files"]
    assert set(tree) == {"lowering/f.c", "lowering/f.anchors.json", "proof_unit/src/unit.cc",
                         "contract/formal_halves.acsl", "contract/unit_postcondition.acsl", "summaries/dxc_wait.acsl",
                         "context/goals.json", "context/rejected_hints.json", "context/blamed_hints.json",
                         "context/seeds.json"}
    goals = json.loads((root / "context" / "goals.json").read_text())
    assert goals == GOALS and all(g["kind"] and g["failure_class"] for g in goals)
    assert json.loads((root / "context" / "rejected_hints.json").read_text())[0]["rule"] == "vocabulary"
    assert json.loads((root / "context" / "blamed_hints.json").read_text()) == BLAMED
    assert json.loads((root / "context" / "seeds.json").read_text()) == SEEDS
    assert metadata["workspace_manifest"]["visible_files"] == manifest["visible_files"]


HIDDEN = [
    ("evaluator code", "evaluator/bfs_verify.cc", "bool verify(const int *parent) { return true; }\n"),
    ("a workload input", "inputs/kron-10.sg", "0 1\n1 2\n"),
    ("a test", "tests/test_unit.py", "def test_f():\n    assert True\n"),
    ("a negative control", "negative_controls/missing_wait.c", "int f(int n) { return n; }\n"),
    ("another candidate artifact", "candidates/candidate.other/src/unit.cc", "int f(int n) { return 0; }\n"),
]


@pytest.mark.parametrize("category,name,text", HIDDEN, ids=[h[0] for h in HIDDEN])
def test_hidden_material_makes_the_role_refuse_to_start_and_name_the_file(category, name, text, provider, plan, tmp_path):
    with pytest.raises(Failure, match=f"hidden material \\({category}\\): {name}"):
        run(provider, plan, tmp_path / "call", inputs={**files(), name: text})
    assert provider.runs() == [] and not (tmp_path / "call").exists()


def test_a_second_proof_unit_from_another_candidate_artifact_is_refused(provider, plan, tmp_path):
    inputs = {**files(), "proof_unit/src/other.cc": "int g(void) { return 1; }\n"}
    with pytest.raises(Failure, match="exactly one proof unit"):
        run(provider, plan, tmp_path / "call", inputs=inputs)
    other = files(proof_unit_text="int f(int n) { return 0; }\n")          # not the candidate's bytes
    with pytest.raises(Failure, match="another candidate artifact.*proof_unit/src/unit.cc"):
        run(provider, plan, tmp_path / "call2", inputs=other)
    assert provider.runs() == []


def test_a_counterexample_is_refused_it_goes_to_counterexample_guided_repair(provider, plan, tmp_path):
    goals = [{**GOALS[0], "counterexample": {"n": -1}}]
    with pytest.raises(Failure, match="counterexample.*context/goals.json"):
        run(provider, plan, tmp_path / "call", inputs=files(goals=goals))
    assert provider.runs() == []


def test_a_file_outside_the_layout_is_refused(provider, plan, tmp_path):
    with pytest.raises(Failure, match="outside its workspace layout: notes/strategy.md"):
        run(provider, plan, tmp_path / "call", inputs={**files(), "notes/strategy.md": "hi\n"})


# --- the narrow guard exception (map 18 item 6) ------------------------------------------------------------

TDSTEP_LOWERING = LOWERING.replace("int f(", "int TDStepMAA(").replace("f.", "TDStepMAA.")
TDSTEP_ANCHORS = {"function": "TDStepMAA", "anchors": [{"id": a["id"].replace("f.", "TDStepMAA."), "kind": a["kind"]}
                                                      for a in ANCHORS["anchors"]]}
TDSTEP_UNIT = UNIT.replace("int f(", "int64_t TDStepMAA(")


def tdstep_files(unit=TDSTEP_UNIT):
    return files(function="TDStepMAA", lowering=TDSTEP_LOWERING, anchors=TDSTEP_ANCHORS, proof_unit_text=unit,
                 goals=[{**GOALS[0], "goal": "typed_TDStepMAA_ensures", "function": "TDStepMAA"}])


def tdstep_candidate(unit=TDSTEP_UNIT, authors_function="TDStepMAA"):
    return candidate(id="candidate.authors-tdstep", authors_function=authors_function,
                     files={UNIT_PATH: hashlib.sha256(unit.encode()).hexdigest()})


def test_the_authors_function_is_visible_when_it_is_the_candidate_artifact(provider, plan, tmp_path):
    hint_set, metadata = run(provider, plan, tmp_path / "call", inputs=tdstep_files(), cand=tdstep_candidate())
    root = Path(metadata["workspace_manifest"]["root"])
    assert "TDStepMAA" in (root / "proof_unit" / "src" / "unit.cc").read_text()
    assert metadata["workspace_manifest"]["authors_code_exception"] is True and hint_set["hints"]


def test_the_authors_function_is_refused_when_the_candidate_artifact_is_other_code(provider, plan, tmp_path):
    with pytest.raises(Failure, match="authors' accelerated code \\(TDStepMAA in context/goals.json\\)"):
        run(provider, plan, tmp_path / "call", inputs=tdstep_files(), cand=tdstep_candidate(authors_function=None))
    assert provider.runs() == []


@pytest.mark.parametrize("second", ["DOBFSMAA", "PBFSMAA"])
def test_a_second_authors_function_next_to_the_candidate_is_refused(second, provider, plan, tmp_path):
    unit = TDSTEP_UNIT + f"void {second}(void) {{}}\n"
    with pytest.raises(Failure, match=f"authors' accelerated code \\({second} in proof_unit/src/unit.cc\\)"):
        run(provider, plan, tmp_path / "call", inputs=tdstep_files(unit), cand=tdstep_candidate(unit))
    assert provider.runs() == []


def test_the_exception_keys_on_the_candidate_record_not_on_one_name(provider, plan, tmp_path):
    # The record names DOBFSMAA as the authors' code, but the proof unit is TDStepMAA: refused.
    with pytest.raises(Failure, match="is the authors' DOBFSMAA, but the proof unit is TDStepMAA"):
        run(provider, plan, tmp_path / "call", inputs=tdstep_files(), cand=tdstep_candidate(authors_function="DOBFSMAA"))


@pytest.mark.parametrize("name", ["TDStepMAA", "DOBFSMAA", "PBFSMAA", "BrandesMaa", "PageRankPullMAA", "DeltaStepMAA"])
def test_other_agent_roles_still_refuse_every_guarded_name(name):
    with pytest.raises(Failure, match="authors' accelerated code"):
        provider_roles.checked_inputs({"code.cc": f"void {name}(void) {{}}\n"})


# --- output is hints only ------------------------------------------------------------------------------

def test_the_output_schema_allows_only_anchor_kind_text_records():
    schema = provider_roles.ROLES["proof_hinting"].output_schema
    assert set(schema["properties"]) == {"hints"} and schema["additionalProperties"] is False
    record = schema["properties"]["hints"]["items"]
    assert set(record["properties"]) == {"anchor", "kind", "text"} and record["additionalProperties"] is False
    assert provider_roles.strict_problems(provider_roles.wire_schema(schema)) == []


@pytest.mark.parametrize("mode", ["edit_code", "verdict"])
def test_a_provider_returning_edited_code_or_a_claimed_verdict_fails_the_output_check(mode, provider, plan, tmp_path):
    with pytest.raises(Failure, match="invalid structured output"):
        run(provider, plan, tmp_path / "call", mode=mode)


# --- the frozen wrapper ----------------------------------------------------------------------------------

def test_inside_its_one_call_the_agent_runs_the_check_and_wp_with_the_frozen_flags(provider, plan, tmp_path):
    bad = {"anchor": "f.nowhere", "kind": "assert", "text": "i >= 0;"}
    hint_set, metadata = run(provider, plan, tmp_path / "call", mode="wrapper", calls=[
        ["read_workspace_file", {"path": "context/goals.json"}], ["check_hints", {"hints": [bad]}],
        ["prove_hints", {"hints": [HINT]}]])
    replies = json.loads(provider.replies.read_text())
    assert [t["name"] for t in replies[0]["result"]["tools"]] == list(proof_hinting.TOOLS)
    texts = [r["result"]["content"][0]["text"] for r in replies[1:]]
    assert json.loads(texts[0]) == GOALS
    assert "rule anchor" in texts[1] and "never a verdict" in texts[1]
    assert "1 of 1 goals proven" in texts[2] and "never a verdict" in texts[2]
    wp_runs = [json.loads(line) for line in plan.wp_log.read_text().splitlines()]
    assert len(wp_runs) == 1
    argv = wp_runs[0]["argv"]
    assert argv[:argv.index("-wp-report-json")] == plan.wp_flags
    assert ["-wp-cache", "none"] == argv[argv.index("-wp-cache"):argv.index("-wp-cache") + 2]
    assert "/*@ loop invariant 0 <= i <= n; */" in wp_runs[0]["input"]          # the check merged the hint
    manifest = metadata["workspace_manifest"]["wrapper"]
    assert manifest["sha256"] == hashlib.sha256(proof_hinting.WRAPPER.read_bytes()).hexdigest()
    assert manifest["wp_flags"] == plan.wp_flags
    assert metadata["wrapper_calls"]["count"] == 2
    # Its results reach only the agent: the hint set carries no wrapper outcome.
    assert set(hint_set) == {"format", "role", "candidate", "function", "hints", "provider", "workspace_sha256"}
    assert not list((tmp_path / "call" / "wrapper").glob("scratch-*"))               # WP scratch deleted


def mcp_session(state, calls, extra_args=()):
    process = subprocess.run([sys.executable, "-I", str(proof_hinting.WRAPPER), "--state", str(state), *extra_args],
                             input="\n".join(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call",
                                                         "params": {"name": t, "arguments": a}})
                                             for n, (t, a) in enumerate(calls)) + "\n",
                             capture_output=True, text=True, timeout=120)
    return process, [json.loads(line) for line in process.stdout.splitlines()]


@pytest.fixture
def state(plan, tmp_path):
    workspace = proof_hinting.prepare(proof_hinting.Inputs(files(), candidate(), plan), tmp_path / "prepared",
                                      {"kind": "external_fixture", "emulates": "codex"})
    return workspace.folder / "wrapper"


@pytest.mark.parametrize("extra", [["-wp-cache", "update"], ["-kernel-warn-key", "ghost:bad-use=inactive"]])
def test_the_wrapper_refuses_any_extra_flag_on_its_command_line(extra, state, plan):
    process, replies = mcp_session(state, [("prove_hints", {"hints": [HINT]})], extra)
    assert process.returncode == 2 and replies == [] and "refused" in process.stderr and extra[0] in process.stderr
    assert not plan.wp_log.exists()


@pytest.mark.parametrize("flags", [["-wp-cache", "update"], ["-kernel-warn-key", "ghost:bad-use=inactive"]])
def test_the_wrapper_refuses_any_flag_in_a_tool_call(flags, state, plan):
    process, replies = mcp_session(state, [("prove_hints", {"hints": [HINT], "flags": flags}),
                                           ("check_hints", {"hints": [HINT], "wp_flags": flags})])
    assert all(r["result"]["isError"] and "no flag or option" in r["result"]["content"][0]["text"] for r in replies)
    assert not plan.wp_log.exists()


@pytest.mark.parametrize("flags", [["-wp", "-wp-cache", "update", "-wp-model", "+real"],
                                   ["-wp", "-wp-cache", "none", "-wp-model", "+real", "-kernel-warn-key",
                                    "ghost:bad-use=inactive"],
                                   ["-wp", "-wp-model", "+real"]])
def test_the_wrapper_plan_refuses_unfrozen_flags(flags, plan):
    with pytest.raises(Failure, match="wrapper's WP flags"):
        proof_hinting.wrapper_plan(base=LOWERING, method_flags=flags, seconds_per_solver=30,
                                   check=(HERE / "scripted_check.py", "check"))


def test_the_wrapper_serves_only_visible_files(state):
    _process, replies = mcp_session(state, [("read_workspace_file", {"path": "../wrapper/plan.json"}),
                                            ("read_workspace_file", {"path": "lowering/f.c"})])
    assert replies[0]["result"]["isError"] and "not a workspace file" in replies[0]["result"]["content"][0]["text"]
    assert replies[1]["result"]["content"][0]["text"] == LOWERING


def test_a_changed_wrapper_or_check_is_refused(state, tmp_path):
    plan = json.loads((state / "plan.json").read_text())
    plan["check"]["sha256"] = "0" * 64
    (state / "plan.json").chmod(0o644)
    (state / "plan.json").write_text(json.dumps(plan))
    _process, replies = mcp_session(state, [("check_hints", {"hints": [HINT]})])
    assert replies[0]["result"]["isError"] and "differs from the frozen one" in replies[0]["result"]["content"][0]["text"]


# --- the Mac memory rule ---------------------------------------------------------------------------------

def test_a_wrapper_wp_run_queues_behind_a_running_verifier_job(state, plan, tmp_path):
    # Another ticket's verifier job: a separate process (not an ancestor, so no nested hold) holds the lock.
    released, started = tmp_path / "released", tmp_path / "holding"
    holder = subprocess.Popen([sys.executable, "-c", (
        "import sys, time; from pathlib import Path; from swdb import verifier_lock\n"
        "with verifier_lock.hold('another ticket'):\n"
        f"    Path({str(started)!r}).write_text('1'); time.sleep(2.0); Path({str(released)!r}).write_text(repr(time.time()))\n")],
        cwd=Path(proof_hinting.__file__).parents[1])
    while not started.exists():
        time.sleep(0.05)
    _process, replies = mcp_session(state, [("prove_hints", {"hints": [HINT]})])
    assert holder.wait(timeout=30) == 0
    run_ = json.loads(plan.wp_log.read_text().splitlines()[0])
    assert run_["start"] >= float(released.read_text()) and not replies[0]["result"]["isError"]
    entry = json.loads((state / "calls.jsonl").read_text().splitlines()[0])
    assert entry["wp"]["lock_waited_seconds"] >= 1.0


def test_a_wrapper_wp_run_runs_under_the_rss_watchdog(plan, tmp_path, monkeypatch):
    monkeypatch.setenv("SWDB_VERIFIER_RSS_CAP_BYTES", str(200 * 1024 * 1024))
    capped = proof_hinting.wrapper_plan(base=LOWERING.replace("int i = 0;", "int i = 0; /* STUB_ALLOCATE */"),
                                        method_flags=["-wp", "-wp-cache", "none", "-wp-model", "+real"],
                                        seconds_per_solver=30, check=(HERE / "scripted_check.py", "check"))
    assert plan.cap_bytes == 8 * 1024 ** 3 and capped.cap_bytes == 200 * 1024 * 1024
    workspace = proof_hinting.prepare(proof_hinting.Inputs(files(), candidate(), capped), tmp_path / "capped",
                                      {"kind": "external_fixture", "emulates": "codex"})
    _process, replies = mcp_session(workspace.folder / "wrapper", [("prove_hints", {"hints": [HINT]})])
    assert "out_of_memory" in replies[0]["result"]["content"][0]["text"]


# --- no leak to rewriting --------------------------------------------------------------------------------

def rewriting_workspace(tmp_path, source_files=None):
    from swdb import provider_workspace
    root = tmp_path / "rewrite" / "workspace"
    (root / provider_workspace.CONTEXT_DIR).mkdir(parents=True)
    (root / "src").mkdir()
    shown = {"src/bfs.cc": "int main() { return 0; }\n", **(source_files or {})}
    for name, text in shown.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    workspace = provider_workspace.Workspace(root, tmp_path / "rewrite" / "home", tmp_path / "rewrite", root,
                                             visible={n: artifacts.file_hash(root / n) for n in shown},
                                             source_files=set(shown))
    workspace.metadata = {"extra_files": [], "hidden_fragments": [], "profile_package_projection": {},
                          "source_tree_sha256": None}
    return workspace, {"constraints": {"editable_files": ["src/*"]}}


def hint_set():
    return {"format": proof_hinting.HINT_SET_FORMAT, "role": "proof_hinting", "hints": [HINT]}


REPAIRS = {
    "repair evidence holding a hint set": {"kind": "certification_failure", "hint_set": hint_set()},
    "repair evidence holding hint records": {"kind": "certification_failure", "notes": [HINT]},
    "a counterexample repair holding hint records": {
        "kind": "counterexample_repair", "setting": "campaign", "round": 1, "proof_record": "proof.x",
        "refuted_candidate": "candidate.x", "counterexample": {"n": -1}, "refuted_patch": "--- a\n+++ b\n",
        "last_hints": [HINT]},
}


@pytest.mark.parametrize("repair", list(REPAIRS.values()), ids=list(REPAIRS))
def test_a_rewriting_workspace_refuses_hint_records_in_its_repair_inputs(repair, tmp_path):
    from swdb import provider_workspace
    workspace, request = rewriting_workspace(tmp_path)
    with pytest.raises(Failure, match="hint record"):
        provider_workspace.context_documents(workspace, request, repair)


@pytest.mark.parametrize("name,text", [("src/hints.json", json.dumps([HINT])),
                                       ("src/notes.yaml", yaml.safe_dump({"proof_hints": [HINT]})),
                                       ("src/output.txt", json.dumps(hint_set()))])
def test_a_rewriting_workspace_refuses_a_proof_hinting_output_among_its_files(name, text, tmp_path):
    from swdb import provider_workspace
    workspace, request = rewriting_workspace(tmp_path, {name: text})
    with pytest.raises(Failure, match=f"hint record.*{name}"):
        provider_workspace.context_documents(workspace, request, None)


def test_a_rewriting_workspace_without_hint_records_is_unchanged(tmp_path):
    from swdb import provider_workspace
    workspace, request = rewriting_workspace(tmp_path)
    provider_workspace.context_documents(workspace, request, {"kind": "certification_failure", "reason": "x"})


def test_a_prompt_only_rewrite_refuses_a_hint_set_before_any_call(tmp_path):
    with pytest.raises(Failure, match="hint record"):
        rewrite.call({"kind": "external_fixture", "workspace": False}, {"id": "p"}, {}, {}, None, tmp_path / "call",
                     repair={"kind": "certification_failure", "hint_set": hint_set()})
    assert not (tmp_path / "call").exists()


# --- inputs immutable, Mac confinement ------------------------------------------------------------------

def test_a_provider_that_tries_to_edit_the_lowering_or_the_proof_unit_changes_nothing(provider, plan, tmp_path):
    targets = ["lowering/f.c", "proof_unit/src/unit.cc"]
    with pytest.raises(Failure, match="tried to edit a read-only workspace input: lowering/f.c"):
        run(provider, plan, tmp_path / "call", mode="edit_input", targets=targets)
    root = tmp_path / "call" / "workspace"
    assert (root / "lowering" / "f.c").read_text() == LOWERING and (root / "proof_unit" / UNIT_PATH).read_text() == UNIT
    audit = json.loads((tmp_path / "call" / "audit.json").read_text())
    assert [v["reason"] for v in audit["violations"]] == [
        f"provider tried to edit a read-only workspace input: {name}" for name in targets]


def test_a_provider_that_starts_a_build_is_refused_and_the_audit_records_it(provider, plan, tmp_path):
    with pytest.raises(Failure, match="started a build; proof_hinting builds nothing: clang\\+\\+"):
        run(provider, plan, tmp_path / "call", mode="build")
    audit = json.loads((tmp_path / "call" / "audit.json").read_text())
    assert [v["code"] for v in audit["violations"]] == ["build"]


def test_a_provider_that_writes_outside_the_workspace_is_refused_and_the_audit_records_it(provider, plan, tmp_path):
    with pytest.raises(Failure, match="outside the workspace: ../outside.txt"):
        run(provider, plan, tmp_path / "call", mode="write_outside")
    audit = json.loads((tmp_path / "call" / "audit.json").read_text())
    assert {v["code"] for v in audit["violations"]} == {"external_write"}
    assert "a file appeared beside the workspace: outside.txt" in audit["reasons"]


def test_the_codex_call_runs_in_its_own_read_only_sandbox_with_the_wrapper_as_its_only_tool(provider, plan, tmp_path):
    _hint_set, metadata = run(provider, plan, tmp_path / "call")
    argv = provider.runs()[0]["argv"]
    assert argv[argv.index("--sandbox") + 1] == "read-only"
    assert "--dangerously-bypass-approvals-and-sandbox" not in argv
    assert ["--disable", "shell_tool"] == argv[argv.index("shell_tool") - 1:argv.index("shell_tool") + 1]
    assert f'mcp_servers.{proof_hinting.SERVER}.args=' in " ".join(argv)
    assert argv[argv.index("--model") + 1] == "gpt-5.6-sol" and 'model_reasoning_effort="xhigh"' in argv
    assert argv[-1] == proof_hinting.PROMPT and provider.runs()[0]["cwd"] == metadata["workspace_manifest"]["root"]
    assert metadata["guard_command"][-1] == proof_hinting.PROMPT
    assert metadata["workspace_manifest"]["confinement"]["shell"] == "off"


def test_the_real_codex_argv_is_confined_the_same_way(tmp_path):
    from swdb import provider_adapters
    folder = tmp_path / "call"
    (folder / "provider-home").mkdir(parents=True)
    config = {"kind": "codex", "command": ["/opt/codex/bin/codex"], "workspace": True}
    argv = provider_adapters.ADAPTERS["codex"].command(config, proof_hinting.PROMPT, folder, proof_hinting.ROLE.output_schema)
    confined = proof_hinting.confine(argv, folder / "wrapper")
    assert confined[:2] == ["/opt/codex/bin/codex", "exec"] and confined[-1] == proof_hinting.PROMPT
    assert confined[confined.index("--sandbox") + 1] == "read-only"
    assert "--dangerously-bypass-approvals-and-sandbox" not in confined
    assert "shell_tool" in confined and confined[confined.index("shell_tool") - 1] == "--disable"
    args = next(w for w in confined if w.startswith(f"mcp_servers.{proof_hinting.SERVER}.args="))
    assert json.loads(args.split("=", 1)[1]) == ["-I", str(proof_hinting.WRAPPER), "--state", str(folder / "wrapper")]


@pytest.mark.parametrize("platform,kind,message", [("linux", "codex", "Linux lab host is not built"),
                                                   ("darwin", "claude", "built for Codex only")])
def test_a_real_provider_without_a_built_confinement_refuses_to_start(platform, kind, message, monkeypatch):
    monkeypatch.setattr(sys, "platform", platform)
    with pytest.raises(Failure, match=message):
        proof_hinting.confinement({"kind": kind})


def test_real_codex_on_the_mac_runs_in_codex_own_read_only_sandbox(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert proof_hinting.confinement({"kind": "codex"}) == {
        "mode": "codex_sandbox_mac", "sandbox": "read-only", "shell": "off", "tools": [proof_hinting.SERVER],
        "adr": "ADR 0006 scoped Mac exception (O3)"}
