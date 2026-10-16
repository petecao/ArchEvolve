#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, method24), throwaway. Created 2026-10-16 ET.
# The bounded hint falsifier (method24 step 3, approved by Yan-Ru 2026-10-16 12:46 ET). It runs the
# instrumented hint-free stand-in (build.py) on every instance of instances.py and evaluates each hint
# on the recorded states: assertions at their anchor, loop invariants at every loop-head visit, loop
# variants across consecutive visits, loop assigns as a frame check against LoopEntry. A hint that
# evaluates to false on one recorded state is false (a concrete counterexample); everything else is
# "not refuted" and still needs WP. It never proves anything and never changes a verdict: it is a
# filter in front of WP. Lemmas, strategies and attachments are not evaluated.
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import acsl_eval as A  # noqa: E402
import build as B  # noqa: E402
import instances as I  # noqa: E402

LOOPS = ("chunk_loop", "range_loop", "k_loop", "i_loop", "j_loop")
HEADERS = ("dxc_summaries.h", "gapbs_models.h", "bfs_unit.h")
MAX_EVENTS_PER_HINT = 4000


def strip_kw(text, kw):
    t = text.strip()
    assert t.startswith(kw), (t, kw)
    t = t[len(kw):].strip()
    if t.endswith(";"):
        t = t[:-1]
    return t


