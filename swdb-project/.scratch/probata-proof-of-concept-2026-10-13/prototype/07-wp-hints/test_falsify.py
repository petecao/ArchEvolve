# PROTOTYPE (Probata PoC ticket 07, method24), throwaway. Created 2026-10-16 ET.
# Tests of the bounded hint falsifier (falsify/). One shared build+run of the instrumented stand-in.
import json, re, sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "falsify"))
import acsl_eval as A  # noqa: E402
import falsify as F  # noqa: E402


@pytest.fixture(scope="module")
def fz(tmp_path_factory):
    return F.Falsifier(HERE / "standin", tmp_path_factory.mktemp("fz"))


def h(i, anchor, kind, text):
    return {"id": i, "anchor": anchor, "kind": kind, "text": text}


def verdicts(fz, hints):
    return {k: v["verdict"] for k, v in fz.run(hints).items()}


def contract_clauses(kind):
    src = (HERE / "standin" / "tdstep_standin.c").read_text()
    contract = src[src.index("/*@ requires guard_sizes"):src.index("void TDStep(")]
    stop = "ensures|//|\\*/" if kind == "ensures" else "requires|//|assigns"
    return re.findall(rf"{kind} (\w+): (.*?);\n\s*(?={stop})", contract, re.S)


def test_instances_meet_every_named_precondition(fz):
    for name, text in contract_clauses("requires"):
        e = A.parse(text)
        for evs in fz.by_inst.values():
            st = A.State(evs[0])
            assert A.check(A.Ctx({"Pre": st, "Here": st}, "Here", fz.header_defs), e) is True, name


def test_every_postcondition_holds_on_every_run(fz):
    clauses = contract_clauses("ensures")
    assert len(clauses) == 9
    for name, text in clauses:
        e = A.parse(text)
        for evs in fz.by_inst.values():
            ex = [x for x in evs if x["a"] == "stmt:exit"][0]
            ctx = A.Ctx({"Pre": A.State(evs[0]), "Here": A.State(ex)}, "Here", fz.header_defs)
            assert A.check(ctx, e) is True, name


def test_old_state_read_of_a_pushed_position_is_refuted(fz):
    # The pre-method24 pushed_are_new form: queue->shared[i] read in the pre-state.
    bad = h("b", "stmt:after_flush", "assert",
            "assert \\forall integer i; \\at(queue->shared_in,Pre) <= i < queue->shared_in ==> "
            "\\at(parent->start_[queue->shared[i]],Pre) < 0;")
    good = h("g", "stmt:after_flush", "assert",
             "assert \\forall integer i; \\at(queue->shared_in,Pre) <= i < queue->shared_in ==> "
             "\\let w = queue->shared[i]; \\at(parent->start_[w],Pre) < 0;")
    assert verdicts(fz, [bad, good]) == {"b": "refuted", "g": "not_refuted"}


def test_run13_partial_chunk_invariant_is_refuted(fz):
    hints = json.loads((HERE / "falsify" / "fixtures" / "run13_partial_chunk.json").read_text())
    res = fz.run(hints)
    assert res["r1c18h1"]["verdict"] == "refuted"
    assert "td_hit_to" in res["r1c18h1"]["failing_conjunct"]


def test_simple_loop_facts(fz):
    hints = [
        h("i1", "loop:k_loop", "loop_invariant", "loop invariant 0 <= k <= count;"),
        h("i2", "loop:k_loop", "loop_invariant", "loop invariant k < count;"),
        h("v1", "loop:k_loop", "loop_variant", "loop variant count - k;"),
        h("v2", "loop:k_loop", "loop_variant", "loop variant k;"),
        h("v3", "loop:range_loop", "loop_variant",
          "loop variant (dxc_tile_len[c.tile[1]] - dxc_reg[c.reg[4]]) * (num_edges + 2) + (num_edges + 1 - dxc_reg[c.reg[5]]);"),
        h("a1", "loop:i_loop", "loop_assigns",
          "loop assigns i, parent->start_[0 .. num_nodes - 1], lqueue.in, lqueue.local_queue[0 .. 16384 - 1], "
          "queue->shared_in, queue->shared[\\at(queue->shared_in, Pre) .. 36893488147419103231];"),
        h("a2", "loop:i_loop", "loop_assigns", "loop assigns parent->start_[0 .. num_nodes - 1], lqueue.in, "
          "lqueue.local_queue[0 .. 16384 - 1], queue->shared_in, queue->shared[0 .. 36893488147419103231];"),
        h("s1", "stmt:after_wait7", "assert", "assert dxc_pending[c.tile[7]] == 0;"),
    ]
    v = verdicts(fz, hints)
    assert v == {"i1": "not_refuted", "i2": "refuted", "v1": "not_refuted", "v2": "refuted",
                 "v3": "not_refuted", "a1": "not_refuted", "a2": "refuted", "s1": "not_refuted"}


def test_ghost_snapshot_feeds_later_hints(fz):
    hints = [
        h("g1", "stmt:range_start", "ghost", "ghost int m24_old_i = dxc_reg[c.reg[4]];"),
        h("s1", "stmt:after_range_call", "assert", "assert m24_old_i <= dxc_reg[c.reg[4]];"),
        h("s2", "stmt:after_range_call", "assert", "assert m24_old_i < dxc_reg[c.reg[4]];"),
    ]
    v = verdicts(fz, hints)
    assert v["s1"] == "not_refuted" and v["s2"] == "refuted"


