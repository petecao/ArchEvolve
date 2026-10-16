# PROTOTYPE (Probata PoC ticket 07, method24), throwaway. Created 2026-10-16 ET.
# Tests of the method24 driver and its in-call tool server that need no prover.
import io, json, sys, time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hints as H  # noqa: E402
import loop as L  # noqa: E402
import m24  # noqa: E402
import m24_tool as T  # noqa: E402


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    out = tmp_path_factory.mktemp("m24")
    state = out / "state"
    state.mkdir()
    (state / "config.json").write_text(json.dumps({
        "out": str(out), "t0": time.time(), "budget_min": 60, "final_reserve_min": 9, "round": 1,
        "ladder": [3, 10], "pin": L.PIN, "owner": "t07f-test"}))
    return T.Server(state)


def rpc(server, *msgs):
    fin = io.StringIO("".join(json.dumps(m) + "\n" for m in msgs))
    fout = io.StringIO()
    server.serve(fin, fout)
    return [json.loads(x) for x in fout.getvalue().splitlines()]


def test_tools_listed(server):
    r = rpc(server, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert {t["name"] for t in r[0]["result"]["tools"]} == {"falsify_hints", "check_hints", "prove_hints", "show_goal"}


def test_falsify_tool_reports_counterexample(server):
    args = {"hints": [{"anchor": "loop:k_loop", "kind": "loop_invariant", "text": "loop invariant k < count;"}]}
    r = rpc(server, {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                     "params": {"name": "falsify_hints", "arguments": args}})
    text = r[0]["result"]["content"][0]["text"]
    assert "1 hint(s) refuted" in text and "input: num_nodes=" in text
    rec = json.loads((server.state / "submissions.jsonl").read_text().splitlines()[-1])
    assert rec["tool"] == "falsify_hints" and rec["hints"][0]["provenance"].startswith("codex ")


def test_prove_refuses_a_refuted_set_before_wp(server):
    args = {"hints": [{"anchor": "loop:k_loop", "kind": "loop_invariant", "text": "loop invariant k < count;"}]}
    r = rpc(server, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                     "params": {"name": "prove_hints", "arguments": args}})
    assert r[0]["result"]["content"][0]["text"].startswith("Not sent to WP.")
    assert not list(Path(server.cfg["out"]).glob("r1-c*"))  # no run folder was created


def test_vocabulary_rejection_in_falsify(server):
    args = {"hints": [{"anchor": "global", "kind": "lemma", "text": "lemma x: \\forall integer a; a == a; requires"}]}
    r = rpc(server, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                     "params": {"name": "falsify_hints", "arguments": args}})
    assert "Rejected by the vocabulary check" in r[0]["result"]["content"][0]["text"]


def test_negative_control_removes_only_the_covering_wait():
    merged = H.merge((L.STANDIN_DIR / L.UNIT).read_text(), [])
    neg = m24.negctl_source(merged)
    assert "__dxc_wait(c.tile[5]);" not in neg and "__dxc_wait(c.tile[3]);" in neg
    assert len(neg.splitlines()) == len(merged.splitlines())


def test_prompt_formats_and_names_the_tools():
    text = m24.PROMPT.format(budget=60, reserve=9, minutes=1.0, round=1, rounds=10, feedback="fb", files="files")
    for name in ("falsify_hints", "check_hints", "prove_hints", "show_goal"):
        assert name in text
    # Generic guidance only (review S4): no names of this unit outside the workspace section.
    guidance = text.split("=== Workspace")[0]
    for word in ("BFS", "frontier", "queue", "parent", "shared", "TDStep_", "dxc_reg", "chunk"):
        assert word not in guidance, word


def test_report_reader_keeps_unexpected_statuses():
    rep = ("[report] Computing properties status...\n--- Properties of Function 'TDStep'\n"
           "[    Bug    ] Assertion 'x' (file tdstep_standin.c, line 3)\n"
           "[  Valid  ] Post-condition 'y' (file tdstep_standin.c, line 4)\n")
    props = H.read_report(rep)
    assert [p["status"] for p in props] == ["Bug", "Valid"]
    assert [p["status"] for p in H.verdict_problems(props, set())] == ["Bug"]
