"""2026-10-16 ET. No-child admission/result controls; never invoke the profile."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
attempts = []


def deny_children(event, args):
    if event in {"subprocess.Popen", "os.system", "os.fork", "os.posix_spawn", "socket.connect", "ctypes.dlopen"}:
        attempts.append(event)
        raise AssertionError("pure control attempted a child/network/native operation: " + event)


sys.addaudithook(deny_children)
source = (HERE / "entry.py").read_bytes()
tree = ast.parse(source)
tree.body = [node for node in tree.body if not isinstance(node, ast.If)]
entry = {"__file__": str(HERE / "entry.py"), "__name__": "mixed_pure_controls"}
exec(compile(tree, str(HERE / "entry.py"), "exec"), entry)


def fixture():
    hashes = {name: hashlib.sha256(name.encode()).hexdigest() for name in entry["MEMBERS"]}
    rows = []
    for index, name in enumerate(entry["MEMBERS"]):
        rows.append({"id": "proof.model." + str(index), "evidence_kind": "contract_fixture",
            "subject": {"kind": "c_model", "id": name}, "job": {"adapter": "wp"}, "verdict": "proven",
            "settings": {"rss_cap_bytes": 8589934592},
            "pins": {"code": {"sha256": hashes[name]}, "method_version": {"id": "method.pair-workflow-fixture"}},
            "goals": [{"status": "valid", "smoke": False}, {"status": "valid", "smoke": True}]})
    for index, (adapter, contract, verdict) in enumerate([
            ("wp", "contract.fixture_pair_pointer_values", "proven"),
            ("wp", "contract.fixture_pair_pointer_wrong_identity", "not_proven"),
            ("cbmc", "contract.fixture_pair_pointer_values", "proven"),
            ("cbmc", "contract.fixture_pair_pointer_wrong_identity", "refuted")]):
        rows.append({"id": "proof.caller." + str(index), "evidence_kind": "contract_fixture",
            "subject": {"kind": "library_summary", "id": contract}, "job": {"adapter": adapter},
            "verdict": verdict, "settings": {"rss_cap_bytes": 8589934592},
            "pins": {"method_version": {"id": "method.pair-workflow-fixture"}},
            "goals": [{"status": "valid", "smoke": False}, {"status": "valid", "smoke": True}]})
    rows[4]["pins"]["models"] = [{"id": name, "proof_record": rows[i]["id"], "sha256": hashes[name]}
                                           for i, name in enumerate(entry["MEMBERS"])]
    rows[5].update(failure_class="unknown", goals=[{"status": "unknown", "smoke": False}, {"status": "valid", "smoke": True}])
    rows[6]["settings"]["agreement"] = {"verdict": "agree"}
    rows[7]["counterexample"] = {"replay": {"replayed": True}}
    rows[7]["settings"]["forms"] = {"cxx": "refuted (counterexample replayed)"}
    return rows, hashes


class Controls(unittest.TestCase):
    def accepts(self, rows, hashes):
        return entry["check_eight_records"](rows, hashes)

    def refuses(self, mutate):
        rows, hashes = fixture()
        mutate(rows, hashes)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            self.accepts(rows, hashes)

    def test_original_eight_obligations_have_distinct_roles(self):
        rows, hashes = fixture()
        self.assertEqual(self.accepts(rows, hashes)["records"], 8)
        self.refuses(lambda rows, hashes: rows.pop())
        self.refuses(lambda rows, hashes: rows[7].update(id=rows[6]["id"]))
        self.refuses(lambda rows, hashes: rows[4]["subject"].update(id="another-contract"))
        self.refuses(lambda rows, hashes: rows[6]["job"].update(adapter="wp"))
        self.refuses(lambda rows, hashes: rows[3].update(skip_reason="skipped"))

    def test_current_model_text_and_exact_proof_dependencies(self):
        self.refuses(lambda rows, hashes: rows[0]["pins"]["code"].update(sha256="0" * 64))
        self.refuses(lambda rows, hashes: rows[4]["pins"]["models"][0].update(proof_record="older-proof"))
        self.refuses(lambda rows, hashes: rows[4]["pins"]["models"].append(copy.deepcopy(rows[4]["pins"]["models"][0])))
        self.refuses(lambda rows, hashes: rows[0]["pins"]["method_version"].update(id="other-method"))
        self.refuses(lambda rows, hashes: rows[1]["settings"].update(rss_cap_bytes=4294967296))

    def test_complete_positive_wp_observation(self):
        self.refuses(lambda rows, hashes: rows[0].update(goals=[]))
        self.refuses(lambda rows, hashes: rows[1]["goals"][0].update(status="unknown"))
        self.refuses(lambda rows, hashes: rows[4]["goals"].pop())
        self.refuses(lambda rows, hashes: rows[0].update(unproven_properties=["missing"]))

    def test_wrong_identity_retains_ordinary_failure_and_healthy_smokes(self):
        self.refuses(lambda rows, hashes: rows[5].update(verdict="proven"))
        self.refuses(lambda rows, hashes: rows[5].update(failure_class="parse_error"))
        self.refuses(lambda rows, hashes: rows[5]["goals"][0].update(status="valid"))
        self.refuses(lambda rows, hashes: rows[5]["goals"][1].update(status="unknown"))
        self.refuses(lambda rows, hashes: rows[5].update(goals=[{"smoke": False, "status": "unknown"}]))

    def test_cbmc_safe_agreement_and_actual_cpp_counterexample_replay(self):
        self.refuses(lambda rows, hashes: rows[6]["settings"]["agreement"].update(verdict="disagree"))
        self.refuses(lambda rows, hashes: rows[7].update(verdict="not_proven"))
        self.refuses(lambda rows, hashes: rows[7]["counterexample"]["replay"].update(replayed=False))
        self.refuses(lambda rows, hashes: rows[7]["settings"]["forms"].update(cxx="refuted"))

    def test_exact_junit_case_and_zero_skips(self):
        text = ('<testsuites><testsuite tests="1" errors="0" failures="0" skipped="0">'
                '<testcase classname="tests.test_pair_pointer_workflow" '
                'name="test_actual_mixed_pair_bodies_callers_and_bounded_cpp_replay"/></testsuite></testsuites>')
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            path = Path(folder) / "junit.xml"
            path.write_text(text)
            self.assertEqual(entry["junit_census"](path)["tests"], 1)
            for bad in (text.replace('skipped="0"', 'skipped="1"'), text.replace('/></testsuite>', '><skipped/></testcase></testsuite>'),
                        text.replace('tests="1"', 'tests="0"'), text.replace("tests.test_pair_pointer_workflow", "other"),
                        text.replace("</testsuite>", '<testcase name="extra"/></testsuite>')):
                path.write_text(bad)
                with self.assertRaises(ValueError):
                    entry["junit_census"](path)

    def test_raw_membership_and_quota_refuse_without_large_writes(self):
        before = entry["TOTAL_BYTES"], entry["STAGE_BYTES"], entry["FINAL_RESERVE_BYTES"]
        entry["TOTAL_BYTES"], entry["STAGE_BYTES"] = 7, 4
        entry["FINAL_RESERVE_BYTES"] = 0
        try:
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                root = Path(folder)
                (root / "a").write_bytes(b"1234")
                self.assertEqual(entry["raw_extent"](root)["bytes"], 4)
                (root / "b").write_bytes(b"1234")
                with self.assertRaisesRegex(ValueError, "total budget"):
                    entry["raw_extent"](root)
                (root / "b").unlink()
                (root / "a").write_bytes(b"12345")
                with self.assertRaisesRegex(ValueError, "per-file budget"):
                    entry["raw_extent"](root)
                (root / "a").write_bytes(b"1")
                (root / "alias").symlink_to("a")
                with self.assertRaisesRegex(ValueError, "unlisted raw output symlink"):
                    entry["raw_extent"](root)
        finally:
            entry["TOTAL_BYTES"], entry["STAGE_BYTES"], entry["FINAL_RESERVE_BYTES"] = before

    def aliases(self, root):
        base = root / entry["PYTEST_BASE"]
        base.mkdir(parents=True)
        target = base / (entry["CASE_PREFIX"] + "0")
        target.mkdir()
        alias = base / (entry["CASE_PREFIX"] + "current")
        alias.symlink_to(target)
        return base, target, alias

    def test_only_exact_physical_current_alias_is_admitted(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder)
            base, target, alias = self.aliases(root)
            extent = entry["raw_extent"](root, require_aliases=True)
            self.assertEqual(extent["aliases"], [{"relative": str(alias.relative_to(root)),
                "literal_target": str(target), "target_relative": str(target.relative_to(root))}])
            alias.unlink()
            with self.assertRaisesRegex(ValueError, "complete exact"):
                entry["raw_extent"](root, require_aliases=True)
            for value in (target.name, str(base / (entry["CASE_PREFIX"] + "1")), str(root.parent)):
                alias.symlink_to(value)
                with self.assertRaisesRegex(ValueError, "link literal differs"):
                    entry["raw_extent"](root)
                alias.unlink()
            alias.symlink_to(target)
            (base / "unexpected-case").mkdir()
            with self.assertRaisesRegex(ValueError, "sole expected pytest"):
                entry["raw_extent"](root, require_aliases=True)

    def test_current_alias_cannot_follow_nested_or_escaping_target(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder)
            _base, target, _alias = self.aliases(root)
            target.rmdir()
            outside = root / "outside"
            outside.mkdir()
            target.symlink_to(outside)
            with self.assertRaises(ValueError):
                entry["raw_extent"](root)
            target.unlink(); target.mkdir()
            (root / "unlisted-current").symlink_to(target)
            with self.assertRaisesRegex(ValueError, "unlisted raw output symlink"):
                entry["raw_extent"](root)

    def test_projected_final_metadata_fits_at_reserved_near_limit(self):
        old = {key: entry[key] for key in ("TOTAL_BYTES", "STAGE_BYTES", "FINAL_RESERVE_BYTES", "FINAL_RESULT_BYTES")}
        entry.update(TOTAL_BYTES=8192, STAGE_BYTES=8192, FINAL_RESERVE_BYTES=4096, FINAL_RESULT_BYTES=2048)
        try:
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                root = Path(folder); self.aliases(root)
                before = entry["raw_extent"](root, require_aliases=True)["bytes"]
                (root / "payload").write_bytes(b"x" * (4096 - before))
                result, code = entry["finalize_result"](root,
                    {"status": "PRODUCER_WORKFLOW_COMPLETE", "independent_cold_acceptance": False}, 0, clock=lambda: 1)
                self.assertEqual(code, 0)
                final = entry["raw_extent"](root, require_aliases=True, reserve=0)
                self.assertEqual(final["bytes"], result["finalization"]["projected_total_bytes"])
                self.assertLessEqual(final["bytes"], 8192)
                self.assertLessEqual((root / "mixed-result.json").stat().st_size, 2048)
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                root = Path(folder); self.aliases(root)
                before = entry["raw_extent"](root, require_aliases=True)["bytes"]
                (root / "payload").write_bytes(b"x" * (4097 - before))
                with self.assertRaisesRegex(ValueError, "final metadata reserve"):
                    entry["finalize_result"](root, {"status": "PRODUCER_WORKFLOW_COMPLETE"}, 0, clock=lambda: 1)
                self.assertFalse((root / "mixed-result.json").exists())
        finally:
            entry.update(old)

    def test_final_size_and_pre_post_time_gates_refuse_success(self):
        with self.assertRaisesRegex(ValueError, "projected final metadata"):
            entry["final_payload"]({"reason": "x" * entry["FINAL_RESULT_BYTES"]},
                                   {"bytes": 0, "aliases": [], "regular_files": 0}, 1)
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder); self.aliases(root)
            result, code = entry["finalize_result"](root, {"status": "PRODUCER_WORKFLOW_COMPLETE"},
                                                  0, clock=lambda: 1199.5)
            self.assertEqual(code, 1)
            self.assertEqual(result["status"], "REFUSED_OR_FAILED")
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder); self.aliases(root)
            ticks = iter([1, 1201])
            with self.assertRaisesRegex(ValueError, "deadline exceeded after final fsync"):
                entry["finalize_result"](root, {"status": "PRODUCER_WORKFLOW_COMPLETE"}, 0, clock=lambda: next(ticks))

    def test_staged_exact_CBMC_gate_api_matches_controller_call(self):
        policy = json.loads((HERE / "policy.json").read_bytes())
        command = json.loads((HERE / "command.json").read_bytes())
        gate_path = Path(next(row["path"] for row in command["controller_inputs"] if row["name"] == "cbmc_release_gate.py"))
        gate = {"__name__": "cbmc_pure_control"}
        exec(compile(gate_path.read_bytes(), str(gate_path), "exec"), gate)
        raw = policy["cbmc_version_output"]
        result = gate["check_cbmc_version"](policy, 0, raw["stdout"], raw["stderr"])
        self.assertEqual(result["exact_observed_version"], "6.11.0")
        for code, text in ((1, raw["stdout"]), (0, "6.11 (cbmc)\n"), (0, "6.11.01-extra\n")):
            with self.assertRaises(ValueError):
                gate["check_cbmc_version"](policy, code, text, "")

    def test_final_root_authorization_is_exact_and_mandatory(self):
        policy = json.loads((HERE / "policy.json").read_bytes())
        self.assertIs(policy["source_admission"]["root_authorized"], True)
        entry["policy_gate"](policy)
        denied = copy.deepcopy(policy)
        denied["source_admission"]["root_authorized"] = False
        with self.assertRaisesRegex(ValueError, "root30-control success"):
            entry["policy_gate"](denied)
        for key, value in (("source_commit", "0" * 40), ("raw_name", "wrong"), ("profile_seconds", 901), ("selection", "tests")):
            bad = copy.deepcopy(policy); bad[key] = value
            with self.assertRaises(ValueError): entry["policy_gate"](bad)
        for key, value in (("workers", 2), ("rss_cap_bytes", 4294967296), ("whole_tree_seconds", 1201), ("raw_budget_bytes", 1 << 30)):
            bad = copy.deepcopy(policy); bad["guard"][key] = value
            with self.assertRaises(ValueError): entry["policy_gate"](bad)

    def test_exact_root30_receipt_gate_has_no_sibling_or_incomplete_fallback(self):
        policy = json.loads((HERE / "policy.json").read_bytes())
        actual_bytes = (HERE / "root30-control-admission.json").read_bytes()
        self.assertEqual((len(actual_bytes), hashlib.sha256(actual_bytes).hexdigest()),
                         (2798, "3ba333bebdd77c6117f4bfeb6981cafda249248a3323d6ab48b02f55ef12a9ae"))
        actual = json.loads(actual_bytes)
        entry["root_control_gate"](policy, actual)
        pending = json.loads((HERE.with_name("mixed-pair-actual-v3") / "root30-control-admission.json").read_bytes())
        with self.assertRaises(ValueError): entry["root_control_gate"](policy, pending)
        valid = {"schema": "mixed-pair-root30-admission-1", "status": "ROOT_CONTROLS_PASSED",
            "actual_success_admitted": True, "source_commit": entry["SOURCE"],
            "raw_root": policy["root_control_admission"]["expected_raw_root"],
            "tests": {"cases": 30, "failures": 0, "errors": 0, "skips": 0, "cache_absent": True},
            "guard": {"exit_code": 0, "rss_cap_bytes": 8589934592, "workers": 1, "whole_seconds": 1200},
            "outer_exit_code": 0, "formal_WP_CBMC_disabled": True,
            "actual_flags": {"SWDB_PAIR_ACTUAL": "0", "SWDB_MIXED_PAIR_ACTUAL": "0"},
            "evidence": {key: {"path": "/synthetic-not-admitted/" + key, "bytes": 1, "sha256": "a" * 64}
                for key in ("command", "junit", "result", "guard", "outer", "source_publication")}}
        entry["root_control_gate"](policy, valid)
        mutations = [lambda value: value.update(source_commit="0" * 40),
            lambda value: value.update(raw_root=value["raw_root"] + "-sibling"),
            lambda value: value.update(status="PENDING"), lambda value: value.update(actual_success_admitted=False),
            lambda value: value["tests"].update(cases=29), lambda value: value["tests"].update(skips=1),
            lambda value: value["tests"].update(errors=False), lambda value: value["tests"].update(cache_absent=False),
            lambda value: value["guard"].update(exit_code=1), lambda value: value["guard"].update(workers=2),
            lambda value: value["guard"].update(rss_cap_bytes=4294967296), lambda value: value.update(outer_exit_code=1),
            lambda value: value.update(formal_WP_CBMC_disabled=False),
            lambda value: value["actual_flags"].update(SWDB_MIXED_PAIR_ACTUAL="1"),
            lambda value: value["evidence"].pop("junit"),
            lambda value: value["evidence"]["guard"].update(sha256="")]
        for mutate in mutations:
            value = copy.deepcopy(valid); mutate(value)
            with self.assertRaises(ValueError): entry["root_control_gate"](policy, value)
        self.assertIs(actual["actual_success_admitted"], True)
        self.assertIs(pending["actual_success_admitted"], False)

    def test_current_checker_composite_metadata_is_bound(self):
        policy = json.loads((HERE / "policy.json").read_bytes())
        current = policy["source_checker_identities"]
        self.assertEqual(set(current), {"bounded_initialization", "cbmc_translator", "wp_pointer_bounds", "std_models", "proof_setup"})
        rows = policy["source_checker_material"]["proof_setup_ordered_inputs"]
        self.assertEqual(hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                         current["proof_setup"]["proof_setup_check"]["sha256"])
        for row in rows:
            self.assertEqual(row["sha256"], policy["source_files"][row["path"]])
        self.assertIn("tests/test_pair_pointer_initialization.py", policy["source_files"])
        self.assertIn("tests/test_pair_pointer_initialization.py", policy["source_consumer_trees"])
        parent = json.loads((HERE.with_name("mixed-pair-actual-v4") / "policy.json").read_bytes())
        for key in ("runtime_files", "native_runtime", "linux_clang_components", "linux_header_surfaces", "guard", "finalization",
                    "source_files", "source_consumer_trees", "source_checker_identities", "source_checker_material"):
            self.assertEqual(policy[key], parent[key])

    def test_unpinned_native_C_wrapper_refuses_passively(self):
        policy = json.loads((HERE / "policy.json").read_bytes())
        self.assertEqual(policy["mixed_native_c_wrapper"]["sha256"], "cb1253820eb3815c92a98f20e384f1dc8350eb90839588cd567f4b3963ba0d78")
        policy["mixed_native_c_wrapper"]["admitted"] = False
        with self.assertRaisesRegex(ValueError, "fresh exact physical pin"):
            entry["native_c_wrapper_check"](policy)
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            path = Path(folder) / "clang"
            path.write_bytes(b"inert bytes, never executable\n")
            policy["linux_clang_components"]["command"] = [str(path) + "++"]
            policy["mixed_native_c_wrapper"] = {"admitted": True, "path": str(path),
                "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "mode": path.stat().st_mode & 0o7777}
            entry["native_c_wrapper_check"](policy)
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "bytes/mode differ"):
                entry["native_c_wrapper_check"](policy)

    def test_final_control_bytes_and_command_are_bound(self):
        policy = json.loads((HERE / "policy.json").read_bytes())
        command = json.loads((HERE / "command.json").read_bytes())
        self.assertLessEqual(sum(row["bytes"] for row in command["controller_inputs"]), 1048576)
        self.assertEqual(len(command["controller_inputs"]), len({row["name"] for row in command["controller_inputs"]}))
        for row in command["controller_inputs"]:
            raw = Path(row["path"]).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (row["bytes"], row["sha256"]))
        raw = command["raw_root"]
        self.assertEqual(command["argv"], [policy["tools"]["opam"]["path"], "exec", "--switch=framac-33", "--",
            policy["linux_launch_binding"]["python"], "-I", "-B", raw + "/control/entry.py", command["source"],
            raw, raw + "/control/policy.json", hashlib.sha256((HERE / "policy.json").read_bytes()).hexdigest()])
        self.assertEqual(command["root_guard"], policy["guard"])
        self.assertEqual(command["node"], 0)
        self.assertEqual(entry["NODE"], 0)
        self.assertEqual(policy["linux_launch_binding"]["node"], 0)
        self.assertEqual(command["run_environment_unset"], ["LIBRARY_PATH"])
        self.assertEqual(policy["linux_launch_binding"]["entry_sha256"], hashlib.sha256(source).hexdigest())

    def test_reviewed_definitions_are_exact_copies(self):
        lineage = json.loads((HERE / "reviewed-function-lineage.json").read_bytes())
        for item in lineage["definitions"]:
            original = (REPO / item["source"]).read_bytes()
            self.assertEqual(hashlib.sha256(original).hexdigest(), item["source_sha256"])
            expected = b"".join(original.splitlines(keepends=True)[item["lines"][0] - 1:item["lines"][1]])
            copied = (HERE / item["output"]).read_bytes()
            function = next(node for node in ast.parse(copied).body if isinstance(node, ast.FunctionDef) and node.name == item["function"])
            actual = b"".join(copied.splitlines(keepends=True)[function.lineno - 1:function.end_lineno])
            self.assertEqual(expected, actual)
            self.assertEqual(hashlib.sha256(actual).hexdigest(), item["function_sha256"])

    def test_predecessors_are_preserved_and_delta_inverse_is_exact(self):
        report = json.loads((HERE / "entry-delta-v5.json").read_bytes())
        lines = source.decode().splitlines(keepends=True)
        for edit in reversed(report["line_edits"]):
            start, end = edit["new_range"]
            self.assertEqual(lines[start:end], edit["new_lines"])
            lines[start:end] = edit["old_lines"]
        restored = "".join(lines).encode()
        self.assertEqual(hashlib.sha256(restored).hexdigest(), report["parent"]["sha256"])
        self.assertEqual(restored, Path(report["parent"]["path"]).read_bytes())
        self.assertIn("check_eight_records", report["unchanged_functions"])
        self.assertIn("junit_census", report["unchanged_functions"])
        for version, digest in [(1, "ca3b2f44b75a684ed0d2b9dc7dc60eed0406b23ef05448f7621e8c757833c13d"),
                                (2, "997b44443d31ebd4c3cb971d67f8bca8cec8eca7736e44955b129be9b64f168f"),
                                (3, "fdca6ae8ab559244cf92d177cfc4023914fdf775bca5ada6eac0724e54ca1146"),
                                (4, "5417f524f1ac3d2f417257801955de8cfdea3f3870f367d4b5f8bcf719835886")]:
            original = HERE.with_name("mixed-pair-actual-v" + str(version)) / "source-packet.json"
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), digest)
            for row in json.loads(original.read_bytes())["files"]:
                self.assertEqual(hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest(), row["sha256"])

    def test_entry_and_gate_sources_compile_without_execution(self):
        for name in ("entry.py", "reviewed_wp_gates.py", "reviewed_native_gates.py", "prepare.py"):
            compile((HERE / name).read_bytes(), name, "exec")
        self.assertEqual(attempts, [])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"date": "2026-10-16 ET", "pure_controls": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "child_native_network_attempts": attempts, "actual_profile_executed": False}, sort_keys=True))
    raise SystemExit(not result.wasSuccessful())
