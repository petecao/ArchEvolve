"""The C lowering tool: `swdb lower` turns a core-subset C++ proof unit into C with kept names and anchors.

Created: 2026-10-14 ET (Probata proof of concept ticket 21). Design: formal-verification map 16 items 3
and 6 (C lowering, kept names), 13 items 4 and 7 (anchors), 11 item 3 (a trusted tool). Format:
docs/reference/format-v0.4-c-lowering-wp.md.

Updated: 2026-10-14 ET (ticket 24: the declared C++ subset, its construct-group fixtures in
tests/fixtures/proof/lowering/, and the spike (b) differential against prototype/06c-cbmc/unit_peter.c).

Seam: the public command `swdb lower` (and, for the faithfulness tests, the lowered C file it writes).
Cases need clang 22.1.8 (the tool's C++ front end) and skip cleanly without it. No proof runs here; one
case type-checks a formal half with Frama-C (skipped without it).
"""
import hashlib
import json
import re
import shutil
import subprocess

import pytest
import yaml

from conftest import FIXTURES, REPO, run_swdb

WP = FIXTURES / "proof" / "wp"
SPIKE = REPO / ".scratch" / "probata-proof-of-concept-2026-10-13" / "prototype" / "06-two-lanes"


def _clang():
    from swdb import c_lowering
    return c_lowering.locate()


pytestmark = pytest.mark.skipif(bool(_clang().missing), reason="clang 22.1.8 (the C lowering's front end) is missing")


def lower(source, function, out, *extra, ok=True):
    result = run_swdb("lower", "--source", source, "--function", function, "--out", out, "--format", "json", *extra)
    assert (result.returncode == 0) is ok, result.stderr + result.stdout
    return json.loads(result.stdout) if ok else result


def test_lowering_twice_gives_byte_identical_c_and_the_same_anchor_list(tmp_path):
    first = lower(WP / "core_subset.cc", "swdb_core_kernel", tmp_path / "one")
    second = lower(WP / "core_subset.cc", "swdb_core_kernel", tmp_path / "two")
    assert first["c_lowering"]["sha256"] == second["c_lowering"]["sha256"]
    assert first["anchors"]["sha256"] == second["anchors"]["sha256"]
    c_one, c_two = (tmp_path / "one" / "swdb_core_kernel.c"), (tmp_path / "two" / "swdb_core_kernel.c")
    assert c_one.read_bytes() == c_two.read_bytes()
    assert (tmp_path / "one" / "swdb_core_kernel.anchors.json").read_bytes() == \
        (tmp_path / "two" / "swdb_core_kernel.anchors.json").read_bytes()
    assert str(tmp_path) not in c_one.read_text()          # no absolute path, so a second folder gives the same bytes


FILL_C = """\
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
/* swdb-anchor ghost.globals */
void swdb_fixture_fill(int *a, int n, int v);
/* swdb-anchor swdb_fixture_fill.contract */
void swdb_fixture_fill(int *a, int n, int v) {
  /* swdb-anchor swdb_fixture_fill.entry */
  /* swdb-anchor swdb_fixture_fill.s1.before */
  /* swdb-anchor swdb_fixture_fill.loop1.head */
  for (int i = 0; i < n; ++i) {
    /* swdb-anchor swdb_fixture_fill.s2.before */
    a[i] = v;
    /* swdb-anchor swdb_fixture_fill.s2.after */
  }
  /* swdb-anchor swdb_fixture_fill.s1.after */
}
"""


def test_kept_names_and_anchors_at_entry_loop_heads_around_each_statement_and_one_ghost_slot(tmp_path):
    out = lower(WP / "fixture_units.cc", "swdb_fixture_fill", tmp_path)
    text = (tmp_path / "swdb_fixture_fill.c").read_text()
    header, rest = text.split("\n", 1)
    assert header.startswith("/* C lowering of swdb_fixture_fill from fixture_units.cc (sha256 ")
    assert rest == FILL_C                                   # the C++ names are kept, no renaming layer
    listed = json.loads((tmp_path / "swdb_fixture_fill.anchors.json").read_text())
    assert listed["c_lowering_sha256"] == out["c_lowering"]["sha256"]
    assert [(a["id"], a["kind"], a["line"]) for a in listed["anchors"]] == [
        ("ghost.globals", "ghost_globals", 5), ("swdb_fixture_fill.contract", "contract", 7),
        ("swdb_fixture_fill.entry", "entry", 9), ("swdb_fixture_fill.s1.before", "before", 10),
        ("swdb_fixture_fill.loop1.head", "loop_head", 11), ("swdb_fixture_fill.s2.before", "before", 13),
        ("swdb_fixture_fill.s2.after", "after", 15), ("swdb_fixture_fill.s1.after", "after", 17)]
    lines = text.splitlines()
    for anchor in listed["anchors"]:                         # each listed line holds that anchor's comment
        assert lines[anchor["line"] - 1].strip() == f"/* swdb-anchor {anchor['id']} */"


