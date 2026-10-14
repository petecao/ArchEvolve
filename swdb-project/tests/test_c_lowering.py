"""The C lowering tool: `swdb lower` turns a core-subset C++ proof unit into C with kept names and anchors.

Created: 2026-10-14 ET (Probata proof of concept ticket 21). Design: formal-verification map 16 items 3
and 6 (C lowering, kept names), 13 items 4 and 7 (anchors), 11 item 3 (a trusted tool). Format:
docs/reference/format-v0.4-c-lowering-wp.md.

Seam: the public command `swdb lower` (and, for the faithfulness test, the lowered C file it writes).
Cases need clang 22.1.8 (the tool's C++ front end) and skip cleanly without it. No verifier runs here.
"""
import json
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


OUTSIDE = {
    "reference type": "int f(int &x) { return x; }\n",
    "member access": "struct P { int a; };\nint f(struct P *p) { return 0; }\n",
    "function template": "template <typename T> T f(T x) { return x; }\nint g() { return f<int>(1); }\n",
    "OpenMP directive": "int f(int *a, int n) {\n#pragma omp parallel for\n  for (int i = 0; i < n; ++i) a[i] = 0;\n  return 0;\n}\n",
    "floating-point type": "double f(double x) { return x; }\n",
    "no body": "int g(int);\nint f(int x) { return g(x); }\n",
    "member function": "struct S { int f() { return 1; } };\n",
    "overloaded function": "int f(int x) { return x; }\nint f(long x) { return 1; }\n",
}
FUNCTION_OF = {"function template": "g"}


@pytest.mark.parametrize("construct", sorted(OUTSIDE))
def test_a_construct_outside_the_core_subset_is_refused_by_name_with_no_partial_lowering(tmp_path, construct):
    source = tmp_path / "unit.cc"
    source.write_text(OUTSIDE[construct])
    result = lower(source, FUNCTION_OF.get(construct, "f"), tmp_path / "out", ok=False)
    assert result.returncode == 1
    assert "unsupported construct" in result.stderr and "Traceback" not in result.stderr
    words = {"member access": "type struct P", "no body": "no body"}.get(construct, construct)
    assert words in result.stderr
    assert not (tmp_path / "out").exists()


def test_the_spike_b_unit_is_refused_cleanly_until_ticket_24_widens_the_subset(tmp_path):
    """The hand lowering of prototype/06c-cbmc/unit_peter.c is the reference for 24: classes, references and
    templates are outside 21's core subset, so the tool names the first such construct instead of crashing."""
    result = lower(SPIKE / "unit_peter.cpp", "swdb_unit_peter", tmp_path / "out",
                   "--include", REPO / "library" / "dx100", ok=False)
    assert "unsupported construct" in result.stderr and "Traceback" not in result.stderr
    assert not (tmp_path / "out").exists()


CORPUS = sorted((FIXTURES / "proof" / "regression_corpus").glob("*.yaml"))


@pytest.mark.parametrize("case", [c for c in CORPUS if yaml.safe_load(c.read_text())["adapter"] == "c_lowering"],
                         ids=lambda c: c.stem)
def test_each_lowering_regression_corpus_case_gives_its_recorded_class_again(tmp_path, case):
    data = yaml.safe_load(case.read_text())
    assert data["cause"].strip()
    given = data["input"]
    extra = [arg for folder in given.get("include", []) for arg in ("--include", REPO / folder)]
    result = lower(REPO / given["source"], given["function"], tmp_path / "out", *extra, ok=False)
    words = {"unsupported_construct": "unsupported construct", "parse_error": "parse error"}[data["failure_class"]]
    assert words in result.stderr


def test_cpp_that_does_not_parse_is_a_parse_error(tmp_path):
    source = tmp_path / "broken.cc"
    source.write_text("int f(int x) { return x + ; }\n")
    result = lower(source, "f", tmp_path / "out", ok=False)
    assert "parse error" in result.stderr and "expected expression" in result.stderr