def test_unbounded_existential_never_refutes(fz):
    # A witness may lie outside the finite window, so a false unbounded \exists is not a counterexample.
    hints = [h("e1", "stmt:entry", "assert", "assert \\exists integer x; x * x == 4096 * 4096;")]
    assert verdicts(fz, hints)["e1"] == "unchecked"


def test_report_names_the_counterexample(fz):
    hints = [h("i2", "loop:k_loop", "loop_invariant", "loop invariant k < count;")]
    text = F.report_text(hints, fz.run(hints))
    assert "i2 (loop_invariant at loop:k_loop) is FALSE" in text and "input: num_nodes=" in text


def test_review_s1_true_hints_are_not_refuted(fz):
    # Review 2026-10-16 S1: C types of quantified variables, casts, ghost storage types, the range-loop
    # break visit and moving loop-assigns ranges must not produce false refutations.
    hints = [
        h("q1", "stmt:entry", "assert", "assert \\forall unsigned x; x < 3 ==> x >= 0;"),
        h("q2", "stmt:entry", "assert", "assert \\forall size_t p; p < queue->shared_in ==> p + 1 > 0;"),
        h("c1", "stmt:entry", "assert", "assert (unsigned)(num_nodes - num_nodes - 1) == 4294967295;"),
        h("g1", "stmt:k_start", "ghost", "ghost unsigned m24_m = k - 1;"),
        h("g2", "stmt:k_start", "assert", "assert k == 0 ==> m24_m == 4294967295;"),
        h("g3", "stmt:entry", "ghost", "ghost int m24_a = 1; m24_b = 2;"),
        # -1 exactly at the visit that breaks out (state (n, -1)), >= 0 and decreasing on every back edge.
        h("v1", "loop:range_loop", "loop_variant",
          "loop variant (dxc_tile_len[c.tile[1]] - dxc_reg[c.reg[4]]) * (num_edges + 2) + (num_edges + 1 - dxc_reg[c.reg[5]]) - (num_edges + 3);"),
        h("a1", "loop:i_loop", "loop_assigns",
          "loop assigns i, parent->start_[0 .. num_nodes - 1], lqueue.in, lqueue.local_queue[0 .. 16384 - 1], "
          "queue->shared_in, queue->shared[queue->shared_in .. 36893488147419103231];"),
    ]
    v = verdicts(fz, hints)
    assert all(v[k] != "refuted" for k in ("q1", "q2", "c1", "g2", "v1", "a1")), v


def test_review_s1_casts_and_types_still_refute_false_hints(fz):
    hints = [
        h("c2", "stmt:entry", "assert", "assert (unsigned)(num_nodes - num_nodes - 1) == -1;"),
        # Does not decrease when one row fills a whole tile (the row index stays the same).
        h("v2", "loop:range_loop", "loop_variant", "loop variant dxc_tile_len[c.tile[1]] - dxc_reg[c.reg[4]];"),
    ]
    v = verdicts(fz, hints)
    assert v["c2"] == "refuted" and v["v2"] == "refuted"


def test_run27_constructs_are_evaluated(fz):
    # Run 27 hints the first falsifier could not evaluate: a local struct's address and nested slices.
    hints = [
        h("b1", "loop:k_loop", "loop_invariant", "loop invariant gapbs_buffer_domain(&lqueue) && lqueue.in <= lqueue.local_size;"),
        h("b2", "loop:k_loop", "loop_invariant", "loop invariant (&lqueue)->in < lqueue.in;"),
        h("a1", "loop:chunk_loop", "loop_assigns",
          "loop assigns begin, parent->start_[0 .. num_nodes-1], lqueue.in, lqueue.local_queue[0 .. lqueue.local_size-1], "
          "queue->shared_in, queue->shared[\\at(queue->shared_in,Pre) .. num_nodes-1], "
          "dxc_tile_data[0 .. DXC_NUM_TILES-1][0 .. TILE_SIZE-1], dxc_tile_len[0 .. DXC_NUM_TILES-1], "
          "dxc_reg[0 .. DXC_NUM_REGS-1], dxc_pending[0 .. DXC_NUM_TILES-1], dxc_dep[0 .. DXC_NUM_TILES*DXC_NUM_TILES-1];"),
        h("a2", "loop:chunk_loop", "loop_assigns",
          "loop assigns begin, parent->start_[0 .. num_nodes-1], lqueue.in, lqueue.local_queue[0 .. lqueue.local_size-1], "
          "queue->shared_in, queue->shared[\\at(queue->shared_in,Pre) .. num_nodes-1], "
          "dxc_tile_data[0 .. 1][0 .. TILE_SIZE-1], dxc_tile_len[0 .. DXC_NUM_TILES-1], "
          "dxc_reg[0 .. DXC_NUM_REGS-1], dxc_pending[0 .. DXC_NUM_TILES-1], dxc_dep[0 .. DXC_NUM_TILES*DXC_NUM_TILES-1];"),
    ]
    v = verdicts(fz, hints)
    assert v == {"b1": "not_refuted", "b2": "refuted", "a1": "not_refuted", "a2": "refuted"}, v
