"""Standard-model declaration provenance through prove; created 2026-10-15 ET.

The original TU's include search is authoritative; a clean macro probe or rebuilt
cut cannot certify a candidate-local shadow header. These controls use stand-in WP.
"""
import json
import shlex

import pytest

from conftest import REPO, run_swdb
from test_c_lowering import lower
from test_closed_owner_data import SOURCE
from test_closed_owner_members import _record
from test_vector_ownership_wp import _ownership_seed
from test_wp_adapter import fake, needs_wp


@needs_wp
@pytest.mark.parametrize("header", ["vector", "utility"])
def test_a_local_standard_header_with_an_allocation_override_refuses_before_verification(tmp_path, header):
    seed = _ownership_seed(tmp_path, source=SOURCE.replace("#include <cstddef>", "#include <cstddef>\n#include <utility>"), cases=[("data_safe", 7)])
    # The main source, type spellings and genuine libc++ templates are unchanged.
    # The original TU nevertheless sees a replacement new with an observable write.
    (tmp_path / "library" / "proof_units" / header).write_text("""#pragma once
#include_next <HEADER>
#include <cstdlib>
int swdb_header_allocation_calls=0;
void *operator new(std::size_t count) {
  ++swdb_header_allocation_calls;
  return std::malloc(count);
}
""".replace("HEADER", header))
    record = _record(seed, "--summary", "contract.fixture_vector_owner_data_safe",
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])


@needs_wp
@pytest.mark.parametrize("registration", ["std::set_new_handler(project_handler);",
    "auto install=std::set_new_handler; install(project_handler);"])
def test_a_transitive_header_new_handler_registration_refuses_before_verification(tmp_path, registration):
    source = SOURCE.replace("#include <cstddef>", '#include <cstddef>\n#include "project_hooks.h"')
    seed = _ownership_seed(tmp_path, source=source, cases=[("data_safe", 7)])
    folder = tmp_path / "library" / "proof_units"
    (folder / "project_hooks.h").write_text('''#include <new>
inline void project_handler() {}
struct project_registration {
  project_registration() { REGISTRATION }
};
inline project_registration project_registration_instance;
'''.replace('REGISTRATION', registration))
    record = _record(seed, "--summary", "contract.fixture_vector_owner_data_safe",
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])
    assert "handler registration" in record["settings"]["stdlib_provenance"]["reason"]


def test_an_ordinary_transitive_project_header_keeps_canonical_model_admission(tmp_path):
    source = tmp_path / "unit.cc"
    source.write_text('#include <vector>\n#include "project_support.h"\n'
        'int unit(int n) { std::vector<int> v(n,7); return v.size(); }\n')
    (tmp_path / "project_support.h").write_text(
        "#pragma once\ninline int project_identity(int x) { return x; }\n")
    out = tmp_path / "out"
    lower(source, "unit", out)
    certificate = json.loads((out / "unit.anchors.json").read_text())["stdlib_provenance"]
    assert certificate["verdict"] == "passed"
    assert certificate["parser"]["id"] == "libclang-22.1.8"
    assert any(row["path"].endswith("/project_support.h") for row in certificate["headers"])


def test_a_gapbs_project_header_is_not_a_standard_header_shadow(tmp_path):
    source = tmp_path / "unit.cc"
    source.write_text('#include <vector>\n#include "pvector.h"\n'
        'int unit(int n) { std::vector<int> v(n,7); return v.size(); }\n')
    out = tmp_path / "out"
    lower(source, "unit", out, "--include", REPO / "apps" / "gapbs" / "src")
    certificate = json.loads((out / "unit.anchors.json").read_text())["stdlib_provenance"]
    assert certificate["verdict"] == "passed"
    assert any(row["path"].endswith("/pvector.h") for row in certificate["headers"])


def test_original_tu_preserves_the_drivers_c_compatibility_header_order(tmp_path):
    """Linux driver defaults must not precede its captured libc++ search paths."""
    source = tmp_path / "unit.cc"
    source.write_text('#include <vector>\n#include <cstddef>\n#include <cctype>\n#include <cwctype>\n'
        'int unit(int n) { std::vector<int> v(n,7); return v.size(); }\n')
    out = tmp_path / "out"
    lower(source, "unit", out)
    certificate = json.loads((out / "unit.anchors.json").read_text())["stdlib_provenance"]
    assert certificate["verdict"] == "passed", certificate["reason"]
    # These libc++ C wrappers must precede the underlying compiler/platform headers.
    for header in ("stddef.h", "ctype.h", "wctype.h"):
        assert any(row["path"].endswith("/include/c++/v1/" + header)
                   for row in certificate["headers"]), header


@pytest.mark.parametrize("injected,verdict", [(["-DSWDB_HIDDEN_WRAPPER=1"], "refused"),
    (["-stdlib=libc++"], "passed")])
def test_a_compiler_wrapper_cannot_hide_undeclared_definitions(tmp_path, injected, verdict):
    from swdb import c_lowering
    wrapper = tmp_path / "wrapped-clang++"
    wrapper.write_text("#!/bin/sh\nexec " + shlex.join([*c_lowering.locate().command, *injected]) + ' "$@"\n')
    wrapper.chmod(0o755)
    source = tmp_path / "unit.cc"
    source.write_text('#include <vector>\nint unit(int n) { std::vector<int> v(n,7); return v.size(); }\n')
    out = tmp_path / "out"
    result = run_swdb("lower", "--source", source, "--function", "unit", "--out", out,
        "--format", "json", env={"SWDB_CLANG": str(wrapper)})
    assert result.returncode == 0, result.stderr + result.stdout
    certificate = json.loads((out / "unit.anchors.json").read_text())["stdlib_provenance"]
    assert certificate["verdict"] == verdict
    if verdict == "refused":
        assert "undeclared preprocessor" in certificate["reason"]
    else:
        assert certificate["effective"]["command_executable"]["path"] == str(wrapper)
        assert certificate["effective"]["command_executable"]["sha256"] != certificate["effective"]["driver"]["sha256"]


def test_bare_new_array_provenance_needs_no_standard_header_version_macro(tmp_path):
    source = tmp_path / "unit.cc"
    source.write_text("int unit(int n) { int *p=new int[n]; delete[] p; return n; }\n")
    out = tmp_path / "out"
    lower(source, "unit", out)
    certificate = json.loads((out / "unit.anchors.json").read_text())["stdlib_provenance"]
    assert certificate["verdict"] == "passed"
    assert certificate["library"]["version_macro_required"] is False
    assert certificate["toolchain_headers"]["files"] > 0
