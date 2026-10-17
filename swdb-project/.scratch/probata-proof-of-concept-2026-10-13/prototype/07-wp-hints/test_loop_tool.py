# PROTOTYPE (Probata PoC ticket 07, continuation t07c), throwaway. Created 2026-10-14 ET.
# Updated 2026-10-15 ET: fail-closed ghost-witness ownership guard.
# Seam: how the loop reads the in-call tool's submissions (method change d).
import json

import loop as L

H1 = [{"id": "a", "anchor": "stmt:entry", "kind": "assert", "text": "assert num_nodes >= 0;"}]
H2 = [{"id": "b", "anchor": "stmt:entry", "kind": "assert", "text": "assert num_edges >= 0;"}]


def write_subs(tmp_path, subs, r=1, turn=0):
    st = tmp_path / f"tool-r{r}-t{turn}"
    st.mkdir()
    (st / "submissions.jsonl").write_text("".join(json.dumps(s) + "\n" for s in subs))


def test_codex_stopped_at_deadline_falls_back_to_the_best_proven_submission(tmp_path):
    write_subs(tmp_path, [
        {"n": 1, "tool": "prove_hints", "result": "not all proven", "n_failing": 9, "hints": H1, "lockwait_total_s": 5},
        {"n": 2, "tool": "prove_hints", "result": "not all proven", "n_failing": 3, "hints": H2, "lockwait_total_s": 7},
        {"n": 3, "tool": "check_hints", "result": "check failed", "hints": H1, "lockwait_total_s": 7}])
    L.LOCKWAIT[0] = 0.0
    c = {"hints": None, "error": "no final.json"}
    L.pick_tool_result(tmp_path, 1, 0, c)
    assert c["hints"] == H2 and c["tool"]["fallback_from_submission"] == 2 and c["error"] is None
    assert L.LOCKWAIT[0] == 7 and c["tool"]["prove_calls"] == 2


def test_a_returned_set_the_tool_proved_reuses_its_round_run(tmp_path):
    write_subs(tmp_path, [
        {"n": 1, "tool": "prove_hints", "result": "all proven (round mode)", "n_failing": 0, "hints": H1,
         "dir": "/x/round-1t0-call1", "lockwait_total_s": 0}])
    c = {"hints": [dict(H1[0], id="r1t0h1")], "error": None}
    L.pick_tool_result(tmp_path, 1, 0, c)
    assert c["proved_dir"] == "/x/round-1t0-call1"
    c2 = {"hints": H2, "error": None}
    L.pick_tool_result(tmp_path, 1, 0, c2)
    assert "proved_dir" not in c2


def test_a_returned_unproven_set_reuses_its_round_run_too(tmp_path):
    write_subs(tmp_path, [
        {"n": 1, "tool": "prove_hints", "result": "not all proven", "n_failing": 4, "hints": H2,
         "dir": "/x/call1", "lockwait_total_s": 0},
        {"n": 2, "tool": "prove_hints", "result": "wp failed", "hints": H1, "dir": "/x/call2", "lockwait_total_s": 0}])
    c = {"hints": H2, "error": None}
    L.pick_tool_result(tmp_path, 1, 0, c)
    assert c["proved_dir"] == "/x/call1"
    c2 = {"hints": H1, "error": None}
    L.pick_tool_result(tmp_path, 1, 0, c2)
    assert "proved_dir" not in c2


def test_precheck_rejects_model_shadow_before_any_verifier_call(tmp_path, monkeypatch):
    def forbidden_verifier(*args, **kwargs):
        raise AssertionError("unsafe ghost hint reached a verifier")
    monkeypatch.setattr(L, "verifier", forbidden_verifier)
    standin = (L.STANDIN_DIR / L.UNIT).read_text()
    hs = [{"id": "shadow", "anchor": "stmt:entry", "kind": "ghost",
           "text": "ghost int dxc_pending = 0;"}]
    record = {}
    assert L.precheck(tmp_path, "unsafe", standin, hs, record) is None
    assert record["outcome"] == "rejected (proof hint check)"
    assert any(r["rule"] == "ghost_ownership" for r in record["rejections"])
    assert not (tmp_path / "unsafe").exists()
