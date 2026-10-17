"""2026-10-16 ET. Pure source/algebra controls; not native C execution.

The small independent deferred interpreter tests the guard/selection protocol;
the range loop is transcribed separately from pinned primary source. Emitted C
still requires independent source review and a root-admitted native profile.
"""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("no-child value preparation: " + event)


sys.addaudithook(no_child)
HERE = Path(__file__).resolve().parent


def owned(name):
    path = HERE / (name + ".py")
    namespace = {"__file__": str(path), "__name__": "value_source_controls"}
    exec(compile(ast.parse(path.read_bytes()), str(path), "exec"), namespace)
    return namespace


VALUES = owned("value_builders")


class GuardFailure(ValueError):
    pass


class Deferred:
    """Independent lazy, immutable-ID oracle; not a model of native C memory."""
    def __init__(self):
        self.nodes = []
        self.covered = {}

    def node(self, kind, *args):
        if kind in ("select", "require", "add"):
            for parent in args[:3 if kind == "select" else 2]:
                if type(parent) is not int or not 0 <= parent < len(self.nodes):
                    raise GuardFailure("acyclic IDs")
        self.nodes.append((kind, args))
        return len(self.nodes) - 1

    def cover(self, identity):
        if identity in self.covered: return self.covered[identity]
        kind, args = self.nodes[identity]
        if kind == "constant": value = args[0]
        elif kind == "poison": raise GuardFailure("uninitialized selected value")
        elif kind == "history": value = args[0][-1]
        elif kind == "select": value = self.cover(args[1] if self.cover(args[0]) else args[2])
        elif kind == "require":
            if not self.cover(args[0]): raise GuardFailure(args[2])
            value = self.cover(args[1])
        elif kind == "add": value = self.cover(args[0]) + self.cover(args[1])
        else: raise GuardFailure("unknown oracle kind")
        self.covered[identity] = value
        return value


def source_range(mins, maxs, conditions, start_i, start_j, stride, source_capacity=16384):
    """RangeFuser.cc Work/Finish projection under the explicit signed domain."""
    if start_i < 0 or start_j < -1 or stride <= 0: raise GuardFailure("range domain")
    output, i, j = [], start_i, start_j
    while True:
        if i >= len(mins): break
        if len(output) >= source_capacity: break
        if conditions is None or conditions[i]:
            if mins[i] is None or maxs[i] is None: raise GuardFailure("selected uninitialized")
            if not 0 <= mins[i] <= 2147483647 or not 0 <= maxs[i] <= 2147483647:
                raise GuardFailure("conversion domain")
            if j == -1: j = mins[i]
            while j < maxs[i] and len(output) < source_capacity:
                output.append((i, j));j += stride
                if j > 2147483647: raise GuardFailure("signed postincrement")
            if j >= maxs[i]: j = -1
            elif len(output) == source_capacity: break
        i += 1
    return output, i, j


def prefix_range(mins, maxs, conditions, start_i, start_j, stride, bound=2):
    """Independent closed-form count/slot projection used by the builder."""
    if len(mins) > bound or start_i < 0 or start_j < -1 or stride <= 0: raise GuardFailure("range domain")
    output, j = [], start_j
    for row in range(len(mins)):
        if row < start_i or conditions is not None and not conditions[row]: continue
        lo, hi = mins[row], maxs[row]
        if lo is None or hi is None: raise GuardFailure("selected uninitialized")
        if not 0 <= lo <= 2147483647 or not 0 <= hi <= 2147483647: raise GuardFailure("conversion domain")
        start = lo if j == -1 else j
        count = 0 if start >= hi else (hi - start - 1) // stride + 1
        if start + count * stride > 2147483647: raise GuardFailure("signed postincrement")
        if len(output) + count > bound: raise GuardFailure("value prefix")
        output += [(row, start + k * stride) for k in range(count)]
        j = -1
    return output, max(start_i, len(mins)), j


