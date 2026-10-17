"""2026-10-16 ET. Pure cold-reader refusal controls; no project/tool runtime."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest


def deny(event, arguments):
    if event.startswith(("subprocess.", "os.exec", "os.spawn")) or event in {"os.system", "os.fork", "os.forkpty", "ctypes.dlopen"}:
        raise RuntimeError("child execution prohibited")

sys.addaudithook(deny)
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("initialized_cold_obligations", HERE / "initialized_cold_obligations_v1.py")
reader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reader)


def synthetic_current_fixture():
    """Closed coherence fixture only; no retained/generated proof evidence."""
    site = Path("/synthetic-only/scratch/wp_input.c")
    def prop(name, function, kind, description, line=9):
        return {"property": name, "function": function, "kind": kind,
                "description": description, "line": line, "source_file": str(site),
                "status_registered": True, "property_export_origin": "registered",
                "generated_smoke_failure": False, "dependencies": [], "origin": None,
                "extern": False, "property_variant": "IPOther" if kind == "other" else "IPEnsures",
                "emitter": "", "call_context": None}
    properties = [prop(helper + "_exits", helper, "contract", r"exits \false", 1)
                  for helper in sorted(reader.HELPERS)]
    properties += [prop("trust_fixture_ensures", "trust_fixture", "contract", r"ensures \result == 711"),
                   prop("trust_fixture_smoke", "trust_fixture", "other", "wp_smoke_dead_code")]
    goals = [{"goal": "typed_real_trust_fixture_ensures", "property": "trust_fixture_ensures",
              "function": "trust_fixture", "line": 9, "smoke": False, "passed": True,
              "targets": [], "results": ["valid"]},
             {"goal": "typed_real_trust_fixture_smoke", "property": "trust_fixture_smoke",
              "function": "trust_fixture", "line": 9, "smoke": True, "passed": True,
              "targets": [], "results": ["unknown"]}]
    native = [{"goal": goal["goal"], "property": goal["property"], "function": goal["function"],
               "line": goal["line"], "smoke": goal["smoke"], "passed": True, "file": str(site),
               "verdict": "unknown" if goal["smoke"] else "valid", "proved": 1,
               "provers": [{"prover": "qed", "success": 1, "time": 0}]} for goal in goals]
    saved = [{"goal": goal["goal"], "property": goal["property"], "function": goal["function"],
              "smoke": goal["smoke"], "source": "wp_json", "status": "valid", "solver": "qed", "seconds": 0}
             for goal in goals]
    record = {"verdict": "proven", "pins": {"proof_semantics": "synthetic-only"}, "assumptions": [], "goals": saved}
    inventory = {"version": "1", "complete": True, "properties": properties, "goals": goals,
                 "property_closure": {"registration_membership_refreshed_after_consolidation": True,
                                      "unregistered_status_lookup_performed": False,
                                      "unregistered_wp_smoke_properties": [], "unregistered_wp_call_instances": [],
                                      "initial_registered_snapshot_count": len(properties),
                                      "registered_snapshot_count": len(properties), "exported_count": len(properties)}}
    rows = [{"directory": ".", "file": "wp_input.c", "line": "1", "function": helper,
             "property kind": "postcondition", "status": "Unknown", "property": r"\false"}
            for helper in sorted(reader.HELPERS)]
    rows += [{"directory": ".", "file": "wp_input.c", "line": "9", "function": "trust_fixture",
              "property kind": "postcondition", "status": "Valid", "property": r"\result == 711"}]
    return record, inventory, native, rows, site


class ColdObligations(unittest.TestCase):
    def test_current_goal_property_site_and_owner(self):
        fixture = synthetic_current_fixture()
        self.assertEqual(reader.current_goals(*fixture)["goals"], 2)
        for field, value in [("line", 99), ("function", "get_reg_unsigned_int")]:
            record, inventory, native, rows, site = copy.deepcopy(fixture)
            # Make all goal artifacts agree, leaving only the property/CSV site
            # unchanged. A current-only crosswalk must detect this inconsistency.
            inventory["goals"][0][field] = value
            native[0][field] = value
            if field == "function": record["goals"][0][field] = value
            with self.subTest(field=field):
                with self.assertRaises(AssertionError):
                    reader.current_goals(record, inventory, native, rows, site)

    def test_only_explicit_helper_dead_call_owner_bridge(self):
        record, inventory, native, rows, site = synthetic_current_fixture()
        helper = "get_reg_unsigned_int"
        name = helper + "_wp_smoke_dead_call_s31"
        goal_name = "typed_real_" + name
        inventory["properties"][-1].update(property=name, function=helper, description="wp_smoke_dead_call")
        inventory["goals"][-1].update(goal=goal_name, property=name, function=helper)
        native[-1].update(goal=goal_name, property=name)
        record["goals"][-1].update(goal=goal_name, property=name)
        report = reader.current_goals(record, inventory, native, rows, site)
        self.assertEqual(report["helper_context_bridges"], [goal_name])
        native[-1]["function"] = helper
        record["goals"][-1]["function"] = "init_MAA"
        with self.assertRaises(AssertionError):
            reader.current_goals(record, inventory, native, rows, site)

    def test_ordinary_direct_valid_requires_native_success(self):
        record, inventory, native, rows, site = synthetic_current_fixture()
        native[0]["provers"][0]["success"] = 0
        record["goals"][0].update(solver=None, seconds=None)
        with self.assertRaises(AssertionError):
            reader.current_goals(record, inventory, native, rows, site)
        for field, value in [("proved", 0), ("proved", True), ("failed", 1),
                             ("timeout", 1), ("unknown", 1), ("tactics", 1), ("cached", 1)]:
            record, inventory, native, rows, site = synthetic_current_fixture()
            native[0][field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(AssertionError):
                    reader.current_goals(record, inventory, native, rows, site)

    def test_exact_initialized_input(self):
        text = (HERE / "cold-reference-wp-correct.c").read_text()
        self.assertEqual(reader.initialized_wp_source(text, 711, HERE)["expected_result"], 711)
        self.assertEqual(reader.initialized_wp_source(text.replace("== 711 ;", "== 1107 ;"), 1107, HERE)["expected_result"], 1107)
        self.assertEqual(reader.initialized_wp_source(text.replace("C lowering of", "Different ordinary comment: C lowering of"), 711, HERE)["expected_result"], 711)
        for changed in [text.replace("0 <= REG_count <= 31", "0 <= REG_count <= 32"),
                        text.replace("unsigned int", "unsignedint"),
                        text.replace("/* swdb-anchor trust_fixture.s4.before */", r"//@ assert \false;"),
                        text.replace("/* swdb-anchor trust_fixture.s4.before */", "/* *" + chr(92) + "\n/ int injected; /* */"),
                        text.replace("/* swdb-anchor trust_fixture.s4.before */", "/* *" + chr(92) + " \n/ int injected; /* */"),
                        text.replace("/* swdb-anchor trust_fixture.s4.before */", "/* *??/\n/ int injected; /* */"),
                        text.replace("SPD_count ,", ""),
                        text.replace("int first =", "/*@ assume REG_count == 0; */ int first ="),
                        text.replace("+ 0", "+ 1", 1),
                        text.replace("terminates \\false;", "terminates \\true;", 1)]:
            with self.subTest(changed=changed[:30]):
                with self.assertRaises(AssertionError): reader.initialized_wp_source(changed, 711, HERE)

    def test_smoke_display_health(self):
        goal = {"goal": "smoke", "passed": True, "results": ["unknown"]}
        native = {"passed": True, "verdict": "unknown", "proved": 1,
                  "provers": [{"prover": "qed", "success": 0, "time": 0},
                              {"prover": "Z3:5.1.0", "success": 1, "time": 0}]}
        self.assertEqual(reader.check_passed_smoke(goal, native)["raw_best_verdict"], "unknown")
        for key, value in [("results", []), ("results", ["valid"]), ("results", ["untried"]), ("passed", False)]:
            changed = copy.deepcopy(goal); changed[key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(AssertionError): reader.check_passed_smoke(changed, native)
        for key, value in [("passed", False), ("verdict", "valid"), ("proved", 0), ("cached", 1), ("script", {})]:
            changed = copy.deepcopy(native); changed[key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(AssertionError): reader.check_passed_smoke(goal, changed)

    def test_dependency_census_and_cycle(self):
        inventory = {"properties": [{"property": "origin", "dependencies": []}, {"property": "caller", "dependencies": ["origin"]}]}
        self.assertEqual(reader.dependency_DAG(inventory)["dependency_edges"], 1)
        mutations = [inventory["properties"] + [inventory["properties"][0]],
                     [{"property": "caller", "dependencies": ["missing"]}],
                     [{"property": "loop", "dependencies": ["loop"]}]]
        for properties in mutations:
            with self.subTest(properties=properties):
                with self.assertRaises(AssertionError): reader.dependency_DAG({"properties": properties})

    def test_tsv_no_omitted_or_malformed_rows(self):
        header = "directory\tfile\tline\tfunction\tproperty kind\tstatus\tproperty\n"
        row = ".\twp_input.c\t1\ttrust_fixture\tpostcondition\tValid\tresult == 711\n"
        self.assertEqual(len(reader.csv_properties(header + row)), 1)
        for text in [header, "wrong\n" + row, header + "unexpected\tshape\n", header + " continuation\n"]:
            with self.subTest(text=text):
                with self.assertRaises(AssertionError): reader.csv_properties(text)


if __name__ == "__main__": unittest.main()
