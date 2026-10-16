"""Compiler identity through the public proof command; created 2026-10-15 ET.

External compiler/report stand-ins exercise admission only. Synthetic reports
never establish a theorem. No installed compiler or parser is modified.
"""
import hashlib
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from test_proof_setup import wp_setup


def _compiler(tmp_path, optional_failure="parser"):
    from swdb import c_lowering
    real = list(c_lowering.locate().command)
    root = tmp_path / "isolated-llvm"
    resource = root / "lib" / "clang" / "22"
    resource.mkdir(parents=True)
    if optional_failure == "headers":
        actual = subprocess.run([*real, "-print-resource-dir"], check=True,
                                capture_output=True, text=True).stdout.strip()
        lib = Path(actual).resolve().parents[2] / "lib"
        parser = next((lib / name for name in ("libclang.dylib", "libclang.so") if (lib / name).is_file()), None)
        if parser is None:
            pytest.skip("matching libclang required for the missing-header control")
        (root / "lib" / parser.name).symlink_to(parser.resolve())
    driver = root / "driver"
    driver.write_text("#!" + sys.executable + "\n" + f'''import os, shlex, sys
args = sys.argv[1:]
if "--version" in args:
    print("clang version 22.1.8"); sys.exit(0)
if "-print-resource-dir" in args:
    print({str(resource)!r}); sys.exit(0)
if "-###" in args:
    print(shlex.join([{str(driver)!r}, "-cc1", args[-1]]), file=sys.stderr)
    sys.exit(0)
os.execv({real[0]!r}, {real!r} + args)
''')
    driver.chmod(0o755)
    wrapper = root / "wrapped-clang++"
    wrapper.write_text("#!/bin/sh\nexec " + shlex.quote(str(driver)) + ' "$@"\n')
    wrapper.chmod(0o755)
    return driver, wrapper


@pytest.mark.parametrize("optional_failure", ["parser", "headers"])
@pytest.mark.parametrize("selected", ["wrapper", "direct"])
def test_unchanged_command_cannot_hide_same_version_driver_change_without_optional_provenance(
        tmp_path, monkeypatch, wp_setup, selected, optional_failure):
    import yaml
    from swdb import c_lowering
    driver, wrapper = _compiler(tmp_path, optional_failure)
    monkeypatch.setenv("SWDB_CLANG", str(wrapper if selected == "wrapper" else driver))
    # Pin the actual isolated fallback environment, not a previous full identity.
    wp_setup.method["c_lowering"]["translators"] = [c_lowering.identity()["c_lowering"]]
    wp_setup.method_path.write_text(yaml.safe_dump(wp_setup.method, sort_keys=False))
    first = wp_setup.record(wp_setup.prove("helper"))
    assert first["verdict"] == "proven"  # Stand-in only: proves admission occurred.
    runtime = first["settings"]["compiler_runtime"]
    assert runtime["driver"] == {"path": str(driver), "sha256": hashlib.sha256(driver.read_bytes()).hexdigest()}
    executable = wrapper if selected == "wrapper" else driver
    assert runtime["command_executable"] == {
        "path": str(executable), "sha256": hashlib.sha256(executable.read_bytes()).hexdigest()}
    assert ("matching libclang" if optional_failure == "parser" else "header tree") in runtime["unavailable"]
    previous = set(wp_setup.records.glob("proofs/*.yaml"))
    wrapper_bytes = wrapper.read_bytes()
    driver.write_text(driver.read_text() + "\n# same-version replacement driver\n")
    wp_setup.marker.unlink()
    done = wp_setup.prove("helper")
    assert done.returncode != 0, done.stdout
    assert "translator" in done.stderr or "compiler" in done.stderr, done.stderr
    assert wrapper.read_bytes() == wrapper_bytes
    assert not wp_setup.marker.exists()
    assert set(wp_setup.records.glob("proofs/*.yaml")) == previous


@pytest.mark.parametrize("trace", ["opaque", "multiple", "missing_binary", "changed_source"])
def test_unresolvable_frontend_refuses_even_a_freshly_pinned_method(tmp_path, monkeypatch, wp_setup, trace):
    import yaml
    from swdb import c_lowering
    driver, wrapper = _compiler(tmp_path)
    text = driver.read_text()
    if trace == "opaque":
        text = text.replace('"-cc1"', '"opaque-job"')
    elif trace == "multiple":
        text = text.replace('    sys.exit(0)\nos.execv',
                            f'    print(shlex.join([{str(driver)!r}, "-cc1", args[-1]]), file=sys.stderr)\n'
                            '    sys.exit(0)\nos.execv')
    elif trace == "missing_binary":
        text = text.replace(repr(str(driver)) + ', "-cc1"', repr(str(driver) + "-missing") + ', "-cc1"')
    else:
        text = text.replace('"-cc1", args[-1]', '"-cc1", "different-source.cc"')
    driver.write_text(text)
    monkeypatch.setenv("SWDB_CLANG", str(wrapper))
    wp_setup.method["c_lowering"]["translators"] = [c_lowering.identity()["c_lowering"]]
    wp_setup.method_path.write_text(yaml.safe_dump(wp_setup.method, sort_keys=False))
    done = wp_setup.prove("helper")
    assert done.returncode != 0, done.stdout
    assert "frontend" in done.stderr, done.stderr
    assert not wp_setup.marker.exists()
    assert not list(wp_setup.records.glob("proofs/*.yaml"))