class ValueControls(unittest.TestCase):
    def test_01_exact_delta_and_all_closed_routes(self):
        original = (HERE / "whole_backend.h").read_text()
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), VALUES["BASE_SHA256"])
        extended = VALUES["extend_backend"](original)
        tree = ast.parse((HERE / "value_builders.py").read_bytes())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "extend_backend")
        changes = ast.literal_eval(next(n.value for n in function.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "changes" for t in n.targets)))
        self.assertEqual(len(changes), 6)
        for old, new in reversed(changes):
            self.assertEqual(extended.count(new), 1);extended = extended.replace(new, old, 1)
        self.assertEqual(extended, original)
        with self.assertRaises(ValueError): VALUES["extend_backend"](original + "\n")
        declarations = json.loads((HERE / "declarations.json").read_text())
        routes = VALUES["render_closed_routes"](declarations)
        self.assertEqual(len(re.findall(r"static unsigned dxw_call_", routes)), 11)
        self.assertNotIn("dwi_value_builder", routes)
        for row in declarations:
            if "packet" not in row: continue
            op = row["packet"]["opcode"]
            expected = "dxw_alu" if op >= 8 else "dxw_range" if op == 7 else "dxw_stream" if op <= 1 else "dxw_indirect"
            body = routes.split("dxw_call_" + row["name"] + "(", 1)[1].split("\n}", 1)[0]
            self.assertIn(", " + expected + ", ", body)
        builders = VALUES["render_builders"]()
        self.assertNotRegex(builders, r"\bdxm_(?:cover|value)\s*\(")
        for name in ("dxw_alu", "dxw_indirect", "dxw_stream", "dxw_range"):
            self.assertIn("static unsigned " + name + "(", builders)

    def test_02_guard_first_and_inactive_initializedness(self):
        d = Deferred();zero=d.node("constant",0);one=d.node("constant",1);poison=d.node("poison")
        masked=d.node("select",zero,poison,one)
        self.assertEqual(d.cover(masked),1)
        guard=d.node("require",zero,poison,"classified guard before right value")
        with self.assertRaisesRegex(GuardFailure,"classified guard before right value"): d.cover(guard)
        live=d.node("select",one,poison,zero)
        with self.assertRaisesRegex(GuardFailure,"uninitialized selected value"): d.cover(live)

    def test_03_immutable_versions_and_history_choose_at_cover(self):
        d=Deferred();history=[2];read=d.node("history",history);three=d.node("constant",3)
        output=d.node("add",read,three)
        self.assertEqual(d.covered,{})
        history.append(7)
        self.assertEqual(d.cover(output),10)
        history.append(9)
        self.assertEqual(d.cover(output),10)
        newer=d.node("history",history)
        self.assertEqual(d.cover(newer),9)
        # A new current version never rewrites an earlier captured parent ID.
        replacement=d.node("constant",100)
        self.assertNotEqual(replacement,read)
        self.assertEqual(d.cover(output),10)

    def test_04_range_primary_loop_against_closed_form(self):
        cases = [([4,None],[6,None],[1,0],0,-1,1),
                 ([4,None],[7,None],[1,0],0,5,1),
                 ([4,8],[4,9],None,0,-1,1),
                 ([None,8],[None,9],[0,1],0,8,1),
                 ([],[],None,0,-1,1),
                 ([None],[None],[0],2,7,1)]
        for args in cases:
            self.assertEqual(prefix_range(*args),source_range(*args))
        for start_i in range(4):
            for start_j in (-1,0,1,2):
                for stride in (1,2,3):
                    args=([0,1],[1,2],[1,1],start_i,start_j,stride)
                    self.assertEqual(prefix_range(*args),source_range(*args))
        with self.assertRaisesRegex(GuardFailure,"value prefix"): prefix_range([0],[3],None,0,-1,1)
        with self.assertRaisesRegex(GuardFailure,"signed postincrement"):
            prefix_range([2147483646],[2147483647],None,0,-1,2)
        with self.assertRaises(GuardFailure): prefix_range([0],[1],None,0,-2,1)
        with self.assertRaises(GuardFailure): prefix_range([0],[1],None,0,-1,0)

    def test_05_native_controls_remain_inert(self):
        source=(HERE / "whole_values_native_v1.c").read_text()
        self.assertIn("dxw_controls==86",source)
        self.assertIn('"source-minus-accumulator-order"',source)
        self.assertIn('"other-thread-history-through-dependent-alu"',source)
        self.assertIn('"progressive-old-second-lane"',source)
        self.assertNotRegex(source,r"\b(?:system|fork|execve|popen|dlopen)\s*\(")
        primary=HERE / "source/gem5-e4fc4af"
        pins={"RangeFuser.cc":"27a3713469a44031829d638b3e865f714cd63a0423c493d78cbcc07dd9b7d42e",
              "RangeFuser.hh":"1794c7469f5b88e0ed36adb129f632d4370cf8adf983892b100b65a79cb88218"}
        for name,expected in pins.items(): self.assertEqual(hashlib.sha256((primary/name).read_bytes()).hexdigest(),expected)


if __name__ == "__main__":
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ValueControls))
    print(json.dumps({"date":"2026-10-16","test_cases":result.testsRun,"failures":len(result.failures),
                      "errors":len(result.errors),"skips":len(result.skipped),"compiler_native_execution":False,
                      "native_harness_status":"INERT_86_CONTROLS_NOT_EXECUTED"},sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
