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


@pytest.mark.parametrize("variable", ["CPATH", "CPLUS_INCLUDE_PATH"])
def test_environment_search_cannot_hide_an_explicit_include_allocation_hook(tmp_path, variable):
    explicit, environment = tmp_path / "explicit", tmp_path / "environment"
    explicit.mkdir(); environment.mkdir()
    guard = "PROJECT_CONTEXT_CHOICE"
    (explicit / "choice.h").write_text(f"#ifndef {guard}\n#define {guard}\n"
        "int allocation_calls=0;\n"
        "void *operator new(std::size_t n) {++allocation_calls; return std::malloc(n);}\n#endif\n")
    (environment / "choice.h").write_text(f"#ifndef {guard}\n#define {guard}\n#endif\n")
    source = tmp_path / "unit.cc"
    # Both physical files are included, so equal dependency sets cannot detect
    # choosing the environment header before the driver's explicit -I header.
    source.write_text('#include <vector>\n#include <new>\n#include <cstdlib>\n#include <choice.h>\n'
        '#include "explicit/choice.h"\n#include "environment/choice.h"\n'
        'int unit(int n) {std::vector<int> v(n,7); return v.size();}\n')
    out = tmp_path / "out"
    result = run_swdb("lower", "--source", source, "--function", "unit", "--include", explicit,
        "--out", out, "--format", "json", env={variable:str(environment)})
    assert result.returncode == 0, result.stderr + result.stdout
    certificate = json.loads((out / "unit.anchors.json").read_text())["stdlib_provenance"]
    assert certificate["verdict"] == "refused", certificate["reason"]
    assert "allocation/deallocation hook" in certificate["reason"]


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


def test_original_include_environment_remains_in_driver_context(tmp_path):
    environment = tmp_path / "environment"
    environment.mkdir()
    (environment / "project_context.h").write_text("inline int project_identity(int x) {return x;}\n")
    source = tmp_path / "unit.cc"
    source.write_text('#include <vector>\n#include <project_context.h>\n'
        'int unit(int n) {std::vector<int> v(n,7); return v.size();}\n')
    out = tmp_path / "out"
    result = run_swdb("lower", "--source", source, "--function", "unit", "--out", out,
        "--format", "json", env={"CPATH": str(environment)})
    assert result.returncode == 0, result.stderr + result.stdout
    certificate = json.loads((out / "unit.anchors.json").read_text())["stdlib_provenance"]
    assert certificate["verdict"] == "passed", certificate["reason"]
    assert certificate["context"]["environment"]["CPATH"] == str(environment)
    assert str(environment / "project_context.h") in {row["path"] for row in certificate["headers"]}


@pytest.mark.parametrize("failure", ["nonzero", "timeout", "invalid-json", "invalid-hash"])
def test_isolated_parser_failure_refuses_without_changing_parent_environment(monkeypatch, failure):
    import os
    import subprocess
    from types import SimpleNamespace
    from swdb import stdlib_provenance as provenance

    monkeypatch.setenv("CPATH", "/parent/compiler/context")
    def parser_failure(command, **options):
        assert command[1] == "-I" and command[-1] == "--certify"
        assert all(key not in options["env"] for key in provenance.ENV)
        assert json.loads(options["input"])["environment"]["CPATH"] == "/parent/compiler/context"
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 300)
        payload = {"check": provenance.identity(), "verdict": "passed", "sha256": "0" * 64}
        return SimpleNamespace(returncode=int(failure == "nonzero"),
            stdout="invalid" if failure == "invalid-json" else json.dumps(payload))
    monkeypatch.setattr(subprocess, "run", parser_failure)
    report = provenance.certify(SimpleNamespace(command=("clang++",), version="22.1.8"), "missing.cc")
    assert report["verdict"] == "refused"
    assert os.environ["CPATH"] == "/parent/compiler/context"


def test_a_platform_integer_format_header_keeps_its_canonical_physical_identity(tmp_path):
    """2026-10-15 ET: original GAPBS uses the platform C inttypes wrapper."""
    source = tmp_path / "unit.cc"
    source.write_text('#include <vector>\n#include <inttypes.h>\n'
        'int unit(int n) {std::vector<int> v(n,7); return v.size();}\n')
    out = tmp_path / "out"
    lower(source, "unit", out)
    certificate = json.loads((out / "unit.anchors.json").read_text())["stdlib_provenance"]
    assert certificate["verdict"] == "passed", certificate["reason"]
    platform = [row for row in certificate["headers"]
                if row["path"].endswith("/inttypes.h") and "/include/c++/v1/" not in row["path"]]
    assert platform, "the original platform C header must remain in the physical closure"
    assert all(row in certificate["baseline"] for row in platform)


@pytest.mark.parametrize("header", ["inttypes.h", "cinttypes"])
def test_an_integer_header_shadow_cannot_borrow_the_clean_canonical_baseline(tmp_path, header):
    """2026-10-15 ET: canonical C-header coverage never trusts a project twin."""
    include = tmp_path / "include"
    include.mkdir()
    (include / header).write_text('#pragma once\n#include_next <' + header + '>\n'
        '#include <cstdlib>\n'
        'int integer_header_allocation_calls=0;\n'
        'void *operator new(std::size_t n) {\n'
        '  ++integer_header_allocation_calls; return std::malloc(n);\n}\n')
    source = tmp_path / "unit.cc"
    source.write_text('#include <vector>\n#include <' + header + '>\n'
        'int unit(int n) {std::vector<int> v(n,7); return v.size();}\n')
    out = tmp_path / "out"
    lower(source, "unit", out, "--include", include)
    certificate = json.loads((out / "unit.anchors.json").read_text())["stdlib_provenance"]
    assert certificate["verdict"] == "refused", certificate["reason"]
    assert "noncanonical standard header" in certificate["reason"], certificate["reason"]