@pytest.mark.parametrize("body", [
    "return std::min(n, n);",
    "int *p = new int[1]; p[0] = n; int result = p[0]; delete[] p; return result;",
], ids=["standard-model", "allocation"])
def test_missing_optional_parser_never_waives_original_standard_source_certificate(
        tmp_path, monkeypatch, wp_setup, body):
    import yaml
    from swdb import c_lowering
    driver, wrapper = _compiler(tmp_path)
    monkeypatch.setenv("SWDB_CLANG", str(wrapper))
    wp_setup.method["c_lowering"]["translators"] = [c_lowering.identity()["c_lowering"]]
    wp_setup.method_path.write_text(yaml.safe_dump(wp_setup.method, sort_keys=False))
    source = '#include <algorithm>\nint summary_helper(int n) {' + body + '}\n'
    source += 'int setup_unit(int n) { return summary_helper(n); }\n'
    (tmp_path / "library" / "proof_units" / "setup.cc").write_text(source)
    for path in wp_setup.entries.values():
        data = yaml.safe_load(path.read_text())
        data["proof_unit"]["source"]["sha256"] = hashlib.sha256(source.encode()).hexdigest()
        path.write_text(yaml.safe_dump(data, sort_keys=False))
    record = wp_setup.record(wp_setup.prove("helper"))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct"
    assert "matching libclang" in record["settings"]["stdlib_provenance"]["reason"]
    assert not wp_setup.marker.exists()
    assert not record.get("goals")


def test_driver_change_after_planning_refuses_before_verifier_invocation(tmp_path, monkeypatch, wp_setup):
    import yaml
    from swdb import c_lowering
    driver, wrapper = _compiler(tmp_path)
    monkeypatch.setenv("SWDB_CLANG", str(wrapper))
    wp_setup.method["c_lowering"]["translators"] = [c_lowering.identity()["c_lowering"]]
    wp_setup.method_path.write_text(yaml.safe_dump(wp_setup.method, sort_keys=False))
    compiler = tmp_path / "ocamlfind.py"
    compiler.write_text(compiler.read_text() +
        f"\np = Path({str(driver)!r})\np.write_text(p.read_text() + '\\n# replaced after planning\\n')\n")
    done = wp_setup.prove("helper")
    assert wp_setup.compiled.exists()
    assert done.returncode != 0, done.stdout
    assert "compiler_runtime" in done.stderr, done.stderr
    assert not wp_setup.marker.exists()
    assert not list(wp_setup.records.glob("proofs/*.yaml"))


@pytest.mark.parametrize("changed", ["arguments", "frontend"])
def test_unchanged_executables_cannot_hide_compiler_semantic_flag_changes(tmp_path, monkeypatch, wp_setup, changed):
    import yaml
    from swdb import c_lowering
    driver, wrapper = _compiler(tmp_path)
    if changed == "frontend":
        # A truthful fixed wrapper: preserve the real driver's complete cc1
        # trace, varying only an ordinary semantic option from its environment.
        real = c_lowering.locate().command
        resource = wrapper.parent / "lib" / "clang" / "22"
        wrapper.write_text('#!/bin/sh\nif [ "$1" = "-print-resource-dir" ]; then\n'
                           + "  printf '%s\\n' " + shlex.quote(str(resource)) + '\n  exit 0\nfi\nexec '
                           + shlex.join(real) + ' "$SWDB_TEST_FRONTEND_FLAG" "$@"\n')
        monkeypatch.setenv("SWDB_TEST_FRONTEND_FLAG", "-fsigned-char")
    command = [str(wrapper), "-fsigned-char"] if changed == "arguments" else [str(wrapper)]
    monkeypatch.setenv("SWDB_CLANG", shlex.join(command))
    wp_setup.method["c_lowering"]["translators"] = [c_lowering.identity()["c_lowering"]]
    wp_setup.method_path.write_text(yaml.safe_dump(wp_setup.method, sort_keys=False))
    first = wp_setup.record(wp_setup.prove("helper"))
    assert first["verdict"] == "proven"  # Stand-in admission, not a theorem.
    previous = set(wp_setup.records.glob("proofs/*.yaml"))
    before = (driver.read_bytes(), wrapper.read_bytes())
    if changed == "arguments":
        monkeypatch.setenv("SWDB_CLANG", shlex.join([str(wrapper), "-funsigned-char"]))
    else:
        monkeypatch.setenv("SWDB_TEST_FRONTEND_FLAG", "-funsigned-char")
    wp_setup.marker.unlink()
    done = wp_setup.prove("helper")
    assert done.returncode != 0, done.stdout
    assert "translator" in done.stderr or "compiler_runtime" in done.stderr, done.stderr
    assert (driver.read_bytes(), wrapper.read_bytes()) == before
    assert not wp_setup.marker.exists()
    assert set(wp_setup.records.glob("proofs/*.yaml")) == previous
