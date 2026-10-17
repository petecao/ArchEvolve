"""2026-10-16 ET. Tiny no-child controls; actual controller never invoked."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
EVENTS = []


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        EVENTS.append(event)
        raise RuntimeError("pure capture control refuses " + event)


sys.addaudithook(no_child)
path = HERE / "linux_compiler_capture_v5.py"
SOURCE = path.read_bytes()
API = {"__name__": "inert_capture_controls", "__file__": str(path)}
exec(compile(SOURCE, str(path), "exec"), API)


class Controls(unittest.TestCase):
    def test_pin_requires_physical_regular_stable_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            data = root / "data"
            data.write_bytes(b"exact")
            row = API["pin"](data)
            self.assertEqual(row["sha256"], hashlib.sha256(b"exact").hexdigest())
            API["recheck"]([row])
            link = root / "link"
            link.symlink_to(data)
            with self.assertRaises(ValueError): API["pin"](link)
            data.write_bytes(b"other")
            with self.assertRaises(ValueError): API["recheck"]([row])

    def test_closed_derived_stub_bytes_links_and_membership(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "include/gem5").mkdir(parents=True)
            (root / "m5ops.h").write_bytes(b"void declared_only();\n")
            target = root / "include/gem5/m5ops.h"
            target.write_bytes((root / "m5ops.h").read_bytes())
            API["check_derived_stub"](root)
            target.write_bytes(b"changed")
            with self.assertRaises(ValueError): API["check_derived_stub"](root)
            target.unlink()
            target.symlink_to(root / "m5ops.h")
            with self.assertRaises(ValueError): API["check_derived_stub"](root)
            target.unlink()
            target.write_bytes((root / "m5ops.h").read_bytes())
            (root / "include/extra").write_bytes(b"")
            with self.assertRaises(ValueError): API["check_derived_stub"](root)

    def test_exact_preprocess_ast_dependency_membership(self):
        before = [{"path": "/inert/source.cpp"}, {"path": "/inert/header.hpp"}]
        after = [row["path"] for row in before]
        API["compare_dependencies"](before, after, {"/inert/source.cpp"})
        for changed in (after[:-1], after + ["/inert/new.hpp"], list(reversed(after)), ["/inert/rebound.cpp", after[1]]):
            with self.assertRaises(ValueError): API["compare_dependencies"](before, changed, set())
        with self.assertRaises(ValueError): API["compare_dependencies"](before, after, {"/inert/missing.hpp"})
        with self.assertRaises(ValueError): API["compare_dependencies"]([before[0], before[0]], [after[0], after[0]], set())

    def test_actual_call_names_and_both_overloads_required(self):
        declarations = [{"name": "get_new_reg"}, {"name": "other"}]
        prepared = {"calls": [{"name": "get_new_reg", "formal_arity": 0},
                              {"name": "get_new_reg", "formal_arity": 1}, {"name": "other", "formal_arity": 0}]}
        API["check_prepared"](prepared, declarations)
        for rows in (prepared["calls"][:-1], prepared["calls"][1:], prepared["calls"] + [{"name": "extra", "formal_arity": 0}]):
            with self.assertRaises(ValueError): API["check_prepared"]({"calls": rows}, declarations)

    def test_exact_runtime_helpers_and_no_entry_main_execution(self):
        helper = WHOLE / "linux_native86_entry_v4.py"
        functions = API["original_helpers"](helper)
        self.assertEqual({name for name in functions if name in {"make_dependencies", "verified_linux_lane", "physical_runtime"}},
                         {"make_dependencies", "verified_linux_lane", "physical_runtime"})
        self.assertNotIn("main", functions)
        source = ast.parse(helper.read_bytes())
        for name in ("make_dependencies", "verified_linux_lane", "physical_runtime"):
            node = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == name)
            self.assertFalse(any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(node)))

    def test_policy_actual_root_shape_and_frozen_recipe_before_any_child(self):
        policy_path = HERE / "linux_compiler_capture_policy_v5.json"
        policy = json.loads(policy_path.read_bytes())
        command = json.loads((HERE / "linux_compiler_capture_command_v5.json").read_bytes())
        self.assertEqual(policy["raw_name"], API["RAW_NAME"])
        self.assertEqual(policy["source_commit"], API["SOURCE_COMMIT"])
        self.assertEqual(command["argv"][-1], hashlib.sha256(policy_path.read_bytes()).hexdigest())
        self.assertEqual(command["root_guard"]["rss_cap_bytes"], API["RSS_BYTES"])
        self.assertEqual(command["run_environment_unset"], ["LIBRARY_PATH"])
        self.assertEqual(command["root_required_environment"]["SWDB_VERIFIER_RSS_CAP_BYTES"], "4294967296")
        self.assertFalse(command["actual_launched"])
        self.assertFalse(command["public_proof"])
        self.assertFalse(command["source_call_admission"])
        recipe = policy["capture_recipe"]
        self.assertEqual(len(recipe["commands"]), 4)
        for row in recipe["commands"]:
            self.assertEqual(row["argv"][0], policy["compiler"]["wrapper"]["path"])
            self.assertNotIn("--version", row["argv"])
            if row["phase"].endswith("-ast"):
                self.assertTrue(row["argv"][-1].endswith(".cpp"))
                self.assertIn("-fsyntax-only", row["argv"])
        for row in command["controller_inputs"]:
            raw = Path(row["path"]).read_bytes()
            self.assertEqual({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
                             {k: row[k] for k in ("bytes", "sha256")})
        self.assertLess(sum(row["bytes"] for row in command["controller_inputs"]), 1048576)
        self.assertEqual(EVENTS, [])


    def test_v5_exact_inverse_restores_frozen_v4(self):
        delta = json.loads((HERE / "compiler-capture-v5-inverse.json").read_bytes())
        inverse = SOURCE.decode()
        for edit in reversed(delta["edits"]):
            self.assertGreaterEqual(inverse.count(edit["new"]), 1)
            inverse = inverse.replace(edit["new"], edit["old"])
        original = Path(delta["predecessor"]["path"]).read_text()
        self.assertEqual(inverse, original)
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), delta["predecessor"]["sha256"])
        self.assertEqual(hashlib.sha256(SOURCE).hexdigest(), delta["successor"]["sha256"])

    def test_v4_projected_final_extent_prevents_false_success(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory).resolve();out = raw / "component";out.mkdir()
            value, result, manifest = API["finalization_payloads"](raw, out, {"accepted":True},
                used_bytes=API["TOTAL_BYTES"]-100, elapsed=1)
            self.assertFalse(value["accepted"])
            self.assertIn("budget", value["finalization_refusal"])
            self.assertFalse((out / "result.json").exists())
            value, result, manifest = API["finalization_payloads"](raw, out, {"accepted":True}, used_bytes=0, elapsed=1)
            self.assertTrue(value["accepted"])
            entry = json.loads(manifest)[0]
            self.assertEqual(entry["sha256"], hashlib.sha256(result).hexdigest())
            self.assertEqual(entry["bytes"], len(result))

    def test_v4_entry_deadline_and_postpublication_invalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory).resolve();out = raw / "component";out.mkdir()
            value, _result, _manifest = API["finalization_payloads"](raw, out, {"accepted":True}, used_bytes=0, elapsed=165.01)
            self.assertFalse(value["accepted"])
            clock = API["time"]
            API["time"] = type("InertClock", (), {"monotonic":staticmethod(iter([1.0,166.0]).__next__)})
            try:
                self.assertFalse(API["finalize_capture"](raw, out, {"accepted":True}, started=0))
            finally:
                API["time"] = clock
            result = (out / "result.json").read_bytes()
            self.assertFalse(json.loads(result)["accepted"])
            manifest = json.loads((out / "artifact-manifest.json").read_bytes())
            self.assertEqual(next(row for row in manifest if row["relative"] == "result.json")["sha256"],hashlib.sha256(result).hexdigest())

    def test_v4_success_manifest_complete_and_depfile_final_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory).resolve();out = raw / "component";out.mkdir()
            (out / "captured.json").write_bytes(b"{}")
            clock = API["time"]
            API["time"] = type("InertClock", (), {"monotonic":staticmethod(lambda:1.0)})
            try:
                self.assertTrue(API["finalize_capture"](raw,out,{"accepted":True},started=0))
            finally:
                API["time"] = clock
            rows=json.loads((out / "artifact-manifest.json").read_bytes())
            self.assertEqual({row["relative"] for row in rows},{"captured.json","result.json"})
            for row in rows:
                data=Path(row["path"]).read_bytes()
                self.assertEqual(row["sha256"],hashlib.sha256(data).hexdigest())
            self.assertIn('group["preprocess_dependency"]',SOURCE.decode())
            self.assertEqual(API["FINAL_METADATA_RESERVE"],1048576)


    def test_v5_exact_ast_inverse_preserves_all_runtime_functions(self):
        delta=json.loads((HERE/"compiler-capture-v5-inverse.json").read_bytes())
        inverse=SOURCE.decode()
        for edit in reversed(delta["edits"]):
            self.assertEqual(inverse.count(edit["new"]),1)
            inverse=inverse.replace(edit["new"],edit["old"],1)
        before=Path(delta["predecessor"]["path"]).read_bytes()
        self.assertEqual(ast.dump(ast.parse(inverse),include_attributes=False),ast.dump(ast.parse(before),include_attributes=False))
        old_functions={node.name:ast.dump(node,include_attributes=False) for node in ast.parse(before).body if isinstance(node,ast.FunctionDef)}
        new_functions={node.name:ast.dump(node,include_attributes=False) for node in ast.parse(SOURCE).body if isinstance(node,ast.FunctionDef)}
        self.assertEqual(set(old_functions),set(new_functions))
        for name in old_functions:
            if name!="main":self.assertEqual(old_functions[name],new_functions[name])
        main=next(node for node in ast.parse(SOURCE).body if isinstance(node,ast.FunctionDef) and node.name=="main")
        main=copy.deepcopy(main)
        for node in ast.walk(main):
            if isinstance(node,ast.Constant) and node.value=="whole_interface_v4.py":node.value="whole_interface_v3.py"
        self.assertEqual(ast.dump(main,include_attributes=False),old_functions["main"])
        self.assertEqual(API["FINAL_METADATA_RESERVE"],1048576)
        self.assertEqual((API["WHOLE_SECONDS"],API["ENTRY_SECONDS"],API["RSS_BYTES"],API["STAGE_BYTES"],API["TOTAL_BYTES"]),
                         (180,165,4294967296,134217728,268435456))

    def test_v5_all_staged_inputs_policy_command_and_runtime_inverse_agree(self):
        delta=json.loads((HERE/"compiler-capture-v5-inverse.json").read_bytes())
        for key in ("policy","command"):
            record=delta[key]
            successor=json.loads(Path(record["successor"]["path"]).read_bytes())
            predecessor=json.loads(Path(record["predecessor"]["path"]).read_bytes())
            inverse=copy.deepcopy(successor)
            for edit in reversed(record["json_edits"]):
                cursor=inverse
                for part in edit["path"][:-1]:cursor=cursor[part]
                self.assertEqual(cursor[edit["path"][-1]],edit["new"])
                cursor[edit["path"][-1]]=edit["old"]
            self.assertEqual(inverse,predecessor)
        policy=json.loads((HERE/"linux_compiler_capture_policy_v5.json").read_bytes())
        old_policy=json.loads((WHOLE/"compiler-capture-v4/linux_compiler_capture_policy_v4.json").read_bytes())
        for key in policy:
            if key not in {"schema","raw_name","entry_sha256","controller_files","capture_recipe"}:
                self.assertEqual(policy[key],old_policy[key])
        staged=policy["controller_files"]
        self.assertIn("whole_interface_v4.py",staged);self.assertNotIn("whole_interface_v3.py",staged)
        self.assertEqual(staged["whole_interface_v4.py"]["sha256"],API["BINDER_SHA"])
        self.assertEqual(staged["compiler_unit_adapter_v2.py"]["sha256"],API["ADAPTER_SHA"])
        command=json.loads((HERE/"linux_compiler_capture_command_v5.json").read_bytes())
        selected={Path(row["path"]).name:{k:row[k] for k in ("bytes","sha256")} for row in command["controller_inputs"]}
        self.assertEqual(selected,{**staged,"linux_compiler_capture_policy_v5.json":{k:API["pin"](HERE/"linux_compiler_capture_policy_v5.json")[k] for k in ("bytes","sha256")}})
        expected={"source_dispatch_v3.py":"d05d3ba716af2d88703636ffbf57bf0834acd5e59ee7ce3aebe0a72648a8b703",
                  "source_argument_staging_v2.py":"79bdae72fd7b4de05771776684b5c6af275afb736313ece1df8790ae57ae6178"}
        for name,sha in expected.items():
            self.assertEqual(API["pin"](WHOLE/name)["sha256"],sha)
            self.assertNotIn(name,staged)
        self.assertFalse(command["native_or_solver_run"]);self.assertFalse(command["source_call_admission"])
        self.assertFalse(command["public_proof"]);self.assertEqual(EVENTS,[])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"skips":len(result.skipped),
        "child_events":EVENTS,"controller_sha256":hashlib.sha256(SOURCE).hexdigest(),
        "controls_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "policy_sha256":hashlib.sha256((HERE/"linux_compiler_capture_policy_v5.json").read_bytes()).hexdigest(),
        "command_sha256":hashlib.sha256((HERE/"linux_compiler_capture_command_v5.json").read_bytes()).hexdigest()},sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun == 12 and not result.skipped and not EVENTS else 1)
