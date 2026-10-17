"""2026-10-16 ET. No-child admission/result controls; never invoke the profile."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import os
import socket
from unittest.mock import patch
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
        for key in ("native_runtime", "linux_clang_components", "linux_header_surfaces", "guard",
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
        report = json.loads((HERE / "entry-delta-v6.json").read_bytes())
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
                                (4, "5417f524f1ac3d2f417257801955de8cfdea3f3870f367d4b5f8bcf719835886"),
                                (5, "2825deff0f8bfd1fbee80c96ea13c43cbac6f942e63511f12813707d8766b841")]:
            original = HERE.with_name("mixed-pair-actual-v" + str(version)) / "source-packet.json"
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), digest)
            for row in json.loads(original.read_bytes())["files"]:
                self.assertEqual(hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest(), row["sha256"])

    def make_job(self, root, candidate=None, adapter="wp"):
        candidate = candidate or "model." + entry["MEMBERS"][0]
        if candidate.startswith("model."):
            function, contract = candidate[6:], "c_model." + candidate[6:]
        else:
            contract = candidate
            function = {"contract.fixture_pair_pointer_values": "swdb_pair_pointer_values",
                "contract.fixture_pair_pointer_wrong_identity": "swdb_pair_pointer_wrong_identity"}[candidate]
        job = root / entry["PYTEST_BASE"] / (entry["CASE_PREFIX"] + "0") / "runs" / (
            "proof." + candidate + ".20261016t205430z.bab6f02e")
        temporary = job / "scratch/tmp"
        temporary.mkdir(parents=True)
        unit = "None" if adapter == "wp" else "library summary " + contract
        (job / "adapter.log").write_text(f"adapter: {adapter}\nunit: {unit} {function}\ncontract: {contract}\n")
        return job, temporary

    def make_socket(self, temporary, basename="why3serverabcdefsock"):
        # Filesystem-only AF_UNIX fixture. No listen/connect/send/receive or child.
        # Relative bind avoids the macOS sockaddr_un pathname length limit.
        before = Path.cwd()
        try:
            os.chdir(temporary)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as fixture_socket:
                fixture_socket.bind(basename)
        finally:
            os.chdir(before)
        return temporary / basename

    def test_known_why3_socket_is_live_metadata_only_and_final_success_refuses(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder)
            job, temporary = self.make_job(root)
            sock = self.make_socket(temporary)
            observed = entry["raw_extent"](root, allow_runtime_ipc=True)
            self.assertEqual(len(observed["runtime_ipc"]), 1)
            self.assertEqual(observed["runtime_ipc"][0]["relative"], str(sock.relative_to(root)))
            self.assertEqual(observed["runtime_ipc"][0]["kind"], "S_IFSOCK")
            with self.assertRaisesRegex(ValueError, "special entry refused"):
                entry["raw_extent"](root)
            # Merely closing the fixture does not count as socket settlement.
            with self.assertRaises(ValueError):
                entry["finalize_result"](root, {"status": "PRODUCER_WORKFLOW_COMPLETE"}, 0, clock=lambda: 1)
            sock.unlink()
            entry["raw_extent"](root)

    def test_why3_socket_wrong_name_location_adapter_owner_and_type_refuse(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder)
            job, temporary = self.make_job(root)
            sock = self.make_socket(temporary, "why3serverabcdef.sock")
            with self.assertRaisesRegex(ValueError, "socket path refused"):
                entry["raw_extent"](root, allow_runtime_ipc=True)
            sock.unlink(); sock = self.make_socket(temporary)
            with patch.object(entry["os"], "geteuid", return_value=os.geteuid() + 1):
                with self.assertRaises(ValueError): entry["raw_extent"](root, allow_runtime_ipc=True)
            (job / "adapter.log").write_text("adapter: cbmc\n")
            with self.assertRaisesRegex(ValueError, "producer attribution"):
                entry["raw_extent"](root, allow_runtime_ipc=True)
            sock.unlink()
            fifo = temporary / "why3serverabcdefsock"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(ValueError, "special entry refused"):
                entry["raw_extent"](root, allow_runtime_ipc=True)
            fifo.unlink()
            self.make_socket(root)
            with self.assertRaisesRegex(ValueError, "socket path refused"):
                entry["raw_extent"](root, allow_runtime_ipc=True)

    def test_socket_symlink_ancestor_and_multiple_live_servers_refuse(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder)
            _job, temporary = self.make_job(root)
            self.make_socket(temporary)
            self.make_socket(temporary, "why3server123456sock")
            with self.assertRaisesRegex(ValueError, "count exceeds"):
                entry["raw_extent"](root, allow_runtime_ipc=True)
            (temporary / "why3server123456sock").unlink()
            moved = temporary.with_name("moved")
            temporary.rename(moved); temporary.symlink_to(moved)
            with self.assertRaises(ValueError): entry["raw_extent"](root, allow_runtime_ipc=True)

    def test_exact_all_eight_job_roles_and_no_other_scratch_lifecycle(self):
        candidates = ["model." + name for name in entry["MEMBERS"]]
        candidates += ["contract.fixture_pair_pointer_values", "contract.fixture_pair_pointer_wrong_identity"]
        for adapter, selected in (("wp", candidates), ("cbmc", candidates[-2:])):
            for candidate in selected:
                with tempfile.TemporaryDirectory(dir=HERE) as folder:
                    root = Path(folder)
                    _job, temporary = self.make_job(root, candidate, adapter)
                    self.assertTrue(entry["missing_owned_live_entry"](root, temporary / "gone"))
                    self.assertFalse(entry["missing_owned_live_entry"](root, temporary.parent.parent / "not-scratch"))
                    if adapter == "cbmc":
                        self.make_socket(temporary)
                        with self.assertRaisesRegex(ValueError, "producer attribution"):
                            entry["raw_extent"](root, allow_runtime_ipc=True)
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder); _job, temporary = self.make_job(root)
            (temporary.parent.parent / "adapter.log").write_text("adapter: wp\nunit: None wrong\ncontract: wrong\n")
            with self.assertRaises(ValueError): entry["missing_owned_live_entry"](root, temporary / "gone")

    def test_exact_lock_owner_ticket_and_unknown_missing_path_rules(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder)
            profile = root / "mixed-pair-profile"; profile.mkdir()
            queue = profile / "verifier.queue"; queue.mkdir()
            for relative in ("verifier.lock", "verifier.lock/owner", "verifier.queue/00000000000000000001-123"):
                self.assertTrue(entry["missing_owned_live_entry"](root, profile / relative))
            for relative in ("verifier.queue", "verifier.queue/123-123", "verifier.queue/00000000000000000001-0",
                             "verifier.lock/other", "other", "verifier.slot2.lock"):
                self.assertFalse(entry["missing_owned_live_entry"](root, profile / relative))

    def test_live_lock_lstat_race_is_narrow_and_settled_walk_is_strict(self):
        original = os.scandir
        def run(relative, live, accepted):
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                root = Path(folder)
                target = root / "mixed-pair-profile" / relative
                target.parent.mkdir(parents=True); target.write_text("fixture")
                hit = []
                class Entry:
                    def __init__(self, item): self.item, self.path = item, item.path
                    def stat(self, **kwargs):
                        if Path(self.path) == target:
                            target.unlink(); hit.append(str(target)); raise FileNotFoundError(str(target))
                        return self.item.stat(**kwargs)
                class Scan:
                    def __init__(self, parent): self.scan = original(parent)
                    def __enter__(self):
                        self.entries = self.scan.__enter__()
                        return self
                    def __iter__(self): return (Entry(item) for item in self.entries)
                    def __exit__(self, *args): return self.scan.__exit__(*args)
                with patch.object(entry["os"], "scandir", side_effect=Scan):
                    if accepted:
                        entry["raw_extent"](root, allow_missing_lifecycle=live)
                    else:
                        with self.assertRaises(FileNotFoundError): entry["raw_extent"](root, allow_missing_lifecycle=live)
                self.assertEqual(len(hit), 1)
        run("verifier.lock/owner", True, True)
        run("verifier.queue/00000000000000000001-123", True, True)
        run("unrelated", True, False)
        run("verifier.lock/owner", False, False)

    def test_success_settlement_requires_absent_lock_scratch_and_empty_queue(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder); self.aliases(root)
            profile = root / "mixed-pair-profile"
            lock = profile / "verifier.lock"; lock.mkdir()
            with self.assertRaisesRegex(ValueError, "lock must be absent"): entry["raw_extent"](root, require_aliases=True)
            lock.rmdir(); queue = profile / "verifier.queue"; queue.mkdir()
            (queue / "ticket").write_text("x")
            with self.assertRaisesRegex(ValueError, "queue must be empty"): entry["raw_extent"](root, require_aliases=True)
            (queue / "ticket").unlink()
            job, temporary = self.make_job(root)
            with self.assertRaisesRegex(ValueError, "scratch must settle"): entry["raw_extent"](root, require_aliases=True)
            temporary.rmdir(); temporary.parent.rmdir()
            entry["raw_extent"](root, require_aliases=True)

    def test_queued_directory_cleanup_race_is_exact_and_live_only(self):
        original = os.scandir
        for kind, live, accepted in (("lock", True, True), ("wp", True, True), ("cbmc", True, True),
                                     ("unknown", True, False), ("lock", False, False)):
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                root = Path(folder)
                if kind in ("wp", "cbmc"):
                    _job, target = self.make_job(root,
                        "contract.fixture_pair_pointer_values" if kind == "cbmc" else None,
                        "cbmc" if kind == "cbmc" else "wp")
                else:
                    target = root / "mixed-pair-profile" / ("verifier.lock" if kind == "lock" else "other")
                    target.mkdir(parents=True)
                hit = []
                def race(parent):
                    if Path(parent) == target:
                        target.rmdir(); hit.append(str(target)); raise FileNotFoundError(str(target))
                    return original(parent)
                with patch.object(entry["os"], "scandir", side_effect=race):
                    if accepted:
                        entry["raw_extent"](root, allow_missing_lifecycle=live)
                    else:
                        with self.assertRaises(FileNotFoundError): entry["raw_extent"](root, allow_missing_lifecycle=live)
                self.assertEqual(len(hit), 1)

    def test_primary_error_is_independent_first_failure_and_fits_shared_reserve(self):
        old_parent = entry["RAW_PARENT"]
        try:
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                entry["RAW_PARENT"] = Path(folder)
                root = Path(folder) / entry["RAW_NAME"]; root.mkdir()
                first = ValueError("original live refusal")
                entry["preserve_primary_error"](root, first, "profile-work")
                original = (root / "mixed-primary-error.json").read_bytes()
                entry["preserve_primary_error"](root, RuntimeError("later postcheck"), "postcheck")
                self.assertEqual((root / "mixed-primary-error.json").read_bytes(), original)
                self.assertEqual(entry["primary_error_summary"](root)["reason"], "original live refusal")
                result, code = entry["finalize_result"](root, {"status": "REFUSED_OR_FAILED"}, 0, clock=lambda: 1)
                self.assertEqual(code, 1)
                self.assertEqual(result["primary_error"]["reason"], "original live refusal")
                self.assertLessEqual(entry["raw_extent"](root, reserve=0)["bytes"], entry["TOTAL_BYTES"])
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                entry["RAW_PARENT"] = Path(folder)
                root = Path(folder) / entry["RAW_NAME"]; root.mkdir()
                os.mkfifo(root / "unknown-fifo")
                entry["preserve_primary_error"](root, first, "profile-work")
                with self.assertRaisesRegex(ValueError, "special entry refused"):
                    entry["finalize_result"](root, {"status": "REFUSED_OR_FAILED"}, 0, clock=lambda: 1)
                self.assertEqual(entry["primary_error_summary"](root)["reason"], "original live refusal")
                with self.assertRaisesRegex(ValueError, "primary error prevents"):
                    entry["finalize_result"](root, {"status": "PRODUCER_WORKFLOW_COMPLETE"}, 0, clock=lambda: 1)
        finally:
            entry["RAW_PARENT"] = old_parent

    def test_fresh_why3_additions_are_prospective_and_prior_runtime_pins_preserved(self):
        policy = json.loads((HERE / "policy.json").read_bytes())
        old = json.loads((HERE.with_name("mixed-pair-actual-v5") / "policy.json").read_bytes())
        self.assertEqual(len(policy["runtime_files"]), len(old["runtime_files"]) + 148)
        self.assertTrue(all(policy["runtime_files"][path] == digest for path, digest in old["runtime_files"].items()))
        self.assertEqual(policy["ocaml_packages"]["why3"], entry["WHY3_ROOT"])
        self.assertEqual(policy["runtime_ipc_policy"], entry["runtime_ipc_policy"]())
        self.assertIn("not historical", policy["why3_runtime_extension"]["historical_gap"])
        for key in ("source_files", "source_consumer_trees", "source_checker_identities", "source_checker_material",
                    "native_runtime", "guard", "selection", "actual_initialized_lineup", "root_control_admission"):
            self.assertEqual(policy[key], old[key])
        for path, inventory in policy["why3_runtime_extension"]["inventories"].items():
            for row in inventory["files"]:
                self.assertEqual(policy["runtime_files"][str(Path(path) / row["relative"])], row["sha256"])
        elf = json.loads((HERE / "why3-extension-ELF-candidates-passive.json").read_bytes())
        self.assertEqual(len(elf["ELFs"]), 45)
        self.assertTrue(all(binding["covered"] for row in elf["ELFs"] for binding in row["bindings"].values()))

    def test_primary_error_and_final_metadata_share_the_original_fixed_reserve(self):
        keys = ("RAW_PARENT", "TOTAL_BYTES", "STAGE_BYTES", "FINAL_RESERVE_BYTES", "FINAL_RESULT_BYTES", "PRIMARY_ERROR_BYTES")
        old = {key: entry[key] for key in keys}
        entry.update(TOTAL_BYTES=8192, STAGE_BYTES=8192, FINAL_RESERVE_BYTES=4096,
                     FINAL_RESULT_BYTES=2048, PRIMARY_ERROR_BYTES=1024)
        try:
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                entry["RAW_PARENT"] = Path(folder)
                root = Path(folder) / entry["RAW_NAME"]; root.mkdir()
                (root / "payload").write_bytes(b"x" * 4096)
                entry["preserve_primary_error"](root, ValueError("primary"), "profile-work")
                result, code = entry["finalize_result"](root, {"status": "REFUSED_OR_FAILED"}, 0, clock=lambda: 1)
                self.assertEqual(code, 1)
                self.assertEqual(result["primary_error"]["reason"], "primary")
                self.assertLessEqual(result["finalization"]["projected_total_bytes"], 8192)
                self.assertLessEqual((root / "mixed-primary-error.json").stat().st_size, 1024)
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                entry["RAW_PARENT"] = Path(folder)
                root = Path(folder) / entry["RAW_NAME"]; root.mkdir()
                (root / "payload").write_bytes(b"x" * 4097)
                with self.assertRaisesRegex(ValueError, "fixed reserved budget"):
                    entry["preserve_primary_error"](root, ValueError("primary"), "profile-work")
                self.assertFalse((root / "mixed-primary-error.json").exists())
        finally:
            entry.update(old)

    def test_failed_known_socket_can_settle_metadata_without_claiming_success(self):
        old_parent = entry["RAW_PARENT"]
        try:
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                entry["RAW_PARENT"] = Path(folder)
                root = Path(folder) / entry["RAW_NAME"]; root.mkdir()
                _job, temporary = self.make_job(root)
                self.make_socket(temporary)
                entry["preserve_primary_error"](root, ValueError("original work failure"), "profile-work")
                result, code = entry["finalize_result"](root, {"status": "REFUSED_OR_FAILED"}, 0, clock=lambda: 1)
                self.assertEqual(code, 1)
                self.assertEqual(result["primary_error"]["reason"], "original work failure")
                self.assertEqual(len(result["finalization"]["before"]["runtime_ipc"]), 1)
                self.assertFalse(result.get("independent_cold_acceptance", False))
        finally:
            entry["RAW_PARENT"] = old_parent

    def test_two_console_records_fit_declared_shared_metadata_reserve(self):
        value = {"error": "\U0001f4a5" * 128, "reason": "\U0001f4a5" * 4096,
                 "primary_error": {"path": "mixed-primary-error.json", "bytes": 16384, "sha256": "f" * 64}}
        first = json.dumps({"primary_failure": entry["console_failure"](value)}, sort_keys=True).encode() + b"\n"
        second = json.dumps({"status": "FINALIZATION_REFUSED", "error": "\U0001f4a5" * 64,
            "reason": "\U0001f4a5" * 192, "primary_failure": entry["console_failure"](value),
            "independent_cold_acceptance": False}, sort_keys=True).encode() + b"\n"
        self.assertLessEqual(len(first), 8192)
        self.assertLessEqual(len(second), 8192)
        self.assertLessEqual(entry["PRIMARY_ERROR_BYTES"] + entry["FINAL_RESULT_BYTES"]
                             + len(first) + len(second) + 16384, entry["FINAL_RESERVE_BYTES"])

    def test_entry_and_gate_sources_compile_without_execution(self):
        for name in ("entry.py", "reviewed_wp_gates.py", "reviewed_native_gates.py", "prepare.py"):
            compile((HERE / name).read_bytes(), name, "exec")
        self.assertEqual(attempts, [])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"date": "2026-10-16 ET", "pure_controls": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "child_native_network_attempts": attempts, "actual_profile_executed": False}, sort_keys=True))
    raise SystemExit(not result.wasSuccessful())