class Falsifier:
    def __init__(self, standin_dir, work_dir, count=2000, seed=7):
        self.standin_dir = Path(standin_dir)
        self.work = Path(work_dir)
        self.exe = B.build(self.standin_dir, self.work / "build")
        self.rows = I.instances(count, seed)
        text = "\n".join(" ".join(map(str, r)) for r in self.rows) + "\n"
        r = subprocess.run([str(self.exe)], input=text, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise RuntimeError(f"falsifier run failed ({r.returncode}): {r.stdout[-400:]} {r.stderr[-2000:]}")
        self.by_inst = {}
        for ln in r.stdout.splitlines():
            ev = json.loads(ln)
            if "pre" in ev:
                raise RuntimeError(f"model precondition violated on instance {ev['inst']}: {ev['pre']}")
            if ev.get("end"):
                continue
            self.by_inst.setdefault(ev["inst"], []).append(ev)
        self.header_defs = {}
        for h in HEADERS:
            self.header_defs.update(A.header_definitions((self.standin_dir / h).read_text()))

    # ---- one hint set ----
    def run(self, hints):
        defs = dict(self.header_defs)
        results = {}
        parsed = {}
        for h in hints:
            kind, hid = h["kind"], h["id"]
            try:
                if kind in ("predicate", "logic"):
                    name, d = A.parse_definition(h["text"].strip())
                    defs[name] = d
                    results[hid] = {"verdict": "not_evaluated", "why": "definition"}
                elif kind == "loop_invariant":
                    parsed[hid] = ("inv", A.parse(strip_kw(h["text"], "loop invariant")))
                elif kind == "assert":
                    parsed[hid] = ("assert", A.parse(strip_kw(h["text"], "assert")))
                elif kind == "loop_variant":
                    parsed[hid] = ("var", A.parse(strip_kw(h["text"], "loop variant")))
                elif kind == "loop_assigns":
                    body = strip_kw(h["text"], "loop assigns")
                    parsed[hid] = ("assigns", [] if body.strip() == "\\nothing" else
                                   [A.parse(x) for x in split_top(body)])
                elif kind == "ghost":
                    parsed[hid] = ("ghost", parse_ghost(h["text"]))
                else:
                    results[hid] = {"verdict": "not_evaluated", "why": kind}
            except (A.Unknown, AssertionError) as e:
                results[hid] = {"verdict": "not_evaluated", "why": f"unsupported: {e}"}
        by_anchor = {}
        for h in hints:
            if h["id"] in parsed:
                by_anchor.setdefault(h["anchor"], []).append(h)
        stats = {hid: {"checked": 0, "unknown": 0} for hid in parsed}
        refuted = {}
        for inst, evs in self.by_inst.items():
            self._instance(inst, evs, by_anchor, parsed, defs, stats, refuted)
        for h in hints:
            hid = h["id"]
            if hid in results:
                continue
            if hid in refuted:
                results[hid] = {"verdict": "refuted", **refuted[hid]}
            elif parsed[hid][0] == "ghost":
                results[hid] = {"verdict": "not_evaluated", "why": "ghost statement (executed for later hints)"}
            elif stats[hid]["checked"] == 0:
                results[hid] = {"verdict": "unchecked", "why": f"no evaluable state ({stats[hid]['unknown']} unknown)"}
            else:
                results[hid] = {"verdict": "not_refuted", **stats[hid]}
        return results

    def _instance(self, inst, evs, by_anchor, parsed, defs, stats, refuted):
        pre = None
        ghost, gtypes = {}, {}
        unions = {}     # (hint, loop instance) -> covered locations over all visits so far
        stack = []      # [loop, entry_state, last_state, entry_index]
        heads = {}      # (loop entry seq) -> [(state, seq)]
        for ev in evs:
            a = ev["a"]
            if a.startswith("stmt:after_") and a[len("stmt:after_"):] in LOOPS:
                lp = a[len("stmt:after_"):]
                while stack:
                    top = stack.pop()
                    if top[0] == lp:
                        self._variants(inst, top, heads, by_anchor, parsed, defs, stats, refuted, pre)
                        break
            st = A.State(ev, ghost)
            if pre is None:
                pre = st
            if a.startswith("loop:"):
                lp = a[5:]
                if stack and stack[-1][0] == lp:
                    stack[-1][2] = st
                else:
                    stack.append([lp, st, st, ev["seq"]])
                heads.setdefault((lp, stack[-1][3]), []).append(st)
            labels = {"Pre": pre, "Here": st}
            if stack:
                labels["LoopEntry"] = stack[-1][1]
                labels["LoopCurrent"] = stack[-1][2]
            for h in by_anchor.get(a, []):
                hid = h["id"]
                kind, e = parsed[hid]
                if hid in refuted and kind != "ghost":
                    continue
                ctx = A.Ctx(labels, "Here", defs)
                if kind == "ghost":
                    for name, ty, rhs in e:
                        if ty is not None:
                            gtypes[name] = ty
                        try:
                            val = A.eval_term(A.Ctx(labels, "Here", defs), rhs) if rhs is not None else 0
                            ghost[name] = A.convert(gtypes.get(name, ("integer", 0)), val)
                        except A.Unknown:
                            ghost.pop(name, None)
                        st.ghost = dict(ghost)
                    continue
                if stats[hid]["checked"] + stats[hid]["unknown"] > MAX_EVENTS_PER_HINT:
                    continue
                if kind in ("inv", "assert"):
                    r = A.check(ctx, e)
                    self._record(hid, r, inst, ev, st, e, ctx, stats, refuted)
                elif kind == "assigns" and stack:
                    acc = unions.setdefault((hid, stack[-1][3]), [set(), set(), set(), True])
                    if acc[3]:
                        try:
                            for loc in e:
                                cover(ctx, loc, acc[0], acc[1], acc[2])
                        except A.Unknown:
                            acc[3] = False
                    if st is stack[-1][1]:
                        continue
                    r, why = frame_check(ctx, e, stack[-1][1], st, acc if acc[3] else None)
                    if r is False:
                        refuted[hid] = {"instance": I.describe(self.rows[inst]), "anchor": a,
                                        "visit": visit_no(heads, stack), "detail": why,
                                        "locals": scalars(st)}
                    else:
                        stats[hid]["checked" if r else "unknown"] += 1

    def _variants(self, inst, top, heads, by_anchor, parsed, defs, stats, refuted, pre):
        lp = top[0]
        seq = heads.get((lp, top[3]), [])
        for h in by_anchor.get("loop:" + lp, []):
            hid = h["id"]
            if parsed[hid][0] != "var" or hid in refuted:
                continue
            vals = []
            for st in seq:
                ctx = A.Ctx({"Pre": pre, "Here": st, "LoopEntry": seq[0], "LoopCurrent": st}, "Here", defs)
                try:
                    v = A.eval_term(ctx, parsed[hid][1])
                except A.Unknown:
                    v = None
                vals.append(v if isinstance(v, int) else None)
            # The variant must be >= 0 and decrease from each visit to the next visit of the same loop instance.
            # WP 33 checks positivity only on the back edge (cfgAnnot.ml:441-449): visits followed by another visit.
            entered = len(vals) - 1
            for t in range(entered):
                v = vals[t]
                if v is None:
                    stats[hid]["unknown"] += 1
                    continue
                bad = None
                if v < 0:
                    bad = f"variant is {v} < 0 at visit {t + 1}, which enters the loop body"
                elif t + 1 < len(vals) and vals[t + 1] is not None and vals[t + 1] >= v:
                    bad = f"variant does not decrease: {v} at visit {t + 1}, {vals[t + 1]} at visit {t + 2}"
                if bad:
                    refuted[hid] = {"instance": I.describe(self.rows[inst]), "anchor": "loop:" + lp,
                                    "visit": t + 1, "detail": bad, "locals": scalars(seq[t])}
                    break
                stats[hid]["checked"] += 1

    def _record(self, hid, r, inst, ev, st, e, ctx, stats, refuted):
        if r is None:
            stats[hid]["unknown"] += 1
            return
        if r:
            stats[hid]["checked"] += 1
            return
        failing = None
        for part in A.conjuncts(e):
            if A.check(ctx, part) is False:
                failing = part[-1] if isinstance(part[-1], str) else None
                break
        refuted[hid] = {"instance": I.describe(self.rows[inst]), "anchor": ev["a"], "event": ev["seq"],
                        "failing_conjunct": failing, "locals": scalars(st)}


def visit_no(heads, stack):
    return len(heads.get((stack[-1][0], stack[-1][3]), []))


def scalars(st):
    out = {}
    for k, v in st.loc.items():
        if isinstance(v, (int, bool)):
            out[k] = int(v)
        elif isinstance(v, dict) and k == "lqueue":
            out["lqueue.in"] = v.get("in")
        elif isinstance(v, dict) and k == "c":
            out["c.tile"] = v.get("tile")
            out["c.reg"] = v.get("reg")
    out.update({k: v for k, v in st.ghost.items() if isinstance(v, int)})
    out["dxc_reg"] = st.mem.get("dxc_reg")
    out["dxc_tile_len"] = st.mem.get("dxc_tile_len")
    out["parent.start_"] = st.mem.get("parent.start_")
    out["queue.shared"] = st.mem.get("queue.shared")
    out["queue.shared_in"] = st.mem.get("Q", {}).get("shared_in")
    return out


def split_top(text):
    parts, lvl, cur = [], 0, ""
    for ch in text:
        if ch in "([{":
            lvl += 1
        elif ch in ")]}":
            lvl -= 1
        if ch == "," and lvl == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def parse_ghost(text):
    """[(name, type or None, rhs expr or None)] for each `T x = e;`, `T x;` or `x = e;` statement."""
    t = text.strip()
    assert t.startswith("ghost"), t
    t = t[len("ghost"):]
    stmts = []
    for st in [x.strip() for x in t.split(";") if x.strip()]:
        if "=" in st and not any(op in st.split("=", 1)[0] for op in "<>!"):
            lhs, rhs = st.split("=", 1)
            rhs_e = A.parse(rhs.strip())
        else:
            lhs, rhs_e = st, None
        words = lhs.replace("*", " * ").split()
        name = words[-1]
        ty = (" ".join(w for w in words[:-1] if w != "*"), words.count("*")) if len(words) > 1 else None
        stmts.append((name, ty, rhs_e))
    return stmts


def frame_check(ctx, locs, entry, here, acc=None):
    """False (with reason) if a location changed since LoopEntry lies outside the union of the loop assigns
    evaluated at every loop-head visit from LoopEntry to Here (sound under either reading of WP's frame)."""
    if acc is None:
        return None, None
    covered_mem, covered_loc, covered_struct = acc[0], acc[1], acc[2]
    for blk, vals in here.mem.items():
        if isinstance(vals, list) and blk in entry.mem and blk not in ("dxc_tile_data", "swdb_contexts"):
            for i, (x, y) in enumerate(zip(entry.mem[blk], vals)):
                if x != y and (blk, i) not in covered_mem and not any(
                        b == blk and isinstance(r, tuple) and r[1] <= i <= r[2] for b, r in covered_mem):
                    return False, f"{blk}[{i}] changed from {x} to {y} since LoopEntry but is not in the loop assigns"
    for f, y in here.mem.get("Q", {}).items():
        if entry.mem["Q"].get(f) != y and ("Q", f) not in covered_struct:
            return False, f"queue->{f} changed since LoopEntry but is not in the loop assigns"
    for name, y in here.loc.items():
        if name not in entry.loc:
            continue
        x = entry.loc[name]
        if isinstance(y, dict):
            for f in y:
                if x.get(f) != y[f] and name not in covered_loc and (name, f) not in covered_loc:
                    return False, f"{name}.{f} changed since LoopEntry but is not in the loop assigns"
        elif x != y and name not in covered_loc:
            return False, f"local {name} changed since LoopEntry but is not in the loop assigns"
    return True, None


def cover(ctx, e, mem, loc, struct):
    k = e[0]
    if k == "id":
        n = e[1]
        here = ctx.labels["Here"]
        if n in here.loc:
            loc.add(n)
            return
        v = A.ident(ctx, n)
        if isinstance(v, A.Ptr) and v.b in here.mem:
            mem.add((v.b, ("range", 0, here.dumped.get(v.b, 0))))
            return
        raise A.Unknown("location")
    if k == "dot" and e[1][0] == "id" and e[1][1] in ctx.labels["Here"].loc:
        loc.add((e[1][1], e[2]))
        return
    if k == "arrow":
        p = A.eval_term(ctx, e[1])
        if isinstance(p, A.Ptr) and p.b == "Q":
            struct.add(("Q", e[2]))
            return
        raise A.Unknown("location")
    if k == "idx":
        p = A.eval_term(ctx, e[1])
        i = A.eval_term(ctx, e[2])
        if isinstance(p, A.Ptr) and isinstance(i, int):
            mem.add((p.b, p.i + i))
            return
        raise A.Unknown("location")
    if k == "slice":
        p = A.eval_term(ctx, e[1])
        lo, hi = A.eval_term(ctx, e[2]), A.eval_term(ctx, e[3])
        if isinstance(p, A.Ptr) and isinstance(lo, int) and isinstance(hi, int):
            mem.add((p.b, ("range", p.i + lo, p.i + hi)))
            return
        raise A.Unknown("location")
    raise A.Unknown("location kind")


def report_text(hints, results, limit=12):
    """Feedback for the proof-hint agent: refuted hints first, with the concrete counterexample."""
    by_id = {h["id"]: h for h in hints}
    lines = []
    ref = [hid for hid, r in results.items() if r["verdict"] == "refuted"]
    for hid in ref[:limit]:
        r, h = results[hid], by_id[hid]
        lines.append(f"- {hid} ({h['kind']} at {h['anchor']}) is FALSE on a concrete execution:")
        lines.append(f"    input: {r['instance']}")
        where = f"at {r['anchor']}" + (f", visit {r['visit']}" if r.get("visit") else "")
        lines.append(f"    {where}; state: {json.dumps(r['locals'])}")
        if r.get("failing_conjunct"):
            lines.append(f"    false conjunct: {r['failing_conjunct'][:400]}")
        if r.get("detail"):
            lines.append(f"    {r['detail']}")
    if len(ref) > limit:
        lines.append(f"- ... and {len(ref) - limit} more refuted hints: {', '.join(ref[limit:])}")
    unchecked = [hid for hid, r in results.items() if r["verdict"] in ("unchecked",) or
                 (r["verdict"] == "not_evaluated" and r.get("why", "").startswith("unsupported"))]
    if unchecked:
        lines.append(f"- not checked by the falsifier (unsupported or never evaluable): {', '.join(unchecked)}")
    return "\n".join(lines) if lines else "- no hint refuted on the bounded inputs"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--standin", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--hints", required=True, help="JSON file: a list of hints or {hints: [...]}")
    ap.add_argument("--count", type=int, default=2000)
    a = ap.parse_args()
    data = json.loads(Path(a.hints).read_text())
    hs = data["hints"] if isinstance(data, dict) else data
    F = Falsifier(a.standin, a.work, a.count)
    res = F.run(hs)
    print(report_text(hs, res))
    print(json.dumps({k: v["verdict"] for k, v in res.items()}, indent=1))
