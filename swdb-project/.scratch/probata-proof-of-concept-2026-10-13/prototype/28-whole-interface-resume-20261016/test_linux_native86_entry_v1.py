"""2026-10-16 ET. Pure no-child native-controller parser/recipe controls."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("native86 source controls: " + event)


sys.addaudithook(no_child)
HERE = Path(__file__).resolve().parent
PATH = HERE / "linux_native86_entry_v1.py"
TREE = ast.parse(PATH.read_bytes())
FUNCTIONS = {n.name: n for n in TREE.body if isinstance(n, ast.FunctionDef)}
CONSTANTS = {n.targets[0].id: ast.literal_eval(n.value) for n in TREE.body if isinstance(n, ast.Assign)
             and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}


def project(name, **values):
    context = {"Path": Path, **values}
    exec(compile(ast.Module(body=[FUNCTIONS[name]], type_ignores=[]), "<inert-native86-" + name + ">", "exec"), context)
    return context[name]


class NativeSourceControls(unittest.TestCase):
    def test_make_dependencies_exact_files_and_mutation_refusals(self):
        with tempfile.TemporaryDirectory(prefix="native86-parser-", dir=HERE) as directory:
            root = Path(directory)
            for name in ("original.c", "header with spaces.h", "colon:header.h"): (root / name).write_text("inert\n")
            parse = project("make_dependencies")
            text = "c11: original.c header\\ with\\ spaces.h \\\n colon\\:header.h original.c\n"
            self.assertEqual(parse(text, "c11", root), sorted(str(root / name) for name in ("original.c", "header with spaces.h", "colon:header.h")))
            for broken in ("other: original.c", "c11:", "c11: $VAR", "c11: #comment", "c11: original.c\\", "c11: bad\\q"):
                with self.assertRaises(ValueError): parse(broken, "c11", root)

    def test_linker_trace_preserves_all_regular_archive_and_alias_inputs(self):
        with tempfile.TemporaryDirectory(prefix="native86-link-", dir=HERE) as directory:
            root = Path(directory)
            for name in ("case.o", "libasan.a", "libc.so.6"): (root / name).write_bytes(b"inert not ELF\n")
            (root / "libc.so").symlink_to("libc.so.6")
            parse = project("link_inputs")
            text = "case.o\n" + str(root / "libasan.a") + "(asan_rtl.cpp.o)\n" + str(root / "libc.so") + "\n"
            self.assertEqual(parse(text, root), sorted(str(root / name) for name in ("case.o", "libasan.a", "libc.so.6")))
            for broken in ("", "libasan.a()", "two words", "libasan.a", "missing.a"):
                if broken == "libasan.a": continue  # archive path without member is valid GNU output
                with self.assertRaises((ValueError, FileNotFoundError)): parse(broken, root)

    def test_exact_eight_phase_recipe_and_86_census_are_private(self):
        self.assertEqual(CONSTANTS["RESULT"], {"controls": 86, "family_dtype_cases": 66, "history_cases": 6,
            "subtract_fold_cases": 6, "action_order_cases": 2, "refusals": 6})
        self.assertEqual(sum(CONSTANTS["RESULT"][name] for name in CONSTANTS["RESULT"] if name != "controls"), 86)
        source = PATH.read_text()
        self.assertNotIn("from swdb", source)
        self.assertNotIn("--version", source)
        self.assertIn('"-fuse-ld=" + compiler["linker"]["path"]', source)
        self.assertIn('"-Wl,-t"', source)
        self.assertIn('len(commands) == 8', source)
        self.assertIn('"public_proof": False', source)
        self.assertNotIn("SWDB_VERIFIER_RUN_TOKEN", source)
        # Read the direct label suffixes without assuming C execution happened.
        self.assertEqual(source.count('stage(label + "-'), 4)
        self.assertIn('WHOLE_SECONDS, ENTRY_SECONDS, RSS_BYTES = 180, 165, 4294967296', source)

    def test_runtime_closure_refuses_missing_admission_before_compile(self):
        function = FUNCTIONS["physical_runtime"]
        text = ast.unparse(function)
        self.assertIn("native.get('admitted') is not True", text)
        self.assertIn("not native.get('pins')", text)
        self.assertIn("not native.get('trees')", text)
        self.assertIn("native['absence']", text)
        self.assertIn("native['aliases']", text)
        self.assertIn("header['inventory_sha256']", text)
        with tempfile.TemporaryDirectory(prefix="native86-runtime-", dir=HERE) as directory:
            root = Path(directory)
            closed = types.SimpleNamespace(verify_python_metadata=lambda value: {"fixture": True}, _resolution=lambda path, links: path)
            empty = hashlib.sha256(b"[]").hexdigest()
            policy = {"python_surface_binding": {}, "runtime_files": {},
                      "linux_header_surfaces": {label: {"path": str(root), "count": 0, "inventory_sha256": empty}
                                                for label in ("libc++", "clang-resource")},
                      "native_runtime": {"admitted": False, "pins": [], "trees": []}}
            actual = project("physical_runtime", hashlib=hashlib, json=json, stat=__import__("stat"), os=__import__("os"))
            for native in ({"admitted": False, "pins": [1], "trees": [1]},
                           {"admitted": True, "pins": [], "trees": [1]},
                           {"admitted": True, "pins": [1], "trees": []}):
                policy["native_runtime"] = native
                with self.assertRaisesRegex(ValueError, "prospectively admitted"):
                    actual(policy, closed)

    def test_native_4gib_entry_role_preserves_shared_projection_without_8gib_child_builder(self):
        helper = HERE.parent / "28-public-memory-trace-resume-20261016/python_startup_roles_v2.py"
        tree = ast.parse(helper.read_bytes())
        names = {"startup_projection_v2", "role_request_v2"}
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        assignments = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                       if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {"ENV_KEYS", "PYTHON_ENV_KEYS", "PACKAGES"}}
        namespace = {"ENV_KEYS": assignments["ENV_KEYS"], "PYTHON_ENV_KEYS": set(assignments["PYTHON_ENV_KEYS"]),
                     "PACKAGES": assignments["PACKAGES"]}
        exec(compile(ast.Module(body=selected, type_ignores=[]), "<entry-only-role-projection>", "exec"), namespace)
        plan = {"source_project": "/inert/project", "package_sys_path": ["/inert/python"],
                "executable": "/inert/python/bin/python", "prefix": "/inert/python", "base_prefix": "/inert/base",
                "module_origins": {}}
        environment = {"SWDB_VERIFIER_RSS_CAP_BYTES": "4294967296", "PYTHONDONTWRITEBYTECODE": "1"}
        request = namespace["role_request_v2"](plan, role="entry-isolated", environment=environment, cache="/inert/cache")
        self.assertEqual(request["startup_environment"]["SWDB_VERIFIER_RSS_CAP_BYTES"], "4294967296")
        self.assertEqual(request["initial_sys_path"], ["/inert/python"])
        self.assertNotIn("child_environment_v2(", PATH.read_text())
        self.assertIn('"rss_bytes": RSS_BYTES', PATH.read_text())


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeSourceControls))
    print(json.dumps({"date": "2026-10-16", "cases": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skips": len(result.skipped), "compiler_native_project_import_child_execution": False}, sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