def test_every_anchor_id_is_unique_and_the_c_compiles_as_c11(tmp_path):
    lower(WP / "core_subset.cc", "swdb_core_kernel", tmp_path)
    listed = json.loads((tmp_path / "swdb_core_kernel.anchors.json").read_text())["anchors"]
    ids = [a["id"] for a in listed]
    assert len(ids) == len(set(ids))
    assert sum(a["kind"] == "loop_head" for a in listed) == 4 and sum(a["kind"] == "ghost_globals" for a in listed) == 1
    assert {a["function"] for a in listed if a["kind"] == "entry"} == {"swdb_core_kernel", "swdb_core_clamp", "swdb_core_mix"}
    clang = _clang().command[0].replace("clang++", "clang")
    done = subprocess.run([clang, "-std=c11", "-Wall", "-Werror", "-fsyntax-only", tmp_path / "swdb_core_kernel.c"],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_the_c_lowering_agrees_with_the_cpp_on_every_input_of_a_bounded_domain(tmp_path):
    """C-versus-C++ differential (pattern of prototype/06c-cbmc/faith/): same harness, identical output."""
    lower(WP / "core_subset.cc", "swdb_core_kernel", tmp_path / "low")
    compiler = _clang().command[0]
    (tmp_path / "x.cc").write_text(f'#include "{WP / "core_subset.cc"}"\n#include "{WP / "core_harness.inc"}"\n')
    (tmp_path / "c.c").write_text(f'#include "{tmp_path / "low" / "swdb_core_kernel.c"}"\n'
                                  f'#include "{WP / "core_harness.inc"}"\n')
    outputs = {}
    for name, command in (("cxx", [compiler, "-std=c++17", "-O1", tmp_path / "x.cc", "-o", tmp_path / "cxx"]),
                          ("c", [compiler.replace("clang++", "clang"), "-std=c11", "-O1", tmp_path / "c.c",
                                 "-o", tmp_path / "c"])):
        built = subprocess.run(command, capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        outputs[name] = subprocess.run([tmp_path / name], capture_output=True, text=True, check=True).stdout
    assert outputs["c"] == outputs["cxx"] and len(outputs["c"].splitlines()) == 4000


# Ticket 24: outside the declared subset (map 16 item 6: "out at first"), plus what the subset never had.
# Each source names its function swdb_outside_unit and its types Swdb*, so clang's name-filtered dumps stay small.
OUTSIDE = {
    "inheritance": "struct SwdbBase { int x; };\nstruct SwdbDerived : SwdbBase { int y; };\n"
                   "int swdb_outside_unit(SwdbDerived *d) { return d->y; }\n",
    "virtual function": "struct SwdbShape { int x; virtual int area() { return x; } };\n"
                        "int swdb_outside_unit(SwdbShape *s) { return s->x; }\n",
    "exception": "int swdb_outside_unit(int x) {\n  if (x < 0) throw 1;\n  return x;\n}\n",
    "lambda": "int swdb_outside_unit(int x) {\n  auto add = [](int y) { return y + 1; };\n  return add(x);\n}\n",
    "RTTI": "struct SwdbNode { int x; };\nint swdb_outside_unit(SwdbNode *n) {\n"
            "  SwdbNode *m = dynamic_cast<SwdbNode *>(n);\n  return m->x;\n}\n",
    "standard container std::map": "#include <map>\nint swdb_outside_unit(int k) {\n  std::map<int, int> m;\n"
                                   "  m[k] = 1;\n  return m[k];\n}\n",
    "stream": "#include <iostream>\nint swdb_outside_unit(int x) {\n  std::cout << x;\n  return x;\n}\n",
    "floating-point type": "long double swdb_outside_unit(long double x) { return x; }\n",
    "no body": "int swdb_outside_g(int);\nint swdb_outside_unit(int x) { return swdb_outside_g(x); }\n",
    "member function": "struct SwdbS { int swdb_outside_unit() { return 1; } };\n",
    "overloaded function": "int swdb_outside_unit(int x) { return x; }\nint swdb_outside_unit(long x) { return 1; }\n",
    "OpenMP directive": "int swdb_outside_unit(int *a, int n) {\n#pragma omp parallel\n  {\n#pragma omp single\n"
                        "    a[0] = n;\n  }\n  return 0;\n}\n",
    "OpenMP clause": "int swdb_outside_unit(int *a, int n) {\n  int t = 0;\n#pragma omp parallel for private(t)\n"
                     "  for (int i = 0; i < n; ++i) { t = i; a[i] = t; }\n  return 0;\n}\n",
    # ticket 25: what the std::vector and std::pair models leave out
    "std::vector<bool>": "#include <vector>\nint swdb_outside_unit(int n) {\n  std::vector<bool> b((unsigned)n);\n"
                         "  return (int)b.size();\n}\n",
    "std::vector<int> member pop_back (not modeled)": "#include <vector>\nint swdb_outside_unit(int n) {\n"
                                                     "  std::vector<int> v((unsigned)n);\n  v.pop_back();\n"
                                                     "  return (int)v.size();\n}\n",
    "std::vector<int> operator= (not modeled)": "#include <vector>\nint swdb_outside_unit(int n) {\n"
                                                "  std::vector<int> v((unsigned)n), w;\n  w = v;\n  return 0;\n}\n",
    "std::pair<int, int> member swap (not modeled)": "#include <utility>\nint swdb_outside_unit(int n) {\n"
                                                     "  std::pair<int, int> p(n, 1), q(1, n);\n  p.swap(q);\n"
                                                     "  return p.first;\n}\n",
    "std::vector of SwdbP": "#include <vector>\nstruct SwdbP { int x; };\nint swdb_outside_unit(int n) {\n"
                            "  std::vector<SwdbP> v((unsigned)n);\n  return (int)v.size();\n}\n",
    "range-based for over anything but a std::vector": "int swdb_outside_unit(int n) {\n  int a[3] = {n, n, n};\n"
                                                        "  int s = 0;\n  for (int x : a) s += x;\n  return s;\n}\n",
}
LINE_OF = {"exception": 2, "lambda": 2, "RTTI": 3, "standard container std::map": 3, "stream": 3,
           "OpenMP directive": 4, "OpenMP clause": 3, "std::vector<bool>": 3,
           "std::vector<int> member pop_back (not modeled)": 4, "std::vector<int> operator= (not modeled)": 4,
           "std::pair<int, int> member swap (not modeled)": 4}


@pytest.mark.parametrize("construct", sorted(OUTSIDE))
def test_a_construct_outside_the_subset_is_refused_by_name_and_line_with_no_partial_lowering(tmp_path, construct):
    source = tmp_path / "unit.cc"
    source.write_text(OUTSIDE[construct])
    result = lower(source, "swdb_outside_unit", tmp_path / "out", ok=False)
    assert result.returncode == 1
    assert "unsupported construct" in result.stderr and "Traceback" not in result.stderr
    assert construct in result.stderr
    if construct in LINE_OF:
        assert f"unit.cc line {LINE_OF[construct]})" in result.stderr
    assert str(tmp_path) not in result.stderr                # names the file, never an absolute path
    assert not (tmp_path / "out").exists()


def test_the_spike_b_unit_as_built_is_refused_for_the_inheritance_of_its_push_hook(tmp_path):
    """Ticket 06's unit_peter.cpp includes the candidate prelude's push hook, a class that derives from
    QueueBuffer: outside the subset. The tool names it instead of crashing (spike_peter_unit.cc undoes the hook)."""
    result = lower(SPIKE / "unit_peter.cpp", "swdb_unit_peter", tmp_path / "out",
                   "--include", REPO / "library" / "dx100", ok=False)
    assert "unsupported construct: inheritance (class swdb_hooked_QueueBuffer has a base class)" in result.stderr
    assert "spike_lowering.hpp line" in result.stderr and "Traceback" not in result.stderr
    assert not (tmp_path / "out").exists()


CORPUS = sorted((FIXTURES / "proof" / "regression_corpus").glob("*.yaml"))


@pytest.mark.parametrize("case", [c for c in CORPUS if yaml.safe_load(c.read_text())["adapter"] == "c_lowering"],
                         ids=lambda c: c.stem)
def test_each_lowering_regression_corpus_case_gives_its_recorded_class_again(tmp_path, case):
    data = yaml.safe_load(case.read_text())
    assert data["cause"].strip()
    given = data["input"]
    extra = [arg for folder in given.get("include", []) for arg in ("--include", REPO / folder)]
    extra += [arg for name in given.get("summary", []) for arg in ("--summary", f"{name}=corpus")]   # ticket 24
    result = lower(REPO / given["source"], given["function"], tmp_path / "out", *extra, ok=False)
    words = {"unsupported_construct": "unsupported construct", "parse_error": "parse error"}[data["failure_class"]]
    assert words in result.stderr
    assert data.get("construct", "") in result.stderr          # ticket 24: the construct the case names


def test_cpp_that_does_not_parse_is_a_parse_error(tmp_path):
    source = tmp_path / "broken.cc"
    source.write_text("int f(int x) { return x + ; }\n")
    result = lower(source, "f", tmp_path / "out", ok=False)
    assert "parse error" in result.stderr and "expected expression" in result.stderr


# --- ticket 24: the declared C++ subset ------------------------------------------------------------------
# Seams: `swdb lower` (the public command) and, for faithfulness, the C it writes, built next to the C++ with
# one shared harness per construct group (C-versus-C++ differential on a bounded domain, as above).

LOWERING = FIXTURES / "proof" / "lowering"
CPROTO = REPO / ".scratch" / "probata-proof-of-concept-2026-10-13" / "prototype" / "06c-cbmc"
GROUPS = {   # construct group: (fixture, unit function, extra `swdb lower` arguments)
    "classes": ("classes.cc", "swdb_class_unit", ()),
    "templates": ("templates.cc", "swdb_template_unit", ()),
    "new_array": ("new_array.cc", "swdb_new_unit", ()),
    "std_models": ("std_models.cc", "swdb_std_unit", ()),
    "omp": ("omp_atomics.cc", "swdb_omp_unit", ()),
    "atomics": ("omp_atomics.cc", "swdb_atomics_unit", ()),
    "floats": ("floats.cc", "swdb_float_unit", ()),
    "vector_pair": ("vector_pair.cc", "swdb_vector_unit", ()),          # ticket 25
    "dxc_summary": ("summaries.cc", "swdb_dxc_unit", ("--summary", "__dxc_tile_size=fixture.dxc_tile_size.1")),
    "maa_summary": ("summaries.cc", "swdb_maa_unit", ("--summary", "maa_const_i32=fixture.maa_const.1",
                                                      "--summary", "maa_indirect_load_i32=fixture.maa_indirect_load.1")),
}
HARNESS = {"classes": "classes_harness.inc", "templates": "templates_harness.inc", "new_array": "new_array_harness.inc",
           "std_models": "std_models_harness.inc", "omp": "omp_atomics_harness.inc", "floats": "floats_harness.inc",
           "vector_pair": "vector_pair_harness.inc"}


def _c_compiler():
    return _clang().command[0].replace("clang++", "clang")


def _lowered(group, out):
    fixture, function, extra = GROUPS[group]
    lower(LOWERING / fixture, function, out, *extra)
    return (out / f"{function}.c").read_text(), json.loads((out / f"{function}.anchors.json").read_text())


@pytest.mark.parametrize("group", sorted(GROUPS))
def test_each_construct_group_lowers_twice_to_identical_c_and_anchors_that_compile_as_c11(tmp_path, group):
    fixture, function, extra = GROUPS[group]
    first = lower(LOWERING / fixture, function, tmp_path / "one", *extra)
    second = lower(LOWERING / fixture, function, tmp_path / "two", *extra)
    assert first["c_lowering"]["sha256"] == second["c_lowering"]["sha256"]
    assert first["anchors"]["sha256"] == second["anchors"]["sha256"]
    assert first["tool"]["version"] == "4" and first["tool"]["naming_rules"] == "kept-names.3"
    c_file = tmp_path / "one" / f"{function}.c"
    assert str(tmp_path) not in c_file.read_text()
    done = subprocess.run([_c_compiler(), "-std=c11", "-Wall", "-Werror", "-fsyntax-only", c_file],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize("group", sorted(HARNESS))
def test_each_construct_group_c_lowering_agrees_with_the_cpp_on_a_bounded_domain(tmp_path, group):
    """One harness, two builds: the C++ fixture (no -fopenmp: one thread) and its C lowering print the same lines."""
    fixture, function, _ = GROUPS[group]
    harness = LOWERING / HARNESS[group]
    functions = [function] if group != "omp" else ["swdb_omp_unit", "swdb_atomics_unit"]   # one harness, both units
    c_units = []
    for name in functions:
        lower(LOWERING / fixture, name, tmp_path / name)
        c_units.append(tmp_path / name / f"{name}.c")
    (tmp_path / "x.cc").write_text(f'#include "{LOWERING / fixture}"\n#include "{harness}"\n')
    (tmp_path / "c.c").write_text("".join(f'#include "{u}"\n' for u in c_units) + f'#include "{harness}"\n')
    outputs = {}
    for name, command in (("cxx", [_clang().command[0], "-std=c++17", "-O1", tmp_path / "x.cc", "-o", tmp_path / "cxx"]),
                          ("c", [_c_compiler(), "-std=c11", "-O1", tmp_path / "c.c", "-o", tmp_path / "c"])):
        built = subprocess.run(command, capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        outputs[name] = subprocess.run([tmp_path / name], capture_output=True, text=True, check=True).stdout
    assert outputs["c"] == outputs["cxx"] and len(outputs["c"].splitlines()) > 100


def test_kept_names_a_class_becomes_a_struct_references_become_pointers_members_become_named_functions(tmp_path):
    text, listed = _lowered("classes", tmp_path)
    assert "typedef struct Bag Bag;" in text and "struct Bag { int *data; int n; };" in text
    assert "struct Counter { int count_; int *total_; };" in text          # a reference member is a pointer
    assert "int *Bag_operator_index(Bag *this, int i);" in text             # operator[] returns int& -> int*
    assert "int Bag_size(const Bag *this);" in text                         # a const member function
    assert "void Bag_scale(Bag *this, int k);" in text
    assert "static void bump(int *x, int by);" in text                      # a reference parameter
    assert "int swdb_class_sum(const Bag *b);" in text
    body = text.split("int swdb_class_unit(int *a, int n, int mode) {")[1]
    assert "Counter counter;\n" in body and "Counter_ctor(&counter, &total);" in body   # constructor: explicit call
    assert body.index("Counter_ctor(&counter") < body.index("Counter_dtor(&counter);")  # destructor at scope end
    assert "Counter_add(&counter, (*Bag_operator_index(&bag, i)));" in body
    assert "bump(&total, kScale);" in body
    assert "int m = " in body and "? 2 : 0" in body                          # enum class -> int, enumerators -> values
    assert "const int kScale = 3;" in text                                  # constexpr -> const
    ids = {a["id"] for a in listed["anchors"]}
    assert {"Counter_ctor.entry", "Counter_dtor.entry", "Bag_operator_index.contract"} <= ids


def test_a_formal_half_over_the_class_field_names_type_checks_against_the_c_lowering():
    from swdb import c_lowering, framac
    tool = framac.locate()
    if tool.missing:
        pytest.skip(tool.missing)
    lowering = c_lowering.lower(LOWERING / "classes.cc", "swdb_class_sum")
    acsl = ("/*@ requires \\valid_read(b) && 0 <= b->n <= 1000;\n"
            "    requires \\valid_read(b->data + (0 .. b->n - 1));\n"
            "    assigns \\nothing; */\n")
    head, prototype = lowering.declaration.rstrip("\n").rsplit("\n", 1)
    assert prototype == "int swdb_class_sum(const Bag *b);"
    assert framac.typecheck(tool, f"{head}\n{acsl}{prototype}\n") is None
    wrong = acsl.replace("b->n", "b->size")                                 # a name the class does not have
    assert framac.typecheck(tool, f"{head}\n{wrong}{prototype}\n") is not None


def test_a_template_at_two_types_lowers_to_two_c_functions_and_two_structs_by_the_naming_rules(tmp_path):
    text, _ = _lowered("templates", tmp_path)
    assert "int twice_int(int x);" in text and "long twice_long(long x);" in text
    assert "struct Ring_int_3 { int items[3]; int head; };" in text
    assert "struct Ring_long_2 { long items[2]; int head; };" in text
    assert "void Ring_int_3_put(Ring_int_3 *this, int v);" in text
    assert "long Ring_long_2_get(const Ring_long_2 *this, int i);" in text


def test_new_and_delete_arrays_lower_to_allocation_models_and_the_seeded_bugs_lower_too(tmp_path):
    text, _ = _lowered("new_array", tmp_path)
    assert "#include <stdlib.h>" in text
    assert "int *buf = swdb_alloc_new_array_int((size_t)(n));" in text and "swdb_alloc_delete_array_int(buf);" in text
    for bug in ("swdb_new_out_of_range", "swdb_new_after_delete"):
        lower(LOWERING / "new_array.cc", bug, tmp_path / bug)
        assert "swdb_alloc_delete_array_int(buf);" in (tmp_path / bug / f"{bug}.c").read_text()


def test_each_std_function_lowers_to_a_call_of_its_c_model_with_its_acsl_contract(tmp_path):
    out = lower(LOWERING / "std_models.cc", "swdb_std_unit", tmp_path)
    text = (tmp_path / "swdb_std_unit.c").read_text()
    assert out["models"] == ["std_min_int", "std_max_int", "std_swap_int", "std_copy_int", "std_max_long"]
    for call in ("std_min_int(x, y)", "std_max_int(x, y)", "std_swap_int(&lo, &hi)", "std_copy_int(a, a + n, b)",
                 "std_max_long(lo, 7)"):
        assert call in text
    contract = text.split("static int *std_copy_int(")[0].rsplit("/*@", 1)[1]
    assert "assigns d_first[0 .. last - first - 1];" in contract and "\\separated(" in contract


def test_openmp_constructs_and_atomics_lower_to_their_one_thread_meaning(tmp_path):
    text, _ = _lowered("omp", tmp_path / "omp")
    for directive in ("parallel for", "parallel", "for", "atomic", "critical", "barrier"):
        assert f"/* omp {directive} (one thread) */" in text
    assert "sum += a[i];" in text and "#pragma" not in text
    text, _ = _lowered("atomics", tmp_path / "atomics")
    for model in ("swdb_atomic_load_n_int(p)", "swdb_atomic_store_n_int(p, old + v)", "swdb_atomic_fetch_add_int(p, 1)",
                  "swdb_atomic_exchange_n_int(p, f)", "swdb_atomic_compare_exchange_n_int(p, e, 9)",
                  "swdb_sync_bool_compare_and_swap_int(p, 9, 4)", "swdb_sync_val_compare_and_swap_int(p, 4, 5)",
                  "swdb_sync_fetch_and_add_int(p, 2)", "swdb_sync_add_and_fetch_int(p, 3)"):
        assert model in text


def test_a_reduction_variable_used_other_than_in_its_update_is_refused(tmp_path):
    source = tmp_path / "unit.cc"
    source.write_text("int swdb_reduce_unit(int *a, int n) {\n  int s = 0;\n#pragma omp parallel for reduction(+:s)\n"
                      "  for (int i = 0; i < n; ++i) { a[i] = s; s += 1; }\n  return s;\n}\n")
    result = lower(source, "swdb_reduce_unit", tmp_path / "out", ok=False)
    assert "unsupported construct: reduction variable s used other than in a `+=` update" in result.stderr


@pytest.mark.parametrize("group, call, summary", [
    ("dxc_summary", "__dxc_tile_size(tile)",
     {"name": "__dxc_tile_size", "c_name": "__dxc_tile_size", "summary": "fixture.dxc_tile_size.1"}),
    ("maa_summary", "maa_indirect_load_i32(base, 0, 1, -1)",
     {"name": "maa_indirect_load_i32", "c_name": "maa_indirect_load_i32", "summary": "fixture.maa_indirect_load.1"})])
def test_dxc_and_maa_calls_stay_calls_through_their_summary_and_the_lowering_lists_it(tmp_path, group, call, summary):
    text, listed = _lowered(group, tmp_path)
    assert call in text
    assert summary in listed["summaries"]
    name = re.escape(summary["c_name"])
    assert re.search(rf"^\w[\w ]*\b{name}\([^;{{]*\);$", text, re.M)              # a prototype ...
    assert not re.search(rf"\b{name}\([^;{{]*\)\s*{{", text)                       # ... and no definition


@pytest.mark.parametrize("function, name", [("swdb_dxc_unit", "__dxc_tile_size"), ("swdb_maa_unit", "maa_const_i32")])
def test_a_dxc_or_maa_call_with_no_summary_is_an_unsupported_construct(tmp_path, function, name):
    result = lower(LOWERING / "summaries.cc", function, tmp_path / "out", ok=False)
    assert f"unsupported construct: call to {name} with no summary" in result.stderr
    assert "summaries.cc line" in result.stderr


def test_the_naming_rules_carry_a_version_and_a_hash_that_bumping_changes():
    from swdb import c_lowering
    pin = c_lowering.identity()["naming_rules"]
    assert pin == {"id": "kept-names.3", "sha256": c_lowering.RULES_SHA256}
    bumped = hashlib.sha256("\n".join(("kept-names.4", *c_lowering.RULES)).encode()).hexdigest()
    assert bumped != pin["sha256"]


SPIKE_SUMMARIES = ("swdb_cxx_assert", "maa_const", "maa_stream_load", "maa_indirect_load", "maa_range_loop",
                   "wait_ready", "get_tile_size", "swdb_probe_tile_read", "swdb_probe_cpu", "__dxc_tile_size",
                   "__dxc_tile_pointer", "__dxc_accelerated_chunk")
SPIKE_GLUE = """
/* The spike's declared-only DX100 API (summaries), defined by the 06c stubs as faith/faith_cxx.cpp does. */
#define SWDB_UNIT_PETER 1
#define TILE_SIZE 2
#define NUM_TILES_PER_CORE 8
#define SPIKE_V 3
#define SPIKE_E 3
#define SPIKE_F 2
#define SPIKE_Q 8
#include <string.h>
int32_t swdb_tile_data[8][2];   /* tile memory (unit_common.hpp): only the stubs, the harness and the glue touch it */
#include "{stubs}"
void maa_const_int(int a, int b) {{ dx_const((int32_t)a, b); }}
void maa_stream_load_int(int *d, int lo, int hi, int st, int dst, int cond) {{
  dx_ps_stream_bounds(lo, hi, st); dx_ps_stream_capacity(lo, hi, st); dx_ps_stream_load(d, lo, hi, st, dst, cond);
}}
void maa_indirect_load_int(int *d, int idx, int dst, int cond) {{ dx_gather(d, idx, dst, cond); }}
void maa_range_loop_int(int li, int lj, int mn, int mx, int st, int di, int dj, int cond) {{
  dx_range_loop(li, lj, mn, mx, st, di, dj, cond);
}}
void wait_ready(int t) {{ dx_wait(t); }}
uint16_t get_tile_size(int t) {{ return dx_get_tile_size(t); }}
void swdb_probe_tile_read(int t) {{ dx_probe_tile_read(t); }}
void swdb_probe_cpu(int region, int is_write) {{ dx_probe_cpu(region, is_write); }}
uint16_t __dxc_tile_size(int t) {{ return get_tile_size(t); }}
int *__dxc_tile_pointer_int(int t) {{ swdb_probe_tile_read(t); return swdb_tile_data[t]; }}
void __dxc_accelerated_chunk(void) {{ ++swdb_spike_chunks; }}
void swdb_cxx_assert(bool ok, const char *text) {{     /* faith/faith_cxx.cpp's, in C */
  if (ok) return;
  static char name[128];
  const char *q = strchr(text, '"');
  if (!q) {{ swdb_native_prop_failed(text); return; }}
  size_t n = 0;
  for (const char *s = q + 1; *s && *s != '"' && n + 1 < sizeof name; ++s) name[n++] = *s;
  name[n] = 0;
  swdb_native_prop_failed(name);
}}
#include "{harness}"
"""


def _stream_sha256(command):
    digest, lines = hashlib.sha256(), 0
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as run:
        for chunk in iter(lambda: run.stdout.read(1 << 20), b""):
            digest.update(chunk)
            lines += chunk.count(b"\n")
        err = run.stderr.read().decode()
    assert run.returncode == 0, err
    return digest.hexdigest(), lines, err


def test_the_generated_lowering_of_the_spike_b_unit_agrees_with_its_hand_lowering_on_every_bounded_input(tmp_path):
    """prototype/06c-cbmc/unit_peter.c is ticket 06's hand lowering of spike (b)'s proof unit 1. The tool's
    lowering of the same unit (spike_peter_unit.cc: unit_peter.cpp without its push hook, Peter's code
    unchanged) runs ticket 06's native harness over every input of the bounded domain (1,731,456 runs, both
    acceleration settings) with the same DX100 stubs: the final state, the DX100 call trace and the P2
    properties print identically. Safe build only: the fault builds need the push hook (inheritance)."""
    includes = [SPIKE, SPIKE.parent / "06c-cbmc" / "faith" / "shim", REPO / "library" / "dx100"]
    extra = [a for folder in includes for a in ("--include", folder)]
    extra += [a for name in SPIKE_SUMMARIES for a in ("--summary", f"{name}=prototype.06-two-lanes.summaries.saw")]
    out = lower(LOWERING / "spike_peter_unit.cc", "swdb_unit_peter", tmp_path / "low", *extra)
    assert {s["name"] for s in out["summaries"]} <= set(SPIKE_SUMMARIES)
    text = (tmp_path / "low" / "swdb_unit_peter.c").read_text()
    for kept in ("void TDStep(const Graph *g, pvector_int *VertexOffsets, pvector_int *parent, SlidingQueue_int *queue,"
                 " int num_nodes, int num_edges)", "QueueBuffer_int_push_back(&lqueue, v);", "std_min_size_t(",
                 "QueueBuffer_int_ctor(&lqueue, queue, 16384);", "this->sq->shared_in"):
        assert kept in text
    glue = SPIKE_GLUE.format(stubs=CPROTO / "dx100_stubs.h", harness=CPROTO / "harness.h")
    (tmp_path / "gen.c").write_text(f'#include "{tmp_path / "low" / "swdb_unit_peter.c"}"\n{glue}')
    flags = ["-std=c11", "-O1", "-DSWDB_NATIVE", "-DSWDB_TRACE"]
    for name, source in (("gen", tmp_path / "gen.c"), ("hand", CPROTO / "unit_peter.c")):
        built = subprocess.run([_c_compiler(), *flags, source, "-o", tmp_path / name], capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
    generated, hand = _stream_sha256([tmp_path / "gen"]), _stream_sha256([tmp_path / "hand"])
    assert generated == hand
    assert hand[1] == 1731456 and "RUNS 1731456 failed_check 0 failed_p2 0" in hand[2]
    concrete = [subprocess.run([tmp_path / n, "concrete"], capture_output=True, text=True, check=True).stdout
                for n in ("gen", "hand")]
    assert concrete[0] == concrete[1] and "call " in concrete[0]          # ticket 06's SAW input, full call trace


def test_float_and_double_lower_to_the_same_c_types_with_literals_spelled_exactly(tmp_path):
    """Ticket 26's real-valued units: the C keeps IEEE float/double; the proof's float model is the method
    version's WP flag (-wp-model +real today), not the lowering's."""
    text, _ = _lowered("floats", tmp_path)
    assert "struct Rank { double value; float weight; };" in text
    assert "double swdb_float_unit(const double *a, int n, float scale)" in text
    assert "r.weight = (scale * 0.5f);" in text and "0.001" in text and "3.0" in text


def test_a_class_template_with_defaulted_arguments_names_every_argument(tmp_path):
    source = tmp_path / "unit.cc"
    source.write_text("template <class T, class U = T, bool B = true> struct SwdbPair { T a; U b; };\n"
                      "int swdb_default_unit(SwdbPair<int> *p) { return p->a + p->b; }\n")
    lower(source, "swdb_default_unit", tmp_path / "out")
    text = (tmp_path / "out" / "swdb_default_unit.c").read_text()
    assert "struct SwdbPair_int_int_true { int a; int b; };" in text
    assert "int swdb_default_unit(SwdbPair_int_int_true *p)" in text


# --- ticket 25: the std::vector and std::pair models ---------------------------------------------------------

def test_a_unit_using_the_models_lists_the_model_version_and_allocation_and_one_using_neither_lists_neither(tmp_path):
    from swdb import std_models
    used = lower(LOWERING / "vector_pair.cc", "swdb_vector_unit", tmp_path / "vector")
    assert used["std_models"] == {**std_models.identity(), "types": ["std_pair_int_int", "std_vector_int"]}
    assert used["std_models"]["id"] == "swdb-std-models-1" and used["allocation"] is True
    anchors = json.loads((tmp_path / "vector" / "swdb_vector_unit.anchors.json").read_text())
    assert anchors["std_models"] == used["std_models"] and anchors["allocation"] is True
    new_only = lower(LOWERING / "new_array.cc", "swdb_new_unit", tmp_path / "new")
    assert "std_models" not in new_only and new_only["allocation"] is True        # new[]: allocation succeeds only
    neither = lower(WP / "core_subset.cc", "swdb_core_kernel", tmp_path / "core")
    assert "std_models" not in neither and "allocation" not in neither


VECTOR_CITES = {"ctor": "[vector.cons]", "ctor_count": "[vector.cons]", "ctor_count_value": "[vector.cons]",
                "copy_ctor": "[container.requirements.general]", "move_ctor": "[container.requirements.general]",
                "dtor": "[container.requirements.general]", "operator_index": "[sequence.reqmts]",
                "at": "[sequence.reqmts]", "data": "[vector.data]", "size": "[container.requirements.general]",
                "empty": "[container.requirements.general]", "begin": "[container.requirements.general]",
                "end": "[container.requirements.general]", "push_back": "[vector.modifiers]",
                "resize": "[vector.capacity]", "reserve": "[vector.capacity]", "clear": "[sequence.reqmts]",
                "swap": "[vector.special]"}


def test_each_modeled_member_has_a_c_function_whose_acsl_contract_cites_its_standard_clause(tmp_path):
    lower(LOWERING / "vector_pair.cc", "swdb_vector_unit", tmp_path)
    text = (tmp_path / "swdb_vector_unit.c").read_text()
    for member, clause in VECTOR_CITES.items():
        match = re.search(rf"/\* (\[[^@]*?)\*/\n/\*@ ((?:(?!\*/).)*)\*/\nstatic [^\n]*\bstd_vector_int_{member}\(", text,
                          re.S)
        assert match, member
        assert clause in match.group(1), (member, match.group(1))
        assert "ensures" in match.group(2) and "requires" in match.group(2), member
    for member in ("ctor", "copy_ctor", "operator_assign"):
        match = re.search(rf"/\* (\[pairs\.pair\][^@]*?)\*/\n/\*@ ((?:(?!\*/).)*)\*/\nstatic [^\n]*\bstd_pair_int_int_"
                          rf"{member}\(", text, re.S)
        assert match and "ensures" in match.group(2), member


def test_a_reallocating_member_names_the_struct_fields_and_buffer_it_writes_and_states_the_old_buffer_freed(tmp_path):
    lower(LOWERING / "vector_pair.cc", "swdb_vector_unit", tmp_path)
    text = (tmp_path / "swdb_vector_unit.c").read_text()
    for member in ("push_back", "resize", "reserve"):
        contract = re.search(rf"/\*@ ((?:(?!\*/).)*)\*/\nstatic void std_vector_int_{member}\(", text, re.S).group(1)
        assert re.search(r"assigns \*this\b", contract), member                 # data, size and capacity
        assert "!\\valid(\\old(this->data))" in contract, member               # growth frees the old buffer
    assert "assigns *this, this->data[this->size];" in text                    # push_back's buffer write
    at = re.search(r"/\*@ ((?:(?!\*/).)*)\*/\nstatic int \*std_vector_int_at\(", text, re.S).group(1)
    assert "requires std_vector_int_readable(this) && n < this->size;" in at   # at out of range: an obligation


def test_the_model_contracts_type_check_in_frama_c_over_the_c_lowering():
    from swdb import c_lowering, framac
    tool = framac.locate()
    if tool.missing:
        pytest.skip(tool.missing)
    lowering = c_lowering.lower(LOWERING / "vector_pair.cc", "swdb_vector_unit")
    assert framac.typecheck(tool, lowering.text) is None
    wrong = lowering.text.replace("ensures \\result == this->data; */", "ensures \\result == this->buffer; */", 1)
    assert wrong != lowering.text and framac.typecheck(tool, wrong) is not None       # a field the model lacks


def test_changing_one_member_contract_gives_a_new_model_pin(tmp_path):
    from swdb import std_models
    source = open(std_models.__file__).read()
    old = 'f"    ensures \\\\result == this->data + n; */\\n"'
    assert source.count(old) == 2                                             # operator[] and at
    changed = tmp_path / "std_models.py"
    changed.write_text(source.replace(old, 'f"    ensures \\\\result == this->data; */\\n"', 1))
    assert std_models.identity(changed)["id"] == std_models.identity()["id"]
    assert std_models.identity(changed)["sha256"] != std_models.identity()["sha256"]


def test_terminal_delete_certificate_keeps_the_native_lowering_and_names_the_checked_release(tmp_path):
    record = lower(LOWERING / "new_array.cc", "swdb_new_unit", tmp_path)
    certificate = record["terminal_release"]
    assert certificate["function"] == "swdb_new_unit" and certificate["owner"] == "buf"
    assert certificate["model"] == "swdb_alloc_delete_array_int"
    assert certificate["checker"]["id"] == "terminal-release-check-1"
    assert "swdb_alloc_delete_array_int(buf);" in (tmp_path / "swdb_new_unit.c").read_text()
    anchors = json.loads((tmp_path / "swdb_new_unit.anchors.json").read_text())
    assert anchors["terminal_release"] == certificate


@pytest.mark.parametrize("body", [
    "int **escaped = &buf; buf[0] = n; delete[] buf; return n;",
    "int *alias = buf; alias[0] = n; delete[] buf; return n;",
    "int value = n; int *escaped = &value; buf[0] = *escaped; delete[] buf; return value;",
    "buf[0] = n; delete[] buf; return buf[0];",
    "if (n == 1) delete[] buf; delete[] buf; return n;",
    "delete[] buf; delete[] buf; return n;",
    "buf = new int[n]; delete[] buf; return n;",
    "buf[0] = n; delete[] buf; return swdb_later(n);",
])
def test_terminal_release_checker_refuses_escapes_aliases_later_heap_reads_and_extra_effects(tmp_path, body):
    source = tmp_path / "lifetime_control.cc"
    source.write_text("int swdb_later(int n) { return n; }\n"
                      "int swdb_terminal_guard(int n) { int *buf = new int[n]; "
                      "for (int i = 0; i < n; ++i) buf[i] = n; " + body + " }\n")
    record = lower(source, "swdb_terminal_guard", tmp_path / "out")
    assert "terminal_release" not in record


def test_terminal_release_does_not_certify_a_read_before_any_array_initialization(tmp_path):
    source = tmp_path / "uninitialized.cc"
    source.write_text("int swdb_uninitialized(int n) { int *buf = new int[n]; "
                      "int ignored = buf[0]; delete[] buf; return n; }\n")
    record = lower(source, "swdb_uninitialized", tmp_path / "out")
    assert "terminal_release" not in record
